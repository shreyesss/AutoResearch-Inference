"""Run a small live example with explicit component boundaries; no GPU execution."""
import argparse
import json
from pathlib import Path

from ideation.evidence import new_output, write_json
from ideation.store import Store
from ideation.store import now
from ideation.toolbox import registry

p = argparse.ArgumentParser()
p.add_argument("--output", required=True)
p.add_argument("--db", default="data/corpus.sqlite")
a = p.parse_args()
out = new_output(a.output)
store = Store(a.db)
tools = registry(store)
discovery = {}
manifest = {"started_at": now(), "status": "running", "components": ["github", "research", "hypothesis"]}
write_json(out / "manifest.json", manifest)
try:
    discovery["github"] = tools.call("github.search", query="speculative asynchronous", limit=4)
    discovery["literature"] = tools.call("research.search", query="asynchronous speculative decoding", limit=3)
    discovery["fulltext"] = tools.call("research.read", url="https://arxiv.org/abs/2603.03251")
    write_json(out / "discovery.json", discovery)
    source_ids = ["github:vllm-project/vllm:36037", "github:vllm-project/vllm:62541", "github:vllm-project/vllm:62073", discovery["fulltext"]["id"]]
    source_ids += [d["id"] for d in discovery["github"][:2]]
    source_ids += discovery["literature"]["ids"][:2]
    result = tools.call("research.evidence",
                        question="Which evidence supports or challenges transferring asynchronous speculation to DeepSeek-V4.1-Flash on B200? Extract the mechanism, resource costs, correctness constraints, and applicability gaps. No measured vLLM bottleneck is assumed.",
                        source_ids=list(dict.fromkeys(source_ids)), output=str(out / "evidence"), timeout=300)
    print(json.dumps(result), flush=True)
    brief = json.loads(Path("config/b200.json").read_text())
    brief.update(count=2, focus="Asynchronous speculative decoding and bounded control of wasted speculation")
    write_json(out / "brief.json", brief)
    result = tools.call("hypothesis.run", brief=str(out / "brief.json"), packet=result["packet"],
                        output=str(out / "hypotheses"), rounds=1, timeout=600)
    manifest.update(status=result["status"], hypotheses=result["selected"],
                    evidence_claims=len(json.loads((out / "evidence" / "packet.json").read_text())["claims"]))
    (out / "decision.md").write_text((out / "hypotheses" / "decision.md").read_text())
    print(json.dumps(result), flush=True)
except Exception as error:
    manifest.update(status="failed", error=str(error))
    raise
finally:
    manifest["finished_at"] = now()
    write_json(out / "manifest.json", manifest)
    store.db.close()
