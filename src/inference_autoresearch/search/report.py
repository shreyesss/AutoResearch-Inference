"""Compatibility-scoped point-estimate Pareto exports; confirmation stays separate."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections import Counter
from pathlib import Path
from typing import Any

OBJECTIVES = ("output_tokens_per_s", "ttft_p99_ms", "tpot_p99_ms")


def eligible(row: dict[str, Any]) -> bool:
    counts = row.get("counts", {})
    metrics = row.get("metrics", {})
    return (row.get("status") == "valid" and row.get("behavior") == "normal"
            and row.get("evidence_grade") != "ineligible"
            and not row.get("controller_validation")
            and counts.get("planned") == counts.get("completed") == counts.get("dispatched")
            and all(counts.get(key) == 0 for key in
                    ("not_dispatched", "failed", "timed_out", "canceled", "censored"))
            and all(isinstance(metrics.get(k), (int, float)) for k in OBJECTIVES))


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    am, bm = a["metrics"], b["metrics"]
    weak = (am["output_tokens_per_s"] >= bm["output_tokens_per_s"]
            and am["ttft_p99_ms"] <= bm["ttft_p99_ms"]
            and am["tpot_p99_ms"] <= bm["tpot_p99_ms"])
    strict = any(am[k] != bm[k] for k in OBJECTIVES)
    return weak and strict


def pareto_front(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [r for r in rows if eligible(r)]
    scopes = {tuple(str(row.get(key, "")) for key in ("scenario_id", "offered_load", "load_unit",
                "cache_protocol", "stage", "measurement_protocol")) for row in valid}
    if len(scopes) > 1:
        raise ValueError("Pareto points require one compatible exact-load/protocol scope")
    return [r for r in valid if not any(dominates(other, r) for other in valid if other is not r)]


def export(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    """Group by exact scenario/load/protocol/stage; never average p99s."""
    output_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row.get(k, "")) for k in
                    ("scenario_id", "offered_load", "load_unit", "cache_protocol", "stage", "measurement_protocol"))
        groups[key].append(row)
    fronts = []
    for key, members in sorted(groups.items()):
        front = pareto_front(members)
        fronts.append({"scope": dict(zip(("scenario_id", "offered_load", "load_unit", "cache_protocol",
                                              "stage", "measurement_protocol"), key)),
                       "members": front, "ineligible": len(members) - sum(eligible(x) for x in members)})
    json_path = output_dir / "fronts.json"
    json_path.write_text(json.dumps(fronts, indent=2, sort_keys=True) + "\n")
    csv_path = output_dir / "points.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scenario_id", "config_id", "stage", "status",
                         "behavior", "evidence_grade", *OBJECTIVES, "front_member"])
        writer.writeheader()
        for members in groups.values():
            front_ids = {id(r) for r in pareto_front(members)}
            for r in members:
                writer.writerow({"scenario_id": r.get("scenario_id"), "config_id": r.get("config_id"),
                    "stage": r.get("stage"), "status": r.get("status"), "behavior": r.get("behavior"),
                    "evidence_grade": r.get("evidence_grade"),
                    **{k: r.get("metrics", {}).get(k) for k in OBJECTIVES},
                    "front_member": id(r) in front_ids})
    summary = {
        "total_cells": len(rows), "status_counts": dict(Counter(str(r.get("status")) for r in rows)),
        "behavior_counts": dict(Counter(str(r.get("behavior")) for r in rows)),
        "eligible_cells": sum(eligible(r) for r in rows),
        "reason_counts": dict(Counter(reason for r in rows for reason in r.get("reason_codes", []))),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    plot_paths = _plots(groups, output_dir)
    return {"fronts_json": str(json_path), "points_csv": str(csv_path),
            "summary_json": str(summary_path), **plot_paths}


def _plots(groups: dict[tuple[str, ...], list[dict[str, Any]]], output_dir: Path) -> dict[str, str]:
    """SVG graphics use only clean, compatible point estimates; missing plots are explicit."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return {"plots_status": "matplotlib_unavailable"}
    paths: dict[str, str] = {}
    baseline_curve: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for index, (scope, members) in enumerate(sorted(groups.items()), 1):
        valid = [row for row in members if eligible(row)]
        if not valid:
            continue
        front_ids = {id(row) for row in pareto_front(valid)}
        fig, ax = plt.subplots(figsize=(7, 5))
        last_scatter = None
        for row in valid:
            m = row["metrics"]
            last_scatter = ax.scatter(m["ttft_p99_ms"], m["output_tokens_per_s"],
                       c=m["tpot_p99_ms"], cmap="viridis", vmin=min(x["metrics"]["tpot_p99_ms"] for x in valid),
                       vmax=max(x["metrics"]["tpot_p99_ms"] for x in valid) + 1e-9,
                       marker="o" if id(row) in front_ids else "x", s=70)
            ax.annotate(str(row.get("config_id", ""))[:8],
                        (m["ttft_p99_ms"], m["output_tokens_per_s"]), fontsize=7)
            if row.get("is_baseline"):
                try:
                    baseline_curve[str(row.get("workload_group_id") or scope[0])].append(
                        (float(scope[1]), float(m["output_tokens_per_s"])))
                except ValueError:
                    pass
        if last_scatter is not None:
            fig.colorbar(last_scatter, ax=ax, label="TPOT p99 (ms/token; lower is better)")
        ax.set(xlabel="TTFT p99 (ms; lower is better)",
               ylabel="Finite-run output tokens/s (higher is better)",
               title=f"Provisional: {scope[0]} · load {scope[1]} {scope[2]} · {scope[4]}")
        ax.grid(alpha=.2)
        note = "Marker o: exact point front; x: dominated. TPOT p99 in points.csv."
        fig.text(.02, .01, note, fontsize=8)
        fig.tight_layout(rect=(0, .04, 1, 1))
        plot_path = output_dir / f"pareto-{index:03d}.svg"
        fig.savefig(plot_path)
        plt.close(fig)
        paths[f"pareto_{index:03d}"] = str(plot_path)
    if baseline_curve:
        fig, ax = plt.subplots(figsize=(7, 5))
        for scenario, points in baseline_curve.items():
            points.sort()
            ax.plot([x for x, _ in points], [y for _, y in points], marker="o", label=scenario)
        ax.set(xlabel="Offered load (scope unit in fronts.json)", ylabel="Finite-run output tokens/s",
               title="B0 observed load curve")
        ax.legend()
        ax.grid(alpha=.2)
        fig.tight_layout()
        path = output_dir / "b0-load-curve.svg"
        fig.savefig(path)
        plt.close(fig)
        paths["b0_load_curve_svg"] = str(path)
    return paths


def export_history(ledger: Any, campaign_id: str, output_dir: Path) -> dict[str, str]:
    """Human-readable and machine-readable proposal/feedback trail."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output: dict[str, str] = {}
    for kind in ("proposal", "feedback", "evaluation", "search_error", "search_stop"):
        rows = [{"seq": event["seq"], "utc": event["utc"], "entity_id": event["entity_id"],
                 "payload": event["payload"]} for event in ledger.events(campaign_id, kind)]
        path = output_dir / f"{kind}.json"
        path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
        output[kind] = str(path)
    summary = json.loads((output_dir / "summary.json").read_text()) if (output_dir / "summary.json").is_file() else {}
    lines = [f"# Campaign {campaign_id}", "", "All plotted points are observed point estimates; screens are provisional.", "",
             f"Cells: {summary.get('total_cells', 0)}; frontier-eligible: {summary.get('eligible_cells', 0)}.",
             f"Statuses: {summary.get('status_counts', {})}.",
             f"Behaviors: {summary.get('behavior_counts', {})}.",
             f"Failures/reasons: {summary.get('reason_counts', {})}.", "",
             "See fronts.json for exact compatible-load nondominance, points.csv for B0 and dominated points,",
             "feedback.json for matched-B0 deltas, and ledger.sqlite3 for append-only events."]
    path = output_dir / "REPORT.md"
    path.write_text("\n".join(lines) + "\n")
    output["markdown"] = str(path)
    return output
