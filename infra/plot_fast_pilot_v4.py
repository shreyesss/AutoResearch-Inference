#!/usr/bin/env python3
"""Plot observed latency curves and Pareto points from the completed v4 run."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / ".artifacts/fast-pilot-v4"
CURVE = PILOT / "operator-curve-32x3"
OUT = PILOT / "analysis"
PUBLISH = ROOT / "results/2026-10-18-fast-pilot-v4"
PERCENTILES = ("p50", "p90", "p99")
METRICS = ("ttft", "tpot")
LABELS = {
    "B0": "B0",
    "pilot-v4-batch4096-a0001": "batch 4096",
    "pilot-v4-graph64-a0002": "graph 64",
    "pilot-v4-batch16384-a0003": "batch 16384",
    "pilot-v4-asyncfalse-a0004": "async off",
    "pilot-v4-eagertrue-a0005": "eager on",
    "pilot-v4-batch2048-a0006": "batch 2048",
    "pilot-v4-gpu-memory-085-attempt-0007": "GPU mem .85",
    "pilot-v4-graph64-memory085-a0008": "graph64 + mem .85",
}
COLORS = {"B0": "#17365d", "pilot-v4-batch4096-a0001": "#e07a22",
          "pilot-v4-gpu-memory-085-attempt-0007": "#7a4eab"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def save_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pareto_flags(rows: list[dict]) -> list[bool]:
    """Maximize output tokens/s; minimize p90 TTFT and p90 TPOT."""
    values = [(float(r["output_tokens_per_s"]), float(r["ttft_p90_ms"]),
               float(r["tpot_p90_ms"])) for r in rows]
    flags = []
    for i, (throughput, ttft, tpot) in enumerate(values):
        dominated = any(
            j != i and other_throughput >= throughput and other_ttft <= ttft
            and other_tpot <= tpot
            and (other_throughput > throughput or other_ttft < ttft or other_tpot < tpot)
            for j, (other_throughput, other_ttft, other_tpot) in enumerate(values))
        flags.append(not dominated)
    return flags


def load_screen() -> list[dict]:
    source = PILOT / "all-screen-points.csv"
    rows = read_csv(source)
    if len(rows) != 9 or any(r["status"] != "valid" for r in rows):
        raise ValueError("expected B0 plus eight valid proposal screens")
    return [{**r, "short_label": LABELS[r["label"]],
             **{f"{k}_ms": float(r[f"{k}_ms"]) for k in
                (f"{metric}_{percentile}" for metric in METRICS for percentile in PERCENTILES)},
             "output_tokens_per_s": float(r["output_tokens_per_s"])} for r in rows]


def load_curve() -> list[dict]:
    status = json.loads((CURVE / "run-status.json").read_text())
    if status.get("status") != "complete":
        raise ValueError("operator-curve run is incomplete")
    source = json.loads((CURVE / "all-points.json").read_text())
    points = source["points"]
    if len(points) != 9:
        raise ValueError("expected three configurations times three rates")
    rows = []
    for point in points:
        trial = point["trial"]
        if trial["status"] != "valid" or trial["completed"] != 32 or trial["planned"] != 32:
            raise ValueError(f"invalid or incomplete point: {point['label']} {point['rate_rps']}")
        summary_path = Path(point["trial_path"]).parent / "aiperf/profile_export_aiperf.json"
        summary = json.loads(summary_path.read_text())
        row = {"label": point["label"], "short_label": LABELS[point["label"]],
               "config_id": point["config_id"], "offered_rps": float(point["rate_rps"]),
               "realized_rps": float(trial["realized_rate_rps"]),
               "output_tokens_per_s": float(trial["native_summary_metrics"]["output_tokens_per_s"]),
               "planned": trial["planned"], "completed": trial["completed"],
               "class_metrics": trial["class_metrics"],
               "summary_path": str(summary_path.relative_to(ROOT)), "summary_sha256": sha(summary_path)}
        for metric, native in (("ttft", "time_to_first_token"), ("tpot", "inter_token_latency")):
            for percentile in PERCENTILES:
                key = f"{metric}_{percentile}_ms"
                row[key] = float(summary[native][percentile])
                prior = trial["native_summary_metrics"].get(key)
                if prior is not None and abs(row[key] - float(prior)) > 1e-6:
                    raise ValueError(f"summary and trial disagree: {point['label']} {key}")
        rows.append(row)
    return rows


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    fig.savefig(OUT / f"{name}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_curves(rows: list[dict], metric: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharex=True)
    unit = "s" if metric == "ttft" else "ms/token"
    factor = 1000.0 if metric == "ttft" else 1.0
    title = "Time to first token" if metric == "ttft" else "Time per output token"
    for ax, percentile in zip(axes, PERCENTILES):
        for label in ("B0", "pilot-v4-batch4096-a0001", "pilot-v4-gpu-memory-085-attempt-0007"):
            series = sorted((r for r in rows if r["label"] == label), key=lambda r: r["offered_rps"])
            ax.plot([r["offered_rps"] for r in series],
                    [r[f"{metric}_{percentile}_ms"] / factor for r in series],
                    marker="o", linewidth=2.2, color=COLORS[label], label=LABELS[label])
        ax.set_title(percentile.upper())
        ax.set_xticks([0.2, 0.4, 0.8])
        ax.set_xlabel("Configured offered requests/s")
        ax.set_ylabel(f"{title} ({unit})")
        ax.grid(alpha=0.25)
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle(f"{title}: 32 requests per point, 8 per class")
    fig.text(0.5, -0.01,
             "Only B0 and two finalists received three-rate measurements. p99 is descriptive with 32 samples.",
             ha="center", fontsize=9)
    fig.tight_layout()
    save_figure(fig, f"operator-{metric}-p50-p90-p99")


def plot_screen(rows: list[dict]) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(17, 8.5), sharex=True)
    names = [r["short_label"] for r in rows]
    x = list(range(len(rows)))
    for i, metric in enumerate(METRICS):
        factor = 1000.0 if metric == "ttft" else 1.0
        unit = "s" if metric == "ttft" else "ms/token"
        for j, percentile in enumerate(PERCENTILES):
            ax = axes[i][j]
            values = [r[f"{metric}_{percentile}_ms"] / factor for r in rows]
            colors = ["#17365d" if r["label"] == "B0" else "#899ba9" for r in rows]
            ax.bar(x, values, color=colors)
            ax.set_title(f"{metric.upper()} {percentile.upper()}")
            ax.set_ylabel(unit)
            ax.grid(axis="y", alpha=0.25)
            ax.set_xticks(x, names, rotation=42, ha="right", fontsize=8)
    fig.suptitle("All eight proposals plus B0 at the 36-request fixed screen")
    fig.text(0.5, -0.01,
             "These are single-load diagnostics at configured 0.4 requests/s; class tails and small deltas are unstable.",
             ha="center", fontsize=9)
    fig.tight_layout()
    save_figure(fig, "screen-all-configs-p50-p90-p99")


def plot_pareto(rows: list[dict], flags: list[bool], name: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(13, 6))
    legend_lines = []
    for index, (row, frontier) in enumerate(zip(rows, flags), 1):
        label = row["short_label"] + (f" @ {row['offered_rps']:.1f}" if "offered_rps" in row else "")
        marker_size = 70 + row["tpot_p90_ms"] * 0.7
        if frontier:
            ax.scatter(row["output_tokens_per_s"], row["ttft_p90_ms"] / 1000,
                       s=marker_size, marker="o", color="#2b7a57",
                       edgecolors="#154d35", linewidths=1.5)
        else:
            ax.scatter(row["output_tokens_per_s"], row["ttft_p90_ms"] / 1000,
                       s=marker_size, marker="x", color="#9e4853", linewidths=2)
        offsets = ((0, 13), (0, -15), (20, 0), (-20, 0), (15, 13), (-15, -13),
                   (25, -10), (-25, 10), (0, 22))
        ax.annotate(str(index), (row["output_tokens_per_s"], row["ttft_p90_ms"] / 1000),
                    xytext=offsets[index - 1], textcoords="offset points",
                    ha="center", va="center", fontsize=9, weight="bold")
        legend_lines.append(f"{index}. {'Pareto' if frontier else 'dominated':9s} {label}")
    ax.set_xlabel("Output tokens/s — higher is better")
    ax.set_ylabel("p90 TTFT (s) — lower is better")
    ax.set_title(title)
    ax.grid(alpha=0.25)
    fig.subplots_adjust(right=0.7)
    fig.text(0.72, 0.83, "\n".join(legend_lines), va="top", fontsize=9, family="monospace")
    fig.text(0.48, -0.01,
             "Filled green = observed 3-objective Pareto; red x = dominated. Marker size grows with p90 TPOT (worse).",
             ha="center", fontsize=9)
    save_figure(fig, name)


def plot_class_p90(rows: list[dict]) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(17, 8), sharex=True)
    for col, request_class in enumerate(("chat", "agent", "code", "document")):
        for row_index, metric in enumerate(METRICS):
            ax = axes[row_index][col]
            factor = 1000.0 if metric == "ttft" else 1.0
            for label in ("B0", "pilot-v4-batch4096-a0001", "pilot-v4-gpu-memory-085-attempt-0007"):
                series = sorted((r for r in rows if r["label"] == label), key=lambda r: r["offered_rps"])
                ax.plot([r["offered_rps"] for r in series],
                        [r["class_metrics"][request_class][f"{metric}_p90_ms"] / factor for r in series],
                        marker="o", linewidth=2, color=COLORS[label], label=LABELS[label])
            ax.set_title(f"{request_class}: {metric.upper()} p90")
            ax.set_xticks([0.2, 0.4, 0.8])
            ax.set_xlabel("Offered requests/s")
            ax.set_ylabel("s" if metric == "ttft" else "ms/token")
            ax.grid(alpha=0.25)
    axes[0][0].legend(frameon=False)
    fig.suptitle("Per-class p90 curves: 8 requests per class and rate")
    fig.text(0.5, -0.01, "These per-class tails are diagnostics, not reliable SLA estimates.",
             ha="center", fontsize=9)
    fig.tight_layout()
    save_figure(fig, "operator-class-p90-ttft-tpot")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    screen = load_screen()
    curve = load_curve()
    screen_flags = pareto_flags(screen)
    global_flags = pareto_flags(curve)
    rate_flags = []
    for row in curve:
        peers = [r for r in curve if r["offered_rps"] == row["offered_rps"]]
        rate_flags.append(pareto_flags(peers)[peers.index(row)])
    screen_rows = [{**r, "observed_p90_pareto": flag} for r, flag in zip(screen, screen_flags)]
    curve_rows = [{**r, "observed_global_p90_pareto": global_flag,
                   "observed_rate_matched_p90_pareto": rate_flag}
                  for r, global_flag, rate_flag in zip(curve, global_flags, rate_flags)]
    screen_fields = ["label", "short_label", "config_id", "output_tokens_per_s",
                     *(f"{m}_{p}_ms" for m in METRICS for p in PERCENTILES), "observed_p90_pareto"]
    curve_fields = ["label", "short_label", "config_id", "offered_rps", "realized_rps",
                    "output_tokens_per_s", "planned", "completed",
                    *(f"{m}_{p}_ms" for m in METRICS for p in PERCENTILES),
                    "observed_global_p90_pareto", "observed_rate_matched_p90_pareto",
                    "summary_path", "summary_sha256"]
    save_csv(OUT / "screen-pareto-p90.csv", screen_rows, screen_fields)
    save_csv(OUT / "operator-pareto-p90.csv", curve_rows, curve_fields)
    plot_screen(screen)
    for metric in METRICS:
        plot_curves(curve, metric)
    plot_class_p90(curve)
    plot_pareto(screen, screen_flags, "screen-pareto-p90",
                "36-request screen: observed p90 Pareto across B0 and eight proposals")
    plot_pareto(curve, global_flags, "operator-pareto-p90",
                "Three-rate study: observed p90 Pareto across nine measured points")
    report = {
        "scope": "sample_point_estimates_only_no_uncertainty_or_sla_capacity_claim",
        "objectives": {"maximize": ["output_tokens_per_s"],
                       "minimize": ["ttft_p90_ms", "tpot_p90_ms"]},
        "screen_frontier": [r["label"] for r, keep in zip(screen, screen_flags) if keep],
        "operator_global_frontier": [f"{r['short_label']}@{r['offered_rps']:.1f}"
                                     for r, keep in zip(curve, global_flags) if keep],
        "operator_rate_matched_frontier": {
            str(rate): [r["short_label"] for r, keep in zip(curve, rate_flags)
                        if r["offered_rps"] == rate and keep]
            for rate in (0.2, 0.4, 0.8)},
        "caveats": ["36 screen requests and 32 curve requests per point are small samples",
                    "Only three configurations have multi-rate curves; the others have one screen point",
                    "p99 is dominated by the highest one or two request latencies",
                    "No repeated windows, adaptive load search, independent test, or SLA capacity estimate"],
        "source_sha256": {str((PILOT / "all-screen-points.csv").relative_to(ROOT)):
                              sha(PILOT / "all-screen-points.csv"),
                          str((CURVE / "all-points.json").relative_to(ROOT)):
                              sha(CURVE / "all-points.json")},
    }
    (OUT / "pareto-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    PUBLISH.mkdir(parents=True, exist_ok=True)
    for path in OUT.iterdir():
        if path.suffix in {".svg", ".csv", ".json"}:
            shutil.copyfile(path, PUBLISH / path.name)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
