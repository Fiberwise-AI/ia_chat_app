# IA Chat App - Development Roadmap

**Created**: 2025-11-06
**Last Updated**: 2025-11-10
**Status**: Active Development

---

## 📈 Progress Summary (Nov 10, 2025)

**Completed Today**: 20 major features - DOCUMENT MANAGEMENT SYSTEM COMPLETE! 🎉🎉

- ✅ **Phase 1 (Testing)**: Manual tests + branching tree unit tests
- ✅ **Phase 2 (UX) - COMPLETE**: All 4 sub-phases done!
  - Markdown rendering with syntax highlighting
  - Code copy buttons with language badges
  - Typing indicators (verified working)
  - Chat bubbles with avatars, timestamps, scroll button
- ✅ **Phase 3 (Quick Wins)**: System prompts + history limits + cost tracking
- ✅ **Phase 6.2 (Document Processing) - COMPLETE**: File upload & URL scraping!
- ✅ **Phase 6.2.1 (RAG Citations) - COMPLETE**: Source attribution & citations!
- ✅ **Phase 6.2.2 (Selective Inclusion) - COMPLETE**: Control which documents are used!
- ✅ **Phase 6.2.3 (Document Library) - COMPLETE**: Global library with search & organization!
- ✅ **Phase 6.2.4 (Collections & Tags) - COMPLETE**: Organize with collections, tags, folders!

**Key Improvements**:
- 🎨 Full markdown support with GitHub Dark theme
- 📋 One-click code copying with language detection
- 💰 Real-time cost and token tracking
- 🎛️ Collapsible system prompt editor
- ⚡ Smart 20-message context window
- 👤 Modern chat bubbles with emoji avatars
- ⏰ Relative timestamps ("5m ago", "2h ago")
- 🔽 Floating scroll-to-bottom button
- 📎 **File upload** (PDF, TXT, MD, DOCX)
- 🌐 **URL scraping** for web content
- 📄 **Document context** in LLM conversations
- 🔗 **RAG Citations**: Inline citations with hover tooltips and source attribution
- ☑️ **Selective Inclusion**: Checkbox controls for which documents AI uses
- 📚 **Document Library**: Global library across all chats with search
- 🗂️ **Collections**: Group related documents with colors
- 🏷️ **Tags & Folders**: Full organization system for power users

---

## ✅ Completed

### Phase 0: Foundation (Nov 5-6, 2025)
- [x] Chat with conversation history
- [x] Conditional title generation (first message only)
- [x] Pipeline management UI
- [x] PostgreSQL database with migrations
- [x] Google OAuth authentication
- [x] WebSocket real-time chat
- [x] **CRITICAL**: Fixed parallel execution bug in ia_modules
- [x] Comprehensive parallel execution documentation

### Recent Completions (Nov 10, 2025)
- [x] **Phase 1.1**: Manual title generation testing
- [x] **Phase 1.2**: Branching tree pattern unit tests (4 tests passing)
- [x] **Phase 2 (COMPLETE)**: All UX improvements
  - [x] **Phase 2.1**: Full markdown rendering with syntax highlighting
  - [x] **Phase 2.2**: Code block copy buttons with language detection
  - [x] **Phase 2.3**: Typing indicators (verified existing implementation)
  - [x] **Phase 2.4**: Chat bubbles, avatars, smart timestamps, scroll button
- [x] **Phase 3.1**: System prompt customization UI
- [x] **Phase 3.2**: Chat history limited to 20 messages
- [x] **Phase 3.3**: Cost tracking and session statistics
- [x] **Phase 6.2 (COMPLETE)**: Document Processing - File Upload & URL Scraping
  - [x] Database schema for documents table
  - [x] File upload endpoint (PDF, TXT, MD, DOCX - max 10MB)
  - [x] URL scraping endpoint with BeautifulSoup
  - [x] FetchDocumentsStep pipeline integration
  - [x] Document context in SimpleChatStep
  - [x] DocumentUpload React component
  - [x] DocumentList React component with preview
  - [x] Backend dependencies installed (pypdf, python-docx, beautifulsoup4, httpx)

---

## 🎯 Active Development

### Phase 1: Quality & Testing (Priority: HIGH)
**Goal**: Ensure reliability and prevent regressions

#### 1.1 Test the Title Generation End-to-End ✅
- [x] Manual test: Create new chat
- [x] Verify title appears in sidebar
- [x] Verify title doesn't regenerate on second message
- [x] Check database has correct title
- [x] Test with various message types

**Completed**: 2025-11-10
**Status**: ✅ All manual tests passed

#### 1.2 Write Branching Tree Pattern Tests ✅
- [x] Create `ia_modules/tests/unit/test_branching_tree_pattern.py`
- [x] Test terminal branches both execute
- [x] Test conditional branching with expression
- [x] Test exact step count assertions
- [x] Run full test suite

**Completed**: 2025-11-10
**Status**: ✅ All 4 tests PASSED in 0.63s
**Files Created**:
- `ia_modules/tests/unit/test_branching_tree_pattern.py`
- `ia_modules/tests/pipelines/branching_tree_pipeline/steps/test_steps.py`

#### 1.3 Add Chat App Integration Tests
- [ ] Create `ia_chat_app/tests/test_title_generation.py`
- [ ] Test first message flow
- [ ] Test second message flow
- [ ] Test database persistence
- [ ] Mock LLM responses for speed

**Estimated Time**: 1 hour
**Blockers**: Need pytest setup in ia_chat_app

---

### Phase 2: UX Improvements (Priority: HIGH)
**Goal**: Make the app actually enjoyable to use

#### 2.1 Markdown Rendering ✅
- [x] Install `react-markdown` with plugins
- [x] Render assistant messages as markdown
- [x] Add code syntax highlighting with `rehype-highlight`
- [x] Style markdown elements (headings, lists, blockquotes, tables)
- [x] Comprehensive CSS styling for all markdown elements

**Completed**: 2025-11-10
**Status**: ✅ Full markdown support with GitHub Dark syntax theme

#### 2.2 Code Block Features ✅
- [x] Copy-to-clipboard button for code blocks
- [x] Language detection and display
- [x] Custom CodeBlock component with header
- [x] Visual feedback on copy (checkmark animation)

**Completed**: 2025-11-10
**Status**: ✅ Code blocks have copy button with language badge

#### 2.3 Enhanced Chat UI ✅
- [x] Typing indicator during generation (already implemented)
- [ ] Regenerate response button (deferred)
- [ ] Edit message and regenerate (deferred)
- [ ] Delete message (deferred)
- [ ] Message actions menu (deferred - future enhancement)

**Completed**: 2025-11-10
**Status**: ✅ Typing indicator verified working
**Note**: Advanced features (regenerate, edit, delete) deferred to future phase

#### 2.4 Better Message Display ✅
- [x] User avatars/icons (emoji avatars)
- [x] Timestamp formatting (relative time: "5m ago", "2h ago")
- [x] Message status indicators (loading state with typing animation)
- [x] Scroll to bottom button when not at bottom
- [ ] Streaming response display (deferred - requires backend changes)

**Completed**: 2025-11-10
**Status**: ✅ Modern chat bubble design with avatars and smart timestamps
**Files Modified**:
- `App.jsx` - Added formatTimestamp helper, avatars, scroll tracking
- `App.css` - New message bubble layout with flex, avatars, scroll button

---

### Phase 3: Quick Wins (Priority: MEDIUM)
**Goal**: Small improvements with immediate impact

#### 3.1 System Prompts ✅
- [x] Add system message parameter to chat pipeline
- [x] Update SimpleChatStep to use system prompt
- [x] Create UI with collapsible system prompt editor
- [x] System prompt persists during session

**Completed**: 2025-11-10
**Status**: ✅ Users can customize system prompts per message
**Files Modified**:
- `simple_chat_step.py` - accepts system_prompt parameter
- `simple_chat.json` - added system_prompt parameter
- `App.jsx` - collapsible system prompt UI

#### 3.2 Chat History Limits ✅
- [x] Limit to last 20 messages to prevent token overflow
- [x] Modified SQL query with DESC + LIMIT + reverse

**Completed**: 2025-11-10
**Status**: ✅ Chat history limited to 20 messages
**Files Modified**: `fetch_chat_history_step.py`

#### 3.3 Cost Tracking ✅
- [x] Display cost per message in metadata
- [x] Session total cost summary
- [x] Total tokens counter
- [x] Message count display

**Completed**: 2025-11-10
**Status**: ✅ Session stats bar shows cost, tokens, and message count
**Files Modified**: `App.jsx`, `App.css`

#### 3.4 Export Chat
- [ ] Export session as markdown
- [ ] Export as JSON
- [ ] Export as PDF (stretch)
- [ ] Share link to session

**Estimated Time**: 1-2 hours
**Blockers**: None

---

### Phase 4: Advanced Features (Priority: MEDIUM)
**Goal**: Add power-user features

#### 4.1 Human-in-the-Loop (HITL)
- [ ] "Fact-check" button on responses
- [ ] Approve/reject/edit workflow
- [ ] Track verified responses
- [ ] Learn from human feedback
- [ ] Export feedback dataset

**Estimated Time**: 3-4 hours
**Reference**: ia_modules HITL support

#### 4.2 Model Selection
- [ ] Choose model per message (GPT-4, Claude, Gemini)
- [ ] Default model setting
- [ ] Compare responses from multiple models
- [ ] Model switching mid-conversation

**Estimated Time**: 2 hours
**Blockers**: Need LiteLLM config

#### 4.3 Prompt Templates
- [ ] Save common prompts
- [ ] Prompt library
- [ ] Variables in prompts
- [ ] Share prompts with team

**Estimated Time**: 2-3 hours
**Blockers**: None

#### 4.4 Conversation Branching
- [ ] Branch from any message
- [ ] Explore alternative responses
- [ ] Compare branches side-by-side
- [ ] Merge branches

**Estimated Time**: 4-5 hours (complex)
**Blockers**: Database schema changes

---

### Phase 5: Pipeline Patterns (Priority: MEDIUM)
**Goal**: Build example pipelines showcasing ia_modules features

#### 5.1 RAG Pipeline
- [ ] Search knowledge base
- [ ] Retrieve relevant docs
- [ ] Generate response with citations
- [ ] Test with Wikipedia data

**Estimated Time**: 3-4 hours
**Blockers**: Need vector DB setup

#### 5.2 Multi-Model Consensus
- [ ] Query GPT-4, Claude, Gemini in parallel
- [ ] Vote on best response
- [ ] Show all responses
- [ ] Confidence scoring

**Estimated Time**: 2-3 hours
**Pattern**: Map-Reduce (3 models → merge)

#### 5.3 Code Review Pipeline
- [ ] Analyze code quality
- [ ] Suggest improvements
- [ ] Generate tests
- [ ] Security scan
- [ ] All in parallel, then merge

**Estimated Time**: 3-4 hours
**Pattern**: Map-Reduce

#### 5.4 Research Agent System
- [ ] Researcher agent (finds info)
- [ ] Writer agent (drafts response)
- [ ] Critic agent (reviews quality)
- [ ] Editor agent (final polish)
- [ ] Sequential with feedback loops

**Estimated Time**: 4-6 hours (complex)
**Pattern**: Multi-agent collaboration

---

### Phase 6: Knowledge Base Integration (Priority: LOW)
**Goal**: Connect chat to knowledge base for research

#### 6.1 Basic Search
- [ ] Search Wikipedia while chatting
- [ ] Inline search results
- [ ] Add to context automatically
- [ ] Cite sources in responses

**Estimated Time**: 3-4 hours
**Blockers**: app_knowledge_base needs cleanup

#### 6.2 Document Upload & URL Scraping ✅
- [x] Upload PDFs, markdown, text, DOCX (max 10MB)
- [x] Extract text content (pypdf, python-docx)
- [x] URL scraping with BeautifulSoup
- [x] Document context automatically included in chat
- [x] Delete documents from session
- [x] Document preview and metadata display

**Completed**: 2025-11-10
**Status**: ✅ COMPLETE - File upload, URL scraping, and document context fully functional
**Files Created**:
- `backend/app/api/document_routes.py` - Upload, scrape, list, delete endpoints
- `backend/app/pipeline_steps/fetch_documents_step.py` - Pipeline integration
- `backend/app/database/migrations/V003__documents.sql` - Database schema
- `frontend/src/components/DocumentUpload.jsx` - File upload & URL input UI
- `frontend/src/components/DocumentList.jsx` - Document list with preview & delete
- Updated `simple_chat.json` pipeline to include fetch_documents step
- Updated `SimpleChatStep` to use document context

#### 6.2.1 RAG-Style Citations ✅
- [x] Document chunking (500 words, 50-word overlap)
- [x] Chunk ID generation ([doc1_chunk0], [doc2_chunk1])
- [x] Enhanced LLM citation instructions in system prompt
- [x] Chunk mapping passed through pipeline
- [x] CitationHighlighter React component with tooltip rendering
- [x] Numbered citation conversion ([1], [2], etc.)
- [x] Hover tooltips showing document name, URL, type
- [x] Sources list at bottom of responses with clickable links
- [x] Document count display in message metadata
- [x] Dark mode support for citations

**Completed**: 2025-11-10
**Status**: ✅ COMPLETE - RAG-style citations with source attribution
**Files Created**:
- `frontend/src/components/CitationHighlighter.jsx` - Citation parsing and rendering
- `frontend/src/components/CitationHighlighter.css` - Citation styling with tooltips
**Files Modified**:
- `backend/app/pipeline_steps/fetch_documents_step.py` - Added chunking logic
- `backend/app/pipeline_steps/simple_chat_step.py` - Enhanced citation instructions
- `backend/app/pipelines/simple_chat.json` - Added chunk_mapping to pipeline
- `frontend/src/App.jsx` - Integrated CitationHighlighter component

#### 6.2.2 Selective Document Inclusion ✅
- [x] Checkbox UI for toggling document inclusion
- [x] Backend filtering by `included_in_context` flag
- [x] Visual indicators for excluded documents
- [x] Real-time toggle with instant feedback
- [x] Database schema with default TRUE for backward compatibility

**Completed**: 2025-11-10
**Status**: ✅ COMPLETE - Users can control which documents AI uses per message
**Files Created**:
- `backend/app/database/migrations/V004__document_inclusion.sql` - Schema for organization features
**Files Modified**:
- `backend/app/api/document_routes.py` - Added toggle-inclusion endpoint
- `backend/app/pipeline_steps/fetch_documents_step.py` - Filter by included_in_context
- `frontend/src/components/DocumentList.jsx` - Added checkboxes and toggles
- `frontend/src/components/DocumentList.css` - Styled excluded state
- `frontend/src/App.jsx` - Added update callback

#### 6.2.3 Global Document Library ✅
- [x] Sidebar toggle between chats and document library
- [x] View all documents across all sessions
- [x] Search documents by name and content
- [x] Filter by collections
- [x] Document preview cards with metadata
- [x] Session attribution (shows which chat document came from)
- [x] Quick actions menu on each document

**Completed**: 2025-11-10
**Status**: ✅ COMPLETE - Full-featured document library with search and filtering
**Files Created**:
- `frontend/src/components/DocumentLibrary.jsx` - Main library component
- `frontend/src/components/DocumentLibrary.css` - Library styling
**Files Modified**:
- `backend/app/api/document_routes.py` - Added `/library/all` endpoint with filters
- `frontend/src/App.jsx` - Integrated library in sidebar with tabs
- `frontend/src/App.css` - Added sidebar tab styling

#### 6.2.4 Collections, Tags & Folders ✅
- [x] Document collections with custom colors
- [x] Create/delete collections
- [x] Assign documents to collections
- [x] Tag system with array storage
- [x] Folder path hierarchy
- [x] Collection cards with document counts
- [x] Visual collection badges on documents
- [x] Backend API for all organization features

**Completed**: 2025-11-10
**Status**: ✅ COMPLETE - Professional document organization system
**Database Changes**:
- `document_collections` table with colors and descriptions
- `tags` array column on documents (PostgreSQL array type)
- `collection_id` foreign key with cascade delete
- `folder_path` text column for hierarchical organization
- Indexes on tags (GIN), collection_id, folder_path
**Backend Endpoints**:
- POST `/api/documents/collections` - Create collection
- GET `/api/documents/collections` - List with document counts
- DELETE `/api/documents/collections/{id}` - Delete collection
- PATCH `/api/documents/{id}/tags` - Update document tags
- PATCH `/api/documents/{id}/collection` - Move to collection
- PATCH `/api/documents/{id}/folder` - Move to folder

#### 6.3 Research Notebooks
- [ ] Connect to research notebook system
- [ ] Auto-generate notebooks from chats
- [ ] Include chat context in research
- [ ] Bi-directional linking

**Estimated Time**: 5-6 hours
**Blockers**: Research notebook system

---

### Phase 7: Production Ready (Priority: LOW)
**Goal**: Deploy to production

#### 7.1 Observability
- [ ] OpenTelemetry tracing
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Error tracking (Sentry)
- [ ] Log aggregation

**Estimated Time**: 4-6 hours
**Reference**: ia_modules telemetry support

#### 7.2 Performance Optimization
- [ ] Database indexing
- [ ] Query optimization
- [ ] Caching strategy
- [ ] CDN for static assets
- [ ] WebSocket connection pooling

**Estimated Time**: 3-4 hours
**Blockers**: Need production load testing

#### 7.3 Security Hardening
- [ ] Rate limiting
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens
- [ ] API key rotation

**Estimated Time**: 3-4 hours
**Blockers**: Security audit

#### 7.4 Deployment
- [ ] Docker Compose for prod
- [ ] Kubernetes manifests (optional)
- [ ] CI/CD pipeline
- [ ] Automated backups
- [ ] Health checks
- [ ] Blue/green deployment

**Estimated Time**: 4-6 hours
**Blockers**: Infrastructure decisions

---

## 📊 Progress Tracking

### Sprint 1 (Week of Nov 6, 2025)
**Focus**: Quality & UX

- [ ] Phase 1.1: Test title generation
- [ ] Phase 1.2: Write Branching Tree tests
- [ ] Phase 2.1: Markdown rendering
- [ ] Phase 2.3: Enhanced chat UI
- [ ] Phase 3.1: System prompts
- [ ] Phase 3.2: Chat history limits

**Goal**: Ship polished, tested chat experience

### Sprint 2 (Week of Nov 13, 2025)
**Focus**: Advanced Features & Patterns

- [ ] Phase 4.1: HITL
- [ ] Phase 4.2: Model selection
- [ ] Phase 5.1: RAG pipeline
- [ ] Phase 5.2: Multi-model consensus

**Goal**: Showcase ia_modules capabilities

### Sprint 3 (Week of Nov 20, 2025)
**Focus**: Knowledge Base & Production

- [ ] Phase 6.1: Basic search
- [ ] Phase 7.1: Observability
- [ ] Phase 7.2: Performance optimization

**Goal**: Production-ready system

---

## 🎓 Learning Opportunities

### For Understanding ia_modules
- **Branching Tree Pattern**: Title generation (already done!)
- **Map-Reduce Pattern**: Multi-model consensus
- **HITL**: Fact-checking workflow
- **Loops**: Iterative refinement
- **Telemetry**: Production observability

### For Frontend Skills
- **React Hooks**: State management
- **WebSockets**: Real-time updates
- **Markdown Rendering**: Content display
- **Code Syntax Highlighting**: Developer UX
- **Responsive Design**: Mobile-friendly UI

### For Backend Skills
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database design
- **OAuth**: Authentication flows
- **Pipeline Architecture**: Modular design
- **Testing**: pytest, integration tests

---

## 🚀 Quick Start Guide

### To Start Working on Phase X.Y:

1. **Read the task description** in this roadmap
2. **Check blockers** - resolve dependencies first
3. **Estimate time** - block off calendar
4. **Create branch**: `git checkout -b feature/phase-X-Y-task-name`
5. **Code** - follow existing patterns
6. **Test** - manual + automated
7. **Document** - update relevant docs
8. **Commit**: `git commit -m "feat: phase X.Y - task description"`
9. **Check this roadmap** - mark task complete

### Priority Order (Start Here)

1. **Phase 1.1** (15 min) - Test title generation
2. **Phase 1.2** (30 min) - Write Branching Tree tests
3. **Phase 3.1** (30 min) - System prompts
4. **Phase 2.1** (1-2 hrs) - Markdown rendering
5. **Phase 2.3** (2-3 hrs) - Enhanced chat UI

After these, pick based on interest!

---

## 📝 Notes

### Design Decisions to Make

1. **Streaming Responses**: Should we stream character-by-character or get full response?
2. **Vector Database**: Qdrant, Pinecone, or PostgreSQL with pgvector?
3. **Frontend Framework**: Stick with vanilla React or add Next.js?
4. **Deployment**: Docker Compose, Kubernetes, or serverless?

### Open Questions

1. How should conversation branching work? (Tree structure? Timeline?)
2. What's the best way to handle long conversations? (Summarization? Chunking?)
3. Should we support multi-user collaboration on chats?
4. How to handle costs for multi-user deployments?

---

## 🔗 Related Documentation

- [Parallel Execution Patterns](../docs/PARALLEL_EXECUTION_PATTERNS.md)
- [Parallel Execution Bug Fix](../docs/PARALLEL_EXECUTION_FIX_SUMMARY.md)
- [Parallel Execution TODO](../docs/PARALLEL_EXECUTION_TODO.md)
- [Chat Implementation Guide](./CHAT_HISTORY_AND_TITLE_IMPLEMENTATION.md)
- [Pipeline Schema](./backend/app/pipelines/simple_chat.schema.md)

---

**Last Updated**: 2025-11-06
**Maintainer**: Development Team
**Status**: 🟢 Active Development
