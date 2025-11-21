/**
 * ChatInput component for message input with attach functionality.
 */

import React from 'react'
import { AttachPopover } from './AttachPopover'

export function ChatInput({
  input,
  loading,
  showAttachPopover,
  fileInputRef,
  onInputChange,
  onKeyDown,
  onSendMessage,
  onAttachClick,
  onFileSelect,
  onUrlSubmit,
  onClosePopover,
  onFileChange
}) {
  return (
    <div className="input-container">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        hidden
        onChange={onFileChange}
        accept=".pdf,.txt,.md,.docx"
      />

      <div className="input-wrapper">
        <div className="input-actions">
          {/* Attach button */}
          <button
            className="attach-button"
            onClick={onAttachClick}
            aria-label="Attach file or URL"
          >
            📎
          </button>

          {/* Popover menu */}
          {showAttachPopover && (
            <AttachPopover
              onClose={onClosePopover}
              onFileSelect={onFileSelect}
              onUrlSubmit={onUrlSubmit}
            />
          )}
        </div>

        {/* Message input */}
        <textarea
          className="input-field"
          value={input}
          onChange={onInputChange}
          onKeyDown={onKeyDown}
          placeholder="Message..."
          disabled={loading}
          rows={1}
        />

        {/* Send button */}
        <button
          className="send-button"
          onClick={onSendMessage}
          disabled={loading || !input.trim()}
        >
          ➤
        </button>
      </div>
    </div>
  )
}

export default ChatInput
