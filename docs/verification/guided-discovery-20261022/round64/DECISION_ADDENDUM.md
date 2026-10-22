# CR64 arm-specific adjudication correction

The frozen report's phrase “FIRST or NORMAL wins” in the null/rejection paragraph is ambiguous and must not be used as the whole-hypothesis rejection rule. CR64 includes both NORMAL and LAST as alternatives to original FIRST.

- NORMAL beating FIRST under the frozen target objective and all guards supports role-aware policy selection. It does not support choosing LAST over NORMAL.
- LAST beating FIRST under those conditions supports the LAST arm; compare it directly with NORMAL before selecting it.
- FIRST winning, or neither alternative producing a reproducible target-objective improvement under the guards, is a null result for the proposed improvement. A tie is not forced promotion.
- Lower cache misses or faster isolated attention alone cannot promote either arm if complete-round/service performance or tail guards fail.

Original report, candidate and manifest remain unchanged. The candidate's three-arm design remains valid; this append-only note supplies the precise adjudication rule.
