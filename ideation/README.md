# Inference ideation workbench

## B200 PR audit and experiment explanations

- [PR evaluation audit and reconstruction guide](runs/pr-evaluation-audit-001/README.md): source pins, frozen inputs, archive map, offline rebuild steps, 18 conditional performance plans and five correctness gates. No GPU experiments from this audit have run.
- [Plain-language experiment guide](runs/pr-evaluation-audit-001/walkthrough/NOVICE_GUIDE.md): the serving path, each proposed inefficiency and the first observation needed to decide whether to test it.
- [Detailed E01–E03 walkthroughs](runs/pr-evaluation-audit-001/walkthrough/README.md): source-level mechanism, eligibility and evaluation caveats from the October 20 discussion.
- [Evaluator critique and enhanced evalset](runs/pr-evaluation-audit-001/evaluation/EVALUATOR_RECONCILIATION.md): reconciled tooling advice, [source versus agent mechanism cards](runs/pr-evaluation-audit-001/evaluation/MECHANISM_CARDS.md) and [PR-specific measurement/frontier plan](runs/pr-evaluation-audit-001/evaluation/EVALUATION_PLAN.md). Documentation only; no benchmark or implementation was run.

## New: three independent tools

The preferred interface now separates **GitHub corpus tools**, **research/evidence tools**, and **hypothesis generation**. One calling agent uses ordinary JSON CLI calls; no orchestration server is required.

- [Architecture, contracts, gates and commands](docs/THREE_TOOLS.md)
- [Recent papers and actual repository choices](docs/RECENT_RESEARCH.md)
- [Instructions for the calling agent](docs/AGENT_WORKFLOW.md)
- [Live verification and limitations](docs/THREE_TOOLS_VERIFICATION.md)
- [Cloned Fathom web tools and live OpenAlex integration](docs/FATHOM_INTEGRATION.md)
- [Actual system design, diagrams, scoring and cost controls](docs/SYSTEM_ARCHITECTURE.md)
- [Interactive searches, user instructions and hypothesis playground](docs/PLAYGROUND.md)
- [Current verified state, costs, latest run and download progress](docs/CURRENT_STATE.md)
- [Latest live decision: proposal rejected after prior-art review](runs/three-tools-002/hypotheses/decision.md)

On the VM, from `/home/ubuntu/shreyas/skunk-work/ideation`:

```bash
.venv-research/bin/python -m ideation tools
.venv-research/bin/python -m ideation tool research.providers
.venv-research/bin/python -m ideation tool github.search \
  --args '{"query":"deepseek b200","match":"all","after":"2026-10-01","limit":5}'
.venv-research/bin/python -m scripts.demo_three_tools --output runs/three-tools-new
```

The environment imports pinned DiscoveryRSI records/replay/tool registry, PyAlex, JSON Schema validation and pypdf. PaperQA is an optional adapter requiring a separate install and configured model/embedding providers. The default evidence and hypothesis calls use the existing authenticated agent. New setup: create a Python >=3.10 virtual environment and install `requirements-research.txt`; optional PaperQA needs Python >=3.11 and `requirements-evidence.txt`.

Hypotheses use a task-derived rubric: novelty is off unless requested, and known methods/flags/ports can qualify. Every proposal and decision is retained in an append-only SQLite memory graph, linked to task, baseline, policy, evidence and scoped test outcomes. Selection remains distinct from experimental validation. See [adaptive policy and memory](docs/ADAPTIVE_POLICY_AND_MEMORY.md).

## Earlier prototype and corpus operations

Two tracks share one corpus: **find relevant engineering evidence**, then **turn it into testable mechanisms**.

Deployed at `sofia-gpu-mumbai:/home/ubuntu/shreyas/skunk-work/ideation`. The remote database is authoritative; the workstation has a separate prototype snapshot. No GPU workloads are launched.

## Open the workbench

Forward VM port 8765 in VS Code, or run:

```bash
ssh -N -L 8765:127.0.0.1:8765 sofia-gpu-mumbai
```

Open <http://localhost:8765>. Search words or quoted phrases; combine GPU, model/architecture, metric, source type, state, and date filters. Inspect each result for source text, base/head commits, and graph connections. GPU/model tags mean **mentioned**, not proven applicability. Dates are UTC; `after` is inclusive and `before` exclusive.

Open <http://localhost:8765/runs> for completed and in-progress research runs.

## Track 1: corpus and search

From the remote `ideation` directory:

```bash
python3 -m ideation status
python3 -m ideation search 'deepseek-v4.1-flash b200' --match all --after 2026-10-01
python3 -m ideation search 'tpot' --tag b200 --kind pr --state merged --date-field merged_at
python3 -m ideation search 'speculative' --kind issue --before 2026-09-01
python3 -m ideation hydrate 36037 62541 62073
python3 -m ideation graph github:vllm-project/vllm:36037
```

`sync` enumerates **all issues and PRs**, plus repository-wide issue comments and inline review comments, using GitHub REST continuation links. It avoids GitHub Search's result cap. Full PR details are a separate feed. Formal review submissions and diffs are downloaded on demand with `hydrate`; they are not exhaustively backfilled. Binary/missing patches and the GitHub 3,000-file PR limit remain explicit limits.

The initial historical archive is resumable and **not complete until each feed has a `completed_at` checkpoint**. A separate recent-change pass runs first. Incremental passes overlap by one day; an update watermark advances only after a pass finishes. Raw API pages are compressed under `data/raw/github/`; new requests have a URL/time/hash manifest. Records are idempotently upserted, not duplicated. Deleted/private/unavailable historical content cannot be recovered from the public API.

Hourly refresh and the UI run as user services with login lingering enabled:

```bash
systemctl --user status ideation-sync.timer ideation-sync.service ideation-ui.service
journalctl --user -u ideation-sync.service -n 20
systemctl --user start ideation-sync.service
```

An active long backfill is not duplicated by the timer. Interrupted/rate-limited runs retain progress and retry at a later timer tick. Authentication uses `GITHUB_TOKEN`, `GH_TOKEN`, or the VM's existing `gh auth`; tokens are never written to the corpus.

## Track 2: deep research and hypothesis generation

```bash
python3 -m ideation papers 'speculative decoding' --provider both --limit 8
python3 -m ideation fetch https://arxiv.org/abs/2603.03251
python3 -m ideation expand github:vllm-project/vllm:36037
python3 -m ideation citations arxiv:2603.03251 --limit 5
python3 -m ideation code vllm-project/vllm COMMIT_SHA path/to/file.py
python3 -m ideation research config/b200.json --output runs/my-new-run --timeout 900 --rounds 2
```

The default runner uses the already-authenticated Codex CLI (PATH, `IDEATION_CODEX_BIN`, or the VS Code extension). It preserves the configured model unless `--model` is supplied. Each run is: plan → fetch/search → draft → targeted follow-up retrieval → critique → revision → quote validation/repair. Stages have separate prompts, outputs and logs. `--rounds 1` skips the additional discovery round. Ordinary JSON/Markdown artifacts are the interface; there is no workflow server or GPU dependency.

The B200 brief is a starting profile, not an assertion that historical measurements prove a current bottleneck. Edit model/GPU/workload/metrics, the source pin, prior decisions, date window and requested count. The prototype uses five as a working shortlist target; unsupported candidates are dropped and shortfalls recorded.

Each card must state a concrete code change, nearest prior implementation, what is added, applicability, counterevidence, correctness, the strongest existing/static comparator and a cheap rejection test. Novelty relative to deployment, implementation and publication are separate fields. Publication novelty is not guaranteed. Quote validation proves that cited text exists, **not** that a claim follows from it; the critique pass and engineering review address that distinction.

Knowledge graph edges include mentions, explicit links, canonical paper identities, parent/child documents, bibliographic citations, and attributed hypothesis support/challenge. All edges retain source provenance. Keyword co-occurrence never becomes a causal claim. Explicit links and identities are followed during evidence-pack assembly.

arXiv and Hugging Face paper search work without new credentials. arXiv requests are spaced; HTML full text is captured where available, with method/evaluation/limitations excerpts. The new research environment adds pypdf fallback when arXiv HTML returns 404; a base install without pypdf reports the missing dependency. Semantic Scholar citation expansion is optional; the earlier live public request returned HTTP 429, so that path needs an API key or a later retry. HF paper coverage is curated and is not the entire literature.

## Legacy optional wider web research

This section describes the earlier prototype. Use the three-tool interface and adaptive policy guide above for current work; the legacy `research` command does not use the new hypothesis memory or task-derived rubric. GPT Researcher was the optional discovery backend. A separate `.venv-web` is installed on the VM; see `requirements-web.txt` for the exact package version. It needs its own configured model/search providers (normally `OPENAI_API_KEY` and `TAVILY_API_KEY`). Codex login is not automatically exported as an API key.

```bash
python3 -m venv .venv-web
.venv-web/bin/pip install -r requirements-web.txt
.venv-web/bin/python -m ideation research config/b200.json \
  --backend gpt-researcher --output runs/web-run --timeout 1200
```

That backend adds recursive web discovery before the same source-grounded hypothesis stages; its report is discovery context, not primary evidence. This optional API path has an import/setup check, not a completed paid-provider research run. The default Codex + arXiv + HF path has a completed live run.

## Artifacts and checks

- [Component plan and acceptance criteria](docs/DESIGN.md)
- [Open-source choices and reasons](docs/OSS_CHOICES.md)
- [Live prototype result](runs/b200-prototype-001/decision.md)
- [Prototype validation](runs/b200-prototype-001/validation.json)
- [Second live run, executed on the VM](runs/b200-prototype-002/decision.md)
- [Deployment and collection snapshot](docs/DEPLOYMENT_STATUS.json)
- [Observed repository revisions](docs/oss-snapshot.json)

Run `python3 -m unittest discover -s tests -v`. Tests cover cursor resumption, large-collection continuation links, aliases/filter intersections, distinct date semantics, reindexing/provenance, PR branch preservation, and rejection of fabricated citations. `python3 scripts/evaluate_retrieval.py --db data/corpus.sqlite` checks the three supplied examples; this is a small regression set, not a general relevance benchmark.

Local code is synced by the existing workstation sync job. Remote `data/`, virtual environments, and research runs are excluded from that mirror, so editing code cannot delete the collected corpus.

## What the live runs established

The first run completed planning, literature retrieval, five full-text downloads, targeted follow-up, critique, revision and citation repair. One conditional mechanism survived against a target of five. The second run executed on the VM with pinned-code retrieval and retained two provisional mechanisms; both carry explicit warnings that deeper implementation evidence is needed. These are demonstrations of the research pipeline, not claims of experimentally validated improvements or proven publication novelty. Both shortfalls are preserved in their manifests.

One exact PR-head source file downloaded successfully. The historical baseline's requested raw file returned HTTP 404; the runner records that gap rather than substituting current main. Subsequent runs also hydrate a bounded shortlist of newly discovered PRs before synthesis. arXiv keyword queries now use explicit Boolean conjunction, with a logged relaxation when there are no results; this avoids treating a long natural-language query as an implicit OR search.
