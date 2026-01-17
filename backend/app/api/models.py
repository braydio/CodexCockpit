# backend/app/api/models.py

from fastapi import APIRouter

from app.codex.models import MODEL_REGISTRY, ModelSpec

router = APIRouter()


def _serialize_model(name: str, spec: ModelSpec) -> dict[str, object]:
    """Serialize a model registry entry for API responses."""
    return {
        "name": name,
        "type": spec.runtime,
        "context": spec.context,
        "tools": spec.tools,
    }


@router.get("/")
def list_models():
    """List available models from the central model registry."""
    models = [
        _serialize_model(name, spec)
        for name, spec in sorted(MODEL_REGISTRY.items())
    ]
    return {"models": models}
