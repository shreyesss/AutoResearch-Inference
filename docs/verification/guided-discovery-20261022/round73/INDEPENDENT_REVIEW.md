# Independent review of round73: exact Engram remainder

## Verdict

No blocker to retaining ER73-01 as a **scoped deferred experiment**. The adapted quotient/remainder algorithm is mathematically sound over the admitted integer domain. Neither its native implementation nor a performance benefit has been established. No author packet was changed.

Verified all 53 frozen author files, seven exact claim quotations against their exported revision bodies, and byte equality of the two principal target source copies with the local c455 pin. Read the complete report/card, relevant Engram/model code, the selected paper formula and author arithmetic diagnostic. I did not rerun the author's 3,312 scalar cases. Review execution comprises four separate arbitrary-precision formula controls, hash checks and quote readback. No native/model imports, compilation, GPU work, new online retrieval or canonical mutation occurred.

## Domain and masks

The multiplier generator bounds each valid mapped-ID product below 2^63. XOR does not introduce a sign bit when every operand has bit 63 clear. Mapped padding is a valid compressed ID. Dead or blocked history values are replaced with this pad value before multiplication. The V1 cache starts with zeros and stores mapped/dead IDs; V2 uses provided lookback history with mapped padding fallback. This supports the source domain under the existing valid token/history-input contract; it does not prove that an arbitrary corrupted cache or invalid token ID is safe.

The inspected image sentinel mask marks tokenizer ID 129264 before dead-value replacement; that path does not require treating a negative sentinel as an unsigned multiplicand. Invalid token lanes do not store outputs. Current eight heads fill the head tile. The generic inactive-head divisor 1 needs an explicit result or safe fallback: floor(2^64/1) cannot be stored in uint64. The proposed correction preserves original XOR order and output offsets. Exact bucket identity is mandatory because changed IDs select different learned rows.

## Mathematical transfer and adversarial control

For Q=2^64, p>1 and mu=floor(Q/p), the real quotient difference x/p - x*mu/Q is nonnegative and less than one for 0<=x<Q. Consequently floor(x*mu/Q) is the true quotient or one below; the residual lies in [0,2p), and one subtraction yields the exact remainder. Also q*p<=x, so reconstruction fits unsigned64. This argument does not depend on the number of random examples.

The selected paper's Figure 1 uses a uint32 numerator and ceil(2^64/p) with a low-product formulation. Simply widening its numerator is invalid. My independent four-case control shows failure at x=2^63-1 and at a permitted product-bound endpoint for p=16000057, while the proposed floor-reciprocal algorithm remains exact. The bound endpoint is not claimed to be an observed target hash or the actual fixed-seed sampled multiplier. This refutes a direct formula transplant, **not** the separately derived adaptation.

## Ownership and compiler alternatives

Generated prime/multiplier buffers belong to EngramHash and are nonpersistent. Ordinary learned-weight loading does not itself establish a new prime layout. Prepare constants with that owner, keyed to the entire ordered divisor/layout contract; changed layout, device allocation or captured pointers require appropriate regeneration and capture handling. Avoid an extra per-step launch or host preparation. Sleep/wake and graph replay remain native integration gates.

The strongest objection is that `%` in source is not proof of an expensive instruction surviving compilation. A compiler may already lower it efficiently. Conversely, a tuple indexed by dynamic layer/head is not automatically a per-lane constant. Compare original loaded-prime remainder, actual constant-divisor specialization, and explicit unsigned64 multiply-high plus correction. Extra loads, registers, selects or spills can erase any arithmetic saving. Correct Python high-product arithmetic does not certify native unsigned lowering.

## Exposure and next useful check

The source launches one hash invocation spanning both Engram layers on the current forward stream before embedding lookup preparation and early decoder work. The auxiliary prefetch stream waits on that stream; later consumers wait on lookup completion. These dependencies support relevance but do not measure occupied or exposed cost. Logical 48*N output remainders are neither instruction count nor an ITL prediction. There is no extra factor for decoder depth, draft depth or already included verification rows.

The cheapest remaining discriminating check is to inspect any already-retained exact-kernel compiled artifact. If none exists, a later separately authorized code-generation comparison must establish actual divisor lowering, multiply-high implementation and resource costs for all three arms. Native output equality across pad/dead/history, partial blocks, changed batches, reinitialization and replay comes before timing. Then compare the whole hash invocation and the unchanged serving workloads. No such compilation or measurement is authorized or performed here.

The current paper and source evidence justify a bounded experiment, not priority above measured alternatives or a service forecast. No fresh hypothesis identity was created by this review.
