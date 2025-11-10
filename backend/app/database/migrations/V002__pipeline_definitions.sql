-- Pipeline Definitions Schema
-- Stores pipeline JSON configurations in database for dynamic management

CREATE TABLE IF NOT EXISTS pipeline_definitions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL,
    pipeline_json TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_definitions_name ON pipeline_definitions(name);
CREATE INDEX IF NOT EXISTS idx_pipeline_definitions_is_active ON pipeline_definitions(is_active);
CREATE INDEX IF NOT EXISTS idx_pipeline_definitions_created_at ON pipeline_definitions(created_at);
