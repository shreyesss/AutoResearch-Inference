# Persistence state at this Git checkpoint

- Eleven frozen typed proposals, their screening/decisions and two review-ready CPU plans were created successfully in an isolated local state. IDs are in `persistent-ids.json`.
- Five executed CPU checks are queued for canonical lifecycle recording with explicit narrow scopes. A further tile-constraint check is retained in the report and source appendix. No broad hypothesis is experimentally validated.
- Canonical single-writer import is queued behind the active downloader/publication lock. Its script retains exact sources, all decisions, CPU artifacts and command journal; no second concurrent writer was started.
- This Git checkpoint does not claim the new batch is backed up to S3. A later canonical-import and publication receipt is required. The previous Engram batch's S3 publication was separately verified successful.
- Full local batch: `~/.local/share/autoresearch-reviews/guided-discovery-20261022-001/`.
- Intended canonical batch: `~/.local/share/inference-autoresearch/research/records/guided-discovery-20261022-001/`.
- Active next-round research remains under the external batch's `round2-runtime/`, `moe/round2/` and `review/round2/`. It is not included in the eleven-intervention denominator.
