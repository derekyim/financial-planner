import sys
from pathlib import Path

_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from shared.config import load_env
load_env()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent_initialized = False


def _ensure_agent():
    """Lazy-initialize the financial agent on first request."""
    global _agent_initialized
    if _agent_initialized:
        return

    from agents.financial_agent import setup_agent

    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_url = os.getenv(
        "SPREADSHEET_URL",
        "https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM/edit",
    )

    if not Path(creds_path).is_absolute():
        creds_path = str(Path(_backend_dir) / creds_path)

    setup_agent(
        credentials_path=creds_path,
        spreadsheet_url=spreadsheet_url,
    )
    _agent_initialized = True


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    user_id: Optional[str] = "default_user"


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        _ensure_agent()

        from agents.financial_agent import chat

        response = chat(
            message=request.message,
            user_id=request.user_id or "default_user",
            thread_id=request.thread_id,
        )
        return {"reply": response}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
