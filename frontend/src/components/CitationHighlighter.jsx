import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { CodeBlock, InlineCode } from './CodeBlock'
import './CitationHighlighter.css'

export function CitationHighlighter({ content, chunkMapping }) {
  const [hoveredCitation, setHoveredCitation] = useState(null)

  // If no chunk mapping, just render markdown normally
  if (!chunkMapping || chunkMapping.length === 0) {
    return (
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
          }
        }}
      >
        {content}
      </ReactMarkdown>
    )
  }

  // Parse citations from text like [doc1_chunk0]
  const parseCitations = (text) => {
    const citationRegex = /\[doc\d+_chunk\d+\]/g
    const parts = []
    let lastIndex = 0
    let match
    let citationNumber = 1

    while ((match = citationRegex.exec(text)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index)
        })
      }

      // Add citation
      const citationId = match[0].slice(1, -1) // Remove brackets
      const metadata = chunkMapping.find(c => c.chunk_id === citationId)

      parts.push({
        type: 'citation',
        id: citationId,
        number: citationNumber++,
        content: match[0],
        metadata
      })

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex)
      })
    }

    return parts
  }

  const parts = parseCitations(content)

  // Build markdown content with numbered citations
  let processedContent = ''
  for (const part of parts) {
    if (part.type === 'text') {
      processedContent += part.content
    } else {
      // Replace [doc1_chunk0] with superscript number
      processedContent += `<sup class="citation-marker" data-citation-id="${part.id}">[${part.number}]</sup>`
    }
  }

  return (
    <div className="citation-content">
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
          sup({ className, children, ...props }) {
            const citationId = props['data-citation-id']
            if (className === 'citation-marker' && citationId) {
              const part = parts.find(p => p.type === 'citation' && p.id === citationId)
              if (part && part.metadata) {
                return (
                  <sup
                    className="citation"
                    onMouseEnter={() => setHoveredCitation(citationId)}
                    onMouseLeave={() => setHoveredCitation(null)}
                    {...props}
                  >
                    <span className="citation-marker">{children}</span>
                    {hoveredCitation === citationId && (
                      <div className="citation-tooltip">
                        <div className="citation-doc-name">
                          <strong>{part.metadata.filename}</strong>
                        </div>
                        {part.metadata.url && (
                          <div className="citation-url">
                            <a href={part.metadata.url} target="_blank" rel="noopener noreferrer">
                              {part.metadata.url}
                            </a>
                          </div>
                        )}
                        <div className="citation-meta">
                          Document {part.metadata.doc_number} • {part.metadata.file_type.toUpperCase()}
                        </div>
                      </div>
                    )}
                  </sup>
                )
              }
            }
            return <sup {...props}>{children}</sup>
          }
        }}
      >
        {processedContent}
      </ReactMarkdown>

      {parts.some(p => p.type === 'citation') && (
        <div className="citations-list">
          <div className="citations-header">📚 Sources:</div>
          {parts
            .filter(p => p.type === 'citation' && p.metadata)
            .map((part, idx) => (
              <div key={idx} className="citation-item">
                <span className="citation-num">[{part.number}]</span>
                <span className="citation-name">{part.metadata.filename}</span>
                {part.metadata.url && (
                  <a
                    href={part.metadata.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="citation-link"
                  >
                    🔗
                  </a>
                )}
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
