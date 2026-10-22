import argparse
import fcntl
import json
import sys
import urllib.error
from pathlib import Path

from .store import Store

def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def main():
    p = argparse.ArgumentParser(description="Inference corpus and research workbench")
    p.add_argument("--db", default="data/corpus.sqlite")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("tools", help="Describe the three independent agent tool namespaces")
    tool = sub.add_parser("tool", help="Call one tool; JSON arguments inline or from @file.json")
    tool.add_argument("name")
    tool.add_argument("--args", default="{}")
    s = sub.add_parser("sync")
    s.add_argument("--repo", default="vllm-project/vllm")
    s.add_argument("--feeds", nargs="+", default=["issues", "pulls", "comments", "review_comments"], choices=["issues", "pulls", "comments", "review_comments"])
    s.add_argument("--max-pages", type=int, default=100)
    s.add_argument("--recent-days", type=int, help="Separate recent-change cursor; full archive progress is preserved")
    h = sub.add_parser("hydrate")
    h.add_argument("numbers", nargs="+", type=int)
    h.add_argument("--repo", default="vllm-project/vllm")
    q = sub.add_parser("search")
    q.add_argument("query", nargs="?", default="")
    q.add_argument("--after")
    q.add_argument("--before")
    q.add_argument("--date-field", default="updated_at", choices=["created_at", "updated_at", "merged_at", "fetched_at"])
    q.add_argument("--kind", help="Stored source kind, e.g. pr, issue, paper, report or code; GitHub pull requests use pr, not pull_request")
    q.add_argument("--state")
    q.add_argument("--tag", action="append", dest="tags")
    q.add_argument("--match", choices=["all", "any"], default="any")
    q.add_argument("--sort", choices=["relevance", "newest"], default="relevance")
    q.add_argument("--limit", type=int, default=20)
    sub.add_parser("status")
    g = sub.add_parser("graph")
    g.add_argument("node")
    d = sub.add_parser("show")
    d.add_argument("id")
    a = sub.add_parser("papers")
    a.add_argument("query")
    a.add_argument("--limit", type=int, default=8)
    a.add_argument("--provider", choices=["arxiv", "hf", "both"], default="both")
    fetch = sub.add_parser("fetch")
    fetch.add_argument("url")
    expand = sub.add_parser("expand")
    expand.add_argument("id")
    expand.add_argument("--limit", type=int, default=5)
    cites = sub.add_parser("citations")
    cites.add_argument("id")
    cites.add_argument("--limit", type=int, default=5)
    code = sub.add_parser("code")
    code.add_argument("repo")
    code.add_argument("ref")
    code.add_argument("path")
    pack = sub.add_parser("pack")
    pack.add_argument("brief")
    pack.add_argument("--output", default="runs/latest")
    research = sub.add_parser("research")
    research.add_argument("brief")
    research.add_argument("--output", required=True)
    research.add_argument("--model")
    research.add_argument("--timeout", type=int, default=600)
    research.add_argument("--rounds", type=int, default=2)
    research.add_argument("--backend", choices=["codex", "gpt-researcher"], default="codex")
    validate = sub.add_parser("validate")
    validate.add_argument("report")
    ui = sub.add_parser("serve")
    ui.add_argument("--host", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=8765)
    args = vars(p.parse_args())
    command, db = args.pop("command"), args.pop("db")
    store = Store(db)
    try:
        if command in ("tools", "tool"):
            from .toolbox import registry
            registry = registry(store)
            if command == "tools":
                emit(registry.describe())
            else:
                raw = args["args"]
                parameters = json.loads(Path(raw[1:]).read_text() if raw.startswith("@") else raw)
                if not isinstance(parameters, dict):
                    raise ValueError("Tool arguments must be a JSON object")
                emit(registry.call(args["name"], **parameters))
        elif command in ("sync", "hydrate"):
            from .github import GitHub
            lock_path = Path(db).with_suffix(".sync.lock")
            with lock_path.open("w") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise RuntimeError("Another GitHub ingestion is running; try after it finishes")
                gh = GitHub(store, args.pop("repo"))
                getattr(gh, command)(**args)
        elif command == "search":
            emit(store.search(**args))
        elif command == "show":
            emit(store.get(args["id"]))
        elif command == "status":
            emit(store.stats())
        elif command == "graph":
            emit(store.graph(args["node"]))
        elif command in ("papers", "fetch", "expand", "citations", "code"):
            from .sources import Sources
            emit(getattr(Sources(store), command)(**args))
        elif command in ("pack", "research", "validate"):
            from . import research
            emit(getattr(research, command)(store, **args))
        elif command == "serve":
            from .ui import serve
            serve(db, **args)
    except (RuntimeError, ValueError, urllib.error.URLError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    finally:
        store.db.close()
