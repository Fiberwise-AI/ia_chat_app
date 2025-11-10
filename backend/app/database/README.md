# Database Schema for IA Chat App

This directory contains SQL migration files for the chat application.

## Schema Overview

### Auth Tables (from ia_auth_sessions)
- `users` - User accounts with authentication
- `sessions` - Active user sessions

### Chat Tables (app-specific)
- `chat_sessions` - Chat conversation sessions
- `chat_messages` - Individual messages in conversations
- `pipeline_executions` - Track pipeline runs (optional)

## Schema Diagram

```
users (from ia_auth_sessions)
  ↓ FK
  ├─→ chat_sessions
  │     ↓ FK
  │     └─→ chat_messages
  │
  └─→ pipeline_executions
```

## Tables

### chat_sessions
Stores chat conversation sessions for each user.

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| user_id | VARCHAR(36) | FK to users.id |
| title | VARCHAR(255) | Session title/summary |
| created_at | TIMESTAMP | When session started |
| updated_at | TIMESTAMP | Last message time |

### chat_messages
Individual messages within a chat session.

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| session_id | VARCHAR(36) | FK to chat_sessions.id |
| role | VARCHAR(20) | 'user', 'assistant', or 'system' |
| content | TEXT | Message content |
| model | VARCHAR(100) | LLM model used (if assistant) |
| tokens_used | INTEGER | Token count |
| metadata | TEXT | JSON metadata |
| created_at | TIMESTAMP | Message timestamp |

### pipeline_executions
Tracks pipeline execution history (optional).

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| user_id | VARCHAR(36) | FK to users.id |
| pipeline_name | VARCHAR(100) | Pipeline identifier |
| input_data | TEXT | JSON input |
| output_data | TEXT | JSON output |
| status | VARCHAR(20) | 'running', 'completed', 'failed' |
| error_message | TEXT | Error details if failed |
| duration_ms | INTEGER | Execution time |
| created_at | TIMESTAMP | Start time |
| completed_at | TIMESTAMP | End time |

## Migrations

Migrations are numbered with prefix `V###__description.sql`:

- `V001__chat_history.sql` - Initial chat schema

### Adding New Migrations

1. Create a new file: `V002__your_change.sql`
2. Use `CREATE TABLE IF NOT EXISTS` for safety
3. Test with all supported databases (PostgreSQL, MySQL, SQLite)
4. Restart the app to apply

### Example Migration

```sql
-- V002__add_chat_folders.sql

CREATE TABLE IF NOT EXISTS chat_folders (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_folders_user_id ON chat_folders(user_id);
```

## Initialization

The schema is initialized automatically on app startup:

```python
# In main.py lifespan
from ia_auth_sessions import initialize_database
from database import initialize_chat_schema

# 1. Auth tables first
await initialize_database(db_manager)

# 2. Chat tables second
await initialize_chat_schema(db_manager)
```

## Testing

For testing, you can drop and recreate tables:

```python
from database import drop_chat_tables, initialize_chat_schema

# Clean slate
await drop_chat_tables(db_manager)
await initialize_chat_schema(db_manager)
```

## Database Support

All SQL is written to be compatible with:
- PostgreSQL
- MySQL
- SQLite

Notes:
- Use `VARCHAR` not `TEXT` for indexed columns
- Use `TEXT` for JSON (cross-DB compatible)
- Use `TIMESTAMP` not `DATETIME`
- Always use `IF NOT EXISTS` for idempotency
