# Local TinyLlama Chat Stack

## Setup
1. **Create and activate a Python virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **Install Python dependencies** (FastAPI backend, llama.cpp bindings, model downloader)
   ```bash
   pip install --upgrade pip
   pip install fastapi "uvicorn[standard]" llama-cpp-python huggingface_hub python-multipart
   ```
3. **Prepare directories used by the stack**
   ```bash
   mkdir -p models downloads
   ```
4. **Download the TinyLlama chat model (quantized for CPU inference)**
   ```bash
   huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF \
     tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
     --local-dir downloads
   cp downloads/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf models/
   ```
5. **Set optional environment tuning variables** (recommended for reproducibility)
   ```bash
   export LLAMA_MODEL_PATH="$(pwd)/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
   export LLAMA_CPP_THREADS="$(nproc)"
   # Comma-separated list of allowed web origins for the FastAPI CORS policy
   export FRONTEND_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
   ```

## Backend Code
The FastAPI application lives in [`backend/app.py`](../backend/app.py) and performs the following:
- Loads the TinyLlama GGUF model with `llama_cpp.Llama` on startup (see `_load_model`).
- Exposes `POST /chat`, expecting an array of `{role, content}` messages and returning the generated reply.
- Provides `GET /healthz` for quick status checks.
- Uses a threading lock so multiple HTTP requests cannot initialize the model concurrently.
- Allows overrides through environment variables `LLAMA_MODEL_PATH` and `LLAMA_CPP_THREADS`.

## Front-End Code
The static UI in [`frontend/index.html`](../frontend/index.html) offers a lightweight chat surface:
- Responsive layout with dark-friendly styling.
- Sends the transcript plus new prompt to the backend via `fetch("/chat")`.
- Streams conversation history within the page and displays any HTTP or network errors.
- Assumes the backend is reachable at `http://localhost:8000` (adjust via reverse proxy if needed).

## Run Instructions
1. **Launch the backend API**
   ```bash
   source .venv/bin/activate
   uvicorn backend.app:app --host 0.0.0.0 --port 8000
   ```
2. **Serve the front-end from another shell**
   ```bash
   source .venv/bin/activate
   python -m http.server 3000 --directory frontend
   ```
3. Open a browser to `http://localhost:3000` and start chatting.

## Verification
1. **Health check**
   ```bash
   curl http://localhost:8000/healthz
   ```
   Expect `{"status": "ok"}` while the backend is running.
2. **Smoke test via API**
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
   ```
   A valid response returns JSON with a `reply` field containing the model output.
3. **UI round trip**
   - Load the front-end page.
   - Submit a prompt and confirm the reply is rendered under “Model”.

## Troubleshooting
- **Model file not found**: Ensure the GGUF file exists at `models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` or set `LLAMA_MODEL_PATH` to the correct absolute path.
- **Slow responses on CPU**: Lower `max_tokens` in the request or export `LLAMA_CPP_THREADS=4` (or similar) to balance load.
- **CORS errors when hosting elsewhere**: Update the `FRONTEND_ORIGINS` environment variable (comma separated) to include your front-end host before starting the backend.
- **Port conflicts**: Change the ports passed to `uvicorn` and `python -m http.server`, then update the fetch URL in `frontend/index.html` accordingly.
