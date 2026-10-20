# Use the tools interactively

Run these on `sofia-gpu-mumbai`, from `/home/ubuntu/shreyas/skunk-work/ideation`. The remote corpus is the live one.

## Start by inspecting searches

Forward port 8765 in VS Code, then open:

- [MoE decode GEMM since September](http://localhost:8765/?q=MoE%20GEMM%20decode&match=all&after=2026-09-01)
- [B200 autotuning failures](http://localhost:8765/?q=B200%20autotune&match=all&after=2026-09-01)
- [CUDA graph + fused MoE](http://localhost:8765/?q=CUDA%20graph%20fused_moe&match=all&after=2026-09-01)

Each result has an Inspect button for full stored opening body, metadata and graph connections. The interface now displays the raw BM25 rank. Discussion and code are separate records; an opening body does not imply the full thread has been collected.

```bash
.venv-research/bin/python -m ideation tool github.search \
  --args '{"query":"MoE GEMM decode","match":"all","after":"2026-09-01","kind":"pr","limit":5}'
.venv-research/bin/python -m ideation tool github.get --args '{"number":57977}'
.venv-research/bin/python -m ideation tool github.get --args '{"number":46238}'
.venv-research/bin/python -m ideation tool research.cache_status
```

Actual inspected leads from this session:

| Lead | Why inspect | What it does not establish |
|---|---|---|
| [#57977](https://github.com/vllm-project/vllm/pull/57977), MXFP8 activation handoff | Existing work removes re-quantization launches; a generic “keep FP8 between kernels” proposal needs a specific new difference | That the deployed baseline includes it or the reported gains transfer |
| [#46238](https://github.com/vllm-project/vllm/pull/46238), SM100 autotuning guard | Reports TMA alignment faults at tiny expert token counts; useful counterevidence to unsafe automatic tuning | That all kernels, precisions or B200 workloads share that failure |
| [#60468](https://github.com/vllm-project/vllm/pull/60468), MegaMoE warmup | Separates first-request JIT stalls from steady decode performance | A steady-state TPOT improvement |
| [#54520](https://github.com/vllm-project/vllm/pull/54520), NVFP4 MegaMoE integration | Direct-to-symmetric-buffer staging and graph-safe allocation contracts | Measured DeepSeek/B200 gains; its reported experiment uses GLM/GB300 |

[Full eight-query inspection report](../runs/moe-low-m-001/search/inspection.md). [Editable generated plan](../runs/moe-low-m-001/planning/plan.json). The query results are bounded candidate lists, not claims that every relevant PR was found.

## Control scope with ordinary instructions

Tell the calling agent, for example:

> Search only merged vLLM PRs from the last month about B200 low-batch MoE kernels. Exclude MTP. Show five concrete code changes and failure cases; do not generate hypotheses yet.

> Broaden to SGLang and TensorRT-LLM implementation evidence. Focus on graph-safe per-shape dispatch; give one falsifiable adaptation and its strongest static comparator.

> Switch to CPU tokenization overhead on H100 serving. Search code and issues first. Keep web searches to one. Identify unknowns before proposing an experiment.

Different repositories need their own collected corpus or direct pinned-code reads; changing `repo` does not download another repository automatically. Natural-language controls are interpreted by the calling agent and optional planner, not by the FTS engine.

## Generate and edit a plan

```bash
.venv-research/bin/python -m ideation tool research.topics
.venv-research/bin/python -m ideation tool research.topics --args '{"ids":["05","12","19"]}'
.venv-research/bin/python -m ideation tool research.plan --args '{"instructions":"Investigate B200 low-batch MoE dispatch and graph replay. Exclude MTP. Seek counterevidence and one falsifiable mechanism.","topic_ids":["05","12","19"],"after":"2026-09-01","count":1,"output":"runs/my-direction/planning"}'
```

Edit the generated `plan.json` / `brief.json`, or create them manually. Then:

```bash
# Local search only; no model or external search calls.
.venv-research/bin/python -m scripts.search_plan \
  --plan runs/my-direction/planning/plan.json --output runs/my-direction/search
# Use a new output folder to preserve prior results. Add --papers and/or --web explicitly.
```

Queries should progress from mechanism to identifier to failure case. The guide contains 20 groups/878 terms; it is not a checklist of 878 API calls.

## Evidence and hypothesis generation stay separate

After inspecting candidates, choose source IDs. Read paper full text using `research.read`; use `research.web_read` for general pages. `research.get` returns stored text. `research.citations` expands a useful OpenAlex work in both directions. `research.triage` cheaply ranks URLs already present in selected source records; its output is discovery context.

```bash
.venv-research/bin/python -m ideation tool research.web_search \
  --args '{"query":"DeepSeek B200 low batch MoE kernel performance","limit":5}'
.venv-research/bin/python -m ideation tool research.read \
  --args '{"url":"https://arxiv.org/abs/2410.12247"}'
```

One optional convenience command runs evidence then hypotheses, with explicit inputs:

```bash
.venv-research/bin/python -m scripts.run_selected \
  --brief runs/my-direction/planning/brief.json \
  --question 'What evidence supports or challenges graph-safe low-M MoE dispatch?' \
  --source github:vllm-project/vllm:46238 \
  --source github:vllm-project/vllm:54520 \
  --source fulltext:2410.12247 \
  --output runs/my-direction-analysis
```

This small source set may be inadequate; a rejection is useful feedback, not a reason to weaken the gates. Add relevant exact-SHA code and contrary evidence before implementation. Latest run: [MoE analysis decision after the citation-context fix](../runs/moe-low-m-002/decision.md).

## Inspect costs and freshness

```bash
.venv-research/bin/python -m ideation tool research.cache_status
.venv-research/bin/python -m ideation tool github.status
```

`refresh:true` is available for research search/citations/read/web-read/web-search/triage. It forces fresh retrieval while retaining provider budget limits. See [system architecture](SYSTEM_ARCHITECTURE.md) for precise TTLs, actual OSS reuse, gates and limitations.

## Completed B200 exploration

See [three-agent findings and six experiment designs](../runs/frontier-exploration-001/REPORT.md). The run includes seeded search logs, recent research, pinned source inspection, original and repaired reviews, and registered conditional test plans. Start with the baseline audit and CPU eligibility checks; no GPU experiment has run.
