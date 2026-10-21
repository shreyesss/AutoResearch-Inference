"""Persist operator/chat proposals in the existing hypothesis graph.

The CLI owns the shared writer lock and snapshot/publication. This helper does
not call a model, execute an experiment, or independently approve a proposal.
"""
import json
from pathlib import Path

from .hypothesis_memory import HypothesisMemory
from .store import Store


def _nonempty_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " must be nonempty text")


def persist_card(root, record):
    """Validate local source quotes, append proposal/review, return stored record.

    record: run_id, card, brief, disposition; optional policy and prescreen.
    Disposition is a caller-attributed selection judgment, never test evidence.
    """
    # Detach caller objects and reject nonportable NaN/infinite values.
    record = json.loads(json.dumps(record, allow_nan=False))
    if not isinstance(record, dict):
        raise ValueError("Record must be an object")
    _nonempty_text(record.get("run_id"), "run_id")
    card, brief = record.get("card"), record.get("brief")
    if not isinstance(card, dict) or not isinstance(brief, dict):
        raise ValueError("card and brief must be objects")
    for key in ("id", "statement", "mechanism", "proposed_change"):
        _nonempty_text(card.get(key), "card." + key)
    if not isinstance(brief.get("baseline"), dict) or not brief["baseline"]:
        raise ValueError("Explicit baseline object required; mark missing facts unknown")
    selection = brief.setdefault("selection", {})
    if not isinstance(selection, dict):
        raise ValueError("brief.selection must be an object")
    selection.setdefault("require_novelty", False)
    if not isinstance(selection["require_novelty"], bool):
        raise ValueError("require_novelty must be boolean")
    disposition = record.get("disposition")
    if not isinstance(disposition, dict) or disposition.get("status") not in {
        "proposed", "accepted", "deferred", "rejected", "superseded"
    }:
        raise ValueError("Disposition must be a selection status, not an experiment result")
    reasons = disposition.get("reasons")
    if not isinstance(reasons, list) or not reasons:
        raise ValueError("Disposition needs explicit reasons")
    for reason in reasons:
        _nonempty_text(reason, "disposition reason")
    evidence = card.setdefault("evidence", [])
    parents = card.setdefault("parents", [])
    if not isinstance(evidence, list) or not isinstance(parents, list):
        raise ValueError("evidence and parents must be lists")
    for parent in parents:
        _nonempty_text(parent, "parent")
    policy = record.get("policy", {"origin": "chat-task-policy", "require_novelty": selection["require_novelty"]})
    if not isinstance(policy, dict):
        raise ValueError("policy must be an object")
    prescreen = record.get("prescreen")
    if prescreen is not None and not isinstance(prescreen, dict):
        raise ValueError("prescreen must be an object")
    if disposition["status"] == "accepted" and (not evidence or not prescreen):
        raise ValueError("Accepted selection needs source evidence and explicit prescreen assumptions/unknowns")
    for citation in evidence:
        if not isinstance(citation, dict) or citation.get("relation") not in {"supports", "challenges", "context"}:
            raise ValueError("Each citation needs supports/challenges/context relation")
        _nonempty_text(citation.get("source_id"), "source_id")
        _nonempty_text(citation.get("quote"), "quote")

    root = Path(root)
    source_path = root / "research/corpus.sqlite"
    if not source_path.is_file():
        raise ValueError("Initialize or restore the research corpus first")
    store = Store(source_path)
    sources = {}
    try:
        for citation in evidence:
            source = store.get(citation["source_id"])
            if not source or source["kind"] == "discovery":
                raise ValueError("Citation requires an existing primary source record")
            quote = " ".join(citation["quote"].split())
            text = " ".join((source["title"] + " " + source["body"]).split())
            if len(quote) < 12 or quote not in text:
                raise ValueError("Citation quote does not match local source")
            sources[source["id"]] = source
    finally:
        store.db.close()

    ledger = HypothesisMemory(root / "research/hypotheses.sqlite")
    try:
        identity = ledger.register("chat:" + record["run_id"], card, brief, policy, sources)
        assessment = {
            **disposition,
            "eligible": disposition["status"] == "accepted",
            "origin": "chat_operator",
            "meaning": "Caller-attributed selection; quote presence checked, scientific merit and service ROI not independently validated",
        }
        ledger.review(identity, assessment,
                      {"origin": "chat_operator", "prescreen": prescreen}, policy=policy)
        return {"hypothesis": ledger.get(identity), "source_count": len(sources),
                "quote_validation": {"valid": True, "meaning": "Exact normalized substring only; not factual entailment"},
                "gpu_experiments": 0}
    finally:
        ledger.db.close()


def recall_cards(root, query=None, limit=20):
    """Existing ledger search; selection status remains separate from outcomes."""
    ledger = HypothesisMemory(Path(root) / "research/hypotheses.sqlite")
    try:
        return ledger.query(text=query, limit=limit)
    finally:
        ledger.db.close()
