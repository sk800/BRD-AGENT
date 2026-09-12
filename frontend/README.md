# BRD Agent — Frontend

Next.js web application for the **BRD Agent** — an agentic AI tool for Business Requirements Document generation. Provides conversational intake, document upload, BRD review, and user approval workflows.

## Overview

The frontend is the user-facing layer for the BRD Agent system. It connects to the FastAPI backend and supports:

- Conversational requirement intake & clarification
- Document upload (PDF, DOCX, images, email)
- BRD creation, viewing, and editing
- User feedback and approval flows
- Session history and enterprise knowledge browsing

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Next.js (App Router) |
| Language | TypeScript |
| Styling | TBD |
| State management | TBD (Zustand / React Context) |
| API client | Typed client in `src/lib/api/` |
| Testing | Unit, integration, E2E |

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/             # Login, register
│   │   ├── (dashboard)/        # Authenticated shell
│   │   ├── api/                # Optional BFF route handlers
│   │   ├── brd/                # BRD workspace (new, view, review)
│   │   ├── chat/               # Conversational intake
│   │   ├── documents/upload/   # File upload & extraction status
│   │   └── sessions/[id]/      # Session history
│   ├── components/
│   │   ├── ui/                 # Base UI primitives
│   │   ├── layout/             # Header, sidebar, nav
│   │   ├── chat/               # Message UI, streaming input
│   │   ├── documents/          # Upload dropzone, file preview
│   │   ├── brd/                # BRD sections, diff, export
│   │   ├── feedback/           # Approve / request clarification
│   │   └── common/             # Loaders, errors, wrappers
│   ├── features/               # Feature modules (logic + hooks)
│   │   ├── intake/
│   │   ├── brd-generation/
│   │   ├── document-upload/
│   │   ├── approval/
│   │   ├── knowledge/
│   │   └── sessions/
│   ├── lib/
│   │   ├── api/                # Typed API client → backend
│   │   ├── utils/
│   │   └── validations/
│   ├── hooks/
│   ├── services/
│   ├── stores/
│   ├── types/
│   ├── constants/
│   └── styles/
├── public/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── deploy/
└── docs/
```

## User Flows

| Flow | Route | Feature Module |
|---|---|---|
| Login / Register | `/login`, `/register` | — |
| Dashboard | `/dashboard` | — |
| Conversational intake | `/chat` | `features/intake` |
| Upload documents | `/documents/upload` | `features/document-upload` |
| Create BRD | `/brd/new` | `features/brd-generation` |
| View / edit BRD | `/brd/[id]` | `features/brd-generation` |
| Review & approve | `/brd/review` | `features/approval` |
| Session history | `/sessions/[id]` | `features/sessions` |

## Getting Started

```bash
cd frontend

# Install dependencies
npm install

# Configure backend URL
cp .env.local.example .env.local

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Make sure the backend is running at `http://localhost:8000`.

## Environment Variables

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend FastAPI base URL (e.g. `http://localhost:8000`) |
| `NEXT_PUBLIC_APP_ENV` | `dev` / `staging` / `prod` |

## Backend Communication

```
Browser → Next.js (this app) → FastAPI (../backend/)
              lib/api/              api/routes/
              features/             agents/graph/
```

The frontend and backend are fully separate apps with no shared runtime code. API types can be generated from the backend OpenAPI spec later.

## Related

Backend lives in the sibling `../backend/` directory.
