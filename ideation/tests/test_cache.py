from concurrent.futures import ThreadPoolExecutor
import tempfile
import time
import unittest
from unittest.mock import patch

from ideation.cache import Cache
from ideation.fathom import FathomTools
from ideation.sources import Sources
from ideation.store import Store


class CacheTests(unittest.TestCase):
    def test_identical_concurrent_misses_fetch_once(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Cache(folder)
            calls = []
            def fetch():
                calls.append(1)
                time.sleep(.03)
                return {"text": "source"}
            with ThreadPoolExecutor(4) as pool:
                values = list(pool.map(lambda _: cache.call("test", {"q": "x"}, fetch, 60), range(4)))
            self.assertEqual(len(calls), 1)
            self.assertEqual(sum(v[1]["hit"] for v in values), 3)
            self.assertEqual(len({v[1]["fetched_at"] for v in values}), 1)

    def test_expiry_refresh_and_failure_do_not_reuse_bad_results(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Cache(folder)
            first, _ = cache.call("test", "x", lambda: 1, -1)
            second, meta = cache.call("test", "x", lambda: 2, 60)
            third, _ = cache.call("test", "x", lambda: 3, 60, refresh=True)
            self.assertEqual((first, second, third, meta["hit"]), (1, 2, 3, False))
            def fail():
                raise RuntimeError("unavailable")
            with self.assertRaises(RuntimeError):
                cache.call("test", "error", fail, 60)
            self.assertFalse(cache.call("test", "error", lambda: "ok", 60)[1]["hit"])

    def test_budget_is_atomic_and_persists_failures(self):
        with tempfile.TemporaryDirectory() as folder, patch("ideation.cache.policy", return_value={"budgets": {"serper": {"total": 2, "rolling_24h": 2}}}):
            cache = Cache(folder)
            def attempt(_):
                try:
                    cache.reserve("serper")
                    return 1
                except RuntimeError:
                    return 0
            with ThreadPoolExecutor(5) as pool:
                self.assertEqual(sum(pool.map(attempt, range(5))), 2)
            self.assertEqual(Cache(folder).status()["budgets"]["serper"]["attempts"], 2)

    def test_source_bytes_cached_across_instances(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder + "/corpus.sqlite")
            with patch.object(Sources, "_request", return_value=(b"paper bytes", "text/plain")) as network:
                self.assertEqual(Sources(store).request("https://example.org/paper"), (b"paper bytes", "text/plain"))
                source = Sources(store)
                source.request("https://example.org/paper")
                self.assertTrue(source.last_cache["hit"])
                self.assertEqual(network.call_count, 1)
            store.db.close()

    def test_serper_same_query_different_limit_no_second_fetch(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", {"SERPER_API_KEY": "test"}):
            store = Store(folder + "/corpus.sqlite")
            with patch.object(FathomTools, "_uncached", return_value={"id": "search", "characters": 10}) as network:
                tool = FathomTools(store)
                a = tool.search("low  batch MoE", 3)
                b = tool.search("low batch MoE", 5)
                self.assertFalse(a["cache"]["hit"])
                self.assertTrue(b["cache"]["hit"])
                self.assertEqual(network.call_count, 1)
                self.assertEqual(b["requested_limit"], 5)
            store.db.close()
