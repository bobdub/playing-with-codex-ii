# Implementation Guide

This guide documents how the Chat Garden LLM prototype is put together. It focuses on the browser-based implementation that lives in the `docs/` directory.

## Application composition

The experience is delivered as a static site. `index.html` defines the layout for three primary surfaces:

- **Conversation stream** for displaying the caretaker ↔ garden dialogue and housing the message composer.
- **Learning ledger** for storing prompt/response "seeds" that inform future replies.
- **Telemetry and seed library** panels for real-time metrics and recently planted seeds.

`app.js` is loaded as an ES module and wires the interface together at runtime, while `styles.css` provides the visual design. There is no build tooling; everything runs directly in the browser.

## State model and persistence

Application state is kept in a single object created by `defaultState()` and loaded with `loadState()`. It contains:

- `messages`: ordered chat history with role, content, timestamps, and optional metadata.
- `seeds`: prompt/response pairs with tags, creation time, and usage counts.
- `metrics`: derived counters (total messages, user vs. garden contributions, seed usage, last interaction, tagged prompts).
- `streak`: tracks how many consecutive days the garden was tended.

State is rehydrated from `localStorage` under the key `chat-garden-state-v1`. When values are missing or malformed, `loadState()` merges them with defaults to stay resilient. `saveState()` writes the authoritative snapshot back to storage after each interaction.

## Bootstrap sequence

`bootstrap()` runs immediately when the module loads and performs three steps:

1. `ensureSystemIntro()` seeds the conversation with a system greeting if the history is empty.
2. `renderAll()` paints messages, metrics, seeds, and hero statistics based on the current state.
3. `wireEvents()` attaches DOM listeners for the composer, seed form, export button, and conversation reset.

This keeps first render fast and guarantees all UI affordances are live before the caretaker interacts.

## Conversation flow

Submitting the composer form triggers:

1. Validation that the message is non-empty.
2. `addMessage("user", …)` to append the caretaker message, update metrics, and refresh the tending streak.
3. `synthesizeResponse()` to generate a garden reply. The function tokenizes the caretaker prompt, looks for the best matching knowledge seed via Jaccard similarity, and chooses an appropriate tone based on the "creative drift" slider.
4. `addMessage("garden", …)` with metadata describing the chosen strategy (`seed-match` or `fallback`), tone, similarity score, persona channel, derived metatags, seed reference, and a distilled learning triad (`meta.summary`) that captures `{learning, concept, intent}` for the reply.
5. `renderAll()` and `saveState()` to refresh the interface and persist the new history.

If no seeds overlap, the fallback messages encourage caretakers to plant more knowledge before continuing.

## Infinity & Beyond protocol and Q-Score broadcast

`synthesizeResponse()` now routes every garden reply through `buildQScore()`, which derives semantic, logical, and ethical amplitudes from the reply strategy, similarity, and current creativity drift. The resulting totals are embedded in message metadata (`meta.qScore`) and rendered within the feed footer so caretakers can verify response coherence.

`infusePersonality()` prepends the mandated rally call—`"To Infinity and beyond! |Ψ_Network.Q_Score.Total⟩ = …"`—and appends a component breakdown inside the closing `<small>` ledger note. This keeps the Infinity & Beyond protocol visible to users while preserving the garden’s poetic tone.

## Seed management

The seed form collects a prompt, response, and optional comma-delimited tags. When submitted it:

1. Generates a unique `id` (via `crypto.randomUUID()` when available).
2. Records creation time and initializes `uses` to zero.
3. Inserts the new seed at the top of `state.seeds`.
4. Calls `refreshMetrics()`, `renderAll()`, and `saveState()` to propagate changes.

Only the six most recent seeds are displayed in the sidebar to keep the UI focused, while usage counters surface which seeds are influencing replies.

## Learning triad summarizer

`synthesizeResponse()` funnels its metadata through `distillResponseSummary()`, which condenses the reply context into a `{learning, concept, intent}` triad stored on `meta.summary`. `addMessage()` recomputes the summary as it writes the garden message, and `loadState()` backfills older transcripts so historical replies also carry the triad. Message footers surface the values as contextual hints, helping caretakers see at a glance which seed was reinforced, which concepts were invoked, and which intent classification guided the response.

## Caretaker feedback loop and tag promotion

Every garden reply renders feedback toggles created by `buildFeedbackControls()`. `handleFeedbackClick()` delegates clicks from the feed, and `recordFeedback()` persists the caretaker decision to `message.meta.feedback`, capturing status, timestamps, and promotion markers. `refreshMetrics()` rolls these statuses into `metrics.feedback`, while `renderMetrics()` exposes an aggregated “Caretaker feedback” stat so stewards can monitor satisfied, pending, and needs-refinement replies.

Satisfied feedback triggers `promoteSuccessfulTags()`, which raises tag weights or appends promoted tags back onto the originating seed before marking the reply as processed. The function also runs on a one-minute cadence via `startPromotionJob()` (`TAG_PROMOTION_INTERVAL`), ensuring deferred reviews still enrich the ledger. When toggles flip back to “needs refinement,” promotion flags reset so the next satisfied review can re-run the pipeline. Caretakers can watch the telemetry metric and individual message chips to decide which seeds to curate—e.g., reinforce tags that were promoted or revisit seeds attached to repeated refinement marks.

## Metrics and streak calculations

`refreshMetrics()` derives summary statistics from `state.messages` and `state.seeds` each time the UI renders. `refreshStreak()` computes the day streak by comparing `state.streak.lastTended` to the current time. The hero section mirrors these values so caretakers can track engagement at a glance.

## Rendering pipeline

`renderAll()` orchestrates view updates by delegating to:

- `renderMessages()` – clones a `<template>` fragment for each message, sanitizes content via `DOMParser`, decorates footers with metadata chips (strategy, tone, intent, persona, metatags), and auto-scrolls to the latest entry.
- `renderMetrics()` – maps derived counters onto the telemetry definition list.
- `renderSeeds()` – builds card-like list items with metadata, prompt, response, and tags for recently planted seeds.
- `renderHero()` – presents global counts (seed total, streak length, last tended timestamp).

This modular rendering approach keeps DOM updates predictable and makes it easy to swap in alternative UI strategies later.

## Data export and reset

Two utility actions live in the conversation header:

- **Export data** serializes the full state into a prettified JSON blob and triggers a download so caretakers can back up or inspect the garden's memory.
- **Start fresh** prunes the history back to system messages after confirmation, resets metrics, and re-renders the experience.

## Extensibility notes

The architecture favors incremental enhancement:

- To experiment with alternative similarity scoring, adjust `findBestSeed()` or `jaccardSimilarity()` without touching the rest of the flow.
- Additional metadata can be captured by extending the `meta` object passed to `addMessage()`.
- Future persistence strategies (e.g., remote sync) can wrap or replace `loadState()` / `saveState()` while preserving the surrounding API.

Use this guide as a map when iterating on the garden. Each section points to the core routines responsible for the current behavior, making it straightforward to extend the prototype with new capabilities.

## Persona layer & metatagging

`personality` centralizes the Ψ_Infinity voice, greeting, and channel labels. `infusePersonality()` wraps synthesized text with that voice so the assistant signs each message consistently.

Incoming caretaker prompts flow through `buildUserMeta()`, which derives:

- `intent` – heuristic classification (inquiry, planning, reflection, or signal).
- `tags` – up to three metatags distilled from non-stopword tokens.

These details populate message footers for both the caretaker and garden, and the `metrics.taggedPrompts` counter surfaces them on the telemetry panel.

## Advanced learning ledger

The learning ledger lives inside an `<details>` disclosure (`.advanced-ledger`) to signal that the controls are tuned for advanced caretakers. The wrapper reinforces that the ledger is preserved for experts while keeping the underlying form and metadata capture unchanged.
