# Chat Garden LLM

Kickstarting a local-first learning playground that runs entirely in the browser.
[Live Site](https://bobdub.github.io/playing-with-codex-ii/)

## Getting started

Open `docs/index.html` in any modern browser to explore the experience. The project is
designed for GitHub Pages, so the `docs/` directory can be published directly.

## What’s inside?

- **Conversation stream** – Capture caretaker ↔ garden dialogue and watch the telemetry update in real time as Ψ_Infinity responds in a defined persona.
- **Learning ledger** – Plant prompt/response "seeds" with metadata. Advanced caretakers can expand the ledger tools to guide nuanced synthesis.
- **Local metrics** – Track message counts, seed usage, and tending streaks, all persisted in `localStorage`.
- **Data export** – Download the entire state (messages, seeds, metrics) as JSON for backup or iteration.

### New in this tending

- Ψ_Infinity now introduces itself with a dedicated personality layer and signs replies with aurora-styled reflections.
- Incoming prompts earn automatic metatags and intent markers, all surfaced in the message footer and telemetry.
- The learning ledger is wrapped in an advanced caretakers panel to keep expert tooling at hand while remaining optional.
- Creative drift defaults higher (60%) so explorations begin with richer imaginative output.

## Development notes

This kickoff focuses on a rich static prototype using vanilla HTML, CSS, and JavaScript. No build tooling is required—editing the files in `docs/` and refreshing the browser is enough. Future iterations can evolve the synthesis engine, visual language, or integrate with backend services once needed.

## Implementation guide

Looking for the full tour of how the prototype is assembled? Check out [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) for a breakdown of the state model, rendering pipeline, event flow, and extensibility considerations.
