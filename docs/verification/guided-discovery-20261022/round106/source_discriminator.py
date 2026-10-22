"""Three bounded source/formula controls, never a native TMA test."""
from pathlib import Path
import struct,json
H=Path(__file__).parent
f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
def bf16(x):
 b=struct.unpack('I',struct.pack('f',f32(x)))[0]
 b=(b+0x7fff+((b>>16)&1))&0xffff0000
 return struct.unpack('f',struct.pack('I',b))[0]
def fold(xs,cast):
 v=0.0
 for x in xs:v=cast(v+x)
 return v
# Exact source heuristic for the scaled-FP8 activation case, H5120.
hidden=5120;pull=hidden
while pull>8192:assert pull%2==0;pull//=2
assert hidden//pull==1
# All partials are legal finite BF16 values. Scalar formulas illustrate the
# different intermediate rounding boundary; no actual cp.reduce instruction.
a=[256.0,1.0,-256.0]
assert all(bf16(x)==x for x in a)
base=bf16(fold(a,f32));bf16_each=fold(a,bf16)
assert base==1.0 and bf16_each==0.0
# FP32 keeps the width but unordered atomic arrivals need not keep native order.
b=[float(2**24),1.0,-float(2**24)]
assert all(bf16(x)==x for x in b)
ordered=bf16(fold(b,f32));other=bf16(fold([b[2],b[0],b[1]],f32))
assert ordered==0.0 and other==1.0
out={'scope':'One target source-heuristic substitution and two finite arithmetic contract witnesses; not GPU execution, actual target activations, TMA hardware behavior, quality frequency or timing.',
 'dispatch':{'hidden':hidden,'FP8_activation_bytes':hidden,'scaled_pull_limit':8192,'chosen_pull_bytes':pull,'chunks':hidden//pull,'conclusion':'No within-row multi-chunk pipeline at this source geometry.'},
 'bf16_partial_add_witness':{'partials':a,'FP32_fold_then_BF16':base,'BF16_round_after_each_add':bf16_each},
 'FP32_order_witness':{'native_shared_first_then_routes':b,'native_result':ordered,'reordered_result':other},
 'meaning':'These refute automatic arithmetic equivalence of the naive replacements. They do not establish occurring quality loss or rule out an admitted numerical-change design.'}
(H/'source_discriminator.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
