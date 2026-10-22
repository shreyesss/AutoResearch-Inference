import hashlib
import json

import pytest

from ideation.foundation import _import_corpus, invoke
from ideation.store import Store


def doc(identity, body, date="2026-10-01T00:00:00Z"):
    return dict(id=identity, source="arxiv", kind="fulltext", title="Retained paper",
                body=body, url="https://arxiv.org/html/2610.00001v1", updated_at=date,
                fetched_at=date, metadata={"version_pinned": True})


def rows(store):
    return {table: sorted(tuple(r) for r in store.db.execute("SELECT * FROM " + table))
            for table in ("documents", "document_revisions", "edges", "checkpoints", "search_index")}


def test_selected_cli_reuses_revisions_edges_without_other_records_or_cursors(tmp_path):
    source_path = tmp_path / "source.sqlite"
    source = Store(source_path)
    selected = "fulltext:2610.00001v1"
    source.put(doc(selected, "Original text"))
    source.put(doc(selected, "Corrected text", "2026-10-02T00:00:00Z"))
    source.put(doc("paper:unselected", "Unrelated source"))
    source.edge(selected, "discovered_by", "query:retained", "query:retained", {"provider": "arxiv"})
    source.edge("query:inbound", "found", selected, "query:inbound", {})
    source.edge("paper:unselected", "discovered_by", "query:other", "query:other", {})
    source.checkpoint("arxiv:last_request", 123)
    expected_revisions = source.revisions(selected)
    source.db.close()
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()
    state = tmp_path / "state"
    invoke(["--state-dir", str(state), "init"])
    args = ["--state-dir", str(state), "--local-only", "--defer-snapshot", "import-corpus",
            "--source", str(source_path), "--source-id", selected, "--source-id", selected]
    first = invoke(args)
    assert first["selected_source_ids"] == [selected]
    assert first["documents_seen"] == 1 and first["checkpoints_imported"] == 0
    target = Store(state / "research/corpus.sqlite", readonly=True)
    assert target.get(selected)["body"] == "Corrected text"
    assert target.get("paper:unselected") is None
    assert target.revisions(selected) == expected_revisions
    assert not target.db.execute("SELECT * FROM checkpoints").fetchall()
    assert target.db.execute("SELECT 1 FROM edges WHERE src='query:inbound' AND dst=?", (selected,)).fetchone()
    assert not target.db.execute("SELECT 1 FROM edges WHERE dst='query:other'").fetchone()
    initial = rows(target)
    target.db.close()
    second = invoke(args)
    assert second["revisions_imported"] == 0
    target = Store(state / "research/corpus.sqlite", readonly=True)
    assert rows(target) == initial
    target.db.close()
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before
    assert not (state / "research/cache").exists()


def test_selection_preserves_newer_target_and_historical_source_body(tmp_path):
    identity = "fulltext:2610.00001"
    source = Store(tmp_path / "old.sqlite")
    source.put(doc(identity, "Old https://example.org/old"))
    source.edge(identity, "discovered_by", "query:old", "query:old", {})
    source.db.commit()
    source.db.close()
    target = Store(tmp_path / "target.sqlite")
    target.put(doc(identity, "New https://example.org/new", "2026-10-03T00:00:00Z"))
    target.db.commit()
    result = _import_corpus(tmp_path / "old.sqlite", target, [identity])
    assert result["newer_local_preserved"] == 1
    assert target.get(identity)["body"].startswith("New")
    assert {r["body"].split()[0] for r in target.revisions(identity)} == {"Old", "New"}
    assert not target.db.execute("SELECT 1 FROM edges WHERE dst='https://example.org/old'").fetchone()
    assert target.db.execute("SELECT 1 FROM edges WHERE dst='query:old'").fetchone()
    target.db.close()


def test_missing_selection_fails_before_any_destination_write(tmp_path):
    source = Store(tmp_path / "source.sqlite")
    source.put(doc("paper:present", "Present")); source.db.commit(); source.db.close()
    target = Store(tmp_path / "target.sqlite")
    initial = rows(target)
    statements = []
    target.db.set_trace_callback(statements.append)
    with pytest.raises(ValueError, match="missing"):
        _import_corpus(tmp_path / "source.sqlite", target, ["paper:present", "paper:missing"])
    assert rows(target) == initial
    assert not any(s.startswith(("BEGIN IMMEDIATE", "INSERT", "DELETE", "UPDATE")) for s in statements)
    target.db.close()


def test_incident_derived_edges_do_not_restore_links_from_newer_unselected_document(tmp_path):
    selected = "paper:selected"
    unselected = "paper:unselected"
    source = Store(tmp_path / "source.sqlite")
    source.put(doc(selected, "Selected paper"))
    source.put({**doc(unselected, "Old relation"), "parent": selected})
    source.edge(unselected, "links_to", selected, unselected, {})
    source.edge(unselected, "discovered_by", selected, unselected, {"historical": True})
    source.db.commit(); source.db.close()
    target = Store(tmp_path / "target.sqlite")
    target.put(doc(unselected, "New with no relation", "2026-10-03T00:00:00Z"))
    target.db.commit()
    before = target.get(unselected)
    result = _import_corpus(tmp_path / "source.sqlite", target, [selected])
    assert result["historical_derived_edges_skipped"] == 2
    assert target.get(unselected) == before
    assert len(target.revisions(unselected)) == 1
    assert not target.db.execute("SELECT 1 FROM edges WHERE src=? AND relation IN ('links_to','child_of')", (unselected,)).fetchone()
    assert target.db.execute("SELECT 1 FROM edges WHERE src=? AND relation='discovered_by'", (unselected,)).fetchone()
    target.db.close()


def test_jsonlines_filter_rejected_whole_file_import_unchanged(tmp_path):
    path = tmp_path / "source.jsonl"
    path.write_text(json.dumps(doc("paper:one", "First")) + "\n" + json.dumps(doc("paper:two", "Second")) + "\n")
    target = Store(tmp_path / "target.sqlite")
    with pytest.raises(ValueError, match="SQLite"):
        _import_corpus(path, target, ["paper:one"])
    assert not target.db.execute("SELECT * FROM documents").fetchall()
    assert _import_corpus(path, target)["documents_seen"] == 2
    target.db.close()
