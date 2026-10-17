# Mooncake input qualification for Qwen B0

The three production YAMLs in `Deepseek_serve/testing/workloads/aiperf/` use the
same pinned Mooncake source. Their fixed schedules own the request rate; there is
no RPS calibration knob. Keep this input separate from the synthetic loads.

## Reproduce

```bash
.venv/bin/python infra/vendor/ops_aiperf/prepare_mooncake.py \
  --download --data-root .artifacts/ops-aiperf-inputs
.venv/bin/python infra/prepare_mooncake_qwen.py \
  --source-root .artifacts/ops-aiperf-inputs \
  --output-root .artifacts/ops-aiperf-inputs/qwen-filtered
for name in median burst cache-heavy; do
  .venv/bin/aiperf validate mooncake-trace \
    --input ".artifacts/ops-aiperf-inputs/qwen-filtered/mooncake/subsets/$name.jsonl"
done
```

Source revision: `d750cddafa4b62387ca135949595008c51e05815`;
source SHA256: `b434f1816a707f4bac697235588184ebc374c9907cb981bb65fb0643471fe711`.
The byte-identical vendored preparer SHA256 is
`8ab94ee6c38c144d3ede916b75e3e175fbfb1fe8c8892cbd08c78a298dbb07ac`;
campaign YAML SHA256 is
`dca02e47551290c32eeae0ec3d914def94e53eff4fc4164ec5398397f3e77cf6`.

| Window | Original requests / RPS | Original peak 1 s | Over Qwen context | Qwen-filtered requests / RPS | Filtered peak 1 s | Filtered SHA256 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Median | 4004 / 6.673 | 38 | 87 | 3915 / 6.525 | 38 | `30d070f0a0ab60bd9aaa8aa6135940a53b70ce5c8bc8336095608e6b1d67babc` |
| Burst | 4220 / 7.033 | 47 | 91 | 4128 / 6.880 | 46 | `8120050925686658901317429e222279279afad96a815266152772692b51d1df` |
| Cache-heavy | 4053 / 6.755 | 36 | 74 | 3979 / 6.632 | 36 | `7804500504d3f2dfc1e43d61271d18717b28f3f5b12dcf75a2196681fadee6b6` |

Raw traces include prompt-plus-output lengths as high as roughly 120–126K,
above Qwen's 40,960-token context. The derived cohort removes rows whose
recorded input plus output exceeds 40,704 tokens, reserving 256 tokens for
chat-template and tokenization differences. All remaining row bodies and
arrival timestamps are byte-for-byte unchanged. The full drop list, reasons,
source hashes, and resulting timing counts are in
`.artifacts/ops-aiperf-inputs/qwen-filtered/mooncake/qualification.json`.

The filtered cohorts are **derived Qwen inputs**, not the original Mooncake
windows. AIPerf `validate mooncake-trace` passes all three. That validates file
shape only; completed requests, actual token counts, replay lag, and Qwen B0
latency still require a live run. The three 10-minute schedules are around
6.5–6.9 RPS after filtering, so a failed SLA at B0 is a valid overload result,
not a reason to relabel the load.

When running the provided `ops_aiperf/runner.py`, set `--data-root` to
`.artifacts/ops-aiperf-inputs/qwen-filtered` and pass Qwen's pinned tokenizer
revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` explicitly. The
runner's default tokenizer revision belongs to DeepSeek.
