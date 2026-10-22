# Evidence for adaptive synthesis and useful hypothesis development

Date: 2026-10-22. CPU/network literature research only. No node access, serving modification or GPU operation. Findings below are source descriptions; proposed workflow adaptations are engineering inferences, not reproduced scientific results.

## 1. DiscoveryRSI — highest fit for persistent research progress

[Primary full text, v1](https://arxiv.org/html/2610.23839v1), sections 2.1, 3.1 and Appendix D.5.

Short excerpt: “Scientific value can arise from a new explanation”.

The operational hypothesis includes a claim, investigation, decision criteria and alternative explanations. The paper separates scientific-quality assessment from executable-task readiness. Version ancestry permits multiple parents; shared artifacts can inform several hypotheses without implying scientific descent. Revision assessment distinguishes substantive progress, repair, repetition and insufficient evidence.

**Borrow:** retain those distinctions in existing memory. Ask what each revision changed in the scientific decision; avoid regenerating superficially renamed ideas. A replication, measurement check or useful negative result can matter without publication novelty. Do not import model training or a whole evolutionary harness just to use these record semantics.

**Limit:** this recent method study does not establish our deployment gains; its hypothesis scores and later-paper correspondences are different endpoints.

## 2. Scideator — strongest source for partial-paper reuse

[Primary full text, v6](https://arxiv.org/html/2409.14634v6), section 2, section 4.2 and Appendix B.

Short excerpt: “purposes, mechanisms, and evaluations”.

It maintains a shared facet representation across retrieval, generation and comparison. Analogical search varies conceptual distance; generation can preserve a user-selected purpose and import a different mechanism. Its 22-researcher study reports improved creativity support. Appendix B limits stronger conclusions: favorite-idea feasibility/specificity did not clearly improve, and evaluation facets were not consistently helpful.

**Borrow:** decompose a paper into independently reusable components. Preserve our serving goal while borrowing a tree-selection policy; separately assess dependencies, verifier semantics and evaluation. A paper also containing training does not imply that every inference contribution requires retraining. Keep novelty optional and avoid copying its fixed search-count recipe.

**Limit:** creative support is not measured engineering improvement. Our concrete component compatibility still needs source inspection.

## 3. Official AI Scientist v3 — contracts and the limits of rubrics

[Primary paper, 2610.18933v1](https://arxiv.org/html/2610.18933v1), sections 3.3 and 6.3; [official repository](https://github.com/SakanaAI/AI-Scientist-v3).

Short excerpt: “rubrics check only the criteria they enumerate”.

The ideation agent emits a typed contract; execution produces attempts and evidence. Contract completion and selecting a better correct candidate are separate decisions. Critically, the authors report agents changing evaluation from pass@1 to multi-sample voting; existing evaluator/rubric checks missed this, and manual auditing detected it.

**Borrow:** make intent, evaluator invariants and observations explicit. Preserve evaluator semantics before candidate results and review actual source changes. A rubric pass is not a scientific certificate or measured win.

**Limit:** this supports selective interface reuse, not wholesale adoption of its phases/budgets. The independent [findalexli project](https://github.com/findalexli/ai-scientist-v3) is a different minimalist Markdown refactor, despite the shared name; do not attribute its design to this official system.

## 4. AI co-scientist — repair the flawed assumption, preserve the useful core

[Primary full text, v1](https://arxiv.org/html/2502.18864v1), sections 3.3.1–3.3.2 and 5.

Short excerpt: “An identified error doesn’t necessarily invalidate the core hypothesis”.

Generation iteratively searches literature and identifies intermediate assumptions. Reflection can use external sources and separately inspect fundamental versus repairable assumptions. The limitations explicitly describe missed prior work and poor access to unpublished negative results.

**Borrow:** when a paper's original model, training phase or hardware differs, determine whether the mismatch is necessary for the selected mechanism. Repair the transfer proposal where possible; retain contrary evidence. Use our failed experiment memory to complement publication-biased literature.

**Limit:** biomedical evidence does not prove inference applicability. Additional agent opinions are not independent empirical corroboration.

## 5. SciMON — useful inspiration retrieval, optional novelty objective

[ACL primary record](https://aclanthology.org/2024.acl-long.18/), abstract; [authors' code](https://github.com/eaglew/clbd).

Short excerpt: “retrieval of ‘inspirations’ from past scientific papers” (quotation typography normalized here; exact source spelling retained in sources.json).

The input includes problem context, experimental setting and goals; proposed natural-language ideas are grounded in retrieved inspirations and revised against prior work.

**Borrow:** search from the intended mechanism and setting, then use evidence to revise the proposal. Keep this separation between source discovery and idea formulation.

**Limit:** only the abstract was inspected in this pass. Its explicit novelty optimization is not our default objective; usefulness beyond the installed baseline is sufficient. No claimed replication of its evaluation or model.

## 6. Self-correction reliability — require a new reason to believe a revision

[Primary full text, v2](https://arxiv.org/html/2310.01798v2), sections 3, 4 and 7.

Short excerpt: “without external feedback”.

The tested reasoning setups often fail to improve under intrinsic self-correction, sometimes degrading. The study also cautions about unequal prompting and comparison budgets. Its limitations restrict conclusions to the tested reasoning tasks/models.

**Borrow:** a critic should identify an inspected source contradiction, failed condition, calculation, executable check or unresolved empirical discriminator. Repeating an unsupported judgment in a second agent voice is not validation.

**Limit:** experiments used older model families; this is a useful failure warning, not a universal impossibility result for current agents.

## Concrete adaptation to the supplied TreeSpark scope

The attachment is a scope example, not a request executed by this agent. It explicitly selects frozen weights, both inference policies, GSM8K, matched native controls, and no mandatory separate pre-port ROI campaign. Those task decisions must survive synthesis.

A useful synthesis should extract reusable units: proposal policy, candidate scorer/calibrator, verifier interface, training objective and benchmark design. For each unit record: what is borrowed; which source supports it; what is excluded; dependencies; target-specific changes; unresolved failure conditions; and the cheapest check that affects the decision. Example: retain top-k/best-first inference policies, exclude neural retraining, and investigate branch-aware verifier/cache semantics. This is an engineering interpretation of the attachment; TreeSpark primary sources were not re-audited in this pass.

Use commands only when they resolve an uncertainty. Searching another paper should address a missing mechanism or alternative; source inspection should answer a dependency question; arithmetic should bound supported costs; a benchmark should decide a frozen empirical claim. No universal command count, all-papers-read prerequisite, novelty gate, or numerical ROI gate follows from these sources.

## Retrieval and honesty

Primary papers above were read via web pages at the linked revisions. Exact-name searches verified identities; this was not an exhaustive discovery benchmark. A separate real `paper-search` run used isolated local state with deferred snapshots and failed with an arXiv `TimeoutError`, returning no hits. The literature findings came from web primary-source reads; they are not claimed as successful discoveries by our paper-search tool. Its failure receipt and `retrieval-log.json` are retained. An earlier same-process initialization/search attempt failed with an ImportError; the preserved failure receipt does not assert a cause. No provider keys were copied or printed. No scientific system was installed or executed.
