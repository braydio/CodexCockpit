import asyncio
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.codex.local_driver import LocalModelDriver
from app.codex.model_adapters import ModelAdapter, OllamaAdapter
from app.codex.models import ModelSpec


class FakeAdapter(ModelAdapter):
    """Adapter that records prompts and returns static output."""

    def __init__(self, output: str = "hello"):
        self.output = output
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.output


class TestOllamaAdapter(unittest.TestCase):
    def test_generate_returns_stdout(self):
        with tempfile.NamedTemporaryFile() as executable:
            adapter = OllamaAdapter(executable.name, "qwen")
            completed = subprocess.CompletedProcess(
                args=[executable.name, "run", "qwen"],
                returncode=0,
                stdout="ok",
                stderr="",
            )
            with patch("subprocess.run", return_value=completed) as run_mock:
                result = adapter.generate("hello")

            self.assertEqual(result, "ok")
            run_mock.assert_called_once()

    def test_generate_raises_on_failure(self):
        with tempfile.NamedTemporaryFile() as executable:
            adapter = OllamaAdapter(executable.name, "qwen", timeout_s=1)
            completed = subprocess.CompletedProcess(
                args=[executable.name, "run", "qwen"],
                returncode=1,
                stdout="",
                stderr="boom",
            )
            with patch("subprocess.run", return_value=completed):
                with self.assertRaises(RuntimeError):
                    adapter.generate("hello")


class TestLocalModelDriver(unittest.IsolatedAsyncioTestCase):
    async def test_start_session_uses_adapter(self):
        adapter = FakeAdapter(output="adapter output")
        spec = ModelSpec(
            name="local-test",
            runtime="local",
            endpoint=None,
            adapter="ollama",
            executable_path="/bin/ollama",
            timeout_s=10,
            context=2048,
            tools=False,
        )

        with tempfile.TemporaryDirectory() as workspace:
            sample_path = Path(workspace) / "sample.py"
            sample_path.write_text("print('hello')", encoding="utf-8")

            driver = LocalModelDriver(spec, adapter)
            await driver.start_session(
                "session-1",
                {"workspace": workspace, "goal": "test prompt"},
            )

            async def collect_events():
                events = []
                async for event in driver.stream_events("session-1"):
                    events.append(event)
                return events

            events = await asyncio.wait_for(collect_events(), timeout=2)

        self.assertTrue(adapter.prompts)
        self.assertEqual(events[0]["type"], "thought")
        self.assertIn("adapter output", events[0]["content"])
        self.assertEqual(events[-1]["type"], "final")


if __name__ == "__main__":
    unittest.main()
