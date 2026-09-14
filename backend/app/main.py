import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.utils.logging_config import setup_logging
from app.services.retrieval import RetrievalService
from app.services.generation import GenerationService
from app.api.routes import query

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load configuration, vector store, and generation services once at startup."""
    logger.info("Initializing application services at startup...")
    app.state.settings = settings
    app.state.retrieval_service = RetrievalService()
    app.state.generation_service = GenerationService()
    logger.info("Startup complete. Vector store and LLM ready.")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="FastAPI Backend for RAG Assistant loaded from rag_config.json",
    lifespan=lifespan,
)

# Allow CORS for Streamlit frontend running on http://localhost:8501
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes (/query and /health)
app.include_router(query.router)
