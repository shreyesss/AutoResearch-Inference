"""Render development and held-out measurements without mixing their baselines."""
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/2026-10-18-direct-optuna'
COLS = [('search', 0, 'B0'), ('search', 9, 'Trial 9'),
        ('search', 10, 'Trial 10'), ('search', 11, 'Trial 10 repeat¹'),
        ('search', 24, 'Trial 24'), ('confirmation', 0, 'B0 before'),
        ('confirmation', 1, 'Trial 9'), ('confirmation', 2, 'Trial 10'),
        ('confirmation', 3, 'Trial 24'), ('confirmation', 4, 'B0 after')]
METRICS = [('output_tok_s', 'Output tokens/s ↑', 1, 1),
           ('requests_s', 'Achieved requests/s ↑', 1, 3),
           *[(f'ttft_p{q}_ms', f'TTFT p{q} (s) ↓', .001, 3) for q in (50, 90, 99)],
           *[(f'tpot_p{q}_ms', f'TPOT p{q} (ms/token) ↓', 1, 2) for q in (50, 90, 99)],
           ('successful', 'Successful requests', 1, 0),
           ('errored', 'Failed requests', 1, 0), ('incomplete', 'Incomplete requests', 1, 0),
           ('prefix_hit_fraction', 'Prefix token hit fraction (%)', 100, 1),
           ('preemptions', 'Server preemptions', 1, 0),
           ('wall_seconds', 'Point wall time² (s)', 1, 1)]


def main():
    rows = list(csv.DictReader((OUT / 'points.csv').open()))
    classes = list(csv.DictReader((OUT / 'class-points.csv').open()))
    lookup = {(r['phase'], int(r['trial'].split('_')[1]), int(r['concurrency'])): r
              for r in rows if r['validated'] == 'True' and r['trial_state'] == 'COMPLETE'}
    clookup = {(r['phase'], int(r['trial'].split('_')[1]), int(r['concurrency']), r['class']): r
               for r in classes}
    def table(body):
        header = '<tr><th rowspan="2">Metric</th><th colspan="5">Development inputs</th><th colspan="5">Held-out test inputs</th></tr>'
        header += '<tr>' + ''.join(f'<th>{html.escape(c[2])}</th>' for c in COLS) + '</tr>'
        return '<div class="scroll"><table><thead>' + header + '</thead><tbody>' + body + '</tbody></table></div>'
    def row(label, values):
        return '<tr><th>' + html.escape(label) + '</th>' + ''.join(f'<td>{html.escape(str(v))}</td>' for v in values) + '</tr>'
    def fmt(record, key, factor=1, decimals=2):
        return '—' if record is None or record.get(key, '') == '' else f'{float(record[key])*factor:,.{decimals}f}'
    sections = []
    for c in (16, 32, 64):
        records = [lookup.get((phase, trial, c)) for phase, trial, _ in COLS]
        body = ''.join(row(label, [fmt(r, key, factor, digits) for r in records])
                       for key, label, factor, digits in METRICS)
        body += row('All classes meet research targets?',
                    [('Yes' if r['all_classes_observed_target_pass'] == 'True' else 'No') if r else '—' for r in records])
        part = f'<section data-load="{c}"' + (' hidden' if c != 32 else '') + f'><h2>{c} concurrent clients</h2>'
        part += '<p>120 requests per measured point: 54 chat · 24 agent-like · 24 code-like · 18 document.</p>' + table(body)
        part += '<h3>Changes against the matching baseline</h3><p>Test ranges compare each candidate separately against B0 before and B0 after; they are not confidence intervals. Lower latency is better.</p>'
        delta = ''
        for key, label in [('output_tok_s', 'Output tokens/s change (%)'), ('ttft_p90_ms', 'p90 TTFT change (%)'), ('tpot_p90_ms', 'p90 TPOT change (%)')]:
            values = []
            for (phase, trial, _), r in zip(COLS, records):
                if not r: values.append('—'); continue
                if (phase == 'search' and trial == 0) or (phase == 'confirmation' and trial in (0, 4)):
                    values.append('Reference'); continue
                bases = [lookup[(phase, b, c)] for b in ([0] if phase == 'search' else [0, 4]) if (phase, b, c) in lookup]
                differences = sorted(100*(float(r[key])/float(b[key])-1) for b in bases)
                values.append(' to '.join(f'{x:+.2f}%' for x in differences))
            delta += row(label, values)
        part += table(delta)
        for cls, limit in [('chat', 1.5), ('agent', 2.5), ('code', .75), ('document', 12)]:
            crs = [clookup.get((phase, trial, c, cls)) if records[i] else None
                   for i, (phase, trial, _) in enumerate(COLS)]
            cb = row('Request count', [fmt(r, 'count', 1, 0) for r in crs])
            for metric, unit, factor in [('ttft', 's', .001), ('tpot', 'ms/token', 1)]:
                for q in (50, 90, 99):
                    cb += row(f'{metric.upper()} p{q} ({unit})', [fmt(r, f'{metric}_p{q}_ms', factor, 3 if metric == 'ttft' else 2) for r in crs])
            cb += row('Observed target pass?', [('Yes' if r['observed_target_pass'] == 'True' else 'No') if r else '—' for r in crs])
            part += f'<details><summary>{cls.title()} metrics · p90 TTFT ≤ {limit}s; TPOT ≤ 70ms/token</summary>' + table(cb) + '</details>'
        part += '</section>'
        sections.append(part)
    parameters = ['max_num_batched_tokens', 'max_num_seqs', 'gpu_memory_utilization',
                  'long_prefill_token_threshold', 'async_scheduling', 'enforce_eager',
                  'max_cudagraph_capture_size', 'enable_prefix_caching', 'enable_chunked_prefill']
    pbody = ''
    for key in parameters:
        pbody += row(key, [json.loads(lookup[(phase, trial, 32)]['parameters']).get(key, '—') for phase, trial, _ in COLS])
    document = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Development vs held-out comparisons</title><style>
body{font:15px system-ui,sans-serif;color:#172238;background:#f6f8fb;margin:28px;line-height:1.5}h1{margin-bottom:6px}
.scroll{overflow:auto;margin:18px 0;background:white;border:1px solid #dce3ed;border-radius:8px}table{border-collapse:collapse;min-width:1250px;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:10px 12px;border-bottom:1px solid #e6ebf2;text-align:right;white-space:nowrap}th{background:#edf2fa}tbody th{text-align:left;position:sticky;left:0;z-index:1}
thead tr:first-child th:nth-child(3){background:#dcefe8}tbody td:nth-child(7){border-left:3px solid #96b8aa}tbody tr:hover td{background:#f3f7fc}
select{padding:8px;font:inherit}details{margin:12px 0}summary{cursor:pointer;padding:12px;background:#e8eef7;border-radius:6px}.note{max-width:1100px}.summary{padding:15px;background:#e7f1ed;border-left:4px solid #31775d}a{color:#175fb0}
</style><h1>Development → held-out comparison</h1>
<p class="note">Original search trial IDs are used throughout. This is held-out validation with different frozen prompts from the same synthetic workload; only the two test B0 runs and development trials 10/11 are same-input repeats. Compare each candidate against its own split's baseline.</p>
<p class="summary"><strong>Finding:</strong> Trial 9's development +10% throughput did not reproduce. Trial 10 reduced held-out p90 TTFT at 32 clients by 29–34%, with throughput within 1% of baseline and TPOT 1.3–3.3% worse. Trial 24 trades severe waiting for faster decode. These are measured tradeoffs, not significance claims.</p>
<label>Concurrent clients: <select id="load"><option>16</option><option selected>32</option><option>64</option></select></label>
<p class="note">↑ higher is better · ↓ lower is better · — no measurement (64 clients was tested only during confirmation). TTFT includes waiting for the first token; TPOT measures subsequent decode. All percentiles give each request one vote.</p>
''' + ''.join(sections) + '<details><summary>Exact serving settings, development and test</summary>' + table(pbody) + '''</details>
<p class="note">¹ Development search trial 11 repeated trial 10's exact settings. ² Point wall time includes client startup and export work; server launch and separate prefix warmup are excluded. It is not the throughput denominator. p99 and per-class tails are descriptive with these sample sizes. Test baseline ranges reflect two observed runs, not statistical confidence bounds.</p>
<p><a href="ANALYSIS.md">Analysis</a> · <a href="points.csv">Raw aggregate CSV</a> · <a href="class-points.csv">Per-class CSV</a> · <a href="index.html">All curves</a></p>
<script>document.getElementById('load').addEventListener('change',e=>document.querySelectorAll('section[data-load]').forEach(s=>s.hidden=s.dataset.load!==e.target.value));</script></html>'''
    (OUT / 'comparison.html').write_text(document)
    print(f'Wrote {OUT / "comparison.html"}; all 15 held-out and 10 selected development points represented.')


if __name__ == '__main__':
    main()
