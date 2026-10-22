"""Known local validation is actionable without exposing arbitrary error text."""
import json

import pytest

from ideation.foundation import UnsupportedDeferSnapshotError, invoke, main


@pytest.mark.parametrize("command", [["init"], ["refresh"], ["backfill", "start"]])
@pytest.mark.parametrize("existing", [False, True])
def test_unsupported_defer_is_safe_and_precedes_all_side_effects(
    tmp_path, monkeypatch, capsys, command, existing
):
    root = tmp_path / "state"
    if existing:
        root.mkdir()
        (root / "sentinel").write_bytes(b"preserve existing state")
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def forbidden(*args, **kwargs):
        raise AssertionError("Unsupported flags must fail before environment loading or locking")

    monkeypatch.setattr("ideation.foundation._locked", forbidden)
    monkeypatch.setattr("ideation.providers.load_provider_env", forbidden)
    argv = ["--state-dir", str(root), "--env-file", "unused-secret-path", "--defer-snapshot", *command]
    with pytest.raises(UnsupportedDeferSnapshotError) as caught:
        invoke(argv)
    assert caught.value.error_code == "unsupported_defer_snapshot"
    assert main(argv) == 1
    output = capsys.readouterr()
    assert not output.out
    error = json.loads(output.err)
    assert error["error_code"] == "unsupported_defer_snapshot"
    assert "Remove --defer-snapshot" in error["message"]
    assert "unused-secret-path" not in output.err
    assert root.exists() == existing
    assert {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


def test_unrelated_value_error_text_remains_redacted(tmp_path, monkeypatch, capsys):
    secret = "https://provider.invalid/?api_key=must-not-appear"

    def fail(*args, **kwargs):
        raise ValueError(secret)

    monkeypatch.setattr("ideation.foundation.invoke", fail)
    assert main(["--state-dir", str(tmp_path / "state"), "init"]) == 1
    output = capsys.readouterr()
    error = json.loads(output.err)
    assert error["error_type"] == "ValueError"
    assert "error_code" not in error
    assert secret not in output.err
    assert "must-not-appear" not in output.err


@pytest.mark.parametrize("status,hits,exit_code", [
    ("failed", [], 1),
    ("completed", [], 0),
    ("completed", [{"id": "arxiv:fixture"}], 0),
    ("partial", [{"id": "arxiv:fixture"}], 0),
])
def test_paper_cli_retains_receipt_and_distinguishes_failed_from_empty(
    monkeypatch, capsys, status, hits, exit_code
):
    receipt = {"status": status, "hits": hits, "snapshot": {"id": "retained"}}
    monkeypatch.setattr("ideation.foundation.invoke", lambda argv: receipt)
    assert main(["paper-search", "normalization inference"]) == exit_code
    output = capsys.readouterr()
    assert json.loads(output.out) == receipt
    assert output.err == ""
