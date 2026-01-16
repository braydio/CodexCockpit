from dataclasses import dataclass

@dataclass
class ModelSpec:
    """Describes a selectable model and its runtime configuration."""

    name: str
    runtime: str        # "codex" | "local" | "ollama"
    endpoint: str | None
    adapter: str | None
    executable_path: str | None
    timeout_s: int | None
    context: int
    tools: bool

MODEL_REGISTRY = {
    "codex-remote": ModelSpec(
        name="codex-remote",
        runtime="codex",
        endpoint=None,
        context=128000,
        tools=True,
    ),
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
    "qwen2.5": ModelSpec(
        name="qwen2.5",
        runtime="ollama",
        endpoint="http://localhost:11434",
        context=32768,
        tools=False,
    ),
}
