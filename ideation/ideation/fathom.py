"""Adapter to a pinned Fathom checkout; fixed functions, no remote exec endpoint."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlparse

from .providers import load_provider_env
from .store import now
from .cache import Cache, policy

REVISION = "7e1f36414cda74748c886aed2998cee324a5e831"


def public_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Expected an HTTP(S) source URL without credentials")
    if parsed.hostname.lower() == "localhost" or parsed.hostname.lower().endswith(".localhost"):
        raise ValueError("Use a public source URL")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return url
    if not address.is_global:
        raise ValueError("Use a public source URL")
    return url


class FathomTools:
    def __init__(self, store):
        load_provider_env()
        self.store = store
        self.project = Path(__file__).resolve().parents[1]
        self.python = self.project / ".venv-fathom/bin/python"
        self.cache = Cache(store.path.parent)

    def status(self):
        return {"checkout": str(self.project / "vendor/Fathom-DeepResearch"), "revision": REVISION,
                "runtime_installed": self.python.exists(), "web_read": "CPU fetchers; no LLM key needed",
                "web_search_key_present": bool(os.getenv("SERPER_API_KEY")),
                "jina_key_present": bool(os.getenv("JINA_API_KEY")),
                "query_llm_key_present": bool(os.getenv("OPENAI_API_KEY")),
                "query_helper_model": policy()["helper_model"],
                "query_helper_backend": "openai" if os.getenv("OPENAI_API_KEY") else "codex login",
                "execution": "fixed local functions in subprocess; upstream arbitrary-exec HTTP service is not used"}

    def _call(self, request, timeout=120, refresh=False):
        ttl = policy()["ttl_seconds"]["serper" if request["operation"] == "search" else "page"]
        value, cached = self.cache.call("fathom_" + request["operation"], {"revision": REVISION, **request},
                                        lambda: self._uncached(request, timeout, refresh), ttl, refresh)
        return {**value, "cache": cached}

    def _uncached(self, request, timeout, refresh):
        if not self.python.exists():
            raise RuntimeError("Install requirements-fathom.txt in .venv-fathom")
        process = subprocess.run([str(self.python), str(self.project / "scripts/fathom_worker.py")],
                                 input=json.dumps({**request, "refresh": refresh, "data_root": str(self.store.path.parent.resolve())}), text=True, capture_output=True, timeout=timeout,
                                 cwd=str(self.project))
        try:
            result = json.loads(process.stdout)
        except json.JSONDecodeError:
            raise RuntimeError("Fathom worker returned no JSON; verify its isolated dependencies and browser installation") from None
        if process.returncode or result.get("error"):
            raise RuntimeError("Fathom: " + result.get("error", "worker failed"))
        raw = json.dumps({"request": request, "result": result, "fetched_at": now(), "upstream_revision": REVISION}, ensure_ascii=False).encode()
        digest = hashlib.sha256(raw).hexdigest()
        folder = self.store.path.parent / "raw/fathom"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (digest + ".json")).write_bytes(raw)
        operation = request["operation"]
        discovery = operation != "read"
        identity = json.dumps(request, sort_keys=True)
        id = "fathom:" + operation + ":" + hashlib.sha256(identity.encode()).hexdigest()[:16]
        self.store.put(dict(id=id, source="fathom", kind="discovery" if discovery else "resource",
                            title=request.get("url") or request.get("query"), body=result["text"],
                            url=request.get("url") or "https://google.serper.dev/search",
                            metadata={"upstream_revision": REVISION, "raw_sha256": digest,
                                      "read_depth": "discovery_only" if discovery else "extracted_web_text",
                                      "may_be_truncated": True, "archive_fallback": "archive.org" in result["text"][:300],
                                      "provenance_note": "Provider extraction; inspect original for code, figures and precise experimental claims"}))
        self.store.db.commit()
        return {"id": id, "characters": len(result["text"]), "kind": "discovery" if discovery else "resource", "raw_sha256": digest}

    def read(self, url, mode="auto", timeout=120, refresh=False):
        """Fathom general-web extraction: auto fallback, direct HTML, or browser."""
        if mode not in ("auto", "html", "browser"):
            raise ValueError("mode must be auto, html, or browser")
        return self._call({"operation": "read", "url": public_url(url), "mode": mode}, min(300, max(10, timeout)), refresh)

    def search(self, query, limit=5, refresh=False):
        """Fathom's cached Serper web search. Requires SERPER_API_KEY."""
        if not os.getenv("SERPER_API_KEY"):
            raise RuntimeError("Set SERPER_API_KEY in .env to enable Fathom web search; research.search already supports OpenAlex/arXiv/HF")
        # Serper returns ten organic hits per call. Cache one set for all smaller display limits.
        result = self._call({"operation": "search", "query": " ".join(query.split()), "limit": 10}, refresh=refresh)
        return {**result, "requested_limit": min(10, max(1, int(limit))), "stored_limit": 10}

    def query(self, url, question, refresh=False):
        """Cached Fathom read plus cheap helper synthesis; output is discovery context."""
        from .helper import Helper
        source = self.read(url, refresh=refresh)
        return Helper(self.store).triage(question, [source["id"]], refresh=refresh)
