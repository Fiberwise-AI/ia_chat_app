/**
 * AttachPopover - Compact menu for uploading files or adding URLs
 * Appears when user clicks the attach button
 */

import React, { useState } from 'react'
import './AttachPopover.css'

export function AttachPopover({ onClose, onFileSelect, onUrlSubmit }) {
  const [mode, setMode] = useState('menu') // 'menu' or 'url-input'
  const [url, setUrl] = useState('')

  const handleUrlSubmit = (e) => {
    e.preventDefault()
    if (url.trim()) {
      onUrlSubmit(url.trim())
      setUrl('')
      setMode('menu')
      onClose()
    }
  }

  const handleBackToMenu = () => {
    setMode('menu')
    setUrl('')
  }

  if (mode === 'url-input') {
    return (
      <div className="attach-popover">
        <div className="popover-header">
          <button className="back-btn" onClick={handleBackToMenu}>
            ← Back
          </button>
          <h3>Add URL</h3>
        </div>

        <form onSubmit={handleUrlSubmit}>
          <input
            type="url"
            className="url-input-field"
            placeholder="https://example.com/article"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            autoFocus
            required
          />
          <div className="popover-actions">
            <button type="button" onClick={handleBackToMenu} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Add to Chat
            </button>
          </div>
        </form>
      </div>
    )
  }

  return (
    <div className="attach-popover">
      <div className="attach-options">
        <button
          className="attach-option"
          onClick={() => {
            onFileSelect()
            onClose()
          }}
        >
          <span className="option-icon">📄</span>
          <div className="option-content">
            <div className="option-title">Upload File</div>
            <div className="option-desc">PDF, TXT, MD, DOCX</div>
          </div>
        </button>

        <button className="attach-option" onClick={() => setMode('url-input')}>
          <span className="option-icon">🔗</span>
          <div className="option-content">
            <div className="option-title">Add URL</div>
            <div className="option-desc">Paste a link to process</div>
          </div>
        </button>
      </div>
    </div>
  )
}

export default AttachPopover
