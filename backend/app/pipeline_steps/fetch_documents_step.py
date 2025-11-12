"""
Fetch documents pipeline step for including document context in chat with RAG-style citations.
"""

from ia_modules.pipeline.core import Step
from typing import Dict, Any, List


def chunk_document(content: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Split document into overlapping chunks for better retrieval and citation.

    Args:
        content: Full document text
        chunk_size: Target size in words
        overlap: Number of overlapping words between chunks

    Returns:
        List of chunks with metadata
    """
    words = content.split()
    chunks = []

    if len(words) <= chunk_size:
        # Document is small enough, return as single chunk
        return [{
            'text': content,
            'start_word': 0,
            'end_word': len(words),
            'chunk_index': 0
        }]

    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)

        chunks.append({
            'text': chunk_text,
            'start_word': i,
            'end_word': i + len(chunk_words),
            'chunk_index': len(chunks)
        })

    return chunks


class FetchDocumentsStep(Step):
    """Fetch documents associated with a chat session and format for LLM context with citations."""

    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch documents for session and format for LLM context with chunk-based citations.

        Args:
            data: Input data containing session_id

        Returns:
            Dictionary with:
                - documents: List of document metadata
                - document_context: Formatted string for LLM system message with chunk IDs
                - document_count: Number of documents attached
                - chunk_mapping: Mapping of chunk IDs to document metadata
        """

        session_id = data.get('session_id')
        if not session_id:
            return {
                'documents': [],
                'document_context': '',
                'document_count': 0,
                'chunk_mapping': []
            }

        db_manager = self.services.get('db_manager')
        if not db_manager:
            raise RuntimeError("Database manager not available in services")

        # Fetch active documents for this session that are included in context
        docs = db_manager.fetch_all(
            """
            SELECT id, filename, file_type, url, content, word_count, char_count
            FROM documents
            WHERE session_id = :session_id
              AND status = 'active'
              AND included_in_context = TRUE
            ORDER BY created_at ASC
            """,
            {'session_id': session_id}
        )

        if not docs:
            return {
                'documents': [],
                'document_context': '',
                'document_count': 0,
                'chunk_mapping': []
            }

        # Chunk documents and format for LLM context with citation IDs
        chunked_context_parts = ["=== ATTACHED DOCUMENTS ===\n"]
        chunk_mapping = []  # Track which chunks came from which documents

        for i, doc in enumerate(docs, 1):
            # Chunk the document content
            chunks = chunk_document(doc['content'], chunk_size=500, overlap=50)

            # Add document header
            chunked_context_parts.append(f"\n--- Document {i}: {doc['filename']} ---")
            if doc['url']:
                chunked_context_parts.append(f"Source: {doc['url']}")
            chunked_context_parts.append(f"Type: {doc['file_type'].upper()}")
            chunked_context_parts.append("")

            # Add each chunk with citation ID
            for chunk in chunks:
                chunk_id = f"doc{i}_chunk{chunk['chunk_index']}"

                # Format chunk with citation ID
                chunked_context_parts.append(f"[{chunk_id}] {chunk['text']}\n")

                # Track chunk metadata for frontend citations
                chunk_mapping.append({
                    'chunk_id': chunk_id,
                    'doc_id': str(doc['id']) if doc.get('id') else None,
                    'doc_number': i,
                    'filename': doc['filename'],
                    'file_type': doc['file_type'],
                    'url': doc.get('url'),
                    'start_word': chunk['start_word'],
                    'end_word': chunk['end_word']
                })

            chunked_context_parts.append("=" * 70)

        document_context = "\n".join(chunked_context_parts)

        # Convert to list of dicts for easier access
        documents = [dict(doc) for doc in docs]

        return {
            'documents': documents,
            'document_context': document_context,
            'document_count': len(docs),
            'chunk_mapping': chunk_mapping
        }
