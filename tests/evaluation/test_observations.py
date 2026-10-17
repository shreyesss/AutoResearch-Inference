import json

from inference_autoresearch.evaluation.observations import observation_receipt


def test_requested_observations_distinguish_measured_from_unavailable(tmp_path):
    (tmp_path / "aiperf").mkdir()
    (tmp_path / "server").mkdir()
    (tmp_path / "aiperf/server_metrics_export.csv").write_text("Metric,avg\n")
    (tmp_path / "server/server.log").write_text("graph capture\n")
    (tmp_path / "cell-result.json").write_text(json.dumps({"diagnostics": {
        "server_gauges": {"queue_max": 1, "kv_cache_usage_max": 0.35,
                          "achieved_cache_hit_fraction": 0.0}}}))
    receipt = observation_receipt(
        ["resolved_config", "queue_batch_summary", "token_budget_summary",
         "cache_memory_summary", "graph_summary", "targeted_profile"],
        {"effective_settings": {"max_num_batched_tokens": 4096}}, tmp_path)
    observations = receipt["observations"]
    assert observations["resolved_config"]["status"] == "available"
    assert observations["queue_batch_summary"]["queue_max"] == 1
    assert observations["token_budget_summary"]["status"] == "partial"
    assert observations["token_budget_summary"]["max_num_batched_tokens"] == 4096
    assert observations["cache_memory_summary"]["kv_cache_usage_max"] == 0.35
    assert observations["graph_summary"]["status"] == "raw_log_only"
    assert observations["targeted_profile"]["status"] == "not_executed"
    assert receipt["extra_gpu_traffic_executed"] is False
