"""Versioned search domain and effective-configuration identities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(data: Any) -> str:
    return hashlib.sha256(canonical(data).encode()).hexdigest()


def scientific_campaign_hash(campaign: dict[str, Any]) -> str:
    """Operational status/report location do not change the frozen experiment."""
    frozen = {k: v for k, v in campaign.items() if k not in
              ("status", "real_search_qualification_path", "project_root",
               "qualification_requirements")}
    return sha(frozen)


def config_identity(campaign: dict[str, Any], effective: dict[str, Any]) -> str:
    """Use the exact trusted runtime resolver so dedupe matches measured config IDs."""
    from inference_autoresearch.runtime.config import ALLOWED_KEYS, PinnedEnvironment, resolve_config
    model, runtime = campaign["model"], campaign["runtime"]
    pinned = PinnedEnvironment(Path(model["local_path"]).resolve(), image=runtime["image"],
                  model_name=model["id"], model_revision=model["revision"],
                  max_model_len=model["max_model_len"],
                  tensor_parallel_size=model["tensor_parallel_size"], dtype=model["dtype"],
                  gpu_uuid=runtime["gpu_uuid"])
    return resolve_config({k: v for k, v in effective.items() if k in ALLOWED_KEYS}, pinned).config_id


@dataclass(frozen=True)
class Domain:
    raw: dict[str, Any]

    @classmethod
    def load(cls, path: Path) -> "Domain":
        raw = json.loads(path.read_text())
        if not isinstance(raw.get("parameters"), dict):
            raise ValueError("search domain needs parameters")
        for key, spec in raw["parameters"].items():
            if spec.get("baseline") not in spec.get("values", []):
                raise ValueError(f"B0 value missing from domain: {key}")
        return cls(raw)

    @property
    def digest(self) -> str:
        return sha(self.raw)

    def validate(self, overrides: dict[str, Any]) -> None:
        for key, value in overrides.items():
            spec = self.raw["parameters"].get(key)
            if spec is None:
                raise ValueError(f"unsupported parameter: {key}")
            if spec.get("active") is False:
                raise ValueError(f"parameter requires capability qualification: {key}")
            if value not in spec["values"] or isinstance(value, bool) != isinstance(spec["baseline"], bool):
                raise ValueError(f"value outside active domain: {key}={value!r}")
        if "long_prefill_token_threshold" in overrides:
            if overrides.get("enable_chunked_prefill") is False:
                raise ValueError("long prefill threshold requires chunked prefill")

    def effective(self, baseline: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        self.validate(overrides)
        effective = dict(baseline)
        effective.update(overrides)
        if not effective.get("enable_chunked_prefill") and effective.get("long_prefill_token_threshold", 0):
            raise ValueError("long prefill threshold requires chunked prefill")
        return effective

    def proposal_schema(self) -> dict[str, Any]:
        """Sparse application wire contract, after Codex null overrides are removed."""
        props = {name: {"enum": spec["values"]} for name, spec in self.raw["parameters"].items()
                 if spec.get("active") is not False}
        prediction = {"type": "object", "properties": {k: {"type": "string", "minLength": 1} for k in
                      ("observation", "expected_change", "scope")},
                      "required": ["observation", "expected_change", "scope"],
                      "additionalProperties": False}
        fields: dict[str, Any] = {
            "schema_version": {"const": "0.2"}, "proposal_id": {"type": "string", "minLength": 1},
            "parent_configuration_ids": {"type": "array", "items": {"type": "string"}},
            "parameters": {"type": "object", "properties": props, "additionalProperties": False},
            "hypothesis": {"type": "string", "minLength": 1},
            "expected_tradeoff": {"type": "string", "minLength": 1},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
            "experiment_kind": {"enum": ["hypothesis", "exploration"]},
            "predictions": {"type": "array", "items": prediction, "minItems": 1},
            "falsification_condition": {"type": "string", "minLength": 1},
            "requested_observations": {"type": "array", "items": {"enum": [
                "resolved_config", "queue_batch_summary", "token_budget_summary",
                "cache_memory_summary", "speculation_summary", "graph_summary", "targeted_profile"]}},
        }
        return {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
                "properties": fields, "required": list(fields), "additionalProperties": False}

    def codex_output_schema(self) -> dict[str, Any]:
        """Strict Codex JSON Schema: every object property is required and typed.

        Nullable parameter values represent omitted overrides. This is normalized
        back to the sparse v0.2 application contract before domain validation.
        """
        params: dict[str, Any] = {}
        for name, spec in self.raw["parameters"].items():
            if spec.get("active") is False:
                continue
            baseline = spec["baseline"]
            kind = "boolean" if type(baseline) is bool else "integer" if type(baseline) is int else "number"
            params[name] = {"type": [kind, "null"], "enum": [*spec["values"], None]}
        pred_props = {key: {"type": "string"} for key in ("observation", "expected_change", "scope")}
        prediction = {"type": "object", "properties": pred_props,
                      "required": list(pred_props), "additionalProperties": False}
        fields: dict[str, Any] = {
            "schema_version": {"type": "string", "enum": ["0.2"]},
            "proposal_id": {"type": "string"},
            "parent_configuration_ids": {"type": "array", "items": {"type": "string"}},
            "parameters": {"type": "object", "properties": params,
                           "required": list(params), "additionalProperties": False},
            "hypothesis": {"type": "string"},
            "expected_tradeoff": {"type": "string"},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
            "experiment_kind": {"type": "string", "enum": ["hypothesis", "exploration"]},
            "predictions": {"type": "array", "items": prediction},
            "falsification_condition": {"type": "string"},
            "requested_observations": {"type": "array", "items": {"type": "string", "enum": [
                "resolved_config", "queue_batch_summary", "token_budget_summary",
                "cache_memory_summary", "speculation_summary", "graph_summary", "targeted_profile"]}},
        }
        return {"type": "object", "properties": fields, "required": list(fields),
                "additionalProperties": False}
