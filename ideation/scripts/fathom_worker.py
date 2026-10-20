"""Call actual upstream Fathom functions in their isolated dependency environment."""
import asyncio
import contextlib
import json
import os
from pathlib import Path
import sys

request = json.load(sys.stdin)
project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project))
checkout = project / "vendor/Fathom-DeepResearch/serving/web_agents"
sys.path.insert(0, str(checkout))


async def fetch_with_browser_cleanup(function, url):
    try:
        return await function(url)
    finally:
        from fetchers import crawl4ai_fetcher
        crawler = crawl4ai_fetcher._CRAWLER
        if crawler is not None:
            await crawler.__aexit__(None, None, None)


try:
    # Upstream modules print crawler diagnostics; keep the JSON channel clean.
    with contextlib.redirect_stdout(sys.stderr):
        from config import CFG, _SESS
        from ideation.cache import Cache, policy
        # Do not use third-party credentials embedded in the public checkout.
        CFG.reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
        CFG.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        cache = Path(request["data_root"]) / "fathom-cache"
        cache.mkdir(parents=True, exist_ok=True)
        CFG.jina_cache_dir = str(cache)
        CFG.serper_cache_dir = str(cache)
        if request["operation"] == "read":
            import fetchers_async
            if not CFG.jina_key:
                fetchers_async.fetch_jina = lambda url: None
            if not CFG.reddit_client_id or not CFG.reddit_client_secret:
                fetchers_async.fetch_reddit = lambda url: None
            mode = request.get("mode", "auto")
            if mode == "html":
                from fetchers.basic_fetcher import fetch_html
                text = fetch_html(request["url"])
            elif mode == "browser":
                from fetchers.crawl4ai_fetcher import fetch_crawl4ai
                text = asyncio.run(fetch_with_browser_cleanup(fetch_crawl4ai, request["url"]))
            else:
                text = asyncio.run(fetch_with_browser_cleanup(fetchers_async.fetch_url, request["url"]))
        elif request["operation"] == "search":
            if not CFG.serper_key:
                raise RuntimeError("SERPER_API_KEY is required for Fathom web search")
            from search_api import search_urls
            from utils import _search_cache_paths
            CFG.retries = 1
            CFG.search_cache_ttl = policy()["ttl_seconds"]["serper"]
            if request.get("refresh"):
                Path(_search_cache_paths(request["query"], request["limit"])).unlink(missing_ok=True)
            original_post = _SESS.post
            def budgeted_post(url, *args, **kwargs):
                if url == CFG.serper_ep:
                    Cache(request["data_root"]).reserve("serper")
                return original_post(url, *args, **kwargs)
            _SESS.post = budgeted_post
            text = search_urls(request["query"], top_k=request["limit"])
        elif request["operation"] == "query":
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("OPENAI_API_KEY is required for this Fathom query-LLM configuration; use research.evidence with the existing agent instead")
            from search_api import query_url
            text = query_url(request["url"], request["question"])
        else:
            raise ValueError("Unknown Fathom operation")
        if not text or str(text).lower().startswith(("[error", "[failed", "[unable", "[binary")):
            raise RuntimeError("Fathom returned no usable source text")
    print(json.dumps({"text": text, "operation": request["operation"]}))
except Exception as error:
    message = str(error)
    for key in ("OPENAI_API_KEY", "JINA_API_KEY", "SERPER_API_KEY"):
        if os.getenv(key):
            message = message.replace(os.environ[key], "[redacted]")
    print(json.dumps({"error": message, "type": type(error).__name__}))
    sys.exit(1)
