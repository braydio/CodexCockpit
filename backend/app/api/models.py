# backend/app/api/models.py

from fastapi import APIRouter, HTTPException, Query
import httpx

from app.codex.models import MODEL_REGISTRY, ModelSpec

router = APIRouter()


def _serialize_model(name: str, spec: ModelSpec) -> dict[str, object]:
    """Serialize a model registry entry for API responses."""
    return {
        "name": name,
        "type": spec.runtime,
        "endpoint": spec.endpoint,
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


@router.get("/ollama/tags")
async def list_ollama_tags(
    endpoint: str = Query(..., description="Ollama base URL, e.g. http://localhost:11434"),
):
    """Fetch available Ollama models from the supplied endpoint."""
    base = endpoint.strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=400, detail="endpoint is required")

    url = f"{base}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            payload = resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"ollama endpoint error: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ollama endpoint error: {exc.response.status_code} {exc.response.text}",
        ) from exc

    models = [
        m.get("name")
        for m in (payload.get("models") or [])
        if isinstance(m, dict) and m.get("name")
    ]
    return {"endpoint": base, "models": models}
