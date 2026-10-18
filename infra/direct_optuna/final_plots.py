"""Plot the finished held-out comparisons from committed CSVs; no GPU required."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parents[2] / 'results/2026-10-18-direct-optuna'
LABELS = {'trial_0': 'B0 before', 'trial_1': 'Search 9', 'trial_2': 'Search 10',
          'trial_3': 'Search 24', 'trial_4': 'B0 after'}
COLORS = {'trial_0': '#111827', 'trial_4': '#737373', 'trial_1': '#3b82f6',
          'trial_2': '#16815a', 'trial_3': '#d97706'}


def main():
    rows = [r for r in csv.DictReader((OUT / 'points.csv').open())
            if r['phase'] == 'confirmation' and r['validated'] == 'True' and r['trial_state'] == 'COMPLETE']
    assert len(rows) == 15, 'This report requires the complete held-out campaign'
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for trial, label in LABELS.items():
        subset = sorted([r for r in rows if r['trial'] == trial], key=lambda r: int(r['concurrency']))
        for ax, key, scale, title, unit in zip(axes,
            ['output_tok_s', 'ttft_p90_ms', 'tpot_p90_ms'], [1, .001, 1],
            ['Throughput ↑', 'p90 TTFT ↓', 'p90 decode TPOT ↓'], ['Output tokens/s', 'Seconds', 'ms/token']):
            ax.plot([int(r['concurrency']) for r in subset], [float(r[key])*scale for r in subset],
                    'o--' if trial in ('trial_0', 'trial_4') else 'o-', color=COLORS[trial], label=label)
            ax.set(xlabel='Concurrent clients', ylabel=unit, title=title, xticks=[16,32,64]); ax.grid(alpha=.2)
    axes[0].legend(fontsize=9)
    fig.suptitle('Held-out operating points · 120 requests/point · same configurations, unseen prompts\n'
                 'Two B0 runs bracket candidates; lines connect measured points, not fitted capacity curves', fontsize=11)
    fig.tight_layout(); fig.savefig(OUT / 'heldout-operating-curves.svg'); plt.close(fig)
    matched = [r for r in rows if r['concurrency'] == '32']
    def dominates(a, b):
        va = [-float(a['output_tok_s']),float(a['ttft_p90_ms']),float(a['tpot_p90_ms'])]
        vb = [-float(b['output_tok_s']),float(b['ttft_p90_ms']),float(b['tpot_p90_ms'])]
        return all(x<=y for x,y in zip(va,vb)) and any(x<y for x,y in zip(va,vb))
    front = [r for r in matched if not any(dominates(s,r) for s in matched)]
    fig, axes = plt.subplots(1, 3, figsize=(15,4.8))
    for ax, xkey, ykey, xs, ys, xlabel, ylabel in [
        (axes[0],'output_tok_s','ttft_p90_ms',1,.001,'Output tokens/s ↑','p90 TTFT seconds ↓'),
        (axes[1],'output_tok_s','tpot_p90_ms',1,1,'Output tokens/s ↑','p90 TPOT ms/token ↓'),
        (axes[2],'ttft_p90_ms','tpot_p90_ms',.001,1,'p90 TTFT seconds ↓','p90 TPOT ms/token ↓')]:
        for r in matched:
            trial=r['trial']; x=float(r[xkey])*xs; y=float(r[ykey])*ys
            ax.scatter(x,y,color=COLORS[trial],marker='*' if r in front else 'o',s=160,label=LABELS[trial])
        ax.set(xlabel=xlabel,ylabel=ylabel);ax.grid(alpha=.2)
    axes[0].legend(fontsize=9)
    fig.suptitle('Held-out three-objective Pareto observations at 32 clients (stars)\n'
                 'Point estimates only; frontier membership is not a significance or service-quality claim', fontsize=11)
    fig.tight_layout();fig.savefig(OUT/'heldout-pareto.svg');plt.close(fig)
    print('Wrote heldout-operating-curves.svg and heldout-pareto.svg from 15 verified points.')


if __name__ == '__main__':
    main()
