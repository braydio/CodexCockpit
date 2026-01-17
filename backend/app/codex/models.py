from dataclasses import dataclass

@dataclass
class ModelSpec:
    """Describes a selectable model and its runtime configuration."""

    name: str
    runtime: str        # "codex" | "local"
    endpoint: str | None
    adapter: str | None
    executable_path: str | None
    timeout_s: int | None
    context: int
    tools: bool

MODEL_REGISTRY = {
    "codex-default": ModelSpec(
        name="codex-default",
        runtime="codex",
        endpoint=None,
        adapter=None,
        executable_path=None,
        timeout_s=None,
        context=128000,
        tools=True,
    ),
    "local-qwen": ModelSpec(
        name="local-qwen",
        runtime="local",
        endpoint=None,
        adapter="ollama",
        executable_path="/usr/local/bin/ollama",
        timeout_s=120,
        context=32768,
        tools=False,
    ),
}
