"""
Document processing service for URLs and file uploads.
Handles scraping, extraction, and storage with WebSocket progress updates.
"""

import logging
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from uuid import uuid4
from typing import Optional

from nexusql import DatabaseManager
from app.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents (URLs and files) with live progress updates."""

    def __init__(self, db: DatabaseManager, websocket_manager: WebSocketManager):
        self.db = db
        self.ws_manager = websocket_manager

    async def process_url(
        self,
        url: str,
        session_id: str,
        user_id: str,
        message_id: Optional[str] = None
    ) -> dict:
        """
        Process a URL through the document ingestion pipeline.

        Args:
            url: The URL to process
            session_id: The chat session ID
            user_id: The user ID
            message_id: Optional message ID that triggered this processing

        Returns:
            Dict with document_id and metadata
        """
        try:
            # Step 1: Fetching
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='fetch_content',
                status='started',
                message='📄 Fetching content...'
            )

            fetch_result = await self._fetch_url(url)

            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='fetch_content',
                status='completed',
                message=f'✓ Fetched: {fetch_result["title"]}',
                metadata={'title': fetch_result['title']}
            )

            # Step 2: Extracting text
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='extract_text',
                status='started',
                message='📝 Extracting text...'
            )

            text_content = fetch_result['text_content']
            word_count = len(text_content.split())

            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='extract_text',
                status='completed',
                message=f'✓ Extracted {word_count:,} words'
            )

            # Step 3: Store document
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='store_document',
                status='started',
                message='💾 Storing in knowledge base...'
            )

            document_id = await self._store_document(
                session_id=session_id,
                user_id=user_id,
                url=url,
                title=fetch_result['title'],
                content=text_content,
                word_count=word_count,
                metadata=fetch_result['metadata']
            )

            logger.info(f"Stored document {document_id} for session {session_id}")

            # Final success message
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='complete',
                status='completed',
                message=f'✓ Document "{fetch_result["title"]}" added to session',
                metadata={
                    'document_id': document_id,
                    'title': fetch_result['title'],
                    'word_count': word_count,
                    'url': url
                }
            )

            logger.info(f"Successfully processed URL: {url} -> document {document_id}")

            return {
                'document_id': document_id,
                'title': fetch_result['title'],
                'word_count': word_count,
                'url': url
            }

        except Exception as e:
            # Broadcast error
            logger.error(f"Failed to process URL {url}: {e}")

            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='error',
                status='failed',
                message=f'❌ Failed to process URL: {str(e)}',
                metadata={'error': str(e), 'url': url}
            )

            # Don't re-raise since we've already handled and broadcast the error
            # and this is running in a background task
            return None

    async def process_file(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        session_id: str,
        user_id: str
    ) -> dict:
        """
        Process an uploaded file.

        Args:
            file_content: The file bytes
            filename: Original filename
            file_type: File extension (pdf, txt, md, docx)
            session_id: The chat session ID
            user_id: The user ID

        Returns:
            Dict with document_id and metadata
        """
        try:
            # Broadcast upload start
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='upload',
                status='started',
                message=f'📤 Uploading {filename}...'
            )

            # Step 1: Extract text based on file type
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='extract_text',
                status='started',
                message=f'📝 Extracting text from {file_type.upper()}...'
            )

            text_content = await self._extract_file_text(file_content, file_type)
            word_count = len(text_content.split())

            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='extract_text',
                status='completed',
                message=f'✓ Extracted {word_count:,} words'
            )

            # Step 2: Store document
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='store_document',
                status='started',
                message='💾 Storing document...'
            )

            document_id = await self._store_document(
                session_id=session_id,
                user_id=user_id,
                url=None,
                title=filename,
                content=text_content,
                word_count=word_count,
                metadata={
                    'file_type': file_type,
                    'file_size': len(file_content)
                }
            )

            # Final success message
            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='complete',
                status='completed',
                message=f'✓ Document "{filename}" added to session',
                metadata={
                    'document_id': document_id,
                    'title': filename,
                    'word_count': word_count,
                    'file_type': file_type
                }
            )

            logger.info(f"Successfully processed file: {filename} -> document {document_id}")

            return {
                'document_id': document_id,
                'title': filename,
                'word_count': word_count,
                'file_type': file_type
            }

        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}", exc_info=True)

            await self.ws_manager.broadcast_pipeline_event(
                session_id=session_id,
                step_name='error',
                status='failed',
                message=f'❌ Failed to process file: {str(e)}',
                metadata={'error': str(e), 'filename': filename}
            )

            raise

    async def _fetch_url(self, url: str) -> dict:
        """Fetch and parse URL content."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; IAChatBot/1.0)'}
            )
            response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            element.decompose()

        # Extract text
        text_content = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        text_content = '\n'.join(lines)

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else url

        # Truncate long titles
        if len(title) > 200:
            title = title[:200] + '...'

        return {
            'text_content': text_content,
            'title': title,
            'metadata': {
                'content_type': response.headers.get('content-type', ''),
                'status_code': response.status_code,
                'url': url
            }
        }

    async def _extract_file_text(self, content_bytes: bytes, file_type: str) -> str:
        """Extract text from file bytes based on file type."""
        if file_type in ['txt', 'md']:
            return content_bytes.decode('utf-8', errors='ignore')

        elif file_type == 'pdf':
            try:
                from pypdf import PdfReader
                import io

                pdf_file = io.BytesIO(content_bytes)
                reader = PdfReader(pdf_file)

                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)

                return "\n\n".join(text_parts)

            except ImportError:
                raise Exception("PDF support not installed. Install pypdf: pip install pypdf")

        elif file_type == 'docx':
            try:
                from docx import Document
                import io

                docx_file = io.BytesIO(content_bytes)
                doc = Document(docx_file)

                text_parts = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text)

                return "\n\n".join(text_parts)

            except ImportError:
                raise Exception("DOCX support not installed. Install python-docx: pip install python-docx")

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    async def _store_document(
        self,
        session_id: str,
        user_id: str,
        url: Optional[str],
        title: str,
        content: str,
        word_count: int,
        metadata: dict
    ) -> str:
        """Store document in database."""
        document_id = str(uuid4())
        now = datetime.now()

        char_count = len(content)
        preview = content[:500].strip()

        self.db.execute(
            """
            INSERT INTO documents
            (id, session_id, user_id, filename, file_type, url,
             content, content_preview, word_count, char_count,
             extraction_method, extracted_at, created_at, updated_at, status, included_in_context)
            VALUES (:id, :session_id, :user_id, :filename, :file_type, :url,
                    :content, :preview, :words, :chars,
                    :method, :extracted_at, :created_at, :updated_at, :status, :included)
            """,
            {
                'id': document_id,
                'session_id': session_id,
                'user_id': user_id,
                'filename': title,
                'file_type': 'url' if url else metadata.get('file_type', 'unknown'),
                'url': url,
                'content': content,
                'preview': preview,
                'words': word_count,
                'chars': char_count,
                'method': 'beautifulsoup' if url else 'direct',
                'extracted_at': now,
                'created_at': now,
                'updated_at': now,
                'status': 'active',
                'included': True
            }
        )

        return document_id
