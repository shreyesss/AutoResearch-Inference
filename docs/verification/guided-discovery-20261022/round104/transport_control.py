"""Integer cell-tag transport only; no floating point/native/GPU execution."""
from pathlib import Path
import json
H=Path(__file__).parent
# Each parity class holds eight values: even rows0/1, odd rows2/3.
registers=[[8*(lane&1)+k for k in range(8)] for lane in range(32)]
send=[registers[lane][(lane>>1)&7] for lane in range(32)]
naive_send=[registers[lane][((lane-8)&7) if 8<=lane<24 else 0] for lane in range(32)]
rows=[]
for lane in range(8,24):
    idx=lane-8;src=2*(idx&7)+(idx>>3)
    rows.append(dict(destination_lane=lane,expected_cell=idx,source_lane=src,
                     sender_register=(src>>1)&7,received_cell=send[src],
                     naive_received_cell=naive_send[idx>>3]))
assert all(r['received_cell']==r['expected_cell'] for r in rows)
assert len({r['source_lane'] for r in rows})==16
assert sum(r['naive_received_cell']!=r['expected_cell'] for r in rows)==14
out={'scope':'Integer tag mapping of the stated parity-class register layout only. Not numerical parity, compiled instruction count, register allocation or performance.',
     'correct_destinations':16,'naive_wrong_destinations':14,'rows':rows,
     'all_32_lanes_participate':True,'non_comb_safe_source':0}
(H/'transport_control.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
