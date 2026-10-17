"""The unattended B0 continuation must wait for complete source shutdown."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "infra/wait_and_run_v3_matched_b0.py"


def module():
    spec = importlib.util.spec_from_file_location("v3_b0_waiter", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gate(checkpoint, *, tmux_alive):
    return module().gate(checkpoint, tmux_alive=tmux_alive)


def test_waiter_never_starts_before_shutdown_and_tmux_exit():
    assert gate(None, tmux_alive=True)[0] == "waiting"
    assert gate({"status": "running"}, tmux_alive=True)[0] == "waiting"
    qualified = {"status": "development_inputs_qualified"}
    assert gate(qualified, tmux_alive=False)[0] == "waiting"
    qualified["b0_stop_exit_code"] = 0
    assert gate(qualified, tmux_alive=True)[0] == "waiting"
    assert gate(qualified, tmux_alive=False)[0] == "ready"


def test_waiter_stops_on_failed_input_gate_or_shutdown():
    assert gate({"status": "blocked", "error": "class quota failed"}, tmux_alive=False)[0] == "blocked"
    assert gate({"status": "development_inputs_qualified", "b0_stop_exit_code": 1},
                tmux_alive=False)[0] == "blocked"


def test_missing_source_timer_resets_only_when_source_returns_or_gate_passes():
    track = module().absent_source_since
    assert track(None, decision="waiting", tmux_alive=False, clock=100) == 100
    assert track(100, decision="waiting", tmux_alive=False, clock=120) == 100
    assert track(100, decision="waiting", tmux_alive=True, clock=120) is None
    assert track(100, decision="ready", tmux_alive=False, clock=120) is None
