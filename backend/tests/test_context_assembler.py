import os
import tempfile
import unittest

from app.codex.context_assembler import ContextAssembler


class ContextAssemblerTests(unittest.TestCase):
    """Unit tests for context assembly behavior."""

    def setUp(self) -> None:
        """Create a temporary workspace for context assembly tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        workspace = self.temp_dir.name

        os.makedirs(os.path.join(workspace, "src"), exist_ok=True)
        os.makedirs(os.path.join(workspace, "node_modules"), exist_ok=True)
        os.makedirs(os.path.join(workspace, "dist"), exist_ok=True)

        self._write_file("main.py", "def foo():\n    return 'bar'\n")
        self._write_file("README.md", "ignored")
        self._write_file(os.path.join("src", "component.tsx"), "const Foo = () => null;")
        self._write_file(os.path.join("node_modules", "skip.js"), "console.log('skip');")
        self._write_file(os.path.join("dist", "bundle.js"), "console.log('dist');")
        self._write_file("large.py", "x" * 200)

    def tearDown(self) -> None:
        """Clean up temporary workspace."""
        self.temp_dir.cleanup()

    def _write_file(self, relative_path: str, content: str) -> None:
        """Write content into a file inside the temporary workspace.

        Args:
            relative_path: Path relative to the temporary workspace.
            content: File contents to write.
        """
        full_path = os.path.join(self.temp_dir.name, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def test_summary_and_snippets_are_bounded(self) -> None:
        """Ensure summaries and snippets respect filters and size limits."""
        assembler = ContextAssembler(
            self.temp_dir.name,
            max_file_bytes=50,
            max_snippets=10,
            max_files=10,
        )
        context = assembler.assemble("Add foo handler")

        self.assertIn("main.py", context["summary"])
        self.assertIn(os.path.join("src", "component.tsx"), context["summary"])
        self.assertNotIn("README.md", context["summary"])
        self.assertNotIn(os.path.join("node_modules", "skip.js"), context["summary"])
        self.assertNotIn(os.path.join("dist", "bundle.js"), context["summary"])

        snippet_paths = {snippet["path"] for snippet in context["snippets"]}
        self.assertIn("main.py", snippet_paths)
        self.assertNotIn("large.py", snippet_paths)
        self.assertEqual(context["errors"], [])


if __name__ == "__main__":
    unittest.main()
