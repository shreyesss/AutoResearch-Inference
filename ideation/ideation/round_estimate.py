"""Conditional round-count diagnostic for ideal fixed-block speculative laws.

No model loading or probability collection. See docs/OFFLINE_ROUND_ESTIMATE.md.
The block posterior follows Sun et al. 2403.10444v3 and the round-start
occupancy construction follows EDR 2610.10411v1; this is not a native verifier.
"""
import hashlib
import json
import math


def _probability(value, label, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not 0 <= value <= 1 or not math.isfinite(value)
            or positive and value == 0):
        raise ValueError(label + " must be a finite probability" + (" > 0" if positive else ""))
    return float(value)


def estimate_rounds(record):
    """Return E[rounds | supplied target trajectory] in O(length * block_size).

    p[t] is the normalized target probability of the realized token at t.
    q[n][j] is its proposal probability at position n+j from anchor n,
    conditioned on the realized preceding path, not only a visited draft path.
    The full block is generated before truncating committed output at the cap.
    """
    if (not isinstance(record, dict) or type(record.get("schema_version")) is not int
            or record["schema_version"] != 1):
        raise ValueError("schema_version must be 1")
    if not isinstance(record.get("law"), str) or record["law"] not in {"ordinary", "block"}:
        raise ValueError("law must be ordinary or block")
    if record.get("horizon") != "fixed_output_cap_no_eos_full_block":
        raise ValueError("Unsupported stopping policy")
    if record.get("adaptive_verification") is not False:
        raise ValueError("Adaptive verification is outside this diagnostic")
    size = record.get("block_size")
    if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= 1024:
        raise ValueError("block_size must be an integer in 1..1024")
    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("provenance is required")
    for name in ("target", "proposal", "trajectory", "probability_source"):
        if not isinstance(provenance.get(name), str) or not provenance[name].strip():
            raise ValueError("provenance." + name + " is required")
    if (not isinstance(provenance.get("kind"), str)
            or provenance["kind"] not in {"synthetic", "target_sampled", "user_supplied"}):
        raise ValueError("provenance.kind must describe trajectory origin")
    if record.get("probability_semantics") != "normalized_after_sampling_transforms_all_anchors":
        raise ValueError("Normalized actual p/q at all anchors are required")
    target = record.get("target_probabilities")
    proposal = record.get("proposal_probabilities_by_anchor")
    if not isinstance(target, list) or not 1 <= len(target) <= 100_000:
        raise ValueError("target_probabilities must contain 1..100000 values")
    length = len(target)
    if length * min(size, length) > 2_000_000:
        raise ValueError("Diagnostic exceeds two million probability cells")
    if not isinstance(proposal, list) or len(proposal) != length:
        raise ValueError("One proposal row is required for every anchor")
    p = [_probability(v, "target_probabilities", positive=True) for v in target]
    q = []
    for anchor, row in enumerate(proposal):
        if not isinstance(row, list) or len(row) != min(size, length - anchor):
            raise ValueError("Proposal rows must cover min(block_size, remaining_output) positions")
        q.append([_probability(v, "proposal_probabilities_by_anchor") for v in row])

    starts = [0.0] * length
    starts[0] = 1.0
    terminal = 0.0
    for anchor, weight in enumerate(starts):
        if weight == 0:
            continue
        survival = 1.0
        log_ratio = 0.0
        log_survival = 0.0
        remaining = length - anchor
        for advance in range(1, min(size + 1, remaining) + 1):
            if advance == remaining or advance == size + 1:
                boundary = survival
            else:
                probability = q[anchor][advance - 1]
                step = (math.log(probability) - math.log(p[anchor + advance - 1])
                        if probability else -math.inf)
                if record["law"] == "block":
                    log_ratio += step
                    log_survival = min(log_survival, log_ratio)
                else:
                    log_survival += min(0.0, step)
                next_survival = math.exp(log_survival)
                boundary = survival - next_survival
                survival = next_survival
            mass = weight * boundary
            if anchor + advance == length:
                terminal += mass
            else:
                starts[anchor + advance] += mass
    if not math.isclose(terminal, 1.0, rel_tol=1e-10, abs_tol=1e-10):
        raise ArithmeticError("Terminal probability mass failed conservation")
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {
        "schema_version": 1, "status": "conditional_diagnostic_only",
        "law": record["law"], "block_size": size, "output_length": length,
        "expected_rounds_given_trajectory": math.fsum(starts),
        "round_start_probabilities": starts, "terminal_probability": terminal,
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "provenance": dict(provenance), "provenance_verified": False,
        "limitations": [
            "Caller supplies normalized actual p/q at every potential anchor; this tool cannot verify them from scalar probabilities.",
            "Ideal independent coins, exact residual law, fixed block and no EOS; not native numerical/RNG or AV validation.",
            "Binary64 log arithmetic avoids prefix-product underflow; tiny survival probabilities can still underflow to zero.",
            "A workload expectation requires target-law sampled trajectories; arbitrary text is only a conditional diagnostic.",
            "Expected rounds is not latency, ITL, goodput, accepted-length ratio or a promotion decision.",
        ],
        "network_calls": 0, "model_calls": 0, "gpu_calls": 0,
    }
