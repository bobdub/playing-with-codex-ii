# playing-with-codex-ii

Welcome to a playful little lab for chatting with a locally hosted large
language model (LLM). The project stays intentionally small so you can spin it
up in minutes, experiment freely, and remix it into your own creative console.

## Jump straight into a conversation

Want to see the experience before wiring anything together? Open the GitHub
Pages build at [`docs/index.html`](docs/index.html). It serves the same static
client that lives in `frontend/`, so you can tinker with temperature, max
tokens, and system prompts right from the browser. Point the **Backend URL**
field at your running FastAPI instance (typically `http://localhost:8000`) and
start chatting.

## How the pieces fit together

| Path | What you'll find |
| --- | --- |
| `backend/app.py` | A FastAPI service that offers a `/chat` endpoint backed by [`llama.cpp`](https://github.com/ggerganov/llama.cpp). |
| `frontend/index.html` | A zero-dependency HTML/JS client that streams conversations to and from the backend. |
| `models/` | Drop your `.gguf` model weights here so the backend can discover them. |

## What you need before you start

1. **Python 3.9+** with `pip` available.
2. **A C compiler toolchain** for `llama-cpp-python`. On Debian/Ubuntu run
   `sudo apt-get update && sudo apt-get install build-essential`.
3. **A GGUF model file.** Compact options such as
   [`TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF`](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF)
   are perfect for quick experiments.

### Grab a model checkpoint

Store a model in `models/` or point the `LLAMA_MODEL_PATH` environment variable
at a different `.gguf` file before launching the backend. The app double-checks
that the file exists when it boots.

```bash
mkdir -p models
wget -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf

# Optional: point the backend at a different weight file.
export LLAMA_MODEL_PATH=/absolute/path/to/another-model.gguf
```

## Bring the backend to life

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

uvicorn backend.main:app --reload --port 8000

# Or lean on python -m uvicorn to resolve the entrypoint module.
python -m uvicorn backend.main:app --reload --port 8000
```

The server confirms that your model path is valid on startup. Adjust
`LLAMA_CPP_THREADS` whenever you need to balance speed and CPU headroom.

## Light up the frontend

The frontend keeps things simple—just HTML, CSS, and a splash of JavaScript—so
you can host it anywhere:

```bash
cd frontend
python -m http.server 3000
```

Visit <http://localhost:3000>, plug in your backend URL, and (optionally) add a
system instruction to steer the assistant’s vibe.

## Remix ideas

* Seed the chat with a custom persona in `frontend/index.html`.
* Add more generation controls—`top_p`, `repeat_penalty`, or your favourite
  knobs—by extending the `ChatRequest` model in `backend/app.py`.
* Put the FastAPI app behind HTTPS with a proxy such as Caddy or nginx and
  tweak the CORS settings to match.

## Ship it as an Android app

An Android wrapper lives in [`android/`](android/README.md). It packages the web
console inside a WebView so you can install it on phones or publish it through
the Play Store. Open the directory in Android Studio (or install Gradle 8.7+,
generate the wrapper, and run `./gradlew assembleDebug`) to produce an APK. The
build automatically copies the latest `frontend/index.html` so the mobile shell
always matches the web console.
