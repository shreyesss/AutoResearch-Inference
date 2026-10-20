"""Run evidence and hypotheses on explicitly selected sources and a user-controlled brief."""
import argparse
import json
from pathlib import Path
from ideation.evidence import new_output, write_json
from ideation.store import Store, now
from ideation.toolbox import registry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--source", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--db", default="data/corpus.sqlite")
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()
    out, store = new_output(args.output), Store(args.db)
    tools = registry(store)
    manifest = {"started_at": now(), "status": "running", "question": args.question, "selected_sources": args.source}
    write_json(out / "manifest.json", manifest)
    try:
        evidence = tools.call("research.evidence", question=args.question, source_ids=args.source, output=str(out / "evidence"), timeout=300)
        print(json.dumps(evidence), flush=True)
        result = tools.call("hypothesis.run", brief=args.brief, packet=evidence["packet"], output=str(out / "hypotheses"), rounds=args.rounds, timeout=600)
        manifest.update(status=result["status"], hypotheses=result["selected"], evidence_claims=evidence["claims"])
        (out / "decision.md").write_text((out / "hypotheses/decision.md").read_text())
        print(json.dumps(result), flush=True)
    except Exception as error:
        manifest.update(status="failed", error_type=type(error).__name__)
        raise
    finally:
        manifest["finished_at"] = now()
        write_json(out / "manifest.json", manifest)
        store.db.close()


if __name__ == "__main__":
    main()
