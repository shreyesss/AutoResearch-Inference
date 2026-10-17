"""Descriptive curves from completed class-aware SLA profile point files.

These are observed, in-sample load points. The plots and point-estimate
nondominance labels do not establish capacity, uncertainty, or a test result.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


POINT_FIELDS = (
    "point_id", "profile_index", "config_id", "policy_id", "scenario_id",
    "point_index", "offered_rps", "arrival_seed", "screen_status",
    "qualified_status", "reason_codes", "planned", "completed", "errors",
    "realized_rps", "output_tokens_per_s", "ttft_p50_ms", "ttft_p90_ms",
    "tpot_p50_ms", "tpot_p90_ms", "observed_feasible", "provisional_nondominated",
)
CLASS_FIELDS = (
    "point_id", "config_id", "offered_rps", "realized_rps", "class",
    "point_status", "planned", "completed", "errors", "ttft_eligible",
    "tpot_eligible", "ttft_p50_ms", "ttft_p90_ms", "tpot_p50_ms",
    "tpot_p90_ms", "observed_feasible", "reason_codes",
)


def _number(value: Any) -> float | None:
    if type(value) in (int, float) and math.isfinite(value):
        return float(value)
    return None


def _nonnegative_int(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _profile(source: Path) -> dict[str, Any]:
    data = json.loads(source.read_text())
    if (data.get("schema_version") != "sla-profile-points-v1"
            or data.get("claim") != "observed_development_points_no_confirmed_capacity"
            or data.get("capacity_confirmed") is not False
            or not isinstance(data.get("config_id"), str)
            or not isinstance(data.get("policy_id"), str)
            or not isinstance(data.get("development_scenario_id"), str)
            or not isinstance(data.get("points"), list)):
        raise ValueError(f"Not a descriptive SLA profile: {source}")
    return data


def _is_dominated(row: dict[str, Any], other: dict[str, Any]) -> bool:
    axes = ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms")
    if any(_number(row.get(axis)) is None or _number(other.get(axis)) is None for axis in axes):
        return False
    return (other["output_tokens_per_s"] >= row["output_tokens_per_s"]
            and other["ttft_p90_ms"] <= row["ttft_p90_ms"]
            and other["tpot_p90_ms"] <= row["tpot_p90_ms"]
            and any(other[axis] != row[axis] for axis in axes))


def _write_csv(path: Path, fields: tuple[str, ...], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: json.dumps(row[field], sort_keys=True)
                             if isinstance(row.get(field), (list, dict)) else row.get(field)
                             for field in fields})


def _plot(points: list[dict[str, Any]], classes: list[dict[str, Any]], out: Path) -> dict[str, str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return {"plots_status": "matplotlib_unavailable"}

    paths: dict[str, str] = {}
    valid = [p for p in points if p["qualified_status"] == "valid"]
    configs = sorted({p["config_id"] for p in points})
    panels = (
        ("realized_rps", "Realized requests/s"),
        ("output_tokens_per_s", "Output tokens/s"),
        ("ttft_p90_ms", "Aggregate TTFT p90 (ms)"),
        ("tpot_p90_ms", "Aggregate TPOT p90 (ms/token)"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for config in configs:
        selected = sorted((p for p in valid if p["config_id"] == config),
                          key=lambda p: p["offered_rps"] or -1)
        for axis, (metric, label) in zip(axes.flat, panels):
            pairs = [(p["offered_rps"], p[metric]) for p in selected
                     if p["offered_rps"] is not None and p[metric] is not None]
            if pairs:
                axis.plot([x for x, _ in pairs], [y for _, y in pairs], "o-", label=config)
            axis.set(xlabel="Offered requests/s", ylabel=label)
            axis.grid(alpha=.2)
    for axis in axes.flat:
        if axis.has_data():
            axis.legend(fontsize=7)
    fig.suptitle("Observed qualified SLA profile points; no confirmed capacity")
    fig.tight_layout()
    path = out / "load-curves.svg"
    fig.savefig(path)
    plt.close(fig)
    paths["load_curves_svg"] = str(path)

    names = sorted({r["class"] for r in classes if r["class"]})
    if names:
        fig, axes = plt.subplots(2, len(names), figsize=(max(11, 3 * len(names)), 7),
                                 squeeze=False)
        for col, name in enumerate(names):
            for config in configs:
                selected = sorted((r for r in classes if r["class"] == name
                                   and r["config_id"] == config and r["point_status"] == "valid"),
                                  key=lambda r: r["offered_rps"] or -1)
                for row, metric in enumerate(("ttft", "tpot")):
                    for percentile, style in (("p50", "--"), ("p90", "-")):
                        key = f"{metric}_{percentile}_ms"
                        pairs = [(r["offered_rps"], r[key]) for r in selected
                                 if r["offered_rps"] is not None and r[key] is not None]
                        if pairs:
                            axes[row][col].plot([x for x, _ in pairs], [y for _, y in pairs],
                                                marker="o", linestyle=style,
                                                label=f"{config} {percentile}")
                    axes[row][col].set(xlabel="Offered requests/s",
                                       ylabel=f"{metric.upper()} (ms{'/token' if metric == 'tpot' else ''})",
                                       title=name)
                    axes[row][col].grid(alpha=.2)
        for axis in axes.flat:
            if axis.has_data():
                axis.legend(fontsize=6)
        fig.suptitle("Observed per-class p50/p90; qualified points only")
        fig.tight_layout()
        path = out / "class-curves.svg"
        fig.savefig(path)
        plt.close(fig)
        paths["class_curves_svg"] = str(path)

    scatter = [p for p in valid if all(p[key] is not None for key in
               ("ttft_p90_ms", "tpot_p90_ms", "output_tokens_per_s"))]
    fig, axis = plt.subplots(figsize=(8, 5))
    for point in scatter:
        marker = "o" if point["provisional_nondominated"] else "x"
        color = "tab:green" if point["observed_feasible"] else "tab:orange"
        axis.scatter(point["ttft_p90_ms"], point["output_tokens_per_s"],
                     marker=marker, color=color)
        axis.annotate(f"{point['config_id']} @ {point['offered_rps']:g}",
                      (point["ttft_p90_ms"], point["output_tokens_per_s"]), fontsize=7)
    axis.set(xlabel="Aggregate TTFT p90 (ms; lower is better)",
             ylabel="Output tokens/s (higher is better)",
             title="Observed throughput vs latency; point estimates only")
    axis.grid(alpha=.2)
    fig.text(.08, .01, "Circle = provisional 3-axis nondominated; green = observed class-SLO feasible. "
             "TPOT p90 and all class metrics are in CSV/JSON.", fontsize=8)
    fig.tight_layout(rect=(0, .05, 1, 1))
    path = out / "throughput-latency.svg"
    fig.savefig(path)
    plt.close(fig)
    paths["throughput_latency_svg"] = str(path)
    return paths


def export_sla_curves(profile_paths: Iterable[Path], output_dir: Path) -> dict[str, Any]:
    """Export every sampled rate, class metrics, and descriptive plots.

    Multiple profiles must share the same qualified corpus and approved policy.
    Each source is hashed so later inspection can trace every plotted point.
    """
    sources = [Path(path).resolve() for path in profile_paths]
    if not sources:
        raise ValueError("At least one SLA profile is required")
    profiles = [_profile(source) for source in sources]
    identity = {(p["policy_id"], p["development_scenario_id"], p.get("policy_sha256"))
                for p in profiles}
    if len(identity) != 1:
        raise ValueError("SLA profile curves require the same policy and development corpus")
    points: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []
    for profile_index, (source, profile) in enumerate(zip(sources, profiles), 1):
        for point_index, point in enumerate(profile["points"], 1):
            if not isinstance(point, dict):
                raise ValueError(f"Malformed profile point: {source}:{point_index}")
            screen = point.get("screen") if isinstance(point.get("screen"), dict) else {}
            qualified = point.get("qualified") if isinstance(point.get("qualified"), dict) else {}
            native = qualified.get("native_summary_metrics") or {}
            assessment = qualified.get("assessment") or {}
            planned = _nonnegative_int(qualified.get("planned"))
            completed = _nonnegative_int(qualified.get("completed"))
            row = {
                "point_id": f"profile-{profile_index:02d}-point-{point_index:02d}",
                "profile_index": profile_index,
                "config_id": profile["config_id"], "policy_id": profile["policy_id"],
                "scenario_id": profile["development_scenario_id"],
                "point_index": point_index, "offered_rps": _number(point.get("rate_rps")),
                "arrival_seed": point.get("arrival_seed"),
                "screen_status": screen.get("status", "not_run"),
                "qualified_status": qualified.get("status", "not_run"),
                "reason_codes": sorted(set((screen.get("reason_codes") or [])
                                           + (qualified.get("reason_codes") or []))),
                "planned": planned, "completed": completed,
                "errors": planned - completed if planned is not None and completed is not None else None,
                "realized_rps": _number(qualified.get("realized_rate_rps")),
                "output_tokens_per_s": _number(native.get("output_tokens_per_s")),
                "ttft_p50_ms": _number(native.get("ttft_p50_ms")),
                "ttft_p90_ms": _number(native.get("ttft_p90_ms")),
                "tpot_p50_ms": _number(native.get("tpot_p50_ms")),
                "tpot_p90_ms": _number(native.get("tpot_p90_ms")),
                "observed_feasible": qualified.get("observed_feasible") is True
                                     and qualified.get("status") == "valid",
                "provisional_nondominated": False,
            }
            points.append(row)
            for name, result in sorted((assessment.get("classes") or {}).items()):
                diag = result.get("diagnostic_percentiles_ms") or {}
                count = _nonnegative_int(result.get("planned"))
                done = _nonnegative_int(result.get("completed"))
                class_rows.append({
                    "point_id": row["point_id"], "config_id": row["config_id"],
                    "offered_rps": row["offered_rps"], "realized_rps": row["realized_rps"],
                    "class": name, "point_status": row["qualified_status"],
                    "planned": count, "completed": done,
                    "errors": count - done if count is not None and done is not None else None,
                    "ttft_eligible": result.get("ttft_eligible"),
                    "tpot_eligible": result.get("tpot_eligible"),
                    "ttft_p50_ms": _number((diag.get("ttft") or {}).get("p50")),
                    "ttft_p90_ms": _number((diag.get("ttft") or {}).get("p90")),
                    "tpot_p50_ms": _number((diag.get("tpot") or {}).get("p50")),
                    "tpot_p90_ms": _number((diag.get("tpot") or {}).get("p90")),
                    "observed_feasible": result.get("observed_feasible") is True,
                    "reason_codes": result.get("reason_codes") or [],
                })
    comparable = [p for p in points if p["qualified_status"] == "valid" and
                  all(p[key] is not None for key in
                      ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms"))]
    for row in comparable:
        row["provisional_nondominated"] = not any(
            _is_dominated(row, other) for other in comparable if other is not row)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_records = [{"path": str(source),
                       "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "config_id": profile["config_id"],
                       "point_count": len(profile["points"]),
                       "stop_reason": profile.get("stop_reason"),
                       "profile_spec": profile.get("spec")}
                      for source, profile in zip(sources, profiles)]
    report = {
        "schema_version": "descriptive-sla-curves-v1",
        "claim": "observed_in_sample_points_only_no_confirmed_capacity_or_frontier",
        "policy_id": profiles[0]["policy_id"],
        "development_scenario_id": profiles[0]["development_scenario_id"],
        "sources": source_records, "points": points, "class_points": class_rows,
        "provisional_nondominated_definition":
            "Complete valid qualified point estimates: maximize aggregate output tokens/s; "
            "minimize aggregate TTFT p90 and TPOT p90. Different Poisson seeds, no uncertainty "
            "adjustment; this is not a capacity or confirmed Pareto claim.",
        "provisional_nondominated_point_ids":
            [p["point_id"] for p in comparable if p["provisional_nondominated"]],
        "observed_feasible_point_ids":
            [p["point_id"] for p in points if p["observed_feasible"]],
    }
    json_path = output_dir / "sla-curves.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    points_csv = output_dir / "sla-curve-points.csv"
    class_csv = output_dir / "sla-curve-class-points.csv"
    _write_csv(points_csv, POINT_FIELDS, points)
    _write_csv(class_csv, CLASS_FIELDS, class_rows)
    paths = _plot(points, class_rows, output_dir)
    return {"report_json": str(json_path), "points_csv": str(points_csv),
            "class_points_csv": str(class_csv), **paths,
            "point_count": len(points), "class_point_count": len(class_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", action="append", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_sla_curves(args.profile, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
