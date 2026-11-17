import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np

import cadence_experiment as driver
from cadence_fixtures import moving_fixture
from cadence_protocol import make_freeze,case_keys,digest


class CadenceRun(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(getattr(driver,'summarize_receipts',None),'final run orchestration is not implemented')

    def synthetic_receipts(self,root):
        p=root/'input';p.write_text('synthetic')
        inputs={'fixture':p};frozen=make_freeze({'source':p},inputs)
        case=driver.CaseInput('skillcorner','1874553',moving_fixture(40),np.zeros(40,dtype=np.uint8),np.ones(40,dtype=np.uint8),inputs)
        prototype=driver.build_receipt(case,'natural',frozen)
        rows=[]
        for c,m,r in case_keys():
            row=copy.deepcopy(prototype);row.update(cohort=c,match=m,regime=r);rows.append(row)
        return rows,frozen,inputs

    def test_summary_requires_exact_full_inventory_and_exposes_all_settings(self):
        with tempfile.TemporaryDirectory() as d:
            rows,frozen,inputs=self.synthetic_receipts(Path(d))
            report=driver.summarize_receipts(rows,frozen)
            self.assertEqual(report['cases_scored'],20)
            self.assertEqual(report['variant_scorings'],200)
            self.assertEqual(len(report['by_provider']['skillcorner']['natural']),10)
            self.assertFalse(report['assessment']['automatic_continuation_allowed']) # No D truth in this toy.
            with self.assertRaises(ValueError):driver.summarize_receipts(rows[:-1],frozen)
            rows[-1]=copy.deepcopy(rows[0])
            with self.assertRaises(ValueError):driver.summarize_receipts(rows,frozen)

    def test_immutable_receipt_roundtrip_and_stale_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rows,frozen,inputs=self.synthetic_receipts(root)
            destination=root/'case.json'
            driver.store_receipt(destination,rows[0],frozen,inputs)
            driver.store_receipt(destination,rows[0],frozen,inputs) # Exact resume is harmless.
            changed=copy.deepcopy(rows[0]);changed['experiment_sha256']='0'*64
            with self.assertRaises(ValueError):driver.store_receipt(destination,changed,frozen,inputs)
            self.assertEqual(driver.read_receipt(destination,frozen,inputs),rows[0])
            destination.write_text('{"partial":')
            with self.assertRaises(ValueError):driver.read_receipt(destination,frozen,inputs)

    def test_guarded_receipt_inventory_rejects_extra_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rows,frozen,inputs=self.synthetic_receipts(root)
            cases=root/'cases'
            for row in rows:driver.store_receipt(cases/driver.case_filename(row['cohort'],row['match'],row['regime']),row,frozen,inputs)
            by_case={(c,m):inputs for c,m,_ in case_keys()}
            actual=driver.read_stage(cases,frozen,by_case)
            self.assertEqual(len(actual),20)
            (cases/'unexpected.json').write_text('{}')
            with self.assertRaises(ValueError):driver.read_stage(cases,frozen,by_case)


if __name__=='__main__':unittest.main()
