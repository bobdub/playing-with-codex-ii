# Chat Garden LLM

Kickstarting a local-first learning playground that runs entirely in the browser.
[Live Site](https://bobdub.github.io/playing-with-codex-ii/)

## Getting started

Open `docs/index.html` in any modern browser to explore the experience. The project is
designed for GitHub Pages, so the `docs/` directory can be published directly.

## What’s inside?

- **Conversation stream** – Capture caretaker ↔ garden dialogue and watch the telemetry update in real time.
- **Learning ledger** – Plant prompt/response "seeds" with metadata. The garden references these to shape its replies.
- **Local metrics** – Track message counts, seed usage, and tending streaks, all persisted in `localStorage`.
- **Data export** – Download the entire state (messages, seeds, metrics) as JSON for backup or iteration.

## Development notes

This kickoff focuses on a rich static prototype using vanilla HTML, CSS, and JavaScript. No build tooling is required—editing the files in `docs/` and refreshing the browser is enough. Future iterations can evolve the synthesis engine, visual language, or integrate with backend services once needed.
