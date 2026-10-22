# Match decision rules to the actual experiment arms

The frozen CR64 report proposes two variants, compressed-cache NORMAL and LAST, against current FIRST. Its final section nevertheless lists NORMAL winning as a rejection. That is a consequential ambiguity: NORMAL beating FIRST supports the family-level hypothesis even when LAST is inferior. A preference between NORMAL and LAST alone does not prove either improves FIRST.

Root requested an additive author correction, preserving the original packet. The critic skill now explicitly checks arm-specific and family-level support/null/rejection against the actual baseline, objective and guards, including ties and inconclusive uncertainty. This is a small reasoning instruction based on an observed field error. It is not a semantic validator, automatic adjudicator or measured improvement in research quality.

Skill validation passed using the existing skill-creator validator and its already available YAML dependency path. No runtime code or serving experiment changed. Independent review is separate; no code test result is invented for this documentation-only change.
