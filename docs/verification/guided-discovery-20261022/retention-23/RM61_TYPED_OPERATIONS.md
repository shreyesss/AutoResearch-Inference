# RM61 isolated typed workflow and recovery check

## Result

- Hypothesis: `hypothesis:452d29e6fc196c7ae128f0e61598a386445f809b5da759f0c66a5075649671c8`.
- Exact existing planned baseline: `baseline:d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`.
- Status: **deferred**, no gain prediction, no implementation qualification.
- Latest immutable local snapshot: `95127d9cf3b6677aa81c59692a864932f3c94484adc01afd2df923fe1c6f9b09`.
- Snapshot restored through normal production CLI into `relocated-complete-state`;58 explicitly retained artifacts verified by hash through the production resolver.
- No canonical writes, cloud publication, GPU/native execution or source edits.

This workflow used normal `init`, `import-corpus`, `claim record`, `hypothesis propose`, `screen`, `decide`, `hypothesis retain-artifacts`, `snapshot`, `restore` and `hypothesis show` commands. Local prior memory was copied with readonly SQLite backup solely into this isolated state. Source import preserved68 documents,70 revisions and377 edges; all six exact claimed revisions were independently compared after the first relocated restore. The second snapshot only adds the explicit source-alias mapping and preserves the prior snapshot.

## Immutable input and science scope

The author packet remains unchanged: `round61-request-movement/manifest.json` SHA `34b82cb453e523aad8084231ad599fa6ad46d30922f337656feaead8ae7c08d1`. Independent review remains unchanged: `review/round61-agent/manifest.json` SHA `342e7ed8935b3e7aeec599930c380edbefe9078f21d53fb5bef424e6ca2bbeed`. Every selected input was verified before staging and again before operational freeze.

`proposal.json` adapts the reviewed candidate into the required typed schema without inventing a measured gain. `decision.json` records the effective-generated-seed/explicit-seed flag, original frontend stop/stream lifetime, optimistic DSpark boundary and shared-collective obligations. It explicitly classifies this as research-heavy integration with lower readiness than PJ01/CF59; no actual graph-bucket change or profitable imbalance was measured. The card is not rewritten after creation. Six claims limit naive shortcuts rather than alleging the complete design has failed.

The screening tool retains unknown exposure. The CPU source probes remain inconclusive for the complete candidate; no migration lifecycle or native result was created. This is a normal-tool qualification workflow, not an implementation test.

## Retry and recovery evidence

`retry-check.json` records exact-input claim/proposal/screen/decision/retention replay. Hypotheses144, claims181, research records125, claim links159 and events946 remain unchanged. The same hypothesis/baseline identity was returned, and zero new retained mappings were added. These are observed no-op counts for these exact inputs, not a general transaction guarantee.

`restore-readback.json` verifies first-snapshot relocated hypothesis projection, six exact source revisions,68/70/377 source counts and57 artifact references. A further immutable snapshot adds the alias mapping itself into the state; `complete-restore-readback.json` verifies58 references and that mapping under another relocated root. Default storage skips original `.py` files; reviewed content-addressed UTF8 copies restore their selected evidence through the existing resolver. No cloud durability is claimed.

## Preserved operational failures and bounded alias

The first retention selection was refused by the existing sensitive-filename guard: reviewed public `source-vllm__v1__engine__detokenizer.py` contains `token`, whereas the narrow existing exception covers tokenizer/tokenization. No guard was changed. A neutral reviewed UTF8 copy `public-output-decoder-source.txt` retains exactly the same bytes/digest, with explicit original-path mapping. Its provenance is the pinned public source already independently reviewed. This does not admit arbitrary token/credential files or alter historical references.

**The original detokenizer path is not promised to resolve automatically.** Consumers should use the restored explicit mapping to the verified alias. Both author/reviewer originals and original manifests remain unchanged. `source-alias-map.json` is itself preserved in the latest snapshot.

A local orchestration helper initially expected retention output fields at the top level, while the actual CLI returns a `retention` envelope. The successful retention receipt and failed wrapper point are preserved; a separate continuation reads the real envelope. No source validation was weakened, no completed command receipt was overwritten, and no scientific inference was based on that failure.

## Parent review / eventual canonical retention

Use the frozen JSON inputs and exact identity above for a separately reviewed production-tool import. These operational scripts are isolated validation scripts, not authorization to copy their prior-memory database over canonical state. Do not import an entire isolated hypothesis database. Parent must verify canonical baseline/status and use normal commands/selected evidence retention. Publishing and subsequent remote restoration are separate future steps.
