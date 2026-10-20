"""Describe retained baseline draft submission shapes; no timing inference."""
from collections import Counter
import hashlib
import json
from pathlib import Path

run = Path(__file__).resolve().parent
source = run.parent / "c03-execution-001" / "A-exposure-final-snapshots"
out = run / "native-shape-context.json"
if out.exists():
    raise SystemExit("Refuse to overwrite existing receipt")
result = {"scope": "Historical baseline diagnostic warmup plus profiling, online submissions only; not service timings or current traffic frequencies", "counting_unit": "one replica DP step, rank 0 once; all four common-event digests checked as coherence witnesses", "replicas": [], "sources": []}
total = Counter()
for replica in range(2):
    snapshots = []
    for rank in range(4):
        path = source / f"replica-{replica}-rank-{rank}.json"
        data = path.read_bytes()
        result["sources"].append({"path": str(path), "sha256": hashlib.sha256(data).hexdigest()})
        snapshots.append(json.loads(data))
    if len({s['common_event_sha256'] for s in snapshots}) != 1:
        raise RuntimeError("Cross-rank event digest disagreement")
    counter = Counter()
    for row in snapshots[0]["histogram"]:
        event = row["event"]
        if event["online"]:
            counter[(event["draft"]["mode"], event["draft"]["requests"], event["draft"]["tokens"])]+=row["count"]
    if sum(counter.values()) != snapshots[0]['counts']['online']:
        raise RuntimeError("Histogram count disagrees with online total")
    result["replicas"].append({"replica": replica, "online_events": sum(counter.values()), "common_event_sha256": snapshots[0]['common_event_sha256']})
    total.update(counter)
result["online_events"] = sum(total.values())
result["submitted_draft_shapes"] = [{"mode": k[0], "requests": k[1], "tokens": k[2], "events": v, "fraction_all_online": v / result["online_events"]} for k, v in sorted(total.items())]
result["limits"] = ["Descriptor submission is not device completion or time", "Historical workload frequencies may shift with a candidate", "Ranks are not independent samples", "Counts include dummy cooperation and both warmup/profiling phases"]
out.write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({"online_events": result["online_events"], "shape_count": len(total), "top": sorted(result["submitted_draft_shapes"], key=lambda x:x['events'], reverse=True)[:12]}, indent=2))
