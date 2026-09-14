# BRD Agent — Backend

Agentic AI backend for **Business Requirements Document (BRD)** generation. Built with **FastAPI** for the API layer and **LangGraph** for the multi-stage agent workflow.

## Overview

The backend implements an agentic requirements engineering pipeline:

```
extract → discover → validate → enrich → route → generate → validate → learn
```

It handles conversational intake, document extraction, enterprise knowledge retrieval, LLM routing, guardrails, user feedback loops, and post-experience memory.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Agent orchestration | LangGraph |
| LLM routing | Multi-model gateway (General, Domain/Legal, Long-Context) |
| Observability | LangSmith (tracing, evals, monitoring) |
| Language | Python 3.11+ |

## Project Structure

```
backend/
├── src/brd_agent/
│   ├── api/              # FastAPI routes, middleware, schemas
│   ├── agents/           # LangGraph graph, nodes, edges, state
│   ├── intake/           # Requirement intake & clarification
│   ├── extraction/       # Document extraction (PDF, DOCX, OCR, email)
│   ├── ingestion/        # Chunking, normalization, persistence
│   ├── orchestration/    # Content assembly & context management
│   ├── knowledge/        # Enterprise connectors (Confluence, Slack, DB)
│   ├── memory/           # Conversation history & feedback memory
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

## Agent Pipeline

```
START
  → intake (requirement_intake_clarification)
  → extraction (document_extraction_gateway)
  → ingestion
  → orchestration (content_assembly)
  → guardrails (input_validation)
  → llm_gateway (query-aware routing)
  → guardrails (output_validation)
  → feedback (user_approval)
      ├─ approved       → memory update → END
      └─ needs clarification → intake (loop)
```

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
