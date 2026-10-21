"""Bounded, restartable discovery. Retrieval ranks are not scientific qualification.

One writer per corpus is required (the CLI holds the state-directory lock). No
LLM, cloud writes, PDFs or deployment changes are implicit in this module.
"""
import datetime as dt
import hashlib
import json
import math
import random
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

from .github import GitHub
from .sources import Sources, arxiv_query


def _time(value=None):
    if isinstance(value, str):
        value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    value = value or dt.datetime.now(dt.timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


def _stamp(value):
    return _time(value).isoformat().replace("+00:00", "Z")


def _key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]


def load_config(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text())
    if "families" not in config:
        taxonomy = path.parent / config.get("taxonomy", "keyword-guide.json")
        config["families"] = json.loads(taxonomy.read_text())["topics"]
    validate(config)
    return config


def validate(config):
    if config.get("version") != 1:
        raise ValueError("discovery config version must be 1")
    for repo in config.get("repositories", []):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("Invalid owner/repository: " + repo)
    budgets = config["budgets"]
    for field in ("github_pages", "pages_per_repository", "paper_requests", "citation_requests", "results_per_query", "shortlist_size"):
        if not isinstance(budgets[field], int) or budgets[field] < 0:
            raise ValueError("Nonnegative integer required: " + field)
    if not 1 <= budgets["results_per_query"] <= 100 or not 1 <= budgets["shortlist_size"] <= 500:
        raise ValueError("results_per_query must be 1..100; shortlist_size 1..500")
    if not 0 <= config.get("exploration_fraction", 0.2) <= 1:
        raise ValueError("exploration_fraction must be 0..1")
    for field in ("refresh_hours", "failure_retry_minutes", "recency_days"):
        if config[field] <= 0:
            raise ValueError(field + " must be positive")
    for provider in config.get("paper_providers", []):
        if provider not in ("arxiv", "openalex", "hf"):
            raise ValueError("Unsupported paper provider: " + provider)
    if config.get("github_initial_days") is not None and config["github_initial_days"] <= 0:
        raise ValueError("github_initial_days must be null or positive")
    if config.get("citation_limit", 3) < 1:
        raise ValueError("citation_limit must be positive")
    weights = config.get("ranking_weights", {"lexical": 70, "recency": 30})
    if set(weights) != {"lexical", "recency"} or any(not isinstance(v, (int, float)) or v < 0 for v in weights.values()) or abs(sum(weights.values()) - 100) > 1e-6:
        raise ValueError("ranking_weights must have nonnegative lexical/recency weights summing to 100")
    if config.get("github_recent_lane") and (config.get("github_recent_days", 7) <= 0 or budgets["pages_per_repository"] < 2):
        raise ValueError("Recent+archive lanes require positive github_recent_days and pages_per_repository >= 2")
    return config


def _tasks(config, moment=None):
    tasks = []
    for seed in config.get("seeds", []):
        paper = seed.get("arxiv_id")
        if paper:
            if not re.fullmatch(r"\d{4}\.\d+(?:v\d+)?", paper):
                raise ValueError("Invalid seed arXiv identifier")
            tasks.append({"provider": "arxiv", "query": "id:" + paper, "lane": "seed", "seed": seed})
    for query in config.get("broad_queries", []):
        tasks.append({"provider": "arxiv", "query": query, "lane": "broad"})
    providers = config.get("paper_providers", ["arxiv"])
    epoch = int(_time(moment).timestamp() // (config["refresh_hours"] * 3600))
    for family in config.get("families", []):
        terms = family.get("terms", [])
        for provider_index, provider in enumerate(providers):
            if not terms:
                continue
            # Rotate through the complete guide, rather than always searching
            # the first few generic terms of each family.
            offset = ((epoch + provider_index) * 3) % len(terms)
            selected = (terms + terms)[offset:offset + min(3, len(terms))]
            query = " OR ".join('all:"' + term.replace('"', '') + '"' for term in selected) if provider == "arxiv" else " ".join(selected[:2])
            tasks.append({"provider": provider, "query": query, "lane": "targeted", "family": family["id"]})
    for item in config.get("queries", []):
        if item["provider"] not in ("arxiv", "openalex", "hf"):
            raise ValueError("Unsupported query provider")
        tasks.append({"lane": "user", **item})
    return list({_key(task): task for task in tasks}.values())


def plan(config, now=None):
    """Offline: enumerate tasks and limits. Does not inspect credentials or use APIs."""
    validate(config)
    return {"version": 1, "at": _stamp(_time(now)), "repositories": config.get("repositories", []),
            "github_scope": "all issue/PR opening records" if config.get("github_initial_days") is None else "opening records updated within initial window",
            "paper_tasks": _tasks(config, now), "budgets": config["budgets"],
            "recency_days": config["recency_days"], "refresh_hours": config["refresh_hours"],
            "limitations": ["A bounded run is not full corpus coverage.", "PR diffs/reviews/comments require explicit hydration.",
                            "No speedup or architecture claim is verified by discovery.",
                            "Seeds are user-supplied identities, not validated paper claims.",
                            "Budgets count logical page/search calls; provider retries can add HTTP attempts."]}


class PaperClient:
    """Existing cached Sources and ResearchTools, with paginated arXiv retrieval."""
    def __init__(self, store):
        self.store = store
        self.sources = Sources(store)
        self._research = None

    @property
    def research(self):
        if self._research is None:
            from .evidence import ResearchTools
            self._research = ResearchTools(self.store)
        return self._research

    def search(self, task, state, limit):
        provider, query = task["provider"], task["query"]
        if provider != "arxiv":
            result = self.research.search(query, provider=provider, limit=min(20, limit), after=state.get("after"), before=state.get("before"))
            result.update(next_cursor=None, exhaustive=False, coverage="bounded provider search; no exhaustive coverage asserted")
            return result
        effective = arxiv_query(query)
        if state.get("after"):
            effective = "(" + effective + ") AND submittedDate:[" + state["after"][:10].replace("-", "") + "0000 TO " + state["before"][:10].replace("-", "") + "2359]"
        start = state.get("cursor", 0)
        params = urllib.parse.urlencode({"search_query": effective, "start": start, "max_results": limit,
                                       "sortBy": "submittedDate", "sortOrder": "descending"})
        raw, _ = self.sources.request("https://export.arxiv.org/api/query?" + params, xml=True)
        root = ET.fromstring(raw)
        ns = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}
        entries = root.findall("a:entry", ns)
        ids = []
        for entry in entries:
            url = entry.findtext("a:id", "", ns).replace("http://", "https://")
            if not re.search(r"/abs/\d{4}\.\d+(?:v\d+)?$", url):
                raise ValueError("arXiv returned an error/non-paper entry")
            identifier = re.sub(r"v\d+$", "", url.rsplit("/", 1)[-1])
            doc = {"id": "arxiv:" + identifier, "source": "arxiv", "kind": "paper", "url": url,
                   "title": " ".join(entry.findtext("a:title", "", ns).split()), "body": entry.findtext("a:summary", "", ns),
                   "created_at": entry.findtext("a:published", None, ns), "updated_at": entry.findtext("a:updated", None, ns),
                   "metadata": {"read_depth": "abstract", "retrieval_query": query,
                                "arxiv_version": url.rsplit("/", 1)[-1], "claim_status": "unassessed_source",
                                "authors": [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)]}}
            self.store.put(doc)
            ids.append(doc["id"])
        total = int(root.findtext("o:totalResults", str(start + len(entries)), ns))
        next_cursor = start + len(entries) if entries and start + len(entries) < total else None
        self.store.db.commit()
        return {"ids": ids, "errors": [], "next_cursor": next_cursor, "total_results": total,
                "exhaustive": next_cursor is None, "coverage": "arXiv query pagination; live index can change during paging"}

    def citations(self, identifier, limit):
        # Non-OpenAlex citation IDs need resolution; graph edges alone are not papers.
        return self.research.citations(identifier, direction="forward", limit=limit)


def _due(state, moment, config, force):
    if force:
        return True
    if state.get("retry_after") and _time(state["retry_after"]) > moment:
        return False
    return bool(state.get("in_progress") or not state.get("completed_at") or
                moment - _time(state["completed_at"]) >= dt.timedelta(hours=config["refresh_hours"]))


def _error(error):
    # Do not persist exception messages: URLs in SDK errors can contain API keys.
    result = {"type": type(error).__name__, "message": "Provider failed; checkpoint retained. Check provider availability/credentials locally."}
    if getattr(error, "code", None):
        result["http_status"] = error.code
    return result


def _paper_key(task, config):
    # Stable family identity lets a query finish paging across refresh epochs.
    identity = {k: v for k, v in task.items() if k != "query"} if task.get("family") else task
    return "discovery:paper:" + _key([identity, config["recency_days"]])


def refresh(store, config, *, force=False, now=None, github_factory=GitHub, paper_factory=PaperClient):
    """Incrementally populate the local corpus and return an auditable JSON receipt.

    A repeated invocation inside the TTL makes no calls for completed tasks.
    Partial feeds resume on the next invocation, within independent budgets.
    Failures have a cooldown; force bypasses scheduling, not response caches.
    """
    validate(config)
    moment = _time(now)
    receipt = {"version": 1, "started_at": _stamp(moment), "config_sha256": _key(config),
               "requests": {"github_pages": 0, "paper_searches": 0, "citation_calls": 0},
               "coverage": [], "errors": [], "candidate_ids": [], "network_attempts": "See cache/provider logs; logical calls can hit cache or retry."}
    bounds = config["budgets"]
    repos = list(dict.fromkeys(config.get("repositories", [])))
    dual_lane = config.get("github_recent_lane", False) and config.get("github_initial_days") is None
    jobs = [(repo, lane) for repo in repos for lane in (("recent", "archive") if dual_lane else ("archive",))]
    cursor = store.get_checkpoint("discovery:repo_rotation", 0)
    jobs = jobs[cursor % len(jobs):] + jobs[:cursor % len(jobs)] if jobs else []
    visited = 0
    for repo, lane in jobs:
        if receipt["requests"]["github_pages"] >= bounds["github_pages"]:
            break
        visited += 1
        key = "discovery:github:" + repo + (":recent" if lane == "recent" else "")
        state = store.get_checkpoint(key, {})
        if not _due(state, moment, config, force):
            receipt["coverage"].append({"repo": repo, "lane": lane, "status": "cooldown" if state.get("retry_after") else "fresh", **state})
            continue
        if not state.get("in_progress"):
            since = state.get("watermark")
            initial_days = config.get("github_recent_days", 7) if lane == "recent" else config.get("github_initial_days")
            if not since and initial_days:
                since = _stamp(moment - dt.timedelta(days=initial_days))
            state.update(in_progress=True, pass_started=_stamp(moment), next_url=None,
                         params={"state": "all", "per_page": 100, "sort": "updated" if since else "created", "direction": "desc" if lane == "recent" else "asc"},
                         initial_scope=state.get("initial_scope", {"since": since, "all_history": since is None}), pages_in_pass=0)
            if since:
                state["params"]["since"] = since
            store.checkpoint(key, state)
        client = github_factory(store, repo)
        client.syncing = True  # refresh pagination at the collector TTL, not cache TTL
        try:
            per_lane = bounds["pages_per_repository"] // 2 if dual_lane else bounds["pages_per_repository"]
            for _ in range(min(per_lane, bounds["github_pages"] - receipt["requests"]["github_pages"])):
                receipt["requests"]["github_pages"] += 1
                items, headers = client.get(state["next_url"]) if state.get("next_url") else client.get("issues", state["params"])
                if not isinstance(items, list):
                    raise ValueError("GitHub issues endpoint did not return a list")
                link = headers.get("Link") or headers.get("link", "")
                match = re.search(r'<([^>]+)>;\s*rel="next"', link)
                next_url = match.group(1) if match else None
                if next_url and not next_url.startswith("https://api.github.com/"):
                    raise ValueError("Unexpected GitHub pagination origin")
                with store.db:
                    for item in items:
                        client.ingest(item)
                        receipt["candidate_ids"].append("github:" + repo + ":" + str(item["number"]))
                state.update(next_url=next_url, last_fetch=_stamp(moment), pages_in_pass=state["pages_in_pass"] + 1,
                             rate_remaining=headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining"))
                state.pop("retry_after", None)
                if not next_url:
                    state.update(in_progress=False, completed_at=_stamp(moment),
                                 watermark=_stamp(_time(state["pass_started"]) - dt.timedelta(days=1)))
                    state["initial_scan_complete"] = True
                store.checkpoint(key, state)
                if not state["in_progress"]:
                    break
        except Exception as error:
            state["retry_after"] = _stamp(moment + dt.timedelta(minutes=config["failure_retry_minutes"]))
            store.checkpoint(key, state)
            receipt["errors"].append({"repo": repo, "lane": lane, **_error(error)})
        finally:
            client.syncing = False
        receipt["coverage"].append({"repo": repo, "lane": lane, "status": "partial" if state["in_progress"] else "completed_pass", **state})
    if jobs:
        store.checkpoint("discovery:repo_rotation", (cursor + visited) % len(jobs))

    tasks = _tasks(config, moment)
    for identifier in store.get_checkpoint("discovery:unresolved_citations", []):
        if identifier.startswith("arxiv:") and not store.get(identifier):
            tasks.append({"provider": "arxiv", "query": "id:" + identifier.split(":", 1)[1], "lane": "citation"})
    cursor = store.get_checkpoint("discovery:paper_rotation", 0)
    tasks = tasks[cursor % len(tasks):] + tasks[:cursor % len(tasks)] if tasks else []
    # Give new explicit queries a first attempt without resetting the archive/
    # taxonomy cursor. Subsequent pages and refreshes rejoin normal rotation;
    # a persistent user query cannot monopolize every invocation.
    priority = []
    for position, task in enumerate(tasks):
        state = store.get_checkpoint(_paper_key(task, config), {})
        if task["lane"] == "user" and not state.get("last_attempt") and not state.get("last_fetch") and _due(state, moment, config, force):
            priority.append(position)
    priority = priority[:math.ceil(bounds["paper_requests"] / 2)]
    schedule = [(None, tasks[position]) for position in priority]
    schedule += [(position, task) for position, task in enumerate(tasks) if position not in priority]
    papers, visited = None, 0
    for rotation_position, task in schedule:
        if receipt["requests"]["paper_searches"] >= bounds["paper_requests"]:
            break
        if rotation_position is not None:
            visited = rotation_position + 1
        # A targeted family's query rotates only when its previous pass has
        # finished. Keep the in-flight query and cutoff stable across dates.
        key = _paper_key(task, config)
        state = store.get_checkpoint(key, {})
        if not _due(state, moment, config, force):
            continue
        if not state.get("in_progress"):
            after = None if task["lane"] in ("seed", "citation") else (moment - dt.timedelta(days=config["recency_days"])).date().isoformat()
            state = {"in_progress": True, "cursor": 0, "pass_started": _stamp(moment), "after": after,
                     "before": (moment + dt.timedelta(days=1)).date().isoformat() if after else None, "task": task}
            store.checkpoint(key, state)
        else:
            task = state.get("task", task)
        state["last_attempt"] = _stamp(moment)
        store.checkpoint(key, state)
        try:
            papers = papers or paper_factory(store)
            receipt["requests"]["paper_searches"] += 1
            result = papers.search(task, state, bounds["results_per_query"])
            if result.get("errors"):
                raise RuntimeError("Provider returned search errors")
            ids = result.get("ids", [])
            for identifier in ids:
                store.edge(identifier, "discovered_by", "query:" + _key(task), identifier,
                           {"task": task, "retrieved_at": _stamp(moment), "meaning": "retrieval provenance, not relevance verification"})
            store.db.commit()
            state.update(cursor=result.get("next_cursor"), ids=ids, last_fetch=_stamp(moment), exhaustive=result.get("exhaustive", False),
                         coverage=result.get("coverage", "bounded search"))
            state.pop("retry_after", None)
            if state["cursor"] is None:
                state.update(in_progress=False, completed_at=_stamp(moment))
            store.checkpoint(key, state)
            receipt["candidate_ids"].extend(ids)
            receipt["coverage"].append({"task": task, "status": "partial" if state["in_progress"] else "completed_search", **state})
        except Exception as error:
            state["retry_after"] = _stamp(moment + dt.timedelta(minutes=config["failure_retry_minutes"]))
            store.checkpoint(key, state)
            receipt["errors"].append({"task": task, **_error(error)})
    if tasks:
        store.checkpoint("discovery:paper_rotation", (cursor + visited) % len(tasks))

    # Forward citation discovery is one cached work lookup plus one search in
    # OpenAlex; S2 is one call. Reserve worst-case 2 logical requests per seed.
    citations = [r[0] for r in store.db.execute("SELECT id FROM documents WHERE kind='paper' AND (id LIKE 'openalex:%' OR id LIKE 'arxiv:%') ORDER BY updated_at DESC,id")]
    for identifier in citations:
        if receipt["requests"]["citation_calls"] + 2 > bounds["citation_requests"]:
            break
        key = "discovery:citations:" + identifier
        state = store.get_checkpoint(key, {})
        if not _due(state, moment, config, force):
            continue
        try:
            papers = papers or paper_factory(store)
            receipt["requests"]["citation_calls"] += 2
            result = papers.citations(identifier, config.get("citation_limit", 3))
            if result.get("error") or result.get("errors"):
                raise RuntimeError("Citation provider failure")
            ids = result.get("ids", [])
            store.checkpoint(key, {"completed_at": _stamp(moment), "ids": ids})
            unresolved = store.get_checkpoint("discovery:unresolved_citations", [])
            unresolved = list(dict.fromkeys(unresolved + [i for i in ids if not store.get(i)]))
            store.checkpoint("discovery:unresolved_citations", [i for i in unresolved if not store.get(i)])
            receipt["candidate_ids"].extend(i for i in ids if store.get(i))
            receipt["coverage"].append({"citation_seed": identifier, "discovered_ids": ids,
                                        "unresolved_ids": [i for i in ids if not store.get(i)],
                                        "status": "bounded_citation_expansion"})
        except Exception as error:
            store.checkpoint(key, {**state, "retry_after": _stamp(moment + dt.timedelta(minutes=config["failure_retry_minutes"]))})
            receipt["errors"].append({"citation_seed": identifier, **_error(error)})
    receipt["candidate_ids"] = list(dict.fromkeys(receipt["candidate_ids"]))
    receipt["shortlist"] = shortlist(store, config, now=moment)
    receipt["repository_status"] = [{"repo": repo, **store.get_checkpoint("discovery:github:" + repo, {"status": "not_started"}),
                                      "recent_lane": store.get_checkpoint("discovery:github:" + repo + ":recent", {"status": "not_started" if dual_lane else "disabled"})} for repo in config.get("repositories", [])]
    receipt["scheduled_tasks"] = {"repositories": len(config.get("repositories", [])), "paper_queries": len(tasks)}
    receipt["new_user_queries_prioritized"] = len(priority)
    receipt["shortlist_pool"] = "Newest 500 records, FTS top 25 per family, and daily seeded 100-record sample over all paper/issue/PR IDs; configurable family-match/recency weights with exploration slots. Known paper identities are deduplicated. Scores are retrieval hints only."
    receipt["ranking_weights"] = config.get("ranking_weights", {"lexical": 70, "recency": 30})
    receipt["scope"] = "Persistent local corpus retained; bounded discovery is not an exhaustive paper review. No automatic hypothesis qualification."
    receipt["completed_at"] = _stamp(_time())
    store.checkpoint("discovery:last_receipt", receipt)
    return receipt


def shortlist(store, config, *, limit=None, now=None):
    """Explainable retrieval ranking, plus deterministic keyword-independent slots.

    Recency is a preference, never a mandatory filter. Exact keyword matches
    are classification signals, not evidence of compatibility or improvement.
    """
    validate(config)
    moment = _time(now)
    limit = config["budgets"]["shortlist_size"] if limit is None else max(0, min(500, int(limit)))
    if not limit:
        return []
    # Rank a bounded pool: recent records, FTS results across every family, and
    # keyword-independent sampling over all retained IDs (including old work).
    pool = {doc["id"]: doc for doc in store.search(limit=500, sort="newest") if doc["kind"] in ("paper", "issue", "pr")}
    for family in config.get("families", []):
        query = " ".join('"' + term.replace('"', '') + '"' for term in family.get("terms", [])[:12])
        if query:
            for doc in store.search(query=query, limit=25):
                if doc["kind"] in ("paper", "issue", "pr"):
                    pool[doc["id"]] = doc
    all_ids = [r[0] for r in store.db.execute("SELECT id FROM documents WHERE kind IN ('paper','issue','pr') ORDER BY id")]
    rng = random.Random(str(config.get("exploration_seed", 0)) + moment.date().isoformat())
    for identifier in rng.sample(all_ids, min(100, len(all_ids))):
        pool[identifier] = store.get(identifier)
    patterns = [(family["id"], [(term, re.compile(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)")) for term in family.get("terms", [])]) for family in config.get("families", [])]
    scored = []
    weights = config.get("ranking_weights", {"lexical": 70, "recency": 30})
    for doc in pool.values():
        text = (doc["title"] + " " + doc["body"]).casefold()
        matches = []
        for family_id, family_patterns in patterns:
            terms = [term for term, pattern in family_patterns if pattern.search(text)]
            if terms:
                matches.append({"family": family_id, "terms": terms[:5]})
        date = doc.get("updated_at") or doc.get("created_at")
        try:
            age = max(0, (moment - _time(date)).total_seconds() / 86400) if date else None
        except (ValueError, TypeError):
            age = None
        recency = 0 if age is None else math.exp(-age / config["recency_days"])
        lexical = min(1, len(matches) / 4)
        score = weights["lexical"] * lexical + weights["recency"] * recency
        metadata = doc.get("metadata", {})
        identity = metadata.get("canonical_paper_id") or metadata.get("canonical_id") or doc["id"]
        if doc["id"].startswith(("arxiv:", "hf:")):
            identity = "arxiv:" + re.sub(r"v\d+$", "", doc["id"].split(":", 1)[1])
        elif metadata.get("arxiv_id"):
            identity = "arxiv:" + re.sub(r"v\d+$", "", metadata["arxiv_id"])
        scored.append({"id": doc["id"], "title": doc["title"], "url": doc["url"], "source": doc["source"],
                       "canonical_id": identity, "score": round(score, 3), "score_components": {"lexical": round(weights["lexical"] * lexical, 3), "recency": round(weights["recency"] * recency, 3)},
                       "matches": matches, "age_days": None if age is None else round(age, 1),
                       "claim_status": "unassessed_source", "qualification": "not evaluated"})
    scored.sort(key=lambda x: (-x["score"], x["id"]))
    deduplicated = {}
    for item in scored:
        if item["canonical_id"] in deduplicated:
            deduplicated[item["canonical_id"]]["also_seen_as"].append(item["id"])
        else:
            item["also_seen_as"] = []
            deduplicated[item["canonical_id"]] = item
    scored = list(deduplicated.values())
    reserved = min(len(scored), math.ceil(limit * config.get("exploration_fraction", 0.2)))
    ranked = scored[:max(0, limit - reserved)]
    remaining = [item for item in scored if item not in ranked]
    # Stable daily sampling allows reproducible reports without selecting only
    # high keyword scorers. All retained dates remain eligible for exploration.
    rng = random.Random(str(config.get("exploration_seed", 0)) + moment.date().isoformat())
    exploration = rng.sample(remaining, min(reserved, len(remaining)))
    return [{**item, "selection": "ranked"} for item in ranked] + [{**item, "selection": "exploration"} for item in exploration]
