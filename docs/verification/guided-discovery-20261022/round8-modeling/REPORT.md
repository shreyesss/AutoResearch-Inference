# Round8 — evaluator components and assumption audit

CPU/source-only; no new serving hypothesis counted. Parent self-review, not independent evaluation. Exact target remains Flash-1017, DSpark5, TP1/DP4/EP4. No GPU work or simulator-generated service claim.

## Adaptive search actually executed

A general web query surfaced RoofLang and a SGLang optimization report. Then the actual research tool ran one bounded OpenAlex query: `LLM inference performance modeling simulation architecture optimization`, published >=2026-07-01 and <2026-10-23, limit8. Eight records returned without provider search errors. RoofLang did not appear in this bounded set: web discovery and tool discovery are separate provenance, not claimed as one successful retrieval.

Selected the October compositional-KV paper and September AgentPerfBench for `investigate`, with two sources, four HTTP misses maximum, zero repositories and no paid model reasoning. Both full texts were retained. Both citation lookups failed with ProviderError; no citation coverage is established. Source dossier readiness does not mean complete research. Full-text URLs were unversioned; exact observed content hashes and receipt limitations remain retained. Online v1 HTML was also inspected separately.

The search was useful for evaluation design and contrary evidence. It did not yield another service-qualified optimization. State and original query/source documents are isolated under `state/`, not yet imported to canonical memory or S3.

## Component selection

### RoofLang: retain modeling discipline, defer simulator adoption

[Paper](https://arxiv.org/html/2609.12551v1), [author code](https://github.com/yzygitzh/rooflang).

Its architecture-search results are simulated, with ideal compute/communication overlap and balanced expert routing. The evaluated graphs omit speculative decoding and KV appends. Initial graph correctness remains external. Useful components are explicit dependency/resource graphs and constrained transformations. These assumptions preclude transferring its percentages to Flash-1017. A target-specific, validated graph and calibrated uncertainty would be required before using it as a selection oracle. No code was installed or executed.

### Compositional KV modeling: retain state invariants

[Paper](https://arxiv.org/html/2610.15366v1).

Separate logical reusable content, reserved capacity, and completed/visible replicas. Protect a source during transfer; publish destination readiness only at completion. Its timing models require calibration and validation on compatible workers. Reported Qwen/SGLang accuracy is not target accuracy. These invariants strengthen later cache-policy CPU checks; adoption of an entire simulator is not justified by the current task. No author implementation was established from this investigation; linked Vidur/SGLang are not automatically its repository.

### AgentPerfBench: retain context-growth coverage, reject content-independence transfer

[Paper](https://arxiv.org/html/2609.34683v1).

Its agent-session profiles and saturation sweeps are useful comparison dimensions. The paper states that random token content at matched lengths gives equivalent serving behavior; that assumption is not established for our deployment. Our source routes token-dependent hidden states to experts and uses content-dependent speculative acceptance, so matched lengths alone cannot certify equivalent traffic or useful progress. Keep actual prompt identities, sampling settings and prefix reuse when evaluating these mechanisms. The inspected v1 lists its code/data link as anonymized; do not claim an installed off-the-shelf package.

## Application to retained candidates — our engineering inference

- RD01/M01: preserve routed-expert distributions and decode/verify token counts; a length-only workload model cannot select a locality or tile tactic reliably.
- AT03: model peak live dedicated-buffer storage and actual reader lifetime; removed byte counts do not imply exposed latency savings. Its within-forward reuse does not require a new cross-request KV routing simulator.
- S01/routing work: repeated fixed prefixes do not replace growing-session replay. Reuse standard benchmark variants where they express the required behavior; add a narrowly defined trace only when a named failure mode remains uncovered.
- Future cost-model integration: typed measured/inferred/unknown inputs, capacity and dependency checks, sensitivity to overlap, and a source-specific no-GPU diagnostic. No single simulator score becomes a golden acceptance gate.

## Yield

One online research query;8 hits;2 selected full texts;2 failed citation expansions;0 new hypotheses;3 evaluator components considered with explicit limitations. Existing cards can reference this assessment without being duplicated. This is evidence inspection, not a controlled experiment proving a better research skill.
