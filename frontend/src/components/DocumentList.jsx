import { useState } from 'react'
import './DocumentList.css'

export function DocumentList({ documents, onDocumentRemoved, onDocumentUpdated, apiBaseUrl }) {
  const [expanded, setExpanded] = useState(true)

  if (!documents || documents.length === 0) {
    return null
  }

  const handleDelete = async (docId) => {
    if (!confirm('Remove this document from the conversation?')) return

    try {
      const response = await fetch(`${apiBaseUrl}/api/documents/${docId}`, {
        method: 'DELETE',
        credentials: 'include'
      })

      if (response.ok) {
        onDocumentRemoved(docId)
      }
    } catch (err) {
      console.error('Failed to delete document:', err)
    }
  }

  const handleToggleInclusion = async (docId, currentlyIncluded) => {
    try {
      const formData = new FormData()
      formData.append('included', (!currentlyIncluded).toString())

      const response = await fetch(`${apiBaseUrl}/api/documents/${docId}/toggle-inclusion`, {
        method: 'PATCH',
        credentials: 'include',
        body: formData
      })

      if (response.ok) {
        // Notify parent to refresh document list
        if (onDocumentUpdated) {
          onDocumentUpdated()
        }
      }
    } catch (err) {
      console.error('Failed to toggle document inclusion:', err)
    }
  }

  const getFileIcon = (fileType) => {
    const icons = {
      'pdf': '📄',
      'txt': '📝',
      'md': '📘',
      'docx': '📃',
      'url': '🌐'
    }
    return icons[fileType] || '📎'
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <div className="document-list">
      <button
        className="document-list-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? '▼' : '▶'} Attached Documents ({documents.length})
      </button>

      {expanded && (
        <div className="documents">
          {documents.map(doc => (
            <div key={doc.id} className={`document-item ${!doc.included_in_context ? 'excluded' : ''}`}>
              <label className="document-checkbox" title={doc.included_in_context ? "Included in AI context" : "Excluded from AI context"}>
                <input
                  type="checkbox"
                  checked={doc.included_in_context !== false}
                  onChange={() => handleToggleInclusion(doc.id, doc.included_in_context !== false)}
                />
              </label>

              <div className="document-icon">
                {getFileIcon(doc.file_type)}
              </div>

              <div className="document-info">
                <div className="document-name" title={doc.filename}>
                  {doc.filename}
                  {!doc.included_in_context && <span className="excluded-badge">Excluded</span>}
                </div>
                <div className="document-meta">
                  {doc.word_count?.toLocaleString()} words
                  {doc.file_size && ` • ${formatFileSize(doc.file_size)}`}
                  {doc.url && ` • ${new URL(doc.url).hostname}`}
                </div>
                {doc.content_preview && (
                  <div className="document-preview">
                    {doc.content_preview}...
                  </div>
                )}
              </div>

              <button
                className="document-delete"
                onClick={() => handleDelete(doc.id)}
                title="Remove document"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
