import { useState } from 'react'
import './DocumentUpload.css'

export function DocumentUpload({ sessionId, onDocumentAdded, apiBaseUrl, onSessionCreated }) {
  const [uploading, setUploading] = useState(false)
  const [scrapingUrl, setScrapingUrl] = useState(false)
  const [urlInput, setUrlInput] = useState('')
  const [error, setError] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  // Create a session if one doesn't exist
  const ensureSession = async () => {
    if (sessionId) return sessionId

    // Create a new session
    try {
      const response = await fetch(`${apiBaseUrl}/api/sessions`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' })
      })

      if (!response.ok) throw new Error('Failed to create session')

      const data = await response.json()
      const newSessionId = data.session_id || data.id

      // Notify parent component
      if (onSessionCreated) {
        onSessionCreated(newSessionId)
      }

      return newSessionId
    } catch (err) {
      throw new Error('Could not create session: ' + err.message)
    }
  }

  const uploadFile = async (file) => {
    if (!file) return

    setUploading(true)
    setError(null)

    try {
      const activeSessionId = await ensureSession()

      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', activeSessionId)

      const response = await fetch(`${apiBaseUrl}/api/documents/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      onDocumentAdded(data.document)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (file) {
      await uploadFile(file)
      e.target.value = '' // Reset file input
    }
  }

  const handleUrlScrape = async () => {
    if (!urlInput.trim()) return

    setScrapingUrl(true)
    setError(null)

    try {
      const activeSessionId = await ensureSession()

      const formData = new FormData()
      formData.append('url', urlInput)
      formData.append('session_id', activeSessionId)

      const response = await fetch(`${apiBaseUrl}/api/documents/scrape-url`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Scraping failed')
      }

      const data = await response.json()
      onDocumentAdded(data.document)

      setUrlInput('')
    } catch (err) {
      setError(err.message)
    } finally {
      setScrapingUrl(false)
    }
  }

  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    // Only set to false if we're leaving the component entirely
    if (e.currentTarget === e.target) {
      setIsDragging(false)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      // Only handle the first file for now
      await uploadFile(files[0])
    }
  }

  return (
    <div
      className={`document-upload ${isDragging ? 'dragging' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {isDragging && (
        <div className="drop-overlay">
          <div className="drop-message">📎 Drop file to upload</div>
        </div>
      )}

      <div className="upload-controls">
        <div className="upload-section">
          <label className="file-upload-btn">
            <input
              type="file"
              accept=".pdf,.txt,.md,.docx"
              onChange={handleFileUpload}
              disabled={uploading}
              style={{ display: 'none' }}
            />
            {uploading ? '📤 Uploading...' : '📎 Upload File'}
          </label>

          <span className="upload-hint">PDF, TXT, MD, DOCX (max 10MB) · Drag & drop supported</span>
        </div>

        <div className="url-section">
          <input
            type="url"
            className="url-input"
            placeholder="Enter URL to scrape..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleUrlScrape()}
            disabled={scrapingUrl}
          />
          <button
            className="scrape-btn"
            onClick={handleUrlScrape}
            disabled={scrapingUrl || !urlInput.trim()}
          >
            {scrapingUrl ? '🔄 Scraping...' : '🌐 Scrape'}
          </button>
        </div>
      </div>

      {error && <div className="upload-error">❌ {error}</div>}
    </div>
  )
}
