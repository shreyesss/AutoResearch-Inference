# Experiment walkthroughs

These notes supplement the frozen experiment plans. They do not overwrite hypothesis cards, mark tests started, or manufacture results.

For each experiment, establish:

1. What operation is being performed, and why does serving need it?
2. Where is the unnecessary work or failure mode?
3. Which facts establish applicability to this deployment?
4. How does the proposed implementation change the work?
5. Why should it preserve required behavior, and what exceptions need testing?
6. Which observation would prove or contradict the mechanism?
7. Can existing synthetic/Mooncake evaluation establish user benefit?
8. What evidence is missing before execution or promotion?

## Progress

- [Plain-language guide to all 18 proposals and five gates](NOVICE_GUIDE.md): shared vocabulary, suspected inefficiency, first decision check, and evaluation logic.
- [E01: candidate-block selection](E01.md): code-level walkthrough and evaluation audit completed; GPU/runtime evidence still pending.
- [E02: drafter padding](E02.md): pinned-path and upstream review completed; adaptive-verification-off runtime trace pending.
- [E03: graph bucket reachability](E03.md): capture arithmetic and source review completed; resolved graph-list/runtime dispatch evidence pending.
- Next detailed walkthrough: E04, CPU DP metadata coordination.
- Remaining plans retain their original conditional status in [the experiment index](../EXPERIMENT_INDEX.md).
