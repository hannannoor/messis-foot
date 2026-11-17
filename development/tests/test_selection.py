import importlib.util
import unittest
import numpy as np
from gap_solver.core import Frame

try:
    from gap_solver.selection import ball_mask,mask_frames,export_tree
except ImportError:
    ball_mask=mask_frames=export_tree=None


class ExternalSelection(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(ball_mask,'external-only masking/export contract is missing')

    def test_mask_is_deterministic_and_tracks_declared_rate(self):
        self.module()
        periods=np.array([1]*500+[2]*500)
        first=ball_mask(periods,.3,1729)
        second=ball_mask(periods,.3,1729)
        np.testing.assert_array_equal(first,second)
        self.assertEqual(int(first.sum()),300)

    def test_mask_changes_observations_without_inserting_labels(self):
        self.module()
        original=[Frame(ball_x=10,ball_y=10,home_distance=.5,away_distance=4)]*10
        changed=mask_frames(original,[True]*5+[False]*5)
        self.assertTrue(all(not f.ball_observed and f.home_distance is None and f.away_distance is None for f in changed[:5]))
        self.assertEqual(changed[5:],original[5:])
        self.assertTrue(original[0].ball_observed)

    @unittest.skipUnless(importlib.util.find_spec('sklearn'),'training-only sklearn unavailable')
    def test_portable_export_matches_training_predictions(self):
        self.module()
        from sklearn.tree import DecisionTreeClassifier
        from gap_solver.tactical import FEATURE_NAMES,PortableTree
        rng=np.random.RandomState(123)
        features=rng.rand(800,len(FEATURE_NAMES)).astype(np.float32)
        target=np.where(features[:,0]<.3,0,np.where(features[:,1]>.5,1,2))
        classifier=DecisionTreeClassifier(max_depth=4,random_state=1729).fit(features,target)
        tree=PortableTree(export_tree(classifier))
        expected=classifier.predict_proba(features)
        actual=np.array([tree.predict(row) for row in features])
        np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-12)


if __name__=='__main__':
    unittest.main()
