import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import Column, PGEngine, PGVectorStore
from src.core.config import settings
from src.utils.db_uri import normalize_db_uri_for_pgvector

class VectorStoreService:
    def __init__(self):
        self._engine = None
        self._vector_store = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg://", "postgresql://")
        normalized = normalize_db_uri_for_pgvector(db_url)
        if normalized.startswith("postgresql://") and "+" not in normalized:
            normalized = "postgresql+psycopg://" + normalized.split("://", 1)[1]
        self._engine = PGEngine.from_connection_string(url=normalized)
        try:
            self._engine.init_vectorstore_table(
                table_name=settings.VECTOR_STORE_TABLE_NAME,
                vector_size=settings.VECTOR_SIZE,
                id_column=Column("langchain_id", "TEXT"),
                overwrite_existing=False,
            )
        except Exception:
            pass
        if not os.environ.get("OPENAI_API_KEY") and settings.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        self._vector_store = PGVectorStore.create_sync(
            engine=self._engine,
            table_name=settings.VECTOR_STORE_TABLE_NAME,
            embedding_service=OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")),
        )
        self._initialized = True

    def get_retriever(self, search_type: str = "similarity", search_kwargs: Optional[dict] = None):
        self._ensure_initialized()
        kwargs = search_kwargs or {}
        if "k" not in kwargs:
            kwargs["k"] = 5
        return self._vector_store.as_retriever(search_type=search_type, search_kwargs=kwargs)

    def add_documents(self, documents: List[Document], ids: Optional[List[str]] = None) -> List[str]:
        self._ensure_initialized()
        return self._vector_store.add_documents(documents=documents, ids=ids)

_vector_store_service = None
def get_vector_store_service():
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
