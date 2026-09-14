import logging
from typing import List
import ollama
from app.core.config import settings
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a precise FastAPI documentation assistant. "
    "Answer the user question using ONLY the provided context excerpts from the FastAPI docs. "
    "If the answer is not in the context, say 'Not covered in retrieved docs.' "
    "After your answer, list the source file(s) as citations."
)


class GenerationService:
    """Service responsible for building grounded prompts and querying Ollama."""

    def __init__(self) -> None:
        self.llm_model = settings.llm_model
        logger.info(f"Initializing GenerationService with model '{self.llm_model}'")

    def build_prompt(self, question: str, chunks: List[RetrievedChunk]) -> str:
        """Assemble retrieved context blocks into grounded prompt."""
        context_blocks = []
        for rank, ch in enumerate(chunks, start=1):
            context_blocks.append(
                f"[Excerpt {rank} | File: {ch.source_file} | Section: {ch.section_title}]\n"
                f"{ch.content[:500]}"
            )
        context_str = "\n\n".join(context_blocks)
        return (
            f"Context excerpts from FastAPI documentation:\n"
            f"{'='*60}\n"
            f"{context_str}\n"
            f"{'='*60}\n\n"
            f"Question: {question}\n\n"
            f"Answer (cite source files at the end):"
        )

    def generate(self, question: str, chunks: List[RetrievedChunk]) -> str:
        """Call Ollama chat API with grounded prompt and return answer text."""
        prompt = self.build_prompt(question, chunks)
        response = ollama.chat(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.1, "num_predict": 350},
        )
        return response["message"]["content"].strip()
