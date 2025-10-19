# Prompt for gpt-5-codex

You are gpt-5-codex operating inside a temporary Linux container with Python,
`pip`, and basic CLI tools available. The user cannot provide proprietary API
keys or rely on long-lived cloud servers. Your task is to deliver everything
needed to stand up a simple chat website that talks to an open-source LLM using
only local resources or public, unauthenticated downloads.

## Goals
1. Provide a step-by-step setup guide that installs the minimum dependencies
   (e.g., `huggingface_hub`, `transformers`, and a lightweight inference backend
   such as `llama.cpp`, `text-generation-inference`, or `text-generation-webui`)
   that can run completely inside this container without secret tokens.
2. Produce the front-end source code for a minimal web UI (HTML/JS or a
   framework like Streamlit) that lets a user enter prompts and display model
   responses.
3. Show the Python (or Node) backend code necessary to load a small,
   license-friendly model from Hugging Face, run inference, and expose the chat
   endpoint that the front-end calls.
4. Include runnable commands for launching the backend and front-end inside the
   container, plus any verification steps to confirm the system works.

## Constraints & Context
- Assume no outbound network access once the solution starts running, so cache
  or download all required models during setup.
- Use only models and datasets that are publicly accessible without API keys.
- Document any environment variables, ports, or file paths that must be set.
- Keep resource usage modest (target models ≈7B parameters or smaller) so they
  can run on CPU if GPU acceleration is unavailable.
- Ensure the instructions are reproducible from a clean checkout of this
  repository.

## Deliverables
- Ordered list of setup commands with brief explanations.
- Backend source file(s) with comments explaining the flow from HTTP request to
  model inference.
- Front-end source file(s) that demonstrate a functional chat interface.
- Testing or smoke-check instructions to prove the stack is working end to end.
- Any troubleshooting tips for common failure cases in this environment.

Respond with clearly separated sections for **Setup**, **Backend Code**,
**Front-End Code**, **Run Instructions**, **Verification**, and **Troubleshooting**.
