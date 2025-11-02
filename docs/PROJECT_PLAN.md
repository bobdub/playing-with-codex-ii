# Chat Garden Enhancement Plan

This plan builds on the current architecture described in [`IMPLEMENTATION.md`](./IMPLEMENTATION.md). Each workstream references the existing state model, rendering pipeline, and event flow documented there to ensure upgrades integrate smoothly with the live static prototype.

## Phase 1 · Observability and caretaker feedback

**Objective:** Give caretakers immediate insight into how the synthesis engine is behaving so they can decide when to plant more knowledge seeds.

1. **Instrument conversation strategies**  
   - Extend `state.metrics` (see *State model and persistence*) to include counts for seed-matched and fallback garden replies.  
   - Recompute these totals in `refreshMetrics()` (per *Metrics and streak calculations*) using each message’s `meta.strategy`.  
   - Surface the new values within the Telemetry panel by expanding `renderMetrics()` and the corresponding HTML scaffold (*Rendering pipeline*).
2. **Highlight stale tending streaks**  
   - Add UI affordances in `renderHero()` when `state.streak.lastTended` exceeds 48 hours (e.g., warning text or accent color) so caretakers notice lapses quickly.
3. **Expose similarity context in the feed**  
   - Enhance `buildFooter()` to include a textual explanation when `meta.similarity` falls below a configurable threshold, guiding caretakers to add more relevant seeds.

## Phase 2 · Knowledge seed management

**Objective:** Make it easier to curate and reuse prompt-response seeds as described in *Seed management*.

1. Add tag-based filtering controls to the seed library (`renderSeeds()` and surrounding UI) so caretakers can browse targeted knowledge sets.
2. Support inline editing of existing seeds by introducing modal or inline forms that update `state.seeds` while preserving persistence through `saveState()`.
3. Provide import tooling alongside the existing export path to merge saved seed collections back into the garden.

## Phase 3 · Response personalization

**Objective:** Explore richer synthesis behaviors without disrupting the vanilla stack outlined in the guide.

1. Experiment with alternative similarity scoring strategies inside `findBestSeed()` (e.g., cosine similarity over term frequency vectors) behind a caretaker-selectable toggle.  
2. Augment `synthesizeResponse()` with optional stylistic overlays (poetic, advisory, playful) keyed to the "Creative drift" slider and stored in seed metadata.  
3. Introduce lightweight analytics—such as per-seed success feedback loops—by enriching the `meta` payload recorded in `addMessage()` and summarizing results in Telemetry.

## Milestones and success criteria

- **Kickoff (this change):** Ship seed vs. fallback instrumentation so caretakers can see how well their seeds are being reused.  
- **Phase 1 complete:** Telemetry reflects strategy usage, streak health, and similarity guidance without regressing existing functionality.  
- **Phase 2 complete:** Seeds are searchable, editable, and portable between browsers.  
- **Phase 3 complete:** Caretakers can experiment with alternative synthesis behaviors and capture feedback for future tuning.

Progress through these phases will be iterative—each milestone should end in a stable, deployable static build so GitHub Pages can be updated at any time.
