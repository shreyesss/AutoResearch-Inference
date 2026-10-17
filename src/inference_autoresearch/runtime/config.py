"""Pinned, allowlisted vLLM configuration resolution.

This module accepts settings, never shell fragments. Domain revisions are owned by
the campaign; broad numeric bounds here are safety checks rather than a search grid.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from inference_autoresearch.contracts import ResolvedServeConfig


PINNED_IMAGE = "vllm/vllm-openai@sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14"
PINNED_MODEL_REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
MODEL_NAME = "Qwen/Qwen3.8-27B"
BASELINE = {
    "max_num_seqs": 512,
    "max_num_batched_tokens": 8192,
    "gpu_memory_utilization": 0.92,
    "enable_prefix_caching": True,
    "mtp_draft_tokens": 0,
    "enable_chunked_prefill": True,
    "long_prefill_token_threshold": 0,
}
ALLOWED_KEYS = frozenset(BASELINE)


class ConfigError(ValueError):
    """A proposal cannot be mapped to a permitted serving configuration."""


@dataclass(frozen=True)
class PinnedEnvironment:
    model_dir: Path
    image: str = PINNED_IMAGE
    model_name: str = MODEL_NAME
    model_revision: str = PINNED_MODEL_REVISION
    max_model_len: int = 40960
    tensor_parallel_size: int = 1
    dtype: str = "bfloat16"
    reasoning_parser: str = "qwen3"
    gpu_uuid: str = "GPU-9bb5b2a6-b234-55f6-6462-e030fcadfa83"

    def validate(self) -> None:
        if self.image != PINNED_IMAGE or self.model_revision != PINNED_MODEL_REVISION:
            raise ConfigError("real runtime requires the measured image and model revision")
        if (self.model_name, self.max_model_len, self.tensor_parallel_size, self.dtype, self.reasoning_parser) != (
            MODEL_NAME, 40960, 1, "bfloat16", "qwen3"
        ):
            raise ConfigError("model/task policy is fixed for this campaign")
        if not self.model_dir.is_absolute():
            raise ConfigError("model_dir must be an absolute path")
        if self.gpu_uuid != "GPU-9bb5b2a6-b234-55f6-6462-e030fcadfa83":
            raise ConfigError("GPU UUID differs from the measured campaign")


def resolve_config(overrides: Mapping[str, object], pinned: PinnedEnvironment,
                   domain: Mapping[str, list[object]] | None = None) -> ResolvedServeConfig:
    pinned.validate()
    unknown = set(overrides) - ALLOWED_KEYS
    if unknown:
        raise ConfigError(f"unsupported serve setting(s): {sorted(unknown)}")
    settings = dict(BASELINE)
    for key, value in overrides.items():
        if domain is not None and (key not in domain or value not in domain[key]):
            raise ConfigError(f"{key}={value!r} is outside the frozen domain")
        settings[key] = value
    for key, upper in (("max_num_seqs", 2048), ("max_num_batched_tokens", 65536)):
        val = settings[key]
        if type(val) is not int or not 1 <= val <= upper:
            raise ConfigError(f"{key} must be an integer in 1..{upper}")
    if settings["max_num_batched_tokens"] > pinned.max_model_len:
        raise ConfigError("token budget exceeds the fixed model context")
    mem = settings["gpu_memory_utilization"]
    if type(mem) not in (float, int) or not 0.5 <= mem <= 0.95:
        raise ConfigError("gpu_memory_utilization must be in 0.5..0.95")
    settings["gpu_memory_utilization"] = float(mem)
    if type(settings["enable_prefix_caching"]) is not bool:
        raise ConfigError("enable_prefix_caching must be a boolean")
    mtp = settings["mtp_draft_tokens"]
    if type(mtp) is not int or not 0 <= mtp <= 5:
        raise ConfigError("mtp_draft_tokens must be an integer in 0..5")
    if type(settings["enable_chunked_prefill"]) is not bool:
        raise ConfigError("enable_chunked_prefill must be a boolean")
    threshold = settings["long_prefill_token_threshold"]
    if type(threshold) is not int or threshold < 0 or threshold > pinned.max_model_len:
        raise ConfigError("invalid long_prefill_token_threshold")
    if threshold and not settings["enable_chunked_prefill"]:
        raise ConfigError("long prefill threshold requires chunked prefill")

    # Explicitly set all supported effective values except MTP=0, whose native
    # behavior is omission. The baseline still hashes its resolved defaults.
    argv = [
        "/models/Qwen3.8-27B", "--served-model-name", pinned.model_name,
        "--tensor-parallel-size", "1", "--dtype", "bfloat16",
        "--max-model-len", "40960", "--reasoning-parser", "qwen3",
        "--max-num-seqs", str(settings["max_num_seqs"]),
        "--max-num-batched-tokens", str(settings["max_num_batched_tokens"]),
        "--gpu-memory-utilization", str(settings["gpu_memory_utilization"]),
        "--enable-prefix-caching" if settings["enable_prefix_caching"] else "--no-enable-prefix-caching",
        "--enable-chunked-prefill" if settings["enable_chunked_prefill"] else "--no-enable-chunked-prefill",
    ]
    if threshold:
        argv += ["--long-prefill-token-threshold", str(threshold)]
    if mtp:
        argv += ["--speculative-config", json.dumps({"method": "mtp", "num_speculative_tokens": mtp}, separators=(",", ":"))]
    argv += ["--host", "0.0.0.0", "--port", "8000"]
    pins = {"model": pinned.model_name, "revision": pinned.model_revision, "image": pinned.image,
            "dtype": pinned.dtype, "context": str(pinned.max_model_len)}
    identity = {"settings": settings, "pins": pins}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return ResolvedServeConfig(f"cfg-{digest[:20]}", argv, settings, pins, pinned.image, {})


def verify_model_files(model_dir: Path) -> dict[str, object]:
    """Fail closed on the measured local checkpoint shape and revision."""
    if not model_dir.is_dir():
        raise ConfigError(f"model directory absent: {model_dir}")
    shards = sorted(model_dir.glob("*.safetensors"))
    if len(shards) != 18 or any(p.stat().st_size == 0 for p in shards):
        raise ConfigError("expected 18 non-empty local safetensors shards")
    for filename in ("config.json", "tokenizer_config.json"):
        if not (model_dir / filename).is_file():
            raise ConfigError(f"missing {filename}")
    return {"model_dir": str(model_dir), "shard_count": len(shards),
            "total_shard_bytes": sum(p.stat().st_size for p in shards),
            "expected_revision": PINNED_MODEL_REVISION}
