# Baseline Observations

## Coverage Snapshot
- Logged conversations span analytical questions, operational signals, and creative prompts, providing seed-match coverage for core caretaker scenarios.
- Creative and signal transcripts still rely on a small set of legacy seeds, indicating room to diversify tone-specific responses.

## Duplicate Tag Frequency
- `streak-alert` and `aurora-drift` appear across multiple transcripts, signaling healthy reuse but also a risk of over-saturation if new tags are not introduced.
- No duplicate tags were observed within a single transcript, confirming tag hygiene at the conversation level.

## Intent Misclassifications
- Escalation prompts occasionally blend `question.metrics` with `signal.status`, which may mislabel follow-up actions; clarify detection rules to reduce overlap.
- Creative revision requests trend toward `creative.request` instead of `creative.revision`, suggesting the classifier should prioritize contextual cues from prior turns.
