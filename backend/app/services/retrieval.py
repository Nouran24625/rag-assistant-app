import logging
from pathlib import Path
from typing import List, Tuple, NamedTuple
import chromadb
from app.core.config import settings

logger = logging.getLogger(__name__)


class RetrievedChunk(NamedTuple):
    content: str
    source_file: str
    section_title: str
    score: float


class RetrievalService:
    """Service responsible for loading Chroma PersistentClient and retrieving top-k chunks."""

    def __init__(self) -> None:
        self.vector_store_path = settings.vector_store_path
        self.collection_name = settings.collection_name
        self.embedding_model_name = settings.embedding_model
        self.top_k = settings.top_k

        logger.info(f"Initializing RetrievalService with store at {self.vector_store_path}")

        # 1. Load the SentenceTransformer model directly (fallback to Chroma ONNX default embedding function if not installed)
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self._use_st = True
            logger.info(f"Loaded SentenceTransformer({self.embedding_model_name})")
        except ImportError:
            from chromadb.utils import embedding_functions
            self.embedding_model = embedding_functions.DefaultEmbeddingFunction()
            self._use_st = False
            logger.info(f"Using Chroma DefaultEmbeddingFunction for manual encoding")

        # 2. Connect to Chroma persistent store without passing embedding_function to get_collection
        self.client = chromadb.PersistentClient(path=str(self.vector_store_path))
        self.collection = self.client.get_collection(name=self.collection_name)
        logger.info(f"Loaded collection '{self.collection_name}' with {self.collection.count()} chunks (no embedding_function attached).")

    def retrieve(self, question: str, top_k: int = None) -> List[RetrievedChunk]:
        """Compute query embedding manually and query Chroma using query_embeddings."""
        k = top_k if top_k is not None else self.top_k

        # Compute query embedding manually
        if self._use_st:
            query_embedding = self.embedding_model.encode([question]).tolist()
        else:
            query_embedding = self.embedding_model([question])

        # Query Chroma by passing query_embeddings instead of query_texts
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        chunks: List[RetrievedChunk] = []
        if not results["documents"] or not results["documents"][0]:
            return chunks

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, distances):
            source = meta.get("source_file", "unknown")
            section = meta.get("section_title", "")
            chunks.append(RetrievedChunk(
                content=doc,
                source_file=source,
                section_title=section,
                score=round(dist, 4),
            ))

        return chunks
