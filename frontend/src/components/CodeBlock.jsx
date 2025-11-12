import { useState } from 'react'
import './CodeBlock.css'

export function CodeBlock({ children, className, ...props }) {
  const [copied, setCopied] = useState(false)

  // Extract language from className (format: language-javascript)
  const language = className ? className.replace('language-', '') : ''

  const handleCopy = () => {
    const code = children?.toString() || ''
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        {language && <span className="code-language">{language}</span>}
        <button
          className="code-copy-btn"
          onClick={handleCopy}
          aria-label="Copy code"
        >
          {copied ? '✓ Copied!' : '📋 Copy'}
        </button>
      </div>
      <pre {...props}>
        <code className={className}>
          {children}
        </code>
      </pre>
    </div>
  )
}

// Inline code component (for `inline code`)
export function InlineCode({ children, ...props }) {
  return <code {...props}>{children}</code>
}
