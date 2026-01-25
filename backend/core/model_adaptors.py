
# === ATTNT: This file is an example file scaffolded with ChatGPT
# === UPON the model_adapters.py being completed this should be removed asap.


"""
model_adapters.py
--------------------------------
Unified interface for all CodexCockpit model backends.
Implements OpenAI, Ollama, LM Studio, and Offline cache adapters.
"""

import subprocess
import requests
import os
import hashlib


class ModelAdapter:
    """Abstract interface for all model adapters."""

    def generate(self, prompt: str) -> str:
        raise NotImplementedError("generate() must be implemented by subclass")


# --------------------------
# OpenAI API Adapter
# --------------------------

class OpenAIAdapter(ModelAdapter):
    def __init__(self, model: str = "gpt-4-turbo", temperature: float = 0.3):
        import openai
        self.client = openai
        self.model = model
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        resp = self.client.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are CodexCockpit, an autonomous software development agent."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature
        )
        return resp["choices"][0]["message"]["content"]


# --------------------------
# Ollama Adapter (Qwen, LLaMA, Mistral)
# --------------------------

class OllamaAdapter(ModelAdapter):
    def __init__(self, model_name: str = "qwen"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        cmd = ["ollama", "run", self.model_name]
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            output, _ = process.communicate(prompt)
            return output.strip()
        except FileNotFoundError:
            raise RuntimeError("Ollama not found. Ensure it's installed and available in PATH.")


# --------------------------
# LM Studio Adapter
# --------------------------

class LMStudioAdapter(ModelAdapter):
    def __init__(self, endpoint: str = "http://localhost:1234/v1/chat/completions"):
        self.endpoint = endpoint

    def generate(self, prompt: str) -> str:
        data = {
            "model": "mixtral",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        resp = requests.post(self.endpoint, json=data, timeout=90)
        return resp.json()["choices"][0]["message"]["content"]


# --------------------------
# Offline Cache Adapter
# --------------------------

class OfflineAdapter(ModelAdapter):
    def __init__(self, cache_path: str = "./backend/cache/responses/"):
        self.cache_path = cache_path
        os.makedirs(self.cache_path, exist_ok=True)

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def generate(self, prompt: str) -> str:
        key = self._hash(prompt)
        path = os.path.join(self.cache_path, f"{key}.txt")

        if os.path.exists(path):
            return open(path, "r", encoding="utf-8").read()

        # No cache hit — return placeholder and save for review
        placeholder = "[OfflineAdapter] No cached response found."
        with open(path, "w", encoding="utf-8") as f:
            f.write(placeholder)
        return placeholder
