# Baseline k5 timing: root-only launch handoff

Run the renderer with the existing launcher interpreter:

```bash
/home/ubuntu/Deepseek_serve/.venv/bin/python /home/ubuntu/Deepseek_serve-c03/av-k5/render_launch.py
```

It performs no container or service operation. It verifies that `c03/rendered-rollback-backends.txt` contains the exact same two Docker argv arrays as the original baseline command receipt, validates the evaluator observation manifest and both original/source hashes, and requires the observation files to be read-only. It emits `rendered-backends.json` and `rendered-backends.txt` only after all guards pass. Re-run immediately before root launches so changed observation source cannot silently pass an old receipt.

Root launches the two structured `commands[].argv` arrays using its established sudo/environment handling after independent node/port checks. The original Docker names, GPU groups, ports, RPC ports, immutable image, model revision, storage/cache mounts and complete engine argv remain unchanged. No router command is included; root preserves/restores its previously attested router independently. Neither original `.venv` is changed.

The only diagnostic additions are:

1. Two read-only file mounts from the evaluator-owned observation manifest: original `gpu/model_runner.py` plus original `gpu/spec_decode/dflash/speculator.py` with three approved profiler labels. No C03 optimization source or diagnostic helper is used.
2. `PYTHONPYCACHEPREFIX=/tmp/av-k5-pycache`. Each new container starts with a fresh cache at this path.
3. One `--profiler-config` JSON argument. Each replica has its own `/profiles/av-k5-timing-001/replica0` or `replica1` directory. Activities CPU/CUDA, stack/shapes/memory/FLOPs disabled, frontend ignored, startup-capture profiler disabled, warmup1/active20/wait0/max20 as chosen by the evaluator designer. DSpark remains k5, probabilistic/block, adaptive OFF.

The existing `/profiles` storage mount is reused. Do not invoke the old shell profiling wrapper's JSON-body controls: the pinned server ignores them. The evaluator controller must call both backend ports' `/start_profile` and `/stop_profile`; these endpoints return empty HTTP200. The approved episode schedule, workload truncation, trace parsing, start/stop behavior and acceptance checks are owned by the evaluator team, not this launcher. Root should verify all8 worker traces and source/image identity; do not start a second CUPTI profiler.

`avk5.draft_execution` is the whole captured draft execution composite, including context preparation/model/sampling when FULL graphs run. It must not be relabeled pure draft-model time. Host scope duration is not GPU duration. This launch is timing qualification, not a performance score or an AV-ON trial.

Rollback is the exact two commands in `c03/rendered-rollback-backends.txt`, after root stops only the experiment backends and preserves the router. No package rollback is necessary. Root owns all launches, stops, clients and artifact collection.

Validation receipts: the renderer restores each generated argv by deleting precisely the two file mounts, fresh-cache environment and appended profiler-config and asserts byte-for-byte list equality with its original baseline. Both replicas' source mounts are identical, with output directories the only profiler difference. Source semantics are independently reviewed by the evaluator designer/builder via `observation-manifest.json`; the optimization developer does not change or adjudicate those fixtures.

Final offline validation passed with the original Python3.10 launcher interpreter after the evaluator froze both files0444. Renderer syntax and shell round-trip also pass. `rendered-backends.json` SHA256 is `e75711be87a18fb707c5f1fa03e1c9c322d36c0a636983051117b8f3fa64df0d`; observation-manifest SHA256 is `f40811bc88c6a181b68bd0458bbeb36277d82bf198b0e4ce3cd5fdb596597d8d`. The `/profiles` mount resolves to `/home/jl_fs/profiler-cache` on this node. No runtime validation or launch was performed by the launcher developer.
