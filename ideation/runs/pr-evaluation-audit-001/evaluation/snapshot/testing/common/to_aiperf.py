#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def convert(record: dict[str, Any]) -> dict[str, Any]:
    body = record.get("body") if isinstance(record.get("body"), dict) else record
    metadata = record.get("metadata", record.get("_metadata", {}))
    headers = record.get("headers", record.get("_headers", {}))
    messages = body.get("messages")
    if not isinstance(messages, list) or len(messages) != 1:
        raise ValueError("AIPerf single-turn adapter requires one message per record")
    content = messages[0].get("content")
    text_parts: list[str] = []
    images: list[str] = []
    if isinstance(content, str):
        text_parts.append(content)
    elif isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                text_parts.append(item["text"])
            elif item.get("type") == "image_url":
                image = item.get("image_url")
                if isinstance(image, dict) and isinstance(image.get("url"), str):
                    images.append(image["url"])
    if not text_parts and not images:
        raise ValueError("request contains no text or image modality")

    session_id = None
    if isinstance(headers, dict):
        session_id = headers.get("X-Session-ID")
    if not session_id and isinstance(metadata, dict):
        session_id = metadata.get("session_id")
    extra = {
        key: value
        for key, value in body.items()
        if key
        not in {
            "model",
            "messages",
            "stream",
            "stream_options",
            "max_tokens",
            "max_completion_tokens",
        }
    }
    converted: dict[str, Any] = {
        "text": "\n".join(text_parts),
        "output_length": int(
            body.get("max_tokens", body.get("max_completion_tokens", 128))
        ),
        "extra": extra,
    }
    if images:
        converted["images"] = images
    if session_id:
        converted["session_id"] = str(session_id)
    return converted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.input.open() as source, args.output.open("w") as destination:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                destination.write(json.dumps(convert(record), separators=(",", ":")) + "\n")
            except Exception as exc:
                raise SystemExit(f"{args.input}:{line_number}: {exc}") from exc
            count += 1
    if count == 0:
        raise SystemExit("input dataset is empty")
    print(f"Converted {count} records for AIPerf: {args.output}")


if __name__ == "__main__":
    main()
