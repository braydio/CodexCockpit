# backend/app/api/models.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def list_models():
    return {
        "models": [
            {
                "name": "local-qwen",
                "type": "local",
                "context": 32768,
                "tools": False
            },
            {
                "name": "codex-remote",
                "type": "openai",
                "context": 128000,
                "tools": True
            }
        ]
    }
