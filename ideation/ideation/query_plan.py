"""Validate agent-authored semantic search rounds; never execute a workflow."""
import datetime as dt
import hashlib
import json
import re


def _text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError(field + ' requires bounded nonempty text')
    return ' '.join(value.split())


def _texts(value, field):
    if not isinstance(value, list) or len(value) > 50:
        raise ValueError(field + ' requires a bounded list')
    return [_text(v, field) for v in value]


def _date(value):
    if value is not None:
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError('Dates must be YYYY-MM-DD')
        dt.date.fromisoformat(value)
    return value


def _request(row, after=None, before=None):
    if not isinstance(row, dict):
        raise ValueError('Query/observation must be an object')
    provider = row.get('provider')
    if provider not in ('arxiv', 'openalex', 'local'):
        raise ValueError('Choose arxiv, openalex or local')
    query = _text(row.get('query'), 'query')
    start, end = _date(row.get('after', after)), _date(row.get('before', before))
    if start and end and start >= end:
        raise ValueError('after must precede exclusive before')
    repo = row.get('repo')
    if repo is not None and (provider != 'local' or not isinstance(repo, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo)):
        raise ValueError('repo is a local owner/repository filter')
    match = row.get('match', 'any')
    if match not in ('any', 'all'):
        raise ValueError('Local match must be any or all')
    field = row.get('date_field', 'updated_at')
    if field not in ('created_at', 'updated_at', 'merged_at', 'fetched_at'):
        raise ValueError('Unknown local date field')
    value = {'query': query, 'provider': provider, 'after': start, 'before': end}
    if provider == 'local':
        value.update(repo=repo, match=match, date_field=field)
    return value


def _key(request):
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def compile_plan(question, plan, after=None, before=None):
    if not isinstance(plan, dict):
        raise ValueError('plan must be an object')
    mechanism = _text(plan.get('mechanism'), 'mechanism')
    constraints = plan.get('constraints', {})
    if not isinstance(constraints, dict):
        raise ValueError('constraints must be an object')
    keep = _texts(constraints.get('must_keep', []), 'must_keep')
    allowed = _texts(constraints.get('may_relax', []), 'may_relax')
    if set(keep) & set(allowed):
        raise ValueError('A constraint cannot be both fixed and relaxable')
    rows, prior = plan.get('queries', []), plan.get('observations', [])
    if not isinstance(rows, list) or len(rows) > 12 or not isinstance(prior, list) or len(prior) > 50:
        raise ValueError('At most 12 queries and 50 observations per round')
    stop = _text(plan['stop_reason'], 'stop_reason') if plan.get('stop_reason') else None
    if not rows and not stop:
        raise ValueError('Supply queries or an explicit stop_reason')
    observations, by_key = [], {}
    for row in prior:
        request = _request(row)
        status = row.get('status')
        if status not in ('useful', 'irrelevant', 'empty', 'error', 'redundant'):
            raise ValueError('Unknown search observation status')
        observation = {**request, 'status': status, 'reason': _text(row.get('reason'), 'observation.reason'),
                       'source_ids': _texts(row.get('source_ids', []), 'source_ids')}
        observations.append(observation)
        by_key.setdefault(_key(request), []).append(observation)
    recipes, seen, warnings = [], set(), []
    for row in rows:
        request = _request(row, after, before)
        identity = _key(request)
        relaxes = _texts(row.get('relaxes', []), 'relaxes')
        if any(item not in allowed or item in keep for item in relaxes):
            raise ValueError('Relaxation must be permitted by constraints.may_relax')
        for key, widened in (
            ('after', after is not None and (request['after'] is None or request['after'] < after)),
            ('before', before is not None and (request['before'] is None or request['before'] > before)),
        ):
            if widened and key not in relaxes:
                raise ValueError('Widening ' + key + ' requires an allowed, recorded relaxation')
        previous = by_key.get(identity, [])
        duplicate = identity in seen
        seen.add(identity)
        if duplicate or previous:
            warnings.append({'query_id': identity, 'kind': 'repeat',
                             'meaning': 'Exact request repeated; supply a retry reason or choose a new question. Cache hits are not independent evidence.'})
        recipe = {**request, 'query_id': identity, 'purpose': _text(row.get('purpose'), 'purpose'),
                  'why': _text(row.get('why'), 'why'), 'based_on': _texts(row.get('based_on', []), 'based_on'),
                  'relaxes': relaxes, 'previous_observations': previous, 'duplicate_in_round': duplicate}
        if request['provider'] == 'local':
            recipe['local'] = {k: v for k, v in request.items() if k != 'provider'}
        else:
            recipe['paper_search'] = {'query': request['query'], 'providers': [request['provider']],
                                      'after': request['after'], 'before': request['before']}
        recipes.append(recipe)
    return {'version': 2, 'mode': 'agent_authored', 'question': question, 'mechanism': mechanism,
            'constraints': {'must_keep': keep, 'may_relax': allowed}, 'queries': recipes,
            'observations': observations, 'open_questions': _texts(plan.get('open_questions', []), 'open_questions'),
            'stop_reason': stop, 'warnings': warnings,
            'limits': {'max_queries': 12, 'network_calls': 0, 'model_calls': 0},
            'notes': ['Host agent authors semantic expansion and chooses queries; recipes do not execute themselves.',
                      'Reasons, relevance labels and source links are agent judgments, not verified evidence.',
                      'Date widening and declared relaxations are checked; other semantic constraints require review.',
                      'Combine papers and implementation evidence; provider mirrors are not independent corroboration.']}
