# Independent review — round90 host output transport

**No blocker to zero-new closure and the conditional nonstreaming component.** The two donor transformations do not establish missing work on the inspected target streaming route. The frozen author report remains unchanged; no runtime or measurement claim is added.

## Exact source applicability

The target output socket path reclaims only completed tracker buffers, serializes via `encoder.encode_into`, sends the first frame with `copy=False, track=True`, and sends the remaining frames with `copy=False` (core2021–2041,2071–2086). The asynchronous frontend receives multipart frames with `copy=False` (core_client1211) and passes the frame sequence to the decoder; the decoder uses its first frame directly while retaining auxiliary frames for decoding (serial_utils344–350). That is the particular copy/bytes-materialization transformation in SGLang45097. It is already present on this inspected path. Small-message library behavior, serialization allocations, GIL contention and physical zero-copy coverage remain unmeasured; source flags are not a claim that these costs vanish.

The donor42889 helper returns non-BaseModel objects unchanged. Its selective improvement targets nonstreaming Pydantic responses, not streaming SSE. Native target streaming serializes each model directly with `model_dump_json`, using actual `exclude_unset`/`exclude_none` behavior, and wraps the generator with `StreamingResponse`. The saved Bitlane runner selects chat streaming. This is route evidence, not live launch attestation or proof that all frontend traffic streams.

A real remaining target operation is nonstreaming `JSONResponse(content=generator.model_dump(), headers=...)`. A future selective port can remove that Python intermediate. **Its control must be this existing explicit JSONResponse path**, not the donor's old FastAPI auto-encoding path: their avoided traversals differ. Preserve native field/alias/default/None semantics, errors/status and metrics headers, custom serializers and nonfinite handling. A mixed workload could expose this work indirectly, but no compatible shape/frequency/CPU evidence is retained here. Parking without creating a new card is appropriate; the mechanism remains searchable and reopenable.

## Paper and measurement interpretation

The selected ExaServe section explicitly reports healthy server latency,195k converged SSE streams and increased retransmissions while HAProxy stays under2%CPU. It attributes the measured collapse to concentrated network I/O rather than saturated proxy CPU/queues/ports. The report correctly avoids turning this into evidence that a local MessagePack copy is our bottleneck. Distributed ingress is a selectively usable component in the demonstrated deployment regime, not disproved by its poor fit to the currently retained target topology. Neither the optional saved gateway URL nor one-node planned EP topology establishes actual proxy load.

`stream_interval` changes ready-token delivery cadence. Any later comparison must preserve/report the existing client metric and gap semantics rather than assume buffered output is a free optimization. No paper or donor throughput ratio transfers to our source-only evaluation.

## Coverage and evidence audit

Verified59 author hashes and all8 exact quotes against their original retained revision fingerprints. Checked target source copies against the c455 archive. The two paper-query receipts have12+10 hits and22 unique retained IDs;22 abstract dispositions cover them. PR title scouts40+44 produce81 unique IDs covered by the disposition table. Updated-date filtering/caps are not creation-date/exhaustive upstream coverage, and title screening is not full diff review. Only the two selected donor patch sets and the selected paper sections support the detailed conclusions.

No broad test or synthetic timing would resolve the missing service exposure. The smallest future useful check is observed nonstreaming response shapes and exact CPU serialization equivalence against the correct target control, followed by a mixed-service comparison only if that traffic exists. For streaming delays, separate engine readiness, IPC/serialization and client-network delivery; a network bottleneck does not establish serializer headroom. No GPU, source mutation, test rerun, network request or canonical write was performed in this independent review.
