"""BGE-small embeddings via FastEmbed (ONNX, no PyTorch required at import)."""

from __future__ import annotations

import asyncio
import logging

from brd_agent.core.config import get_settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model

    if _model is None:
        from fastembed import TextEmbedding

        settings = get_settings()
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = TextEmbedding(model_name=settings.embedding_model)

    return _model


def embed_texts_sync(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = _get_model()
    return [vector.tolist() for vector in model.embed(texts)]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    return await asyncio.to_thread(embed_texts_sync, texts)
