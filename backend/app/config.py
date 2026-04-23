from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # LLM
    groq_api_key: str = ""
    groq_model_primary: str = "llama-3.3-70b-versatile"
    groq_model_fast: str = "llama-3.1-8b-instant"

    # Vector DB
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "disha_knowledge"

    # Embeddings + Reranker
    hf_api_key: str = ""
    hf_embedding_model: str = "BAAI/bge-m3"
    hf_reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # OCR
    ocr_space_api_key: str = ""
    ocr_space_endpoint: str = "https://api.ocr.space/parse/image"

    # Maps
    google_maps_api_key: str = ""
    google_doc_ai_credentials_json: str = ""

    # Admin
    admin_key: str = ""

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "INFO"

    # Data paths
    data_dir: str = "./app/data"
    storage_dir: str = "./app/data/storage"
    upload_dir: str = "./app/data/storage/uploads"
    sqlite_path: str = "./app/data/storage/disha.db"

    # RAG thresholds
    rag_match_threshold: float = 0.78
    rag_context_threshold: float = 0.62
    auto_enrich_min_answer_len: int = 50

    # File limits
    max_file_size_mb: int = 10

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    def ensure_dirs(self) -> None:
        """Create data/storage/upload directories if missing."""
        for path_str in (self.data_dir, self.storage_dir, self.upload_dir):
            Path(path_str).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
