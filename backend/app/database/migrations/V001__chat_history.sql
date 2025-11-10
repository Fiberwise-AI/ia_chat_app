-- Chat History Schema for IA Chat App
-- Compatible with PostgreSQL, MySQL, SQLite via NexusQL

-- Chat Sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at);

-- Chat Messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    metadata TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

-- Pipeline Executions (optional - tracks pipeline runs)
CREATE TABLE IF NOT EXISTS pipeline_executions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    input_data TEXT,
    output_data TEXT,
    status VARCHAR(20) CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pipeline_executions_user_id ON pipeline_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_status ON pipeline_executions(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_created_at ON pipeline_executions(created_at);
