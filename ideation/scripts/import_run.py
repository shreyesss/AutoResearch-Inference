"""Import run evidence and verified claim edges without overwriting newer GitHub records."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ideation.store import Store
from ideation.research import validate

p = argparse.ArgumentParser()
p.add_argument("run")
p.add_argument("--db", default="data/corpus.sqlite")
args = p.parse_args()
run = Path(args.run)
s = Store(args.db)
count = 0
for d in json.loads((run / "sources.json").read_text()):
    existing = s.get(d["id"])
    if not existing or (d["source"] != "github" and d["fetched_at"] > existing["fetched_at"]):
        s.put(d)
        count += 1
s.db.commit()
report = json.loads((run / "hypotheses.json").read_text())
check = validate(s, report)
if check["valid"]:
    for h in report["hypotheses"]:
        for e in h["evidence"]:
            s.edge("hypothesis:" + run.name + ":" + h["id"], e["relation"], e["source_id"], e["source_id"], {"quote": e["quote"], "claim": e["claim"], "status": "agent interpretation; quote verified", "run": str(run)})
    s.db.commit()
print(json.dumps({"imported": count, "validation": check}, indent=2))
sys.exit(0 if check["valid"] else 1)
