import logging
import os
import re
from typing import Iterable

LOGGER = logging.getLogger(__name__)


class ContextAssembler:
    """Collects repository context to enrich Codex prompts.

    Args:
        workspace_root: Absolute or relative path to the workspace root.
        allow_extensions: Iterable of file extensions to include when scanning.
        deny_dirs: Iterable of directory names to skip while walking the tree.
        max_files: Maximum number of files to include in the summary list.
        max_file_bytes: Maximum number of bytes to read per file when scanning
            for snippet matches.
        max_snippet_chars: Maximum number of characters to include per snippet line.
        max_snippets: Maximum number of snippet entries to return across files.
    """

    def __init__(
        self,
        workspace_root: str,
        allow_extensions: Iterable[str] | None = None,
        deny_dirs: Iterable[str] | None = None,
        max_files: int = 250,
        max_file_bytes: int = 32_000,
        max_snippet_chars: int = 240,
        max_snippets: int = 25,
        max_lines_per_file: int = 4,
    ) -> None:
        self.workspace_root = os.path.abspath(workspace_root)
        self.allow_extensions = {
            ext.lower()
            for ext in (allow_extensions or {".py", ".js", ".ts", ".tsx", ".vue"})
        }
        self.deny_dirs = set(
            deny_dirs
            or {
                ".venv",
                "node_modules",
                "dist",
                "build",
                ".git",
            }
        )
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes
        self.max_snippet_chars = max_snippet_chars
        self.max_snippets = max_snippets
        self.max_lines_per_file = max_lines_per_file

    def assemble(self, goal: str) -> dict:
        """Assemble repository summary and keyword snippets for a prompt.

        Args:
            goal: User goal used to derive keyword hints for snippet matching.

        Returns:
            Dictionary with ``summary`` (list of relative file paths), ``snippets``
            (list of snippet dicts), ``errors`` (list of controlled errors), and
            ``keywords`` (list of derived keywords).
        """
        errors: list[str] = []
        summary = self._list_source_files(errors)
        keywords = self._extract_keywords(goal)
        snippets = self._collect_snippets(summary, keywords, errors)
        return {
            "summary": summary,
            "snippets": snippets,
            "errors": errors,
            "keywords": keywords,
        }

    def _list_source_files(self, errors: list[str]) -> list[str]:
        """Enumerate source files under the workspace root.

        Args:
            errors: Mutable list to append non-fatal errors.

        Returns:
            List of relative paths limited by ``max_files``.
        """
        results: list[str] = []
        try:
            for root, dirnames, filenames in os.walk(self.workspace_root):
                # Filter out heavy or irrelevant directories in-place to avoid
                # descending into them during traversal.
                dirnames[:] = [
                    name for name in dirnames if name not in self.deny_dirs
                ]
                for filename in filenames:
                    if len(results) >= self.max_files:
                        return results
                    _, ext = os.path.splitext(filename)
                    if ext.lower() not in self.allow_extensions:
                        continue
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, self.workspace_root)
                    results.append(relative_path)
        except OSError as exc:
            message = f"Failed to walk workspace {self.workspace_root}: {exc}"
            LOGGER.warning(message)
            errors.append(message)
        return results

    def _extract_keywords(self, goal: str) -> list[str]:
        """Extract simple keyword hints from the user goal.

        Args:
            goal: Raw user goal string.

        Returns:
            List of lowercase keyword tokens with stop words removed.
        """
        tokens = re.findall(r"[A-Za-z0-9_]{3,}", goal.lower())
        stop_words = {
            "the",
            "and",
            "with",
            "from",
            "that",
            "this",
            "into",
            "when",
            "where",
            "make",
            "change",
            "update",
        }
        seen = set()
        keywords: list[str] = []
        for token in tokens:
            if token in stop_words or token in seen:
                continue
            seen.add(token)
            keywords.append(token)
        return keywords[:20]

    def _collect_snippets(
        self,
        files: list[str],
        keywords: list[str],
        errors: list[str],
    ) -> list[dict]:
        """Collect keyword-matched snippet lines from files.

        Args:
            files: List of relative file paths to scan.
            keywords: Keyword tokens to match against file contents.
            errors: Mutable list to append non-fatal errors.

        Returns:
            List of snippet dictionaries with path and matched lines.
        """
        if not keywords:
            return []

        snippets: list[dict] = []
        for relative_path in files:
            if len(snippets) >= self.max_snippets:
                break
            full_path = os.path.join(self.workspace_root, relative_path)
            try:
                size = os.path.getsize(full_path)
            except OSError as exc:
                message = f"Failed to stat {relative_path}: {exc}"
                LOGGER.warning(message)
                errors.append(message)
                continue

            # Respect per-file size limits to keep prompt content bounded.
            if size > self.max_file_bytes:
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as handle:
                    content = handle.read(self.max_file_bytes)
            except OSError as exc:
                message = f"Failed to read {relative_path}: {exc}"
                LOGGER.warning(message)
                errors.append(message)
                continue

            matches: list[str] = []
            for line_number, line in enumerate(content.splitlines(), start=1):
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in keywords):
                    trimmed = line[: self.max_snippet_chars].rstrip()
                    matches.append(f"L{line_number}: {trimmed}")
                if len(matches) >= self.max_lines_per_file:
                    break

            if matches:
                snippets.append({
                    "path": relative_path,
                    "lines": matches,
                })

        return snippets
