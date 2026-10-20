import tempfile
import unittest
from unittest.mock import patch
from ideation.helper import Helper
from ideation.store import Store


class HelperTests(unittest.TestCase):
    def test_invented_url_is_rejected_without_caching(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder + "/db.sqlite")
            store.put(dict(id="source", source="test", kind="resource", title="text", body="Known source", url="https://example.org/known"))
            with patch("ideation.helper.run_agent", return_value={"summary": "text", "selected_urls": ["https://invented.invalid/"], "gaps": []}):
                with self.assertRaisesRegex(ValueError, "invented a URL"):
                    Helper(store).triage("question", ["source"], backend="codex")
            self.assertEqual(store.db.execute("SELECT count(*) FROM documents WHERE kind='discovery'").fetchone()[0], 0)
            store.db.close()

    def test_full_source_change_invalidates_cached_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder + "/db.sqlite")
            doc = dict(id="source", source="test", kind="resource", title="text", body="x" * 20000, url="https://example.org/known")
            store.put(doc)
            with patch("ideation.helper.run_agent", return_value={"summary": "text", "selected_urls": [], "gaps": []}) as model:
                helper = Helper(store)
                helper.triage("question", ["source"], backend="codex")
                self.assertTrue(helper.triage("question", ["source"], backend="codex")["cache"]["hit"])
                doc["body"] += "changed beyond model excerpt"
                store.put(doc)
                self.assertFalse(helper.triage("question", ["source"], backend="codex")["cache"]["hit"])
                self.assertEqual(model.call_count, 2)
            store.db.close()
