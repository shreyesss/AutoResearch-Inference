import copy
import unittest
from parse_short_operation_probe import MODES, analyze


def fixture():
    events = []
    for i, mode in enumerate(MODES):
        start = 100 * i
        events.append(dict(ph='X', cat='user_annotation', name=f'overnight_short.epoch0.{mode}.iteration0', pid=11, tid=11, ts=start, dur=20))
        events.append(dict(ph='X', cat='cuda_runtime', name='cudaGraphLaunch' if mode.startswith('graph') else 'ordinary launch', pid=11, tid=11, ts=start + 5, dur=3, args={'correlation': i + 1, 'External id': i + 10}))
        events.append(dict(ph='X', cat='gpu_memcpy' if mode.endswith('copy') else 'kernel', name='irrelevant to attribution', pid=0, tid=7, ts=start + 6, dur=1, args={'correlation': i + 1, 'External id': i + 10, 'device': 0, 'stream': 7, 'graph id': 8 if mode.startswith('graph') else 0, 'graph node id': 9 if mode.startswith('graph') else 0}))
    return {'traceEvents': events}


class ShortProbeTests(unittest.TestCase):
    def test_complete_explicit_inventory(self):
        a = analyze(fixture(), epochs=1, iterations=1)
        self.assertEqual(a['problems'], [])
        self.assertEqual(a['scope_count'], 4)

    def test_duplicate_runtime_rejected(self):
        f = fixture(); f['traceEvents'].append(copy.deepcopy(f['traceEvents'][1]))
        self.assertIn('missing_or_ambiguous_runtime_association', analyze(f, 1, 1)['problems'])

    def test_missing_runtime_rejected(self):
        f = fixture(); f['traceEvents'].pop(1)
        self.assertIn('missing_or_ambiguous_runtime_association', analyze(f, 1, 1)['problems'])

    def test_gpu_mirror_not_cpu_parent(self):
        f = fixture(); f['traceEvents'][0]['cat'] = 'gpu_user_annotation'
        self.assertIn('incorrect_scope_inventory', analyze(f, 1, 1)['problems'])

    def test_conflicting_external_id_rejected(self):
        f = fixture(); f['traceEvents'][2]['args']['External id'] = 999
        self.assertIn('conflicting_external_ids', analyze(f, 1, 1)['problems'])

    def test_missing_activity_rejected(self):
        f = fixture(); f['traceEvents'].pop(2)
        self.assertIn('required_scope_without_gpu_activity', analyze(f, 1, 1)['problems'])

    def test_dropped_iteration_rejected(self):
        f = fixture(); f['traceEvents'] = f['traceEvents'][3:]
        self.assertIn('incorrect_scope_inventory', analyze(f, 1, 1)['problems'])

    def test_negative_chronology_retained(self):
        f = fixture(); f['traceEvents'][2]['ts'] = 3
        a = analyze(f, 1, 1)
        self.assertEqual(a['negative_end_before_cpu_start_count'], 1)
        self.assertFalse(a['clock_correction_applied'])

    def test_graph_metadata_absence_retained(self):
        f = fixture(); del f['traceEvents'][5]['args']['graph node id']
        a = analyze(f, 1, 1)
        self.assertEqual(a['graph_activities_without_graph_node_metadata'], [5])
        self.assertFalse(a['complete_graph_node_accounting_qualified'])


if __name__ == '__main__': unittest.main()
