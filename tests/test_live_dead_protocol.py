"""Live/dead sequence experiment: protocol constants and deadline. Synthetic only."""
from datetime import datetime, timedelta
import unittest

import live_dead_protocol as lp


class ProtocolTest(unittest.TestCase):
    def test_deadline_is_start_plus_24h(self):
        self.assertEqual(datetime.fromisoformat(lp.DEADLINE_LOCAL) - datetime.fromisoformat(lp.START_LOCAL),
                         timedelta(hours=24))

    def test_enforce_deadline_raises_after(self):
        with self.assertRaisesRegex(ValueError, 'deadline'):
            lp.enforce_deadline(datetime.fromisoformat(lp.DEADLINE_LOCAL) + timedelta(seconds=1))
        lp.enforce_deadline(datetime.fromisoformat(lp.DEADLINE_LOCAL) - timedelta(seconds=1))

    def test_enforce_deadline_rejects_naive_time(self):
        with self.assertRaises(ValueError):
            lp.enforce_deadline(datetime(2026, 11, 14, 16, 0))

    def test_cases_are_13_primary_2_secondary(self):
        self.assertEqual(len(lp.PRIMARY), 13)
        self.assertEqual(lp.SECONDARY, ('dfl-J03WOH', 'dfl-J03WOY'))
        self.assertFalse(set(lp.PRIMARY) & set(lp.SECONDARY))
        self.assertEqual({lp.provider_of(c) for c in lp.PRIMARY}, {'skillcorner', 'dfl', 'wcsf'})
        self.assertEqual(sum(lp.provider_of(c) == 'skillcorner' for c in lp.PRIMARY), 10)

    def test_frozen_model_digest(self):
        from memory_ablation import MODEL_SHA
        from memory_ablation_training import model_digest
        self.assertEqual(model_digest(lp.load_frozen_model()), MODEL_SHA)


if __name__ == '__main__':
    unittest.main()
