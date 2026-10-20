"""Live CPU verification; no model calls or paid search requests."""
import json
from pathlib import Path

from ideation.fathom import FathomTools
from ideation.store import Store, now


def main():
    store = Store("data/corpus.sqlite")
    fathom = FathomTools(store)
    reads = []
    for mode in ("html", "browser", "auto"):
        result = fathom.read("https://docs.sglang.ai/", mode=mode)
        doc = store.get(result["id"])
        assert "sglang" in doc["body"].lower() and result["characters"] > 200
        reads.append({"mode": mode, **result, "source": doc["url"], "prefix": doc["body"][:100]})
    missing = {}
    if not fathom.status()["web_search_key_present"]:
        try:
            fathom.search("speculative decoding")
        except RuntimeError as error:
            missing["web_search"] = str(error)
        else:
            raise AssertionError("Missing Serper key must be reported")
    report = {"checked_at": now(), "status": fathom.status(), "reads": reads, "unavailable": missing}
    Path("docs/fathom-live-check.json").write_text(json.dumps(report, indent=2))
    Path("docs/corpus-status-latest.json").write_text(json.dumps({"checked_at": now(), **store.stats()}, indent=2))
    print(json.dumps(report, indent=2))
    store.db.close()


if __name__ == "__main__":
    main()
