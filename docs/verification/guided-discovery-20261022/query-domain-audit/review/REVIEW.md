# Independent query-domain development audit

Frozen A/B/C protocol applied to both retained outputs; classification uses abstracts only. No network/GPU work.

| Set | A: execution mechanism | B: background | C: off-domain/learned change | Total |
|---|---:|---:|---:|---:|
| Historical broad | 0 | 2 | 6 | 8 |
| GPU anchored | 3 | 5 | 0 | 8 |

The GPU anchor removed obvious non-GPU senses of kernel/dependency/inference in this development case. It did not establish better recall, transferable performance, or accepted hypotheses. Five of eight anchored hits remain background under the specific mechanism criterion. Fixed-reduction GEMMs, SyclKittens and CoRun merit mechanism inspection, with incompatible precision/hardware or strong-baseline questions respectively.

N:M co-design is borderline: its abstract names adaptive parallelism but does not specify an independently reusable dependency mechanism. Classifying it A instead changes counts in both sets, not the observed removal of off-domain hits. The repeated hit is scored identically.

## Per-hit judgments

- **historical-search.json / arxiv:2608.15225: C** — Linux vulnerability trigger configuration; kernel and inference are non-GPU meanings.
- **historical-search.json / arxiv:2607.12505: B** — GPU sparse-GEMM dataflow and adaptive parallelism are relevant background, but abstract does not establish a specific dependency/launch mechanism independently applicable to frozen dense/MoE weights. Borderline A under a broader scheduling definition; same classification in both sets.
- **historical-search.json / arxiv:2607.06274: C** — Acoustic neural kernel estimation; no GPU execution mechanism.
- **historical-search.json / arxiv:2610.14318: C** — Statistical dependence and Markov kernels; not GPU execution.
- **historical-search.json / arxiv:2610.01069: C** — Learned dynamic logic-gate architecture/routing; no separable GPU schedule in abstract.
- **historical-search.json / arxiv:2607.23869: C** — Learns attention feature maps and trains network; no separable GPU execution mechanism.
- **historical-search.json / arxiv:2606.08094: B** — GPU VLA runtime and reuse of observation computations; no explicit GPU dependency/launch schedule described. Ternary kernel and robot model assumptions do not establish target compatibility.
- **historical-search.json / arxiv:2610.14214: C** — Hallucination metric substitutes embedding similarity for NLI; not a GPU execution schedule.
- **anchored-search.json / arxiv:2609.30059: B** — GPU kernel optimization/verification process, but no particular dependency/launch scheduling intervention stated in abstract.
- **anchored-search.json / arxiv:2607.11262: B** — Models tile dependency graphs; a simulator, not an established deployment scheduling intervention in abstract.
- **anchored-search.json / arxiv:2609.25624: A** — Explicit shape-fixed reduction order and fused register upcast are an execution-dependency mechanism with unchanged 16-bit weights. Target quantization/accuracy/performance compatibility unverified; benefit is versus a reproducibility baseline, not native target.
- **anchored-search.json / arxiv:2607.12505: B** — GPU sparse-GEMM dataflow and adaptive parallelism are relevant background, but abstract does not establish a specific dependency/launch mechanism independently applicable to frozen dense/MoE weights. Borderline A under a broader scheduling definition; same classification in both sets.
- **anchored-search.json / arxiv:2607.22432: B** — Models overlap, ordered tile actions and cache reuse for analysis; no particular new serving dependency intervention established in abstract.
- **anchored-search.json / arxiv:2607.11368: B** — Matched runtime/quantization attribution study and topology comparisons; coordination identified but no concrete dependency remedy in abstract.
- **anchored-search.json / arxiv:2610.04277: A** — Explicit operand placement, L1 prefetch and fabric communication schedules exposed by tile API. Intel-only evidence; target NVIDIA transfer unverified.
- **anchored-search.json / arxiv:2608.14376: A** — Isolated prefill plus fixed-shape batched decode/CUDA graphs explicitly changes execution scheduling without retraining. Comparison is batch-invariant determinism systems; improvement over our native runtime is unknown.

This is a development case, not a held-out tool evaluation. Titles or abstract speedups were not treated as target evidence. Fulltexts already present elsewhere did not influence this abstract-only classification.
