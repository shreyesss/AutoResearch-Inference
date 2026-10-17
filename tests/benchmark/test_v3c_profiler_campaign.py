import json
from copy import deepcopy
from pathlib import Path

import pytest

from inference_autoresearch.cli import _candidate, _validate_sla_profile_campaign
from inference_autoresearch.search.domain import Domain


ROOT = Path(__file__).resolve().parents[2]


def _study_campaign(tmp_path):
    configs = tmp_path / "configs"
    configs.mkdir()
    source = json.loads((ROOT / "configs/campaign-v2.json").read_text())
    serving = json.loads((ROOT / "configs/campaign-sla-serving-v3c.json").read_text())
    source_path = configs / "campaign-v2.json"
    source_path.write_text(json.dumps(source))
    serving_path = configs / "campaign-sla-serving-v3c.json"
    study_path = tmp_path / "study.json"
    serving["sla_study_path"] = "study.json"
    serving_path.write_text(json.dumps(serving))
    study = {"source_campaign_path": "configs/campaign-v2.json",
             "screen": {"scenario_id": serving["screen_scenario_ids"][0]},
             "adaptive_development": {"scenario_id": serving["development_scenario_ids"][0]}}
    return serving, serving_path, study_path, study


def test_v3c_finalist_profile_accepts_expanded_axes_under_same_b0_pins(tmp_path):
    serving, serving_path, study_path, study = _study_campaign(tmp_path)
    _validate_sla_profile_campaign(serving, serving_path, study_path, study)
    domain = Domain.load(ROOT / "configs/search-domain-v3c.json")
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps({
        "proposal_id": "expanded-finalist",
        "parameters": {"max_num_seqs": 128, "gpu_memory_utilization": 0.9}}))
    candidate = _candidate(candidate_path, domain)
    assert candidate.parameters == {"max_num_seqs": 128, "gpu_memory_utilization": 0.9}
    domain.validate(candidate.parameters)


@pytest.mark.parametrize("changed", ["model", "runtime", "baseline", "sla_study_path",
                                            "search_domain_path"])
def test_v3c_finalist_profile_refuses_changed_study_or_environment(tmp_path, changed):
    serving, serving_path, study_path, study = _study_campaign(tmp_path)
    altered = deepcopy(serving)
    altered[changed] = {} if isinstance(altered[changed], dict) else "different.json"
    with pytest.raises(ValueError, match="approved study or pinned B0 environment"):
        _validate_sla_profile_campaign(altered, serving_path, study_path, study)


def test_v3c_finalist_profile_invokes_its_own_search_campaign(tmp_path, monkeypatch):
    from inference_autoresearch.contracts import CandidateProposal
    from inference_autoresearch.search.sla_controller import SLAServingController
    import inference_autoresearch.search.sla_controller as module

    serving, serving_path, study_path, _ = _study_campaign(tmp_path)
    seen = {}

    class Process:
        returncode = 0

        def __init__(self, argv, **kwargs):
            seen["argv"] = argv

        def communicate(self, timeout):
            return json.dumps({"status": "observed", "artifacts": {}}), ""

    class Ledger:
        def append(self, *args):
            pass

    monkeypatch.setattr(module.subprocess, "Popen", Process)
    controller = SLAServingController(serving, serving_path,
                                      Domain.load(ROOT / "configs/search-domain-v3c.json"),
                                      None, None, None, Ledger(), tmp_path / "artifacts")
    proposal = CandidateProposal(proposal_id="expanded-finalist", experiment_kind="exploration",
                                 hypothesis="Test sequence and KV settings",
                                 expected_tradeoff="KV headroom versus graph pressure",
                                 predictions=[{"observation": "KV capacity", "expected_change": "decrease",
                                               "scope": "mixed development"}],
                                 falsification_condition="No measurable change in KV capacity",
                                 parameters={"max_num_seqs": 128, "gpu_memory_utilization": 0.9})
    controller._profile_finalist(proposal, study_path)
    argv = seen["argv"]
    assert argv[argv.index("--campaign") + 1] == str(serving_path)
    assert argv[argv.index("--study") + 1] == str(study_path)
    candidate = _candidate(Path(argv[argv.index("--candidate") + 1]), controller.domain)
    assert candidate.parameters == proposal.parameters
