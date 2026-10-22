# Reuse existing pinned-code evidence before registering a new alias

Root review stopped the isolated CF59 refinement v2 from canonical application. Its new round-specific source identity referred to exactly the same109,354-character pinned model-runner body already retained under the reader's stable code identity. Canonical readback also found a historical guided-source alias with identical body bytes. The evidence was valid; the additional identity was unnecessary and would split recall and inflate distinct-source counts.

The agent is rebuilding the refinement against the existing exact source/revision. A previously absent callback file should first be checked by standard code identity, then registered with that stable identity and explicit local provenance if absent. Existing historical aliases and claims are preserved. No fuzzy merging or rewriting of old evidence occurs.

Added a short PR-research skill instruction describing the actual reader identity `code:OWNER/REPO:FULL_COMMIT:path`, exact show/import reuse and preservation of historical aliases. Skill validator passed. This uses existing tools; no new automatic deduplication capability, quality gain or corpus-wide cleanup is claimed. The v2 isolated packet remains as review history, not successful canonical ingestion. The previously reviewed58/59/60 application is a separate authorized package and is unaffected.

This body-hash check only covers the one inspected source. A record revision fingerprints metadata as well as body: two revisions with identical code text can still differ in source metadata. Reuse the recorded revision rather than inventing a claim hash from raw file bytes.
