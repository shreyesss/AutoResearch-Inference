# Open-source choices

**Updated selection:** see [Recent research and repository decisions](RECENT_RESEARCH.md) and [Three-tool interface](THREE_TOOLS.md) for the 20 October review. Those add actual DiscoveryRSI core reuse, PyAlex and optional PaperQA. The table below records the earlier prototype decisions.

Inspected 19 October 2026 UTC. Repository metadata and observed HEADs are captured in [oss-snapshot.json](oss-snapshot.json). This is a fit assessment, not a claim to have benchmarked every framework.

| Repository/component | Assessment | Decision |
|---|---|---|
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | Maintained, Apache-2.0; recursive research, source collection and library API. Requires model/search providers; its general report still needs domain-specific provenance and hypothesis checks. | Selected optional wider web-discovery backend; isolated install and adapter. Core corpus remains independently usable. |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | MIT; useful supervisor/research/compression design, but GitHub now marks the repository archived. | Architectural reference, not a new runtime dependency. |
| [Deep Agents](https://github.com/langchain-ai/deepagents) | Maintained MIT general agent harness with planning, files and delegation. | Useful if orchestration grows; unnecessary for the requested small explicit pipeline today. |
| [LightRAG](https://github.com/HKUDS/LightRAG) | Maintained MIT graph/vector retrieval system with extraction, citations and multiple storage options. | Evaluate after a lexical gold set exists. Avoid paying extraction cost across every issue before showing retrieval value. |
| [dzhng/deep-research](https://github.com/dzhng/deep-research) | MIT compact recursive research reference; another language/runtime and Firecrawl-centered setup. | Reference for bounded follow-up searches; not selected over the existing Python/runtime environment. |
| [Codex](https://github.com/openai/codex) | Existing authenticated runtime on workstation and VM; structured noninteractive output. | Working planner, synthesis, critique and revision runner. No new orchestration server. |
| [huggingface_hub](https://github.com/huggingface/huggingface_hub) | Official HF client documents current `list_papers` and `paper_info` endpoints. | Use those HTTP contracts directly in the dependency-free core; adopt SDK if wider Hub operations are added. |
| [SQLite FTS5](https://sqlite.org/fts5.html) | Embedded lexical retrieval with BM25 and transactional storage. | Selected corpus/search/explicit-edge store. Easy to inspect and move; sufficient for this prototype. |

The default core has no pip dependencies. The optional GPT Researcher install is pinned to 0.16.1 (Python 3.12+) in `requirements-web.txt`; its resolved environment is recorded on the VM. A successful import is not proof of a completed API-backed research run. The implemented live demonstration uses Codex, arXiv and HF.

Primary interface references:

- [GitHub repository issue API](https://docs.github.com/en/rest/issues/issues): issues include PRs; state/date/sort controls and pagination.
- [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html): query syntax, metadata, sorting and request spacing.
- [HF paper client source](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/hf_api.py): `list_papers`, `paper_info`, `read_paper`.
- [GPT Researcher library API](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package): conduct research, generate a report, collect sources.
- [Codex noninteractive execution](https://developers.openai.com/codex/noninteractive): JSON schema outputs and saved final messages.

The supplied [Autoloops site](https://autoloops.ai/) currently presents an inference service and DeepSeek V4.1 Flash offering. Its landing-page claims are useful market context, not reproducible kernel/serving benchmark evidence or an open-source research-agent implementation.
