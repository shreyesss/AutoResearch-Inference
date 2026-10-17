"""Compatibility-scoped point-estimate Pareto exports; confirmation stays separate."""

from __future__ import annotations

import csv
import json
import math
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
            and all(isinstance(metrics.get(k), (int, float)) and not isinstance(metrics.get(k), bool)
                    and math.isfinite(metrics[k]) for k in OBJECTIVES))


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


def export(rows: list[dict[str, Any]], output_dir: Path,
           screen_scenario_ids: list[str] | None = None) -> dict[str, str]:
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
    suite_paths = (export_suite_front(rows, screen_scenario_ids, output_dir)
                   if screen_scenario_ids is not None else {})
    return {"fronts_json": str(json_path), "points_csv": str(csv_path),
            "summary_json": str(summary_path), **plot_paths, **suite_paths}


def _suite_dominates(a: dict[str, Any], b: dict[str, Any], scenario_ids: list[str]) -> bool:
    """Point dominance across every task metric, with no cross-task averaging."""
    weak = True
    strict = False
    for scenario_id in scenario_ids:
        for metric in OBJECTIVES:
            av = a["metrics"][scenario_id][metric]
            bv = b["metrics"][scenario_id][metric]
            better_or_equal = av >= bv if metric == "output_tokens_per_s" else av <= bv
            weak &= better_or_equal
            strict |= av != bv
    return weak and strict


def export_suite_front(rows: list[dict[str, Any]], scenario_ids: list[str],
                       output_dir: Path) -> dict[str, str]:
    """Export complete-config fronts at each exact screen measurement protocol.

    Every config, including a triage-only or failed one, remains inspectable. A
    config enters dominance only with exactly one eligible cell for each task at
    the B0-anchored task load and cache protocol.
    """
    if len(scenario_ids) != 4 or len(set(scenario_ids)) != 4:
        raise ValueError("suite frontier requires four distinct screen scenarios")
    output_dir.mkdir(parents=True, exist_ok=True)
    expected = set(scenario_ids)
    relevant = [r for r in rows if r.get("scenario_id") in expected and r.get("config_id")]
    config_ids = sorted({str(r["config_id"]) for r in relevant})
    protocols = sorted({str(r.get("measurement_protocol", "")) for r in relevant
                        if r.get("stage") == "screen"}) or ["fresh-server-cell-v1"]
    scopes: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []
    for protocol in protocols:
        screen = [r for r in relevant if r.get("stage") == "screen"
                  and str(r.get("measurement_protocol", "")) == protocol]
        expected_scopes: dict[str, tuple[str, str, str] | None] = {}
        scope_reasons: list[str] = []
        for scenario_id in scenario_ids:
            members = [r for r in screen if r.get("scenario_id") == scenario_id]
            b0 = [r for r in members if r.get("is_baseline") is True]
            source = b0 or members
            values = {tuple(str(r.get(k, "")) for k in
                            ("offered_load", "load_unit", "cache_protocol")) for r in source}
            expected_scopes[scenario_id] = next(iter(values)) if len(values) == 1 else None
            if not values:
                scope_reasons.append(f"{scenario_id}:missing_screen_scope")
            elif len(values) > 1:
                scope_reasons.append(f"{scenario_id}:ambiguous_screen_scope")
        configurations = []
        for config_id in config_ids:
            config_rows = [r for r in relevant if str(r["config_id"]) == config_id]
            cells: dict[str, str] = {}
            metrics: dict[str, dict[str, float]] = {}
            reasons = list(scope_reasons)
            for scenario_id in scenario_ids:
                members = [r for r in screen if str(r["config_id"]) == config_id
                           and r.get("scenario_id") == scenario_id]
                required = expected_scopes[scenario_id]
                matched = [r for r in members if required is not None and
                           tuple(str(r.get(k, "")) for k in
                                 ("offered_load", "load_unit", "cache_protocol")) == required]
                valid = [r for r in matched if eligible(r)]
                if not members:
                    reasons.append(f"{scenario_id}:missing_screen_cell")
                elif not matched:
                    reasons.append(f"{scenario_id}:incompatible_load_or_cache")
                elif len(valid) != 1:
                    reasons.append(f"{scenario_id}:" +
                                   ("duplicate_eligible_cells" if len(valid) > 1 else "no_eligible_cell"))
                if len(valid) == 1:
                    cells[scenario_id] = str(valid[0].get("cell_id", ""))
                    metrics[scenario_id] = {key: valid[0]["metrics"][key] for key in OBJECTIVES}
            configurations.append({"config_id": config_id,
                                   "is_baseline": any(r.get("is_baseline") is True for r in config_rows),
                                   "status": "incomplete" if reasons else "eligible",
                                   "reason_codes": reasons, "cell_ids": cells,
                                   "metrics": metrics, "dominated_by": []})
        complete = [item for item in configurations if item["status"] == "eligible"]
        for item in complete:
            item["dominated_by"] = [other["config_id"] for other in complete
                                    if other is not item and _suite_dominates(other, item, scenario_ids)]
            item["status"] = "dominated" if item["dominated_by"] else "frontier"
        for item in configurations:
            flat: dict[str, Any] = {"config_id": item["config_id"], "stage": "screen",
                                    "measurement_protocol": protocol,
                                    "is_baseline": item["is_baseline"], "status": item["status"],
                                    "reason_codes": ";".join(item["reason_codes"]),
                                    "dominated_by": ";".join(item["dominated_by"])}
            for scenario_id in scenario_ids:
                flat[f"{scenario_id}.cell_id"] = item["cell_ids"].get(scenario_id, "")
                for metric in OBJECTIVES:
                    flat[f"{scenario_id}.{metric}"] = item["metrics"].get(scenario_id, {}).get(metric, "")
            csv_rows.append(flat)
        scopes.append({"stage": "screen", "measurement_protocol": protocol,
                       "scenario_scopes": {scenario_id: dict(zip(
                           ("offered_load", "load_unit", "cache_protocol"), scope)) if scope else None
                           for scenario_id, scope in expected_scopes.items()},
                       "front_config_ids": [item["config_id"] for item in configurations
                                            if item["status"] == "frontier"],
                       "configurations": configurations})
    result = {"schema_version": "suite-front-v1", "scenario_ids": scenario_ids,
              "objectives": [{"scenario_id": scenario_id, "metric": metric,
                              "direction": "maximize" if metric == "output_tokens_per_s" else "minimize"}
                             for scenario_id in scenario_ids for metric in OBJECTIVES],
              "scopes": scopes}
    json_path = output_dir / "suite-front.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    fieldnames = ["config_id", "stage", "measurement_protocol", "is_baseline", "status",
                  "reason_codes", "dominated_by"] + [
                      key for scenario_id in scenario_ids
                      for key in [f"{scenario_id}.cell_id"] +
                      [f"{scenario_id}.{metric}" for metric in OBJECTIVES]]
    csv_path = output_dir / "suite-front.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    return {"suite_front_json": str(json_path), "suite_front_csv": str(csv_path)}


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
    if (output_dir / "suite-front.json").is_file():
        lines += ["", "See suite-front.json and suite-front.csv for the four-task config frontier,",
                  "including B0, dominated configs, and incomplete configs with exclusion reasons."]
    path = output_dir / "REPORT.md"
    path.write_text("\n".join(lines) + "\n")
    output["markdown"] = str(path)
    return output
