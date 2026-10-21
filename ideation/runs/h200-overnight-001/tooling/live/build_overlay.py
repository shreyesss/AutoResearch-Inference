"""Exact-source reversible additions; never edits original or frozen native inputs."""
from pathlib import Path
import ast
import hashlib
import json
HERE=Path(__file__).resolve().parent
RUN=HERE.parents[1]
NATIVE=RUN/'tooling/native'
BASE=RUN/'developer/source/vllm/v1/worker/gpu'
FRESH=RUN/'native-root/real-request-source/vllm'
PKG='/usr/local/lib/python3.12/dist-packages/vllm/'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files=[]
    def emit(source,relative,edits,arms,**extra):
        old=source.read_text();new=old
        for before,after in edits:
            assert new.count(before)==1,(relative,before)
            new=new.replace(before,after)
        ast.parse(new);back=new
        for before,after in reversed(edits):back=back.replace(after,before)
        assert back==old
        dest=HERE/'overlay'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(new)
        files.append(dict(source=str(dest),destination=PKG+relative,sha256=sha(dest),arms=arms,
            observation_removal_sha256=sha(source),**extra))
    native=json.loads((NATIVE/'manifest.json').read_text())
    for item in native['files']:
        if item['destination'].endswith('/model_runner.py'):continue
        files.append(item)
    source=NATIVE/'overlay/both/model_runner.py'
    init='            run_native(self)\n'
    batch='        if batch_desc.num_tokens == 0:\n'
    call='                draft_tokens = self.speculator.propose(\n'
    end='            self.req_states.draft_tokens[input_batch.idx_mapping] = draft_tokens\n'
    emit(source,'v1/worker/gpu/model_runner.py',[
        (init,init+'            from vllm.v1.worker.gpu.c25_live_observer import initialize\n            initialize(self)\n'),
        (batch,'        from vllm.v1.worker.gpu.c25_live_observer import prepare_batch\n        prepare_batch(self, batch_req_state, batch_desc, dummy_run)\n'+batch),
        (call,'                from vllm.v1.worker.gpu.c25_live_observer import begin, end\n                c25_live_call = begin(self, input_batch)\n'+call),
        (end,'                end(self, c25_live_call, async_output)\n'+end)
    ],['A','B'],base_sha256=sha(BASE/'model_runner.py'),replaces_native_sha256=sha(source))
    dflash=BASE/'spec_decode/dflash/speculator.py'
    point='        num_tokens_padded = batch_desc.num_tokens\n'
    emit(dflash,'v1/worker/gpu/spec_decode/dflash/speculator.py',[(point,
        '        self._c25_live_descriptor = batch_desc  # Raw identity only; formatted after end event.\n'+point)],['A','B'],base_sha256=sha(dflash))
    source=BASE/'async_utils.py'
    point='        return self.model_runner_output\n\n\nclass AsyncPoolingOutput'
    emit(source,'v1/worker/gpu/async_utils.py',[(point,
        '        from vllm.v1.worker.gpu.c25_live_observer import output_ready\n        output_ready(self, self.model_runner_output)\n'+point)],['A','B'],base_sha256=sha(source))
    source=FRESH/'v1/worker/gpu_worker.py'
    point='    def profile(self, is_start: bool = True, profile_prefix: str | None = None):\n'
    emit(source,'v1/worker/gpu_worker.py',[(point,
        '    def c25_live_timing_flush(self, *, run_id, arm, nonce):\n        from vllm.v1.worker.gpu.c25_live_observer import flush\n        return flush(run_id=run_id, arm=arm, nonce=nonce)\n\n'+point)],['A','B'],base_sha256=sha(source))
    source=FRESH/'entrypoints/launchers/app.py'
    point='    register_api_routers(args, app, supported_tasks, model_config)\n'
    emit(source,'entrypoints/launchers/app.py',[(point,point+
        '    from vllm.v1.worker.gpu.c25_live_api import attach_router as attach_c25_live\n    attach_c25_live(app)\n')],['A','B'],base_sha256=sha(source))
    for name in ('c25_live_observer.py','c25_live_api.py'):
        p=HERE/name;files.append(dict(source=str(p),destination=PKG+'v1/worker/gpu/'+name,sha256=sha(p),arms=['A','B']))
    out=dict(schema_version=1,files=files,review_inputs=[str(HERE/p) for p in ('build_overlay.py','parse_live.py','test_live.py','run_traffic.py','pool_preflight.py','build_traffic_manifest.py')] + [str(RUN/'tooling-evidence/live'/p) for p in ('BUILD_REVIEW.md','tests.txt','source-audit.json','build-receipt.json')] + [str(HERE/'pool-preflight-manifest.json')],
        output_mount='/c25-native-out',live_output_mount='/c25-live-out',
        env=native['env']+['C25_LIVE_OUTPUT=/c25-live-out','C25_LIVE_ARM=A|B','C25_LIVE_REPLICA=0|1','C25_LIVE_RUN_ID=<unique>'],
        final_receipt=native['final_receipt'],started_receipt=native['started_receipt'],pass_predicate=native['pass_predicate'],
        live_ready_receipt='replicaN/rankN.ready.json',live_final_receipt='replicaN/rankN.json',
        live_pass_predicate=dict(status='passed',overflow=0,unfinished_calls=0,missing_outputs=0),
        trigger='unchanged native qualification after final capture, then live event pool initialization before API readiness')
    (HERE/'manifest.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
