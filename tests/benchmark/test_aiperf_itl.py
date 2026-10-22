"""CPU-only native export validation; no AIPerf/model/runtime imports."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inference_autoresearch.benchmark.aiperf import normalize_exports


def chunk(delta, count=None, *, usage=None):
    body = {"object": "chat.completion.chunk", "choices": [{"delta": delta}]}
    if usage is not None:
        body["usage"] = usage
    elif count is not None:
        body["usage"] = {"completion_tokens": count}
    return {"perf_ns": 1, "packets": [{"name": "data", "value": json.dumps(body)}]}


class AIPerfITLTest(unittest.TestCase):
    def normalize(self, responses, itl, *, continuous=True, completion=10, reasoning=4,
                  endpoint=None, wire_options=None):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            manifest = {"traffic_mode": "independent_open_loop", "scenario_id": "cpu-fixture",
                        "schedule_sha256": "fixture", "workload_name": "cpu-fixture"}
            planned = [{"session_id": "request", "timestamp": 0, "text": "hello",
                        "output_length": completion}]
            payload = {"messages": [{"role": "user", "content": "hello"}],
                       "max_completion_tokens": completion}
            if continuous is not None:
                payload["stream_options"] = {"continuous_usage_stats": continuous}
            if wire_options is not None:
                payload["stream_options"] = wire_options
            raw = {"metadata": {"conversation_id": "request", "x_request_id": "native",
                                "request_start_ns": 1000000, "request_end_ns": 101000000,
                                "credit_issued_ns": 1000000},
                   "status": 200, "payload": payload}
            if responses is not None:
                raw["responses"] = responses
            metrics = {"time_to_first_token": 20, "request_latency": 100,
                       "inter_token_latency": itl, "usage_prompt_tokens": 2,
                       "usage_completion_tokens": completion, "usage_reasoning_tokens": reasoning}
            (path / "profile_export_raw.jsonl").write_text(json.dumps(raw) + "\n")
            (path / "profile_export.jsonl").write_text(json.dumps({
                "metadata": {"x_request_id": "native"},
                "metrics": {key: {"value": value} for key, value in metrics.items()}}) + "\n")
            summary = {"is_complete": True, "aiperf_version": "0.13.0"}
            if endpoint is not None:
                summary["input_config"] = {"endpoint": endpoint}
            (path / "profile_export_aiperf.json").write_text(json.dumps(summary))
            scenario = {"manifest": manifest, "metadata": {"registry_root": temp}}
            with patch("inference_autoresearch.benchmark.aiperf.verify_scenario",
                       return_value={"planned": planned}):
                result = normalize_exports(scenario, path, config_id="cpu", run_id="cpu",
                                           stage="triage")
            row = json.loads((path / "normalized-requests.jsonl").read_text())
            return result, row

    def test_valid_bundled_first_chunk_is_not_rejected(self):
        result, row = self.normalize([chunk({"content": "abc"}, 3)], 80 / 7)
        self.assertEqual(result.status, "valid", result.reason_codes)
        self.assertEqual(row["first_content_chunk_tokens"], 3)
        self.assertEqual(row["itl_decode_tokens"], 7)
        self.assertEqual(row["itl_validation_source"], "raw_first_content_chunk_usage")
        self.assertEqual(result.metrics["tpot_p50_ms"], 80 / 7)

    def test_wrong_metric_still_fails_with_independent_chunk_evidence(self):
        result, row = self.normalize([chunk({"content": "abc"}, 3)], 80 / 9)
        self.assertIn("token_counting_mismatch", result.reason_codes)
        self.assertEqual(row["itl_decode_tokens"], 7)

    def test_volunteered_usage_without_opt_in_keeps_legacy(self):
        for continuous in (False, None):
            with self.subTest(continuous=continuous):
                result, row = self.normalize([chunk({"content": "abc"}, 3)], 80 / 9,
                                             continuous=continuous)
                self.assertEqual(result.status, "valid", result.reason_codes)
                self.assertEqual(row["itl_decode_tokens"], 9)
                self.assertEqual(row["itl_validation_source"], "legacy_per_chunk_usage_not_requested")

    def test_exported_run_opt_in_overrides_wire_payload(self):
        for enabled, wire, expected in ((False, True, 9), (True, False, 7), (True, None, 7)):
            with self.subTest(enabled=enabled, wire=wire):
                result, row = self.normalize([chunk({"content": "abc"}, 3)], 80 / expected,
                    continuous=wire, endpoint={"per_chunk_usage": enabled,
                        "use_server_token_count": True, "type": "chat", "streaming": True})
                self.assertEqual(result.status, "valid", result.reason_codes)
                self.assertEqual(row["itl_decode_tokens"], expected)

    def test_malformed_or_unsupported_exported_endpoint_is_ineligible(self):
        for endpoint in ({"per_chunk_usage": "false"}, {"use_server_token_count": False},
                         {"type": "completions"}, {"streaming": False}, [], False, "", 0):
            with self.subTest(endpoint=endpoint):
                result, row = self.normalize([chunk({"content": "abc"}, 3)], 80 / 7,
                                             endpoint=endpoint)
                self.assertIn("token_counting_mismatch", result.reason_codes)
                self.assertEqual(row["itl_validation_source"], "unsupported_raw_chunk_evidence")

    def test_malformed_falsy_wire_options_are_not_legacy_evidence(self):
        for options in ([], False, "", 0):
            with self.subTest(options=options):
                result, row = self.normalize([chunk({"content": "abc"}, 3)], 80 / 9,
                                             wire_options=options)
                self.assertIn("token_counting_mismatch", result.reason_codes)
                self.assertEqual(row["itl_validation_source"], "unsupported_raw_chunk_evidence")

    def test_legacy_missing_raw_responses_without_opt_in(self):
        result, row = self.normalize(None, 80 / 9, continuous=None)
        self.assertEqual(result.status, "valid", result.reason_codes)
        self.assertEqual(row["itl_decode_tokens"], 9)

    def test_final_usage_only_does_not_become_first_chunk_count(self):
        final = {"object": "chat.completion.chunk", "choices": [],
                 "usage": {"completion_tokens": 10}}
        responses = [chunk({"content": "abc"}),
                     {"packets": [{"name": "data", "value": json.dumps(final)}]},
                     {"packets": [{"name": "data", "value": "[DONE]"}]}]
        result, row = self.normalize(responses, 80 / 9)
        self.assertEqual(result.status, "valid", result.reason_codes)
        self.assertEqual(row["itl_validation_source"], "legacy_no_content_chunk_usage")

    def test_reasoning_and_tool_text_define_content_but_role_and_tool_id_do_not(self):
        for data in ({"reasoning_content": "think"}, {"reasoning": "think"},
                     {"tool_calls": [{"function": {"name": "run", "arguments": ""}}]},
                     {"tool_calls": [{"function": {"arguments": "{}"}}]}):
            with self.subTest(data=data):
                responses = [chunk({"role": "assistant"}, 1),
                             chunk({"tool_calls": [{"id": "call"}]}, 2), chunk(data, 3)]
                result, row = self.normalize(responses, 80 / 7)
                self.assertEqual(result.status, "valid", result.reason_codes)
                self.assertEqual(row["itl_decode_tokens"], 7)  # Reasoning included once.

    def test_first_response_with_data_and_usage_matches_pinned_parser(self):
        # This is the upstream selection rule, even if usage arrives later
        # than the first content response that set TTFT.
        result, row = self.normalize([chunk({"content": "a"}),
                                     chunk({"content": "bc"}, 3)], 80 / 7)
        self.assertEqual(result.status, "valid", result.reason_codes)
        self.assertEqual(row["first_content_chunk_tokens"], 3)

    def test_nonempty_usage_missing_count_stops_search_like_upstream(self):
        result, row = self.normalize([chunk({"content": "a"}, usage={"prompt_tokens": 2}),
                                     chunk({"content": "bc"}, 3)], 80 / 9)
        self.assertEqual(result.status, "valid", result.reason_codes)
        self.assertEqual(row["itl_validation_source"], "legacy_first_content_usage_missing_count")

    def test_invalid_numeric_counts_use_upstream_fallback(self):
        for count in (-1, 0, 10, 11):
            with self.subTest(count=count):
                result, row = self.normalize([chunk({"content": "abc"}, count)], 80 / 9)
                self.assertEqual(result.status, "valid", result.reason_codes)
                self.assertEqual(row["itl_decode_tokens"], 9)
                self.assertEqual(row["first_content_chunk_tokens"], count)

    def test_unsupported_or_malformed_opted_in_evidence_fails_closed(self):
        bad_responses = [None, [], [{"text": "not SSE"}],
                         [{"packets": [{"name": "data", "value": "not JSON"}]}],
                         [{"packets": [{"name": "data", "value": "[]"}]}],
                         [chunk({"content": "abc"}, True)],
                         [chunk({"content": "abc"}, "3")],
                         [chunk({"content": ["abc"]}, 3)],
                         [chunk({"content": "abc"}, usage={"output_tokens": 3})]]
        for responses in bad_responses:
            with self.subTest(responses=responses):
                result, row = self.normalize(responses, 80 / 9)
                self.assertIn("token_counting_mismatch", result.reason_codes)
                self.assertEqual(row["itl_validation_source"], "unsupported_raw_chunk_evidence")

    def test_single_completion_token_keeps_itl_ineligible(self):
        result, row = self.normalize([chunk({"content": "a"}, 1)], None, completion=1, reasoning=0)
        self.assertEqual(result.status, "valid", result.reason_codes)
        self.assertEqual(result.counts["tpot_eligible"], 0)
        self.assertIsNone(result.metrics["tpot_p50_ms"])

    def test_inconsistent_reasoning_or_nonintegral_counts_fail_validation(self):
        for completion, reasoning in ((10, 11), (10, -1), (10, 1.5), (10.5, 4), (True, 0)):
            with self.subTest(completion=completion, reasoning=reasoning):
                result, _ = self.normalize([chunk({"content": "abc"}, 3)], 80 / 7,
                                           completion=completion, reasoning=reasoning)
                self.assertIn("token_counting_mismatch", result.reason_codes)


if __name__ == "__main__":
    unittest.main()
