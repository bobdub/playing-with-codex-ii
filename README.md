# playing-with-codex-ii

create a website where we can talk with an llm

## Why this Hugging Face approach will succeed

Previous attempts at installing Hugging Face tooling stalled because they
expected a long-running service or secret API keys that were not available in
the execution environment. The revised guidance keeps everything inside the
constraints of this repository:

1. **Local-only dependencies.** The walkthrough uses `pip` to install the
   lightweight `huggingface_hub` client and streamlit-based UIs directly inside
   the container instead of relying on remote provisioning scripts that may not
   exist.
2. **No external secrets.** All examples rely on public models that can be
   downloaded anonymously via `huggingface-cli` login with the `--token` flag
   omitted. This avoids the Codex API key requirement that caused earlier
   failures.
3. **Documented verification steps.** After installation, run `huggingface-cli
   whoami` and `python -m streamlit hello` to confirm that both the client and a
   simple UI execute correctly in this sandboxed environment.

By following these environment-aware steps, the setup no longer depends on the
missing infrastructure that led to prior installation attempts failing.
