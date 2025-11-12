# IA Chat App

A production-ready chat application with AI assistant capabilities, conversation management, and dynamic pipeline orchestration.

## Features

### 🎨 Modern Chat Experience
- **Markdown Rendering** - Full markdown support with syntax highlighting (GitHub Dark theme)
- **Code Copy Buttons** - One-click copying with language detection and visual feedback
- **Smart Timestamps** - Relative time display ("Just now", "5m ago", "2h ago")
- **Chat Avatars** - Emoji avatars for users (👤) and assistant (🤖)
- **Scroll Management** - Auto-scroll with floating "scroll to bottom" button
- **Typing Indicators** - Visual feedback during AI response generation

### 🎛️ Advanced Controls
- **System Prompts** - Customize AI behavior with collapsible system prompt editor
- **Session Management** - Persistent conversation history with session switching
- **Auto-Generated Titles** - AI creates descriptive titles (first message only)
- **Pipeline Management** - View, import, and manage AI processing pipelines

### 💰 Transparency & Tracking
- **Cost Tracking** - Real-time display of LLM costs per message and session totals
- **Token Counting** - Monitor token usage across conversations
- **Metadata Display** - View provider, model, tokens, and cost for each response

### ⚡ Performance & Reliability
- **Smart Context** - Automatic 20-message history limit to prevent token overflow
- **WebSocket Real-time** - Instant message delivery and updates
- **Conditional Pipelines** - Branching tree pattern for efficient processing
- **Database Migrations** - Automated schema management with NexusQL

### 🔐 Authentication
- **Google OAuth** - Secure authentication via Google Sign-In
- **Session Management** - Cookie-based sessions with ia_auth_sessions
- **User Profiles** - Dropdown menu with user info and logout

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

### Smart Conversation Management
- **Smart Context Window**: Automatic 20-message history limit prevents token overflow
- **Persistent Storage**: All messages stored in SQLite/PostgreSQL database
- **Context-Aware AI**: Full conversation history provided to LLM for better responses
- **Efficient Retrieval**: SQL query with DESC + LIMIT + reverse for optimal performance

### Conditional Title Generation
- **Cost-Saving**: Only runs on first message using branching tree pattern
- **Automatic**: AI generates concise 3-6 word descriptive titles
- **No Duplication**: Condition prevents re-generation on subsequent messages
- **Pipeline-Based**: Declarative JSON configuration, not hardcoded logic

### System Prompt Customization
- **Collapsible UI**: Toggle system prompt editor to save space
- **Per-Message**: System prompt passed with each request
- **Flexible**: Customize AI behavior without code changes
- **Pipeline Integration**: Seamlessly integrated into chat pipeline

### Modern UX Features
- **Markdown Rendering**: Full GitHub-flavored markdown with tables, lists, quotes
- **Syntax Highlighting**: Code blocks with GitHub Dark theme via rehype-highlight
- **Code Copying**: One-click copy with language badges and visual feedback
- **Smart Timestamps**: Relative time ("5m ago") with hover for full timestamp
- **Chat Bubbles**: Modern design with emoji avatars and flex layout
- **Scroll Button**: Floating button appears when scrolled up from bottom

### Cost & Performance Tracking
- **Per-Message Costs**: Display LLM API costs for each response
- **Session Totals**: Aggregate cost and token counts for entire conversation
- **Metadata Display**: Show provider, model, tokens, and cost
- **Real-time Updates**: Session stats update as conversation progresses

