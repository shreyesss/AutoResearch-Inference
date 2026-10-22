# CR64 code-generation boundary — append-only clarification

The original 49-file author packet remains unchanged, manifest SHA `6af0ad245160fcdaa28899ef3d4fefa7660a9285102ef3370a9cefb3c1ac32d7`.

Root's source review highlighted two concrete comments in the already retained FlashMLA `core_attn/kernel.cuh` around 320–338:

- A conditional tensor-map pointer used as a gather-assembly operand caused a `cicc` CUDA 13.1 crash; the current code instead passes byte offsets into the kernel parameter object.
- The h128 per-block path is described as near instruction-cache capacity. The helper deliberately issues an eight-gather code burst repeatedly with `CUTE_NO_UNROLL`, rather than replicating all gathers.

The proposed cache hint is a 64-bit integer operand, not a tensor-map pointer, so the existing pointer compiler failure is **not proof that the proposed hint select fails**. It is concrete reason to require a future build/code-generation check. Do not change the existing pointer-offset construction, unroll the burst, or blindly duplicate complete kernel instantiations to obtain a role-specific hint.

Before any future GPU timing, inspect successful compilation with the exact intended toolchain, emitted policy operands, branch/select placement, registers, instruction footprint and generated variants. Preserve original/all-extra/mixed role correctness and the two-CTA scale path. Build-only checks were not executed here; no CUDA compiler/native execution is authorized in this task.

This adds an implementation risk and a concrete pre-timing check. It changes neither candidate identity nor the source-grounded reason to test compressed-only NORMAL/LAST. Hints influence replacement priority; they do not pin lines.
