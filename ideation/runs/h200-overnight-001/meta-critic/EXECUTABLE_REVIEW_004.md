# Meta-critic executable review before native allocation

Read the root controller, watchdog and renderer; the native capture observer,
oracle/restoration path and controlled traffic driver; and the analysis reader.
This is static feasibility and protocol review while the builder/designer finish
tests and freeze hashes. It is not GPU execution or a runtime pass.

The executable follows the intended limited claim. Source mounts are isolated;
root checks the frozen inputs and idle node; each observer's eight-minute timer
starts at that observer's own native work rather than at another rank's startup;
the shared allocation stops work at 85 minutes and reserves cleanup through
90 minutes. Native timing requires actual captured sampler-step and FULL-graph
witnesses, valid prepared state, exact finite cache/token reference agreement,
and state restoration. The fixed twenty real requests have independently
specified outputs, routed identities, cancellation, recovery and EOS checks.
Pending external abort acceptance or natural-stop observation remains distinct
from observed correctness failure and may permit the scoped B native arm under
the prospective contract. It does not permit a service-readiness claim.

Three actionable issues were identified or corroborated before launch:

1. **Owned-process cleanup:** the first watchdog only removed containers if its
   controller disappeared or reached the hard deadline. It could leave the
   router or traffic process alive. Root repaired this by starting those
   processes in separate groups and atomically registering PID, start ticks,
   group identity and role. The revised watchdog validates the exact owned
   process identity before terminating its group, both after parent loss and
   at deadline cleanup. I read the revised implementation. No broad process
   kill or unrelated-node cleanup was introduced.
2. **Capture cleanup:** an earlier observer draft assigned
   `_CAPTURE_ENABLED=False` locally within `run_native`, leaving the module
   flag enabled. The builder confirmed its current revision declares the
   global and clears the registry, and is adding a direct cleanup control.
   Freeze that corrected revision rather than the earlier draft.
3. **Reader identity:** requiring merely nonempty run IDs/UUIDs does not reject
   mixed-run evidence or an A/B device mismatch. Recommend explicit common
   run ID, the same UUID for each replica/rank across arms and eight distinct
   devices per arm, with wrong-run/device controls. The evaluator independently
   requested the same tightening; it remains part of the final builder freeze.

No additional research gate is recommended. Keep the known padded-native scope
prominent and retain all timing cells. Forward-control drift is useful evidence
of launch confounding; an absolute microsecond comparison across differently
sized stages is not automatically a causal veto or a quantity to subtract from
the treatment. Review absolute and percentage drift together with telemetry.

After the final independent source/test/hash acceptance, proceed to the bounded
allocation. Unexpected infrastructure or instrumentation failures should be
preserved and diagnosed rather than counted as failed optimization evidence.
An actual token/cache/ownership failure still stops the affected implementation.
