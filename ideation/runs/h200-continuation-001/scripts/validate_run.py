"""Validate retained research provenance and current continuation, without model/GPU calls."""
import csv
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from ideation.continuation import load_context
from ideation.evidence import quote_errors
from ideation.store import now


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


checks = {}
manifest = read(RUN / 'sources/primary-manifest.json')
count = 0
for entry in manifest:
    assert not entry['errors'], entry
    root = RUN / 'sources' / (entry['repo'].replace('/', '--') + '--' + str(entry['number']))
    for name, record in entry['files'].items():
        assert digest(root / name) == record['sha256'], (entry['url'], name)
        count += 1
checks['primary_files_hash_verified'] = count
archive = RUN / 'sources/feed-openings.jsonl.gz'
receipt = read(RUN / 'sources/feed-openings-manifest.json')
assert digest(archive) == receipt['archive_sha256']
raw = gzip.decompress(archive.read_bytes())
assert hashlib.sha256(raw).hexdigest() == receipt['raw_sha256']
openings = [json.loads(line) for line in raw.splitlines()]
identities = {d['id'] for d in openings}
feeds = read(RUN / 'discovery/feed-coverage.json')
assert identities == {i for row in feeds for i in row['ids']}
assert len(identities) == len(openings) == 2202
checks['opening_archive_records_verified'] = len(identities)
checks['feeds_complete_for_requested_scope'] = sum(x['complete_for_interval'] for x in feeds)
checks['feeds_still_capped'] = [x['repo'] for x in feeds if not x['complete_for_interval']]
rows = list(csv.DictReader((RUN / 'discovery/topic-ledger.csv').open()))
assert len(rows) == len({x['id'] for x in rows}) == 8908
assert sum(x['depth'] == 'title_only' for x in rows) == 1122
assert sum(not x['topics'] for x in rows) == 525
checks['topic_ledger_identities'] = len(rows)
for name in ['combined-evidence.json', 'followup-evidence.json']:
    packet = read(RUN / name)
    assert not quote_errors(packet['claims'], packet['sources'])
    checks[name] = {'sources': len(packet['sources']), 'claims': len(packet['claims']), 'quotes_valid': True}
for directory in ['hypotheses', 'eligibility-followup']:
    run = RUN / directory
    status = read(run / 'manifest.json')['status']
    assert status in {'completed', 'completed_no_selection'}, status
    history = read(run / 'history.json')
    sources = read(run / 'sources.json')
    errors = {row['card']['id']: quote_errors(row['card']['evidence'], sources) for row in history}
    actual = {identity: value for identity, value in errors.items() if value}
    if directory == 'hypotheses':
        assert actual == {'h200-continuation-001:H02': ['Unknown source: runs/c03-mechanism-review-001/REPORT.md']}, actual
        assert next(row for row in history if row['card']['id'] == 'h200-continuation-001:H02')['assessment']['status'] == 'rejected'
    else:
        assert not actual, actual
    checks[directory] = {'status': status, 'proposal_instances': len(history), 'retained_quote_failures': actual}
original, reproduced = read(RUN / 'av-cost-counterexample.json'), read(RUN / 'av-cost-reproduction.json')
original.pop('source'); reproduced.pop('source')
assert original == reproduced
checks['cpu_probe_reproduced_from_retained_source'] = True
assert 'Ran 58 tests' in (RUN / 'software-tests-final.log').read_text()
assert (RUN / 'software-tests-final.log').read_text().rstrip().endswith('OK')
checks['software_tests_passed'] = 58
current = load_context(RUN / 'handoff-003/continuation.json')
assert len(current['families']) == 36
checks['latest_handoff_valid_families'] = len(current['families'])
for number in ['001', '002']:
    path = RUN / f'handoff-{number}/continuation.json'
    old = load_context(path, check=False)
    for item in old['inputs']:
        assert digest(path.parent / item['snapshot']) == item['sha256']
    try:
        load_context(path)
    except ValueError as error:
        assert 'changed input' in str(error)
    else:
        raise AssertionError('Old handoff must detect the legitimate register update')
checks['historical_snapshots_intact_and_old_inputs_detected_stale'] = True
files = list(RUN.glob('*.md')) + [PROJECT / 'docs' / name for name in ['CONTINUATION.md', 'HYPOTHESIS_ROI.md', 'CORPUS_AUDIT_2026-10-21.md']]
files += [PROJECT / 'hypotheses' / name for name in ['C24.md', 'C25.md', 'C26.md']]
broken = []
for path in files:
    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if link.startswith(('http:', 'https:', '#', 'mailto:')):
            continue
        target = link.split('#', 1)[0]
        if (path.parent / target).resolve() == RUN / 'validation.json':
            continue  # This receipt is written only after every check succeeds.
        if not (path.parent / target).exists():
            broken.append([str(path), link])
assert not broken, broken
checks['local_navigation_links_valid'] = len(files)
result = {'at': now(), 'checks': checks, 'gpu_experiments': 0,
          'scope': 'Software, archive/quote integrity and continuation checks; no proof of source entailment, exhaustive recall or service gain.'}
(RUN / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
