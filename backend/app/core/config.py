import json
import logging
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def resolve_rag_config_path() -> Path:
    """Locate rag_config.json dynamically from current or parent directories."""
    candidates = [
        Path("data/vector_store/rag_config.json"),
        Path("backend/data/vector_store/rag_config.json"),
        Path("../backend/data/vector_store/rag_config.json"),
        Path("/Users/noura/rag-assistant-project/backend/data/vector_store/rag_config.json"),
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c.resolve()
    raise FileNotFoundError("Could not find rag_config.json in candidate locations.")


class Settings(BaseSettings):
    """Application settings populated strictly from rag_config.json."""

    app_name: str = "RAG Assistant API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Pipeline configurations loaded from rag_config.json
    embedding_model: str = ""
    collection_name: str = ""
    vector_store_path: Path = Path(".")
    chunk_size: int = 0
    chunk_overlap: int = 0
    top_k: int = 5
    llm_model: str = ""
    hnsw_space: str = "cosine"
    total_chunks: int = 0

    # Ollama host settings
    ollama_base_url: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def load_from_rag_config(self) -> None:
        """Read all pipeline parameters from rag_config.json."""
        cfg_path = resolve_rag_config_path()
        logger.info(f"Loading pipeline settings from {cfg_path}")
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self.embedding_model = cfg["embedding_model"]
        self.collection_name = cfg["collection_name"]
        self.vector_store_path = Path(cfg["vector_store_path"]).resolve()
        self.chunk_size = int(cfg.get("chunk_size", 800))
        self.chunk_overlap = int(cfg.get("chunk_overlap", 150))
        self.top_k = int(cfg.get("top_k", 5))
        self.llm_model = cfg["llm_model"]
        self.hnsw_space = cfg.get("hnsw_space", "cosine")
        self.total_chunks = int(cfg.get("total_chunks", 0))

        logger.info(
            f"Config loaded: collection='{self.collection_name}', "
            f"embedding_model='{self.embedding_model}', top_k={self.top_k}, "
            f"llm_model='{self.llm_model}', store='{self.vector_store_path}'"
        )


settings = Settings()
settings.load_from_rag_config()
