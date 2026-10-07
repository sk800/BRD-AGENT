# BRD Agent — Backend

Agentic AI backend for **Business Requirements Document (BRD)** generation. Built with **FastAPI** for the API layer and **LangGraph** for the multi-stage agent workflow.

## Overview

Nodes and LangGraph definitions live in the shared `agents/nodes/` and
`agents/graph/` directories, following the existing extraction and chunking
patterns. Requirement-specific models, prompts, and service logic live under
`intake/`; context assembly service logic lives under `orchestration/`.

The current implementation focus is requirement discovery and context assembly:

```
user text + uploaded files → requirement checklist → supporting context
```

Uploaded files are extracted and indexed by the ingestion workflow. Requirement
discovery uses Azure OpenAI, with the user request as the primary source and uploaded
documents and conversation history as supporting context. Context assembly retrieves
relevant uploaded-document chunks and optionally fetches enterprise knowledge.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Agent orchestration | LangGraph |
| Requirement discovery | Azure OpenAI |
| Observability | LangSmith (tracing, evals, monitoring) |
| Language | Python 3.11+ |

## Project Structure

```
backend/
├── src/brd_agent/
│   ├── api/              # FastAPI routes, middleware, schemas
│   ├── agents/           # LangGraph graph, nodes, edges, state
│   ├── intake/           # Requirement models, prompts, and discovery service
│   ├── extraction/       # Document extraction (PDF, DOCX, OCR, email)
│   ├── ingestion/        # Chunking, normalization, persistence
│   ├── orchestration/    # Context assembly service
│   ├── knowledge/        # Enterprise connectors and MCP tools
│   ├── memory/           # Durable episodic, semantic, procedural memory
│   ├── guardrails/       # Validation at every pipeline stage
│   ├── llm/              # Query-aware LLM gateway & providers
│   ├── feedback/         # Approval & clarification loop
│   ├── observability/    # LangSmith, metrics, evals
│   ├── domain/           # BRD models, templates, generation logic
│   └── core/             # Config, logging, exceptions, utils
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evals/
├── config/               # Environment & logging configs
├── data/                 # Upload & staging directories
├── deploy/               # Docker, Kubernetes, Terraform
├── docs/                 # Architecture, API, runbooks
└── scripts/              # Dev & utility scripts
```

## Current Workflow

```
POST /api/v1/chat/requirements
  → save text and optional files
  → ingest files (extract + chunk + index)
  → retrieve project-scoped LangMem memories
  → discover or update the concise BRD checklist
  → search uploaded-document vectors for every checklist item
  → search configured Confluence and any explicitly supplied read-only MCP sources
  → assess evidence as answered, missing, or needing clarification
  → persist checklist and evidence state in MongoDB
  → return the checklist, supporting evidence, and questions for the user

Fields: text (optional if files are supplied), files (optional), conversation_id (optional)
Optional fields: enterprise_sources_json (JSON list of read-only MCP sources),
retrieval_top_k (1–50)

`assistant_message` contains the natural next prompt or an off-topic redirection.
Clarification questions are returned in each checklist item's
`clarification_question` and are surfaced through that message for the frontend.
Submitting a reply with the same `conversation_id` re-evaluates the saved checklist.
Conversation state and LangMem memory survive restarts; memory is isolated by
authenticated user and conversation.

LangMem classifies project memories as:
- **Episodic:** project decisions, events, and outcomes
- **Semantic:** stable project facts, terms, and constraints
- **Procedural:** project workflows and user preferences

POST /api/v1/brd/assemble-context
  → retrieve uploaded-document chunks relevant to one requirement
  → optionally fetch configured enterprise knowledge
  → return assembled context

JSON body: conversation_id, requirement_text, optional enterprise_sources and retrieval_top_k
```

Confluence search is automatic when its MCP credentials are configured. ServiceNow
queries require an explicit read-only source specification because the correct table
and query are project-specific. Writes are rejected by the checklist endpoint.

BRD generation, input/output validation, approval feedback, and the final BRD model
are intentionally outside this current scope.

Set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and
`AZURE_OPENAI_DEPLOYMENT` in `backend/.env` to enable requirement discovery.
`AZURE_OPENAI_API_VERSION` defaults to `2024-12-01-preview`. Set
`LLM_MAX_COMPLETION_TOKENS` to control the output-token ceiling; LangMem's
memory extraction uses a smaller ceiling. No live Azure calls are made by tests.

## Getting Started

### Prerequisites

- Python 3.11+
- MongoDB running locally (or a remote MongoDB URI)

### Setup

```bash
cd backend

# 1. Create virtual environment (Python 3.11+)
python3.11 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies (includes PDF/DOCX/PPTX extraction libs)
pip install -e ".[dev]"

# Optional: OCR for scanned PDFs / layout analysis
# pip install -e ".[layout]"

# 4. Copy environment file and configure MongoDB
cp .env.example .env

# 5. Start MongoDB (if running locally)
# mongod

# 6. Run development server
uvicorn brd_agent.api.main:app --reload
```

To deactivate the virtual environment later:

```bash
deactivate
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Auth Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/signup` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and receive JWT |

### Chat & File Upload Endpoints (requires login)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat/messages` | Send free text + optional files (multipart) |
| `GET` | `/api/v1/chat/conversations` | List user conversations |
| `GET` | `/api/v1/chat/conversations/{id}/messages` | Get messages in a conversation |

**Send message** (`multipart/form-data`, Bearer token required):

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | No* | Free-text message (like ChatGPT/Claude) |
| `files` | file(s) | No* | Any file format (PDF, DOCX, images, etc.) |
| `conversation_id` | string | No | Continue an existing conversation |

\* At least one of `text` or `files` is required.

```bash
curl -X POST http://localhost:8000/api/v1/chat/messages \
  -H "Authorization: Bearer <token>" \
  -F "text=Please analyze this requirements document" \
  -F "files=@requirements.pdf" \
  -F "files=@notes.docx"
```

**Signup example:**

```json
{
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "password": "securepass123"
}
```

**Login example:**

```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

Both return:

```json
{
  "user": { "id": "...", "email": "...", "full_name": "...", "is_active": true, "created_at": "..." },
  "access_token": "...",
  "token_type": "bearer"
}
```

## Environment Variables

| Variable | Description |
|---|---|
| `MONGODB_URL` | MongoDB connection string (default: `mongodb://localhost:27017`) |
| `MONGODB_DB_NAME` | Database name (default: `brd_agent`) |
| `SECRET_KEY` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry in minutes |
| `UPLOAD_DIR` | Directory for uploaded files (default: `data/uploads`) |
| `MAX_FILE_SIZE_MB` | Max file size per upload (default: `25`) |
| `MAX_FILES_PER_MESSAGE` | Max files per message (default: `10`) |
| `ENVIRONMENT` | `dev` / `staging` / `prod` |

## Documentation

- [Folder Structure & Architecture](docs/architecture/FOLDER_STRUCTURE.md)
- API docs — `docs/api/` (coming soon)
- Runbooks — `docs/runbooks/` (coming soon)

## Related

Frontend lives in the sibling `../frontend/` directory and communicates with this backend over HTTP/WebSocket.
