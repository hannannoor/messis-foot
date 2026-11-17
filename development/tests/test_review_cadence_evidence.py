"""Post-review publication checks, deliberately outside the V2 source globs."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

from cadence_experiment import CaseInput,build_receipt
from cadence_protocol import make_freeze
from cadence_fixtures import moving_fixture

try:
    from postrun_cadence_verify import strict_validate_receipt,strict_json_loads,attest_omitted_sources
except ImportError:
    strict_validate_receipt=strict_json_loads=attest_omitted_sources=None


class ReviewedCadenceEvidence(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(strict_validate_receipt,'post-review evidence verifier is missing')

    def receipt(self,root):
        p=root/'input';p.write_text('synthetic')
        frozen=make_freeze({'source':p},{'fixture':p})
        truth=np.zeros(40,dtype=np.uint8);truth[10:15]=3
        case=CaseInput('skillcorner','1874553',moving_fixture(40,2),truth,np.ones(40,dtype=np.uint8),{'fixture':p})
        return build_receipt(case,'natural',frozen)

    def test_scalar_fields_reject_event_dictionaries_and_named_lists(self):
        with tempfile.TemporaryDirectory() as d:
            value=self.receipt(Path(d));strict_validate_receipt(value)
            for payload in ({str(i):i for i in range(400)},{'cases':[{'index':123},{'index':256}]}):
                changed=copy.deepcopy(value)
                changed['variants']['frozen-control']['boundary_metrics']['12']['mean_latency_frames']=payload
                with self.assertRaises(ValueError):strict_validate_receipt(changed)

    def test_undefined_recall_and_inconsistent_ratios_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            value=self.receipt(Path(d))
            for section,field,new in (('dead_metrics','recall',1.),('metrics','accuracy',.123),('metrics','macro_f1',.123)):
                changed=copy.deepcopy(value);changed['variants']['frozen-control'][section][field]=new
                with self.assertRaises(ValueError):strict_validate_receipt(changed)
            changed=copy.deepcopy(value)
            changed['variants']['frozen-control']['coverage']['active_rows']=True
            with self.assertRaises(ValueError):strict_validate_receipt(changed)

    def test_duplicate_keys_and_nonfinite_json_are_rejected(self):
        for raw in ('{"x":1,"x":2}','{"nested":{"x":1,"x":2}}','{"x":NaN}','{"x":Infinity}'):
            with self.assertRaises(ValueError):strict_json_loads(raw)
        self.assertEqual(strict_json_loads('{"x":1}'),{'x':1})

    def test_omitted_wrapper_identity_rejects_altered_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('accuracy_experiment.py','accuracy_experiment_frozen.py','accuracy_evidence.py','ball_gap_candidate.py'):
                (root/name).write_text('changed source')
            with self.assertRaises(ValueError):attest_omitted_sources(root)


if __name__=='__main__':unittest.main()
