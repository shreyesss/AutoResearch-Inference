"""Execute an editable plan. Default is local GitHub search; external calls are explicit."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode

from ideation.evidence import new_output, write_json
from ideation.store import Store, now
from ideation.toolbox import registry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--db", default="data/corpus.sqlite")
    parser.add_argument("--papers", action="store_true")
    parser.add_argument("--web", action="store_true")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    out, store = new_output(args.output), Store(args.db)
    tools = registry(store)
    results = {"at": now(), "github": [], "papers": [], "web": [], "errors": []}
    rows = ["# Manual inspection", "", "Local lexical ranking; dates are filters, not a scored recency bonus. BM25: lower is better. Top ten per query, not exhaustive.", ""]
    for repo in plan.get("repos", ["vllm-project/vllm"])[:5]:
        for query in plan["github_queries"][:8]:
            filters = {"query": query["query"], "match": query["match"], "after": plan.get("after"), "date_field": plan.get("date_field", "updated_at"), "limit": 10}
            hits = tools.call("github.search", repo=repo, **filters)
            results["github"].append({"repo": repo, "filters": filters, "purpose": query["purpose"], "hits": hits})
            link = "http://localhost:8765/?" + urlencode({"q": query["query"], "match": query["match"], "after": plan.get("after") or ""})
            rows += ["## " + query["query"], "", query["purpose"], "", "[Inspect interactively](" + link + ")", "",
                     "| Source | State | Updated | BM25 |", "|---|---|---|---|"]
            for hit in hits:
                rows.append(f"| [{hit['title'].replace('|', '/').replace(chr(10), ' ')}]({hit['url']}) | {hit['state']} | {hit['updated_at']} | {hit['rank']:.4f} |")
            rows += [""]
    for enabled, field, tool in [(args.papers, "paper_queries", "research.search"), (args.web, "web_queries", "research.web_search")]:
        if enabled:
            for query in plan.get(field, [])[:4 if args.papers and field == "paper_queries" else 2]:
                try:
                    response = tools.call(tool, query=query, limit=3)
                    results["papers" if field == "paper_queries" else "web"].append({"query": query, "result": response})
                except Exception as error:
                    results["errors"].append({"query": query, "type": type(error).__name__})
    write_json(out / "results.json", results)
    write_json(out / "cache-status.json", tools.call("research.cache_status"))
    (out / "inspection.md").write_text("\n".join(rows))
    print(json.dumps({"output": str(out), "queries": len(results["github"]), "errors": results["errors"]}))
    store.db.close()


if __name__ == "__main__":
    main()
