import sys
import json
import io
import logging
from pathlib import Path

_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)


class TeeStream:
    """Writes to both the original stream and a capture buffer."""

    def __init__(self, original: io.TextIOBase, capture: io.StringIO):
        self._original = original
        self._capture = capture

    def write(self, data: str) -> int:
        self._original.write(data)
        return self._capture.write(data)

    def flush(self) -> None:
        self._original.flush()
        self._capture.flush()

    def __getattr__(self, name: str):
        return getattr(self._original, name)

from shared.config import load_env
load_env()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
    spreadsheet_url = os.getenv("SPREADSHEET_URL", "")

    if not Path(creds_path).is_absolute():
        creds_path = str(Path(_backend_dir) / creds_path)

    setup_agent(
        credentials_path=creds_path,
        spreadsheet_url=spreadsheet_url,
    )
    _agent_initialized = True


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


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


@app.post("/api/chat/stream")
def chat_stream_endpoint(request: ChatRequest):
    """SSE streaming endpoint that emits thinking, log, and reply events."""

    def generate():
        try:
            _ensure_agent()
            from agents.financial_agent import chat_stream

            yield _sse_event("thinking", {
                "text": f"Let me look into that for you. Analyzing your question: \"{request.message}\""
            })

            log_buf = io.StringIO()
            log_handler = logging.StreamHandler(log_buf)
            log_handler.setLevel(logging.DEBUG)
            root_logger = logging.getLogger()
            root_logger.addHandler(log_handler)

            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            real_stdout = sys.__stdout__ or sys.stdout
            real_stderr = sys.__stderr__ or sys.stderr

            sys.stdout = TeeStream(real_stdout, stdout_buf)
            sys.stderr = TeeStream(real_stderr, stderr_buf)

            final_content_parts: list[str] = []

            def drain_logs():
                """Yield SSE log events from capture buffers. Logging-handler
                output isn't teed automatically, so echo it to real stderr."""
                log_text = log_buf.getvalue()
                log_buf.truncate(0); log_buf.seek(0)
                if log_text:
                    real_stderr.write(log_text)
                    real_stderr.flush()

                combined = stdout_buf.getvalue() + stderr_buf.getvalue() + log_text
                stdout_buf.truncate(0); stdout_buf.seek(0)
                stderr_buf.truncate(0); stderr_buf.seek(0)
                events = []
                for raw_line in combined.strip().splitlines():
                    stripped = raw_line.strip()
                    if stripped:
                        events.append(_sse_event("log", {"text": stripped}))
                return events

            try:
                for chunk in chat_stream(
                    message=request.message,
                    user_id=request.user_id or "default_user",
                    thread_id=request.thread_id,
                ):
                    for evt in drain_logs():
                        yield evt

                    if chunk:
                        final_content_parts.append(chunk)
            finally:
                sys.stdout = real_stdout
                sys.stderr = real_stderr
                root_logger.removeHandler(log_handler)

                for evt in drain_logs():
                    yield evt

            final_reply = "".join(final_content_parts)
            yield _sse_event("reply", {"text": final_reply})
            yield _sse_event("done", {})

        except Exception as e:
            traceback.print_exc()
            yield _sse_event("error", {"text": f"Agent error: {str(e)}"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
