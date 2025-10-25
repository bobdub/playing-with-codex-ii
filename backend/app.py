"""FastAPI backend that exposes a chat endpoint backed by llama.cpp."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from llama_cpp import Llama
import threading


DEFAULT_MODEL_PATH = Path("models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
_MODEL_ENV_VAR = "LLAMA_MODEL_PATH"


class ChatMessage(BaseModel):
    """Single message from the conversation history."""

    role: Literal["system", "user", "assistant"] = Field(
        description="Role of the speaker: system, user, or assistant"
    )
    content: str = Field(description="Natural language content of the message")

    @validator("content")
    def _validate_content(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Message content must be a non-empty string.")
        return value


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


DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
_frontend_origins_env = os.environ.get("FRONTEND_ORIGINS")
ALLOWED_ORIGINS = (
    [origin.strip() for origin in _frontend_origins_env.split(",") if origin.strip()]
    if _frontend_origins_env
    else DEFAULT_ALLOWED_ORIGINS
)

app = FastAPI(title="Local LLM Chat Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_llama_instance: Optional[Llama] = None
_current_model_path: Optional[Path] = None
_model_lock = threading.Lock()


def _resolve_concurrency_limit() -> int:
    """Return a sane concurrency limit parsed from the environment."""

    raw_value = os.environ.get("LLAMA_MAX_CONCURRENCY")
    if raw_value is None:
        return 1
    try:
        parsed = int(raw_value)
    except ValueError:
        return 1
    return parsed if parsed > 0 else 1


_request_semaphore = asyncio.Semaphore(_resolve_concurrency_limit())
_REQUEST_QUEUE_TIMEOUT = float(os.environ.get("LLAMA_REQUEST_QUEUE_TIMEOUT", "10"))


class ChatServiceError(Exception):
    """Application-level error that can be surfaced to the client."""

    def __init__(self, status_code: int, message: str, code: str) -> None:
        self.status_code = status_code
        self.message = message
        self.code = code


@app.exception_handler(ChatServiceError)
async def handle_chat_service_error(
    request: Request, exc: ChatServiceError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Invalid request payload.",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred.",
            }
        },
    )


def _resolve_model_path() -> Path:
    """Return the model path requested by the current environment."""

    env_value = os.environ.get(_MODEL_ENV_VAR)
    if env_value:
        return Path(env_value).expanduser()
    return DEFAULT_MODEL_PATH


def _load_model() -> Llama:
    """Create or return the cached Llama instance."""

    global _llama_instance, _current_model_path
    desired_path = _resolve_model_path()
    if _llama_instance is not None and _current_model_path == desired_path:
        return _llama_instance

    if _llama_instance is not None and _current_model_path != desired_path:
        # The configured path changed; drop the cached instance so the
        # application can load the newly requested weights.
        _llama_instance = None

    if _llama_instance is None:
        if not desired_path.exists():
            raise FileNotFoundError(
                "Could not find model file at "
                f"{desired_path}. Set {_MODEL_ENV_VAR} or download the default weights."
            )
        _llama_instance = Llama(
            model_path=str(desired_path),
            n_ctx=4096,
            chat_format="chatml",
            n_threads=int(os.environ.get("LLAMA_CPP_THREADS", os.cpu_count() or 4)),
        )
        _current_model_path = desired_path
    return _llama_instance


@app.on_event("startup")
def preload_model() -> None:
    """Load the model at startup so first requests are responsive."""

    with _model_lock:
        _load_model()


def _invoke_chat_completion(
    messages: List[ChatMessage], max_tokens: Optional[int], temperature: Optional[float]
):
    """Invoke llama.cpp inside a thread to avoid blocking the event loop."""

    with _model_lock:
        llama = _load_model()
        return llama.create_chat_completion(
            messages=[message.dict() for message in messages],
            max_tokens=max_tokens,
            temperature=temperature,
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Generate a chat response using the local model."""

    try:
        await asyncio.wait_for(_request_semaphore.acquire(), timeout=_REQUEST_QUEUE_TIMEOUT)
    except asyncio.TimeoutError as exc:
        raise ChatServiceError(
            status_code=503,
            message="The chat service is busy. Please retry shortly.",
            code="server_busy",
        ) from exc

    try:
        try:
            completion = await asyncio.to_thread(
                _invoke_chat_completion,
                request.messages,
                request.max_tokens,
                request.temperature,
            )
        except ValueError as exc:  # Raised by llama.cpp for malformed input
            raise ChatServiceError(
                status_code=400,
                message=str(exc),
                code="invalid_request",
            ) from exc
    finally:
        _request_semaphore.release()

    try:
        reply_text = completion["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ChatServiceError(
            status_code=502,
            message=f"Malformed model response: {exc}",
            code="model_response_error",
        ) from exc

    return ChatResponse(reply=reply_text)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    """Simple health endpoint used by troubleshooting steps."""

    return {"status": "ok"}
