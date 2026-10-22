"""Stdlib source/conditional protocol check; no CUDA semantics are executed."""
from pathlib import Path
import json
b=Path(__file__).parent
old=(b/'sources/target-sm100_fp8_fp4_mega_moe.cuh').read_text()
new=(b/'sources/donor-sm100_fp8_fp4_mega_moe.cuh').read_text()
reset='ptx::st_rel_sys(workspace.get_combine_ready_grid_idx_ptr(thread_idx), uint64_t(0));'
barrier='kBeforeDispatchPullBarrierTag'
assert reset not in old
pull = new.index('// Barrier before pulling')
assert new.index(reset) < pull < new.index(barrier, pull)
assert 'ptx::ld_acq_sys(peer_ready_ptr) == grid_idx' in old
assert 'ptx::ld_acq_sys(peer_ready_ptr) == grid_idx' in new
# A reused nonzero tag is an explicit assumed input, not a hardware observation.
cases=[dict(name='Distinct launch tag',stored=8,current=9,admitted=False),dict(name='Reused tag without reset',stored=9,current=9,admitted=True),dict(name='Reset before current publication',stored=0,current=9,admitted=False),dict(name='Current publication after reset',stored=9,current=9,admitted=True)]
for c in cases:assert (c['stored']==c['current'])==c['admitted']
out={'source_checks':{'old_reset_absent':True,'donor_reset_before_pull_barrier':True,'both_wait_by_tag_equality':True},'conditional_cases':cases,'scope':'String-level source placement and scalar predicate only. Does not establish grid-ID reuse, device ordering, runtime race, patch correctness, or performance. Assumes nonzero gridid+1; wraparound not modeled.'}
(b/'source_contract_check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
