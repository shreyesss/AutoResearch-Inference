# Round 20 — real pinned TokTier native CPU engine

## Decision

**The native CPU engine is feasible here and was actually built and tested.** Preserve the existing S01 bounded CPU-investigation identity. The previous missing-Cargo/native-engine blocker is removed. Production integration, certified artifact admission, native session repair and serving-value qualification remain deferred. This is neither a new hypothesis nor an inference performance result.

The exact pinned source compiled on this Darwin arm64 host without modifying the original checkout, installing GPU extras, probing a device, loading a model, starting a server, constructing a facade/session store, or editing the certification registry.

## Pinned build and entry point

- Donor: `asu-idi/toktier@0591fe18235f3e64f0576fa7f77a0804af1ba5c2`, package 0.3.0.
- Target tokenizer: DeepSeek-V4.1-Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, tokenizer JSON SHA `c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b`.
- Official PyPI 0.3.0 exposed only a Linux x86_64 wheel. Its receipt is retained; that wheel was **not** used or substituted.
- A `git archive` of the pinned commit was extracted to a separate build directory. Rust 1.93.1 was installed under this round's isolated `cargo-home`/`rustup-home`. The initializer was checked against its official adjacent SHA256 response. Shell profiles were not changed.
- `maturin==1.14.1`, release build, `--locked`, Python 3.12.15; unchanged Cargo.lock pins Rust `tokenizers=0.22.2`, `icu_properties=2.0.2`, `pyo3=0.23.5`.
- Initial generic `python3` created a Python 3.9 environment; package tests instead use the explicitly created `venv312`. The 3.9 environment supplied the architecture-compatible maturin build executable only. All native test execution used Python 3.12.15.
- The CPU core has ARM/Apple implementations. Its dependency graph includes a CUDA *host shim*, whose source dynamically opens the driver only on explicit GPU construction. Compiling it does not compile device code; module registration does not construct a GPU object. Only CPU methods were called.
- Actual binary: `toktier._native.CallbackEncoder.native_fast_cpu(...)`, engine `0.10.0+toktier.pinned.1`, compiled source digest `9594ff243421b89ff95137bda5a439a314343470951b6b7c0a98238bf51c4f41`.
- Local wheel: `wheels/toktier-0.3.0-cp310-abi3-macosx_11_0_arm64.whl`, 5,025,428 bytes, SHA `bea405b6c7897953baa5673f6e749bf5baa521dd1833661d5ca0b386ced7bb12`.

The direct private CPU constructor receives the exact target bytes and explicitly experimental copied anchor repair parameters. This is an isolated compatibility experiment, **not admission through the public registry**. The unchanged public `_repair_callback` gate still declines the target as `artifact_not_in_certified_repair_roster`.

Source URLs, exact retained source hashes, binary hash, compiler facts and build command are in `source-manifest.json` and `build-and-test-receipt.json`. The original checkout is still clean.

## What actually executed

The round18 test cases were reused in a new script. Unmodified pinned **Python `GigatokenRepair`** performs splice selection and offset reconstruction. Its suffix encoder and vocabulary now come from the **actual compiled native CPU engine**, replacing the previous HF suffix proxy. The target HF Python wheel `tokenizers==0.22.2` remains the comparison oracle. Native encodes can intentionally fall back to their embedded reference; every route is counted.

| Check | Executed result | Exact scope |
|---|---:|---|
| Repair output token IDs | 2,818 / 2,818 equal | Finite inherited case set |
| Repair output character offsets | 2,818 / 2,818 equal | Same cases, exact HF offset comparison |
| Actual Python splice paths | 2,813 | Not native Rust session-append paths |
| Direct full native output IDs | 2,710 / 2,710 equal | Main cases, separate from repair windows |
| Embedded native reference output IDs | 2,710 / 2,710 equal | Wiring check against external HF, not a different tokenization algorithm |
| Native suffix attempts using Gigatoken | 1,809 | Actual corrected CPU core used |
| Native suffix attempts using added-token HF guard | 1,614 | Explicit fallback, not Gigatoken parity evidence |
| Direct full encodes using Gigatoken / added-token fallback | 1,194 / 1,516 | Separate denominator: 2,710 full encodes |
| Native engine-error/closure fallback | 0 | No `hf_full_engine_guard` observed |
| Accelerator Python modules loaded | 0 | Import blocker plus retained module check |

There are **3,423 suffix calls**, more than repair cases, because the donor repair widens/retries windows. Aggregate native routes are 3,003 Gigatoken and 3,130 added-token reference calls: these equal the suffix calls plus separate full-encode checks. Native `window_calls=0` is expected because the **Python repair** invokes the native full-encode surface on each window; the native Rust append/repair function is not being exercised.

Coverage inherited unchanged: 300 split positions over the 18 old/new changed added-token literals; 1,124 Unicode/whitespace/digit/contraction/repeated-character cases; midpoint splits of all 1,283 target added literals; three fallback/no-op/invalid-prior cases; one 100-step append trajectory; eight exact renderer transitions, of which two rewrite prior rendered text and deliberately use full-reference fallback. Many cases share the same synthetic prefix. These are not 2,818 independent serving traces.

## Interpretation and remaining gates

1. **Meaningful improvement over round18:** compiled corrected Gigatoken actually encoded 1,809 suffix windows. Its native vocabulary was used for repair byte lengths, and construction checked native/reference byte-length agreement. We no longer infer native feasibility from the HF proxy.
2. **Added-token coverage is guarded:** the native full-encode surface intentionally routes matching added-token text to HF. Therefore the changed literal successes primarily establish correct fallback integration and splice behavior, not raw Gigatoken correctness on every added literal. This may still avoid whole-prefix encoding, but no speed was measured.
3. **Same-source reference limitation:** external HF and the embedded reference both use tokenizers 0.22.2. Equality checks native integration against the intended reference; it is not an independent algorithmic proof.
4. **Artifact scope:** the raw pinned tokenizer JSON and source renderer were used. This does not prove the live deployment's loader/materialized sidecar state or template/session fingerprint is identical. No actual serving request was sent.
5. **Native session path untested:** the Rust session store, native append engine, public facade, persistence/revision lifecycle, concurrency and runtime registry dispatch were not constructed. The successful Python splice harness does not certify them.
6. **Architecture scope:** this is an ARM/macOS CPU build. It establishes local testability and finite compatibility, not the deployment Linux x86 CPU binary or release build certification.
7. **No speed claim:** there is no native throughput benchmark, end-to-end TTFT/ITL estimate, GPU result or service promotion. Existing workload exposure/session mapping must be established separately; default admission remains closed.

Next bounded investigation: materialize and compare the exact serving tokenizer/sidecar state, retain the existing registry fallback, and test the production native append/session boundary under an explicit experimental harness. That requires a separately scoped task because this run deliberately excludes the full facade/session runtime. Measure representative CPU encode/repair cost only after correctness and route accounting are settled.

## Reproduction and artifacts

From this directory after the recorded isolated build/install:

```sh
./venv312/bin/python native_probe.py
```

`native_probe.json` retains every case and per-window route, source hashes, build facts and exact gate result. `build-and-test-receipt.json` pins the local binary/wheel and full build command. Source evidence and Cargo.lock are retained independently of transient build objects. The local wheel is a binary artifact; its existence here does not imply it has been uploaded by the text-only research snapshot policy. No canonical state was changed.
