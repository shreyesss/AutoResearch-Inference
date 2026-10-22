"""Exact integer-address/byte controls; not hardware traffic or loader execution."""
from pathlib import Path
import json
b=Path(__file__).parent
D=256; S=8; R=D+S; N=512*1003

def units(start,length,size):return set(range(start//size,(start+length-1)//size+1))
records=[]
for i in range(512):
 v=i*D; s=N*D+i*S; p=i*R
 records.append({'row':i,'separate_sectors':len(units(v,D,32)|units(s,S,32)),'packed_sectors':len(units(p,R,32)),'separate_pages':len(units(v,D,4096)|units(s,S,4096)),'packed_pages':len(units(p,R,4096))})
assert {x['separate_sectors'] for x in records}=={9}
assert {x['packed_sectors'] for x in records}=={9}
# Byte identity includes every FP8 byte encoding and scale bytes; no floating interpretation.
values=[bytes((j+i)%256 for j in range(D)) for i in range(8)]
scales=[bytes((j*37+i)%256 for j in range(S)) for i in range(8)]
packed=b''.join(v+s for v,s in zip(values,scales))
for i in range(8):assert packed[i*R:i*R+D]==values[i] and packed[i*R+D:(i+1)*R]==scales[i]
# Current DIM-stride indexing is invalid after host repack; updating storage alone fails.
assert packed[D:D+D]!=values[1]
separate_batch_pages=set();packed_batch_pages=set()
for i in range(512):
 separate_batch_pages |= units(i*D,D,4096)|units(N*D+i*S,S,4096)
 packed_batch_pages |= units(i*R,R,4096)
assert len(separate_batch_pages)==len(packed_batch_pages)==33
out={'consecutive_512_row_unique_pages':{'separate':33,'packed':33},'scope':__doc__,'assumptions':'256 value bytes and 8 scale bytes; page-aligned allocation base, 32-byte sectors, 4KiB pages, separate planes, isolated row cold accesses. No claims about actual TLB page size, cache hits, PCIe requests or stalls.','rows_in_alignment_period':512,'sector_counts':{'separate':9,'packed264':9},'page_count_means':{k:sum(x[k] for x in records)/512 for k in ('separate_pages','packed_pages')},'exact_byte_controls':8,'old_stride_negative':True,'records':records}
(b/'layout_control.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='records'})
