import unittest
from control_trace import Guard, ControlMissing


class GuardTests(unittest.TestCase):
    def test_happy_path(self):
        g = Guard(['validate', 'review'])
        self.assertEqual(g.run('validate', lambda: 4), 4)
        g.run('review', lambda: True)
        self.assertEqual(g.finalize({'ok': True}), {'ok': True})
        self.assertEqual(g.state, 'PUBLISHED')

    def test_missing_blocks(self):
        g = Guard(['validate', 'review'])
        g.run('validate', lambda: None)
        with self.assertRaises(ControlMissing) as err:
            g.finalize('result')
        self.assertEqual(err.exception.missing, ['review'])

    def test_failed_function_no_receipt(self):
        g = Guard(['validate'])
        def fail():
            raise RuntimeError('failed')
        with self.assertRaises(RuntimeError):
            g.run('validate', fail)
        self.assertEqual(g.trace(), [])

    def test_retry_isolated(self):
        g = Guard(['validate'])
        g.run('validate', lambda: True)
        self.assertEqual(g.retry_or_hold(), 'RETRY')
        with self.assertRaises(ControlMissing):
            g.finalize('artifact')
        g.run('validate', lambda: True)
        self.assertEqual(g.finalize('artifact'), 'artifact')

    def test_second_retry_holds(self):
        g = Guard(['validate'])
        self.assertEqual(g.retry_or_hold(), 'RETRY')
        self.assertEqual(g.retry_or_hold(), 'HOLD')
        self.assertEqual(len(g.alerts), 1)
        with self.assertRaises(RuntimeError):
            g.finalize('artifact')

    def test_invalid_control(self):
        g = Guard(['validate'])
        with self.assertRaises(ValueError):
            g.run('unknown', lambda: True)

    def test_duplicate_required(self):
        with self.assertRaises(ValueError):
            Guard(['a', 'a'])

    def test_unique_event_ids(self):
        g = Guard(['validate'])
        g.run('validate', lambda: True)
        g.run('validate', lambda: True)
        self.assertNotEqual(g.trace()[0]['event_id'], g.trace()[1]['event_id'])

    def test_closed_after_publish(self):
        g = Guard(['validate'])
        g.run('validate', lambda: True)
        g.finalize('done')
        with self.assertRaises(ValueError):
            g.run('validate', lambda: True)

    def test_revision_in_contract(self):
        a = Guard(['validate'], revision='r1')
        b = Guard(['validate'], revision='r2')
        self.assertNotEqual(a.contract_digest, b.contract_digest)

    def test_attempt_changes_while_running(self):
        g = Guard(['validate'])
        def change():
            g.retry_or_hold()
            return True
        with self.assertRaises(RuntimeError):
            g.run('validate', change)
        self.assertEqual(g.trace(), [])


if __name__ == '__main__':
    unittest.main()
