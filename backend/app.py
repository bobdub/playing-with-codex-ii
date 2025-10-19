"""FastAPI backend that exposes a chat endpoint backed by llama.cpp."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from llama_cpp import Llama
import threading


DEFAULT_MODEL_PATH = Path("models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
MODEL_PATH = Path(os.environ.get("LLAMA_MODEL_PATH", DEFAULT_MODEL_PATH))


class ChatMessage(BaseModel):
    """Single message from the conversation history."""

    role: str = Field(description="Role of the speaker: system, user, or assistant")
    content: str = Field(description="Natural language content of the message")


class ChatRequest(BaseModel):
    """Body payload sent by the front-end."""

    messages: List[ChatMessage] = Field(
        description="Ordered history including the new user message.", min_items=1
    )
    max_tokens: Optional[int] = Field(
        default=512,
        ge=32,
        le=1024,
        description="Maximum number of new tokens to generate in the response.",
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for response diversity.",
    )


class ChatResponse(BaseModel):
    """Model response returned to the client."""

    reply: str


app = FastAPI(title="Local LLM Chat Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_llama_instance: Optional[Llama] = None
_model_lock = threading.Lock()


def _load_model() -> Llama:
    """Create or return the cached Llama instance."""

    global _llama_instance
    if _llama_instance is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Could not find model file at {MODEL_PATH}. Please follow the setup instructions."
            )
        _llama_instance = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=4096,
            chat_format="chatml",
            n_threads=int(os.environ.get("LLAMA_CPP_THREADS", os.cpu_count() or 4)),
        )
    return _llama_instance


@app.on_event("startup")
def preload_model() -> None:
    """Load the model at startup so first requests are responsive."""

    with _model_lock:
        _load_model()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Generate a chat response using the local model."""

    with _model_lock:
        llama = _load_model()
        try:
            completion = llama.create_chat_completion(
                messages=[message.dict() for message in request.messages],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
        except ValueError as exc:  # Raised by llama.cpp for malformed input
            raise HTTPException(status_code=400, detail=str(exc))

    try:
        reply_text = completion["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=500, detail=f"Malformed model response: {exc}")

    return ChatResponse(reply=reply_text)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    """Simple health endpoint used by troubleshooting steps."""

    return {"status": "ok"}
