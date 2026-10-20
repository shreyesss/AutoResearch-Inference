# Research and repository decisions

Reviewed 20 October 2026 against primary papers and repository source. Exact repository revisions are in `research-oss-snapshot.json`. The user-supplied brief is a set of leads, not verified dependency documentation.

| Source | What the source contributes | Decision here |
|---|---|---|
| [AI Scientist v3 / Agentic Scientist](https://arxiv.org/html/2610.18933v1), October 2026; [official repository](https://github.com/SakanaAI/AI-Scientist-v3) | Structured idea contracts, rubric checks, separate execution evidence, controlled comparisons and ablations. The official system is a substantial multi-phase pipeline. | Adopt the contract and evaluation separation. Do not deploy its Docker/workers/paper-writing pipeline for this task. |
| [DiscoveryRSI](https://arxiv.org/html/2610.23839v1), October 2026; [repository](https://github.com/Gen-Verse/DiscoveryRSI) | A hypothesis jointly specifies a claim, investigation, decision rules and alternatives. Revision lineage and research histories support later improvement. | Reuse the public record/replay/tool classes directly. Add domain gates; its public default loop always selects a maximum. No claim to reproduce model training or the paper's full system. |
| [AgentIdeaBench](https://arxiv.org/html/2609.07611v1), September 2026 | Active retrieval improves grounding-related qualities without establishing improved originality under its critics. Literature-informed originality review differs from self-rating. | Retrieve prior art after drafting, then critique. Keep one concise idea statement before the structured test. Retrieval count is not a novelty score. |
| [MechHypoBench](https://arxiv.org/html/2610.05197v1), October 2026 | Evaluates mechanisms through consequences under withheld conditions; reports a gap between generated hypotheses and underlying mechanisms. | Require a held-out workload and a test separating competing explanations. No claim that a filled schema replicates benchmark success. |
| [SciPIP](https://arxiv.org/abs/2410.23166); [code](https://github.com/cheerss/SciPIP) | Literature-based inspiration and related-paper retrieval. Current setup requires Neo4j, prepared corpus and embedding infrastructure. | Use mechanism-transfer search as a design reference. Installing this research environment would add substantial maintenance here. |
| [ResearchAgent](https://arxiv.org/abs/2404.07738); [code](https://github.com/JinheonBaek/ResearchAgent) | Seed-paper expansion and iterative review of problems/methods/experiments. Repository metadata has no declared licence. | Conceptual reference for critique and revision; no code copied. |
| [SciMON](https://arxiv.org/abs/2305.14259); [code](https://github.com/itea1001/SCIMON) | Retrieval and iteration aimed at novelty. | Reference for searching the closest prior mechanism before retaining a proposal. Not a runtime dependency. |
| [PaperQA](https://github.com/Future-House/paper-qa) | Established scientific-document evidence retrieval, contextualization and cited answers. `Docs` permits direct use without its agent loop. | Optional evidence adapter pinned to `paper-qa==2026.8.12`, rather than embedding its whole research agent. Requires separately configured providers. |
| [PyAlex](https://github.com/J535D165/pyalex) | OpenAlex search, structured bibliographic metadata and citation relationships. Current documentation requires an API key for normal use. | Installed `pyalex==0.21`; keyed search/citation adapter. Missing key is surfaced explicitly. |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | General multi-step research orchestration. GitHub marks the repository archived. | No new runtime dependency. Existing GPT Researcher adapter remains optional legacy functionality. |

## Important interpretation limits

DiscoveryRSI's reported correspondence with post-cutoff publications is a retrospective, retrieval- and judge-dependent measurement. It does not demonstrate that researchers adopted these proposals or that our inference-serving proposals will work. Its experiments are primarily outside this serving domain.

The official AI Scientist v3 was distinguished from unrelated forks also using “v3”. Source inspection—not the name—determined the choice. Its paper and code are references; we have not run its complete experiment pipeline.

PaperQA's current package version is date-based, while “PaperQA2” is commonly used for the research system. We pin the verified current package rather than assume version `2.x` is the right dependency.

DiscoveryRSI's GitHub API reports `NOASSERTION`, but the inspected LICENSE explicitly states Apache License 2.0. The dependency is pinned to the reviewed commit; no upstream source is copied into our modules.

## What is actually reused

- DiscoveryRSI: imported `ToolRegistry`, `Tool`, `Candidate`, `Episode`, `ReplayBuffer`.
- PyAlex: imported SDK for OpenAlex search and citation traversal; keyed search and both citation directions verified with the supplied key on October 20.
- Fathom-DeepResearch: actual sparse clone at `7e1f36414cda74748c886aed2998cee324a5e831`, imported CPU web fetchers, isolated dependencies. See [integration and verification](FATHOM_INTEGRATION.md).
- pypdf: established PDF text extraction, with explicit limits.
- PaperQA: direct `Docs.aadd` / `Docs.aquery` adapter; optional install and provider setup.
- Existing implementation: GitHub collector, SQLite FTS5, arXiv/HF clients, source snapshots and authenticated agent runner.

New local code supplies domain contracts, provider adapters, exact-quote validation, selection gates and CLI exposure. It does not recreate a generic agent framework. The live default uses the existing agent for evidence synthesis because no separate provider credentials were available.
