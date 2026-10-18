"""Publish inspectable curves and observed Pareto points from native GuideLLM JSON."""
import csv
import html
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / '.artifacts/optuna-direct-v1'
OUT = ROOT / 'results/2026-10-18-direct-optuna'
LIMITS = {'chat': 1500, 'agent': 2500, 'code': 750, 'document': 12000}


def dominates(a, b):
    av = [-a['output_tok_s'], a['ttft_p90_ms'], a['tpot_p90_ms']]
    bv = [-b['output_tok_s'], b['ttft_p90_ms'], b['tpot_p90_ms']]
    return all(x <= y for x, y in zip(av, bv)) and any(x < y for x, y in zip(av, bv))


def counter_delta(directory, name):
    def total(path):
        found = []
        for line in path.read_text().splitlines():
            if line.startswith(name + '{') or line.startswith(name + ' '):
                found.append(float(line.rsplit(' ', 1)[1]))
        return sum(found) if found else None
    try:
        before = total(directory / 'metrics-before.prom')
        after = total(directory / 'metrics-after.prom')
        return after - before if before is not None and after is not None else None
    except (OSError, ValueError):
        return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = sorted({*STUDY.glob('*/trial_*/c*-window*/guidellm.json'),
                     *STUDY.glob('*/trial_*/c*-window*/point.json'),
                     *STUDY.glob('*/trial_*/validation.json'),
                     *STUDY.glob('*-trials.json'), *STUDY.glob('*-finished.json'),
                     *STUDY.glob('anchor-selection.json')})
    signature = {'source': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'files': [[str(p), p.stat().st_size, p.stat().st_mtime_ns] for p in inputs]}
    state_path = STUDY / 'report-state.json'
    if state_path.exists() and json.loads(state_path.read_text()) == signature:
        return
    rows, classes = [], []
    histories = {}
    for history in STUDY.glob('*-trials.json'):
        histories[history.name.removesuffix('-trials.json')] = {
            f'trial_{t["number"]}': t for t in json.loads(history.read_text())}
    # Completed histories stay the primary record. The read-only database gives
    # parameters for a running trial whose first point has already completed.
    for database in STUDY.glob('*.sqlite3'):
        with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
            entries = connection.execute("SELECT t.number, t.state, a.value_json FROM trials t "
                "JOIN trial_user_attributes a ON t.trial_id=a.trial_id WHERE a.key='resolved_parameters'")
            for number, state, parameters in entries:
                record = histories.setdefault(database.stem, {}).setdefault(f'trial_{number}', {})
                record['state'] = state
                record.setdefault('attrs', {})['resolved_parameters'] = json.loads(parameters)
    for path in sorted(STUDY.glob('*/trial_*/c*-window*/guidellm.json')):
        try:
            data = json.loads(path.read_text())
            point = json.loads(path.with_name('point.json').read_text())
        except (ValueError, OSError):
            continue
        phase, trial = path.parts[-4], path.parts[-3]
        valid = path.parent.parent.joinpath('validation.json').exists()
        for b in data['benchmarks']:
            metrics = b['metrics']
            row = {'phase': phase, 'trial': trial, 'concurrency': point['concurrency'],
                   'validated': valid, 'output_tok_s': metrics['output_tokens_per_second']['total']['mean'],
                   'requests_s': metrics['requests_per_second']['total']['mean'],
                   'wall_seconds': point['wall_seconds'], 'native': str(path.relative_to(ROOT))}
            trial_record = histories.get(phase, {}).get(trial, {})
            row['trial_state'] = trial_record.get('state', '')
            row['source_search_trial'] = trial_record.get('attrs', {}).get('search_trial', '')
            row['parameters'] = json.dumps(trial_record.get('attrs', {}).get(
                'resolved_parameters', trial_record.get('params', {})), sort_keys=True)
            queries = counter_delta(path.parent, 'vllm:prefix_cache_queries_total')
            hits = counter_delta(path.parent, 'vllm:prefix_cache_hits_total')
            row['prefix_queried_tokens'] = queries
            row['prefix_hit_tokens'] = hits
            row['prefix_hit_fraction'] = hits / queries if queries and hits is not None else None
            row['preemptions'] = counter_delta(path.parent, 'vllm:num_preemptions_total')
            counts = b['scheduler_metrics']['requests_made']
            row.update({k: counts[k] for k in ('successful', 'errored', 'incomplete')})
            for label, key in [('ttft', 'time_to_first_token_ms'), ('tpot', 'inter_token_latency_ms')]:
                m = metrics[key]['successful']
                row[f'{label}_native_p90_ms'] = m['percentiles']['p90']
                samples = [r[key] for r in b['requests']['successful']]
                for q in ('p50', 'p90', 'p99'):
                    row[f'{label}_{q}_ms'] = float(np.percentile(samples, int(q[1:])))
            grouped = {c: [] for c in LIMITS}
            for r in b['requests']['successful']:
                # Match GuideLLM's overlap rule for the measured interval.
                if r['request_end_time'] < b['start_time'] or r['request_start_time'] > b['end_time']:
                    continue
                m = re.search(r'Request (?:dev|test)-[ab]-\d+-(chat|agent|code|document)', r['request_args'] or '')
                if m:
                    grouped[m[1]].append(r)
            all_pass = True
            for c, items in grouped.items():
                cr = {'phase': phase, 'trial': trial, 'concurrency': point['concurrency'],
                      'class': c, 'count': len(items)}
                if not items:
                    all_pass = False
                    continue
                for label, key in [('ttft', 'time_to_first_token_ms'), ('tpot', 'inter_token_latency_ms')]:
                    vals = [x[key] for x in items if x[key] is not None]
                    for q in (50, 90, 99):
                        cr[f'{label}_p{q}_ms'] = float(np.percentile(vals, q))
                cr['observed_target_pass'] = cr['ttft_p90_ms'] <= LIMITS[c] and cr['tpot_p90_ms'] <= 70
                all_pass &= cr['observed_target_pass']
                classes.append(cr)
            row['all_classes_observed_target_pass'] = bool(all_pass)
            rows.append(row)
    if not rows:
        return
    anchors_path = STUDY / 'anchor-selection.json'
    anchor = json.loads(anchors_path.read_text())['high'] if anchors_path.exists() else None
    eligible = [r for r in rows if r['phase'] == 'search' and r['validated']
                and r['trial_state'] == 'COMPLETE' and r['concurrency'] == anchor]
    for row in rows:
        row['observed_pareto'] = row in eligible and not any(dominates(other, row) for other in eligible)
        baseline = next((r for r in rows if r['phase'] == row['phase'] and
                         r['trial'] == 'trial_0' and r['concurrency'] == row['concurrency'] and r['validated']), None)
        for metric in ('output_tok_s', 'ttft_p90_ms', 'tpot_p90_ms'):
            row[f'{metric}_change_vs_matched_b0_pct'] = (
                100 * (row[metric] / baseline[metric] - 1) if baseline else '')
    for name, values in [('points.csv', rows), ('class-points.csv', classes)]:
        if values:
            with (OUT / name).open('w') as f:
                w = csv.DictWriter(f, fieldnames=list(values[0])); w.writeheader(); w.writerows(values)
    for metric, title in [('ttft', 'TTFT'), ('tpot', 'Per-request decode TPOT')]:
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        for q, ax in zip((50, 90, 99), axes):
            for phase, trial in sorted({(r['phase'], r['trial']) for r in rows}):
                subset = sorted([r for r in rows if r['phase'] == phase and r['trial'] == trial], key=lambda x: x['concurrency'])
                label = f'{phase}/{trial}'
                ax.plot([r['concurrency'] for r in subset], [r[f'{metric}_p{q}_ms'] for r in subset], 'o-', label=label)
            ax.set(xlabel='Outstanding client requests', ylabel='milliseconds', title=f'{title} p{q}')
            ax.grid(alpha=.25)
        axes[-1].legend(fontsize=6, loc='upper left', bbox_to_anchor=(1,1))
        fig.suptitle('Observed GuideLLM cohorts; p99 is descriptive; calibration uses fewer requests')
        fig.tight_layout(); fig.savefig(OUT / f'{metric}-curves.svg', bbox_inches='tight'); plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for metric, axes_row in zip(('ttft', 'tpot'), axes):
        for q, ax in zip((50, 90, 99), axes_row):
            for phase, trial in sorted({(r['phase'], r['trial']) for r in rows}):
                subset = sorted([r for r in rows if r['phase'] == phase and r['trial'] == trial],
                                key=lambda x: x['concurrency'])
                ax.plot([r['output_tok_s'] for r in subset],
                        [r[f'{metric}_p{q}_ms'] for r in subset], 'o-', label=f'{phase}/{trial}')
                for r in subset:
                    ax.annotate(f'c={r["concurrency"]}', (r['output_tok_s'], r[f'{metric}_p{q}_ms']), fontsize=6)
            ax.set(xlabel='Output tokens/s', ylabel=f'p{q} {metric.upper()} ms')
            ax.grid(alpha=.25)
    axes[0, -1].legend(fontsize=6, loc='upper left', bbox_to_anchor=(1, 1))
    fig.suptitle('Operating curves: measured closed-loop concurrency points; no fitted capacity boundary')
    fig.tight_layout(); fig.savefig(OUT / 'operating-curves.svg', bbox_inches='tight'); plt.close(fig)
    rates = {(r['phase'], r['trial'], r['concurrency']): r['output_tok_s'] for r in rows}
    fig, axes = plt.subplots(2, 4, figsize=(17, 8))
    for col, cls in enumerate(LIMITS):
        for metric, ax in zip(('ttft', 'tpot'), axes[:, col]):
            for phase, trial in sorted({(r['phase'], r['trial']) for r in classes}):
                subset = sorted([r for r in classes if r['class'] == cls and
                                 r['phase'] == phase and r['trial'] == trial], key=lambda r: r['concurrency'])
                if subset:
                    ax.plot([rates[(r['phase'], r['trial'], r['concurrency'])] for r in subset],
                            [r[f'{metric}_p90_ms'] for r in subset], 'o-', label=f'{phase}/{trial}')
            ax.axhline(LIMITS[cls] if metric == 'ttft' else 70, color='red', linestyle='--', label='Research target')
            ax.set(title=f'{cls}: p90 {metric.upper()}', xlabel='Aggregate output tokens/s', ylabel='ms')
            ax.grid(alpha=.25)
    axes[0, -1].legend(fontsize=6, loc='upper left', bbox_to_anchor=(1, 1))
    fig.suptitle('Per-class observed latency in the same mixed workload; sample counts are in class-points.csv')
    fig.tight_layout(); fig.savefig(OUT / 'class-curves.svg', bbox_inches='tight'); plt.close(fig)
    if eligible:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        for ax, metric in zip(axes, ('ttft', 'tpot')):
            for row in eligible:
                ax.scatter(row['output_tok_s'], row[f'{metric}_p90_ms'],
                           marker='*' if row['observed_pareto'] else 'o', s=90)
                ax.annotate(row['trial'], (row['output_tok_s'], row[f'{metric}_p90_ms']), fontsize=8)
            ax.set(xlabel='Output tokens/s (higher is better)', ylabel=f'p90 {metric.upper()} ms (lower is better)')
            ax.grid(alpha=.25)
        fig.suptitle(f'Three-objective observed Pareto (*), matched concurrency {anchor}')
        fig.tight_layout(); fig.savefig(OUT / 'pareto.svg'); plt.close(fig)
    confirmed = [r for r in rows if r['phase'] == 'confirmation' and r['validated'] and r['trial_state'] == 'COMPLETE']
    summary = {'points': len(rows), 'validated_candidates_including_b0': len(eligible),
               'objective_concurrency': anchor, 'observed_front': [r['trial'] for r in eligible if r['observed_pareto']],
               'capacity_confirmed': False, 'heldout_points_completed': len(confirmed),
               'heldout_campaign_finished': (STUDY / 'confirmation-finished.json').exists(),
               'independent_confirmation': 'inspect heldout deltas and B0 repeat' if confirmed else False}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
    table = '<table border="1"><tr>' + ''.join(f'<th>{html.escape(k)}</th>' for k in rows[0]) + '</tr>'
    table += ''.join('<tr>' + ''.join(f'<td>{html.escape(str(v))}</td>' for v in r.values()) + '</tr>' for r in rows) + '</table>'
    (OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Direct Optuna study</title>'
        '<h1>Direct Optuna / GuideLLM study</h1><p>Fresh baseline and same-workload comparisons. '
        'Exploratory observed frontier; no confirmed SLA capacity or production-quality claim.</p>'
        '<p>TPOT means (last token − first token)/(output tokens − 1), called inter_token_latency_ms by GuideLLM.</p>'
        '<img width="100%" src="ttft-curves.svg"><img width="100%" src="tpot-curves.svg">'
        '<img width="100%" src="operating-curves.svg">'
        '<img width="100%" src="class-curves.svg">'
        + ('<img width="100%" src="pareto.svg">' if eligible else '') + table)
    (OUT / 'README.md').write_text('# Direct Optuna study\n\n'
        '[Live report](index.html) · [All points](points.csv) · [Per-class metrics](class-points.csv)\n\n'
        '[Study manifest](study-manifest.json) · [Workload hashes](workload-card.json) · [Model hashes](model-manifest.json)\n\n'
        'Source: `.artifacts/optuna-direct-v1/`. Native GuideLLM exports and exact commands are preserved. '
        'Calibration uses 8 requests at concurrency 1 and 40 at other points; search uses 120 requests per point. '
        'Prefix warmup is separate and excluded; all measured requests complete or invalidate the point. '
        'Compare candidates with search/trial_0, the matched B0. A star denotes three-objective point-estimate '
        'Pareto membership at the common anchor, not proof of a repeatable improvement. '
        'Class target passes are observations, not statistically confirmed SLO attainment.\n')
    print(json.dumps(summary))
    state_path.write_text(json.dumps(signature))


if __name__ == '__main__':
    main()
