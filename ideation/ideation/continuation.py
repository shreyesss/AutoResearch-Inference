"""Immutable research handoffs joining the human register and model memory.

This records state and detects stale inputs. It does not infer experimental
outcomes from prose, schedule jobs, or grant permission to rerun a held idea.
"""
import hashlib
import json
import re
from pathlib import Path

from .evidence import new_output, write_json
from .research import read_brief
from .store import now


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_context(path, check=True):
    path = Path(path).resolve()
    context = json.loads(path.read_text())
    if context.get("version") != 1:
        raise ValueError("Unsupported continuation version")
    if check:
        problems = []
        for item in context["inputs"]:
            original = Path(item["path"])
            frozen = path.parent / item["snapshot"]
            if not frozen.is_file() or sha(frozen.read_bytes()) != item["sha256"]:
                problems.append("snapshot integrity: " + item["path"])
            if not original.is_file() or sha(original.read_bytes()) != item["sha256"]:
                problems.append("changed input: " + item["path"])
        if problems:
            raise ValueError("Stale continuation; prepare a new handoff with previous= this path: " + "; ".join(problems))
    return context


def prompt_context(context):
    return {key: context[key] for key in ("created_at", "families", "state", "changes", "rules")}


class ContinuationTools:
    def __init__(self, hypotheses):
        self.hypotheses = hypotheses

    def prepare(self, brief, output, register="hypotheses", state=None, artifacts=None, previous=None):
        """Freeze all register families, explicit state/next actions and bounded DB recall; previous gives a delta."""
        brief_value = brief if isinstance(brief, dict) else read_brief(brief)
        root = Path(register).resolve()
        index = root / "README.md"
        if not index.is_file():
            raise ValueError("Missing hypothesis register README.md")
        state_value = json.loads(Path(state).read_text()) if state else {"decisions": [], "next_actions": []}
        families = []
        files = [index]
        for line in index.read_text().splitlines():
            if not re.match(r"\|\s*[A-Z]\d+\s*\|", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 4:
                raise ValueError("Expected four register columns: " + line)
            identity, title, status, result = cells
            match = re.search(r"\]\(([^)]+)\)", title)
            if not match:
                raise ValueError("Missing family-card link: " + identity)
            card = (root / match.group(1)).resolve()
            if card.parent != root or not card.is_file():
                raise ValueError("Invalid family-card path: " + identity)
            files.append(card)
            families.append({"family_id": identity, "title": title, "selection_or_execution_state": status,
                             "reported_result": result, "path": str(card),
                             "detail": "Full card is frozen in inputs; register labels are not normalized experimental verdicts."})
        ids = [x["family_id"] for x in families]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("Empty or duplicate register families")
        decisions = state_value.get("decisions", [])
        for decision in decisions:
            if decision.get("family_id") not in ids:
                raise ValueError("Unknown family in continuation decision")
            if decision.get("action") not in {"hold", "await_result", "investigate", "reopen"}:
                raise ValueError("Invalid continuation action")
            if not decision.get("reason"):
                raise ValueError("Continuation decisions need reasons")
            if decision["action"] == "reopen" and (not decision.get("new_evidence") or not decision.get("scope_delta")):
                raise ValueError("Reopening requires new evidence and an explicit scope/mechanism delta")
            files.extend(Path(p).resolve() for p in decision.get("artifacts", []))
        files.extend(Path(p).resolve() for p in (artifacts or []))
        files.extend(Path(p).resolve() for p in brief_value.get("prior_decisions", []) if Path(p).is_file())
        if state:
            files.append(Path(state).resolve())
        if isinstance(brief, str):
            files.append(Path(brief).resolve())
        # Read everything before making the output, so missing inputs leave no partial handoff.
        captured = {str(p): p.read_bytes() for p in dict.fromkeys(files)}
        old = load_context(previous, check=False) if previous else None
        old_hashes = {p["path"]: p["sha256"] for p in old["inputs"]} if old else {}
        hashes = {p: sha(data) for p, data in captured.items()}
        changes = {"added": sorted(set(hashes) - set(old_hashes)),
                   "removed": sorted(set(old_hashes) - set(hashes)),
                   "modified": sorted(p for p in hashes.keys() & old_hashes.keys() if hashes[p] != old_hashes[p])}
        out = new_output(output)
        (out / "inputs").mkdir()
        inputs = []
        for number, (path, data) in enumerate(captured.items()):
            relative = f"inputs/{number:03d}-{Path(path).name}"
            (out / relative).write_bytes(data)
            inputs.append({"path": path, "snapshot": relative, "sha256": hashes[path], "bytes": len(data)})
        context = {"version": 1, "created_at": now(), "brief": brief_value, "inputs": inputs,
                   "families": families, "state": state_value, "changes": changes,
                   "previous": {"path": str(Path(previous).resolve()), "sha256": sha(Path(previous).read_bytes())} if previous else None,
                   "rules": ["Carry every family state; DB recall alone is incomplete.",
                             "A policy change does not erase an unfavorable experiment.",
                             "Held ideas require a specific new-evidence or mechanism/scope reason to reopen.",
                             "Pending experiments stay pending; do not duplicate their runtime work.",
                             "Acceptance is research/test-design eligibility, never a measured speedup or execution approval."]}
        write_json(out / "continuation.json", context)
        write_json(out / "memory.json", self.hypotheses.ledger.recall(brief_value, limit=30, max_chars=40000))
        return {"path": str(out / "continuation.json"), "families": len(families), "changes": changes,
                "execution_authorized": False}

    def check(self, path):
        """Verify frozen bytes and current inputs before resuming; stale handoffs need a new revision."""
        value = load_context(path)
        return {"valid": True, "families": len(value["families"]), "created_at": value["created_at"]}
