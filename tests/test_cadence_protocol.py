import copy
import json
from pathlib import Path
import tempfile
import unittest

try:
    from cadence_protocol import case_keys,protocol,validate_protocol,make_freeze,validate_freeze,write_new
except ImportError:
    case_keys=protocol=validate_protocol=make_freeze=validate_freeze=write_new=None


class CadenceProtocol(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(protocol,'cadence protocol is not implemented')

    def test_exact_four_cases_five_regimes_ten_variants(self):
        keys=case_keys()
        self.assertEqual(len(keys),20)
        self.assertEqual(len(set(keys)),20)
        self.assertEqual({(c,m) for c,m,_ in keys},{('skillcorner','1874553'),('skillcorner','1886347'),('dfl','J03WOH'),('dfl','J03WOY')})
        self.assertEqual(len(protocol()['variants']),10)
        self.assertEqual(protocol()['max_aggregate_scorings'],200)

    def test_horizon_window_and_seed_cannot_be_reselected(self):
        for name,value in (('max_gap_s',.3),('mask_seed',1),('switch_cost',8)):
            altered=copy.deepcopy(protocol());altered[name]=value
            with self.assertRaises(ValueError):validate_protocol(altered)
        altered=copy.deepcopy(protocol());altered['variants']['official-convention-w7']={}
        with self.assertRaises(ValueError):validate_protocol(altered)

    def test_source_input_and_protocol_are_bound(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'a.py';data=root/'a.bin'
            source.write_text('v=1');data.write_bytes(b'synthetic input')
            sources={'a.py':source};inputs={'a.bin':data}
            frozen=make_freeze(sources,inputs)
            validate_freeze(frozen,sources,inputs)
            source.write_text('v=2')
            with self.assertRaises(ValueError):validate_freeze(frozen,sources,inputs)
            source.write_text('v=1');data.write_bytes(b'changed input')
            with self.assertRaises(ValueError):validate_freeze(frozen,sources,inputs)

    def test_omitted_source_inventory_does_not_attest_itself(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/'a';b=root/'b';a.write_text('a');b.write_text('b')
            frozen=make_freeze({'a':a,'b':b},{'input':a})
            del frozen['source_sha256']['b']
            with self.assertRaises(ValueError):validate_freeze(frozen,{'a':a,'b':b},{'input':a})

    def test_unknown_fields_and_disguised_arrays_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_text('x');base=make_freeze({'source':p},{'input':p})
            for extra in ({'surprise':1},{'event_ids':[1,2,3]},{'frames':[1,2,3]}):
                altered=copy.deepcopy(base);altered.update(extra)
                with self.assertRaises(ValueError):validate_freeze(altered,{'source':p},{'input':p})

    def test_no_clobber_and_input_alias(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'input';p.write_text('keep')
            frozen=make_freeze({'source':p},{'input':p})
            out=root/'out.json';write_new(out,frozen,[p])
            self.assertEqual(json.loads(out.read_text()),frozen)
            with self.assertRaises(FileExistsError):write_new(out,frozen,[p])
            with self.assertRaises(ValueError):write_new(p,frozen,[p])
            self.assertEqual(p.read_text(),'keep')


if __name__=='__main__':unittest.main()
