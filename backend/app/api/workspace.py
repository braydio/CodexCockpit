# backend/app/api/workspace.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.workspace_fs import (
    WorkspaceSecurityError,
    build_tree,
    read_text_file,
    resolve_workspace_root,
)

router = APIRouter()


class WorkspaceTreeResponse(BaseModel):
    root: str
    tree: dict


class WorkspaceFileResponse(BaseModel):
    root: str
    path: str
    abs_path: str
    size: int
    truncated: bool
    text: str


@router.get("/tree", response_model=WorkspaceTreeResponse)
def get_tree(
    root: str = Query(".", description="Workspace root path on server"),
    max_depth: int = Query(5, ge=1, le=12),
    max_entries: int = Query(5000, ge=100, le=20000),
):
    try:
        ws = resolve_workspace_root(root)
        tree = build_tree(ws, max_depth=max_depth, max_entries=max_entries)
        return {"root": str(ws.root_abs), "tree": tree}
    except (FileNotFoundError, NotADirectoryError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tree error: {e}")


@router.get("/file", response_model=WorkspaceFileResponse)
def get_file(
    root: str = Query(".", description="Workspace root path on server"),
    path: str = Query(..., description="Workspace-relative file path"),
    max_bytes: int = Query(512_000, ge=10_000, le=5_000_000),
):
    try:
        ws = resolve_workspace_root(root)
        payload = read_text_file(ws, path, max_bytes=max_bytes)
        return {"root": str(ws.root_abs), **payload}
    except WorkspaceSecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (FileNotFoundError, IsADirectoryError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File error: {e}")
