from functools import lru_cache

from brd_agent.core.config import get_settings


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class EmbeddingService:
    def __init__(self):
        settings = get_settings()

        self.model = _load_model(settings.embedding_model_name)

    def embed_documents(self, texts: list[str]):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )

    def embed_query(self, query: str):
        return self.model.encode(
            query,
            normalize_embeddings=True,
        )