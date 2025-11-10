import { useState, useEffect, useRef } from 'react'
import './App.css'
import { API_BASE_URL } from './config'

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
  const messagesEndRef = useRef(null)
  const dropdownRef = useRef(null)

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

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected')
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
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setLoading(false)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    setWs(websocket)

    return () => {
      websocket.close()
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

  const sendMessage = async () => {
    if (!input.trim() || loading || !ws || ws.readyState !== WebSocket.OPEN) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Send message via WebSocket
      ws.send(JSON.stringify({
        message: input,
        session_id: currentSessionId
      }))
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
          </aside>
        )}

        {view === 'chat' && (
          <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Welcome to IA Chat App</h2>
              <p>Start chatting with the AI assistant!</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role} ${msg.error ? 'error' : ''}`}>
              <div className="message-header">
                <strong>{msg.role === 'user' ? 'You' : 'Assistant'}</strong>
                <span className="timestamp">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="message-content">
                <pre>{msg.content}</pre>
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
                  {msg.metadata.retrieved_docs && (
                    <span>Retrieved: {msg.metadata.retrieved_docs} docs</span>
                  )}
                </div>
              )}
            </div>
          ))}

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
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            disabled={loading}
            rows={3}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            {loading ? 'Sending...' : 'Send'}
          </button>
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
