# IA Chat App

A production-ready chat application with AI assistant capabilities, conversation management, and dynamic pipeline orchestration.

## Features

### User Features
- **Account Management** - Create accounts, login with session-based authentication
- **AI Chat** - Converse with multiple AI models (OpenAI, Anthropic, Google)
- **Conversation History** - Full chat history stored and retrieved for context-aware responses
- **Auto-Generated Titles** - AI automatically creates descriptive titles for new conversations
- **Session Management** - View all past conversations, switch between chats
- **Pipeline Management** - View, import, and manage AI processing pipelines

### Chat Features
- **Context-Aware Responses** - AI sees full conversation history for better answers
- **Real-time WebSocket Communication** - Instant message delivery
- **Multiple Sessions** - Maintain separate conversation threads
- **Session Persistence** - Conversations saved to database

## How It Works

The app uses the **ia_modules pipeline system** to process conversations:

### Pipeline Architecture

**Pipelines** = Configurable workflows that define how messages are processed
- Stored as JSON configuration files, not hardcoded
- Steps execute sequentially or in parallel based on conditions
- Can branch based on runtime data (e.g., first message vs. subsequent messages)
- Support conditional execution, parallel processing, and data flow between steps

**Example: Simple Chat Pipeline**
```
Input (message, session_id)
    ↓
[fetch_history] - Query database for conversation history
    ↓
    ├─→ [chat] - Generate AI response (always runs)
    └─→ [generate_title] - Create title (only if first message)
    ↓
Output (response, title?)
```

### Key Technologies
- **Backend**: FastAPI with async/await for high performance
- **Frontend**: React with WebSocket for real-time updates
- **Database**: PostgreSQL with migration support
- **Authentication**: Cookie-based sessions (ia_auth_sessions)
- **AI Integration**: Multiple LLM providers via ia_modules
- **Pipeline Engine**: ia_modules GraphPipelineRunner with conditional routing

## Project Structure

```
ia_chat_app/
├── backend/
│   ├── app/
│   │   ├── api/                    # REST and WebSocket endpoints
│   │   │   ├── routes.py          # Chat endpoints
│   │   │   └── pipeline_routes.py # Pipeline management API
│   │   ├── pipeline_steps/        # Custom pipeline step implementations
│   │   │   ├── fetch_chat_history_step.py
│   │   │   ├── simple_chat_step.py
│   │   │   └── title_generation_step.py
│   │   ├── pipelines/             # Pipeline JSON configurations
│   │   │   └── simple_chat.json   # Main chat pipeline
│   │   ├── services/              # Business logic
│   │   │   └── chat_service.py    # Chat orchestration
│   │   ├── core/                  # Core utilities
│   │   │   └── pipeline_cache.py  # In-memory pipeline cache
│   │   └── database/              # Database migrations
│   └── main.py                    # FastAPI application entry point
├── frontend/
│   └── src/
│       ├── App.jsx                # Main React component (chat + pipelines)
│       ├── App.css                # Styling
│       └── config.js              # API configuration
└── docker-compose.yml             # Docker deployment configuration
```

## Documentation

\

### Feature Documentation
- [Chat History & Title Implementation](CHAT_HISTORY_AND_TITLE_IMPLEMENTATION.md) - How conversation history and title generation work

## Quick Start

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Access the app
open http://localhost:5174
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Environment Configuration

Create a `.env` file in the project root:

```env
# Ports
BACKEND_PORT=8091
FRONTEND_PORT=5174

# Database
DATABASE_URL=postgresql://ia_user:ia_password@localhost:5433/ia_chat_app

# Authentication
AUTH_SECRET_KEY=your-secret-key-here
AUTH_SESSION_MAX_AGE=604800

# AI Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

## Pipeline System

### What are Pipelines?

Pipelines are JSON configuration files that define multi-step AI workflows:

```json
{
  "name": "Simple Chat Pipeline",
  "steps": [
    {"id": "fetch_history", "step_class": "FetchChatHistoryStep", ...},
    {"id": "chat", "step_class": "SimpleChatStep", ...},
    {"id": "generate_title", "step_class": "TitleGenerationStep", ...}
  ],
  "flow": {
    "start_at": "fetch_history",
    "paths": [
      {"from": "fetch_history", "to": "chat", "condition": {"type": "always"}},
      {"from": "fetch_history", "to": "generate_title",
       "condition": {"type": "expression", "config": {...}}}
    ]
  }
}
```

## Key Features Explained

### Conversation History
- All messages stored in PostgreSQL database
- Retrieved on each request to provide context to AI
- Enables multi-turn conversations with memory

### Automatic Title Generation
- Uses conditional pipeline execution
- Only runs on first message of conversation
- AI generates concise 3-6 word titles
- Updates session title in database automatically

