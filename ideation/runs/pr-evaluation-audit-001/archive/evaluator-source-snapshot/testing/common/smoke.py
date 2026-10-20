#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import io
import json
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw


def image_data_url() -> str:
    image = Image.new("RGB", (512, 512), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((96, 96, 416, 416), fill="blue")
    draw.text((180, 230), "V4.1", fill="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode()


def request(
    client: httpx.Client,
    base_url: str,
    model: str,
    messages: list[dict[str, Any]],
    **extra: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 256,
        "stream": False,
    }
    body.update(extra)
    response = client.post(f"{base_url.rstrip('/')}/chat/completions", json=body)
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", default="deepseek-v4.1-flash")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--long-tokens", type=int, default=8192)
    parser.add_argument("--skip-image", action="store_true")
    args = parser.parse_args()

    results: dict[str, Any] = {}
    with httpx.Client(timeout=1800) as client:
        models = client.get(f"{args.base_url.rstrip('/')}/models")
        models.raise_for_status()
        results["models"] = models.json()

        arithmetic = request(
            client,
            args.base_url,
            args.model,
            [{"role": "user", "content": "What is 17 * 19? Return only the integer."}],
            chat_template_kwargs={"thinking": False},
            max_tokens=32,
        )
        arithmetic_text = arithmetic["choices"][0]["message"].get("content", "").strip()
        if arithmetic_text != "323":
            raise SystemExit(f"arithmetic smoke failed: {arithmetic_text!r}")
        results["text"] = arithmetic

        results["reasoning"] = request(
            client,
            args.base_url,
            args.model,
            [{"role": "user", "content": "Prove that the sum of two even integers is even."}],
            reasoning_effort="high",
            chat_template_kwargs={"thinking": True, "reasoning_effort": 75},
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "lookup_weather",
                    "description": "Look up weather for a city.",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                    },
                },
            }
        ]
        results["tool"] = request(
            client,
            args.base_url,
            args.model,
            [{"role": "user", "content": "Use the tool to get weather in Bengaluru."}],
            tools=tools,
            tool_choice="auto",
            chat_template_kwargs={"thinking": False},
        )

        repeated = "capacity latency throughput scheduling correctness " * max(
            1, args.long_tokens // 6
        )
        results["long_context"] = request(
            client,
            args.base_url,
            args.model,
            [{"role": "user", "content": repeated + "\nReturn the first word only."}],
            chat_template_kwargs={"thinking": False},
            max_tokens=16,
        )

        prefix = "shared-prefix " * 4096
        for index in range(2):
            results[f"prefix_{index + 1}"] = request(
                client,
                args.base_url,
                args.model,
                [
                    {
                        "role": "user",
                        "content": f"{prefix}\nRequest {index}: return only OK.",
                    }
                ],
                chat_template_kwargs={"thinking": False},
                max_tokens=16,
            )

        if not args.skip_image:
            content = [
                {"type": "text", "text": "What color is the large square?"},
                {"type": "image_url", "image_url": {"url": image_data_url()}},
            ]
            results["image"] = request(
                client,
                args.base_url,
                args.model,
                [{"role": "user", "content": content}],
                chat_template_kwargs={"thinking": False},
                max_tokens=32,
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Smoke results: {args.output}")


if __name__ == "__main__":
    main()
