import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

summary = load('trace_summary')
controller = load('capture_windows')


def event(name, cat, ts, dur, *, pid=40, tid=7, args=None):
    return dict(name=name, cat=cat, ph='X', ts=ts, dur=dur, pid=pid, tid=tid, args=args or {})


def fixture(cycles=11):
    events = []
    for i in range(cycles):
        t = i * 100
        events.extend([
            event('execute_context_0(0)_generation_2(12)', 'user_annotation', t, 20),
            event('avk5.target_forward', 'user_annotation', t+1, 17),
            event('cudaGraphLaunch', 'cuda_runtime', t+2, 1, args={'correlation': i*2+1}),
            event('target_kernel', 'kernel', t+5, 30, pid=0, tid=1, args={'correlation': i*2+1, 'device': 0, 'stream': 7}),
            event('avk5.draft_propose', 'user_annotation', t+22, 30),
            event('avk5.draft_execution', 'user_annotation', t+25, 20),
            event('cudaGraphLaunch', 'cuda_runtime', t+26, 1, args={'correlation': i*2+2}),
            event('draft_kernel', 'kernel', t+30, 15, pid=0, tid=2, args={'correlation': i*2+2, 'device': 0, 'stream': 8}),
        ])
    return {'traceEvents': events}


class TimingTests(unittest.TestCase):
    def test_union_does_not_sum_overlap(self):
        result = summary.summarize(fixture())
        self.assertTrue(result['descriptive_occupied_time_adequate'])
        row = result['devices'][0]
        self.assertEqual(row['all_activity_union_us'], 440)
        self.assertEqual(row['target_union_us'], 330)
        self.assertEqual(row['draft_total_union_us'], 165)
        self.assertEqual(row['target_draft_overlap_us'], 55)
        self.assertFalse(result['exposed_critical_path_established'])
        self.assertEqual(len(result['complete_eligible_decode_cycles']), 10)
        self.assertEqual(result['cycle_exclusion_counts']['last_target_without_following_target'], 1)
        cycle = result['complete_eligible_decode_cycles'][0]
        self.assertEqual(cycle['cycle_wall_span_us'], 100)
        self.assertEqual(cycle['idle_without_observed_gpu_activity_us'], 60)
        self.assertEqual(cycle['target_occupied_share_of_cycle_span'], .3)
        self.assertEqual(summary.clipped([(0, 12), (18, 30)], 10, 20), [(10, 12), (18, 20)])

    def test_kernel_names_never_substitute_for_correlation(self):
        trace = fixture()
        trace['traceEvents'][3]['args'].pop('correlation')
        result = summary.summarize(trace)
        self.assertFalse(result['descriptive_occupied_time_adequate'])
        self.assertEqual(result['devices'][0]['unattributed_union_us'], 30)

    def test_ambiguous_launch_is_unattributed(self):
        trace = fixture()
        trace['traceEvents'].append(copy.deepcopy(trace['traceEvents'][2]))
        self.assertFalse(summary.summarize(trace)['descriptive_occupied_time_adequate'])

    def test_native_prefill_and_incomplete_cycles_do_not_count(self):
        trace = fixture()
        trace['traceEvents'][0]['name'] = 'execute_context_1(200)_generation_2(12)'
        result = summary.summarize(trace)
        self.assertEqual(len(result['complete_eligible_decode_cycles']), 9)
        self.assertFalse(result['descriptive_occupied_time_adequate'])

    def test_conflicting_correlation_and_negative_duration_rejected(self):
        with self.assertRaises(ValueError):
            summary.correlation({'args': {'correlation': 1, 'correlation_id': 2}})
        with self.assertRaises(ValueError):
            summary.interval({'ts': 0, 'dur': -1})

    def test_missing_rank_writes_failure_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, output = root/'manifest.json', root/'result.json'
            manifest.write_text(json.dumps({'traces': []}))
            with patch('sys.argv', ['trace_summary', '--manifest', str(manifest), '--output', str(output)]):
                self.assertEqual(summary.main(), 1)
            self.assertEqual(json.loads(output.read_text())['status'], 'extraction_failed')

    def test_partial_start_always_stops_both_and_does_not_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity, output = root/'identity.json', root/'result.json'
            identity.write_text('{}')
            calls = []
            def controlled(backends, action):
                calls.append((list(backends), action))
                return [{'ok': True}, {'ok': action == 'stop_profile'}]
            argv = ['capture_windows', '--backend-url', 'http://a', '--backend-url', 'http://b', '--profiling-start-ns', '1000000000000', '--identity-receipt', str(identity), '--output', str(output)]
            with patch('sys.argv', argv), patch.object(controller.time, 'time_ns', return_value=1), patch.object(controller, 'wait_until'), patch.object(controller, 'both', side_effect=controlled):
                self.assertEqual(controller.main(), 1)
            self.assertEqual([action for _, action in calls], ['start_profile', 'stop_profile'])
            result = json.loads(output.read_text())
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(len(result['episodes']), 1)

    def test_late_wakeup_does_not_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity, output = root/'identity.json', root/'result.json'
            identity.write_text('{}')
            argv = ['capture_windows', '--backend-url', 'http://a', '--backend-url', 'http://b', '--profiling-start-ns', '1000000000000', '--identity-receipt', str(identity), '--output', str(output)]
            # Initial guard on time passes; scheduler wakeup is two seconds late.
            with patch('sys.argv', argv), patch.object(controller.time, 'time_ns', side_effect=[1, 1092000000000, 1092000000001]), patch.object(controller, 'wait_until'), patch.object(controller, 'both') as calls:
                self.assertEqual(controller.main(), 1)
            calls.assert_not_called()
            self.assertEqual(json.loads(output.read_text())['status'], 'failed')

if __name__ == '__main__':
    unittest.main()
