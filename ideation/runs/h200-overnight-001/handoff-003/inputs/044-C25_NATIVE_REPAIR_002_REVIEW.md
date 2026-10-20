# Independent release of infrastructure repair, native pair 002

Reviewed before launch, 2026-10-20 UTC. **Release the separately named fresh A/B allocation `native-pair-002` under the unchanged native pilot contract and the original campaign deadline.** This release covers the narrow root identity repair and bounded new allocation; it does not confer a correctness or performance verdict on the unexecuted candidate integration.

The CPU reproduction establishes the exact PermissionError from resolving the root-owned container init executable through host `/proc`. The actual revised helper was exercised in a pinned-image CPU container and passed: denied host executable access remains explicit, container-local PID1 executable/argv are retained, its start ticks equal readable host start ticks, and a second Docker inspection plus host tick read reject identity changes. The worker namespace PID/start-tick check also passes. Both CPU containers were cleaned successfully. This fixes a preflight gap that the first independent review missed; the original scientific gates were not the cause of allocation 001's stop.

I read the controller/renderer diff and independently verified every new manifest input hash. There are no changed hashes among common scientific inputs. Both complete arm specifications are byte-equivalent after normalizing only the execution ID, and the router command is unchanged. The original observer, candidate, traffic, expected-token oracle, shapes, collection order, statistic, and independent watchdog remain frozen. Existing allocation 001 and its exact source copies, raw A observations, incomplete lifecycle, cleanup errors and 2.558871 allocated GPU-hours remain retained.

The versioned controller translates the original origin `2026-10-20T22:54:00.993689+00:00` into monotonic work/watchdog deadlines. Work ends at **2026-10-21 00:19:00.993689 UTC**, with hard cleanup by **00:24:00.993689 UTC**; diagnosis and this review consume that same calendar budget. Before B, remaining work time must cover observed A startup/native time plus 300 seconds for traffic and 120 seconds reserve. That admission decision depends on cost, not A timing results. The original cumulative 12 allocated GPU-hour ceiling and two unconsumed full service attempts remain unchanged.

Pair 002 must use its own baseline A and candidate B for the prospective comparison. Retained A001 versus A002 may be reported as descriptive startup-drift evidence, with both shown; do not pool the baselines, select the faster baseline, or substitute A001 into pair002. No candidate results have been observed at this declaration. Native timing remains a controlled padded draft-proposal endpoint, not service ITL or useful accepted-token progress. Existing actual-request lifecycle and external abort-log review requirements continue; the A-to-B release may distinguish a permitted scoped native comparison from incomplete service integration exactly as already declared.

## Bound inputs and evidence

- Launch `native-root/launch-native-pair-002.json`: `7ef8204e6f441adc75be9d2ca672654416568203733a2a1720bb1d3fe28c786e`.
- Controller `native-root/controller_v2.py`: `e456e48cffe04ed07858e805ba09c1941cf6dde2999f5cc135993993d3b8a804`.
- Renderer `native-root/render_v2.py`: `ca5d5827fc809811b8f5119797db57e217aa27cad51ffc47062b42221dd8751e`.
- Unchanged watchdog: `8783bf8580e25f269b7d699cd6cc52e9132cdaa5a5e1098080c8451cf4683583`.
- Exact-error CPU reproduction: `5f5d8b477789a87f5878a920e765764356adc86677f75b7514a8b23c675835ee`.
- Actual-helper CPU preflight: `14a748962d48dfd3d75059eafb8fd6f7415fe46f168bf091afee0504e9cbbb8f`.

The controller, renderer and watchdog parsed successfully during independent read-only review. Launch remains the root runner's responsibility. No edits to frozen inputs are permitted during allocation.
