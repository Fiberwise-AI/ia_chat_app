-- Pipeline Versions (history for pipeline definitions)
CREATE TABLE IF NOT EXISTS pipeline_versions (
    id VARCHAR(36) PRIMARY KEY,
    pipeline_id VARCHAR(36) NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    pipeline_json TEXT NOT NULL,
    git_commit_sha VARCHAR(64),
    imported_by VARCHAR(36),
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(32) DEFAULT 'filesystem'
);

CREATE INDEX IF NOT EXISTS idx_pipeline_versions_pipeline_name ON pipeline_versions(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_versions_imported_at ON pipeline_versions(imported_at);
