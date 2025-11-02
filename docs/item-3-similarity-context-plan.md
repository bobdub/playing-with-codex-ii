# Mini Task 3 · Similarity Context in the Conversation Feed

## Purpose
Caretakers struggle to understand why Ψ_Infinity occasionally abandons a seed and emits a fallback response. Mini Task 3 ensures the conversation feed communicates when similarity confidence drops, exposes the underlying signals, and invites corrective action (e.g., planting a better seed or adjusting metadata).

## Current Behavior Snapshot
- `synthesizeResponse()` in [`docs/app.js`](./app.js) selects the best seed via `findBestSeed()` and records a `meta.similarity` score plus the chosen strategy (`seed-match` or `fallback`).
- `buildFooter()` renders strategy, intent, persona, metatags, Q-Score, and the learning triad but does **not** surface similarity thresholds or guidance.
- The UI offers no inline control to remediate low-similarity responses beyond the generic "Plant seed" form.

## Goals
1. Visualize similarity confidence for every garden reply without overwhelming high-similarity successes.
2. Alert caretakers when a reply falls below a configurable threshold and explain why fallback text appeared.
3. Provide quick remediation levers (e.g., start a new seed from the current prompt/response or flag the transcript) directly inside the feed.

## Non-Goals
- Replacing the existing Jaccard similarity algorithm (that exploration lives in Phase 3 of the broader plan).
- Introducing remote persistence or authentication.
- Redesigning the entire conversation layout.

## Deliverables
1. **Data Model Enhancements**
   - Extend message metadata with a normalized similarity bucket (`meta.similarityBand`) computed during `synthesizeResponse()`.
   - Persist caretaker acknowledgements (e.g., `meta.similarityAcknowledged = true`) when they dismiss guidance so repeat warnings do not clutter the feed.
2. **UI & Interaction Updates**
   - Add a similarity badge to garden message footers that displays "High", "Medium", or "Low" confidence alongside the numeric score.
   - When similarity is below the warning threshold, append a contextual hint component with:
     - A short explanation referencing the active seed (if any) or fallback reason.
     - CTA buttons: **"Promote as seed"** (pre-populates the seed form with prompt/response), **"Adjust tags"** (opens ledger to edit), and **"Dismiss"** (records acknowledgement).
   - Ensure the hint is accessible (ARIA roles, focus management) and collapses after dismissal.
3. **Configuration & Telemetry**
   - Introduce `config.js` entries for `SIMILARITY_WARNING_THRESHOLD` and `SIMILARITY_CRITICAL_THRESHOLD` so caretakers can tune sensitivity.
   - Expand `refreshMetrics()` to count low-similarity events and expose them via Telemetry (e.g., `metrics.lowSimilarityReplies`).
   - Record caretaker remediation actions in metrics (seed promotions triggered from hints, dismissals, tag adjustments).
4. **Documentation**
   - Update [`docs/IMPLEMENTATION.md`](./IMPLEMENTATION.md) with a new subsection describing similarity bands and UI hints.
   - Document configuration knobs in [`docs/config.js`](./config.js) comments and add usage guidance to [`docs/observations.md`](./observations.md).

## Implementation Phases
1. **Analysis & Design (0.5 day)**
   - Audit existing metadata pipeline (`buildUserMeta()`, `synthesizeResponse()`, `addMessage()`).
   - Define similarity band thresholds and message copy.
   - Mock the hint component structure referencing the styles in `docs/styles.css`.
2. **Data & Logic Wiring (1 day)**
   - Implement similarity band calculation in `synthesizeResponse()` with helper `categorizeSimilarity(similarity)`. Store bands and warning flags on message metadata.
   - Extend `addMessage()` to preserve acknowledgements and ensure historical messages default to "High" when `meta.similarity` is absent.
   - Add metric aggregation for low-similarity counts and remediation actions inside `refreshMetrics()`.
3. **UI Implementation (1.5 days)**
   - Update the message template in `renderMessages()` to include similarity badges and conditional hint blocks.
   - Create CSS styles for badges (color-coded) and hint containers ensuring responsive behavior.
   - Wire CTA buttons: pre-fill the seed form by calling `prefillSeedFormFromMessage(message)` and reveal ledger controls when invoked.
   - Implement dismissal handling in `handleMessageAction()` (new delegate) that toggles `meta.similarityAcknowledged` and re-renders.
4. **Configuration & Testing (0.5 day)**
   - Add configurable thresholds and defaults in `docs/config.js`.
   - Write node-based tests in `tests/intent.test.js` (or new `similarity.test.js`) covering band categorization, metric aggregation, and acknowledgement persistence.
   - Verify manual flows in the browser (seed promotion, dismissal, telemetry updates).
5. **Documentation & Review (0.5 day)**
   - Update relevant docs, capture before/after screenshots for caretakers, and summarize behavior in release notes.

Total estimated effort: **~4 days**.

## Risks & Mitigations
- **UI clutter**: Keep hint copy concise and allow dismissal; use color semantics aligned with existing design tokens.
- **State drift after dismissal**: Persist acknowledgement immediately via `saveState()` and include guard rails in `loadState()` to hydrate missing flags.
- **Seed promotion duplication**: When caretakers promote from hints, ensure the deduplication logic checks for identical prompt/response pairs before inserting.

## Success Metrics
- Less than 5% of fallback responses lack an accompanying explanation.
- At least 50% of low-similarity events lead to one of the remediation actions within 7 days (tracked via telemetry).
- Caretaker satisfaction (captured via existing feedback toggles) improves for previously low-confidence replies.

## Follow-Up Opportunities
- Experiment with alternative similarity algorithms under a feature flag.
- Feed similarity bands into the Q-Score calculation for richer harmonic reporting.
- Surface historical trend lines for low-similarity replies inside the Telemetry panel.
