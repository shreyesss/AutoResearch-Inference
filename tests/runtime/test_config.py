from pathlib import Path

import pytest

from inference_autoresearch.runtime.config import BASELINE, ConfigError, PinnedEnvironment, resolve_config
from inference_autoresearch.runtime.docker import DockerRuntimeManager, RuntimeFailure


def test_baseline_identity_and_authority():
    pin = PinnedEnvironment(Path("/models/Qwen3.8-27B"))
    b0 = resolve_config({}, pin)
    assert b0.effective_settings == BASELINE
    assert resolve_config(dict(BASELINE), pin).config_id == b0.config_id
    assert "--max-num-seqs" in b0.argv and b0.argv[b0.argv.index("--max-num-seqs") + 1] == "512"
    with pytest.raises(ConfigError):
        resolve_config({"model": "another/model"}, pin)
    with pytest.raises(ConfigError):
        resolve_config({"max_num_seqs": 32}, pin, {"max_num_seqs": [128, 512]})


def test_conditional_serve_controls():
    pin = PinnedEnvironment(Path("/models/Qwen3.8-27B"))
    with pytest.raises(ConfigError):
        resolve_config({"enable_chunked_prefill": False, "long_prefill_token_threshold": 2048}, pin)
    mtp = resolve_config({"mtp_draft_tokens": 3}, pin)
    assert "--speculative-config" in mtp.argv
    assert mtp.config_id != resolve_config({}, pin).config_id


def test_eager_execution_is_conditional_and_keeps_stock_identity():
    pin = PinnedEnvironment(Path("/models/Qwen3.8-27B"))
    stock = resolve_config({}, pin)
    assert resolve_config({"enforce_eager": False}, pin).config_id == stock.config_id
    eager = resolve_config({"enforce_eager": True}, pin, {"enforce_eager": [False, True]})
    assert eager.config_id != stock.config_id
    assert "--enforce-eager" in eager.argv
    assert "--enforce-eager" not in stock.argv
    with pytest.raises(ConfigError):
        resolve_config({"enforce_eager": 1}, pin)


def test_canonical_config_reaches_lease_check_without_docker(tmp_path, monkeypatch):
    pin = PinnedEnvironment(Path("/models/Qwen3.8-27B"))
    manager = DockerRuntimeManager(pin, tmp_path / "gpu.lock")
    class LeaseReached(Exception):
        pass
    def stop_before_external_effect():
        raise LeaseReached()
    monkeypatch.setattr(manager, "_acquire", stop_before_external_effect)
    with pytest.raises(LeaseReached):
        manager.start(resolve_config({}, pin), tmp_path / "server")


def test_startup_accepts_pinned_vllm_default_token_budget_log_format():
    pin = PinnedEnvironment(Path("/models/Qwen3.8-27B"))
    config = resolve_config({"max_num_batched_tokens": 2048,
                             "long_prefill_token_threshold": 8192,
                             "enforce_eager": True}, pin,
                            {"max_num_batched_tokens": [2048, 8192],
                             "long_prefill_token_threshold": [0, 8192],
                             "enforce_eager": [False, True]})
    log = ("v0.28.0 model='/models/Qwen3.8-27B' max_seq_len=40960 "
           "'max_num_seqs': 512 enable_prefix_caching=True "
           "enable_chunked_prefill=True "
           "non-default args: {'max_num_batched_tokens': 2048, "
           "'long_prefill_token_threshold': 8192} "
           "Desired GPU memory utilization is (0.92, 87.37 GiB) "
           "enforce_eager=True speculative_config=None")
    evidence = DockerRuntimeManager._verify_startup(log, config)
    assert evidence["checks"]["token_budget"] is True
    with pytest.raises(RuntimeFailure):
        DockerRuntimeManager._verify_startup(log.replace("'max_num_batched_tokens': 2048", ""), config)
