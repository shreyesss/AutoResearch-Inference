# Additive independent-review corrections

The original report/readback/control remain frozen. Independent review found:

1. The21 paired manifests span15 runs on October17 and six on October18,2026 (UTC); the report's “historical October18 results” is too narrow.
2. The original runtime_image_present aggregation used is not None, counting15 empty strings as present. **None of the21 manifests supplies a nonempty selected image.** Fifteen contain an empty string and six null. corrected-availability.json supersedes that aggregation; an absent image is not runtime attestation.
3. Eighteen scores report cache-hit share. Seventeen have full reporting coverage; one public median2x run reports4003/4004 requests. The chosen public cache-heavy example has full coverage and its exact counts are unchanged. No full-coverage claim should be generalized to all runs.

The central outcome is unchanged: these endpoint summaries cannot attribute missed prompt tokens to avoidable eviction, preemption or recomputation and cannot qualify the current d464 deployment. No new measurement, source replacement or status transition occurred.
