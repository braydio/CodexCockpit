import unittest

from app.api.models import list_models
from app.codex.models import MODEL_REGISTRY


class TestApiModels(unittest.TestCase):
    """Tests for API model metadata alignment with the registry."""

    def test_models_align_with_registry(self):
        response = list_models()

        self.assertIn("models", response)
        for model in response["models"]:
            name = model["name"]
            self.assertIn(name, MODEL_REGISTRY)

            spec = MODEL_REGISTRY[name]
            self.assertEqual(model["context"], spec.context)
            self.assertEqual(model["tools"], spec.tools)
            self.assertEqual(model["type"], spec.runtime)


if __name__ == "__main__":
    unittest.main()
