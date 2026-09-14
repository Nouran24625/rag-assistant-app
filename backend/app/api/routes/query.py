import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.query import QueryRequest, QueryResponse
from app.services.retrieval import RetrievalService
from app.services.generation import GenerationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Query & Health"])


@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check endpoint confirming application and vector store status."""
    retrieval_service: RetrievalService = request.app.state.retrieval_service
    collection_count = retrieval_service.collection.count() if retrieval_service else 0
    return {
        "status": "ok",
        "collection": request.app.state.settings.collection_name,
        "total_chunks": collection_count,
        "llm_model": request.app.state.settings.llm_model,
    }


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_endpoint(body: QueryRequest, request: Request) -> QueryResponse:
    """Retrieve top-k chunks, generate grounded answer using Ollama, and return QueryResponse."""
    retrieval_service: RetrievalService = request.app.state.retrieval_service
    generation_service: GenerationService = request.app.state.generation_service

    if not retrieval_service or not generation_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services are not initialized.",
        )

    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    # 1. Retrieve top-k chunks
    chunks = retrieval_service.retrieve(question)

    # 2. Extract unique source filenames in order of retrieval
    sources = list(dict.fromkeys(ch.source_file for ch in chunks if ch.source_file))

    # 3. Generate grounded answer
    try:
        answer = generation_service.generate(question, chunks)
    except Exception as e:
        logger.error(f"Error during LLM generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {str(e)}",
        )

    return QueryResponse(answer=answer, sources=sources)
