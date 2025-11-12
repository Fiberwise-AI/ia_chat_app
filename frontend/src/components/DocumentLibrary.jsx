import { useState, useEffect } from 'react'
import './DocumentLibrary.css'

export function DocumentLibrary({ apiBaseUrl, currentSessionId, onAttachToSession }) {
  const [documents, setDocuments] = useState([])
  const [collections, setCollections] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCollection, setSelectedCollection] = useState(null)
  const [view, setView] = useState('all') // 'all', 'collection', 'tags'
  const [loading, setLoading] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [showNewCollectionModal, setShowNewCollectionModal] = useState(false)
  const [newCollectionName, setNewCollectionName] = useState('')
  const [newCollectionColor, setNewCollectionColor] = useState('#3b82f6')

  useEffect(() => {
    loadDocuments()
    loadCollections()
  }, [])

  const loadDocuments = async (filters = {}) => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (filters.collection_id) params.append('collection_id', filters.collection_id)

      const response = await fetch(
        `${apiBaseUrl}/api/documents/library/all?${params}`,
        { credentials: 'include' }
      )
      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadCollections = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/documents/collections`, {
        credentials: 'include'
      })
      const data = await response.json()
      setCollections(data.collections || [])
    } catch (err) {
      console.error('Failed to load collections:', err)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    loadDocuments()
  }

  const handleAttachDocument = async (docId, sessionId) => {
    // This would require a backend endpoint to copy/link document to session
    // For now, we'll just show a message
    alert(`Document attachment to session ${sessionId} - Feature coming soon!`)
  }

  const handleCreateCollection = async () => {
    try {
      const formData = new FormData()
      formData.append('name', newCollectionName)
      formData.append('color', newCollectionColor)

      const response = await fetch(`${apiBaseUrl}/api/documents/collections`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      if (response.ok) {
        await loadCollections()
        setShowNewCollectionModal(false)
        setNewCollectionName('')
        setNewCollectionColor('#3b82f6')
      }
    } catch (err) {
      console.error('Failed to create collection:', err)
    }
  }

  const handleAddToCollection = async (docId, collectionId) => {
    try {
      const formData = new FormData()
      if (collectionId) formData.append('collection_id', collectionId)

      const response = await fetch(`${apiBaseUrl}/api/documents/${docId}/collection`, {
        method: 'PATCH',
        credentials: 'include',
        body: formData
      })

      if (response.ok) {
        await loadDocuments()
        await loadCollections()
      }
    } catch (err) {
      console.error('Failed to update collection:', err)
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

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="document-library">
      <div className="library-header">
        <h2>📚 Document Library</h2>
        <button
          className="btn-new-collection"
          onClick={() => setShowNewCollectionModal(true)}
        >
          + New Collection
        </button>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="library-search">
        <input
          type="text"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        <button type="submit" className="btn-search">Search</button>
      </form>

      {/* View Tabs */}
      <div className="library-tabs">
        <button
          className={`tab ${view === 'all' ? 'active' : ''}`}
          onClick={() => { setView('all'); setSelectedCollection(null); loadDocuments(); }}
        >
          All Documents ({documents.length})
        </button>
        <button
          className={`tab ${view === 'collection' ? 'active' : ''}`}
          onClick={() => setView('collection')}
        >
          Collections ({collections.length})
        </button>
      </div>

      {/* Collections View */}
      {view === 'collection' && (
        <div className="collections-grid">
          {collections.map(collection => (
            <div
              key={collection.id}
              className="collection-card"
              style={{ borderLeft: `4px solid ${collection.color || '#3b82f6'}` }}
              onClick={() => {
                setSelectedCollection(collection.id)
                setView('all')
                loadDocuments({ collection_id: collection.id })
              }}
            >
              <div className="collection-name">{collection.name}</div>
              <div className="collection-count">{collection.document_count} documents</div>
              {collection.description && (
                <div className="collection-description">{collection.description}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Documents Grid */}
      {view === 'all' && (
        <>
          {selectedCollection && (
            <div className="active-filter">
              <span>Filtered by collection</span>
              <button
                onClick={() => {
                  setSelectedCollection(null)
                  loadDocuments()
                }}
              >
                Clear ✕
              </button>
            </div>
          )}

          {loading ? (
            <div className="library-loading">Loading...</div>
          ) : documents.length === 0 ? (
            <div className="library-empty">
              <p>No documents found.</p>
              <p className="library-empty-hint">
                Upload documents in a chat session to get started.
              </p>
            </div>
          ) : (
            <div className="documents-grid">
              {documents.map(doc => (
                <div key={doc.id} className="library-doc-card">
                  <div className="doc-card-header">
                    <span className="doc-icon">{getFileIcon(doc.file_type)}</span>
                    <div className="doc-header-actions">
                      {doc.collection_name && (
                        <span
                          className="doc-collection-badge"
                          style={{ background: doc.collection_color || '#3b82f6' }}
                        >
                          {doc.collection_name}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="doc-card-body">
                    <h3 className="doc-title" title={doc.filename}>
                      {doc.filename}
                    </h3>
                    <div className="doc-meta">
                      <span>{doc.word_count?.toLocaleString()} words</span>
                      {doc.session_title && <span>• {doc.session_title}</span>}
                      <span>• {formatDate(doc.created_at)}</span>
                    </div>
                    {doc.content_preview && (
                      <div className="doc-preview">
                        {doc.content_preview.substring(0, 120)}...
                      </div>
                    )}
                  </div>

                  <div className="doc-card-footer">
                    <button
                      className="btn-doc-action"
                      onClick={() => setSelectedDoc(doc.id === selectedDoc ? null : doc.id)}
                    >
                      ⋮ Actions
                    </button>

                    {selectedDoc === doc.id && (
                      <div className="doc-actions-menu">
                        {currentSessionId && (
                          <button onClick={() => handleAttachDocument(doc.id, currentSessionId)}>
                            📎 Attach to current chat
                          </button>
                        )}
                        <button onClick={() => setSelectedDoc(null)}>
                          🗂️ Add to collection
                        </button>
                        <button>🏷️ Edit tags</button>
                        <button className="danger">🗑️ Delete</button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* New Collection Modal */}
      {showNewCollectionModal && (
        <div className="modal-overlay" onClick={() => setShowNewCollectionModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Create New Collection</h3>
            <div className="modal-form">
              <input
                type="text"
                placeholder="Collection name"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                className="modal-input"
              />
              <div className="color-picker">
                <label>Color:</label>
                <input
                  type="color"
                  value={newCollectionColor}
                  onChange={(e) => setNewCollectionColor(e.target.value)}
                />
              </div>
              <div className="modal-actions">
                <button
                  className="btn-cancel"
                  onClick={() => setShowNewCollectionModal(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn-create"
                  onClick={handleCreateCollection}
                  disabled={!newCollectionName.trim()}
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
