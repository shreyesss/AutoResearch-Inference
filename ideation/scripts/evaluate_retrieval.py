"""Small known-item regression set; not a general relevance benchmark."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ideation.store import Store

p = argparse.ArgumentParser()
p.add_argument("--db", default="data/corpus.sqlite")
args = p.parse_args()
s = Store(args.db)
cases = [
    (36037, '"speculative speculative decoding"', {"kind": "issue"}),
    (62541, 'deepseek-v4.1-flash b200', {"kind": "pr", "match": "all", "after": "2026-10-01"}),
    (62073, '"CuTeDSL" "NVFP4" "MegaMoE"', {"kind": "pr", "match": "all", "after": "2026-10-01"}),
]
results = []
for number, query, filters in cases:
    id = f"github:vllm-project/vllm:{number}"
    rows = s.search(query, limit=20, **filters)
    rank = next((i+1 for i, r in enumerate(rows) if r["id"] == id), None)
    doc = s.get(id)
    results.append({"number": number, "query": query, "filters": filters, "rank": rank, "found": rank is not None, "state": doc["state"] if doc else None, "base": doc["metadata"].get("base") if doc else None})
output = {"cases": results, "recall_at_20": sum(r["found"] for r in results) / len(results), "mrr_at_20": sum(1/r["rank"] if r["rank"] else 0 for r in results) / len(results), "limitation": "Three supplied seed examples only; no general recall/precision claim."}
print(json.dumps(output, indent=2))
sys.exit(0 if all(r["found"] for r in results) else 1)
