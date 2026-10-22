# Initialization guidance correction

Observed in round112 and round113: the agent reused `--defer-snapshot` for `init`; initialization rejected it.113 then attempted dependent expansion/search before successful initialization. These were operator errors before provider access, not failed literature searches. Existing runtime error messages already state the remedy.

The discovery skill now shows separate initialization and batch invocations, explicitly checks initialization exit status, and retains restore-before-init semantics for existing state recovery. It does not change tool behavior, introduce automatic refresh or loosen persistence rules.

Verification: actual offline initialization of a fresh isolated state succeeded with zero network calls and an unpublished local snapshot; a subsequent deferred `expand` completed. The paper-search example's argument syntax was checked against the actual parser; no provider request was made for this documentation check. Skill validator passed using the existing isolated PyYAML dependency at `/tmp/autoresearch-skill-validator-deps`; initial repo/system Python attempts lacked PyYAML and failed before validation. No production dependency was added. `git diff --check` passed. No research Python code changed, so the previously passed full research suite was not rerun for this small instruction edit.

This is a narrow usability correction grounded in repeated errors. No independent behavioral study, retrieval-quality gain or hypothesis-yield uplift is claimed.
