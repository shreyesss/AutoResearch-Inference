"""Check committed research metadata and recompute metrics from archived requests.

Standard-library only. No Docker, network or GPU workload is started.
"""
import csv
import hashlib
import json
import math
import re
import tarfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/2026-10-18-direct-optuna'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def quantile(values, percentile):
    values = sorted(values)
    rank = (len(values) - 1) * percentile / 100
    lo, hi = math.floor(rank), math.ceil(rank)
    return values[lo] + (values[hi] - values[lo]) * (rank - lo)


def same(a, b):
    assert math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-7), (a, b)


def main():
    registry = json.loads((ROOT / 'results/registry.json').read_text())
    for entry in registry['studies']:
        for key in ('report', 'comparison', 'evidence_manifest', 'config'):
            if key in entry:
                assert (ROOT / entry[key]).is_file(), entry[key]
    imported = ROOT / 'b200-bench-analysis'
    sources = json.loads((ROOT / 'docs/B200_SOURCE_MANIFEST.json').read_text())
    for entry in sources['files']:
        path = imported / entry['path']
        assert path.stat().st_size == entry['bytes'] and sha(path) == entry['sha256'], path
    assert len(json.loads((imported / 'pareto-data.json').read_text())) == 255
    evidence = OUT / 'evidence'
    manifest = json.loads((evidence / 'manifest.json').read_text())
    archive = evidence / manifest['archive']
    assert sha(archive) == manifest['archive_sha256']
    rows = list(csv.DictReader((OUT / 'points.csv').open()))
    classes = list(csv.DictReader((OUT / 'class-points.csv').open()))
    lookup = {(r['phase'],r['trial'],r['concurrency'],r['class']): r for r in classes}
    totals = {}
    per_phase_points = {}
    with tarfile.open(archive, 'r:gz') as bundle:
        for row in rows:
            assert row['validated'] == 'True' and row['trial_state'] == 'COMPLETE'
            native = row['native'].removeprefix('.artifacts/optuna-direct-v1/')
            data = json.load(bundle.extractfile(native))['benchmarks'][0]
            records = data['requests']['successful']
            counts = data['scheduler_metrics']['requests_made']
            assert len(records) == int(row['successful']) == counts['successful']
            assert counts['errored'] == counts['incomplete'] == int(row['errored']) == int(row['incomplete']) == 0
            seen = set()
            for r in records:
                body = json.loads(r['request_args'])['body']
                assert r['output_tokens'] == body.get('max_completion_tokens',body.get('max_tokens'))
                prompt = json.dumps(body['messages'], sort_keys=True)
                assert prompt not in seen
                seen.add(prompt)
            for label, key in [('ttft','time_to_first_token_ms'),('tpot','inter_token_latency_ms')]:
                for q in (50,90,99):
                    same(row[f'{label}_p{q}_ms'],quantile([r[key] for r in records],q))
            for csvkey, nativekey in [('output_tok_s','output_tokens_per_second'),('requests_s','requests_per_second')]:
                same(row[csvkey],data['metrics'][nativekey]['total']['mean'])
            for cls in ('chat','agent','code','document'):
                group = [r for r in records if re.search(r'Request (?:dev|test)-[ab]-\d+-'+cls, r['request_args'] or '')
                         and r['request_end_time'] >= data['start_time'] and r['request_start_time'] <= data['end_time']]
                if not group:
                    continue
                cr = lookup[row['phase'],row['trial'],row['concurrency'],cls]
                assert len(group) == int(cr['count'])
                for label,key in [('ttft','time_to_first_token_ms'),('tpot','inter_token_latency_ms')]:
                    for q in (50,90,99):
                        same(cr[f'{label}_p{q}_ms'],quantile([r[key] for r in group],q))
            totals[row['phase']] = totals.get(row['phase'],0)+len(records)
            per_phase_points[row['phase']] = per_phase_points.get(row['phase'],0)+1
    assert totals == {'calibration':168,'confirmation':1800,'search':6000},totals
    docs = [ROOT/'README.md', ROOT/'infra/README.md', ROOT/'infra/DIRECT_OPTUNA_RUN.md',
            ROOT/'infra/direct_optuna/README.md', ROOT/'configs/README.md', ROOT/'results/README.md',
            ROOT/'docs/B200_REFERENCE.md', OUT/'README.md', evidence/'README.md', *ROOT.glob('docs/*.md')]
    checked_links = 0
    for doc in docs:
        for dest in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if dest.startswith(('http:','https:','mailto:','#')):
                continue
            target = unquote(dest.split('#')[0])
            assert (doc.parent/target).exists(), (str(doc.relative_to(ROOT)),dest)
            checked_links += 1
    result = {'registry_entries':len(registry['studies']), 'unchanged_imported_files':len(sources['files']),
              'native_points_recomputed':len(rows), 'points_per_phase':per_phase_points,
              'validated_request_counts':totals, 'aggregate_and_class_percentiles_match_native':True,
              'checked_document_links':checked_links, 'gpu_work_started':False}
    (ROOT/'results/research-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
