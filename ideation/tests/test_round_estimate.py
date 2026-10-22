import copy
import json
from pathlib import Path

import pytest

from ideation.foundation import invoke
from ideation.round_estimate import estimate_rounds


def example(law="block"):
    # Ternary output abc, B2. At anchor0 q/p = 2, 1/4.
    # Conditional block survival: 1, 1/2. Ordinary: 1, 1/4.
    return {
        "schema_version": 1, "law": law, "block_size": 2,
        "horizon": "fixed_output_cap_no_eos_full_block", "adaptive_verification": False,
        "probability_semantics": "normalized_after_sampling_transforms_all_anchors",
        "provenance": {"kind": "synthetic", "target": "ternary fixture p",
                       "proposal": "anchor-conditioned fixture q", "trajectory": "abc",
                       "probability_source": "hand-derived normalized ternary distributions"},
        "target_probabilities": [.25, .5, .5],
        "proposal_probabilities_by_anchor": [[.5, .125], [.5, .5], [.5]],
    }


def test_block_law_is_not_ordinary_overlap_product():
    block = estimate_rounds(example())
    ordinary = estimate_rounds(example("ordinary"))
    assert block["expected_rounds_given_trajectory"] == pytest.approx(1.5)
    assert ordinary["expected_rounds_given_trajectory"] == pytest.approx(1.75)
    assert block["round_start_probabilities"] == pytest.approx([1, 0, .5])
    assert block["provenance_verified"] is False


@pytest.mark.parametrize("law", ["ordinary", "block"])
def test_exact_proposal_and_zero_proposal_extremes(law):
    data = example(law)
    data["target_probabilities"] = [.5] * 7
    data["proposal_probabilities_by_anchor"] = [[.5] * min(2, 7-n) for n in range(7)]
    assert estimate_rounds(data)["expected_rounds_given_trajectory"] == 3
    data["proposal_probabilities_by_anchor"] = [[0] * min(2, 7-n) for n in range(7)]
    assert estimate_rounds(data)["expected_rounds_given_trajectory"] == 7
    data["target_probabilities"] = [.5]
    data["proposal_probabilities_by_anchor"] = [[0]]
    assert estimate_rounds(data)["expected_rounds_given_trajectory"] == 1


def test_small_probabilities_do_not_lose_prefix_ratio():
    data = example()
    data["target_probabilities"] = [1e-300] * 3
    data["proposal_probabilities_by_anchor"] = [[2e-300, 2.5e-301], [1e-300, 1e-300], [1e-300]]
    assert estimate_rounds(data)["expected_rounds_given_trajectory"] == pytest.approx(1.5)


@pytest.mark.parametrize("field,value", [
    ("schema_version", True), ("schema_version", 1.0), ("law", []),
    ("adaptive_verification", True), ("adaptive_verification", 0),
    ("horizon", "eos"), ("probability_semantics", "logits"),
    ("target_probabilities", [.25, 0, .5]),
    ("target_probabilities", [.25, float("nan"), .5]),
    ("target_probabilities", [.25, True, .5]),
    ("target_probabilities", [.25, 10**1000, .5]),
    ("proposal_probabilities_by_anchor", [[.5, .125]]),
    ("proposal_probabilities_by_anchor", [[.5], [.5, .5], [.5]]),
    ("proposal_probabilities_by_anchor", [[.5, 1.1], [.5, .5], [.5]]),
    ("block_size", True), ("law", "native_dspark"), ("provenance", {}),
])
def test_reject_incompatible_or_incomplete_inputs(field, value):
    data = example()
    data[field] = value
    with pytest.raises(ValueError):
        estimate_rounds(data)


def test_cli_keeps_result_and_journal_without_network_or_model(tmp_path):
    state = tmp_path / "state"
    invoke(["--state-dir", str(state), "init"])
    source = tmp_path / "input.json"
    data = example()
    original = copy.deepcopy(data)
    source.write_text(json.dumps(data))
    result = invoke(["--state-dir", str(state), "--defer-snapshot", "round-estimate", "--record", str(source)])
    saved = json.loads((Path(result["output"]) / "result.json").read_text())
    assert json.loads((Path(result["output"]) / "input.json").read_text()) == original
    assert saved["expected_rounds_given_trajectory"] == pytest.approx(1.5)
    assert saved["gpu_calls"] == saved["model_calls"] == saved["network_calls"] == 0
    assert json.loads(source.read_text()) == original
    history = invoke(["--state-dir", str(state), "history"])
    assert "round-estimate" in json.dumps(history)
