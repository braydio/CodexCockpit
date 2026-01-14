# backend/app/core/workspace_fs.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_IGNORES = {
    ".git",
    ".hg",
    ".svn",
    ".DS_Store",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    ".turbo",
    ".next",
    ".cache",
    ".idea",
    ".vscode",
}


@dataclass(frozen=True)
class ResolvedWorkspace:
    root_abs: Path


class WorkspaceSecurityError(Exception):
    pass


def _realpath(p: Path) -> Path:
    # resolve() can throw if path doesn't exist in some modes; realpath is more tolerant.
    return Path(os.path.realpath(str(p)))


def resolve_workspace_root(root: str) -> ResolvedWorkspace:
    root_path = Path(root).expanduser()
    root_real = _realpath(root_path)

    if not root_real.exists():
        raise FileNotFoundError(f"Workspace root does not exist: {root_real}")
    if not root_real.is_dir():
        raise NotADirectoryError(f"Workspace root is not a directory: {root_real}")

    return ResolvedWorkspace(root_abs=root_real)


def resolve_under_root(ws: ResolvedWorkspace, rel_path: str) -> Tuple[Path, str]:
    """
    Safely resolve a user-provided path under the workspace root.

    Returns:
      (absolute_path, normalized_relative_path)

    Rejects:
      - absolute paths outside root
      - paths with .. that escape root
      - symlinks that escape root
    """
    rel = rel_path.strip().lstrip("/").lstrip("\\")
    if rel == "":
        rel = "."

    requested = Path(rel)

    # Construct and realpath to resolve symlinks and .. components.
    candidate = _realpath(ws.root_abs / requested)

    root_real = ws.root_abs
    try:
        # Python 3.9+: Path.is_relative_to
        is_inside = candidate.is_relative_to(root_real)  # type: ignore[attr-defined]
    except Exception:
        # Fallback: string prefix guard (robust enough with realpaths + path separators)
        root_str = str(root_real)
        cand_str = str(candidate)
        is_inside = cand_str == root_str or cand_str.startswith(root_str + os.sep)

    if not is_inside:
        raise WorkspaceSecurityError("Path escapes workspace root")

    rel_norm = os.path.relpath(str(candidate), str(root_real))
    rel_norm = rel_norm.replace("\\", "/")
    if rel_norm == ".":
        rel_norm = ""

    return candidate, rel_norm


def _should_ignore(name: str, ignores: set[str]) -> bool:
    return name in ignores


def build_tree(
    ws: ResolvedWorkspace,
    max_depth: int = 5,
    max_entries: int = 5000,
    ignores: Optional[set[str]] = None,
) -> Dict[str, Any]:
    """
    Returns a tree:
      {
        "type": "dir",
        "name": "<workspace>",
        "path": "",
        "children": [...]
      }
    Each child:
      { "type": "dir"|"file", "name": "...", "path": "relative/path", "children": [...]? }
    """
    ignores = ignores or set(DEFAULT_IGNORES)

    root = ws.root_abs
    entries_seen = 0

    def walk_dir(dir_abs: Path, dir_rel: str, depth: int) -> Dict[str, Any]:
        nonlocal entries_seen
        node: Dict[str, Any] = {
            "type": "dir",
            "name": dir_abs.name if dir_rel != "" else "<workspace>",
            "path": dir_rel,  # "" for root
            "children": [],
        }

        if depth >= max_depth:
            return node

        try:
            with os.scandir(dir_abs) as it:
                items = []
                for entry in it:
                    if _should_ignore(entry.name, ignores):
                        continue
                    items.append(entry)
        except PermissionError:
            node["children"] = [{
                "type": "error",
                "name": "PermissionError",
                "path": dir_rel,
                "message": "Permission denied",
            }]
            return node

        # Sort: directories first, then files, alphabetical
        items.sort(key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))

        for entry in items:
            if entries_seen >= max_entries:
                node["children"].append({
                    "type": "error",
                    "name": "LimitReached",
                    "path": dir_rel,
                    "message": f"Tree truncated at max_entries={max_entries}",
                })
                break

            entries_seen += 1

            child_rel = f"{dir_rel}/{entry.name}".lstrip("/")
            child_rel = child_rel.replace("\\", "/")

            # Important: do not follow symlinks when deciding type; but resolve later on file read.
            try:
                if entry.is_dir(follow_symlinks=False):
                    child_abs = Path(entry.path)
                    node["children"].append(walk_dir(child_abs, child_rel, depth + 1))
                elif entry.is_file(follow_symlinks=False):
                    node["children"].append({
                        "type": "file",
                        "name": entry.name,
                        "path": child_rel,
                    })
                else:
                    # Skip special files (sockets, devices, etc.)
                    continue
            except OSError:
                continue

        return node

    return walk_dir(root, "", 0)


def read_text_file(
    ws: ResolvedWorkspace,
    rel_path: str,
    max_bytes: int = 512_000,
) -> Dict[str, Any]:
    """
    Read a file as UTF-8 (with replacement). Returns:
      { path, size, text, truncated }
    """
    abs_path, rel_norm = resolve_under_root(ws, rel_path)
    if not abs_path.exists():
        raise FileNotFoundError(f"File does not exist: {rel_norm}")
    if not abs_path.is_file():
        raise IsADirectoryError(f"Path is not a file: {rel_norm}")

    size = abs_path.stat().st_size
    truncated = False

    with open(abs_path, "rb") as f:
        data = f.read(max_bytes + 1)

    if len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True

    text = data.decode("utf-8", errors="replace")

    return {
        "path": rel_norm,
        "abs_path": str(abs_path),
        "size": size,
        "truncated": truncated,
        "text": text,
    }
