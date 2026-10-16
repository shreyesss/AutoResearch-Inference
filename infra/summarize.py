"""Print the small first-baseline AIPerf summary without asserting SLA validity."""

import json
import sys
from pathlib import Path


KEYS = (
    "request_count",
    "error_request_count",
    "request_error_rate",
    "input_sequence_length",
    "output_sequence_length",
    "usage_prompt_tokens",
    "usage_completion_tokens",
    "time_to_first_token",
    "inter_token_latency",
    "request_latency",
    "output_token_throughput",
    "request_throughput",
    "benchmark_duration",
    "replay_schedule_lag_p50",
    "replay_schedule_lag_p99",
)


def main(root: Path) -> int:
    summary = root / "profile_export_aiperf.json"
    paths = [summary] if summary.exists() else sorted(root.rglob("profile_export_aiperf.json"))
    if not paths:
        print(f"No AIPerf summary found under {root}", file=sys.stderr)
        return 1
    for path in paths:
        data = json.loads(path.read_text())
        print(f"\n{path}")
        print(f"AIPerf {data.get('aiperf_version')} / schema {data.get('schema_version')}")
        print(f"Cancelled: {data.get('was_cancelled')}; errors: {data.get('error_summary')}")
        for key in KEYS:
            value = data.get(key)
            if isinstance(value, dict):
                fields = ("avg", "p50", "p99", "count", "unit")
                shown = ", ".join(f"{field}={value[field]}" for field in fields if field in value)
                print(f"{key}: {shown}")
        raw = path.parent / "profile_export.jsonl"
        if raw.exists():
            print(f"exported record lines: {sum(1 for _ in raw.open())}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python summarize.py <aiperf artifact root>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
