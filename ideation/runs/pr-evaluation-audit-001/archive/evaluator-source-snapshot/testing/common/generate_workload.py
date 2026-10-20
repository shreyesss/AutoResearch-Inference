#!/usr/bin/env python3
"""Generate deterministic OpenAI chat-completion request JSONL workloads."""

from __future__ import annotations

import argparse
import base64
import binascii
import copy
import hashlib
import json
import math
import os
import random
import struct
import sys
import zlib
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, cast


class WorkloadError(RuntimeError):
    """Raised for invalid workload input or generation failures."""


class TokenizerLike(Protocol):
    def encode(self, text: str, *, add_special_tokens: bool = ...) -> list[int]: ...

    def decode(
        self,
        token_ids: Sequence[int],
        *,
        skip_special_tokens: bool = ...,
        clean_up_tokenization_spaces: bool = ...,
    ) -> str: ...

    def apply_chat_template(
        self,
        conversation: Sequence[Mapping[str, Any]],
        **kwargs: Any,
    ) -> Any: ...


@lru_cache(maxsize=4)
def load_tokenizer(
    model: str,
    revision: str,
    cache_dir: str | None,
    trust_remote_code: bool,
) -> TokenizerLike:
    """Load once per process; Hugging Face also supplies the on-disk cache."""

    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise WorkloadError(
            "transformers is required; install requirements-tools.txt"
        ) from exc

    kwargs: dict[str, Any] = {
        "revision": revision,
        "trust_remote_code": trust_remote_code,
    }
    if cache_dir:
        kwargs["cache_dir"] = cache_dir
    token = os.environ.get("HF_TOKEN")
    if token:
        kwargs["token"] = token
    try:
        return cast(TokenizerLike, AutoTokenizer.from_pretrained(model, **kwargs))
    except Exception as exc:
        raise WorkloadError(
            f"could not load tokenizer {model!r} at pinned revision "
            f"{revision!r}: {exc}"
        ) from exc


def tokenizer_from_environment() -> tuple[TokenizerLike, str, str]:
    model = (
        os.environ.get("HF_TOKENIZER")
        or os.environ.get("TOKENIZER_MODEL")
        or os.environ.get("MODEL")
    )
    revision = (
        os.environ.get("HF_TOKENIZER_REVISION")
        or os.environ.get("TOKENIZER_REVISION")
        or os.environ.get("MODEL_REVISION")
    )
    if not model:
        raise WorkloadError(
            "set HF_TOKENIZER, TOKENIZER_MODEL, or MODEL to the tokenizer ID"
        )
    if not revision:
        raise WorkloadError(
            "set HF_TOKENIZER_REVISION, TOKENIZER_REVISION, or MODEL_REVISION "
            "to a pinned tokenizer revision"
        )
    if revision.strip().lower() in {"main", "master", "latest", "head"}:
        raise WorkloadError(
            f"tokenizer revision {revision!r} is moving; use a commit or immutable tag"
        )
    cache_dir = os.environ.get("HF_HOME") or os.environ.get("TRANSFORMERS_CACHE")
    trust_remote_code = os.environ.get("TOKENIZER_TRUST_REMOTE_CODE", "0") == "1"
    return (
        load_tokenizer(model, revision, cache_dir, trust_remote_code),
        model,
        revision,
    )


def load_yaml(path: Path) -> dict[str, Any]:
    """Read JSON-compatible YAML without adding a mandatory PyYAML dependency."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkloadError(f"cannot read workload config {path}: {exc}") from exc

    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise WorkloadError(
                f"{path} is not JSON-compatible YAML and PyYAML is not installed"
            ) from exc
        try:
            value = yaml.safe_load(text)
        except Exception as exc:
            raise WorkloadError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkloadError(f"{path} must contain a YAML mapping")
    return cast(dict[str, Any], value)


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = deep_merge(
                cast(Mapping[str, Any], merged[key]),
                cast(Mapping[str, Any], value),
            )
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def require_int(
    value: Any,
    field: str,
    *,
    minimum: int = 0,
    allow_zero: bool = True,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WorkloadError(f"{field} must be an integer")
    lower = minimum if allow_zero else max(1, minimum)
    if value < lower:
        raise WorkloadError(f"{field} must be at least {lower}")
    return value


def require_number(
    value: Any,
    field: str,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise WorkloadError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise WorkloadError(f"{field} must be finite and at least {minimum}")
    if maximum is not None and result > maximum:
        raise WorkloadError(f"{field} must be at most {maximum}")
    return result


def slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part) or "case"


def stable_fraction(seed: int, namespace: str, index: int) -> float:
    digest = hashlib.blake2b(
        f"{seed}:{namespace}:{index}".encode(), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big") / float(1 << 64)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = binascii.crc32(kind)
    checksum = binascii.crc32(payload, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


@lru_cache(maxsize=64)
def simple_png_data_url(width: int, height: int, variant: int) -> str:
    """Create a highly compressible RGB PNG without Pillow or a large raw buffer."""

    if width < 1 or height < 1 or width * height > 16_777_216:
        raise WorkloadError(
            f"image dimensions {width}x{height} exceed the 16-megapixel safety limit"
        )
    palette = (
        (35, 99, 170),
        (185, 65, 75),
        (45, 135, 85),
        (155, 105, 35),
        (105, 75, 165),
        (35, 145, 155),
        (170, 85, 135),
        (95, 105, 115),
    )
    color = palette[variant % len(palette)]
    accent = tuple(min(255, component + 45) for component in color)
    compressor = zlib.compressobj(level=9)
    compressed_parts: list[bytes] = []
    for row_index in range(height):
        row_color = accent if (row_index // max(1, height // 8)) % 2 else color
        scanline = b"\x00" + bytes(row_color) * width
        part = compressor.compress(scanline)
        if part:
            compressed_parts.append(part)
    compressed_parts.append(compressor.flush())
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", b"".join(compressed_parts))
        + png_chunk(b"IEND", b"")
    )
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def parse_resolution(value: Any) -> tuple[int, int]:
    if isinstance(value, int) and not isinstance(value, bool):
        width = height = value
    elif isinstance(value, str) and "x" in value.lower():
        left, right = value.lower().split("x", 1)
        try:
            width, height = int(left), int(right)
        except ValueError as exc:
            raise WorkloadError(f"invalid image resolution {value!r}") from exc
    else:
        raise WorkloadError("image_resolution must be an integer or WIDTHxHEIGHT")
    if width < 1 or height < 1 or width > 8192 or height > 8192:
        raise WorkloadError("image dimensions must be between 1 and 8192 pixels")
    if width * height > 16_777_216:
        raise WorkloadError("image resolution exceeds the 16-megapixel safety limit")
    return width, height


def content_as_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, Mapping) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


class Generator:
    def __init__(
        self,
        *,
        tokenizer: TokenizerLike,
        tokenizer_model: str,
        tokenizer_revision: str,
        config: Mapping[str, Any],
        config_path: Path,
        case_name: str,
        requests: int,
        seed: int,
    ) -> None:
        schema_version = config.get("schema_version")
        if schema_version != 1:
            raise WorkloadError(
                f"{config_path}: schema_version must be 1, got {schema_version!r}"
            )
        cases = config.get("cases")
        if not isinstance(cases, list) or not cases:
            raise WorkloadError(f"{config_path}: cases must be a non-empty list")
        matches = [
            item
            for item in cases
            if isinstance(item, Mapping)
            and (item.get("name") == case_name or item.get("id") == case_name)
        ]
        if len(matches) != 1:
            available = ", ".join(
                str(item.get("name") or item.get("id"))
                for item in cases
                if isinstance(item, Mapping)
            )
            raise WorkloadError(
                f"case {case_name!r} was not found exactly once; available: {available}"
            )
        defaults = config.get("defaults", {})
        if not isinstance(defaults, Mapping):
            raise WorkloadError("defaults must be a mapping")

        self.tokenizer = tokenizer
        self.tokenizer_model = tokenizer_model
        self.tokenizer_revision = tokenizer_revision
        self.config_name = str(config.get("name") or config_path.stem)
        self.case_name = case_name
        self.requests = requests
        self.seed = seed
        self.base_case = deep_merge(
            cast(Mapping[str, Any], defaults),
            {
                key: value
                for key, value in cast(Mapping[str, Any], matches[0]).items()
                if key != "variants"
            },
        )
        variants = cast(Mapping[str, Any], matches[0]).get("variants")
        self.variants = self._validate_variants(variants)
        self.variant_schedule = self._variant_schedule()
        self.prefix_cache: dict[tuple[str, int], str] = {}
        self.percentage_schedules: dict[
            tuple[str, float, int], tuple[int, int, int]
        ] = {}

    def _validate_variants(self, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        if not isinstance(value, list) or not value:
            raise WorkloadError("variants must be a non-empty list")
        result: list[dict[str, Any]] = []
        names: set[str] = set()
        for position, raw in enumerate(value):
            if not isinstance(raw, Mapping):
                raise WorkloadError(f"variant {position} must be a mapping")
            item = dict(raw)
            name = item.get("name")
            if not isinstance(name, str) or not name:
                raise WorkloadError(f"variant {position} needs a non-empty name")
            if name in names:
                raise WorkloadError(f"duplicate variant name {name!r}")
            names.add(name)
            require_number(item.get("weight"), f"variant {name}.weight", minimum=0.0)
            result.append(item)
        if sum(float(item["weight"]) for item in result) <= 0:
            raise WorkloadError("variant weights must have a positive sum")
        return result

    def _variant_schedule(self) -> list[int]:
        if not self.variants:
            return []
        weights = [float(item["weight"]) for item in self.variants]
        total = sum(weights)
        exact = [self.requests * weight / total for weight in weights]
        counts = [math.floor(value) for value in exact]
        remaining = self.requests - sum(counts)
        order = sorted(
            range(len(weights)),
            key=lambda index: (exact[index] - counts[index], weights[index]),
            reverse=True,
        )
        for index in order[:remaining]:
            counts[index] += 1
        schedule = [
            variant_index
            for variant_index, count in enumerate(counts)
            for _ in range(count)
        ]
        random.Random(self.seed).shuffle(schedule)
        return schedule

    def resolved_case(self, index: int) -> tuple[dict[str, Any], str | None]:
        if not self.variants:
            return copy.deepcopy(self.base_case), None
        variant = self.variants[self.variant_schedule[index]]
        merged = deep_merge(
            self.base_case,
            {key: value for key, value in variant.items() if key != "weight"},
        )
        return merged, str(variant["name"])

    def _percentage_hit(
        self,
        *,
        namespace: str,
        index: int,
        percentage: float,
        population: int | None = None,
    ) -> bool:
        """Select the exact rounded share through a deterministic permutation."""

        population = population or self.requests
        if population <= 0 or index < 0 or index >= population:
            raise WorkloadError("internal error: invalid percentage schedule index")
        key = (namespace, percentage, population)
        if key not in self.percentage_schedules:
            selected = math.floor(population * percentage / 100.0 + 0.5)
            if population == 1:
                multiplier = 1
                offset = 0
            else:
                digest = hashlib.blake2b(
                    f"{self.seed}:{namespace}".encode(), digest_size=16
                ).digest()
                multiplier = int.from_bytes(digest[:8], "big") % population
                multiplier = max(1, multiplier)
                while math.gcd(multiplier, population) != 1:
                    multiplier = (multiplier + 1) % population
                    if multiplier == 0:
                        multiplier = 1
                offset = int.from_bytes(digest[8:], "big") % population
            self.percentage_schedules[key] = (selected, multiplier, offset)
        selected, multiplier, offset = self.percentage_schedules[key]
        rank = (multiplier * index + offset) % population
        return rank < selected

    def _count_messages(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        thinking: bool,
        tools: Sequence[Mapping[str, Any]] | None = None,
    ) -> int:
        text_messages = [
            {"role": str(message["role"]), "content": content_as_text(message["content"])}
            for message in messages
        ]
        try:
            template_kwargs: dict[str, Any] = {
                "tokenize": True,
                "add_generation_prompt": True,
                "thinking": thinking,
            }
            if tools:
                template_kwargs["tools"] = tools
            tokenized = self.tokenizer.apply_chat_template(
                text_messages,
                **template_kwargs,
            )
            if isinstance(tokenized, Mapping):
                tokenized = tokenized.get("input_ids")
            if isinstance(tokenized, Sequence):
                if tokenized and isinstance(tokenized[0], Sequence):
                    return len(cast(Sequence[Any], tokenized[0]))
                return len(tokenized)
        except (AttributeError, TypeError, ValueError):
            pass

        fallback = "".join(
            f"<|{message['role']}|>\n{content_as_text(message['content'])}\n"
            for message in text_messages
        )
        if tools:
            fallback += json.dumps(tools, sort_keys=True, separators=(",", ":"))
        fallback += "<|assistant|>\n"
        return len(self.tokenizer.encode(fallback, add_special_tokens=True))

    def _token_text(self, count: int, namespace: str) -> str:
        if count <= 0:
            return ""
        marker = hashlib.blake2s(namespace.encode(), digest_size=6).hexdigest()
        seed_text = (
            f"Evidence block {marker}. Measure request scheduling, cache behavior, "
            "latency, throughput, correctness, and operational tradeoffs. "
            "Retain all relevant details and distinguish observations from assumptions.\n"
        )
        seed_ids = self.tokenizer.encode(seed_text, add_special_tokens=False)
        if not seed_ids:
            raise WorkloadError("the tokenizer produced no tokens for generator text")
        repeats = (count + len(seed_ids) - 1) // len(seed_ids)
        ids = (seed_ids * repeats)[:count]
        return self.tokenizer.decode(
            ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )

    def _plain_text_with_tokens(self, target: int, namespace: str) -> str:
        text = self._token_text(target, namespace)
        for attempt in range(6):
            ids = self.tokenizer.encode(text, add_special_tokens=False)
            delta = target - len(ids)
            if delta == 0:
                return text
            if delta > 0:
                text += self._token_text(delta + 1, f"{namespace}:add:{attempt}")
            else:
                keep = max(1, len(ids) + delta)
                text = self.tokenizer.decode(
                    ids[:keep],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )
        return text

    def _prefix_key(
        self,
        *,
        mode: str,
        reuse_percent: float,
        index: int,
        session_index: int,
        session_count: int,
        pool_size: int,
    ) -> str:
        if mode in {"cold", "unique"}:
            return f"unique-{index}"
        schedule_index = session_index if mode == "multiturn" else index
        population = session_count if mode == "multiturn" else self.requests
        reusable = self._percentage_hit(
            namespace=f"{self.case_name}:{mode}:reuse",
            index=schedule_index,
            percentage=reuse_percent,
            population=population,
        )
        if not reusable:
            return f"unique-{index}"
        if mode == "hot":
            return "hot-0"
        if mode == "multiturn":
            return f"session-{session_index}"
        if mode == "zipf":
            exponent = 1.2
            weights = [1.0 / ((rank + 1) ** exponent) for rank in range(pool_size)]
            threshold = stable_fraction(
                self.seed, f"{self.case_name}:zipf", index
            ) * sum(weights)
            cumulative = 0.0
            for rank, weight in enumerate(weights):
                cumulative += weight
                if threshold <= cumulative:
                    return f"zipf-{rank}"
            return f"zipf-{pool_size - 1}"
        if mode in {"none", ""}:
            return f"request-{index}"
        raise WorkloadError(f"unsupported prefix_mode {mode!r}")

    def _make_prefix(self, key: str, tokens: int) -> str:
        if not key.startswith(("hot-", "zipf-")):
            return self._plain_text_with_tokens(
                tokens, f"prefix:{self.case_name}:{key}"
            )
        cache_key = (key, tokens)
        if cache_key not in self.prefix_cache:
            self.prefix_cache[cache_key] = self._plain_text_with_tokens(
                tokens, f"prefix:{self.case_name}:{key}"
            )
        return self.prefix_cache[cache_key]

    def _instruction(self, category: str, index: int) -> str:
        nonce = hashlib.blake2s(
            f"{self.seed}:{self.case_name}:{index}".encode(), digest_size=5
        ).hexdigest()
        prompts = {
            "chat": "Answer the user's question clearly and concisely.",
            "agentic": (
                "Plan the task, call an available tool only when useful, and report "
                "a verifiable result."
            ),
            "long-doc": (
                "Synthesize the supplied evidence, preserve qualifications, and cite "
                "the relevant evidence-block identifiers."
            ),
            "code-reasoning": (
                "Analyze the algorithm, identify edge cases, and propose a correct "
                "Python implementation with its complexity."
            ),
            "multimodal": (
                "Describe the visual structure and relate it to the accompanying text."
            ),
        }
        return f"Request {nonce}. {prompts.get(category, prompts['chat'])}\n"

    def _fit_messages(
        self,
        scaffold: list[dict[str, Any]],
        *,
        target_isl: int,
        thinking: bool,
        namespace: str,
        tools: Sequence[Mapping[str, Any]] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        if not scaffold or scaffold[-1].get("role") != "user":
            raise WorkloadError("internal error: final scaffold message must be user")
        base = self._count_messages(scaffold, thinking=thinking, tools=tools)
        if base > target_isl:
            raise WorkloadError(
                f"target ISL {target_isl} is smaller than prompt/template overhead {base}"
            )
        filler = self._token_text(target_isl - base, f"{namespace}:initial")
        scaffold[-1]["content"] = str(scaffold[-1]["content"]) + filler

        tolerance = max(3, int(target_isl * 0.00002))
        actual = self._count_messages(scaffold, thinking=thinking, tools=tools)
        for attempt in range(8):
            delta = target_isl - actual
            if abs(delta) <= tolerance:
                return scaffold, actual
            content = str(scaffold[-1]["content"])
            if delta > 0:
                content += self._token_text(
                    delta + 1, f"{namespace}:adjust:{attempt}"
                )
            else:
                ids = self.tokenizer.encode(content, add_special_tokens=False)
                keep = max(1, len(ids) + delta)
                content = self.tokenizer.decode(
                    ids[:keep],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )
            scaffold[-1]["content"] = content
            actual = self._count_messages(scaffold, thinking=thinking, tools=tools)

        relaxed = max(16, int(target_isl * 0.001))
        if abs(actual - target_isl) > relaxed:
            raise WorkloadError(
                f"could not fit target ISL {target_isl}; tokenizer produced {actual}"
            )
        return scaffold, actual

    def _tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "lookup_metric",
                    "description": "Look up one benchmark metric by name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "window": {"type": "string"},
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

    def make_request(self, index: int) -> dict[str, Any]:
        case, variant_name = self.resolved_case(index)
        target_isl = require_int(
            case.get("isl", case.get("target_isl")),
            "isl",
            minimum=1,
            allow_zero=False,
        )
        max_tokens = require_int(
            case.get("max_tokens", case.get("osl")),
            "max_tokens",
            minimum=1,
            allow_zero=False,
        )
        ignore_eos = case.get("ignore_eos", False)
        if not isinstance(ignore_eos, bool):
            raise WorkloadError("ignore_eos must be boolean")
        raw_min_tokens = case.get("min_tokens")
        min_tokens = (
            None
            if raw_min_tokens is None
            else require_int(
                raw_min_tokens,
                "min_tokens",
                minimum=1,
                allow_zero=False,
            )
        )
        if min_tokens is not None and min_tokens > max_tokens:
            raise WorkloadError("min_tokens cannot exceed max_tokens")
        thinking = case.get("thinking", False)
        if not isinstance(thinking, bool):
            raise WorkloadError("thinking must be boolean")
        reasoning_effort = case.get("reasoning_effort", "low")
        if not isinstance(reasoning_effort, str) or not reasoning_effort:
            raise WorkloadError("reasoning_effort must be a non-empty string")
        category = case.get("category", "chat")
        if not isinstance(category, str) or not category:
            raise WorkloadError("category must be a non-empty string")
        temperature = require_number(case.get("temperature", 0), "temperature")
        tools_enabled = case.get("tools", False)
        if not isinstance(tools_enabled, bool):
            raise WorkloadError("tools must be boolean")

        prefix_tokens = require_int(case.get("prefix_tokens", 0), "prefix_tokens")
        prefix_mode = str(case.get("prefix_mode", "none")).lower()
        reuse_percent = require_number(
            case.get("reuse_percent", 0),
            "reuse_percent",
            minimum=0,
            maximum=100,
        )
        pool_size = require_int(
            case.get("prefix_pool_size", 16),
            "prefix_pool_size",
            minimum=1,
            allow_zero=False,
        )
        turns_per_session = require_int(
            case.get("turns_per_session", 4),
            "turns_per_session",
            minimum=1,
            allow_zero=False,
        )
        session_index = index // turns_per_session if prefix_mode == "multiturn" else index
        session_count = (
            math.ceil(self.requests / turns_per_session)
            if prefix_mode == "multiturn"
            else self.requests
        )
        turn_index = index % turns_per_session if prefix_mode == "multiturn" else 0
        prefix_key = self._prefix_key(
            mode=prefix_mode,
            reuse_percent=reuse_percent,
            index=index,
            session_index=session_index,
            session_count=session_count,
            pool_size=pool_size,
        )
        session_id = (
            f"wl-{slug(self.case_name)}-s{session_index:06d}"
            if prefix_mode == "multiturn"
            else f"wl-{slug(self.case_name)}-r{index:08d}"
        )

        messages: list[dict[str, Any]] = []
        actual_prefix_tokens = 0
        if prefix_tokens:
            prefix = self._make_prefix(prefix_key, prefix_tokens)
            actual_prefix_tokens = len(
                self.tokenizer.encode(prefix, add_special_tokens=False)
            )
            messages.append({"role": "system", "content": prefix})
        if prefix_mode == "multiturn":
            for prior_turn in range(turn_index):
                messages.extend(
                    [
                        {
                            "role": "user",
                            "content": f"Continue session task, turn {prior_turn + 1}.",
                        },
                        {
                            "role": "assistant",
                            "content": (
                                f"Recorded intermediate result for turn "
                                f"{prior_turn + 1}."
                            ),
                        },
                    ]
                )
        messages.append(
            {"role": "user", "content": self._instruction(category, index)}
        )
        tools = self._tools() if tools_enabled else None
        messages, actual_isl = self._fit_messages(
            messages,
            target_isl=target_isl,
            thinking=thinking,
            namespace=f"{self.case_name}:{variant_name}:{index}",
            tools=tools,
        )

        image_share = require_number(
            case.get("image_share", 0),
            "image_share",
            minimum=0,
            maximum=100,
        )
        include_images = self._percentage_hit(
            namespace=f"{self.case_name}:{variant_name}:images",
            index=index,
            percentage=image_share,
        )
        image_count = require_int(case.get("image_count", 1), "image_count")
        image_detail = case.get("image_detail", "auto")
        if not isinstance(image_detail, str) or not image_detail:
            raise WorkloadError("image_detail must be a non-empty string")
        width = height = 0
        if include_images:
            if image_count < 1:
                raise WorkloadError("image_count must be positive when images are used")
            width, height = parse_resolution(case.get("image_resolution", 512))
            text = str(messages[-1]["content"])
            content: list[dict[str, Any]] = [{"type": "text", "text": text}]
            for image_index in range(image_count):
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": simple_png_data_url(
                                width, height, index * 7 + image_index
                            ),
                            "detail": image_detail,
                        },
                    }
                )
            messages[-1]["content"] = content

        served_model = (
            os.environ.get("SERVED_MODEL")
            or os.environ.get("MODEL")
            or self.tokenizer_model
        )
        request: dict[str, Any] = {
            "model": served_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "chat_template_kwargs": {"thinking": thinking},
            "reasoning_effort": reasoning_effort,
        }
        if ignore_eos:
            request["ignore_eos"] = True
        if min_tokens is not None:
            request["min_tokens"] = min_tokens
        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        metadata: dict[str, Any] = {
            "schema_version": 1,
            "workload": self.config_name,
            "case": self.case_name,
            "variant": variant_name,
            "request_index": index,
            "target_isl": target_isl,
            "actual_isl": actual_isl,
            "isl_error": actual_isl - target_isl,
            "isl_scope": "chat-template text tokens before image expansion",
            "max_tokens": max_tokens,
            "min_tokens": min_tokens,
            "ignore_eos": ignore_eos,
            "category": category,
            "thinking": thinking,
            "reasoning_effort": reasoning_effort,
            "tokenizer_model": self.tokenizer_model,
            "tokenizer_revision": self.tokenizer_revision,
            "session_id": session_id,
            "X-Session-ID": session_id,
            "prefix_mode": prefix_mode,
            "prefix_key": prefix_key if prefix_tokens else None,
            "target_prefix_tokens": prefix_tokens,
            "actual_prefix_tokens": actual_prefix_tokens,
            "reuse_percent": reuse_percent,
            "turn_index": turn_index,
            "image_share": image_share,
            "has_images": include_images,
            "image_count": image_count if include_images else 0,
            "image_resolution": f"{width}x{height}" if include_images else None,
        }
        request["_headers"] = {"X-Session-ID": session_id}
        request["_metadata"] = metadata
        return request


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one deterministic workload case as request JSONL."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--requests", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.requests <= 0:
        raise WorkloadError("--requests must be positive")
    config_path = args.config.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    if config_path == output_path:
        raise WorkloadError("--output must not overwrite --config")
    config = load_yaml(config_path)
    tokenizer, tokenizer_model, tokenizer_revision = tokenizer_from_environment()
    generator = Generator(
        tokenizer=tokenizer,
        tokenizer_model=tokenizer_model,
        tokenizer_revision=tokenizer_revision,
        config=config,
        config_path=config_path,
        case_name=args.case,
        requests=args.requests,
        seed=args.seed,
    )
    temporary_path = output_path.with_name(
        f".{output_path.name}.{os.getpid()}.tmp"
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with temporary_path.open("w", encoding="utf-8") as handle:
            for index in range(args.requests):
                json.dump(
                    generator.make_request(index),
                    handle,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                handle.write("\n")
        temporary_path.replace(output_path)
    except OSError as exc:
        raise WorkloadError(f"cannot write {output_path}: {exc}") from exc
    finally:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
    print(
        json.dumps(
            {
                "output": str(output_path),
                "requests": args.requests,
                "case": args.case,
                "tokenizer": tokenizer_model,
                "revision": tokenizer_revision,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except WorkloadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
