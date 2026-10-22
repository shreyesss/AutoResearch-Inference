# Round90: output transport and frontend CPU work

## Decision

**Zero new hypotheses, implementations or service qualifications.** Two concrete donor components were checked against the pinned target: zero-copy MessagePack IPC is already present, and one-pass JSON serialization already covers streaming chat. A remaining nonstreaming response component is retained for a changed workload premise, without creating a deferred card solely because source work remains.

Target source is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; planned deployment remains Flash-1017, TP1/DP4/EP4. Source paths and saved runner establish capabilities and selected benchmark behavior, not live process flags, current frontend topology or observed bottlenecks. No GPU, native package, model, server, canonical or cloud operation was performed.

## Adaptive search and prior comparison

Read the complete 153-record compact inventory with one consistent inventory hash, then searched retained round reports for serialization, IPC, output queues and buffering. OH21 removes an unnecessary generated-token-history tuple in a particular reasoning-usage path. S01/S07 concern input tokenization. HM65/AV68 concern worker metadata publication. HS30 removes prompt-tail cache helper overhead. None establishes a missing output transport component. Round30 already documents async execution/output completion and blocking D2H behavior; those were not repackaged.

First `expand` plus dated arXiv search used September 1 inclusive–October 23 exclusive, limit12, with CPU overhead/serialization/interprocess/output-processing terms. It returned12 abstracts, mostly application serialization, prompt representation or unrelated storage pipelines. The serialization branch was ambiguous despite an LLM/inference anchor. The next plan explicitly switched to OpenAlex and CPU/token-streaming terminology, keeping dates unchanged; ten abstracts included the useful ExaServe diagnosis. This is changed evidence coverage, not a measured improvement in search recall or hypothesis quality.

One plan used invalid status `off_topic`; the tool returned the allowed statuses and exact observation index. Changing it to `irrelevant` made the same plan usable. The original invalid plan and error are retained. A readonly corpus lookup initially confused the corpus table with the hypothesis schema; corrected after inspecting its columns. An unsupported `export --help` invocation is also disclosed; the final export uses readonly Store tables. No failures were hidden as successful searches.

ExaServe's canonical arXiv metadata was already retained and was selected-imported before fetching its exact v2 full text. One new fulltext logical cache miss occurred. The paper read was selective: architecture, proxy/streaming diagnosis, measurements and limitations. All22 returned abstracts have dispositions; abstract-only exclusions are not whole-paper judgments.

## Paper diagnosis: streaming path, not demonstrated local CPU saturation

[ExaServe, 2609.10812v2](https://arxiv.org/html/2609.10812v2) studies Aurora deployments reaching3072 vLLM replicas. Its measured streaming failure concentrates roughly195,000 SSE connections on the head node; server token latency remains healthy while client delivery worsens and TCP retransmissions increase. The measured section explicitly reports HAProxy below2% CPU and identifies network-I/O concentration. Its later discussion generalizes to possible endpoint CPU/port limits; that general statement does not override the measured section's narrower cause.

Distributing ingress is a meaningful component in that regime. It does not establish a missing CPU-copy optimization for our planned one-node EP group, nor that our retained gateway has the same topology or pressure. The saved Bitlane runner can address direct URLs or a selected gateway. Neither option proves that a centralized ingress bottleneck actually occurs. The paper's Ray startup handle-resolution cost is a startup/control-plane issue, not recurring long-output decode work.

## PR and exact target triangulation

Two readonly local title scouts used **updated_at >=2026-09-01**, not PR creation date. The initial frontend-inclusive scout was capped40 and noisy. A refined vLLM/SGLang transport-title scout returned44 (under its cap50). Their union contains81 titles, not81 deeply read PRs or exhaustive upstream coverage. Selected IDs were imported into isolated state and searched with actual `pr-search --explain`. Four logical GitHub detail/files reads hydrated the following two exact heads; all returned patches and tests were read. Donor tests were not executed.

### 1. SGLang45097: already-present zero-copy frame transport

[PR45097](https://github.com/sgl-project/sglang/pull/45097), `Aphoh/sglang@b9ab0c3c9c35a7897b4ae95c81ac25126829b72c`, makes MessagePack send/receive use `copy=False` and decodes received frame buffers. Its flag is opt-in; the author reports short-message overhead and larger-payload CPU savings, with tensor-owned-storage semantics retained. These measurements concern its engine, payload and disabled-prefix/graph setup, not our deployment.

The pinned target already has:

- a separate output-socket thread and nonblocking queue publication (`core.py`1148,1231,1642);
- `encode_into` buffer reuse and tracker-based reclamation (`core.py`2021–2041);
- tracked first-frame `copy=False` send and zero-copy remaining multipart frames (`core.py`2071–2086);
- async `recv_multipart(copy=False)` (`core_client.py`1211) followed by direct frame decoding (`serial_utils.py`344–350).

Thus the donor's removed copied-byte step is not an absent operation on this inspected target path. These source flags do not prove the native library performs zero physical copies for every message size or that the thread never contends for the GIL. They are sufficient to reject this direct port as a new intervention.

### 2. SGLang42889: nonstreaming residual, streaming already direct

[PR42889](https://github.com/sgl-project/sglang/pull/42889), `HJSang/sglang@b86177729c541d47dcf8ce67c4f27c7543fb704d`, replaces nonstreaming Pydantic-model return with one-pass `model_dump_json` and a Response. Its helper explicitly passes non-model responses, including streaming, through unchanged. The reported large gains involve nonstreaming top-logprob payloads and do not isolate ordinary streaming-token latency.

Target streaming chat already calls `chunk.model_dump_json(...)` before yielding SSE (`chat_completion/serving.py`493–499). The router wraps that generator in `StreamingResponse` (`api_router.py`82). The saved runner explicitly passes `--endpoint-type chat --streaming` (`sweep.py`225). This is a decisive existing-path check, not a microbenchmark.

Target **nonstreaming** `ChatCompletionResponse` still uses `JSONResponse(content=generator.model_dump())` (`api_router.py`74–78), so a selective one-pass port could remove Python intermediate materialization there. It is parked because the retained workload uses streaming and no concurrent large nonstreaming/top-logprob exposure was recovered. This does not reject the component for other workloads or assume indirect frontend contention is impossible. Reopen with actual nonstreaming/mixed-response exposure and CPU time, preserving JSON aliases, omitted/default fields, nonfinite handling, custom serializers, errors and metrics headers. No speed value from the donor is transferred.

Existing `stream_interval` buffering is also not a new mechanism. Increasing it can reduce emitted work by delaying ready output. Any such comparison must retain client ITL/stream-cadence semantics rather than relabel a delivery delay as a free performance improvement.

## Evaluation gate and stop reason

No new synthetic timing suite is justified for already-present operations. If future compatible traces show frontend exposure, use existing Mooncake/agent-p75 serving evaluation with timestamps from engine output availability, queue receive, serialization completion and client arrival, separating direct/gateway mode and response shape. Countertrace: if model/collective work determines token availability and output delay is negligible, this lane has no material headroom. Another countertrace: if client network delivery dominates, changing MessagePack serialization will not address it.

For the parked nonstreaming component, the cheapest authorized next check would be an exact endpoint CPU response replay with observed response shapes and complete parsed-JSON equality, followed only later by a mixed-traffic service comparison if that is the actual workload. It is not authorized or run in this round. No percentage or latency forecast is available: affected-event frequency and exposed component time are unknown.

**Yield:** two online queries,22 provider rows/22 paper identities, one selected new fulltext, two exact donor heads/patch sets, eight checked source quotes, zero new cards. Source export retains38 documents,39 immutable revisions and160 edges. Query/source records are local in isolated state; canonical import and S3 publication are not claimed. Source evidence closes this bounded question; additional generic output-overhead searches would not change the decision without new workload evidence.
