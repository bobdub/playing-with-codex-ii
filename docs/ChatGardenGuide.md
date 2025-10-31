# Chat Garden Guide

This guide collects practical knowledge for caretakers building on top of the Codex II
chat interface. It explains how the single-page application is organised, how the UI
communicates with a backend LLM service, and how to adapt the experience for different
workflows.

---

## 1. Application anatomy

Codex II ships as a static bundle. The entire interface—markup, styles, and behaviour—lives
in [`index.html`](../index.html). Key regions:

| Section | Purpose |
| --- | --- |
| `<header>` | Introduces the experience and explains the local-first philosophy. |
| `<main>` | Contains two panels: the chat transcript and the persona editor. |
| `<footer>` | Reminds the caretaker to run a backend on `/api/chat`. |
| `<template>` nodes | Provide reusable blueprints for chat messages and typing indicators. |
| `<script>` closure | Implements state management, DOM helpers, storage, and networking. |

### DOM references

The script queries each interactive element once and caches it:

- `#messages` – scrollable container for transcript entries.
- `#chat-form` and `#chat-input` – the message composer.
- `#send-button` – disabled while awaiting a response to prevent duplicate requests.
- `#persona-input`, `#save-persona`, `#reset-persona` – controls for system prompt edits.
- `#endpoint-input`, `#save-endpoint`, `#reset-endpoint` – let caretakers point the UI at a
  different `/api/chat` URL without editing code.

`state.history` tracks user/bot turns so the backend can build longer conversations.

---

## 2. Running the frontend

The page is plain HTML, so any static file server works:

```bash
python -m http.server 8000
# or
npx serve
```

Open the served URL in a browser. Modern Chromium, Firefox, and Safari builds are tested;
Edge works via Chromium compatibility. No bundling step is required, making the project
ideal for air-gapped or minimal environments.

---

## 3. Backend expectations

The frontend sends `POST /api/chat` with JSON. Every request includes:

- `message` – the latest user input.
- `history` – ordered list of prior turns `{ role, content }`.
- `persona` – current system instructions (defaults to a privacy-respecting guide).

Return JSON shaped like `{ "reply": "..." }`. Additional keys can hold debug info or
usage metrics, but only `reply` is rendered.

### Example adapter (Python FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]]
    persona: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
    prompt = build_prompt(req.persona, req.history, req.message)
    reply = call_local_llm(prompt)
    return {"reply": reply}
```

When the endpoint fails, the UI displays a friendly message encouraging the caretaker to
"wake a local model" and includes the thrown error message to aid debugging.

---

## 4. Persona lifecycle

Persona text persists in `localStorage` under the key `codex-ii::persona-user`.

1. On load, `loadPersona()` reads from storage, falling back to the default string if
   storage is unavailable or empty.
2. Saving writes the trimmed textarea value (or default) and posts a system note to the
   transcript.
3. Resetting restores the default persona and records a confirmation message.

This flow allows experimentation with tone, guardrails, or special behaviours for different
projects while remaining entirely client-side.

---

## 5. Endpoint targeting

Caretakers can adjust the chat backend without rebuilding the page:

1. `loadEndpoint()` reads the stored value (`codex-ii::chat-endpoint`) and falls back to
   the default `/api/chat` path when unset.
2. Saving normalises the input (adding `http://` when a scheme is missing) so entries like
   `localhost:9000/api/chat` work without fuss.
3. Resetting removes the stored value and returns to the same-origin `/api/chat`.

The resolved URL is used for every `fetch` call, and the transcript records system
messages whenever the target changes so caretakers have an audit trail.

---

## 6. Message flow breakdown

1. User submits the form – empty or whitespace-only prompts are ignored.
2. UI pushes the user turn into `state.history` and renders it immediately.
3. A typing indicator element is inserted using the `#typing-template` blueprint.
4. `fetch(state.endpoint, …)` sends the payload to the selected backend URL.
5. On success, the reply is appended via `appendBotMessage()` and captured in history.
6. On failure, a fallback message is appended instead of leaving the transcript blank.
7. The typing indicator is removed, and the send button is re-enabled.

`scrollToBottom()` attempts smooth scrolling with `Element.scrollTo({ behavior: 'smooth' })`
and falls back gracefully if unsupported.

---

## 7. Styling notes

- The gradient background and `backdrop-filter` effects create a soft glassmorphism aesthetic.
- Components rely on CSS variables declared on `:root` for colour theming.
- `@media` queries collapse the two-column layout into a single column under 960px width.
- Animations use the `fadeUp` keyframes and a spinner for live feedback.

Customising the palette involves adjusting the CSS variables at the top of the file.

---

## 8. Accessibility considerations

- Screen reader-only labels (`.sr-only`) accompany key inputs.
- `aria-live="polite"` on the messages container ensures announcements without interrupting
the reader.
- Buttons and textareas use native elements to preserve keyboard interactions.
- The typing indicator exposes `role="status"` and `aria-label` for assistive feedback.

When extending the UI, follow these patterns so the interface stays inclusive.

---

## 9. Persistence and error resilience

`loadPersona()`, `persistPersona()`, `loadEndpoint()`, and `persistEndpoint()` catch
`localStorage` exceptions to avoid crashes in private browsing sessions. Network errors are
surfaced in-line with diagnostic text, making backend debugging quicker during development.

---

## 10. Deployment checklists

- [ ] Serve the static files with correct MIME types (HTML, CSS-inlined, JS).
- [ ] Configure HTTPS if exposing beyond localhost; browsers block some APIs on insecure
      origins.
- [ ] Apply CORS headers on the backend if the frontend and API live on different origins.
- [ ] Rate limit or authenticate the backend endpoint as needed—everything else runs locally.
- [ ] Monitor backend latency so the UI feels responsive; consider streaming responses for
      long generations.

---

## 11. Extending the experience

Ideas for future caretakers:

- **Streaming support** – replace the single `fetch` with Server-Sent Events or WebSockets
  to stream tokens into the transcript.
- **Conversation export** – add a download button that serialises `state.history` to a file
  so transcripts can be archived.
- **Multi-persona presets** – store preset personas in JSON and let users switch with a
  dropdown.
- **Model status indicator** – poll a health endpoint and display the active model or queue
  length in the footer.

Document new behaviours in this guide to keep institutional knowledge alive.

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Messages never arrive | Backend not running or wrong port | Start the `/api/chat` service and confirm CORS settings |
| Persona changes vanish on refresh | Browser blocked storage | Check private mode settings or allow storage for the site |
| Layout looks unstyled | Serving `index.html` without MIME headers | Use a static server instead of opening the file directly |
| Smooth scrolling absent | Browser lacks `scrollTo` smooth support | Behaviour falls back automatically; no action required |

---

## 13. Related documents

- [`README.md`](../README.md) – Quick start summary for new contributors.
- [`docs/Goals.md`](Goals.md) – High-level objectives for the project.
- [`MemoryGarden.md`](../MemoryGarden.md) – Living caretaker reflections.

Add new references here as you grow the garden.
