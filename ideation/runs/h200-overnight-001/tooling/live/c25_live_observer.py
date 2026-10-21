"""Bounded actual-request proposal observer; identical A/B observation only."""
from __future__ import annotations
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import threading
import time

CAPACITY = 65536
_STATE = None


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, sort_keys=True, allow_nan=False) + '\n')
    temp.replace(path)


def descriptor(value):
    result = dataclasses.asdict(value)
    result['cg_mode'] = value.cg_mode.name
    return result


class EventPool:
    """The engineering preflight uses this exact initialization and resolution."""
    def __init__(self):
        import torch
        start = time.monotonic()
        free_before,total_before = torch.cuda.mem_get_info()
        rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self.stream = torch.cuda.current_stream()
        self.pairs = [(torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True))
                      for _ in range(CAPACITY)]
        for a, b in self.pairs:
            a.record(self.stream)
            b.record(self.stream)
        self.pairs[-1][1].synchronize()
        self.initialization = {'seconds': time.monotonic() - start,
            'capacity': CAPACITY, 'events': 2 * CAPACITY,
            'rss_max_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'rss_max_before_kib': rss_before, 'device_free_before_bytes':free_before,
            'device_total_bytes':total_before,'device_free_after_bytes':torch.cuda.mem_get_info()[0],
            'memory_scope':'CUDA event resources may be outside torch allocator; device free includes other processes',
            'cuda_memory_allocated': torch.cuda.memory_allocated(),
            'cuda_memory_reserved': torch.cuda.memory_reserved()}

    def resolve(self, indices):
        started = time.monotonic()
        indices = list(indices)
        if indices:
            self.pairs[max(indices)][1].synchronize()
        values = [self.pairs[index][0].elapsed_time(self.pairs[index][1]) * 1000 for index in indices]
        return values, time.monotonic() - started


def initialize(runner):
    global _STATE
    if not os.environ.get('C25_LIVE_RUN_ID'):
        return
    import torch
    if _STATE is not None:
        raise AssertionError('live observer initialized twice')
    if os.environ.get('VLLM_DISABLE_REQUEST_ID_RANDOMIZATION') not in (None, '', '0'):
        raise AssertionError('unreviewed request ID policy')
    rank = int(runner.speculator.dp_rank)
    replica = int(os.environ['C25_LIVE_REPLICA'])
    base = Path(os.environ['C25_LIVE_OUTPUT']) / f'replica{replica}' / f'rank{rank}'
    if any(Path(str(base)+suffix).exists() for suffix in ('.json','.ready.json','.started.json','.records.jsonl')):
        raise AssertionError('refusing to overwrite live observer evidence')
    identity = dict(schema_version=1, run_id=os.environ['C25_LIVE_RUN_ID'],
        arm=os.environ['C25_LIVE_ARM'], replica=replica, rank=rank, pid=os.getpid(),
        pid_start_ticks=int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]),
        gpu_uuid=str(torch.cuda.get_device_properties(runner.device).uuid),
        observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    atomic(str(base) + '.started.json', dict(identity, started_unix_s=time.time()))
    pool = EventPool()
    _STATE = dict(identity=identity, base=base, pool=pool, active=True,
        lock=threading.Lock(), records=[], pending={}, real_calls=0, dummy_calls=0,
        overflow=0, errors=[], activation=getattr(runner.speculator, '_c25_activation', {'active':False}),
        init_unix_s=time.time())
    atomic(str(base) + '.ready.json', dict(identity, status='ready', initialization=pool.initialization))


def prepare_batch(runner, batch_state, batch_desc, dummy_run):
    state = _STATE
    if state is None or not state['active']:
        return
    if dummy_run:
        state['dummy_calls'] += 1
        runner._c25_live_batch = None
        return
    slots = batch_state.idx_mapping_np.tolist()
    runner._c25_live_batch = dict(req_ids=list(batch_state.req_ids), slots=slots,
        scheduled_tokens=batch_state.num_scheduled_tokens.tolist(),
        scheduled_drafts=(batch_state.num_draft_tokens_np.tolist() if batch_state.num_draft_tokens_np is not None else [0]*len(slots)),
        prefill_flags=batch_state.is_prefilling_np.tolist(), has_prefill=bool(batch_state.has_prefill),
        computed_context_upper=runner.req_states.num_computed_tokens_np[batch_state.idx_mapping_np].tolist(),
        requested_target={'num_reqs':len(slots), 'num_tokens':int(batch_state.num_tokens)},
        target=descriptor(batch_desc))


def begin(runner, input_batch):
    state = _STATE
    if state is None or not state['active']:
        return None
    import torch
    state['real_calls'] += 1
    if len(state['records']) + len(state['pending']) >= CAPACITY:
        state['overflow'] += 1
        return None
    index = state['real_calls'] - 1
    record = dict(runner._c25_live_batch)
    record.update(call_index=index, time_unix_s=time.time(),
        context_upper=input_batch.seq_lens_cpu_upper_bound[:input_batch.num_reqs].tolist(),
        actual_rows=int(input_batch.num_reqs), actual_target_tokens=int(input_batch.num_tokens),
        padded_target_rows=int(input_batch.num_reqs_after_padding), padded_target_tokens=int(input_batch.num_tokens_after_padding),
        requested_draft={'num_reqs':int(input_batch.num_reqs), 'num_tokens':int(input_batch.num_reqs*runner.speculator.num_query_per_req)},
        stream=int(torch.cuda.current_stream().cuda_stream), output=None,
        yield_join='unjoined_unknown', slot_generation='request_id; preemption generation unknown')
    if record['stream'] != int(state['pool'].stream.cuda_stream):
        raise AssertionError('proposal changed observer stream')
    runner.speculator._c25_live_descriptor = None
    state['pending'][index] = record
    # No metadata, allocation, or logging after this marker and before propose.
    state['pool'].pairs[index][0].record(state['pool'].stream)
    return index


def end(runner, index, async_output):
    state = _STATE
    if index is None:
        return
    # First observer action after the original propose returns.
    state['pool'].pairs[index][1].record(state['pool'].stream)
    record = state['pending'].pop(index)
    record['draft'] = descriptor(runner.speculator._c25_live_descriptor)
    state['records'].append(record)
    async_output._c25_live_call = record


def output_ready(async_output, model_output):
    state = _STATE
    record = getattr(async_output, '_c25_live_call', None)
    if record is None or state is None:
        return
    # Runs after the original get_output's existing synchronization, in its worker.
    value = dict(req_ids=list(model_output.req_ids),
        num_sampled_tokens=async_output.num_sampled_tokens_np.tolist(),
        sampled_token_ids=[list(row) for row in model_output.sampled_token_ids],
        output_worker_pid=os.getpid(), yield_join='prior verification; no per-proposal join claimed')
    with state['lock']:
        if record['output'] is not None:
            state['errors'].append('duplicate output callback')
        record['output'] = value


def flush(*, run_id, arm, nonce):
    state = _STATE
    if state is None or not state['active']:
        raise AssertionError('observer absent or already flushed')
    if state['identity']['run_id'] != run_id or state['identity']['arm'] != arm or not isinstance(nonce,str) or not nonce:
        raise AssertionError('flush identity mismatch')
    state['active'] = False
    with state['lock']:
        # Deep CPU snapshot prevents callback-thread mutation during export.
        records = json.loads(json.dumps(state['records']))
        errors = list(state['errors'])
    # Missing end markers are incomplete: never synchronize an unrecorded pair.
    values, seconds = state['pool'].resolve(record['call_index'] for record in records)
    for record, value in zip(records, values):
        record['duration_us'] = value
    missing_outputs = sum(record['output'] is None for record in records)
    good = (not state['pending'] and not state['overflow'] and not missing_outputs and
        not errors and len(records) == state['real_calls'] and
        all(math.isfinite(v) and v > 0 for v in values))
    raw = Path(str(state['base']) + '.records.jsonl')
    if raw.exists():
        raise AssertionError('refusing to overwrite live data')
    with raw.open('x') as out:
        for record in records:
            out.write(json.dumps(record, sort_keys=True, allow_nan=False)+'\n')
    receipt = dict(state['identity'], status='passed' if good else 'incomplete', nonce=nonce,
        initialization=state['pool'].initialization, flush_seconds=seconds,
        real_calls=state['real_calls'], dummy_calls=state['dummy_calls'],
        admitted_calls=len(records), overflow=state['overflow'], unfinished_calls=len(state['pending']),
        missing_outputs=missing_outputs, errors=errors, activation=state['activation'],
        stream=int(state['pool'].stream.cuda_stream), records_path=raw.name,
        records_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(), ended_unix_s=time.time(),
        phase='classified offline by exact client response/request IDs',
        scope='instrumented real-request proposal main-stream span; not ITL or full GPU work')
    atomic(str(state['base']) + '.json', receipt)
    return {k:receipt[k] for k in ('run_id','arm','rank','replica','status','nonce')}
