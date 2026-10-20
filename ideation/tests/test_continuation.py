import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from ideation.continuation import ContinuationTools, load_context, prompt_context


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.register = self.root / 'families'
        self.register.mkdir()
        (self.register / 'README.md').write_text(
            '| ID | Hypothesis | Current status | Key local result |\n'
            '| C03 | [Padding](C03.md) | Screen deferred | ITL worsened |\n'
            '| C24 | [AV](C24.md) | Timing pending | No service result |\n')
        (self.register / 'C03.md').write_text('Unfavorable screen; preserve stop.')
        (self.register / 'C24.md').write_text('Diagnostic pending, not a speedup.')
        self.memory = Mock()
        self.memory.ledger.recall.return_value = [{'id': 'old-model-proposal', 'status': 'accepted'}]
        self.tools = ContinuationTools(self.memory)
        self.brief = {'objective': 'Improve H200 latency'}

    def prepare(self, name='first', **kwargs):
        return self.tools.prepare(self.brief, str(self.root / name), str(self.register), **kwargs)['path']

    def test_register_outcomes_survive_incomplete_model_memory(self):
        path = self.prepare()
        context = load_context(path)
        self.assertEqual([x['family_id'] for x in context['families']], ['C03', 'C24'])
        self.assertEqual(context['families'][0]['reported_result'], 'ITL worsened')
        self.assertIn('Timing pending', json.dumps(prompt_context(context)))
        self.assertTrue((Path(path).parent / 'memory.json').is_file())

    def test_original_change_blocks_resume_and_revision_explains_delta(self):
        first = self.prepare()
        (self.register / 'C24.md').write_text('Diagnostic completed, still no service speedup.')
        with self.assertRaisesRegex(ValueError, 'Stale continuation'):
            self.tools.check(first)
        second = self.prepare('second', previous=first)
        context = load_context(second)
        self.assertEqual(context['changes']['modified'], [str(self.register / 'C24.md')])
        frozen = load_context(first, check=False)
        self.assertEqual((Path(first).parent / frozen['inputs'][2]['snapshot']).read_text(), 'Diagnostic pending, not a speedup.')

    def test_frozen_artifact_tampering_is_detected(self):
        path = self.prepare()
        context = load_context(path)
        (Path(path).parent / context['inputs'][1]['snapshot']).write_text('Changed verdict')
        with self.assertRaisesRegex(ValueError, 'snapshot integrity'):
            self.tools.check(path)

    def test_previous_handoff_cannot_be_overwritten(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.prepare()

    def test_reopen_requires_evidence_and_scope_delta(self):
        state = self.root / 'state.json'
        decision = {'family_id': 'C03', 'action': 'reopen', 'reason': 'New rubric'}
        state.write_text(json.dumps({'decisions': [decision]}))
        with self.assertRaisesRegex(ValueError, 'Reopening requires'):
            self.prepare(state=str(state))
        decision.update(new_evidence=['a new component receipt'], scope_delta='AV workload interaction, not the fixed-k5 screen')
        state.write_text(json.dumps({'decisions': [decision]}))
        self.assertTrue(self.tools.check(self.prepare(state=str(state)))['valid'])

    def test_missing_card_or_unknown_family_is_not_silently_omitted(self):
        (self.register / 'C24.md').unlink()
        with self.assertRaisesRegex(ValueError, 'Invalid family-card'):
            self.prepare()

    def test_explicit_evidence_change_invalidates_handoff(self):
        receipt = self.root / 'result.json'
        receipt.write_text('{"state":"pending"}')
        path = self.prepare(artifacts=[str(receipt)])
        receipt.write_text('{"state":"complete"}')
        with self.assertRaisesRegex(ValueError, 'changed input'):
            self.tools.check(path)


if __name__ == '__main__':
    unittest.main()
