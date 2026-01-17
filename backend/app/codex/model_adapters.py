import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ModelAdapter(ABC):
    """Interface for invoking local model backends."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate model output from the provided prompt.

        Args:
            prompt: Prompt text to send to the model.

        Returns:
            The model's stdout output.
        """
        raise NotImplementedError


class OllamaAdapter(ModelAdapter):
    """Adapter for running a local Ollama model via an explicit executable."""

    def __init__(self, executable_path: str, model_name: str, timeout_s: int = 120):
        """Initialize the adapter with an explicit binary path and model name.

        Args:
            executable_path: Absolute path to the Ollama executable.
            model_name: Name of the Ollama model to run.
            timeout_s: Timeout in seconds for the invocation.
        """
        self.executable_path = Path(executable_path)
        if not self.executable_path.is_file():
            raise ValueError(
                f"Ollama executable not found at {self.executable_path}."
            )
        self.model_name = model_name
        self.timeout_s = timeout_s

    def generate(self, prompt: str) -> str:
        """Invoke the Ollama CLI with the prompt and return stdout.

        Args:
            prompt: Prompt text to send to the model.

        Returns:
            The model's stdout output.
        """
        LOGGER.info(
            "Running Ollama model '%s' with executable %s",
            self.model_name,
            self.executable_path,
        )
        try:
            result = subprocess.run(
                [str(self.executable_path), "run", self.model_name],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.timeout_s,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Ollama executable could not be launched."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Ollama invocation exceeded {self.timeout_s} seconds."
            ) from exc

        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            details = stderr or stdout or "Unknown error"
            raise RuntimeError(
                f"Ollama exited with code {result.returncode}: {details}"
            )

        return result.stdout
