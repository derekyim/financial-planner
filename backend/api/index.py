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
from openai import OpenAI
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = None


def get_openai_client():
    """Get or create OpenAI client with lazy initialization."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        _client = OpenAI(api_key=api_key)
    return _client


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        client = get_openai_client()
        user_message = request.message
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a supportive mental health coach.\n\n"
                        "Scope:\n"
                        "- You provide guidance on mental health, emotional regulation, stress, motivation, habits, and personal wellbeing.\n"
                        "- You do NOT answer questions outside this scope. \n\n"
                        "Safety & Routing Rules:\n"
                        "1. Non-mental-health topics:\n"
                        "   If the user asks about anything unrelated to mental or emotional wellbeing, "
                        "politely state that it is outside your expertise and direct them to https://chatgpt.com.\n\n"
                        "2. Crisis or self-harm:\n"
                        "   If the user expresses suicidal thoughts, self-harm, violent intent, or immediate danger, "
                        "respond with empathy and clearly encourage them to call 911 or go to their local emergency room immediately. "
                        "Do not provide advice that could enable harm.\n\n"
                        "3. Relationship-specific issues:\n"
                        "   If the main issue concerns a romantic or partner relationship, acknowledge their feelings "
                        "and refer them to https://relationallife.com/ for specialized relationship support.\n\n"
                        "Tone:\n"
                        "- Compassionate, calm, respectful\n"
                        "- Never judgmental, dismissive, or alarmist unless safety is involved"
                    ),
                },
                {"role": "user", "content": user_message},
            ],
        )
        return {"reply": response.choices[0].message.content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")
