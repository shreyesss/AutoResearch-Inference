"""Small domain adapter around DiscoveryRSI records; no experiment executor."""
import hashlib
import json
import time
from pathlib import Path

from .evidence import ResearchTools, canonical, new_output, quote_errors, write_json, grounded_excerpt, RULES
from .research import S, arr, obj, excerpt, read_brief, run_agent
from .store import now
from .policy import POLICY_SCHEMA, validate_policy, policy_id, policy_prompt, review_schema
from .hypothesis_memory import HypothesisMemory

CITATION = obj({"source_id": S, "quote": S, "relation": {"type": "string", "enum": ["supports", "challenges", "context"]}})
CARD = obj({
    "id": S, "parents": arr(S), "operation": {"type": "string", "enum": ["generate", "evolve", "repair", "combine"]},
    "statement": S, "observed_bottleneck": S, "mechanism": S, "proposed_change": S,
    "code_surface": S, "applicability": S, "predicted_direction": S,
    "classification": {"type": "string", "enum": ["new_mechanism", "adaptation", "activation", "upstream_port"]},
    "alternatives": arr(obj({"explanation": S, "distinguishing_test": S})),
    "evidence": arr(CITATION),
    "novelty": obj({"scientific": S, "implementation": S, "workload": S, "nearest_prior_art": S, "specific_delta": S}),
    "prior_art_query": S,
    "experiment": obj({k: S for k in ["control", "treatment", "metrics", "supports_if", "rejects_if", "inconclusive_if", "held_out_condition", "correctness", "cost"]}),
    "revision_reason": S,
})
PROPOSAL_SCHEMA = obj({"hypotheses": arr(CARD), "gaps": arr(S)})


def fingerprint(card):
    text = " ".join(card["mechanism"].lower().split()) + "|" + " ".join(card["proposed_change"].lower().split())
    return hashlib.sha256(text.encode()).hexdigest()


def assess(card, review, sources, prior_art=None, known_fingerprints=(), *, policy):
    """Integrity checks + task-derived review. Prior-art overlap alone is never a veto."""
    import jsonschema
    errors = [e.message for e in jsonschema.Draft202012Validator(CARD).iter_errors(card)]
    pending = []
    def result(score=None):
        status = "rejected" if errors else "deferred" if pending else "accepted"
        return {"eligible": status == "accepted", "status": status, "score": score,
                "reasons": errors + pending, "policy_id": policy_id(policy),
                "meaning": "Eligible for experiment design only; not scientifically validated or a measured improvement"}
    if errors:
        return result()
    for key in ("statement", "mechanism", "proposed_change", "code_surface", "applicability", "predicted_direction"):
        if not card[key].strip():
            errors.append("Empty hypothesis field: " + key)
    errors += quote_errors(card["evidence"], sources)
    docs = {d["id"]: d for d in sources}
    cited = [docs[e["source_id"]] for e in card["evidence"] if e["source_id"] in docs]
    if any(d["kind"] == "discovery" for d in cited):
        errors.append("Generated discovery output cannot be primary evidence")
    requirements = policy["evidence"]
    if len({canonical(d) for d in cited}) < requirements["minimum_independent_sources"]:
        pending.append("Task rubric needs more independent source identities; mirrors count once")
    if requirements["require_engineering"] and not any(d["id"].startswith("github:") or d["kind"] == "code" for d in cited):
        pending.append("Task rubric needs engineering evidence")
    if requirements["require_paper_fulltext"] and not any(d["kind"] == "fulltext" for d in cited):
        pending.append("Task rubric needs paper full-text evidence")
    if not card["alternatives"]:
        pending.append("No competing explanation and distinguishing test")
    if any(not value.strip() for value in card["experiment"].values()):
        pending.append("Incomplete experiment decision criteria")
    # Duplicate mechanisms are linked in memory, not blacklisted across tasks/baselines/policies.
    if review is None:
        pending.append("Missing critique")
        return result()
    validation = [e.message for e in jsonschema.Draft202012Validator(review_schema(policy)["properties"]["reviews"]["items"]).iter_errors(review)]
    if validation:
        errors += validation
        return result()
    if review["id"] != card["id"]:
        errors.append("Review ID does not match candidate")
    if review["factual_support"] == "fail":
        errors.append("Critic: factual claims unsupported or contradicted")
    elif review["factual_support"] == "unknown":
        pending.append("Critic: factual support needs inspection")
    for criterion in policy["criteria"]:
        judgment = review["criteria"][criterion["id"]]
        if criterion["required"] and judgment["verdict"] != "pass":
            reason = criterion["id"] + ": " + judgment["rationale"]
            (errors if judgment["verdict"] == "fail" else pending).append(reason)
    score = round(sum(c["weight"] * review["criteria"][c["id"]]["score"] / 5 for c in policy["criteria"]), 1)
    if score < policy["threshold"]:
        pending.append("Priority below this task's threshold; reconsider with evidence or a revised policy")
    return result(score)


class HypothesisTools:
    def __init__(self, store):
        self.store = store
        self.ledger = HypothesisMemory(store.path.parent / "hypotheses.sqlite")

    def memory(self, limit=30, status=None, baseline=None, text=None):
        """Query persistent hypotheses; status is selection, not experimental truth."""
        return self.ledger.query(limit=limit, status=status, baseline=baseline, text=text)

    def recall(self, brief, limit=12, max_chars=24000):
        """Bounded task/baseline recall; full records remain available through get/graph."""
        return self.ledger.recall(read_brief(brief), limit=limit, max_chars=max_chars)

    def rubric(self, brief, output, packet=None, model=None, timeout=180):
        """Generate and freeze an editable task rubric without proposing or testing anything."""
        import jsonschema
        brief = read_brief(brief)
        sources = json.loads(Path(packet).read_text())["sources"] if packet else []
        out = new_output(output)
        policy = run_agent(policy_prompt(brief, [{"id": d["id"], "kind": d["kind"], "title": d["title"]} for d in sources]),
                           POLICY_SCHEMA, out, "rubric", model, timeout, RULES)
        jsonschema.validate(policy, POLICY_SCHEMA)
        validate_policy(policy, brief)
        write_json(out / "rubric.json", policy)
        write_json(out / "brief.json", brief)
        return {"path": str(out / "rubric.json"), "policy_id": policy_id(policy), "policy": policy}

    def get(self, hypothesis_id):
        """Full immutable card, policies, selection history and scoped experimental results."""
        return self.ledger.get(hypothesis_id)

    def graph(self, hypothesis_id):
        """Explicit provenance/lineage/test links, not inferred causal relationships."""
        return self.ledger.graph(hypothesis_id)

    def import_runs(self, root="runs"):
        """Idempotently import historical artifacts without re-evaluating their old decisions."""
        return {"runs": self.ledger.import_runs(root),
                "legacy_events": self.ledger.import_jsonl(self.store.path.parent / "hypothesis-memory.jsonl"),
                "memory": self.ledger.stats()}

    def plan_test(self, hypothesis_id, plan, scope, actor="operator"):
        """Persist a proposed evaluation and baseline/workload scope; does not execute it."""
        return self.ledger.plan_test(hypothesis_id, plan, scope, actor=actor)

    def test_result(self, test_id, verdict, artifact, note, actor="operator"):
        """Record attributed validated/invalidated/inconclusive/error result and artifact hash."""
        return self.ledger.test_result(test_id, verdict, artifact, note, actor=actor)

    def run(self, brief, packet, output, rounds=1, model=None, timeout=600, policy=None, revisit=None):
        from discovery_rsi.core import Candidate, Episode, ReplayBuffer
        import jsonschema
        rounds = int(rounds)
        if not 1 <= rounds <= 3:
            raise ValueError("Use 1–3 rounds; each has one proposal and one critique call")
        if revisit and (rounds != 1 or len(revisit) > 5):
            raise ValueError("Revisit 1–5 existing hypotheses in one review round")
        brief = read_brief(brief)
        packet = json.loads(Path(packet).read_text())
        errors = quote_errors(packet.get("claims", []), packet["sources"])
        if errors or not packet.get("quote_validation", {}).get("valid"):
            raise ValueError("Input evidence packet has not passed quote validation")
        out, deadline = new_output(output), time.monotonic() + timeout
        sources = {d["id"]: d for d in packet["sources"]}
        memory = self.ledger.recall(brief)
        known = {e["fingerprint"] for e in memory if e.get("fingerprint")}
        write_json(out / "brief.json", brief)
        write_json(out / "input-evidence.json", packet)
        write_json(out / "memory-input.json", memory)
        manifest = {"started_at": now(), "status": "running", "rounds": [], "requested": brief.get("count", 2),
                    "dependency": "DiscoveryRSI Candidate/Episode/ReplayBuffer; domain gates are local",
                    "model": model or "existing agent configuration", "gpu_experiments": 0}
        write_json(out / "manifest.json", manifest)
        history, selected_cards, evaluations, retained, global_ids = [], [], [], {}, {}
        literature = ResearchTools(self.store)
        def agent(stage, prompt, schema):
            remaining = deadline - time.monotonic()
            if remaining < 15:
                raise RuntimeError("Time budget exhausted; partial artifacts retained")
            result = run_agent(prompt, schema, out, stage, model, int(remaining), RULES)
            jsonschema.validate(result, schema)
            return result
        def bounded(citations=()):
            evidence = packet.get("claims", []) + list(citations)
            return [{**d, "body": grounded_excerpt(d, evidence)} for d in sources.values()]
        try:
            policy = json.loads(Path(policy).read_text()) if isinstance(policy, str) else policy
            if policy is None:
                policy = agent("rubric", policy_prompt(brief, [{"id": d["id"], "kind": d["kind"], "title": d["title"]} for d in sources.values()]), POLICY_SCHEMA)
            validate_policy(policy, brief)
            write_json(out / "rubric.json", policy)
            manifest["policy_id"] = policy_id(policy)
            schema = review_schema(policy)
            for number in range(1, rounds + 1):
                if revisit:
                    cards = []
                    for index, identity in enumerate(revisit, 1):
                        card = self.ledger.get(identity)["card"]
                        cards.append({**card, "id": "R" + str(index), "parents": [identity], "operation": "evolve",
                                      "revision_reason": "Unchanged mechanism reconsidered under this task and policy; original decision retained"})
                    draft = {"hypotheses": cards, "gaps": []}
                    jsonschema.validate(draft, PROPOSAL_SCHEMA)
                    write_json(out / f"propose-{number}.json", draft)
                else:
                    draft = agent(f"propose-{number}", "Propose at most " + str(min(5, brief.get("count", 2))) + " distinct optimization hypotheses. "
                    "First write one clear 80–150 word statement per idea, then specify its test. Try mechanism transfer, "
                    "constraint-specific adaptation, and resolving conflicting evidence. Do not fill the quota with weak ideas. "
                    "Do not invent measured bottlenecks or numerical speedups. Separate predictions from observations. "
                    "Include a strong existing/static comparator, competing explanation, held-out workload, and support/reject/inconclusive criteria. "
                    "Use concise mechanism-based prior_art_query (2–5 terms), not every hardware keyword. "
                    "IDs must be unique in this run. Parents must name real earlier IDs; revise after objections rather than rename. "
                    "Optimize usefulness against this baseline under the supplied task rubric. Known methods, flags and ports are allowed. "
                    "Novelty is descriptive only unless the rubric explicitly enables it. Historical rejections are context, not bans. "
                    "If baseline inclusion is unknown, propose a cheap presence/eligibility check as the first step. "
                    "Parent IDs may also use global hypothesis IDs from memory. "
                    "Return zero ideas if evidence cannot support any.\n" + json.dumps({"brief": brief, "rubric": policy, "evidence": bounded(), "claims": packet.get("claims", []), "history": history, "previous_runs": memory}), PROPOSAL_SCHEMA)
                # Persist EVERY schema-valid proposal before retrieval or critic can fail.
                for card in draft["hypotheses"]:
                    if card["id"] in global_ids:
                        raise ValueError("Duplicate candidate ID")
                    stored_card = {**card, "parents": [global_ids.get(p, p) for p in card["parents"]]}
                    global_ids[card["id"]] = self.ledger.register(str(out), stored_card, brief, policy, list(sources.values()))
                prior = {}
                for card in draft["hypotheses"]:
                    if time.monotonic() > deadline - 100:
                        prior[card["id"]] = {"error": "Retrieval time budget exhausted"}
                        continue
                    # Older implementations and negative evidence remain useful for baseline comparisons.
                    repos = brief.get("repos", ["vllm-project/vllm"])
                    hits = [d for repo in repos for d in self.store.search(card["prior_art_query"], id_prefix="github:" + repo + ":", limit=6)] if policy["retrieval"]["github"] else []
                    for d in hits:
                        sources[d["id"]] = d
                    try:
                        found = literature.search(card["prior_art_query"], limit=3) if policy["retrieval"]["literature"] else {"ids": [], "status": "not_requested"}
                    except Exception as error:
                        found = {"ids": [], "error": str(error), "coverage": "retrieval_failed_not_absence"}
                    for id in found["ids"]:
                        sources[id] = self.store.get(id)
                    prior[card["id"]] = {"query": card["prior_art_query"], "searched_at": now(),
                                           "github": {"ids": [d["id"] for d in hits], "repos": repos, "coverage": "local selected-repository corpus; not proof of absence in other engines"}, "literature": found}
                write_json(out / f"prior-art-{number}.json", prior)
                review = agent(f"critique-{number}", "Challenge these proposals under ONLY the supplied task rubric. "
                    "Evaluate each criterion pass/fail/unknown with score 0–5 and a concrete rationale. "
                    "Use unknown for evidence gaps, fail for established constraint violations. "
                    "Entailment concerns reported facts, not proof of an explicitly untested prediction. "
                    "An unmeasured bottleneck can be the first falsification question; do not demand a proven speedup before proposing a test. "
                    "No-GPU-execution constraints prohibit launching jobs in this research session, not describing a later bounded experiment. "
                    "A full-text source existing does not mean the quoted passage supports the claim. "
                    "No search hits is uncertainty. Novelty is irrelevant unless explicitly enabled by the rubric. "
                    "Score 0–5 with explicit objections. High polish must not rescue a failed gate. "
                    "Known techniques, feature activation and ports are legitimate candidates if useful relative to the baseline. "
                    "An explicit cheap baseline/eligibility check can resolve unknown deployment inclusion before implementation. "
                    "Do not repeat historical novelty rejection as a current veto. Review each ID exactly once.\n" +
                    json.dumps({"brief": brief, "rubric": policy, "draft": draft, "prior_art": prior,
                                "sources": bounded([e for c in draft["hypotheses"] for e in c["evidence"]]), "memory": memory}), schema)
                reviews = {r["id"]: r for r in review["reviews"]}
                if len(reviews) != len(review["reviews"]) or set(reviews) != {c["id"] for c in draft["hypotheses"]}:
                    raise ValueError("Missing, extra or duplicate review IDs")
                candidates, eligible = [], []
                for card in draft["hypotheses"]:
                    previous_ids = {h["card"]["id"] for h in history}
                    if card["id"] in previous_ids:
                        raise ValueError("Duplicate candidate ID or unknown parent")
                    assessment = assess(card, reviews.get(card["id"]), list(sources.values()), prior.get(card["id"], {}), known, policy=policy)
                    record = {"card": card, "global_id": global_ids[card["id"]], "review": reviews.get(card["id"]), "assessment": assessment}
                    history.append(record)
                    evaluations.append({"id": card["id"], **assessment})
                    candidates.append(Candidate(id=card["id"], claim=card["statement"], plan=json.dumps(card["experiment"]),
                                                alternatives=[a["explanation"] for a in card["alternatives"]],
                                                evidence=[e["source_id"] for e in card["evidence"]], parents=card["parents"],
                                                score=assessment["score"] or 0, critique=json.dumps(record["review"])))
                    self.ledger.review(global_ids[card["id"]], assessment, record["review"], policy=policy,
                                       context={"prior_art": prior.get(card["id"], {}), "sources": list(sources.values())})
                    if assessment["eligible"]:
                        eligible.append((card, assessment))
                        for parent in card["parents"]:
                            retained.pop(parent, None)
                        retained[card["id"]] = (card, assessment)
                eligible.sort(key=lambda pair: pair[1]["score"], reverse=True)
                selected_cards = [card for card, _ in sorted(retained.values(), key=lambda pair: pair[1]["score"], reverse=True)][:brief.get("count", 2)]
                ReplayBuffer(out / "episodes.jsonl").append(Episode(number, candidates,
                    eligible[0][0]["id"] if eligible else None, "selected_for_test_design" if eligible else "no_eligible_candidate"))
                manifest["rounds"].append({"round": number, "proposed": len(candidates), "eligible": len(eligible)})
                write_json(out / "history.json", history)
                write_json(out / "sources.json", list(sources.values()))
                write_json(out / "manifest.json", manifest)
            manifest.update(status="completed" if selected_cards else "completed_no_selection", finished_at=now(), selected=len(selected_cards),
                            shortfall=max(0, brief.get("count", 2) - len(selected_cards)), evaluations=evaluations)
            write_json(out / "hypotheses.json", {"hypotheses": selected_cards, "status": "untested", "publication_novelty": "unestablished"})
            lines = ["# Hypothesis decision", "", "Untested proposals. Scores are prioritization judgments, not predicted speedups.", "",
                     f"Selected for test design: {len(selected_cards)}. Requested: {brief.get('count', 2)}.", ""]
            for record in history:
                card, gate = record["card"], record["assessment"]
                lines += ["## " + card["id"], "", card["statement"], "", "**Decision:** " + gate["status"],
                          "", "**Reasons:** " + ("; ".join(gate["reasons"]) or "Passed structural and critic gates; engineering review remains"),
                          "", "**Cheap test:** " + card["experiment"]["treatment"], "", "**Reject if:** " + card["experiment"]["rejects_if"], ""]
            (out / "decision.md").write_text("\n".join(lines))
        except Exception as e:
            manifest.update(status="failed", error=str(e), finished_at=now())
            raise
        finally:
            write_json(out / "manifest.json", manifest)
        return {"output": str(out), **manifest}

    def outcome(self, run, candidate_id, verdict, artifact, note):
        """Legacy adapter: imports the run and records an explicitly scoped supplied result."""
        verdicts = {"supported": "validated", "rejected": "invalidated", "inconclusive": "inconclusive"}
        if verdict not in verdicts:
            raise ValueError("verdict must be supported, rejected, or inconclusive")
        self.ledger.import_runs(run)
        hypothesis = self.ledger.get(self.ledger.identity(str(Path(run).resolve()), candidate_id))
        test = self.ledger.plan_test(hypothesis["id"], hypothesis["card"].get("experiment", {}),
                    {"legacy_scope": "See supplied artifact; scope was not registered before execution", "run": str(Path(run).resolve())})
        return self.ledger.test_result(test["id"], verdicts[verdict], artifact, note)
