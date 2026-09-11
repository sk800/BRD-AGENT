# BRD Agent — Folder Structure

**Two top-level folders only — fully separate apps.**

```
Requirement_BRD/
├── backend/          # LangGraph + FastAPI (Python)
└── frontend/         # Next.js (App Router)
```

---

## Backend (`backend/`)

| Architecture Component | Folder |
|---|---|
| FastAPI — User Input / API | `src/brd_agent/api/` |
| Requirement Intake & Clarification | `src/brd_agent/intake/` |
| Document Extraction Gateway | `src/brd_agent/extraction/` |
| Ingestion Layer | `src/brd_agent/ingestion/` |
| Content Assembly & Context Orchestration | `src/brd_agent/orchestration/` |
| Enterprise Knowledge Sources | `src/brd_agent/knowledge/` |
| Post-Experience Memory Management | `src/brd_agent/memory/` |
| Input / Output Guardrails | `src/brd_agent/guardrails/` |
| LLM Gateway (General, Domain/Legal, Long-Context) | `src/brd_agent/llm/` |
| User Feedback / Approval Loop | `src/brd_agent/feedback/` |
| LangGraph workflow | `src/brd_agent/agents/` |
| LangSmith tracing & evals | `src/brd_agent/observability/` |
| BRD domain models & templates | `src/brd_agent/domain/` |

```
backend/
├── .github/workflows/              # backend CI/CD
├── config/environments/
├── config/logging/
├── data/uploads/
├── data/staging/
├── deploy/docker/
├── deploy/kubernetes/
├── deploy/terraform/
├── docs/
│   ├── architecture/
│   ├── api/
│   └── runbooks/
├── scripts/
├── src/brd_agent/
│   ├── api/                        # FastAPI — routes, middleware, schemas
│   ├── agents/                     # LangGraph — graph, nodes, edges, state
│   ├── intake/
│   ├── extraction/extractors/{pdf,docx,images,email}/
│   ├── ingestion/
│   ├── orchestration/
│   ├── knowledge/connectors/{confluence,slack,enterprise_db}/
│   ├── memory/
│   ├── guardrails/
│   ├── llm/providers/{general,domain_legal,long_context}/
│   ├── feedback/
│   ├── core/
│   ├── observability/
│   └── domain/
├── storage/temp/
└── tests/{unit,integration,evals}/
```

---

## Frontend (`frontend/`)

| User Flow | Folder |
|---|---|
| Conversational intake & clarification | `src/app/chat/`, `features/intake/` |
| Document upload | `src/app/documents/upload/`, `features/document-upload/` |
| BRD create / view / edit | `src/app/brd/`, `features/brd-generation/` |
| Approval & feedback | `src/app/brd/review/`, `features/approval/` |
| Session history | `src/app/sessions/`, `features/sessions/` |
| Enterprise knowledge UI | `features/knowledge/` |
| Backend API client | `src/lib/api/`, `services/` |
| Auth | `src/app/(auth)/` |

```
frontend/
├── .github/workflows/              # frontend CI/CD
├── deploy/
├── docs/
├── public/{icons,images}/
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── (auth)/{login,register}/
│   │   ├── (dashboard)/dashboard/
│   │   ├── api/                    # optional BFF route handlers
│   │   ├── brd/{new,[id],review}/
│   │   ├── chat/
│   │   ├── documents/upload/
│   │   └── sessions/[id]/
│   ├── components/{ui,layout,chat,documents,brd,feedback,common}/
│   ├── features/{intake,brd-generation,document-upload,approval,knowledge,sessions}/
│   ├── hooks/
│   ├── lib/{api,utils,validations}/
│   ├── services/
│   ├── stores/
│   ├── types/
│   ├── constants/
│   └── styles/
└── tests/{unit,integration,e2e}/
```

---

## Communication

```
Browser → frontend/ (Next.js) → backend/ (FastAPI)
              lib/api/               api/routes/
              features/              agents/graph/
```

No shared code between the two — they communicate via HTTP/WebSocket only.
