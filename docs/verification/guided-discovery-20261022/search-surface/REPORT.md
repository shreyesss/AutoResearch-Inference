# Search surface clarification from observed mistakes

Round55 initially passed kind=pull_request and received zero retained sources; the corrected stored kind=pr returned sources. It also used a compound phrase for compact hypothesis recall, which matches literal phrases rather than semantic OR or the separate FTS term-match interface. Neither empty result established scientific absence.

Changed CLI help in both entry points, MCP search_local description and the discovery skill to expose these semantics at use. Prefer pr-search when PR-only intent is known. No argument rewriting, ranking, aliases, schema or source mutation behavior changed. The tool still permits arbitrary stored kinds; the instruction repair does not mechanically prevent a caller from using the wrong kind.

Full research gate361tests+29subtests, bootstrap dry-run, rendered CLI help and skill validation passed. No new low-value mirrored test was added for help strings. Independent source review is requested. This improves availability of correct usage information; future operator-error reduction has not been measured. It is not evidence of better hypotheses or higher retrieval recall by itself.
