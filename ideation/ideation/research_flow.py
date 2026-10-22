"""Typed evidence-to-experiment records in the existing append-only memory.

The host agent authors claims/proposals; these tools check provenance and
readiness, retain uncertainty, and never execute paper code or GPU commands.
"""
import json
import math
import re
from pathlib import Path

from .hypothesis_memory import HypothesisMemory, digest, encoded
from .store import Store, content_fingerprint, now


def clean(value):
    return json.loads(json.dumps(value, allow_nan=False))


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field + ' requires nonempty text')
    return value


def estimate_contract(value):
    """Numerical target forecasts are authored estimates, never copied results."""
    if value is None:
        return
    if not isinstance(value, dict) or value.get('origin') != 'agent_estimate':
        raise ValueError('Target prediction requires an agent_estimate object')
    for key in ('metric', 'unit', 'baseline_id', 'workload_id', 'method_version'):
        text(value.get(key), 'prediction.' + key)
    if not value.get('assumptions') or not value.get('uncertainty'):
        raise ValueError('Prediction requires assumptions and uncertainty')
    for key in ('low', 'high'):
        n = value.get(key)
        if isinstance(n, bool) or not isinstance(n, (float, int)) or not math.isfinite(n):
            raise ValueError('Prediction bounds must be finite')
    if value['low'] > value['high']:
        raise ValueError('Prediction bounds reversed')


def roi_policy(selection):
    """Preserve an explicit task waiver; this is an attributed instruction, not approval."""
    required = selection.get('require_roi_screen', True)
    if not isinstance(required, bool):
        raise ValueError('require_roi_screen must be a boolean')
    if required:
        return {'required': True}
    waiver = selection.get('roi_screen_waiver')
    if not isinstance(waiver, dict) or waiver.get('authority') != 'user':
        raise ValueError('Optional ROI screen requires an attributed user waiver')
    for key in ('reason', 'instruction_reference'):
        text(waiver.get(key), 'roi_screen_waiver.' + key)
    return {'required': False, 'waiver': clean(waiver),
            'meaning': 'Recorded task instruction; does not verify authority, scientific merit or execution permission'}


class ResearchFlow:
    def __init__(self, root):
        self.root = Path(root)
        self.memory = HypothesisMemory(self.root / 'research/hypotheses.sqlite')
        self.db = self.memory.db
        # Additive migration: existing hypothesis IDs, source snapshots and events
        # stay authoritative. Typed indexes refer to their immutable graph nodes.
        with self.db:
            self.db.executescript('''
            CREATE TABLE IF NOT EXISTS flow_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS evidence_claims(
              id TEXT PRIMARY KEY REFERENCES nodes(id), source_id TEXT NOT NULL,
              revision_hash TEXT NOT NULL, grounded INTEGER NOT NULL CHECK(grounded IN (0,1)), created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS claims_source ON evidence_claims(source_id,revision_hash);
            CREATE TABLE IF NOT EXISTS research_records(
              id TEXT PRIMARY KEY REFERENCES nodes(id), hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id),
              kind TEXT NOT NULL CHECK(kind IN ('screening','eval_plan','decision')), created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS records_hypothesis ON research_records(hypothesis_id,kind);
            CREATE TABLE IF NOT EXISTS hypothesis_claims(
              hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id), claim_id TEXT NOT NULL REFERENCES evidence_claims(id),
              relation TEXT NOT NULL CHECK(relation IN ('supports','refutes','background')), rationale TEXT NOT NULL,
              PRIMARY KEY(hypothesis_id,claim_id,relation,rationale));
            ''')
            self.db.execute('INSERT OR IGNORE INTO flow_migrations VALUES(1,?)', (now(),))
            for table in ('evidence_claims', 'research_records', 'hypothesis_claims', 'flow_migrations'):
                for op in ('UPDATE', 'DELETE'):
                    self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'research records are immutable'); END")

    def close(self):
        self.db.close()

    def node(self, identifier, kind=None):
        row = self.db.execute('SELECT kind,data FROM nodes WHERE id=?', (identifier,)).fetchone()
        if not row or kind and row['kind'] != kind:
            raise ValueError('Unknown record or wrong record type')
        return json.loads(row['data'])

    def claim(self, record):
        record = clean(record)
        for key in ('source_id', 'claim_text', 'quote'):
            text(record.get(key), key)
        if record.get('claim_type') not in ('measured_result', 'mechanism', 'design', 'limitation', 'other'):
            raise ValueError('Unknown claim type')
        if record.get('verification_status', 'reported') != 'reported':
            raise ValueError('Source extraction creates reported claims, not reproduced measurements')
        corpus = Store(self.root / 'research/corpus.sqlite')
        try:
            source = corpus.get(record['source_id'])
            revision = record.get('revision_hash')
            if revision:
                row = corpus.db.execute('SELECT document FROM document_revisions WHERE id=? AND content_hash=?', (record['source_id'], revision)).fetchone()
                source = corpus.decode(json.loads(row[0])) if row else None
            if not source:
                raise ValueError('Source revision unavailable')
            revision = content_fingerprint(source)
        finally:
            corpus.db.close()
        quote = record['quote']
        if len(quote) < 12 or len(quote) > 2000:
            raise ValueError('Use a short inspectable exact excerpt (12..2000 characters)')
        field = 'body' if quote in source['body'] else 'title' if quote in source['title'] else None
        if not field:
            raise ValueError('Excerpt does not occur in the pinned source')
        offset = source[field].index(quote)
        locator = {'field': field, 'start': offset, 'end': offset + len(quote), 'url': source['url'],
                   'provider_locator': record.get('locator'), 'scope': 'stored source text offsets, not PDF page coordinates'}
        metric = record.get('reported_metric')
        if metric is not None:
            if not isinstance(metric, dict) or metric.get('origin') != 'author_reported':
                raise ValueError('External numeric result requires author_reported origin')
            for key in ('metric', 'unit', 'baseline', 'conditions'):
                if not metric.get(key):
                    raise ValueError('Reported metric needs units, original baseline and conditions')
            n = metric.get('value')
            if isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n):
                raise ValueError('Reported result value must be finite')
            metric_quote = metric.get('quote')
            if not isinstance(metric_quote, str) or len(metric_quote) < 12 or metric_quote not in source['body']:
                raise ValueError('Reported metric needs its own exact supporting excerpt in this source revision')
        value = {**record, 'revision_hash': revision, 'locator': locator, 'origin': 'external',
                 'grounded': True, 'verification_status': 'reported', 'extraction_version': record.get('extraction_version', 'agent-authored-v1'),
                 'integrity_meaning': 'Exact source-revision quote checked; interpretation and numerical entailment require review'}
        identity = 'claim:' + digest(value)
        with self.memory._transaction():
            source_node = self.memory._node('source', source)
            self.memory._node('claim', value, identity)
            self.db.execute('INSERT OR IGNORE INTO evidence_claims VALUES(?,?,?,?,?)', (identity, record['source_id'], revision, 1, now()))
            self.memory._edge(identity, 'extracted_from', source_node)
            self.memory._event(None, 'claim_recorded', {'claim_id': identity, 'revision_hash': revision}, record.get('actor', 'agent'))
        return {'id': identity, **value}

    def source_claims(self, source_id):
        return [{'id': r[0], **self.node(r[0], 'claim')} for r in self.db.execute('SELECT id FROM evidence_claims WHERE source_id=? ORDER BY created_at,id', (source_id,))]

    def propose(self, record):
        record = clean(record)
        text(record.get('run_id'), 'run_id')
        card, brief = record['card'], record['brief']
        for key in ('id', 'statement', 'mechanism', 'proposed_change', 'falsification_test', 'target_profile_version'):
            text(card.get(key), 'card.' + key)
        if not isinstance(brief.get('baseline'), dict) or not brief['baseline']:
            raise ValueError('Explicit baseline required, with unknowns when necessary')
        if card.get('author_type', 'agent') not in ('agent', 'human'):
            raise ValueError('Proposal author must be agent/human, not source author')
        card.setdefault('author_type', 'agent')
        estimate_contract(card.get('prediction'))
        for key in ('expected_gain_pct', 'expected_gain', 'speedup'):
            if card.get(key) is not None:
                raise ValueError('Use the explicit prediction contract instead of a bare target gain')
        sources, citations, links = {}, [], record.get('claim_links', [])
        for link in links:
            claim = self.node(link['claim_id'], 'claim')
            if link.get('relation') not in ('supports', 'refutes', 'background'):
                raise ValueError('Invalid claim relation')
            text(link.get('rationale'), 'link.rationale')
            edge = self.db.execute("SELECT dst FROM edges WHERE src=? AND relation='extracted_from'", (link['claim_id'],)).fetchone()
            source = self.node(edge[0], 'source')
            previous = sources.get(source['id'])
            if previous and content_fingerprint(previous) != content_fingerprint(source):
                raise ValueError('Separate conflicting revisions into distinct proposals or link them afterward')
            sources[source['id']] = source
            citations.append({'source_id': source['id'], 'quote': claim['quote'], 'revision_hash': claim['revision_hash'],
                              'relation': {'supports': 'supports', 'refutes': 'challenges', 'background': 'context'}[link['relation']]})
        card['evidence'] = citations
        selection = brief.setdefault('selection', {})
        selection.setdefault('require_novelty', False)
        if not isinstance(selection['require_novelty'], bool):
            raise ValueError('Novelty requirement must be a boolean')
        roi_policy(selection)
        identity = self.memory.register('research:' + record['run_id'], card, brief, selection, sources)
        for link in links:
            self.link(identity, **link)
        return {'id': identity, 'hypothesis': self.memory.get(identity), 'target_gain_inherited_from_sources': False}

    def link(self, hypothesis_id, claim_id, relation, rationale):
        if relation not in ('supports', 'refutes', 'background'):
            raise ValueError('Relation must be supports/refutes/background')
        text(rationale, 'rationale')
        self.memory._require(hypothesis_id)
        self.node(claim_id, 'claim')
        with self.memory._transaction():
            self.db.execute('INSERT OR IGNORE INTO hypothesis_claims VALUES(?,?,?,?)', (hypothesis_id, claim_id, relation, rationale))
            self.memory._edge(hypothesis_id, relation + '_claim', claim_id)
            self.memory._event(hypothesis_id, 'evidence_linked', {'claim_id': claim_id, 'relation': relation, 'rationale': rationale})
        return {'hypothesis_id': hypothesis_id, 'claim_id': claim_id, 'relation': relation, 'rationale': rationale}

    def _record(self, kind, hypothesis_id, value, actor='agent'):
        self.memory._require(hypothesis_id)
        if value.get('hypothesis_id', hypothesis_id) != hypothesis_id:
            raise ValueError('Record hypothesis ID conflicts with destination')
        value = clean({**value, 'hypothesis_id': hypothesis_id})
        identity = kind + ':' + digest(value)
        with self.memory._transaction():
            self.memory._node(kind, value, identity)
            self.db.execute('INSERT OR IGNORE INTO research_records VALUES(?,?,?,?)', (identity, hypothesis_id, kind, now()))
            self.memory._edge(hypothesis_id, 'has_' + kind, identity)
            self.memory._event(hypothesis_id, kind + '_recorded', {'record_id': identity}, actor)
        return {'id': identity, **value}

    def screen(self, hypothesis_id, record):
        from .controls import prescreen
        record = clean(record)
        hypothesis = self.memory.get(hypothesis_id)
        provenance = record.get('provenance', {})
        missing = [k for k in ('baseline_id', 'workload_id', 'hardware', 'input_source_ids', 'measurement_origin') if not provenance.get(k)]
        if provenance.get('measurement_origin') and provenance['measurement_origin'] not in ('target_trace', 'reproduced_measurement', 'simulation', 'agent_estimate'):
            raise ValueError('Screen needs target measurement, simulation or explicit agent-estimate provenance; not an author-reported speedup')
        if provenance.get('baseline_id') and provenance['baseline_id'] != hypothesis['baseline']:
            raise ValueError('Screen baseline must match the hypothesis baseline snapshot')
        input_sources = provenance.get('input_source_ids', [])
        corpus = Store(self.root / 'research/corpus.sqlite')
        try:
            if not isinstance(input_sources, list) or any(not corpus.get(s) for s in input_sources):
                raise ValueError('Screen input source IDs must exist')
        finally:
            corpus.db.close()
        if missing:
            result = {'decision': 'defer', 'validated': False, 'target_relative_gain': None,
                      'unknowns': ['Missing target provenance: ' + k for k in missing],
                      'reason': 'insufficient_evidence: supply target timing/trace and workload provenance before estimating service impact'}
        else:
            result = prescreen(record['inputs'])
        return self._record('screening', hypothesis_id, {'tier': 1, 'mode': 'no_gpu', 'method_version': 'exposed-time-v1',
                            'input': record, 'result': result, 'status': 'insufficient_evidence' if missing else 'conditional_estimate',
                            'gpu_calls': 0, 'model_calls': 0})

    def records(self, hypothesis_id, kind=None):
        sql = 'SELECT id FROM research_records WHERE hypothesis_id=?'
        args = [hypothesis_id]
        if kind:
            sql += ' AND kind=?'
            args.append(kind)
        return [{'id': r[0], **self.node(r[0])} for r in self.db.execute(sql + ' ORDER BY created_at,rowid', args)]

    def eval_plan(self, hypothesis_id, manifest):
        from .eval_plan import qualify_plan
        hypothesis = self.memory.get(hypothesis_id)
        result = qualify_plan(manifest, hypothesis)
        links = [dict(r) for r in self.db.execute('SELECT * FROM hypothesis_claims WHERE hypothesis_id=?', (hypothesis_id,))]
        if not any(r['relation'] == 'supports' for r in links):
            result['blocking_gaps'].append('No grounded supporting claim linked to hypothesis')
        screens = self.records(hypothesis_id, 'screening')
        policy = roi_policy(hypothesis['brief'].get('selection', {}))
        result['roi_screen_policy'] = policy
        if policy['required'] and not screens:
            result['blocking_gaps'].append('No hypothesis-linked no-GPU screening record')
        elif policy['required'] and manifest.get('purpose') != 'diagnostic' and (screens[-1]['status'] == 'insufficient_evidence' or screens[-1]['result'].get('decision') in {'defer', 'reject'}):
            result['blocking_gaps'].append('Unresolved/negative screen permits a diagnostic plan, not qualification')
        if policy['required'] and screens and manifest.get('purpose') == 'qualification':
            origin = screens[-1].get('input', {}).get('provenance', {}).get('measurement_origin')
            if origin not in ('target_trace', 'reproduced_measurement'):
                result['blocking_gaps'].append('Simulation/agent-estimate ROI permits diagnosis; qualification needs target trace or reproduced measurement inputs')
        result['readiness'] = 'ready_for_review' if not result['blocking_gaps'] else 'blocked'
        result['execution_authorized'] = False
        return self._record('eval_plan', hypothesis_id, {'manifest': clean(manifest), **result})

    def decide(self, hypothesis_id, record):
        record = clean(record)
        status = record.get('status')
        if status not in ('proposed', 'accepted', 'deferred', 'rejected', 'superseded'):
            raise ValueError('Decision is selection only; measured outcomes belong in experiment registry')
        for key in ('actor', 'rationale', 'reopen_when'):
            text(record.get(key), key)
        if status == 'accepted':
            plan_id = record.get('eval_plan_id')
            plan = self.node(plan_id, 'eval_plan')
            if plan['hypothesis_id'] != hypothesis_id or plan['readiness'] != 'ready_for_review':
                raise ValueError('Acceptance requires this hypothesis\'s review-ready evaluation plan')
        decision = self._record('decision', hypothesis_id, record, record['actor'])
        self.memory.review(hypothesis_id, {'status': status, 'eligible': status == 'accepted', 'decision_id': decision['id']},
                           {'origin': record['actor'], 'rationale': record['rationale'], 'reopen_when': record['reopen_when'], 'meaning': 'Attributed selection, not experimental validation'})
        return decision

    def linked_research(self, hypothesis_id, include_artifacts=False):
        """Read-only projection of retained refinements, never new qualification.

        Retention imports use both evidence/artifacts arrays. Keep their original
        names and all other metadata, with explicit counts for shortened lists.
        """
        result = []
        for row in self.db.execute("""SELECT n.id,n.kind,n.data,e.relation FROM edges e
            JOIN nodes n ON n.id=e.dst WHERE e.src=?
            AND e.relation IN ('has_investigation','has_evidence_bundle')
            AND n.kind IN ('investigation','evidence_bundle') ORDER BY n.rowid""", (hypothesis_id,)):
            value = json.loads(row['data'])
            artifact_lists = {}
            for key in list(value):
                items = value[key]
                if isinstance(items, list) and items and all(isinstance(x, dict) and 'sha256' in x and ('path' in x or 'archive' in x) for x in items):
                    shown = items if include_artifacts else items[:4]
                    artifact_lists[key] = {'total': len(items), 'references': shown,
                                          'omitted': len(items) - len(shown)}
                    del value[key]
            result.append({'id': row['id'], 'kind': row['kind'], 'relation': row['relation'],
                           'record': value, 'artifact_lists': artifact_lists})
        return result

    def dossier(self, hypothesis_id, include_artifacts=False):
        hypothesis = self.memory.get(hypothesis_id)
        links = [dict(r) for r in self.db.execute('SELECT * FROM hypothesis_claims WHERE hypothesis_id=?', (hypothesis_id,))]
        corpus = Store(self.root / 'research/corpus.sqlite')
        try:
            for link in links:
                claim = self.node(link['claim_id'], 'claim')
                source = corpus.get(claim['source_id'])
                link.update(claim=claim, newer_source_revision=bool(source and content_fingerprint(source) != claim['revision_hash']))
        finally:
            corpus.db.close()
        from .experiments import ExperimentRegistry
        registry = ExperimentRegistry(self.root)
        try:
            experiments = registry.list(hypothesis_id=hypothesis_id)
        finally:
            registry.close()
        return {'linked_research': self.linked_research(hypothesis_id, include_artifacts),
                'linked_research_projection': 'Original linked conclusions and qualifications; first four references per artifact list unless include_artifacts=true. Selection is unchanged; these records do not independently validate scientific claims.',
                'hypothesis': hypothesis, 'claims': links, 'records': self.records(hypothesis_id), 'experiments': experiments,
                'review_alerts': [r['claim_id'] for r in links if r['newer_source_revision'] or r['relation'] == 'refutes'],
                'meaning': 'Selection, external claims, conditional estimates and scoped experiment results remain separate'}

    def changes(self, cursor=0, limit=100):
        if cursor < 0 or not 1 <= limit <= 500:
            raise ValueError('Invalid cursor/limit')
        corpus = Store(self.root / 'research/corpus.sqlite')
        try:
            rows = corpus.db.execute('SELECT rowid,id,content_hash,observed_at FROM document_revisions WHERE rowid>? ORDER BY rowid LIMIT ?', (cursor, limit + 1)).fetchall()
            more = len(rows) > limit
            changes = []
            for row in rows[:limit]:
                impact = [r[0] for r in self.db.execute('SELECT DISTINCT hc.hypothesis_id FROM hypothesis_claims hc JOIN evidence_claims c ON c.id=hc.claim_id WHERE c.source_id=? AND c.revision_hash<>?', (row['id'], row['content_hash']))]
                changes.append({'cursor': row['rowid'], 'source_id': row['id'], 'revision_hash': row['content_hash'], 'observed_at': row['observed_at'], 'hypotheses_to_review': impact})
            return {'changes': changes, 'next_cursor': changes[-1]['cursor'] if changes else cursor, 'has_more': more,
                    'meaning': 'Observed revision changes; review triggers, not automatic scientific verdicts. Save next_cursor only after consuming page.'}
        finally:
            corpus.db.close()


def retain_reasoned_packet(root, packet_path, hypothesis_run):
    """Bridge existing optional model workflow into typed claims, without re-generation."""
    packet = json.loads(Path(packet_path).read_text())
    if not packet.get('quote_validation', {}).get('valid'):
        raise ValueError('Evidence packet did not pass quote validation')
    sources = {s['id']: s for s in packet['sources']}
    flow = ResearchFlow(root)
    retained = []
    try:
        for claim in packet['claims']:
            source = sources[claim['source_id']]
            # Existing model output permits whitespace-normalized quotes. Retain
            # exact source bytes for this typed claim and a reproducible locator.
            pattern = r'\s+'.join(re.escape(w) for w in claim['quote'].split())
            match = re.search(pattern, source['body']) or re.search(pattern, source['title'])
            quote = match.group() if match else claim['quote']
            value = flow.claim({'source_id': source['id'], 'revision_hash': content_fingerprint(source),
                'claim_text': claim['claim'], 'claim_type': 'other', 'quote': quote,
                'extraction_version': 'existing-evidence-packet-v1',
                'reported_result_text': claim.get('reported_result'), 'conditions': claim.get('conditions'),
                'limitations': claim.get('limitations'), 'packet_claim_id': claim.get('id')})
            retained.append(value)
        links = 0
        for row in flow.db.execute('SELECT id FROM hypotheses WHERE run=?', (str(Path(hypothesis_run).resolve()),)).fetchall():
            hypothesis = flow.memory.get(row['id'])
            for citation in hypothesis['card'].get('evidence', []):
                for claim in retained:
                    if claim['source_id'] == citation['source_id'] and ' '.join(claim['quote'].split()) == ' '.join(citation['quote'].split()):
                        flow.link(row['id'], claim['id'], {'supports':'supports','challenges':'refutes','context':'background'}[citation['relation']], 'Exact source/excerpt correspondence with generated proposal; entailment remains review judgment')
                        links += 1
        return {'claim_ids': [c['id'] for c in retained], 'linked_citations': links,
                'note': 'Only exact excerpt matches become typed links; other citations remain in original immutable hypothesis record. Selection is not eval-plan approval.'}
    finally:
        flow.close()
