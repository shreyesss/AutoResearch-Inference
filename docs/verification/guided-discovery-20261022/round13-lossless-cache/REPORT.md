# Round 13: exact KV representation compression

22 October 2026. **Outcome: three interventions screened; none implementation-qualified.** Retain a conditional
CPU data diagnostic, not an implementation recommendation or a service gain.

## Why this lane

The prior index covers cache admission/eviction, physical index mapping, sparse
scoring, and AT03's repeated materialization. It does not establish whether the
already-quantized cache bytes have useful lossless redundancy. This is a distinct
question from changing precision or discarding tokens. Baseline remains the
planned Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, vLLM
`c4557869393db4d75c483d92edd02a5125500883`, two TP1/DP4/EP4 groups. Live execution
and cache pressure are unverified.

## Adaptive retrieval actually executed

1. arXiv `abs:lossless AND (abs:"KV cache" OR abs:"key value cache")`, June 1
   inclusive–October 23 exclusive, limit 8. Eight hits; one preserved query,
   no hidden fallback. Several results use “near-lossless” for lossy methods.
2. OpenAlex `lossless KV cache entropy coding`, same dates/limit. Eight hits.
   D-Quant offers a fixed-record entropy scheme; AlignPred concerns persistent
   storage. Read their full texts using `investigate`, no model reasoning.
3. D-Quant cites SplitZip as genuinely lossless. Followed that exact citation
   with `id:2605.01708`, deliberately lifting the recent-publication restriction
   for this named foundation, not repeating a broad search. The result identifies
   v3; `investigate` retained v3. A preliminary browser read of v1 was superseded
   by the retained v3 before final conclusions. This extra lookup changes the
   decision: its FP8 appendix distinguishes E4M3 from E5M2.
4. Inspected donor repository at `42c743118a29db3270ae6a921a4a4eecb20cad04` and
   pinned target record/read paths. No donor import, dependency installation,
   GPU helper or serving code was executed.
5. Three bounded read-only local PR queries found no named donor matches.
   Broad “lossless/cache” and “entropy/KV” hits were largely different mechanisms;
   opening records are not inspected implementations. `local-pr-search.json`
   retains results. An exploratory rowid join was corrected to stable source ID
   before assessment. This is not proof of corpus-wide absence.

The command journal and raw tool receipts retain actual calls. The plan ledger is
a retrospective account, not a claim that `expand` executed before each query.

## Three mechanisms examined in depth

### LC01 — D-Quant fixed-size entropy records

The paper makes entropy streams fit fixed token records by altering expensive
symbols; its encoder also rotates/requantizes inputs. Selective reuse of the
entropy coder is conceivable, but dropping drift removes its fixed-size guarantee
and requires overflow/fallback storage plus a new sparse reader. Existing E4M3
bytes cannot simply be passed through the published quantization chain unchanged.
This branch therefore fails the proposed exact-current-cache intervention, not
all possible lossy compression research. Source: method §§4.2–4.5; “a small
fraction of values drift” in [D-Quant](https://arxiv.org/html/2609.19880v1).

**Disposition:** reject direct exact-preserving port; no numerical target ROI.

### LC02 — AlignPred restoration codec

The method is explicitly error-controlled rather than byte-exact. Its selective
entropy stage is lossless over residual codes, not over original KV values. It
targets persistent cache restoration; the DeepSeek path restores pre-FP8 C4
values through native writeback. This differs from compressing resident packed
Flash-1017 rows consumed during decode. Source: method §3.4 and appendix D.1;
“Residuals are quantized on an error-bounded lattice” in
[AlignPred](https://arxiv.org/html/2610.17970v1).

**Disposition:** reject the current exact resident-cache intervention as scoped;
retain as a future persistence resource if that workload is introduced. A
Mooncake workload trace does not itself imply deployed Mooncake KV transport.

### LC03 — SplitZip lossless exponent coding

The exact codec is relevant, but its own FP8 experiment reports E4M3 Top-8
**0.933×** compression (expansion), versus E5M2 Top-16 **1.136×**. These are paper
results on its workload, not Flash-1017 forecasts. The released implementation
uses BF16-style 16-bit decomposition, whole-buffer decode and dynamic escape
count extraction. Its payload property charges seven bytes per escape; this is
not the paper's three-byte simplified accounting. The public code does not
release the FP8 implementation or SGLang/Mooncake integration.

Do not over-reject: reinterpreting paired FP8 bytes as 16-bit words need not lose
bits. The resulting pseudo-exponent is a different distribution, and a return
view/shape adapter would be needed. Exactness alone does not establish useful
compression or random-access performance. Sources: appendix C of
[SplitZip v3](https://arxiv.org/html/2605.01708v3) and
[pinned codec](https://github.com/Intelligent-Microsystems-Lab/SplitZip/blob/42c743118a29db3270ae6a921a4a4eecb20cad04/codec_gpu.py).

**Disposition:** defer target adoption; revisit only if existing archived target
cache bytes demonstrate net savings after metadata and a bounded reader design.

## Pinned target delta and objections

Target `common/ops/cache_utils.py:40–55` identifies V4.1 main-cache rows as 512
E4M3 values plus 16 UE8M0 scales: **528 bytes**. NVFP4 compressed-cache rows are a
separate optional 288-byte branch, while SWA can remain 528. The indexer has its
own format; it must not be treated as another 528-byte cache.

`attention.py:515–531` resolves format and page alignment. The insert/gather
operators use block and token strides. A compressed replacement would therefore
require agreed allocation sizes, row lookup, escape metadata and decoding before
the existing attention reader, or a new reader contract. It is an integration
proposal, not an existing switch. AT03 already addresses repeated BF16 gather
materialization; this proposal cannot claim that saving again.

No compatible target FP8 data histogram, byte sample, cache-pressure trace or
component exposure was found by the earlier exposure audit. The mathematical
ceilings are not target compression ratios, memory traffic or latency savings.

## CPU falsifier actually executed

`codec_contract.py` implements the published integer decomposition and runs it
over every **65,536** possible 16-bit word, including arbitrary paired-byte
patterns. All reconstruct exactly with explicit escapes. It separately extracts
and executes only the donor's actual `compressed_bytes` property with size-only
objects; no Torch/Triton/GPU import occurs.

For a hypothetical 528-byte object under that public accounting, 264 words have
a 396-byte dense payload. Eighteen escapes give 522 bytes; nineteen give 529,
before additional integration overhead. Constructed zero bytes give 396 bytes;
a constructed cycling-byte pattern gives 1,964. These are deliberately synthetic
counterexamples to universal compression, **not tests of target KV data or the
GPU codec**. The property excludes construction scratch and shared codebook
ownership, so this is generous transmitted-payload accounting.

## Cheapest reopening test and evaluator mapping

If a genuine existing Flash-1017 FP8 cache dump becomes available, first check its
model/revision, record kind, scale bytes and sequence/block boundaries on CPU.
Compute native E4M3 exponent and paired-word histograms, exact compressed payload
including offsets/scales/codebook and worst-case overflow; compare with unchanged
528-byte records. Preserve byte equality for every sample. Stop if total bytes do
not fall, or random selected-token access requires decompressing enough unrelated
data to erase the possible saving. No new GPU capture is requested here.

Only after that gate would a future native experiment be meaningful:

- Same quantized values, cache ownership and selected token IDs; differential
  byte/logit/output checks are needed because AIPerf is not a numerical validator.
- Existing agent-75 and Mooncake request suites cover service TTFT/ITL/E2E,
  throughput and error/tail guards under their existing distributions. Preserve
  their workloads; count actual memory pressure, codec invocations and bytes.
- A persistent restore or PD transfer claim needs an actual restore/transfer
  event test because ordinary request replay does not establish that path. That
  would be a separately scoped experiment, not justification to change the
  current benchmark or claim absent events improved.
- No component or service improvement is forecast; no GPU experiment ran.

## Yield and stop reason

Sixteen initial paper records, one explicit older citation, three full-text
mechanisms examined, one pinned donor codec and pinned target source audit.
**Three concrete interventions formulated: two rejected as scoped, one deferred. Zero implementation-qualified interventions and zero measured service improvements.**
`candidates.json` retains all three; no canonical hypothesis writes occurred.
One conditional archival-data diagnostic is retained. Stop this lane because the
remaining discriminating evidence is actual target cache bytes/access exposure,
not another loosely related paper. Do not inflate yield by counting entropy,
drift and escape layout as independent hypotheses.

## Independent adversarial review

The separate reviewer accepted that no intervention is implementation-qualified; all three screened interventions remain recorded; see
`INDEPENDENT_REVIEW.md` and `review.json`. Its source audit confirms that
compressing bytes inside unchanged fixed-size allocated pages does not release
HBM. The donor's returned encoded object still retains counts/starts construction
scratch, even though transmitted-payload accounting omits it. Dynamic `.item()`
and escape-dependent allocation also prevent treating this public encoder as a
ready CUDA-graph-contained resident codec.

The review's separate CPU arithmetic bounds give an ideal 3.03% scale-only byte
ceiling and 12.12% E4M3 Top-8 ceiling before escapes/headers/offsets on a 528-byte
record. These are conditional representation bounds, not achievable target gains.
Neither review closes target histogram, runtime compatibility, memory pressure or
service-value gates. This is independent critique of source and limited CPU
checks, not independent reproduction of the papers or serving measurements.
