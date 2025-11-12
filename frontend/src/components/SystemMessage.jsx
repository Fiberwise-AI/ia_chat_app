/**
 * SystemMessage component for displaying URL detection, document processing, and other system events.
 */

import React from 'react'
import './SystemMessage.css'

export function SystemMessage({ message, onViewDocument }) {
  const getIcon = (type) => {
    switch (type) {
      case 'url_detection':
        return '🔗'
      case 'document_added':
        return '✓'
      case 'document_uploading':
        return '📤'
      case 'error':
        return '❌'
      default:
        return 'ℹ️'
    }
  }

  const handleViewDocument = () => {
    if (message.metadata?.document_id && onViewDocument) {
      onViewDocument(message.metadata.document_id)
    }
  }

  return (
    <div className={`system-message ${message.type}`}>
      <span className="icon">{getIcon(message.type)}</span>
      <span className="content">{message.content}</span>
      {message.metadata?.document_id && (
        <button
          className="view-doc-btn"
          onClick={handleViewDocument}
        >
          View Document
        </button>
      )}
    </div>
  )
}

export default SystemMessage
