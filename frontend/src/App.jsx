import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github-dark.css'
import './App.modern.css'
import { API_BASE_URL } from './config'
import { CodeBlock, InlineCode } from './components/CodeBlock'
import { DocumentUpload } from './components/DocumentUpload'
import { DocumentList } from './components/DocumentList'
import { CitationHighlighter } from './components/CitationHighlighter'
import { DocumentLibrary } from './components/DocumentLibrary'
import { SystemMessage } from './components/SystemMessage'
import { PipelineProgress } from './components/PipelineProgress'
import { AttachPopover } from './components/AttachPopover'

// Helper function for better timestamp formatting
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

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState(null)
  const [showDropdown, setShowDropdown] = useState(false)
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [showSidebar, setShowSidebar] = useState(true)
  const [ws, setWs] = useState(null)
  const [view, setView] = useState('chat')
  const [pipelines, setPipelines] = useState([])
  const [selectedPipeline, setSelectedPipeline] = useState(null)
  const [pipelineJson, setPipelineJson] = useState(null)
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful AI assistant.')
  const [showSystemPrompt, setShowSystemPrompt] = useState(false)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const [documents, setDocuments] = useState([])
  const [sidebarView, setSidebarView] = useState('chats') // 'chats' or 'documents'
  const [showAttachPopover, setShowAttachPopover] = useState(false)
  const [pipelineEvents, setPipelineEvents] = useState([])
  const messagesEndRef = useRef(null)
  const dropdownRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    // Check URL for session ID
    const urlParams = new URLSearchParams(window.location.search)
    const sessionIdFromUrl = urlParams.get('session')

    // Load user info and sessions on mount
    // Only load history if session_id is in URL
    const requests = [
      fetch(`${API_BASE_URL}/auth/me`, { credentials: 'include' }),
      fetch(`${API_BASE_URL}/api/sessions`, { credentials: 'include' })
    ]

    // Only fetch history if there's a session ID in URL
    if (sessionIdFromUrl) {
      requests.push(fetch(`${API_BASE_URL}/api/history?session_id=${sessionIdFromUrl}`, { credentials: 'include' }))
    }

    Promise.all(requests)
      .then((responses) => {
        if (responses.some(res => res.status === 401)) {
          window.location.href = `${API_BASE_URL}/auth/login`
          return [null, null, null]
        }
        return Promise.all(responses.map(res => res.json()))
      })
      .then((results) => {
        const [userData, sessionsData, historyData] = results

        if (userData) {
          setUser(userData)
        }
        if (sessionsData && sessionsData.sessions) {
          setSessions(sessionsData.sessions)
        }
        if (historyData) {
          if (historyData.session_id) {
            setCurrentSessionId(historyData.session_id)
          }
          if (historyData.messages && historyData.messages.length > 0) {
            setMessages(historyData.messages)
          }
        }
      })
      .catch(err => console.error('Failed to load data:', err))
  }, [])

  useEffect(() => {
    // Connect to WebSocket
    const wsBaseUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    const wsUrl = `${wsBaseUrl}/api/ws/chat`

    console.log('Creating WebSocket connection to:', wsUrl)
    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected successfully')
      setWs(websocket)
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message received:', data)

      if (data.type === 'message_saved') {
        // Update current session ID
        setCurrentSessionId(data.session_id)
        // Update URL
        window.history.pushState({}, '', `?session=${data.session_id}`)
      } else if (data.type === 'assistant_response') {
        console.log('Assistant response data:', {
          response: data.response,
          responseLength: data.response?.length,
          metadata: data.metadata
        })
        // Add assistant message
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          metadata: data.metadata,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, assistantMessage])
        setLoading(false)

        // Refresh sessions list
        fetch(`${API_BASE_URL}/api/sessions`, { credentials: 'include' })
          .then(res => res.json())
          .then(data => setSessions(data.sessions || []))
          .catch(err => console.error('Failed to refresh sessions:', err))
      } else if (data.type === 'url_detected') {
        // Add system message for URL detection
        const systemMessage = {
          role: 'system',
          content: `🔗 Found URL: ${data.data.url}`,
          type: 'url_detection',
          metadata: { url: data.data.url, domain: data.data.domain },
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, systemMessage])
      } else if (data.type === 'pipeline_progress') {
        // Add or update pipeline progress (ephemeral - for real-time display)
        setPipelineEvents(prev => [...prev, data.data])

        // Also save completed steps as system messages so they persist
        if (data.data.status === 'completed') {
          const progressMessage = {
            role: 'system',
            content: data.data.message,
            type: 'pipeline_step',
            metadata: data.data.metadata,
            timestamp: new Date().toISOString()
          }
          setMessages(prev => [...prev, progressMessage])
        }
      } else if (data.type === 'document_complete') {
        // Add completion message and reload documents
        const systemMessage = {
          role: 'system',
          content: `✓ ${data.data.message}`,
          type: 'document_added',
          metadata: data.data.metadata,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, systemMessage])
        setPipelineEvents([])

        // Reload documents - use session_id from the event if available
        const sessionId = data.data.session_id || currentSessionId
        if (sessionId) {
          setTimeout(async () => {
            try {
              const response = await fetch(`${API_BASE_URL}/api/documents/session/${sessionId}`, {
                credentials: 'include'
              })
              const docsData = await response.json()
              setDocuments(docsData.documents || [])
              console.log('Documents reloaded:', docsData.documents?.length || 0)
            } catch (err) {
              console.error('Failed to reload documents:', err)
            }
          }, 500)
        }
      } else if (data.type === 'error') {
        // Add error message
        const errorMessage = {
          role: 'system',
          content: `❌ ${data.data.message}`,
          type: 'error',
          error: true,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMessage])
        setPipelineEvents([])
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setLoading(false)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setWs(null)
    }

    return () => {
      console.log('Cleaning up WebSocket connection')
      if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
        websocket.close()
      }
    }
  }, [])

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false)
      }
    }

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showDropdown])

  useEffect(() => {
    // Load documents when session changes
    if (currentSessionId) {
      fetch(`${API_BASE_URL}/api/documents/session/${currentSessionId}`, {
        credentials: 'include'
      })
        .then(res => res.json())
        .then(data => setDocuments(data.documents || []))
        .catch(err => console.error('Failed to load documents:', err))
    } else {
      setDocuments([])
    }
  }, [currentSessionId])

  useEffect(() => {
    // Track scroll position to show/hide scroll button
    const handleScroll = () => {
      if (!messagesContainerRef.current) return
      const { scrollTop, scrollHeight, clientHeight} = messagesContainerRef.current
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
      setShowScrollButton(!isNearBottom && messages.length > 0)
    }

    const container = messagesContainerRef.current
    if (container) {
      container.addEventListener('scroll', handleScroll)
      handleScroll() // Check initial state
    }

    return () => {
      if (container) {
        container.removeEventListener('scroll', handleScroll)
      }
    }
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async () => {
    console.log('sendMessage called', {
      input: input,
      inputTrimmed: input.trim(),
      loading: loading,
      ws: ws,
      wsReadyState: ws?.readyState,
      wsOpen: WebSocket.OPEN
    })

    if (!input.trim()) {
      console.log('Message is empty, not sending')
      return
    }

    if (loading) {
      console.log('Already loading, not sending')
      return
    }

    if (!ws) {
      console.error('WebSocket is not initialized')
      return
    }

    if (ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not open. State:', ws.readyState)
      const errorMsg = {
        role: 'system',
        content: '❌ Not connected to server. Please refresh the page.',
        type: 'error',
        error: true,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
      return
    }

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    console.log('Sending message:', userMessage)
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Send message via WebSocket
      const payload = {
        message: input,
        session_id: currentSessionId,
        system_prompt: systemPrompt
      }
      console.log('WebSocket payload:', payload)
      ws.send(JSON.stringify(payload))
      console.log('Message sent successfully')
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message}`,
        error: true,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      window.location.href = `${API_BASE_URL}/auth/login`
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const handleDocumentAdded = (document) => {
    setDocuments(prev => [...prev, document])
  }

  const handleDocumentRemoved = (docId) => {
    setDocuments(prev => prev.filter(d => d.id !== docId))
  }

  const loadDocuments = async () => {
    if (!currentSessionId) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/session/${currentSessionId}`, {
        credentials: 'include'
      })
      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const handleDocumentUpdated = () => {
    loadDocuments()
  }

  // Attach popover handlers
  const handleAttachClick = () => {
    setShowAttachPopover(!showAttachPopover)
  }

  const handleFileSelectFromPopover = () => {
    setShowAttachPopover(false)
    fileInputRef.current?.click()
  }

  const handleFileSelected = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Create a user message showing the upload
    const uploadMessage = {
      role: 'user',
      content: `[Uploaded: ${file.name}]`,
      type: 'file_upload',
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, uploadMessage])

    // Upload the file
    const formData = new FormData()
    formData.append('file', file)
    if (currentSessionId) {
      formData.append('session_id', currentSessionId)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        // Update session if created
        if (data.session_id && !currentSessionId) {
          setCurrentSessionId(data.session_id)
          window.history.pushState({}, '', `?session=${data.session_id}`)
        }
        // Document processing will be handled via WebSocket events
        handleDocumentAdded(data.document)
      } else {
        const error = await response.json()
        const errorMsg = {
          role: 'system',
          content: `❌ Upload failed: ${error.detail || 'Unknown error'}`,
          type: 'error',
          error: true,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMsg])
      }
    } catch (err) {
      console.error('Upload failed:', err)
      const errorMsg = {
        role: 'system',
        content: `❌ Upload failed: ${err.message}`,
        type: 'error',
        error: true,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
    }
  }

  const handleUrlSubmit = async (url) => {
    setShowAttachPopover(false)

    // Create a user message showing the URL
    const urlMessage = {
      role: 'user',
      content: `[Added URL: ${url}]`,
      type: 'url_add',
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, urlMessage])

    // Send URL to backend
    const formData = new FormData()
    formData.append('url', url)
    if (currentSessionId) {
      formData.append('session_id', currentSessionId)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/scrape-url`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        // Update session if created
        if (data.session_id && !currentSessionId) {
          setCurrentSessionId(data.session_id)
          window.history.pushState({}, '', `?session=${data.session_id}`)
        }
        // URL processing will be handled via WebSocket events
        handleDocumentAdded(data.document)
      } else {
        const error = await response.json()
        const errorMsg = {
          role: 'system',
          content: `❌ URL scrape failed: ${error.detail || 'Unknown error'}`,
          type: 'error',
          error: true,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMsg])
      }
    } catch (err) {
      console.error('URL scrape failed:', err)
      const errorMsg = {
        role: 'system',
        content: `❌ URL scrape failed: ${err.message}`,
        type: 'error',
        error: true,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
    }
  }

  const loadSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history?session_id=${sessionId}`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
        setCurrentSessionId(sessionId)
        // Update URL
        window.history.pushState({}, '', `?session=${sessionId}`)
      }
    } catch (error) {
      console.error('Failed to load session:', error)
    }
  }

  const newChat = () => {
    setMessages([])
    setCurrentSessionId(null)
    // Update URL to remove session param
    window.history.pushState({}, '', window.location.pathname)
  }

  const loadPipelines = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pipelines/`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        // API returns array directly, not wrapped in {pipelines: [...]}
        const pipelinesArray = Array.isArray(data) ? data : []
        setPipelines(pipelinesArray)
      }
    } catch (error) {
      console.error('Failed to load pipelines:', error)
    }
  }

  const viewPipelineJson = async (pipelineId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pipelines/${pipelineId}/json`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setPipelineJson(data.pipeline_json)
        setSelectedPipeline(pipelineId)
      }
    } catch (error) {
      console.error('Failed to load pipeline JSON:', error)
    }
  }

  const deletePipeline = async (pipelineId, pipelineName) => {
    if (!confirm(`Are you sure you want to delete pipeline "${pipelineName}"?`)) {
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/pipelines/${pipelineId}`, {
        method: 'DELETE',
        credentials: 'include'
      })
      if (response.ok) {
        alert('Pipeline deleted successfully')
        loadPipelines()
        if (selectedPipeline === pipelineId) {
          setSelectedPipeline(null)
          setPipelineJson(null)
        }
      } else {
        const error = await response.json()
        alert(`Failed to delete pipeline: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to delete pipeline:', error)
      alert('Failed to delete pipeline')
    }
  }

  const importPipelinesFromFilesystem = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pipelines/import-from-filesystem`, {
        method: 'POST',
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        alert(`Successfully imported ${data.imported_count} pipelines`)
        loadPipelines()
      } else {
        const error = await response.json()
        alert(`Failed to import pipelines: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to import pipelines:', error)
      alert('Failed to import pipelines')
    }
  }

  useEffect(() => {
    if (view === 'pipelines') {
      loadPipelines()
    }
  }, [view])

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <button
            className="sidebar-toggle"
            onClick={() => setShowSidebar(!showSidebar)}
          >
            ☰
          </button>
          <h1>IA Chat App</h1>
        </div>
        <div className="header-right">
          <button
            onClick={() => setView(view === 'chat' ? 'pipelines' : 'chat')}
            className="clear-btn"
          >
            {view === 'chat' ? 'Pipelines' : 'Chat'}
          </button>
          {view === 'chat' && (
            <button onClick={clearChat} className="clear-btn">Clear Chat</button>
          )}
          {user && (
            <div className="user-profile" ref={dropdownRef}>
              <button
                className="profile-btn"
                onClick={() => setShowDropdown(!showDropdown)}
              >
                {user.username || user.email}
              </button>
              {showDropdown && (
                <div className="dropdown">
                  <div className="dropdown-item">
                    <strong>{user.full_name || user.username}</strong>
                  </div>
                  <div className="dropdown-item">
                    {user.email}
                  </div>
                  <div className="dropdown-divider"></div>
                  <button className="dropdown-item logout-btn" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      <div className="main-content">
        {view === 'chat' && showSidebar && (
          <aside className="sidebar">
            <div className="sidebar-tabs">
              <button
                className={`sidebar-tab ${sidebarView === 'chats' ? 'active' : ''}`}
                onClick={() => setSidebarView('chats')}
              >
                💬 Chats
              </button>
              <button
                className={`sidebar-tab ${sidebarView === 'documents' ? 'active' : ''}`}
                onClick={() => setSidebarView('documents')}
              >
                📚 Library
              </button>
            </div>

            {sidebarView === 'chats' ? (
              <>
                <button className="new-chat-btn" onClick={newChat}>
                  + New Chat
                </button>
                <div className="sessions-list">
                  {sessions.map(session => (
                    <div
                      key={session.id}
                      className={`session-item ${currentSessionId === session.id ? 'active' : ''}`}
                      onClick={() => loadSession(session.id)}
                    >
                      <div className="session-title">{session.title}</div>
                      <div className="session-date">
                        {new Date(session.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="sidebar-library">
                <DocumentLibrary
                  apiBaseUrl={API_BASE_URL}
                  currentSessionId={currentSessionId}
                />
              </div>
            )}
          </aside>
        )}

        {view === 'chat' && (
          <div className="chat-container">
        <div className="messages" ref={messagesContainerRef}>
          {showScrollButton && (
            <button className="scroll-to-bottom" onClick={scrollToBottom}>
              ↓
            </button>
          )}
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Welcome to IA Chat App</h2>
              <p>Start chatting with the AI assistant!</p>
            </div>
          )}

          {messages.length > 0 && (
            <div className="session-stats">
              <span>Session Messages: {messages.length}</span>
              <span>
                Total Cost: ${messages
                  .filter(m => m.metadata?.cost_usd)
                  .reduce((sum, m) => sum + m.metadata.cost_usd, 0)
                  .toFixed(4)}
              </span>
              <span>
                Total Tokens: {messages
                  .filter(m => m.metadata?.tokens)
                  .reduce((sum, m) => sum + m.metadata.tokens, 0)
                  .toLocaleString()}
              </span>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role} ${msg.type || ''} ${msg.error ? 'error' : ''}`}>
              {msg.role !== 'system' && (
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
              )}
              <div className="message-bubble">
                {msg.role !== 'system' && (
                  <div className="message-header">
                    <strong>{msg.role === 'user' ? 'You' : 'Assistant'}</strong>
                    <span className="timestamp" title={new Date(msg.timestamp).toLocaleString()}>
                      {formatTimestamp(msg.timestamp)}
                    </span>
                  </div>
                )}
              <div className="message-content">
                {msg.role === 'system' ? (
                  <SystemMessage message={msg} />
                ) : msg.role === 'assistant' ? (
                  msg.metadata?.chunk_mapping && msg.metadata.chunk_mapping.length > 0 ? (
                    <CitationHighlighter
                      content={msg.content}
                      chunkMapping={msg.metadata.chunk_mapping}
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
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  )
                ) : (
                  <pre>{msg.content}</pre>
                )}
              </div>
              {msg.metadata && (
                <div className="message-metadata">
                  {msg.metadata.provider && (
                    <span>Provider: {msg.metadata.provider}</span>
                  )}
                  {msg.metadata.model && (
                    <span>Model: {msg.metadata.model}</span>
                  )}
                  {msg.metadata.tokens && (
                    <span>Tokens: {msg.metadata.tokens}</span>
                  )}
                  {msg.metadata.cost_usd !== undefined && (
                    <span>Cost: ${msg.metadata.cost_usd.toFixed(4)}</span>
                  )}
                  {msg.metadata.documents_used !== undefined && msg.metadata.documents_used > 0 && (
                    <span>📄 Documents: {msg.metadata.documents_used}</span>
                  )}
                  {msg.metadata.retrieved_docs && (
                    <span>Retrieved: {msg.metadata.retrieved_docs} docs</span>
                  )}
                </div>
              )}
              </div>
            </div>
          ))}

          {pipelineEvents.length > 0 && (
            <PipelineProgress events={pipelineEvents} />
          )}

          {loading && (
            <div className="message assistant loading">
              <div className="message-header">
                <strong>Assistant</strong>
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          {currentSessionId && (
            <DocumentList
              documents={documents}
              onDocumentRemoved={handleDocumentRemoved}
              onDocumentUpdated={handleDocumentUpdated}
              apiBaseUrl={API_BASE_URL}
            />
          )}

          <div className="system-prompt-section">
            <button
              className="system-prompt-toggle"
              onClick={() => setShowSystemPrompt(!showSystemPrompt)}
            >
              {showSystemPrompt ? '▼' : '▶'} System Prompt
            </button>
            {showSystemPrompt && (
              <textarea
                className="system-prompt-editor"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Enter system prompt to guide the assistant's behavior..."
                rows={2}
              />
            )}
          </div>

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            hidden
            onChange={handleFileSelected}
            accept=".pdf,.txt,.md,.docx"
          />

          <div className="input-container">
            <div className="input-wrapper">
              <div className="input-actions">
                {/* Attach button */}
                <button
                  className="attach-button"
                  onClick={handleAttachClick}
                  aria-label="Attach file or URL"
                >
                  📎
                </button>

                {/* Popover menu */}
                {showAttachPopover && (
                  <AttachPopover
                    onClose={() => setShowAttachPopover(false)}
                    onFileSelect={handleFileSelectFromPopover}
                    onUrlSubmit={handleUrlSubmit}
                  />
                )}
              </div>

              {/* Message input */}
              <textarea
                className="input-field"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Message..."
                disabled={loading}
                rows={1}
              />

              {/* Send button */}
              <button
                className="send-button"
                onClick={sendMessage}
                disabled={loading || !input.trim()}
              >
                ➤
              </button>
            </div>
          </div>
        </div>
        </div>
        )}

        {view === 'pipelines' && (
          <div className="pipelines-container">
            <div className="pipelines-header">
              <h2>Pipeline Management</h2>
              <button
                onClick={importPipelinesFromFilesystem}
                className="import-btn"
              >
                Import from Filesystem
              </button>
            </div>

            <div className="pipelines-content">
              <div className="pipelines-list">
                <h3>Pipelines</h3>
                {pipelines.length === 0 ? (
                  <p>No pipelines found. Click "Import from Filesystem" to load pipelines.</p>
                ) : (
                  <table className="pipelines-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Version</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pipelines.map(pipeline => (
                        <tr key={pipeline.id} className={selectedPipeline === pipeline.id ? 'selected' : ''}>
                          <td>
                            <strong>{pipeline.display_name}</strong>
                            <br />
                            <small>{pipeline.description}</small>
                          </td>
                          <td>{pipeline.version}</td>
                          <td>
                            <span className={`badge ${pipeline.is_system ? 'system' : 'user'}`}>
                              {pipeline.is_system ? 'System' : 'User'}
                            </span>
                          </td>
                          <td>
                            <span className={`badge ${pipeline.is_active ? 'active' : 'inactive'}`}>
                              {pipeline.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>
                            <button
                              onClick={() => viewPipelineJson(pipeline.id)}
                              className="action-btn view-btn"
                            >
                              View JSON
                            </button>
                            <button
                              onClick={() => deletePipeline(pipeline.id, pipeline.display_name)}
                              className="action-btn delete-btn"
                              title={pipeline.is_system ? "System pipeline - delete with caution" : "Delete pipeline"}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {pipelineJson && (
                <div className="pipeline-json-viewer">
                  <div className="json-viewer-header">
                    <h3>Pipeline JSON</h3>
                    <button
                      onClick={() => {
                        setSelectedPipeline(null)
                        setPipelineJson(null)
                      }}
                      className="close-btn"
                    >
                      ✕
                    </button>
                  </div>
                  <pre className="json-content">
                    {JSON.stringify(pipelineJson, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
