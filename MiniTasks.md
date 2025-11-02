# Mini Tasks Backlog

This backlog tracks focused follow-up efforts for the Chat Garden LLM prototype. Items link back to the broader [Chat Garden Enhancement Plan](docs/PROJECT_PLAN.md) and help caretakers prioritize incremental tendings.

1. **Telemetry instrumentation for reply strategies** – Expand the metrics model so caretakers can distinguish seeded vs. fallback responses at a glance.
2. **Hero streak health indicators** – Surface visual cues in the hero panel when the tending streak exceeds safe thresholds.
3. **Similarity context in conversation feed** – Provide caretakers with contextual messaging and controls whenever a reply relies on low-similarity seeds or fallbacks.

Each mini-task should ship independently while preserving the static deployment footprint (vanilla HTML/CSS/JS served from `docs/`).
