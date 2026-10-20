import copy
import unittest
from test_timing_tools import load, fixture

v1 = load('trace_summary')
v2 = load('trace_summary_v2')

class ActualKinetoSchemaTests(unittest.TestCase):
    def test_mirrored_gpu_annotations_are_not_cpu_launch_parents(self):
        original = fixture()
        mirrored = copy.deepcopy(original)
        for event in original['traceEvents']:
            if event['cat'] == 'user_annotation':
                gpu_annotation = copy.deepcopy(event)
                gpu_annotation.update(cat='gpu_user_annotation', pid=0, tid=19)
                mirrored['traceEvents'].append(gpu_annotation)
        before = v1.summarize(mirrored)
        self.assertIn('scope_process_identity_not_unique', before['adequacy_problems'])
        self.assertGreater(before['scope_counts']['avk5.target_forward'], 11)
        expected = v2.summarize(original)
        actual = v2.summarize(mirrored)
        self.assertEqual(actual, expected)
        self.assertTrue(actual['descriptive_occupied_time_adequate'])
        self.assertEqual(actual['scope_process_ids'], ['40'])
        self.assertEqual(actual['native_execute_range_count'], 11)
        self.assertEqual(len(actual['complete_eligible_decode_cycles']), 10)
        self.assertEqual(actual['devices'][0]['all_activity_union_us'], 440)

    def test_gpu_only_annotation_cannot_supply_missing_cpu_scope(self):
        trace = fixture()
        for event in trace['traceEvents']:
            if event['cat'] == 'user_annotation':
                event.update(cat='gpu_user_annotation', pid=0, tid=19)
        result = v2.summarize(trace)
        self.assertFalse(result['descriptive_occupied_time_adequate'])
        self.assertEqual(result['scope_counts'], {})
        self.assertEqual(result['native_execute_range_count'], 0)
        self.assertEqual(result['complete_eligible_decode_cycles'], [])

if __name__ == '__main__':
    unittest.main()
