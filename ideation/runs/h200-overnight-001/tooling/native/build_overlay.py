"""CPU-only reproducible observation overlays with exact removal provenance."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
BASE = RUN / 'developer/source/vllm/v1/worker/gpu'
DEV = RUN / 'developer/integration/overlay/vllm/v1/worker/gpu'
DEST = '/usr/local/lib/python3.12/dist-packages/vllm/v1/worker/gpu'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = []
    def emit(source, relative, edits, arms, **extra):
        old = source.read_text(); updated = old
        for before, after in edits:
            if updated.count(before) != 1: raise AssertionError(f'patch anchor ambiguous: {relative}')
            updated = updated.replace(before, after)
        ast.parse(updated)
        stripped = updated
        for before, after in reversed(edits):
            if stripped.count(after) != 1: raise AssertionError('observation removal ambiguous')
            stripped = stripped.replace(after, before)
        if stripped != old: raise AssertionError('observation removal changed original source')
        path = HERE / 'overlay' / ('both' if len(arms) == 2 else arms[0]) / relative
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(updated)
        files.append(dict(source=str(path), destination=DEST + '/' + relative, sha256=sha(path),
                          arms=arms, observation_removal_sha256=sha(source), **extra))
    capture_anchor = '        assert self.cudagraph_manager is not None\n        capture_encoder = ('
    capture_hook = '        assert self.cudagraph_manager is not None\n        from vllm.v1.worker.gpu.c25_native_observer import begin_capture\n        begin_capture(self, profile_only=profile_only)\n        capture_encoder = ('
    return_anchor = '        return cuda_graph_size\n'
    return_hook = '        if not profile_only:\n            from vllm.v1.worker.gpu.c25_native_observer import run_native\n            run_native(self)\n        return cuda_graph_size\n'
    emit(BASE/'model_runner.py', 'model_runner.py', [(capture_anchor,capture_hook),(return_anchor,return_hook)], ['A','B'], base_sha256=sha(BASE/'model_runner.py'))
    sample_anchor = '        self._sample_sequential(num_reqs, head_hidden)\n'
    sample_hook = '        from vllm.v1.worker.gpu.c25_native_observer import observe_sampling\n        with observe_sampling(self, num_reqs, num_tokens_padded, head_hidden):\n            self._sample_sequential(num_reqs, head_hidden)\n'
    rel='spec_decode/dspark/speculator.py'
    emit(BASE/rel, rel, [(sample_anchor,sample_hook)], ['A'], base_sha256=sha(BASE/rel))
    emit(DEV/rel, rel, [(sample_anchor,sample_hook)], ['B'], replaces_candidate_sha256=sha(DEV/rel))
    for source,destination in ((HERE/'c25_native_observer.py', DEST+'/c25_native_observer.py'),
                               (BASE/rel, '/opt/c25-native/reference_dspark.py')):
        files.append(dict(source=str(source), destination=destination, sha256=sha(source), arms=['A','B']))
    manifest={'schema_version':1, 'files':files,
      'review_inputs':[str(HERE/name) for name in ('parse_native.py','test_native.py','build_overlay.py','build_traffic_manifest.py')] + [str(RUN/'tooling-evidence/native'/name) for name in ('BUILD_REVIEW.md','tests.txt','build-receipt.json')] + [str(RUN/'native-root/additional-source-manifest.json')], 'output_mount':'/c25-native-out',
      'env':['C25_NATIVE_OUTPUT=/c25-native-out','C25_NATIVE_ARM=A|B','C25_NATIVE_REPLICA=0|1','C25_NATIVE_RUN_ID=<unique>'],
      'trigger':'capture_model(profile_only=False), after final target/draft capture and workspace lock, before returning/API readiness',
      'temporary_profile_capture':'begin_capture(profile_only=True) disables observation and retains no profiling-pool references',
      'final_receipt':'replicaN/rankN.json', 'started_receipt':'replicaN/rankN.started.json',
      'pass_predicate':{'status':'passed','restored':True,'native_oracle_passed':True,'capture_attestation_passed':True,'timed_samples':960},
      'candidate_merge':'B speculator entry replaces the exact separately reviewed candidate source hash; all other candidate mounts remain separate'}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__': main()
