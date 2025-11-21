/**
 * ChatMessage component for rendering user and assistant messages.
 */

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { CodeBlock, InlineCode } from './CodeBlock'
import { CitationHighlighter } from './CitationHighlighter'
import { SystemMessage } from './SystemMessage'

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export function ChatMessage({ message }) {
  const { role, content, type, error, timestamp, metadata } = message

  return (
    <div className={`message ${role} ${type || ''} ${error ? 'error' : ''}`}>
      {role !== 'system' && (
        <div className="message-avatar">
          {role === 'user' ? '👤' : '🤖'}
        </div>
      )}
      <div className="message-bubble">
        {role !== 'system' && (
          <div className="message-header">
            <strong>{role === 'user' ? 'You' : 'Assistant'}</strong>
            <span className="timestamp" title={new Date(timestamp).toLocaleString()}>
              {formatTimestamp(timestamp)}
            </span>
          </div>
        )}
        <div className="message-content">
          {role === 'system' ? (
            <SystemMessage message={message} />
          ) : role === 'assistant' ? (
            metadata?.chunk_mapping && metadata.chunk_mapping.length > 0 ? (
              <CitationHighlighter
                content={content}
                chunkMapping={metadata.chunk_mapping}
              />
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  code({ inline, className, children, ...props }) {
                    return inline ? (
                      <InlineCode className={className} {...props}>
                        {children}
                      </InlineCode>
                    ) : (
                      <CodeBlock className={className} {...props}>
                        {children}
                      </CodeBlock>
                    )
                  },
                  p({ children }) {
                    // If paragraph contains only a code block, unwrap it to avoid nesting issues
                    if (children && typeof children === 'object' && children.type === CodeBlock) {
                      return children
                    }
                    return <p>{children}</p>
                  }
                }}
              >
                {content}
              </ReactMarkdown>
            )
          ) : (
            <pre>{content}</pre>
          )}
        </div>
        {metadata && role === 'assistant' && (
          <MessageMetadata metadata={metadata} />
        )}
      </div>
    </div>
  )
}

function MessageMetadata({ metadata }) {
  const [showDetails, setShowDetails] = React.useState(false)

  const hasDetails = metadata.provider || metadata.model || metadata.tokens ||
                     metadata.cost_usd !== undefined || metadata.documents_used ||
                     metadata.retrieved_docs

  if (!hasDetails) return null

  return (
    <div className="message-metadata">
      <button
        className="metadata-toggle"
        onClick={() => setShowDetails(!showDetails)}
        title="Show technical details"
      >
        {showDetails ? '▼' : '▶'} Details
      </button>
      {showDetails && (
        <div className="metadata-content">
          {metadata.provider && (
            <span>Provider: {metadata.provider}</span>
          )}
          {metadata.model && (
            <span>Model: {metadata.model}</span>
          )}
          {metadata.tokens && (
            <span>Tokens: {metadata.tokens.toLocaleString()}</span>
          )}
          {metadata.cost_usd !== undefined && (
            <span>Cost: ${metadata.cost_usd.toFixed(4)}</span>
          )}
          {metadata.documents_used !== undefined && metadata.documents_used > 0 && (
            <span>📄 Documents: {metadata.documents_used}</span>
          )}
          {metadata.retrieved_docs && (
            <span>Retrieved: {metadata.retrieved_docs} docs</span>
          )}
        </div>
      )}
    </div>
  )
}

export default ChatMessage
