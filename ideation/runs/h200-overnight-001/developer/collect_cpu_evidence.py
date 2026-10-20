"""Read-only provenance and safetensors-header audit. No model imports or GPU."""
import datetime, hashlib, json, struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
MODEL=Path('/home/jl_fs/models/DeepSeek-V4.1-Flash')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d): (HERE/n).write_text(json.dumps(d,indent=2)+'\n')
files=[{'path':str(p.relative_to(HERE)), 'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted((HERE/'source').rglob('*.py'))]
write('source-manifest.json', {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image':'vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c','method':'CPU-only docker run --rm --network none; standard-library reads; no --gpus, no model/Torch import','files':files})
idx=json.loads((MODEL/'model.safetensors.index.json').read_text())['weight_map']
names=[n for n in idx if n.endswith('.ffn.gate.weight') or 'markov' in n or 'confidence_head' in n]
headers={}; records=[]
for n in sorted(names):
 p=MODEL/idx[n]
 if p.name not in headers:
  with p.open('rb') as f:
   length=struct.unpack('<Q',f.read(8))[0]; raw=f.read(length)
  headers[p.name]=(json.loads(raw),hashlib.sha256(raw).hexdigest())
 h,s=headers[p.name]; m=h[n]
 records.append({'name':n,'shard':p.name,'dtype':m['dtype'],'shape':m['shape'],'header_sha256':s})
config=json.loads((MODEL/'config.json').read_text())
write('checkpoint-metadata.json',{'model_snapshot':str(MODEL.resolve()),'config_sha256':sha(MODEL/'config.json'),'config_fields':{k:v for k,v in {**config,**config.get('text_config',{})}.items() if k in ('dtype','torch_dtype','vocab_size','draft_vocab_size','dspark_draft_topk','dspark_head_dim','dspark_markov_rank','enable_confidence_head','n_mtp_layers','num_nextn_predict_layers','num_hidden_layers','hidden_size')},'scope':'headers only; no tensor data loaded','records':records})
identity=REPO/'runs/av-k5-timing-001/runtime-identity.json'
# HERE.parents[2] is ideation.
d=json.loads(identity.read_text())
write('effective-config-evidence.json',{'source':str(identity),'source_sha256':sha(identity),'prior_attestation_status':d['status'],'containers':[{'replica':c['replica'],'image':c['configured_image'],'has_watermark_config_flag':any('watermark-config' in x for x in c['engine_args']),'has_config_file_flag':'--config' in c['engine_args'],'has_dtype_override':'--dtype' in c['engine_args'],'speculative_config':c['engine_args'][c['engine_args'].index('--speculative-config')+1]} for c in d['containers']],'derived_watermark_config':None,'derivation':'EngineArgs.watermark_config defaults None; create_watermark_config returns None; no CLI config or explicit flag in attested command. This is source/config inference, not a new object dump.','derived_draft_watermarker':None})
print(json.dumps({'files':len(files),'checkpoint_records':len(records),'gate_count':sum(x['name'].endswith('.ffn.gate.weight') for x in records),'gate_dtypes':sorted(set(x['dtype'] for x in records if x['name'].endswith('.ffn.gate.weight'))),'config':config.get('dtype')}))
