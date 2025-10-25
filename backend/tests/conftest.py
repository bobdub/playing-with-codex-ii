"""Pytest configuration installing lightweight stubs when dependencies are unavailable."""
from __future__ import annotations

import asyncio
import contextlib
import inspect
import sys
import types
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_SENTINEL = object()


def _coerce_value(annotation: Any, value: Any) -> Any:
    """Best-effort conversion of JSON-like data into annotated structures."""

    if value is None:
        return None

    origin = get_origin(annotation)
    if origin is None:
        if isinstance(annotation, type) and issubclass(annotation, _BaseModel):
            if isinstance(value, annotation):
                return value
            if isinstance(value, dict):
                return annotation(**value)
        return value

    if origin in (list, tuple):
        (item_type,) = get_args(annotation) or (Any,)
        return [_coerce_value(item_type, item) for item in value]

    if origin is Union:
        for option in get_args(annotation):
            if option is type(None):  # noqa: E721
                continue
            try:
                return _coerce_value(option, value)
            except Exception:  # pragma: no cover - defensive fallback
                continue
        return value

    return value


class _BaseModel:
    """Very small subset of pydantic.BaseModel used in tests."""

    def __init__(self, **data: Any) -> None:
        annotations = get_type_hints(self.__class__)
        for name, annotation in annotations.items():
            default = getattr(self.__class__, name, None)
            value = data.get(name, _SENTINEL)
            if value is _SENTINEL:
                value = default
            value = _coerce_value(annotation, value)
            setattr(self, name, value)

    def dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        annotations = get_type_hints(self.__class__)
        for name in annotations:
            value = getattr(self, name, None)
            result[name] = self._serialize(value)
        return result

    def _serialize(self, value: Any) -> Any:
        if isinstance(value, _BaseModel):
            return value.dict()
        if isinstance(value, list):
            return [self._serialize(item) for item in value]
        return value


def _install_pydantic_stub() -> None:
    if "pydantic" in sys.modules:
        return

    module = types.ModuleType("pydantic")

    def Field(default: Any = None, **_: Any) -> Any:
        return default

    module.BaseModel = _BaseModel  # type: ignore[attr-defined]
    module.Field = Field  # type: ignore[attr-defined]
    sys.modules["pydantic"] = module


class _HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any) -> None:  # type: ignore[no-untyped-def]
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _Response:
    def __init__(self, status_code: int, content: Any, stream: Any | None = None) -> None:
        self.status_code = status_code
        self._content = content
        self._stream = stream

    def json(self) -> Any:
        if isinstance(self._content, _BaseModel):
            return self._content.dict()
        if hasattr(self._content, "dict"):
            return self._content.dict()
        return self._content

    def iter_lines(self):
        if self._stream is None:
            return iter(())

        async def consume_async(iterator):
            collected: list[str] = []
            try:
                async for item in iterator:
                    collected.append(str(item))
            except asyncio.CancelledError:  # pragma: no cover - background task cleanup
                pass
            return collected

        if hasattr(self._stream, "__aiter__"):
            chunks = asyncio.run(consume_async(self._stream))
        else:
            chunks = [str(item) for item in self._stream]

        lines: list[str] = []
        for chunk in chunks:
            lines.extend(chunk.splitlines())
        return iter(lines)


class _FastAPI:
    def __init__(self, **_: Any) -> None:
        self._routes: dict[tuple[str, str], Any] = {}
        self._startup_handlers: list[types.FunctionType] = []
        self._exception_handlers: dict[type[BaseException], types.FunctionType] = {}

    def add_middleware(self, *_: Any, **__: Any) -> None:  # pragma: no cover - noop stub
        return None

    def on_event(self, event_type: str):
        def decorator(func):
            if event_type == "startup":
                self._startup_handlers.append(func)
            return func

        return decorator

    def post(self, path: str, **_: Any):
        def decorator(func):
            self._routes[("POST", path)] = func
            return func

        return decorator

    def get(self, path: str, **_: Any):
        def decorator(func):
            self._routes[("GET", path)] = func
            return func

        return decorator

    def exception_handler(self, exc_type):
        def decorator(func):
            self._exception_handlers[exc_type] = func
            return func

        return decorator


class _TestClient:
    __test__ = False

    def __init__(self, app: _FastAPI) -> None:
        self.app = app
        self._started = False

    def _ensure_startup(self) -> None:
        if not self._started:
            for handler in getattr(self.app, "_startup_handlers", []):
                handler()
            self._started = True

    def _call_route(self, method: str, path: str, json: Any = None) -> _Response:
        self._ensure_startup()
        try:
            handler = self.app._routes[(method, path)]
        except KeyError:
            return _Response(404, {"detail": "Not Found"})

        parameters = inspect.signature(handler).parameters
        type_hints = get_type_hints(handler)
        args: list[Any] = []
        if parameters:
            (param,) = parameters.values()
            annotation = type_hints.get(param.name, param.annotation)
            if isinstance(annotation, str):
                annotation = handler.__globals__.get(annotation, annotation)
            if annotation is inspect._empty:
                args.append(json)
            else:
                coerced = _coerce_value(annotation, json)
                if (
                    isinstance(annotation, type)
                    and issubclass(annotation, _BaseModel)
                    and isinstance(coerced, dict)
                ):
                    coerced = annotation(**coerced)
                args.append(coerced)
        try:
            result = handler(*args)
            if inspect.iscoroutine(result):
                result = asyncio.run(result)
        except _HTTPException as exc:
            return _Response(exc.status_code, {"detail": exc.detail})
        except Exception as exc:  # pragma: no cover - allow custom handlers
            handler_fn = self.app._exception_handlers.get(type(exc))
            if handler_fn is not None:
                response = handler_fn(None, exc)
                if inspect.iscoroutine(response):
                    response = asyncio.run(response)
                return _Response(response.status_code, response.json())  # type: ignore[attr-defined]
            raise

        status_code = 200
        content = result
        stream = None

        if hasattr(result, "status_code") and hasattr(result, "content"):
            status_code = getattr(result, "status_code", 200)
            stream = getattr(result, "content")
            content = getattr(result, "content", None)
            if stream is None:
                content = {}

        return _Response(status_code, content, stream=stream)

    def post(self, path: str, json: Any | None = None) -> _Response:
        return self._call_route("POST", path, json=json)

    def get(self, path: str) -> _Response:  # pragma: no cover - convenience
        return self._call_route("GET", path)

    @contextlib.contextmanager
    def stream(self, method: str, path: str, json: Any | None = None):
        response = self._call_route(method, path, json=json)
        yield response


class _CORSMiddleware:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        self.args = args
        self.kwargs = kwargs


def _install_fastapi_stub() -> None:
    if "fastapi" in sys.modules:
        return

    module = types.ModuleType("fastapi")
    module.FastAPI = _FastAPI  # type: ignore[attr-defined]
    module.HTTPException = _HTTPException  # type: ignore[attr-defined]

    middleware = types.ModuleType("fastapi.middleware")
    cors = types.ModuleType("fastapi.middleware.cors")
    cors.CORSMiddleware = _CORSMiddleware  # type: ignore[attr-defined]
    middleware.cors = cors

    testclient = types.ModuleType("fastapi.testclient")
    testclient.TestClient = _TestClient  # type: ignore[attr-defined]

    module.middleware = middleware
    module.testclient = testclient

    sys.modules["fastapi"] = module
    sys.modules["fastapi.middleware"] = middleware
    sys.modules["fastapi.middleware.cors"] = cors
    sys.modules["fastapi.testclient"] = testclient


def _install_llama_stub() -> None:
    if "llama_cpp" in sys.modules:
        return

    module = types.ModuleType("llama_cpp")

    class Llama:  # noqa: D401 - minimal stub
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        def create_chat_completion(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise NotImplementedError("llama_cpp stub cannot generate completions")

    module.Llama = Llama  # type: ignore[attr-defined]
    sys.modules["llama_cpp"] = module


_install_pydantic_stub()
_install_fastapi_stub()
_install_llama_stub()
