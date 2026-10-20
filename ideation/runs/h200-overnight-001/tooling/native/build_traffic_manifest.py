"""Freeze the twenty independent fixtures and root command templates."""
from pathlib import Path
import hashlib
import json
from controlled_traffic import TOKEN_IDS,CAPS,TOKENIZER_SHA256,CONFIG_SHA256,completion_body,row_token
HERE=Path(__file__).resolve().parent
PYTHON='/home/ubuntu/Deepseek_serve/.venv/bin/python'
ROUTER=Path('/home/ubuntu/Deepseek_serve/lib/router.py')
MODEL=Path('/home/jl_fs/models/DeepSeek-V4.1-Flash')

def main():
    command=[PYTHON,str(HERE/'controlled_traffic.py'),'--base-url','http://127.0.0.1:8000',
      '--backend-urls','http://127.0.0.1:8100','http://127.0.0.1:8101','--model','deepseek-v4.1-flash',
      '--arm','{arm}','--run-id','{run_id}','--identity','{arm_output}/identity.json',
      '--native-observations','{arm_output}/observations','--output','{arm_output}/controlled-traffic.json',
      '--tokenizer-json',str(MODEL/'tokenizer.json'),'--model-config',str(MODEL/'config.json')]
    files=[HERE/name for name in ('controlled_traffic.py','service_rank_control.py','service_lifecycle.py','native_metrics.py')]+[ROUTER,MODEL/'tokenizer.json',MODEL/'config.json']
    manifest={'schema_version':1,'command_template':command,
      'router_command':[PYTHON,str(ROUTER),'--host','127.0.0.1','--port','8000','--backends','http://127.0.0.1:8100','http://127.0.0.1:8101'],
      'router_environment_absent':['DSV41_ROUTER_LOAD_FACTOR','DSV41_ROUTER_RETRY_CONNECTION_ERRORS','DSV41_ROUTER_CONNECTION_LIMIT'],
      'router_difference':'Original unchanged router source; explicit localhost bind confines this controlled pilot to the host and preserves routing semantics.',
      'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
      'total_requests':20,'request_order':'first five per replica concurrently (ten total), then replica0 lifecycle five then replica1 lifecycle five',
      'first_ten':[{'replica':r,'row':i,'body':completion_body('deepseek-v4.1-flash',r,i),'expected_ids':[row_token(r,i)]*CAPS[i]} for r in range(2) for i in range(5)],
      'remaining_per_replica':['one streamed cancel after nonempty singleton prefix, max4096','exact row0 recovery','forced token1 EOS, exactly1/stop','exact row1 wake','natural chat, temperature0, max512; length is inconclusive'],
      'routing':'fixed session SHA256 chooses outer replica; X-data-parallel-rank=0; all response IDs retained',
      'initial_gate':'root identity fresh_exclusive_service=true and no_prior_client_requests=true, matching arm/run_id, eight passed/restored native receipts; observed initial activity/completion counters must be zero, absent series unknown',
      'post_initial_gate':'exactly five rank0 length completions and router requests per replica, all eight running/waiting gauges and router active zero on three one-second polls, deadline60sec',
      'unused_terminal_absence':'None retained only on never-routed ranks1/2/3; any observed positive counter rejects; rank0 counters required',
      'exit_semantics':{'0':'observable fixtures completed; receipt remains pending_external_abort_acceptance or inconclusive_natural_stop','nonzero':'fixture failure; retain partial receipt and all observations'},
      'external_abort_gate':'root immutable container logs must bind exact Added/Aborted/external aborted IDs, ordered request window and DP0 positive witness; independent evaluator accepts separately',
      'budget':'five-minute root wall cap; no retry, no diagnostic/full trace'}
    (HERE/'traffic-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__': main()
