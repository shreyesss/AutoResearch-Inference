# M01 follow-up: separate instruction extent from task overhead

The source establishes BLOCK_M divisible by16, task valid_m as remaining rows capped by BLOCK_M, and per-task MMA token extent align(valid_m,16). For a fixed expert row count n=q*BLOCK_M+r, 0<=r<BLOCK_M:

    sum_task align(valid_m,16)
      = q*BLOCK_M + align(r,16)
      = 16*ceil(n/16).

The identity is independent of BLOCK_M. It applies to the token extent of the inspected grouped tasks while expert row counts, output dimensions and K work remain fixed. N-cluster and K repetition multiply this extent without introducing a different token-padding dependence. The bound holds per fixed output-N cluster and K iteration; changing BLOCK_N, BLOCK_K, precision or the selected kernel is outside it. Shared L1/L2 use the same capped-row construction with their own shared row count, not routed expert counts. Zero rows create no task. Both routed Linear1/Linear2 use this common scheduler/descriptor path; this is not a claim about every other backend or a runtime binary that has not been attested.

Therefore M01 should not project savings by replacing ceil(n/BLOCK_M)*BLOCK_M padded matrix rows with a smaller tactic's rows. The source already shortens the effective tensor instruction extent. Remaining mechanisms are changed number of tasks, repeated weight/staging work, fixed TMA payload, scheduling/occupancy and pipeline effects. Those can favor or hurt a different BLOCK_M and require actual histograms/exposure. Even equal total instruction extents need not mean equal elapsed time.

check_extent.py verifies the integer identity over65,552 pairs after the algebraic derivation. It uses no source imports, model, native kernel or GPU. Its multiples16 range is a mathematical check, not a claim that all tested BLOCK_M values compile or fit the actual kernel. It validates no timing, correctness or serving improvement. This is a falsifier for an overly coarse arithmetic-gain claim; no formal decision or original card is overwritten.
