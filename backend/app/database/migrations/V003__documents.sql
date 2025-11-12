-- Documents Schema for Document Upload and URL Scraping
-- Compatible with PostgreSQL, MySQL, SQLite via NexusQL

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,

    -- Document metadata
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER,
    url TEXT,

    -- Extracted content
    content TEXT NOT NULL,
    content_preview VARCHAR(500),

    -- Processing metadata
    extracted_at TIMESTAMP NOT NULL,
    extraction_method VARCHAR(50),
    word_count INTEGER,
    char_count INTEGER,

    -- Status
    status VARCHAR(20) DEFAULT 'active',

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
