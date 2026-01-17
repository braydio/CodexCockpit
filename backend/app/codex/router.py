
from app.codex.model_adapters import ModelAdapter, OllamaAdapter
from app.codex.models import MODEL_REGISTRY, ModelSpec
from app.codex.codex_sdk import CodexSDKDriver
from app.codex.local_driver import LocalModelDriver


def _build_adapter(spec: ModelSpec) -> ModelAdapter:
    """Build a local model adapter from the supplied spec."""
    if spec.adapter == "ollama":
        if not spec.executable_path:
            raise ValueError(f"Ollama executable path missing for {spec.name}.")
        timeout_s = spec.timeout_s or 120
        return OllamaAdapter(spec.executable_path, spec.name, timeout_s=timeout_s)

    raise ValueError(f"Unsupported adapter: {spec.adapter}")


def get_driver(model_name: str):
    """Resolve a model name into a configured Codex driver."""
    spec = MODEL_REGISTRY.get(model_name)
    if not spec:
        raise ValueError(f"Unknown model: {model_name}")

    if spec.runtime == "codex":
        return CodexSDKDriver()

    if spec.runtime == "local":
        adapter = _build_adapter(spec)
        return LocalModelDriver(spec, adapter)

    raise ValueError("Invalid model runtime")
