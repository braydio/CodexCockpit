
from app.codex.models import MODEL_REGISTRY
from app.codex.codex_sdk import CodexSDKDriver
from app.codex.local_driver import LocalModelDriver

def get_driver(model_name: str):
    spec = MODEL_REGISTRY.get(model_name)
    if not spec:
        raise ValueError(f"Unknown model: {model_name}")

    if spec.runtime == "codex":
        return CodexSDKDriver()

    if spec.runtime == "local":
        return LocalModelDriver(spec)

    raise ValueError("Invalid model runtime")
