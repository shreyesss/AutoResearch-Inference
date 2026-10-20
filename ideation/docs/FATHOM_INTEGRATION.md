# OpenAlex and Fathom integration

Deployment: `sofia-gpu-mumbai:/home/ubuntu/shreyas/skunk-work/ideation`.

## Actual reused code

[Fathom-DeepResearch](https://github.com/FractalAIResearchLabs/Fathom-DeepResearch) is a real sparse Git clone at `vendor/Fathom-DeepResearch`, pinned to `7e1f36414cda74748c886aed2998cee324a5e831` (MIT). Its serving code is also copied to the VM. No model weights are downloaded.

The small adapter `ideation/fathom.py` calls `scripts/fathom_worker.py` in `.venv-fathom`. The worker imports upstream functions:

| Tool | Upstream function | Current availability |
|---|---|---|
| `research.web_read`, mode `html` | `fetchers.basic_fetcher.fetch_html` | No API key needed |
| `research.web_read`, mode `browser` | `fetchers.crawl4ai_fetcher.fetch_crawl4ai` | Chromium and Linux libraries installed |
| `research.web_read`, mode `auto` | `fetchers_async.fetch_url` | Upstream domain routing and fallback; skips Jina/Reddit when credentials are absent |
| `research.web_search` | `search_api.search_urls` | Supplied Serper key configured; live search and cached repeats verified |
| `research.web_query` | Cached upstream fetch + local cheap-model helper | gpt-5.6-luna through existing Codex login; discovery context only |

The bundled `/execute` HTTP service evaluates caller-provided Python. This integration uses fixed local subprocess calls instead. Browser resources are closed at the end of each read. The upstream files remain unchanged; dependency isolation, credential configuration, dispatch, persistence and evidence checks are local adapters. Embedded third-party Reddit credentials in the public checkout are overridden with empty values unless user credentials are explicitly supplied.

Extracted content is stored in `data/corpus.sqlite`; exact worker requests/results, fetch time and revision are saved under `data/raw/fathom/`. Upstream caches live under `data/fathom-cache/`. Search snippets and generated page answers are `discovery` records: both evidence extraction and hypothesis gates reject them as primary evidence. Read the underlying pages first.

Extraction can truncate content and omit code, figures and tables. Upstream HTML fallback may return a Wayback page; `archive_fallback` marks this and the fetch date does not establish publication freshness. The worker timeout bounds a request; there is no long-running orchestration service. Public-URL syntax checks are not a hardened network sandbox.

## OpenAlex

The user-supplied `OPENALEX_API_KEY` is loaded from local `.env`. Only that key was transferred to `~/.config/ideation/providers.env` on the VM with mode 0600. Supported provider settings load without logging values, overwriting existing environment values or exporting unrelated `.env` secrets.

Live verification: a PagedAttention paper search returned three works; backward/forward traversal returned four linked works and stored citation edges. [Exact result IDs and timestamp](openalex-live-check.json). OpenAlex provides bibliographic records and available abstracts; it does not imply that full paper text has been read.

## Live verification — October 20, 2026

At 03:55 IST, SGLang documentation retrieval passed in all three modes: HTML returned 1,246 characters; browser and automatic routing each returned 5,337. Records and raw hashes are in [fathom-live-check.json](fathom-live-check.json). That historical check predates Serper configuration. The later [cache live check](cache-live-check.json) verifies Serper, OpenAlex, Fathom/arXiv reads and the cheap helper, followed by cached repeats. See [current architecture](SYSTEM_ARCHITECTURE.md) for budgets and TTLs.

## Reproduce

On the VM, from the deployment directory:

```bash
.venv-research/bin/python -m ideation tool research.fathom_status
.venv-research/bin/python -m ideation tool research.web_read \
  --args '{"url":"https://docs.sglang.ai/","mode":"auto"}'
.venv-research/bin/python -m ideation tool research.search \
  --args '{"query":"asynchronous speculative decoding","provider":"openalex","limit":3}'
.venv-research/bin/python -m scripts.verify_fathom
```

Fresh installation:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/FractalAIResearchLabs/Fathom-DeepResearch.git vendor/Fathom-DeepResearch
git -C vendor/Fathom-DeepResearch fetch --depth 1 origin 7e1f36414cda74748c886aed2998cee324a5e831
git -C vendor/Fathom-DeepResearch checkout --detach 7e1f36414cda74748c886aed2998cee324a5e831
git -C vendor/Fathom-DeepResearch sparse-checkout set serving
python3 -m venv .venv-fathom
.venv-fathom/bin/pip install -r requirements-fathom.txt
.venv-fathom/bin/python -m playwright install chromium
sudo .venv-fathom/bin/python -m playwright install-deps chromium
```

Resolved packages: [Fathom environment](fathom-environment.txt). Google search and the cheap helper now have live verification. Jina, Reddit, YouTube, specialized Fathom PDF routing and the direct OpenAI API helper remain unverified. Existing arXiv PDF extraction is verified separately. The upstream expensive `query_url` synthesis path has been replaced in the public tool with cached fetching plus the inexpensive helper.
