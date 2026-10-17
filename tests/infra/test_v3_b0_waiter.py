"""The unattended B0 continuation must wait for complete source shutdown."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "infra/wait_and_run_v3_matched_b0.py"


def gate(checkpoint, *, tmux_alive):
    spec = importlib.util.spec_from_file_location("v3_b0_waiter", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.gate(checkpoint, tmux_alive=tmux_alive)


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
