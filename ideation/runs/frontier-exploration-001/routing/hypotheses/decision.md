# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 2.

## B200-R7b-RANK-ROUTE-1

For the two TP1/DP4/EP4 engines, first inspect the effective image, router policy, API2 request path, and internal DP rank selection to establish whether rank-aware prefix routing is already active. If absent, test a bounded policy that prefers a rank holding an exact reusable prefix only while its estimated queue load stays within a chosen skew limit; otherwise it falls back to load-only routing. API2 must preserve or convey the rank choice through the internal DP4 decision, since replica affinity alone cannot guarantee a local cache hit. The 75% cacheability figure is a target, not an observed hit rate. Shadow routing should first determine whether avoidable rank-local misses exist. Predict better goodput only where saved prefill work outweighs skew and routing cost.

**Decision:** deferred

**Reasons:** required_improvement: The proposal gives a cheap inspection gate and a testable route to value. Its delta from the running baseline remains unknown because the effective router policy and rank targeting have not been inspected. The PR author describes a path that is “Disabled by default,” but that does not establish this deployment’s state.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Bounded rank-aware prefix routing, with all engine and scheduler settings fixed.

**Reject if:** Eligible exact-prefix hits are negligible, or load skew and queue delay erase the gain, or either strong control has better frozen SLO goodput.

## B200-R7b-PREFILL-ADMIT-1

First inspect the effective scheduler commit and runtime settings to establish whether adaptive prefill admission already exists. If absent, test a scheduler-local prefill budget that decreases when active decodes approach their measured iteration deadlines and increases when decode pressure eases. Keep the global token budget fixed; bound each prefill request’s waiting time so decode protection cannot starve TTFT. This transfers the pressure-dependent budget mechanism described by P-PAS, while adding an explicit deadline and waiting bound for the R7b objective. The source reports results on other model and GPU configurations, so neither a B200 crossover nor an effect size is known. A cheap trace analysis should first test whether prefill-bearing iterations coincide with decode deadline misses before any GPU replay.

**Decision:** deferred

**Reasons:** required_improvement: The scheduler inspection gate and trace question give a credible testable path. Whether an adaptive admission policy is absent, or prefill interferes with decode on this deployment, remains unknown. The supplied E2E results do not settle either question.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Deadline-aware adaptive prefill admission with a predeclared maximum wait bound; routing and other factors held fixed.

**Reject if:** The cheap trace check finds no association between prefill admission and deadline misses, or the strongest static control matches or exceeds goodput, or TTFT and waiting bounds fail.
