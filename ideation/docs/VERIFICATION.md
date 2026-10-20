# Prototype verification

19 October 2026 UTC / 20 October IST. Built within the requested 30-minute prototype window.

- Nine unit tests pass on the workstation. They cover aliases and intersected filters, date semantics, literal FTS queries, reindexing, graph provenance, interrupted cursors, opaque large-collection cursors, PR branch/merge preservation, fabricated citation rejection, arXiv Boolean construction, and graph traversal through a paper identity without a metadata document. Some tests exercise multiple behaviors.
- The three user-supplied GitHub examples all rank first in the small known-item regression set. See `retrieval-evaluation.json` and `retrieval-evaluation-remote.json`; this is not a general search-quality benchmark.
- UI home, search API, status API, graph API and research-runs pages returned HTTP 200 through the workstation's SSH tunnel.
- The VM UI service and hourly refresh timer are enabled. Login lingering is enabled. The archive collector is active; corpus completeness is deliberately not claimed.
- A real GitHub HTTP 422 at page 100 exposed the large-dataset pagination constraint. The collector now follows opaque continuation links, including repository-ID URLs and cursor parameters; the interrupted backfill resumed.
- Both live research runs completed. The first caught and repaired two inaccurate code quotations. The second executed the agent runner directly on the VM and preserved evidence-depth warnings rather than marking provisional ideas ready for implementation.
- arXiv and HF paper APIs, arXiv HTML retrieval, exact-commit source retrieval, and selected GitHub comments/reviews/diffs were exercised live.
- Optional Semantic Scholar expansion returned HTTP 429 and is explicitly reported as unavailable in that attempt.
- GPT Researcher 0.16.1 was installed in the VM's isolated `.venv-web`, imported successfully, and its `deep` report type checked. The resolved environment is in `requirements-web-resolved.txt`. No API-provider research run is claimed for that optional backend.
- The historical raw source-file URL returned HTTP 404. The current experimental PR-head file downloaded; that does not resolve historical deployment inclusion.

The timestamped collection snapshot is in `DEPLOYMENT_STATUS.json`. The live `/api/status` endpoint is authoritative for ongoing progress. No serving code was patched and no GPU benchmark was launched by this prototype.
