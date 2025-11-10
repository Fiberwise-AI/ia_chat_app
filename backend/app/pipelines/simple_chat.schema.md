# Simple Chat Pipeline - Schema Documentation

**Pipeline**: `simple_chat.json`
**Version**: 3.0.0
**Last Updated**: 2025-11-05

---

## Overview

LLM-powered chat with conversation history and conditional title generation for new conversations.

**Key Features**:
- Retrieves conversation history from database
- Includes history in LLM context for better responses
- Automatically generates titles for new conversations
- Branching Tree pattern execution (chat + conditional title generation)

**Execution Pattern**: Uses the [Branching Tree pattern](../../../../docs/PARALLEL_EXECUTION_PATTERNS.md#pattern-1-divergent-execution-branching-tree) where both `chat` (always) and `generate_title` (conditionally) execute after `fetch_history`, with no reconvergence point.

---

## Pipeline Parameters

Input parameters passed to the pipeline at runtime.

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `message` | `string` | ✅ Yes | User's chat message | `"How do I fix Python import errors?"` |
| `session_id` | `string` | ❌ No | Chat session ID (null for new chat) | `"abc-123-def-456"` or `null` |

---

## Pipeline Steps

### Step 1: `fetch_history`

**Purpose**: Retrieve conversation history from database

**Class**: `FetchChatHistoryStep`
**Module**: `app.pipeline_steps.fetch_chat_history_step`

#### Inputs

| Input | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `session_id` | `string` | `{parameters.session_id}` | ❌ No | Session ID to fetch history for |

#### Outputs

| Output | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `chat_history` | `array` | ✅ Yes | Array of message objects | `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]` |
| `message_count` | `integer` | ✅ Yes | Total messages in session | `5` |
| `is_first_message` | `boolean` | ✅ Yes | Whether this is first message | `true` or `false` |

#### Behavior

- If `session_id` is `null`: Returns empty history, `message_count=0`, `is_first_message=true`
- If `session_id` exists: Queries database, returns full history

---

### Step 2: `chat`

**Purpose**: Generate LLM response with conversation context

**Class**: `SimpleChatStep`
**Module**: `app.pipeline_steps.simple_chat_step`

**Configuration**:
```json
{
    "temperature": 0.7,
    "max_tokens": 500
}
```

#### Inputs

| Input | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `message` | `string` | `{parameters.message}` | ✅ Yes | User's current message |
| `chat_history` | `array` | `{steps.fetch_history.output.chat_history}` | ✅ Yes | Previous conversation messages |

#### Outputs

| Output | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `response` | `string` | ✅ Yes | LLM-generated response | `"To fix Python import errors, you can..."` |
| `metadata` | `object` | ✅ Yes | Response metadata | `{"provider": "openai", "model": "gpt-4o", "tokens": 150, "cost_usd": 0.002}` |

#### Metadata Schema

```typescript
{
    provider: string;      // "openai", "anthropic", "google"
    model: string;         // "gpt-4o", "claude-sonnet-4-5", etc.
    tokens: number;        // Total tokens used
    cost_usd: number;      // Estimated cost in USD
}
```

---

### Step 3: `generate_title`

**Purpose**: Generate concise title for new conversations

**Class**: `TitleGenerationStep`
**Module**: `app.pipeline_steps.title_generation_step`

**Configuration**:
```json
{
    "temperature": 0.3,
    "max_tokens": 20
}
```

**Execution Condition**: Only runs if `fetch_history.is_first_message == true`

#### Inputs

| Input | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `message` | `string` | `{parameters.message}` | ✅ Yes | User's first message |

#### Outputs

| Output | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `title` | `string` | ✅ Yes | LLM-generated title (3-6 words) | `"Python Import Errors"` |
| `title_metadata` | `object` | ✅ Yes | Title generation metadata | `{"model": "gpt-4o", "tokens": 15}` |

#### Title Format

- **Length**: 3-6 words (max 60 characters)
- **Style**: Descriptive, captures main topic
- **Examples**:
  - `"Python Import Errors"`
  - `"React Component Optimization"`
  - `"SQL Query Performance"`

---

## Data Flow

### First Message Flow

```
INPUT:
{
    "message": "How do I fix Python import errors?",
    "session_id": null
}

↓

STEP: fetch_history
OUTPUT: {
    "chat_history": [],
    "message_count": 0,
    "is_first_message": true
}

↓  ↓ (Parallel)

STEP: chat                          STEP: generate_title
INPUT: {                            INPUT: {
    "message": "How do I...",           "message": "How do I..."
    "chat_history": []              }
}
OUTPUT: {                           OUTPUT: {
    "response": "To fix...",            "title": "Python Import Errors",
    "metadata": {...}                   "title_metadata": {...}
}                                   }

↓

FINAL OUTPUT:
{
    "fetch_history": {...},
    "chat": {
        "response": "To fix import errors...",
        "metadata": {"provider": "openai", ...}
    },
    "generate_title": {
        "title": "Python Import Errors",
        "title_metadata": {...}
    }
}
```

### Second Message Flow

```
INPUT:
{
    "message": "What about circular imports?",
    "session_id": "abc-123"
}

↓

STEP: fetch_history
QUERY: SELECT * FROM chat_messages WHERE session_id = 'abc-123'
OUTPUT: {
    "chat_history": [
        {"role": "user", "content": "How do I fix..."},
        {"role": "assistant", "content": "To fix import errors..."}
    ],
    "message_count": 2,
    "is_first_message": false
}

↓

STEP: chat
INPUT: {
    "message": "What about circular imports?",
    "chat_history": [...]  // Full history
}
OUTPUT: {
    "response": "Circular imports occur when...",
    "metadata": {...}
}

STEP: generate_title
❌ SKIPPED (is_first_message == false)

↓

FINAL OUTPUT:
{
    "fetch_history": {...},
    "chat": {
        "response": "Circular imports occur when...",
        "metadata": {...}
    }
    // No "generate_title" - step was skipped
}
```

---

## Conditional Execution

### Condition: Title Generation

**Path**: `fetch_history` → `generate_title`

**Condition**:
```json
{
    "type": "expression",
    "config": {
        "source": "fetch_history.is_first_message",
        "operator": "equals",
        "value": true
    }
}
```

**Evaluation**:
- **Passes**: When `fetch_history.is_first_message == true` (new conversation)
- **Fails**: When `fetch_history.is_first_message == false` (existing conversation)

**Result**:
- ✅ Passes → `generate_title` step executes
- ❌ Fails → `generate_title` step skips, no title in output

---

## Error Handling

### Missing LLM Service

**Step**: `chat`, `generate_title`

**Error**: `RuntimeError: LLM service not available`

**Cause**: LLM provider not registered in services registry

**Resolution**: Ensure `llm_provider` is registered in `main.py`:
```python
services_registry.register('llm_provider', llm_service)
```

### Missing Database Manager

**Step**: `fetch_history`

**Error**: `RuntimeError: Database manager not available`

**Cause**: Database manager not registered in services registry

**Resolution**: Ensure `db_manager` is registered in `main.py`:
```python
services_registry.register('db_manager', db_manager)
```

### Invalid Session ID

**Step**: `fetch_history`

**Behavior**: Returns empty history (treated as new conversation)

**No error thrown** - graceful degradation

---

## Performance

### Parallel Execution

- **First message**: `chat` and `generate_title` run simultaneously
- **Time saved**: ~1-2 seconds (title generation doesn't block response)

### Token Usage

| Step | Temperature | Max Tokens | Typical Usage |
|------|------------|------------|---------------|
| `chat` | 0.7 | 500 | 150-300 tokens |
| `generate_title` | 0.3 | 20 | 10-15 tokens |

### Cost Estimate (GPT-4o)

- **Chat response**: ~$0.002-0.005 per message
- **Title generation**: ~$0.001 (one-time, first message only)

---

## Testing

### Test Case 1: First Message

**Input**:
```json
{
    "message": "How do I fix Python import errors?",
    "session_id": null
}
```

**Expected Output**:
```json
{
    "chat": {
        "response": "To fix Python import errors...",
        "metadata": {"provider": "openai", ...}
    },
    "generate_title": {
        "title": "Python Import Errors"
    }
}
```

**Assertions**:
- ✅ `chat.response` is not empty
- ✅ `generate_title.title` exists
- ✅ `generate_title.title` length ≤ 60 characters

### Test Case 2: Second Message

**Input**:
```json
{
    "message": "What about circular imports?",
    "session_id": "abc-123"
}
```

**Expected Output**:
```json
{
    "fetch_history": {
        "chat_history": [...],  // Previous messages
        "is_first_message": false
    },
    "chat": {
        "response": "Circular imports occur when..."
    }
    // No "generate_title" key
}
```

**Assertions**:
- ✅ `chat.response` is not empty
- ✅ `generate_title` does NOT exist in output
- ✅ `fetch_history.chat_history` is not empty

---

## Modification Guide

### Add System Message

**File**: `simple_chat_step.py`

```python
messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    *chat_history,
    {"role": "user", "content": message}
]
```

### Limit History Length

**File**: `fetch_chat_history_step.py`

```python
messages = db_manager.fetch_all(
    """
    SELECT role, content FROM chat_messages
    WHERE session_id = :session_id
    ORDER BY created_at DESC
    LIMIT 20  -- Last 20 messages
    """,
    {"session_id": session_id}
)
messages.reverse()  # Oldest first
```

### Change Title Style

**File**: `title_generation_step.py`

```python
title_prompt = f"""Generate an emoji + short title (example: "🐍 Python Imports") for:

"{message}"

Format: [emoji] [2-4 words]"""
```

---

## Version History

### v3.0.0 (2025-11-05)
- ✅ Added proper input/output schemas
- ✅ Added conversation history retrieval
- ✅ Added conditional title generation
- ✅ Implemented parallel execution

### v2.0.0 (2025-11-05)
- ❌ Deprecated: Used `is_first_message` flag (replaced with session-based approach)

### v1.0.0 (Initial)
- Single step chat without history
- No title generation

---

## Related Documentation

- [Pipeline Implementation Guide](../../CHAT_HISTORY_AND_TITLE_IMPLEMENTATION.md)
- [Branching Tree Pattern](../../../../docs/PARALLEL_EXECUTION_PATTERNS.md) - Execution pattern used by this pipeline
- [Parallel Execution Bug Fix](../../../../docs/PARALLEL_EXECUTION_FIX_SUMMARY.md) - Critical bug this pipeline helped discover
- [FetchChatHistoryStep](../pipeline_steps/fetch_chat_history_step.py)
- [SimpleChatStep](../pipeline_steps/simple_chat_step.py)
- [TitleGenerationStep](../pipeline_steps/title_generation_step.py)

## Notes

This pipeline was instrumental in discovering a critical bug in ia_modules parallel execution (2025-11-06). The bug caused only the first branch to execute when using the Branching Tree pattern (terminal branches with no outgoing paths). See [PARALLEL_EXECUTION_FIX_SUMMARY.md](../../../../docs/PARALLEL_EXECUTION_FIX_SUMMARY.md) for details.
