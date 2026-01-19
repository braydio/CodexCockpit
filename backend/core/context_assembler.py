
# === ATTNT: This file is an example file scaffolded with ChatGPT
# === UPON the context_adapters.py being completed this should be removed asap.

"""
context_assembler.py
--------------------------------
Builds local repository context for Codex model prompts.
Scans files, extracts relevant snippets, and prepares structured context for model input.
"""

import os
import json
from typing import List, Dict


class ContextAssembler:
    def __init__(self, repo_root: str = "."):
        self.repo_root = os.path.abspath(repo_root)
        self.cache_dir = os.path.join(self.repo_root, ".cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def list_source_files(self, include_ext=None) -> List[str]:
        """Return all relevant source files (Python, JS, TS, etc.)."""
        if include_ext is None:
            include_ext = {".py", ".js", ".jsx", ".ts", ".tsx"}
        source_files = []
        for root, _, files in os.walk(self.repo_root):
            if any(x in root for x in [".git", "node_modules", ".cache", "__pycache__"]):
                continue
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in include_ext:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, self.repo_root)
                    source_files.append(rel_path)
        return source_files

    def extract_file_snippets(self, keywords: List[str], max_chars: int = 2000) -> List[Dict[str, str]]:
        """Extract relevant snippets from files containing given keywords."""
        snippets = []
        for path in self.list_source_files():
            try:
                with open(os.path.join(self.repo_root, path), "r", encoding="utf-8") as f:
                    content = f.read()
                if any(k.lower() in content.lower() for k in keywords):
                    snippet = content[:max_chars]
                    snippets.append({"file": path, "content": snippet})
            except Exception:
                continue
        return snippets

    def assemble_context(self, task_description: str) -> Dict:
        """Assemble structured repository context for a given task."""
        keywords = [w for w in task_description.split() if len(w) > 3]
        source_files = self.list_source_files()
        relevant_files = self.extract_file_snippets(keywords)
        return {
            "repo_root": self.repo_root,
            "repo_files": source_files[:75],  # limit for prompt size
            "relevant_files": relevant_files,
        }

    def dump_context(self, context: Dict, name: str = "context_snapshot.json"):
        """Save the generated context snapshot for debugging or caching."""
        path = os.path.join(self.cache_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(context, f, indent=2)
        return path
