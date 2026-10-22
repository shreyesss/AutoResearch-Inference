"""Offline search planning and conditional ROI arithmetic, never qualification.

These functions do not fetch sources, invoke a model, or run a GPU experiment.
Search families are retrieval suggestions, not hardware compatibility assertions.
"""
import copy
import datetime as dt
import math
import re

from .store import fts_query

_STOP = set("a an and are as at be by can do does find for from how i in into is it me of on or our papers please research search that the this to want what when which with would".split())
_UNITS = {"s": 1_000_000.0, "ms": 1_000.0, "us": 1.0}


def _date(value):
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Date filters must be YYYY-MM-DD")
    return dt.date.fromisoformat(value)


def expand_query(question, config, after=None, before=None, plan=None):
    """Return at most eight transparent query recipes using a resolved config.

    Dates are [after, before). Local dates default to source updated_at; paper
    filters mean publication date. The returned recipes do not run themselves.
    Family neighbours are exploratory terms, deliberately not called synonyms.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be nonempty")
    if len(question) > 4000:
        raise ValueError("question must be at most 4000 characters")
    start, end = _date(after), _date(before)
    if start and end and start >= end:
        raise ValueError("after must precede exclusive before")
    if end == dt.date.min:
        raise ValueError("before has no preceding representable date")
    question = question.strip()
    if plan is not None:
        from .query_plan import compile_plan
        return compile_plan(question, plan, after, before)
    words = list(dict.fromkeys(w for w in re.findall(r"[\w][\w.\-/]*", question) if w.casefold() not in _STOP))[:12]
    words = words or [question]
    matches = []
    for family in config.get("families", config.get("topics", [])):
        terms = [str(t) for t in family.get("terms", []) if str(t).strip()]
        found = [t for t in terms if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", question, re.I)]
        generic = {'latency', 'performance', 'perf', 'throughput', 'optimization', 'speedup', 'ttft', 'tpot', 'itl'}
        if any(t.casefold() not in generic for t in found):
            matches.append({"id": family.get("id"), "name": family.get("name", family.get("id")), "matched_terms": found, "terms": terms})
    matches.sort(key=lambda m: (-len(m["matched_terms"]), -max(map(len, m["matched_terms"])), str(m["id"])))
    recipes = []

    def add(lane, terms, reason, match="any"):
        # Literal queries: Store.search performs the actual safe FTS conversion.
        clean = list(dict.fromkeys(t.replace('"', ' ').strip() for t in terms if t.strip()))
        literal = " ".join('"' + t + '"' for t in clean)
        join = " AND " if match == "all" else " OR "
        arxiv = join.join('all:"' + t + '"' for t in clean)
        filters = []
        if start:
            filters.append("from_publication_date:" + after)
        if end:
            filters.append("to_publication_date:" + (end - dt.timedelta(days=1)).isoformat())
        if start or end:
            first = start.strftime("%Y%m%d") + "0000" if start else "000101010000"
            last = (end - dt.timedelta(days=1)).strftime("%Y%m%d") + "2359" if end else "999912312359"
            arxiv = "(" + arxiv + ") AND submittedDate:[" + first + " TO " + last + "]"
        recipes.append({"lane": lane, "reason": reason, "terms": clean,
                        "fts5": fts_query(literal, match),
                        "local": {"query": literal, "match": match, "after": after, "before": before, "date_field": "updated_at"},
                        "arxiv": {"search_query": arxiv},
                        "openalex": {"search": " ".join(clean), "filter": ",".join(filters) or None}})

    add("exact", [question], "Literal user wording; precise but may have low recall.")
    add("lexical", words, "User vocabulary with common request words removed; broad OR retrieval.")
    for family in matches[:4]:
        found = family["matched_terms"][:3]
        neighbours = [t for t in family["terms"] if t not in found][:2]
        add("family", found + neighbours, "Matched family " + str(family["name"]) + "; extra terms are exploratory neighbours, not equivalence or compatibility claims.")
    # Include falsification-oriented retrieval without requiring inference jargon.
    anchor = max((t for m in matches for t in m["matched_terms"]), key=len, default=words[0])
    add("control", [anchor, "regression"], "Look for counterevidence or regression reports anchored to the request.", "all")
    add("control", [anchor, "limitations"], "Look for applicability boundaries; absence of results is not proof of absence.", "all")
    return {"version": 1, 'mode': 'lexical_fallback', "question": question, "matched_families": [{k: v for k, v in m.items() if k != "terms"} for m in matches],
            "date_filters": {"after_inclusive": after, "before_exclusive": before, "local_field": "updated_at", "paper_field": "publication/submission date"},
            "queries": recipes, "limits": {"max_queries": 8, "max_families": 4, "network_calls": 0, "model_calls": 0},
            "notes": ["Use local.query with Store.search; fts5 is rendered SQL MATCH syntax, not input for Store.search.", "OpenAlex search is provider text search, not guaranteed equivalent to local Boolean/phrase matching.", "No matched taxonomy family leaves user wording intact and adds only general counterevidence searches."]}


def _number(value, label, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(label + " must be a finite number")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(label + " is outside its allowed range")
    return float(value)


def _time(value, label):
    unit = value.get("unit")
    if unit not in _UNITS:
        raise ValueError(label + ".unit must be s, ms, or us")
    return _number(_number(value.get("value"), label + ".value", minimum=0) * _UNITS[unit], label + " converted to us", minimum=0)


def prescreen(record):
    """Estimate exposed iteration savings and amortized time/token, conditionally.

    A caller must explicitly give accepted output progress for both variants.
    Rollout length is not accepted progress. No estimate of TTFT, tail ITL, E2E,
    or throughput is inferred from iteration arithmetic alone.
    """
    record = copy.deepcopy(record)
    target = record.get("target", {})
    if not target.get("benchmark") or not target.get("metric"):
        raise ValueError("target.benchmark and target.metric are required")
    if target.get("direction", "lower") not in ("lower", "higher"):
        raise ValueError("target.direction must be lower or higher")
    threshold = target.get("min_relative_gain")
    if threshold is not None:
        threshold = _number(threshold, "min_relative_gain", minimum=0)
    if target.get("baseline") is not None:
        baseline_metric = target["baseline"]
        _number(baseline_metric.get("value"), "target.baseline.value", minimum=0)
        if not baseline_metric.get("unit"):
            raise ValueError("target.baseline.unit required")
    unknowns = []
    baseline = None
    if record.get("baseline_iteration") is not None:
        baseline = _time(record["baseline_iteration"], "baseline_iteration")
        if baseline <= 0:
            raise ValueError("baseline_iteration must be positive")
    else:
        unknowns.append("baseline iteration duration")
    savings = record.get("component_savings")
    if savings is not None:
        if savings.get("unit") not in _UNITS:
            raise ValueError("component_savings.unit must be s, ms, or us")
        low = _number(savings.get("low"), "component_savings.low") * _UNITS[savings["unit"]]
        high = _number(savings.get("high"), "component_savings.high") * _UNITS[savings["unit"]]
        _number(low, "component_savings.low converted to us")
        _number(high, "component_savings.high converted to us")
        if low > high:
            raise ValueError("component_savings.low must not exceed high")
    else:
        unknowns.append("component savings range")
    calls = record.get("calls_per_iteration")
    if calls is not None:
        calls = _number(calls, "calls_per_iteration", minimum=0)
    else:
        unknowns.append("component calls per complete iteration (not speculative rollout length)")
    exposure = record.get("exposed_fraction")
    if exposure is not None:
        e_low = _number(exposure.get("low"), "exposed_fraction.low", 0, 1)
        e_high = _number(exposure.get("high"), "exposed_fraction.high", 0, 1)
        if e_low > e_high:
            raise ValueError("exposed_fraction.low must not exceed high")
    else:
        unknowns.append("critical-path exposed fraction after overlap")
    progress = record.get("progress") or {}
    base_tokens, candidate_tokens = progress.get("baseline_tokens"), progress.get("candidate_tokens")
    for name, value in (("baseline_tokens", base_tokens), ("candidate_tokens", candidate_tokens)):
        if value is not None and _number(value, "progress." + name, minimum=0) <= 0:
            raise ValueError("progress." + name + " must be positive accepted output tokens per complete iteration")
        if value is None:
            unknowns.append("accepted output tokens per iteration: " + name)
    estimates = {}
    if baseline is not None and savings is not None and calls is not None and exposure is not None:
        deltas = [_number(s * e * calls, "computed iteration savings") for s in (low, high) for e in (e_low, e_high)]
        saved_low, saved_high = min(deltas), max(deltas)
        candidate_low = _number(baseline - saved_high, "candidate iteration lower bound")
        candidate_high = _number(baseline - saved_low, "candidate iteration upper bound")
        if candidate_low <= 0:
            raise ValueError("savings bound consumes the whole iteration; check units, call counts and exposure")
        estimates["saved_iteration_us"] = {"low": saved_low, "high": saved_high}
        estimates["candidate_iteration_us"] = {"low": candidate_low, "high": candidate_high}
        estimates["iteration_relative_gain"] = {"low": _number(saved_low / baseline, "lower iteration gain"), "high": _number(saved_high / baseline, "upper iteration gain")}
        if base_tokens is not None and candidate_tokens is not None:
            base_per_token = _number(baseline / base_tokens, "baseline time per token", minimum=0)
            if base_per_token == 0:
                raise ValueError("baseline time per token underflows; check units and progress")
            per_token_low = _number(candidate_low / candidate_tokens, "candidate low time per token", minimum=0)
            per_token_high = _number(candidate_high / candidate_tokens, "candidate high time per token", minimum=0)
            estimates["baseline_amortized_us_per_token"] = base_per_token
            estimates["candidate_amortized_us_per_token"] = {"low": per_token_low, "high": per_token_high}
            estimates["amortized_time_per_token_relative_gain"] = {"low": _number(1 - per_token_high / base_per_token, "lower relative gain"), "high": _number(1 - per_token_low / base_per_token, "upper relative gain")}
    # Only this deliberately explicit metric can be compared to the estimate.
    # TPOT and ITL labels alone do not establish workload/streaming semantics.
    applicable = target["metric"] == "amortized_time_per_output_token" and target.get("direction", "lower") == "lower"
    gain = estimates.get("amortized_time_per_token_relative_gain") if applicable else None
    if not applicable:
        unknowns.append("mapping iteration/time-per-token estimate to target metric " + str(target["metric"]))
    failed_guards, unknown_guards = [], []
    for guard in record.get("tail_guards", []):
        if not guard.get("name") or guard.get("passed") not in (None, True, False) or isinstance(guard.get("passed"), (int, float)) and not isinstance(guard.get("passed"), bool):
            raise ValueError("tail_guards need a name and passed=true/false/null")
        if guard.get("passed") is False:
            failed_guards.append(guard["name"])
        elif guard.get("passed") is None:
            unknown_guards.append(guard["name"])
    unknowns.extend("unmeasured tail guard: " + name for name in unknown_guards)
    if failed_guards:
        decision, reason = "reject", "Recorded task guard failed: " + ", ".join(failed_guards) + ". Revisit only with a new variant/attempt."
    elif gain is not None and threshold is not None and gain["high"] < threshold:
        decision, reason = "reject", "Even the supplied optimistic bound misses this task's minimum relative gain; this is a conditional screen, not a measured negative result."
    elif not record.get("next_cheapest_falsifier"):
        decision, reason = "defer", "Specify a bounded cheapest falsifier before spending experiment resources."
    else:
        decision, reason = "advance_diagnostic", "Run the stated cheapest falsifier to test assumptions and applicability; no service improvement or deployment qualification is established."
    return {"version": 1, "kind": "conditional_prescreen", "validated": False, "target": target,
            "decision": decision, "reason": reason, "estimates": estimates, "target_relative_gain": gain,
            "unknowns": unknowns, "input": record, "evidence": record.get("evidence", []),
            "assumptions": record.get("assumptions", []), "counters": record.get("counters", []),
            "next_cheapest_falsifier": record.get("next_cheapest_falsifier"),
            "formula": "candidate_iteration_us = baseline_iteration_us - saved_component_us * calls_per_iteration * exposed_fraction; amortized_time_per_token = iteration_us / accepted_output_tokens_per_iteration",
            "limitations": ["Bounds are supplied assumptions, not confidence intervals or independent validation.", "Accepted progress includes all emitted output tokens per complete iteration; rollout length alone is insufficient.", "Streaming gaps, queues, TTFT, tail latency, throughput and E2E require workload-specific measurement; a component speedup is not a service speedup.", "Use CPU source-path, shape and correctness checks before a bounded GPU probe where those checks can falsify the mechanism."]}
