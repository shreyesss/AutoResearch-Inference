import unittest
from audit_saved_trace import audit, corr


def event(cat, name, ts=10, dur=1, pid=11, tid=11, args=None):
    return dict(ph='X', cat=cat, name=name, ts=ts, dur=dur, pid=pid, tid=tid, args=args or {})


class AuditTests(unittest.TestCase):
    def test_negative_chronology_retained_with_exact_index(self):
        a = audit({'traceEvents': [event('cuda_runtime', 'cudaLaunchKernel', args={'correlation': 7, 'External id': 9}), event('kernel', 'test', ts=8, args={'correlation': 7, 'External id': 9})]})
        self.assertEqual(a['negative_chronology_count'], 1)
        self.assertEqual(a['negative_chronology'][0]['gpu']['trace_event_index'], 1)
        self.assertEqual(a['negative_chronology'][0]['gpu_end_minus_cpu_launch_start_us'], -1)
        self.assertTrue(a['negative_chronology'][0]['external_id_present_and_equal'])
        self.assertFalse(a['changed_attribution'])

    def test_duplicate_runtime_and_driver_not_heuristically_disambiguated(self):
        a = audit({'traceEvents': [event('cuda_runtime', 'cudaLaunchKernel', args={'correlation': 7}), event('cuda_driver', 'cuLaunchKernel', args={'correlation': 7}), event('kernel', 'test', ts=8, args={'correlation': 7})]})
        self.assertEqual(a['negative_chronology_count'], 0)
        self.assertEqual(a['gpu_events_without_unique_runtime'][0]['runtime_matches'], 2)

    def test_reused_correlation_across_cpu_processes_is_ambiguous(self):
        a = audit({'traceEvents': [event('cuda_runtime', 'launch', pid=11, args={'correlation': 7}), event('cuda_runtime', 'launch', pid=12, args={'correlation': 7}), event('kernel', 'test', ts=8, args={'correlation': 7})]})
        self.assertEqual(a['gpu_events_without_unique_runtime'][0]['runtime_matches'], 2)

    def test_gpu_annotation_cannot_supply_cpu_parent(self):
        a = audit({'traceEvents': [event('gpu_user_annotation', 'execute_context_0(0)_generation_1(6)', ts=0, dur=20), event('user_annotation', 'avk5.target_forward')]})
        self.assertEqual(len(a['native_ranges']), 0)
        self.assertEqual(a['targets'][0]['native_parent_count'], 0)
        self.assertEqual(a['targets'][0]['outside_native_is_dummy'], 'not established from saved annotations')

    def test_missing_correlation_is_not_joined_to_other_missing_correlation(self):
        a = audit({'traceEvents': [event('cuda_runtime', 'launch'), event('kernel', 'test', ts=8)]})
        self.assertEqual(a['gpu_events_without_unique_runtime'][0]['runtime_matches'], 0)

    def test_conflicting_fields_fail(self):
        with self.assertRaises(ValueError):
            corr({'args': {'correlation': 1, 'correlation_id': 2}})


if __name__ == '__main__':
    unittest.main()
