"""
Document processing routes for file upload and URL scraping.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
import uuid
from datetime import datetime
from pathlib import Path
import io

from app.core.dependencies import get_db_manager, get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Supported file types and MIME types
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'txt': ['text/plain', 'text/markdown'],
    'md': ['text/markdown', 'text/plain'],
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def extract_pdf(content_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF support not installed. Install pypdf: pip install pypdf"
        )

    pdf_file = io.BytesIO(content_bytes)
    reader = PdfReader(pdf_file)

    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            text_parts.append(text)

    return "\n\n".join(text_parts)


def extract_docx(content_bytes: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    try:
        from docx import Document
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="DOCX support not installed. Install python-docx: pip install python-docx"
        )

    docx_file = io.BytesIO(content_bytes)
    doc = Document(docx_file)

    text_parts = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)

    return "\n\n".join(text_parts)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """
    Upload a document and extract text content with WebSocket progress updates.

    Supported formats: PDF, TXT, MD, DOCX
    Maximum file size: 10MB
    """

    # Extract file extension
    file_ext = Path(file.filename).suffix.lower().lstrip('.')

    if not file_ext or file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )

    # Read file content
    content_bytes = await file.read()
    file_size = len(content_bytes)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )

    # Use document processor for WebSocket updates
    from app.services.websocket_manager import get_websocket_manager
    from app.services.document_processor import DocumentProcessor

    ws_manager = get_websocket_manager()
    doc_processor = DocumentProcessor(db, ws_manager)

    try:
        # Process file with WebSocket updates
        result = await doc_processor.process_file(
            file_content=content_bytes,
            filename=file.filename,
            file_type=file_ext,
            session_id=session_id,
            user_id=current_user['id']
        )

        return {
            'success': True,
            'document': {
                'id': result['document_id'],
                'filename': result['title'],
                'file_type': result['file_type'],
                'file_size': file_size,
                'word_count': result['word_count'],
                'char_count': result.get('char_count', 0),
                'preview': result.get('preview', ''),
                'created_at': datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@router.post("/scrape-url")
async def scrape_url(
    url: str = Form(...),
    session_id: str = Form(...),
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """
    Scrape content from a URL and extract text.

    Supports standard HTML pages.
    """

    # Validate URL
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")

    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="URL scraping dependencies not installed. Install: pip install httpx beautifulsoup4"
        )

    try:
        # Fetch URL content with timeout
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
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

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse content: {str(e)}"
        )

    # Validate extracted content
    if not text_content.strip():
        raise HTTPException(
            status_code=400,
            detail="No text content could be extracted from the URL"
        )

    # Calculate metadata
    word_count = len(text_content.split())
    char_count = len(text_content)
    preview = text_content[:500].strip()

    # Save to database
    doc_id = str(uuid.uuid4())
    now = datetime.now()

    db.execute(
        """
        INSERT INTO documents
        (id, session_id, user_id, filename, file_type, url,
         content, content_preview, extraction_method, word_count, char_count,
         extracted_at, created_at, updated_at, status)
        VALUES (:id, :session_id, :user_id, :filename, :file_type, :url,
                :content, :preview, :method, :words, :chars,
                :extracted_at, :created_at, :updated_at, :status)
        """,
        {
            'id': doc_id,
            'session_id': session_id,
            'user_id': current_user['id'],
            'filename': title,
            'file_type': 'url',
            'url': url,
            'content': text_content,
            'preview': preview,
            'method': 'beautifulsoup',
            'words': word_count,
            'chars': char_count,
            'extracted_at': now,
            'created_at': now,
            'updated_at': now,
            'status': 'active'
        }
    )

    return {
        'success': True,
        'document': {
            'id': doc_id,
            'filename': title,
            'file_type': 'url',
            'url': url,
            'word_count': word_count,
            'char_count': char_count,
            'preview': preview,
            'created_at': now.isoformat()
        }
    }


@router.get("/session/{session_id}")
async def list_documents(
    session_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """List all active documents for a session."""

    docs = db.fetch_all(
        """
        SELECT id, filename, file_type, file_size, url,
               word_count, char_count, content_preview, created_at,
               included_in_context, tags, collection_id, folder_path
        FROM documents
        WHERE session_id = :session_id AND status = 'active'
        ORDER BY created_at DESC
        """,
        {'session_id': session_id}
    )

    # Convert to list of dicts
    documents = [dict(doc) for doc in docs] if docs else []

    return {'documents': documents}


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Delete a document (soft delete)."""

    now = datetime.now()

    result = db.execute(
        """
        UPDATE documents
        SET status = 'deleted', updated_at = :updated_at
        WHERE id = :id AND user_id = :user_id
        """,
        {
            'id': document_id,
            'user_id': current_user['id'],
            'updated_at': now
        }
    )

    return {'success': True, 'deleted_at': now.isoformat()}


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Get full document details including content."""

    doc = db.fetch_one(
        """
        SELECT id, filename, file_type, file_size, url,
               content, word_count, char_count, extraction_method,
               extracted_at, created_at
        FROM documents
        WHERE id = :id AND user_id = :user_id AND status = 'active'
        """,
        {'id': document_id, 'user_id': current_user['id']}
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {'document': dict(doc)}


@router.patch("/{document_id}/toggle-inclusion")
async def toggle_document_inclusion(
    document_id: str,
    included: bool = Form(...),
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Toggle whether a document is included in LLM context."""

    now = datetime.now()

    db.execute(
        """
        UPDATE documents
        SET included_in_context = :included, updated_at = :updated_at
        WHERE id = :id AND user_id = :user_id
        """,
        {
            'id': document_id,
            'user_id': current_user['id'],
            'included': included,
            'updated_at': now
        }
    )

    return {'success': True, 'included_in_context': included}


@router.get("/library/all")
async def get_global_document_library(
    search: Optional[str] = None,
    tags: Optional[List[str]] = None,
    collection_id: Optional[str] = None,
    folder_path: Optional[str] = None,
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Get all documents across all sessions for the current user."""

    query_parts = [
        """
        SELECT d.id, d.session_id, d.filename, d.file_type, d.file_size, d.url,
               d.word_count, d.char_count, d.content_preview, d.created_at,
               d.included_in_context, d.tags, d.collection_id, d.folder_path,
               c.name as collection_name, c.color as collection_color,
               s.title as session_title
        FROM documents d
        LEFT JOIN document_collections c ON d.collection_id = c.id
        LEFT JOIN chat_sessions s ON d.session_id = s.id
        WHERE d.user_id = :user_id AND d.status = 'active'
        """
    ]

    params = {'user_id': current_user['id']}

    # Add search filter
    if search:
        query_parts.append("AND (d.filename ILIKE :search OR d.content_preview ILIKE :search)")
        params['search'] = f'%{search}%'

    # Add tag filter
    if tags:
        query_parts.append("AND d.tags && :tags")
        params['tags'] = tags

    # Add collection filter
    if collection_id:
        query_parts.append("AND d.collection_id = :collection_id")
        params['collection_id'] = collection_id

    # Add folder filter
    if folder_path:
        query_parts.append("AND d.folder_path = :folder_path")
        params['folder_path'] = folder_path

    query_parts.append("ORDER BY d.created_at DESC LIMIT 1000")

    docs = db.fetch_all('\n'.join(query_parts), params)

    documents = [dict(doc) for doc in docs] if docs else []

    return {'documents': documents, 'total': len(documents)}


@router.patch("/{document_id}/tags")
async def update_document_tags(
    document_id: str,
    tags: List[str] = Form(...),
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Update document tags."""

    now = datetime.now()

    db.execute(
        """
        UPDATE documents
        SET tags = :tags, updated_at = :updated_at
        WHERE id = :id AND user_id = :user_id
        """,
        {
            'id': document_id,
            'user_id': current_user['id'],
            'tags': tags,
            'updated_at': now
        }
    )

    return {'success': True, 'tags': tags}


@router.patch("/{document_id}/collection")
async def update_document_collection(
    document_id: str,
    collection_id: Optional[str] = Form(None),
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Move document to a collection."""

    now = datetime.now()

    db.execute(
        """
        UPDATE documents
        SET collection_id = :collection_id, updated_at = :updated_at
        WHERE id = :id AND user_id = :user_id
        """,
        {
            'id': document_id,
            'user_id': current_user['id'],
            'collection_id': collection_id,
            'updated_at': now
        }
    )

    return {'success': True, 'collection_id': collection_id}


@router.patch("/{document_id}/folder")
async def update_document_folder(
    document_id: str,
    folder_path: str = Form(...),
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Move document to a folder."""

    now = datetime.now()

    db.execute(
        """
        UPDATE documents
        SET folder_path = :folder_path, updated_at = :updated_at
        WHERE id = :id AND user_id = :user_id
        """,
        {
            'id': document_id,
            'user_id': current_user['id'],
            'folder_path': folder_path,
            'updated_at': now
        }
    )

    return {'success': True, 'folder_path': folder_path}


# Collection management endpoints
@router.post("/collections")
async def create_collection(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Create a new document collection."""

    collection_id = str(uuid.uuid4())
    now = datetime.now()

    db.execute(
        """
        INSERT INTO document_collections
        (id, user_id, name, description, color, created_at, updated_at)
        VALUES (:id, :user_id, :name, :description, :color, :created_at, :updated_at)
        """,
        {
            'id': collection_id,
            'user_id': current_user['id'],
            'name': name,
            'description': description,
            'color': color,
            'created_at': now,
            'updated_at': now
        }
    )

    return {
        'success': True,
        'collection': {
            'id': collection_id,
            'name': name,
            'description': description,
            'color': color,
            'created_at': now.isoformat()
        }
    }


@router.get("/collections")
async def list_collections(
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """List all collections for the current user."""

    collections = db.fetch_all(
        """
        SELECT c.*, COUNT(d.id) as document_count
        FROM document_collections c
        LEFT JOIN documents d ON d.collection_id = c.id AND d.status = 'active'
        WHERE c.user_id = :user_id
        GROUP BY c.id
        ORDER BY c.name
        """,
        {'user_id': current_user['id']}
    )

    return {'collections': [dict(c) for c in collections] if collections else []}


@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db_manager)
):
    """Delete a collection (documents remain, just unlinked)."""

    db.execute(
        """
        DELETE FROM document_collections
        WHERE id = :id AND user_id = :user_id
        """,
        {'id': collection_id, 'user_id': current_user['id']}
    )

    return {'success': True}
