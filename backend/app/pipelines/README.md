# IA Chat App - Pipelines

## Available Pipelines

### Simple Chat (simple_chat.json)
**Location:** Local to this app

**Steps:**
1. SimpleChatStep - Calls LLM directly via services registry

**Dependencies:**
- backend/pipeline_steps/simple_chat_step.py (local)
- LLM service from services registry

**Status:** Fully functional, no external dependencies

## How It Works

When you send a chat message:
1. Request hits /api/chat endpoint
2. Routes to ChatService.simple_chat()
3. Loads simple_chat.json from disk
4. GraphPipelineRunner executes the pipeline
5. Pipeline imports: backend.pipeline_steps.simple_chat_step
6. SimpleChatStep calls LLM service
7. Returns response + metadata
