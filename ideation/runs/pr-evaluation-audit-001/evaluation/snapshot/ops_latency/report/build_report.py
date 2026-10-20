#!/usr/bin/env python3
"""Build a self-contained HTML export for the B200 latency campaign."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import io
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

try:
    from .collect_results import collect
except ImportError:  # Direct script execution.
    from collect_results import collect

try:
    from ops_latency.compare_dep8_2xdep4 import ComparisonError, build_comparison
except ModuleNotFoundError:  # Direct script execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ops_latency.compare_dep8_2xdep4 import ComparisonError, build_comparison


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TEMPLATE = HERE / "template.html"
PROFILE_NAMES = (
    "latency-tp4",
    "latency-dep8",
    "latency-dep8-sla",
    "latency-2xdep4-sla",
    "latency-tp8",
    "low-latency",
    "balanced",
    "throughput",
    "max-throughput",
)
POINT_COLUMNS = (
    ("status", "Status", "text"),
    ("evidence_class", "Evidence", "text"),
    ("profile", "Profile", "text"),
    ("arm", "Arm", "text"),
    ("workload", "Workload", "text"),
    ("scope", "Scope", "text"),
    ("category", "Category", "text"),
    ("provenance", "Provenance", "text"),
    ("request_path", "Path", "text"),
    ("client", "Client", "text"),
    ("target_cacheable_fraction", "Target cacheable", "percent"),
    ("pass_phase", "Phase", "text"),
    ("repetition", "Rep", "int"),
    ("repetition_count", "Runs", "int"),
    ("decision_grade", "Decision-grade", "text"),
    ("pareto_frontier", "Pareto", "text"),
    ("legacy_reference", "Legacy reference", "text"),
    ("include_in_slo_frontier", "Included frontier", "text"),
    ("repeat_command", "Repeat command", "text"),
    ("tier", "Tier", "text"),
    ("mode", "Mode", "text"),
    ("configured_concurrency", "c", "int"),
    ("configured_request_rate", "Offered req/s", "float"),
    ("request_rps", "Completed req/s", "float"),
    ("slo_goodput_rps", "SLO goodput", "float"),
    ("ttft_p50_ms", "TTFT p50 ms", "float"),
    ("ttft_p95_ms", "TTFT p95 ms", "float"),
    ("ttft_p99_ms", "TTFT p99 ms", "float"),
    ("tpot_p50_ms", "TPOT p50 ms", "float"),
    ("tpot_p95_ms", "TPOT p95 ms", "float"),
    ("tpot_p99_ms", "TPOT p99 ms", "float"),
    ("stream_gap_p99_ms", "Chunk gap p99 ms", "float"),
    ("e2e_p50_ms", "E2E p50 ms", "float"),
    ("e2e_p95_ms", "E2E p95 ms", "float"),
    ("e2e_p99_ms", "E2E p99 ms", "float"),
    ("error_rate", "Error", "percent"),
    ("cache_regime", "Cache regime", "text"),
    ("cache_hit_share", "Cache hits", "percent"),
    ("pd_transfer_failures", "PD transfer failures", "float"),
    ("pd_metric_deltas", "PD metric deltas", "text"),
    ("cost_per_million_tasks", "$/1M @ $4.5", "usd"),
)


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def fmt(value: Any, kind: str) -> str:
    if value is None or value == "":
        return "—"
    if kind == "int":
        return f"{float(value):,.0f}"
    if kind == "float":
        number = float(value)
        if abs(number) >= 1000:
            return f"{number:,.0f}"
        if abs(number) >= 100:
            return f"{number:,.1f}"
        return f"{number:,.2f}"
    if kind == "percent":
        return f"{float(value):.2%}"
    if kind == "usd":
        return f"${float(value):,.0f}"
    return esc(value)


def points_table(points: Sequence[Mapping[str, Any]]) -> str:
    head = "".join(f"<th>{esc(title)}</th>" for _, title, _ in POINT_COLUMNS)
    if not points:
        body = (
            f'<tr><td colspan="{len(POINT_COLUMNS)}" class="empty">'
            "No measured values yet.</td></tr>"
        )
    else:
        rows = []
        for point in points:
            cells = "".join(
                f"<td>{fmt(point.get(key), kind)}</td>"
                for key, _, kind in POINT_COLUMNS
            )
            rows.append(f"<tr>{cells}</tr>")
        body = "".join(rows)
    return (
        '<div class="scroll"><table class="data"><thead><tr>'
        f"{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


COMPARISON_COLUMNS = (
    ("arm", "Arm", "text"),
    ("concurrency", "c", "int"),
    ("observations", "Runs", "int"),
    ("qualifies", "Pass", "text"),
    ("confirmed", "3-run confirmed", "text"),
    ("request_rps", "Req/s", "float"),
    ("output_tokens_per_s", "Output tok/s", "float"),
    ("ttft_p50_ms", "TTFT p50 ms", "float"),
    ("ttft_p95_ms", "TTFT p95 ms", "float"),
    ("ttft_p99_ms", "TTFT p99 ms", "float"),
    ("tpot_p50_ms", "TPOT p50 ms", "float"),
    ("tpot_p95_ms", "TPOT p95 ms", "float"),
    ("tpot_p99_ms", "TPOT p99 ms", "float"),
    ("e2e_p50_ms", "E2E p50 ms", "float"),
    ("e2e_p95_ms", "E2E p95 ms", "float"),
    ("e2e_p99_ms", "E2E p99 ms", "float"),
    ("completion_ratio", "Completion", "percent"),
    ("error_rate", "Error", "percent"),
    ("cache_hit_share", "Cache hits", "percent"),
    ("all_backends_active", "All engines active", "text"),
    ("all_router_backends_active", "All router targets active", "text"),
    ("backend_max_to_min_ratio", "Backend max/min", "float"),
    ("router_max_to_min_ratio", "Router max/min", "float"),
    ("backend_shares", "Backend shares", "json"),
    ("router_shares", "Router shares", "json"),
)


def comparison_value(value: Any, kind: str) -> str:
    if kind == "json":
        return esc(json.dumps(value, sort_keys=True)) if value else "—"
    if kind == "text" and isinstance(value, bool):
        return "yes" if value else "no"
    return fmt(value, kind)


def comparison_table(comparison: Mapping[str, Any]) -> str:
    head = "".join(
        f"<th>{esc(title)}</th>" for _, title, _ in COMPARISON_COLUMNS
    )
    aggregates = comparison.get("aggregates") or []
    if not aggregates:
        body = (
            f'<tr><td colspan="{len(COMPARISON_COLUMNS)}" class="empty">'
            "No DEP8 versus 2×DEP4 measurements yet.</td></tr>"
        )
    else:
        body = "".join(
            "<tr>"
            + "".join(
                f"<td>{comparison_value(point.get(key), kind)}</td>"
                for key, _, kind in COMPARISON_COLUMNS
            )
            + "</tr>"
            for point in aggregates
        )
    return (
        '<div class="scroll"><table class="data"><thead><tr>'
        f"{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def delta_percent(value: Any) -> str:
    return "—" if value is None else f"{float(value):+.1%}"


def comparison_delta_table(comparison: Mapping[str, Any]) -> str:
    rows = []
    for item in comparison.get("same_concurrency_deltas") or []:
        rows.append(
            "<tr>"
            f"<td>{esc(item.get('dep4_arm'))}</td>"
            f"<td>{fmt(item.get('concurrency'), 'int')}</td>"
            f"<td>{comparison_value(item.get('dep8_qualifies'), 'text')}</td>"
            f"<td>{comparison_value(item.get('dep4_qualifies'), 'text')}</td>"
            f"<td>{comparison_value(item.get('cache_comparable'), 'text')}</td>"
            f"<td>{delta_percent(item.get('request_rps_delta_fraction'))}</td>"
            f"<td>{delta_percent(item.get('output_tokens_per_s_delta_fraction'))}</td>"
            f"<td>{delta_percent(item.get('ttft_p99_ms_delta_fraction'))}</td>"
            f"<td>{delta_percent(item.get('tpot_p50_ms_delta_fraction'))}</td>"
            f"<td>{delta_percent(item.get('e2e_p50_ms_delta_fraction'))}</td>"
            "</tr>"
        )
    body = "".join(rows) or (
        '<tr><td colspan="10" class="empty">'
        "Same-concurrency deltas will appear after paired runs.</td></tr>"
    )
    return (
        '<div class="scroll"><table class="data"><thead><tr>'
        "<th>2×DEP4 arm</th><th>c</th><th>DEP8 pass</th>"
        "<th>2×DEP4 pass</th><th>Cache-comparable</th>"
        "<th>Req/s Δ</th><th>Output tok/s Δ</th>"
        "<th>TTFT p99 Δ</th><th>TPOT p50 Δ</th><th>E2E p50 Δ</th>"
        f"</tr></thead><tbody>{body}</tbody></table></div>"
    )


def comparison_summary(comparison: Mapping[str, Any]) -> str:
    dep8 = comparison.get("selected_dep8_point")
    dep4 = comparison.get("selected_dep4_point")
    pairing = comparison.get("selected_dataset_pairing") or {}

    def card(title: str, point: Any) -> str:
        if not isinstance(point, Mapping):
            return (
                f'<div class="card"><b>{esc(title)}</b><br>'
                "No qualifying measured point yet.</div>"
            )
        return (
            f'<div class="card"><b>{esc(title)}</b><br>'
            f"{esc(point.get('arm'))} at c={fmt(point.get('concurrency'), 'int')}: "
            f"{fmt(point.get('request_rps'), 'float')} req/s, "
            f"TTFT p99 {fmt(point.get('ttft_p99_ms'), 'float')} ms, "
            f"TPOT p50 {fmt(point.get('tpot_p50_ms'), 'float')} ms. "
            f"Confirmed: {comparison_value(point.get('confirmed'), 'text')}."
            "</div>"
        )

    pair_status = (
        "matching"
        if pairing.get("complete_and_match") is True
        else "not yet complete or mismatched"
    )
    return (
        '<div class="summary-grid">'
        f"{card('Selected DEP8', dep8)}"
        f"{card('Selected 2×DEP4', dep4)}"
        '<div class="card"><b>Dataset pairing</b><br>'
        f"SHA-256 evidence is {esc(pair_status)}.</div>"
        '<div class="card"><b>Claim boundary</b><br>'
        "Agent-f75 only: 8K input, 1K output, target 75% cacheability. "
        "This closed-loop comparison is not a general production SLA.</div>"
        "</div>"
    )


def list_html(values: Any) -> str:
    if not isinstance(values, list) or not values:
        return ""
    return "<ul>" + "".join(f"<li>{esc(value)}</li>" for value in values) + "</ul>"


def experiment_sections(
    campaign: Mapping[str, Any],
    points: Sequence[Mapping[str, Any]],
) -> str:
    sections: list[str] = []
    experiments = campaign.get("experiments") or []
    for experiment in experiments:
        if not isinstance(experiment, Mapping):
            continue
        experiment_id = str(experiment.get("id") or "unknown")
        if experiment_id == "LAT-00":
            rows = [
                point
                for point in points
                if str(point.get("evidence_class", "")).startswith("reused_")
            ]
        else:
            rows = [
                point
                for point in points
                if point.get("experiment_id") == experiment_id
            ]
        status = str(experiment.get("status") or "planned")
        measured_statuses = {
            str(point.get("status"))
            for point in rows
            if point.get("evidence_class") == "measured_latency_campaign"
        }
        if "complete" in measured_statuses:
            status = "complete"
        elif measured_statuses:
            status = sorted(measured_statuses)[0]
        objective = (
            experiment.get("objective")
            or experiment.get("change")
            or ""
        )
        workloads = ", ".join(
            map(
                str,
                experiment.get("workloads")
                or (campaign.get("active_protocol") or {}).get(
                    "workloads", []
                ),
            )
        )
        arms = ", ".join(map(str, experiment.get("arms") or []))
        expected_html = (
            f'<div class="comment"><b>Expected:</b> '
            f"{esc(experiment.get('expected') or experiment.get('comments') or '')}"
        )
        if experiment.get("stop_condition"):
            expected_html += (
                f"<br><b>Stop condition:</b> "
                f"{esc(experiment.get('stop_condition'))}"
            )
        expected_html += (
            f"{list_html(experiment.get('interpretation'))}</div>"
        )
        evidence_notes = ""
        if experiment_id == "LAT-00":
            notes = []
            for evidence in campaign.get("existing_evidence") or []:
                if not isinstance(evidence, Mapping):
                    continue
                notes.append(
                    "<li><b>"
                    f"{esc(evidence.get('id'))} · "
                    f"{esc(evidence.get('label'))}:</b> "
                    f"{esc(evidence.get('comments'))}</li>"
                )
            if notes:
                evidence_notes = (
                    "<details><summary>Imported evidence caveats</summary>"
                    f"<ul>{''.join(notes)}</ul></details>"
                )
        sections.append(
            f'<section id="{esc(experiment_id.lower())}">'
            f"<h3>{esc(experiment_id)} · {esc(experiment.get('title'))}</h3>"
            f'<p><span class="badge {esc(status)}">{esc(status)}</span> '
            f"<b>Change:</b> {esc(objective)}</p>"
            f"<p><b>Workloads:</b> {esc(workloads or '—')}<br>"
            f"<b>Arms:</b> {esc(arms or '—')}</p>"
            f"{expected_html}"
            f"{evidence_notes}"
            f"{points_table(rows)}"
            "</section>"
        )
    return "".join(sections)


def tier_table(campaign: Mapping[str, Any]) -> str:
    rows = []
    tiers = campaign.get("slo_tiers") or {}
    if isinstance(tiers, Mapping):
        for name, tier in tiers.items():
            if not isinstance(tier, Mapping):
                continue
            default = tier.get("default") or {}
            rows.append(
                "<tr>"
                f"<td>{esc(name)}</td>"
                f"<td>{esc(tier.get('description'))}</td>"
                f"<td>{fmt(default.get('ttft_p95_ms'), 'float')}</td>"
                f"<td>{fmt(default.get('ttft_p99_ms'), 'float')}</td>"
                f"<td>{fmt(default.get('tpot_p95_ms'), 'float')}</td>"
                f"<td>{fmt(default.get('tpot_p99_ms'), 'float')}</td>"
                f"<td>{fmt(default.get('maximum_error_rate'), 'percent')}</td>"
                "</tr>"
            )
    return (
        '<div class="scroll"><table class="data"><thead><tr>'
        "<th>Tier</th><th>Description</th><th>TTFT p95 ms</th>"
        "<th>TTFT p99 ms</th><th>TPOT p95 ms</th><th>TPOT p99 ms</th>"
        f"<th>Max error</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def deferred_experiments_html(campaign: Mapping[str, Any]) -> str:
    parts = []
    for experiment in campaign.get("deferred_experiments") or []:
        if not isinstance(experiment, Mapping):
            continue
        parts.append(
            "<details><summary>"
            f"{esc(experiment.get('id'))} · {esc(experiment.get('title'))}"
            "</summary>"
            f"<p>{esc(experiment.get('objective') or '')}</p>"
            f"<p class=\"note\">{esc(experiment.get('comments') or '')}</p>"
            f"{list_html(experiment.get('interpretation'))}"
            "</details>"
        )
    return "".join(parts) or "<p class=\"empty\">No deferred experiments.</p>"


def parameters_html() -> str:
    parts = []
    for name in PROFILE_NAMES:
        path = REPO / f"serving/b200/vllm/profiles/{name}.yaml"
        if path.is_file():
            parts.append(
                f"<details><summary><code>{esc(path.name)}</code></summary>"
                f"<pre>{esc(path.read_text(encoding='utf-8'))}</pre></details>"
            )
    for path in sorted(
        (REPO / "serving/b200/vllm/pd_profiles").glob("*.yaml")
    ):
        parts.append(
            f"<details><summary><code>pd_profiles/{esc(path.name)}</code></summary>"
            f"<pre>{esc(path.read_text(encoding='utf-8'))}</pre></details>"
        )
    experiments = REPO / "serving/b200/vllm/experiments.yaml"
    if experiments.is_file():
        loaded = yaml.safe_load(experiments.read_text(encoding="utf-8"))
        latency_flags = {
            name: value
            for name, value in (loaded.get("experiments") or {}).items()
            if str(name).startswith("lat-")
        }
        parts.append(
            "<details><summary><code>latency-prefixed experiment flags</code>"
            "</summary><pre>"
            f"{esc(yaml.safe_dump(latency_flags, sort_keys=False))}"
            "</pre></details>"
        )
    return "".join(parts)


def log_excerpts(live_root: Path, limit: int = 12000) -> str:
    if not live_root.is_dir():
        return "<p class=\"empty\">No latency campaign logs yet.</p>"
    parts = []
    paths = sorted(live_root.rglob("*.log"))
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        clipped = text[-limit:]
        parts.append(
            f"<details><summary>{esc(path.relative_to(live_root))} "
            f"({len(text):,} chars)</summary><pre>{esc(clipped)}</pre></details>"
        )
    return "".join(parts) or "<p class=\"empty\">No latency campaign logs yet.</p>"


def chat_html(session: Path | None) -> str:
    if session is None or not session.is_file():
        return "<p class=\"empty\">No session transcript was supplied.</p>"
    parts = []
    with session.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = entry.get("type")
            if kind not in {"user", "assistant"}:
                continue
            message = entry.get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "\n".join(
                    str(block.get("text") or "")
                    for block in content
                    if isinstance(block, Mapping) and block.get("type") == "text"
                )
            else:
                text = ""
            if text.strip():
                parts.append(
                    f'<div class="msg {esc(kind)}"><b>{esc(kind.title())}</b>'
                    f"<pre>{esc(text[:20000])}</pre></div>"
                )
    return "".join(parts) or "<p class=\"empty\">Transcript contained no messages.</p>"


def findings(points: Sequence[Mapping[str, Any]]) -> str:
    overall = [point for point in points if point.get("scope") == "overall"]
    reused = [
        point
        for point in overall
        if str(point.get("evidence_class", "")).startswith("reused_")
    ]
    measured = [
        point
        for point in overall
        if point.get("evidence_class") == "measured_latency_campaign"
    ]
    passing = [
        point
        for point in overall
        if point.get("include_in_slo_frontier") is True
    ]
    return (
        "<ul>"
        f"<li><b>{len(reused)}</b> immutable archive points imported; "
        "diagnostic evidence remains excluded from SLO claims.</li>"
        f"<li><b>{len(measured)}</b> new latency-tier points measured so far.</li>"
        f"<li><b>{len(passing)}</b> points currently qualify for the "
        "latency–goodput frontier.</li>"
        "<li>Existing cache-hot boundaries are context, not uncached "
        "production promises.</li>"
        "<li>Planned rows remain empty until their runner writes complete "
        "raw and post-run artifacts.</li>"
        "</ul>"
    )


def runtime_estimate_html(campaign: Mapping[str, Any]) -> str:
    protocol = campaign.get("active_protocol") or {}
    configs = [
        item
        for item in campaign.get("experiments") or []
        if isinstance(item, Mapping)
        and item.get("kind") == "configuration"
    ]
    workloads = len(protocol.get("workloads") or [])
    cache_tiers = len(protocol.get("cache_tiers") or [])
    cells = sum(
        workloads
        * (cache_tiers + (1 if item.get("include_uncached") else 0))
        for item in configs
    )
    warmups = len(configs) * workloads * cache_tiers
    calibrators = sum(item.get("calibrate") is True for item in configs)
    calibration_runs = (
        calibrators
        * workloads
        * int((protocol.get("calibration") or {}).get("rates_per_workload", 0))
    )
    warmup_seconds = int((protocol.get("warmup") or {}).get("duration_s", 0))
    floor_seconds = int((protocol.get("floor") or {}).get("duration_s", 0))
    knee_seconds = int((protocol.get("knee") or {}).get("duration_s", 0))
    maximum_adjustments = int(
        (protocol.get("knee") or {}).get("maximum_adjustments", 0)
    )
    calibration_seconds = int(
        (protocol.get("calibration") or {}).get("duration_s", 0)
    )
    base_seconds = (
        warmups * warmup_seconds
        + cells * floor_seconds
        + cells * knee_seconds
        + calibration_runs * calibration_seconds
    )
    worst_seconds = (
        base_seconds + cells * knee_seconds * maximum_adjustments
    )
    return (
        '<div class="summary-grid">'
        f"<div class=\"card\"><b>{len(configs)} configurations</b><br>"
        f"{cells} workload/cache cells; {calibration_runs} calibration runs.</div>"
        f"<div class=\"card\"><b>{base_seconds / 3600:.1f} load hours</b><br>"
        "Base first pass before model starts, reporting, and S3.</div>"
        f"<div class=\"card\"><b>{worst_seconds / 3600:.1f} load hours</b><br>"
        f"Worst case if every cell takes all {maximum_adjustments} "
        "rate corrections.</div>"
        "<div class=\"card\"><b>"
        f"{(warmup_seconds + 2 * knee_seconds) / 60:.0f} min"
        "</b><br>"
        "One selected point: rewarm plus repetitions 2–3.</div>"
        "</div>"
    )


def points_csv(points: Sequence[Mapping[str, Any]]) -> str:
    keys: list[str] = []
    for point in points:
        for key in point:
            if key not in keys:
                keys.append(key)
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=keys, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(points)
    return output.getvalue()


def comparison_csv(comparison: Mapping[str, Any]) -> str:
    deltas = {
        (item.get("dep4_arm"), item.get("concurrency")): item
        for item in comparison.get("same_concurrency_deltas") or []
    }
    selected = {
        (
            point.get("arm"),
            point.get("concurrency"),
        )
        for point in (
            comparison.get("selected_dep8_point"),
            comparison.get("selected_dep4_point"),
        )
        if isinstance(point, Mapping)
    }
    rows: list[dict[str, Any]] = []
    for aggregate in comparison.get("aggregates") or []:
        row = {
            key: (
                json.dumps(aggregate.get(key), sort_keys=True)
                if kind == "json"
                else aggregate.get(key)
            )
            for key, _, kind in COMPARISON_COLUMNS
        }
        row["selected_operating_point"] = (
            aggregate.get("arm"),
            aggregate.get("concurrency"),
        ) in selected
        delta = deltas.get(
            (aggregate.get("arm"), aggregate.get("concurrency")), {}
        )
        for key, value in delta.items():
            if key not in {"dep4_arm", "concurrency"}:
                row[key] = value
        rows.append(row)
    fields = [key for key, _, _ in COMPARISON_COLUMNS] + [
        "selected_operating_point",
        "dep4_qualifies",
        "dep8_qualifies",
        "cache_comparable",
        *(f"{metric}_delta_fraction" for metric in (
            "request_rps",
            "output_tokens_per_s",
            "ttft_p50_ms",
            "ttft_p95_ms",
            "ttft_p99_ms",
            "tpot_p50_ms",
            "tpot_p95_ms",
            "tpot_p99_ms",
            "e2e_p50_ms",
            "e2e_p95_ms",
            "e2e_p99_ms",
        )),
    ]
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def safe_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":")).replace("</", "<\\/")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--live-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--session", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    campaign_path = args.campaign.expanduser().resolve()
    archive_root = args.archive_root.expanduser().resolve()
    live_root = args.live_root.expanduser().resolve()
    result = collect(
        campaign_path=campaign_path,
        archive_root=archive_root,
        live_root=live_root,
    )
    campaign = result["campaign"]
    points = result["points"]
    try:
        comparison = build_comparison(campaign_path, live_root)
    except ComparisonError:
        comparison = {
            "schema_version": 1,
            "aggregates": [],
            "same_concurrency_deltas": [],
            "dataset_pairing": {
                "discovery_by_arm": {},
                "all_measured_discovery_arms_complete_and_match": False,
                "confirmation_same_concurrency_comparisons": [],
                "confirmation_warmup_by_arm": {},
                "all_available_confirmation_pairs_match": True,
            },
            "selected_dataset_pairing": None,
            "selected_confirmation_warmup_pairing": None,
            "selected_dep8_point": None,
            "selected_dep4_point": None,
        }
    result["dep8_vs_2xdep4"] = comparison
    comparison_csv_text = comparison_csv(comparison)
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    template = TEMPLATE.read_text(encoding="utf-8")
    page = (
        template.replace("__GENERATED__", esc(now))
        .replace("__POINT_COUNT__", str(len(points)))
        .replace("__FINDINGS__", findings(points))
        .replace("__RUNTIME_ESTIMATE__", runtime_estimate_html(campaign))
        .replace("__TIER_TABLE__", tier_table(campaign))
        .replace("__COMPARISON_SUMMARY__", comparison_summary(comparison))
        .replace("__COMPARISON_TABLE__", comparison_table(comparison))
        .replace("__COMPARISON_DELTA_TABLE__", comparison_delta_table(comparison))
        .replace("__EXPERIMENT_SECTIONS__", experiment_sections(campaign, points))
        .replace("__DEFERRED_EXPERIMENTS__", deferred_experiments_html(campaign))
        .replace("__ALL_POINTS__", points_table(points))
        .replace("__PARAMETERS__", parameters_html())
        .replace("__LOGS__", log_excerpts(live_root))
        .replace("__CHAT__", chat_html(args.session))
        .replace("__DATA_JSON__", safe_json(points))
        .replace("__CAMPAIGN_JSON__", safe_json(campaign))
        .replace("__COMPARISON_JSON__", safe_json(comparison))
        .replace("__POINTS_CSV_JSON__", safe_json(points_csv(points)))
        .replace("__COMPARISON_CSV_JSON__", safe_json(comparison_csv_text))
    )
    # Embedded server/queue logs can contain trailing spaces. They add no
    # information and make generated artifacts fail repository whitespace
    # checks.
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding="utf-8")
    data_path = args.output.with_name("latency-campaign-data.json")
    data_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    csv_path = args.output.with_name("latency-campaign-points.csv")
    csv_path.write_text(points_csv(points), encoding="utf-8")
    comparison_json_path = args.output.with_name(
        "latency-dep8-vs-2xdep4.json"
    )
    comparison_json_path.write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    comparison_csv_path = args.output.with_name(
        "latency-dep8-vs-2xdep4.csv"
    )
    comparison_csv_path.write_text(comparison_csv_text, encoding="utf-8")
    print(
        f"{args.output}: {len(page) / 1e6:.2f} MB, "
        f"{len(points)} points"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
