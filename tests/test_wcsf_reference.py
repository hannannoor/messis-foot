"""Reference consensus never feeds clocks, quality or inference."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
from wcsf_fixtures import rows,source_paths
from wcsf_source import ingest


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        try:import wcsf_reference
        except ImportError:self.fail('Missing separate reference contract')
        self.api=wcsf_reference;self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def reference(self,name,data,index,second=None):
        paths=source_paths(self.root/name,data,rows(6) if second is None else second);ingest(paths)
        return self.api.reference_codes(paths.reference_db,index)

    def test_dead_consensus_ignores_owner_disagreement(self):
        data=rows(1)
        for i,r in enumerate(data):r.update(AliveFlag=0,PossessionFlag=('invalid',1,2)[i%3])
        np.testing.assert_array_equal(self.reference('dead',data,[(1,0)]),[2])

    def test_alive_owner_conflict_missing_invalid_are_X(self):
        for i,change in enumerate(({'PossessionFlag':2},{'PossessionFlag':''},{'PossessionFlag':0},{'AliveFlag':0},{'AliveFlag':''},{'AliveFlag':2})):
            data=rows(1);data[0].update(change)
            np.testing.assert_array_equal(self.reference(str(i),data,[(1,0)]),[3])

    def test_conflicting_duplicate_reference_is_X_independent_of_row_order(self):
        data=rows(1);data.append(dict(data[0],PossessionFlag=2))
        for name,items in [('normal',data),('reverse',list(reversed(data)))]:
            np.testing.assert_array_equal(self.reference(name,items,[(1,0)]),[3])

    def test_exact_native_before_gap_preserved_but_intermediate_gap_X(self):
        data=[r for r in rows(6) if r['timestamp_ms'] not in (300,400)]
        for r in data:
            t=r['timestamp_ms'];r['AliveFlag']=0 if t==200 else 1;r['PossessionFlag']=2 if t==100 else 1
        times=[0,40,100,200,240,280,320,360,400,440,480,500]
        np.testing.assert_array_equal(self.reference('gap',data,[(1,t) for t in times]),[0,0,1,2,3,3,3,3,3,3,3,0])

    def test_left_interval_mapping_and_missing_native_gap(self):
        data=rows(3)
        for r in data:r['PossessionFlag']=1 if r['timestamp_ms']==0 else 2
        np.testing.assert_array_equal(self.reference('mapping',data,[(1,t) for t in (0,40,80,120,160,200,240)]),[0,0,0,1,1,1,3])

    def test_periods_are_archive_roles_not_reference(self):
        first=rows(3);second=rows(3)
        for r in second:r.update(AliveFlag=0,PossessionFlag=0)
        np.testing.assert_array_equal(self.reference('halves',first,[(1,0),(2,0),(1,80),(2,80)],second),[0,2,0,2])


if __name__=='__main__':unittest.main()
