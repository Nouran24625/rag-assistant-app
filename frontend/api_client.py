import os
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

# Load environment variables from frontend/.env if present
load_dotenv()

# Read API_BASE_URL from environment variable, default to http://localhost:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class APIClientError(Exception):
    """Custom exception for API client errors with user-friendly messages."""
    pass


class APIClient:
    """Client for interacting with the FastAPI RAG backend."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        """Check if the backend is running and healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise APIClientError(
                f"Cannot connect to backend at {self.base_url}. "
                "Ensure the FastAPI server is running (uvicorn app.main:app --reload)."
            )
        except requests.exceptions.Timeout:
            raise APIClientError("Health check request timed out.")
        except Exception as e:
            raise APIClientError(f"Health check failed: {str(e)}")

    def query(self, question: str) -> Dict[str, Any]:
        """Send a query to the backend and return the generated answer and sources."""
        if not question or not question.strip():
            raise APIClientError("Question cannot be empty.")

        url = f"{self.base_url}/query"
        payload = {"question": question.strip()}

        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 422:
                raise APIClientError("Invalid request format sent to backend.")
            elif response.status_code != 200:
                detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                raise APIClientError(f"Backend returned error ({response.status_code}): {detail}")

            data = response.json()
            return {
                "answer": data.get("answer", "No answer returned."),
                "sources": data.get("sources", []),
            }
        except requests.exceptions.ConnectionError:
            raise APIClientError(
                f"Cannot connect to backend at {self.base_url}. "
                "Please make sure the backend server is running on port 8000."
            )
        except requests.exceptions.Timeout:
            raise APIClientError(
                "The query took too long to complete. The model might be processing a heavy load."
            )
        except APIClientError:
            raise
        except Exception as e:
            raise APIClientError(f"Unexpected error communicating with backend: {str(e)}")
