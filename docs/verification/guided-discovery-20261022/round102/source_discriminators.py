"""Finite combinatorial controls, not native scheduler or workload simulation."""
from pathlib import Path
import json,collections,math
B=Path(__file__).parent
# Source-derived task enumeration within one locality domain.
M,N=4,9
original=[(t//N,t%N) for t in range(M*N)]
naive=[(t%M,t//M) for t in range(M*N)]
claimed=N # target guard for pool block0 is counter >= one local N stripe
required={(0,n) for n in range(N)}
missing=sorted(required-set(naive[:claimed]));assert not(required-set(original[:claimed]));assert missing
# Two legal unique-top6 routing assignments with the SAME physical row count.
T_per_rank=8;EP=4;E=384;K=6;BM=16
spread=[[(t*K+j)%E for j in range(K)] for t in range(T_per_rank*EP)]
hot=[[0,64,128,192,256,320] for _ in range(T_per_rank*EP)]
def counts(routes):
 assert all(len(set(row))==K for row in routes)
 c=collections.Counter(x for row in routes for x in row)
 return {'valid_rows':len(routes),'assignments':sum(c.values()),'experts_touched':len(c),'max_expert_rows':max(c.values()),'experts_with_multiple_m_blocks':sum(n>BM for n in c.values()),'extra_m_blocks_over_one_per_touched_expert':sum(math.ceil(n/BM)-1 for n in c.values())}
out={'scope':'Source-derived integer ordering witness and two constructed legal routing distributions; no native launch, latency, actual routing prevalence or GPU occupancy claim.','counter_guard_witness':{'M_blocks':M,'N_pairs_per_domain':N,'claimed_tasks':claimed,'guard_passes':True,'original_claims':original[:claimed],'naive_N_major_claims':naive[:claimed],'required_first_M_tasks_missing_after_reorder':missing,'interpretation':'The existing counter no longer proves every first-M L1 N task was issued. This does not execute or prove a runtime deadlock.'},'same_shape_multiplicity':{'physical_rows_per_rank':T_per_rank,'EP':EP,'E':E,'topk':K,'BLOCK_M':BM,'spread':counts(spread),'hot':counts(hot),'interpretation':'Identical row counts/config do not determine expert-block reuse. Both are synthetic admissible examples, not measured workload mixtures.'},'necessary_eligibility':'For expert e, b_e=ceil(n_e/BLOCK_M); multi-M reuse requires n_e>BLOCK_M. With unique per-token topk, n_e<=sum_r valid_rows_r.','known_workload_limit':'Prompt lengths, output caps, shared prefixes and request concurrency do not supply per-layer physical routed counts, graph padding/AV mapping or active tactic.'}
(B/'source_discriminators.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'prefix_guard_missing':len(missing),'spread':counts(spread),'hot':counts(hot)}))
