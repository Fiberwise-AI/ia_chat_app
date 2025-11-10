# IA Chat App - Development Roadmap

**Created**: 2025-11-06
**Status**: Active Development

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

---

## 🎯 Active Development

### Phase 1: Quality & Testing (Priority: HIGH)
**Goal**: Ensure reliability and prevent regressions

#### 1.1 Test the Title Generation End-to-End ⏳
- [ ] Manual test: Create new chat
- [ ] Verify title appears in sidebar
- [ ] Verify title doesn't regenerate on second message
- [ ] Check database has correct title
- [ ] Test with various message types

**Estimated Time**: 15 minutes
**Assigned To**: Manual testing
**Blockers**: None

#### 1.2 Write Branching Tree Pattern Tests ⏳
- [ ] Create `ia_modules/tests/unit/test_branching_tree_pattern.py`
- [ ] Test terminal branches both execute
- [ ] Test conditional branching with expression
- [ ] Test exact step count assertions
- [ ] Run full test suite

**Estimated Time**: 30 minutes
**Reference**: `docs/PARALLEL_EXECUTION_TEST_PLAN.md`
**Blockers**: None

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

#### 2.1 Markdown Rendering
- [ ] Install `marked` or `react-markdown`
- [ ] Render assistant messages as markdown
- [ ] Add code syntax highlighting (`highlight.js` or `prism`)
- [ ] Style markdown elements (headings, lists, blockquotes)
- [ ] Test with various markdown samples

**Estimated Time**: 1-2 hours
**Dependencies**: npm packages

#### 2.2 Code Block Features
- [ ] Copy-to-clipboard button for code blocks
- [ ] Language detection and display
- [ ] Line numbers (optional)
- [ ] Syntax theme selection

**Estimated Time**: 1 hour
**Blockers**: Needs 2.1 complete

#### 2.3 Enhanced Chat UI
- [ ] Typing indicator during generation
- [ ] Regenerate response button
- [ ] Edit message and regenerate
- [ ] Delete message
- [ ] Message actions menu (copy, delete, regenerate)

**Estimated Time**: 2-3 hours
**Blockers**: None

#### 2.4 Better Message Display
- [ ] User avatars/icons
- [ ] Timestamp formatting
- [ ] Message status indicators (sending, sent, error)
- [ ] Streaming response display (character-by-character)
- [ ] Scroll to bottom button when not at bottom

**Estimated Time**: 2 hours
**Blockers**: None

---

### Phase 3: Quick Wins (Priority: MEDIUM)
**Goal**: Small improvements with immediate impact

#### 3.1 System Prompts
- [ ] Add system message to chat pipeline
- [ ] Create UI to customize system prompt
- [ ] Save system prompt per session
- [ ] Provide templates (coding assistant, creative writer, etc.)

**Estimated Time**: 30 minutes
**Files**: `simple_chat_step.py`, frontend settings UI

#### 3.2 Chat History Limits
- [ ] Limit to last 20 messages to prevent token overflow
- [ ] Add pagination for viewing old messages
- [ ] Show "X more messages" indicator
- [ ] Option to include full history (advanced)

**Estimated Time**: 30 minutes
**Files**: `fetch_chat_history_step.py`

#### 3.3 Cost Tracking
- [ ] Display estimated cost per message
- [ ] Session total cost
- [ ] User total cost (all sessions)
- [ ] Cost breakdown by model
- [ ] Budget alerts

**Estimated Time**: 1 hour
**Files**: Frontend components, new DB table

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

#### 6.2 Document Upload
- [ ] Upload PDFs, markdown, text
- [ ] Extract and index content
- [ ] Search across uploaded docs
- [ ] Reference in chat

**Estimated Time**: 4-5 hours
**Blockers**: File upload UI, storage

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
