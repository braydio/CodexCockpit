from dataclasses import dataclass

@dataclass
class ModelSpec:
    name: str
    runtime: str        # "codex" | "local"
    endpoint: str | None
    context: int
    tools: bool

MODEL_REGISTRY = {
    "codex-default": ModelSpec(
        name="codex-default",
        runtime="codex",
        endpoint=None,
        context=128000,
        tools=True,
    ),
    "local-qwen": ModelSpec(
        name="local-qwen",
        runtime="local",
        endpoint="http://localhost:8080/v1",
        context=32768,
        tools=False,
    ),
}
