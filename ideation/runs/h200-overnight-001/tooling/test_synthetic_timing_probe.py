import copy
import unittest
from parse_synthetic_timing_probe import analyze, cross_mode_checks


def fixture():
    return {'traceEvents': [
        dict(ph='X', cat='user_annotation', name='overnight_probe.eager.episode0.iteration0', pid=11, tid=11, ts=100, dur=20),
        dict(ph='X', cat='cuda_runtime', name='cudaLaunchKernel', pid=11, tid=11, ts=105, dur=3, args={'correlation': 7, 'External id': 9}),
        dict(ph='X', cat='kernel', name='unimportant', pid=0, tid=7, ts=106, dur=4, args={'correlation': 7, 'External id': 9, 'device': 0, 'stream': 7}),
    ]}


class ProbeTests(unittest.TestCase):
    def test_known_single_launch_and_union(self):
        a = analyze(fixture(), 'eager', 0, 1)
        self.assertEqual(a['problems'], [])
        self.assertEqual(a['scope_summaries'][0]['gpu_activity_union_us'], 4)

    def test_duplicate_candidate_fails(self):
        f = fixture()
        f['traceEvents'].append(copy.deepcopy(f['traceEvents'][1]))
        a = analyze(f, 'eager', 0, 1)
        self.assertIn('missing_or_ambiguous_runtime_association', a['problems'])
        self.assertIn('required_scope_without_gpu_work', a['problems'])

    def test_removed_launch_fails(self):
        f = fixture()
        f['traceEvents'].pop(1)
        self.assertIn('missing_or_ambiguous_runtime_association', analyze(f, 'eager', 0, 1)['problems'])

    def test_gpu_mirror_cannot_supply_parent(self):
        f = fixture()
        f['traceEvents'][0]['cat'] = 'gpu_user_annotation'
        self.assertIn('scope_count_or_identity_mismatch', analyze(f, 'eager', 0, 1)['problems'])

    def test_negative_chronology_reported_without_shift(self):
        f = fixture()
        f['traceEvents'][2]['ts'] = 99
        a = analyze(f, 'eager', 0, 1)
        self.assertEqual(a['negative_end_before_cpu_start_count'], 1)
        self.assertEqual(a['associations'][0]['gpu_end_minus_cpu_start_us'], -2)
        self.assertFalse(a['clock_correction_applied'])

    def test_conflicting_external_identifier_fails(self):
        f = fixture()
        f['traceEvents'][2]['args']['External id'] = 10
        self.assertIn('conflicting_external_ids', analyze(f, 'eager', 0, 1)['problems'])

    def test_graph_scope_requires_linked_graph_launch(self):
        f = fixture()
        f['traceEvents'][0]['name'] = 'overnight_probe.graph_single.episode0.iteration0'
        self.assertIn('graph_scope_without_exactly_one_graph_launch', analyze(f, 'graph_single', 0, 1)['problems'])
        f['traceEvents'][1]['name'] = 'cudaGraphLaunch'
        self.assertEqual(analyze(f, 'graph_single', 0, 1)['problems'], [])

    def test_missing_graph_node_detected_by_cross_mode_multiplicity(self):
        episodes = []
        for mode, n in [('graph_single', 1), ('graph_eight', 8)]:
            f = fixture(); f['traceEvents'][0]['name'] = f'overnight_probe.{mode}.episode0.iteration0'
            f['traceEvents'][1]['name'] = 'cudaGraphLaunch'
            f['traceEvents'][2]['args'].update({'graph id': 4, 'graph node id': 1})
            for i in range(1, n):
                k = copy.deepcopy(f['traceEvents'][2]); k['args']['graph node id'] = i + 1
                f['traceEvents'].append(k)
            episodes.append({'mode': mode, 'analysis': analyze(f, mode, 0, 1)})
        self.assertEqual(cross_mode_checks(episodes)['problems'], [])
        episodes[1]['analysis']['associations'].pop()
        self.assertIn('graph_eight_kernel_multiplicity_not_eightfold', cross_mode_checks(episodes)['problems'])

    def test_overlap_union_is_not_sum(self):
        f = fixture()
        e = copy.deepcopy(f['traceEvents'][2]); e['ts'] = 108
        f['traceEvents'].append(e)
        self.assertEqual(analyze(f, 'eager', 0, 1)['scope_summaries'][0]['gpu_activity_union_us'], 6)


if __name__ == '__main__':
    unittest.main()
