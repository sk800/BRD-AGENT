import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brd_agent.api.routes.auth import router as auth_router
from brd_agent.api.routes.chat import router as chat_router
from brd_agent.api.routes.knowledge import router as knowledge_router
from brd_agent.api.routes.brd import router as brd_router
from brd_agent.core.config import get_settings
from brd_agent.core.database import close_db, init_db
from brd_agent.ingestion.vector.lancedb_store import LanceChunkStore
from brd_agent.services.file_storage_service import FileStorageService

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await FileStorageService().ensure_upload_dir()
    LanceChunkStore()
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="BRD Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(brd_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
