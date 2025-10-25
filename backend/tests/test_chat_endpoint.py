"""Smoke tests for the chat endpoint with the model mocked out."""

import json

from fastapi.testclient import TestClient

from backend import app as app_module


class DummyLlama:
    """Stand-in for llama_cpp.Llama used by the smoke tests."""

    init_kwargs = None
    last_call = None

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        DummyLlama.init_kwargs = kwargs

    def create_chat_completion(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        DummyLlama.last_call = {"args": args, "kwargs": kwargs}
        if kwargs.get("stream"):
            def generator():
                yield {"choices": [{"delta": {"content": "Test "}}]}
                yield {"choices": [{"delta": {"content": "reply"}}]}

            return generator()

        return {"choices": [{"message": {"content": "Test reply"}}]}


def test_chat_endpoint_returns_mocked_response(monkeypatch, tmp_path):
    """Posting to /chat should return the mocked response body."""

    fake_model = tmp_path / "model.gguf"
    fake_model.write_text("pretend weights")

    monkeypatch.setenv("LLAMA_MODEL_PATH", str(fake_model))
    monkeypatch.setattr(app_module, "_llama_instance", None)
    monkeypatch.setattr(app_module, "_current_model_path", None)
    monkeypatch.setattr(app_module, "Llama", DummyLlama)

    client = TestClient(app_module.app)

    payload = {"messages": [{"role": "user", "content": "Hello"}]}
    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    assert response.json() == {"reply": "Test reply"}
    assert DummyLlama.init_kwargs is not None
    assert DummyLlama.init_kwargs["model_path"] == str(fake_model)
    assert DummyLlama.last_call is not None
    assert DummyLlama.last_call["kwargs"]["messages"][0]["content"] == "Hello"
    assert app_module._current_model_path == fake_model


def test_chat_stream_endpoint_emits_sse(monkeypatch, tmp_path):
    """Streaming endpoint should emit incremental deltas."""

    fake_model = tmp_path / "model.gguf"
    fake_model.write_text("pretend weights")

    monkeypatch.setenv("LLAMA_MODEL_PATH", str(fake_model))
    monkeypatch.setattr(app_module, "_llama_instance", None)
    monkeypatch.setattr(app_module, "_current_model_path", None)
    monkeypatch.setattr(app_module, "Llama", DummyLlama)

    client = TestClient(app_module.app)

    payload = {"messages": [{"role": "user", "content": "Hello"}]}

    deltas: list[str] = []
    with client.stream("POST", "/chat/stream", json=payload) as response:
        assert response.status_code == 200
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode() if isinstance(raw_line, bytes) else raw_line
            if line.startswith("data: "):
                event_payload = json.loads(line[6:])
                if "delta" in event_payload:
                    deltas.append(event_payload["delta"])

    assert "".join(deltas) == "Test reply"
    assert DummyLlama.last_call is not None
    assert DummyLlama.last_call["kwargs"].get("stream") is True
