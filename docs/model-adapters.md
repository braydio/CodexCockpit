# Model Adapters

Local model execution is routed through adapter classes under
`backend/app/codex/model_adapters.py`. Adapters provide a minimal interface with
`generate(prompt: str) -> str`, which lets the Codex driver remain model-neutral
while satisfying the explicit binary requirements in `RULES.md`.

## Ollama Adapter

The `OllamaAdapter` executes the Ollama CLI using an explicit executable path.
This avoids relying on implicit shell PATH lookups. The adapter configuration
lives in `backend/app/codex/models.py` as part of the `ModelSpec` entries.

Example configuration:

```
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
```

Update `executable_path` to point at your local Ollama binary, and ensure the
model name matches the model you have pulled locally (for example
`ollama pull qwen2.5`).

## Environment Setup

- Install Ollama and confirm the binary path on your system.
- Configure the `ModelSpec` entry with the explicit executable path.
- Run the backend as usual with `cd backend && ./run.sh`.
