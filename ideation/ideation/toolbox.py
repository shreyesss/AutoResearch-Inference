"""Three independent tool namespaces for any agent that can invoke a CLI."""
import contextlib
import fcntl
import inspect
import sys

from .evidence import ResearchTools
from .github import GitHub
from .hypotheses import HypothesisTools
from .fathom import FathomTools
from .helper import Helper
from .planning import PlanningTools
from .cache import Cache
from .continuation import ContinuationTools


def registry(store):
    try:
        from discovery_rsi.tools import Tool, ToolRegistry
    except ImportError as e:
        raise RuntimeError("Use Python >=3.10 and install requirements-research.txt in .venv-research") from e
    research, hypotheses = ResearchTools(store), HypothesisTools(store)
    continuation = ContinuationTools(hypotheses)
    fathom = FathomTools(store)
    planning, helper = PlanningTools(), Helper(store)

    def github_search(query, repo="vllm-project/vllm", **filters):
        """Local corpus search; supports after/before/date_field/kind/state/tags/match/limit."""
        return store.search(query, id_prefix="github:" + repo + ":", **filters)

    def github_get(number, repo="vllm-project/vllm"):
        """Read the stored opening body and separately stored discussion/diffs."""
        id = f"github:{repo}:{int(number)}"
        return {"document": store.get(id), "children": [store.decode(r) for r in
                store.db.execute("SELECT * FROM documents WHERE parent=? ORDER BY kind,updated_at DESC LIMIT 100", (id,))],
                "hydration": store.get_checkpoint("hydrated:" + repo + ":" + str(number)),
                "note": "Children capped at 100; hydrate fetches available details. Body presence does not imply discussion completeness."}

    def github_hydrate(numbers, repo="vllm-project/vllm"):
        """Download selected issue/PR discussions, formal reviews and file patches."""
        with store.path.with_suffix(".sync.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as e:
                raise RuntimeError("GitHub backfill holds writer lock; existing corpus is still searchable") from e
            with contextlib.redirect_stdout(sys.stderr):
                GitHub(store, repo).hydrate(numbers)
        return [github_get(number, repo) for number in numbers]

    handlers = {
        "github.search": github_search, "github.get": github_get,
        "github.hydrate": github_hydrate, "github.status": store.stats,
        "github.code": research.sources.code,
        "research.search": research.search, "research.read": research.sources.fetch,
        "research.get": store.get, "research.expand": research.sources.expand,
        "research.citations": research.citations, "research.graph": store.graph,
        "research.evidence": research.evidence, "research.paperqa": research.paperqa,
        "research.providers": research.providers,
        "research.web_read": fathom.read, "research.web_search": fathom.search,
        "research.web_query": fathom.query, "research.fathom_status": fathom.status,
        "research.cache_status": Cache(store.path.parent).status,
        "research.topics": planning.topics, "research.plan": planning.plan, "research.triage": helper.triage,
        "hypothesis.run": hypotheses.run, "hypothesis.memory": hypotheses.memory,
        "hypothesis.outcome": hypotheses.outcome,
        "hypothesis.rubric": hypotheses.rubric, "hypothesis.get": hypotheses.get,
        "hypothesis.graph": hypotheses.graph, "hypothesis.import_runs": hypotheses.import_runs,
        "hypothesis.plan_test": hypotheses.plan_test, "hypothesis.test_result": hypotheses.test_result,
        "hypothesis.start_test": hypotheses.ledger.start_test,
        "hypothesis.stats": hypotheses.ledger.stats,
        "hypothesis.recall": hypotheses.recall,
        "hypothesis.continue": continuation.prepare,
        "hypothesis.continuation_check": continuation.check,
    }
    return ToolRegistry([Tool(name, (handler.__doc__ or name).strip() + "\nArguments: " + str(inspect.signature(handler)), handler)
                         for name, handler in handlers.items()])
