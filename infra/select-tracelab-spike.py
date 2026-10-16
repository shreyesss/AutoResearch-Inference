"""Select a small complete session from the pinned TraceLab release for M0."""

import argparse
import gzip
import itertools
import json
from pathlib import Path


def session_id(line: str) -> str:
    return json.loads(line)["session_id"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()

    selected_id = None
    selected_lines = None
    selected_index = None
    with gzip.open(args.source, "rt") as source:
        for index, (sid, grouped) in enumerate(
            itertools.groupby(source, key=session_id), start=1
        ):
            lines = list(grouped)
            if not 2 <= len(lines) <= 5:
                continue
            rows = [json.loads(line) for line in lines]
            peak = max(
                int(row.get("input_tokens_total") or 0)
                + int(row.get("output_tokens") or 0)
                for row in rows
            )
            if peak <= 6000:
                selected_id, selected_lines, selected_index = sid, lines, index
                break

    if selected_lines is None:
        raise SystemExit("No eligible session found")

    with gzip.open(args.source, "rt") as source:
        total = sum(session_id(line) == selected_id for line in source)
    if total != len(selected_lines):
        raise SystemExit("Selected session is split across the source file")

    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_text("".join(selected_lines))
    print(
        json.dumps(
            {
                "source_group_index": selected_index,
                "session_id": selected_id,
                "rows": total,
                "target": str(args.target),
            }
        )
    )


if __name__ == "__main__":
    main()
