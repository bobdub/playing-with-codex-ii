# Codex II Chat Garden

[Live Site](https://bobdub.github.io/playing-with-codex-ii/)

Codex II is a local-first chat interface that lets you speak to an LLM running on your
own machine. The app is a single static page (`index.html`) that calls a lightweight
HTTP endpoint you host at `/api/chat`. Persona prompts are stored in the browser so you
can iterate on tone and instructions without relying on remote services.

## Key features

- **Local privacy by design** – all chat history stays in the browser until your backend
  chooses to persist it.
- **Customisable system persona** – edit the bot personality in the side panel; the value
  is written to `localStorage` and reloaded on refresh.
- **Graceful offline state** – if the `/api/chat` endpoint is unreachable the UI shows an
  informative fallback instead of failing silently.
- **Accessible, responsive UI** – semantic markup with ARIA roles, keyboard friendly
  forms, and a layout that adapts from desktop to narrow screens.

## Quick start

1. Run the bundled development server: `python server.py` (use `--port` to change the port).
2. Visit `http://localhost:8000` (or the host/port you selected) and start chatting.
3. When you're ready, swap the demo backend for your model process by handling `POST /api/chat`.

The frontend expects JSON shaped like the following:

```json
{
  "reply": "Hello from your local model!"
}
```

Additional fields may be returned, but only `reply` is rendered.

## Expected backend contract

The chat form sends a request with this payload:

```json
{
  "message": "User prompt",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "persona": "System instructions for the model"
}
```

Implementations can use `history` and `persona` to maintain context when calling an LLM.
Always return within a reasonable time; the UI disables the **Send** button while waiting
but does not apply client-side timeouts. The included `server.py` script simply echoes
the user's latest message so you can validate the UI before wiring up a real model.

## Persona controls

- **Save persona** – persists the textarea contents to `localStorage` and applies the new
  prompt immediately.
- **Reset to default** – restores the built-in guidance: “You are a thoughtful guide rooted
  in the values of privacy, open tooling, and gentle curiosity. Answer with clarity,
  warmth, and grounded imagination.”

When the persona is updated, a system message confirms the change and future requests use
that value.

## Styling and layout

The UI lives entirely inside `index.html`. Styles are written in modern CSS and rely on
`color-mix`, CSS variables, and smooth scrolling. Older browsers may fall back to instant
scrolling but retain core functionality.

### Message rendering

- Messages are cloned from a `<template id="message-template">` node for consistency.
- Typing indicators use a `<template id="typing-template">` with a spinner that meets
  accessible status announcement patterns.
- History is appended to the `state.history` array so the backend receives full context.

### Storage utilities

`localStorage` access is wrapped in `loadPersona()` and `persistPersona()` functions with
try/catch protection so private browsing modes or blocked storage do not break the UI.

## Further reading

Extensive design notes, backend ideas, and deployment tips are collected in
[`docs/ChatGardenGuide.md`](docs/ChatGardenGuide.md).
