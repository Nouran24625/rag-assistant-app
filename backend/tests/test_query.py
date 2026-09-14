import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_query_happy_path():
    """Happy-path test: POST /query with a real FastAPI question asserts 200, answer, and non-empty sources."""
    payload = {"question": "How do I declare a request body with Pydantic?"}
    with TestClient(app) as client:
        response = client.post("/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0


def test_query_invalid_input():
    """Invalid-input test: POST /query missing 'question' field asserts HTTP 422 Unprocessable Entity."""
    payload = {}  # missing required "question" field
    with TestClient(app) as client:
        response = client.post("/query", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
