# playing-with-codex-ii

Create a lightweight website that chats with a locally hosted large language
model (LLM).

## Live console

Visit the published GitHub Pages site at [`docs/index.html`](docs/index.html)
to launch the in-browser TinyLlama console. The page loads the same static
client that lives under `frontend/`, giving you quick access to the controls
without needing to start a local web server. Point the "Backend URL" field at
your running FastAPI instance (for local testing this is typically
`http://localhost:8000`).

## Repository layout

The project is deliberately small so it can run entirely on a developer's
laptop or inside a Codespaces-style container:

| Path | Purpose |
| --- | --- |
| `backend/app.py` | FastAPI service exposing a `/chat` endpoint backed by [`llama.cpp`](https://github.com/ggerganov/llama.cpp). |
| `frontend/index.html` | Static HTML/JS client that renders the conversation and POSTs user input to the backend. |
| `models/` | Expected location for downloaded `.gguf` model weights. |

## Prerequisites

1. **Python 3.9+** with `pip`.
2. **C compiler toolchain** (needed by `llama-cpp-python`). On Debian/Ubuntu run
   `sudo apt-get update && sudo apt-get install build-essential`.
3. **A GGUF model file.** Tiny models such as
   [`TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF`](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF)
   work well for experimentation.

Download a model into `models/` or point the `LLAMA_MODEL_PATH` environment
variable at your preferred `.gguf` file before starting the backend.

```bash
mkdir -p models
wget -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf
```

## Backend setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn "llama-cpp-python==0.2.*"

# Optional: override if your model lives elsewhere
export LLAMA_MODEL_PATH=/absolute/path/to/model.gguf

uvicorn backend.app:app --reload --port 8000
```

The service validates that the model file exists at startup and will raise a
clear error if it cannot be located. Adjust `LLAMA_CPP_THREADS` to tune CPU
usage.

## Frontend setup

The refreshed frontend is a framework-free HTML experience that exposes
controls for the backend URL, temperature, max tokens, and an optional system
instruction. Serve it with any static file server:

```bash
cd frontend
python -m http.server 3000
```

Open <http://localhost:3000> and start chatting. Update the “Backend URL” field
inside the UI if your API runs elsewhere and provide a system instruction to
steer the assistant’s behaviour.

## Customisation ideas

* Seed the conversation with a system message in `frontend/index.html` for a
  custom persona.
* Expose additional generation parameters such as `top_p` or `repeat_penalty`
  by extending the `ChatRequest` model in `backend/app.py`.
* Deploy behind HTTPS by placing the FastAPI app behind a proxy like Caddy or
  nginx and adjusting CORS origins accordingly.
