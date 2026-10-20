import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ideation.evidence import ResearchTools
from ideation.providers import load_provider_env
from ideation.store import Store


class ProviderTests(unittest.TestCase):
    def test_loader_limits_keys_preserves_environment_and_literal_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text('OPENALEX_API_KEY=file-value\nSERPER_API_KEY="literal-${SECRET}"\nUNRELATED_PASSWORD=private\n')
            with patch.dict(os.environ, {"IDEATION_ENV_FILE": str(path), "OPENALEX_API_KEY": "existing", "SECRET": "expanded"}, clear=True):
                load_provider_env()
                self.assertEqual(os.environ["OPENALEX_API_KEY"], "existing")
                self.assertEqual(os.environ["SERPER_API_KEY"], "literal-${SECRET}")
                self.assertNotIn("UNRELATED_PASSWORD", os.environ)

    def test_discovery_cannot_enter_evidence_extractor(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / "test.sqlite")
            store.put(dict(id="fathom:search:1", kind="discovery", source="fathom", title="Search", body="Generated summary", url="https://example.org"))
            with patch("ideation.evidence.run_agent") as agent:
                with self.assertRaisesRegex(ValueError, "discovery context"):
                    ResearchTools(store).evidence("question", ["fathom:search:1"], str(Path(folder) / "output"))
                agent.assert_not_called()
            store.db.close()
