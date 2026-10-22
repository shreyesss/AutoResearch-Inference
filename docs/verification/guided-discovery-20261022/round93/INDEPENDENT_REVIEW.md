# Independent round93 review

**Verdict: no blocker to retaining a conditional low-priority component, with zero new typed identities and no implementation/service qualification.** I read the frozen report, layout control, exact Engram allocation/lookup/loader paths, pinned CUDA-view implementation and CP AppendixG passages. Independently checked all33 frozen file hashes and all8 quotes against their retained exact revisions. I did not execute author/native code, import a backend/model, or perform network/GPU operations.

## Source applicability

The `_packed` shared/THP allocation is two logical planes, not264-byte interleaved rows. Native lookup hardcodes value row stride256 and scale row stride8. The proposed interleave therefore requires explicit physical row strides in the kernel; changing storage alone corrupts addressing. Both pointer arguments are byte-sized element types here, so stride264 has the intended unit, but that fact must not be generalized to other element types.

The current loader preserves raw UE8M0 bits through a uint8 view and copies into parameter shapes; no inspected loader expression requires destination contiguity. That is a source-level route to a strided destination, not proof every initialization/dummy/reload path supports it. Shared `get_views` guards original parameter data pointers and caches mapped views; retaining original owner, registration and view identity is essential. Its guard alone does not validate arbitrary altered strides. The pinned CUDA-view implementation explicitly preserves sizes/strides and captures the base tensor for pinned inputs. The unpinned branch calls `contiguous`, allocates another buffer and copies, so it cannot be silently counted as the same representation.

Sorted lookup uses `sorted_dst` for output ordering while source addresses use local row IDs. Interleaving must change source address generation only; it must not conflate sorted row order with destination order. The existing packed-output path already combines FP8 and scale output bytes, but that is downstream staging, distinct from this proposed host backing layout (EG01). Reuse/caching (EG02) is likewise different.

## Alignment and page claim

The author correctly reports unique address footprints, not actual transfer counts. My independent integer-address check agrees:264-byte rows cover nine unique32-byte sectors and average1.0625 distinct4KiB pages under the stated alignment assumptions. Separate planes need nine unique sectors and two per-row pages in this illustrative range. Batch union, scale-page reuse, huge pages and translation caching can erase the per-row page difference; the author's512-consecutive-row equality is an important counterexample.

An additional countervailing alignment detail: the256-byte value load crosses nine sectors for three of four interleaved rows instead of eight for aligned separate values. Counting the two load instruction address footprints separately gives an average9.75 sectors (value plus scale), although their union remains nine because the scale load overlaps the final value sector. **This is not9.75 hardware transactions, a bandwidth estimate or a measured regression.** Cache reuse and compiled load/coalescing behavior determine cost. It reinforces the report's caution and rules out inferring free co-location from the union count.

## Paper transfer

CP AppendixG compares compressed row records with trellis tile/window decoding, with different payload layouts and decode work. Its own notes distinguish calculated code traffic/sectors from measured bandwidth and deny a consistent HBM decode win. The proposed exact FP8+UE8M0 layout neither uses the codec nor inherits the measured ratio. The paper's compression is post-training and does not require neural retraining; selective exact layout reuse remains legitimate while codec arithmetic requires a separate quality contract. Mooncake gather is body-only and lacks the native GPU-produced-hash/CPU-owner integration required here.

## Decision usefulness and remaining gate

This packet prevents an attractive but unsupported transfer-byte story and preserves a distinct possible translation-locality mechanism. It does not establish that native host translations are exposed, that4KiB pages are active, or that the large allocation/loader change is worthwhile. Existing compatible allocation/access evidence or a future separately authorized native lookup attribution is the right reopening condition. No extra synthetic case count or new hypothesis identity is needed now. Exact output/scale bytes, masks, sorted order, reload and capture lifetimes must pass before a performance experiment.
