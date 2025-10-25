class Llama:  # pragma: no cover - replaced by tests
    def __init__(self, *args, **kwargs):
        raise RuntimeError("llama_cpp backend not available in test environment")
