
"""
codex_runner.py
--------------------------------
Handles prompt composition, model invocation, and iteration control.
Integrates ContextAssembler and ModelAdapters into a single execution pipeline.
"""

import json
from typing import Dict, Optional
from backend.core.context_assembler import ContextAssembler
from backend.utils.model_adapters import (
    OpenAIAdapter,
    OllamaAdapter,
    LMStudioAdapter,
    OfflineAdapter
)


class CodexRunner:
    def __init__(self, model_name: str = "ollama:qwen", repo_root: str = "."):
        self.model_name = model_name
        self.repo_root = repo_root
        self.context_assembler = ContextAssembler(repo_root=self.repo_root)
        self.model = self._load_model(model_name)

    def _load_model(self, model_name: str):
        """Instantiate the appropriate model adapter based on prefix."""
        if model_name.startswith("openai:"):
            return OpenAIAdapter(model="gpt-4-turbo")
        elif model_name.startswith("ollama:"):
            _, name = model_name.split(":")
            return OllamaAdapter(model_name=name)
        elif model_name.startswith("lmstudio:"):
            return LMStudioAdapter()
        elif model_name.startswith("offline:"):
            return OfflineAdapter()
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def compose_prompt(self, user_prompt: str, context: Dict) -> str:
        """Assemble structured Codex prompt with file context."""
        repo_overview = "\n".join(f"- {p}" for p in context["repo_files"])
        relevant = "\n\n".join(
            f"### {f['file']}\n{f['content']}" for f in context["relevant_files"]
        )
        composed = (
            f"You are CodexCockpit, an autonomous code development framework.\n"
            f"Repository structure:\n{repo_overview}\n\n"
            f"Relevant files:\n{relevant}\n\n"
            f"Task:\n{user_prompt}\n\n"
            f"Respond with proposed file-level edits or diffs."
        )
        return composed

    def run_step(self, user_prompt: str, dump_context: bool = True) -> str:
        """Execute a full Codex step — assemble context, compose prompt, invoke model."""
        context = self.context_assembler.assemble_context(user_prompt)
        if dump_context:
            self.context_assembler.dump_context(context)
        composed = self.compose_prompt(user_prompt, context)
        result = self.model.generate(composed)
        self._log_output(user_prompt, composed, result)
        return result

    def _log_output(self, prompt: str, composed: str, result: str):
        """Persist the full interaction for debugging."""
        record = {
            "prompt": prompt,
            "composed_prompt": composed[:1000],  # truncate for log
            "result": result[:2000],
        }
        with open("backend/logs/last_codex_run.json", "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        print("[CodexRunner] Logged run to backend/logs/last_codex_run.json")
