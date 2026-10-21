import copy

import pytest

from ideation.chat_memory import persist_card, recall_cards
from ideation.hypothesis_memory import HypothesisMemory
from ideation.store import Store


@pytest.fixture
def proposal(tmp_path):
    store = Store(tmp_path / "research/corpus.sqlite")
    store.put({"id": "github:example/lib:1", "source": "github", "kind": "pr", "repo": "example/lib",
               "title": "Avoid redundant staging", "body": "Avoid redundant staging for grouped calls.",
               "url": "https://github.com/example/lib/pull/1"})
    store.db.commit()
    store.db.close()
    return tmp_path, {
        "run_id": "chat-one", "card": {
            "id": "H1", "statement": "Reduce exposed sampler latency", "mechanism": "Avoid redundant staging",
            "proposed_change": "Reuse grouped buffer", "evidence": [{"source_id": "github:example/lib:1",
            "quote": "Avoid redundant staging", "relation": "supports"}]},
        "brief": {"baseline": {"commit": "known-parent"}, "objective": "Reduce ITL"},
        "disposition": {"status": "accepted", "reasons": ["Worth a bounded CPU-first diagnostic"]},
        "prescreen": {"expected_relative_gain": None, "unknowns": ["Exposed critical-path fraction"],
                      "next_check": "Inspect captured shapes and dispatch"}}


def test_retry_preserves_graph_and_selection_without_fabricating_test(proposal):
    root, record = proposal
    first = persist_card(root, record)
    second = persist_card(root, record)
    assert first == second
    hypothesis = second["hypothesis"]
    assert hypothesis["status"] == "accepted"
    assert hypothesis["experiment_status"] == "untested"
    assert hypothesis["brief"]["selection"]["require_novelty"] is False
    assert len(hypothesis["events"]) == 2
    assert recall_cards(root, "sampler")[0]["id"] == hypothesis["id"]
    ledger = HypothesisMemory(root / "research/hypotheses.sqlite")
    assert any(e["relation"] == "supports" for e in ledger.graph(hypothesis["id"])["edges"])
    ledger.db.close()


def test_bad_quote_cannot_enter_memory(proposal):
    root, record = proposal
    record["card"]["evidence"][0]["quote"] = "Invented benchmark result proves 30 percent faster"
    with pytest.raises(ValueError, match="quote"):
        persist_card(root, record)
    assert recall_cards(root) == []


def test_immutable_card_and_new_review_keep_history(proposal):
    root, record = proposal
    original = persist_card(root, record)
    changed = copy.deepcopy(record)
    changed["card"]["statement"] = "Silent rewrite"
    with pytest.raises(ValueError, match="Conflicting"):
        persist_card(root, changed)
    record["disposition"] = {"status": "deferred", "reasons": ["Native timing unavailable"]}
    revised = persist_card(root, record)["hypothesis"]
    assert revised["card"] == original["hypothesis"]["card"]
    assert [e["data"]["status"] for e in revised["events"] if e["type"] == "reviewed"] == ["accepted", "deferred"]
    assert revised["outcomes_by_scope"] == []


def test_partial_proposal_retained_but_acceptance_needs_prescreen(proposal):
    root, record = proposal
    del record["prescreen"]
    with pytest.raises(ValueError, match="prescreen"):
        persist_card(root, record)
    record["disposition"] = {"status": "proposed", "reasons": ["Evidence gap needs inspection"]}
    record["card"]["evidence"] = []
    assert persist_card(root, record)["hypothesis"]["status"] == "proposed"
    record["disposition"]["status"] = "validated"
    with pytest.raises(ValueError, match="selection status"):
        persist_card(root, record)
