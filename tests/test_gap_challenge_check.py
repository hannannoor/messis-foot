"""Synthetic aggregate-only challenge-check contracts; no match inputs."""
import copy
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace as Frame

import gap_challenge_check as check


def frames(periods, observed=None):
    return [Frame(period=p,ball_observed=(observed or [True]*len(periods))[i]) for i,p in enumerate(periods)]


class Aggregates(unittest.TestCase):
    def test_spells_reset_on_owner_dead_unknown_and_period(self):
        result=check.label_summary(frames([0,1,1,1,1,1,1,2,2,0]),tuple('HHHADDHHXX'))
        self.assertEqual(result,dict(graded_frames=8,label_counts=dict(H=4,A=1,D=2,X=1),d_share=.25,spells=4))

    def test_tag_coverage_is_directional_inclusive_and_period_local(self):
        fs=frames([1]*80+[2]*81)
        labels=['H']*len(fs);labels[1]='D';labels[80]='D'
        self.assertEqual(check.tag_coverage(fs,labels,[0,1,76,77,79,80,155,156]),dict(covered=4,total=8,share=4/8))

    def test_set_piece_parser_normalizes_code_and_keeps_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tags.xml'
            p.write_text('<root><instance><code> set  PIECES </code><start>0.04</start></instance><instance><code>SET PIECES</code><start>0.04</start></instance><instance><code>other</code><start>bad</start></instance></root>')
            self.assertEqual(check.tag_starts(p),[1,1])

    def test_invalid_set_piece_time_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tags.xml';p.write_text('<root><instance><code>SET PIECES</code><start>NaN</start></instance></root>')
            with self.assertRaises(ValueError):check.tag_starts(p)

    def test_second_half_interval_is_half_open(self):
        fs=frames([1,0,2,2,2,2],[True,False,False,False,True,False])
        self.assertEqual(check.second_half(fs,tuple('XXHADD'),tuple('XXDDDD')),
            dict(frames=2,observed_ball_found=True,control=dict(H=1,A=1,D=0,X=0),candidate=dict(H=0,A=0,D=2,X=0)))

    def test_second_half_no_ball_stops_at_block_boundary(self):
        fs=frames([2,2,0,2],[False]*4)
        self.assertEqual(check.second_half(fs,tuple('HADX'),tuple('DDXX'))['frames'],2)
        self.assertFalse(check.second_half(fs,tuple('HADX'),tuple('DDXX'))['observed_ball_found'])

    def test_missing_second_half_rejected(self):
        with self.assertRaises(ValueError):check.second_half(frames([0,1]),'XH','XH')

    def test_outside_graded_tag_starts_excluded_not_clipped(self):
        self.assertEqual(check.tag_coverage(frames([0,1,0]),'XDX',[-1,0,1,2,3]),dict(covered=1,total=1,share=1.0))

    def test_invalid_label_and_dimensions_rejected(self):
        for labels in ('H','HZ'):
            with self.assertRaises(ValueError):check.label_summary(frames([1,2]),labels)


class Integrity(unittest.TestCase):
    def sample(self):
        fs=frames([1]*4+[2]*4,[True]*4+[False,False,True,True])
        gap=dict(long_gaps=1,stoppage_gaps=1,live_or_unclassified_gaps=0,long_gap_frames=2,
            stoppage_gap_frames=2,restart_extension_frames=0,frames_relabelled=2,reference_speed_mps=1.5,defined_speed_samples=3)
        return check.aggregate(fs,tuple('HHAAHHAA'),tuple('HHAADDAA'),[5],gap)

    def test_aggregate_contains_only_counts_shares_and_fixed_schema(self):
        result=self.sample();check.validate_aggregate(result)
        self.assertEqual(result['changed_frames'],2)
        self.assertEqual(result['decision'],'Pass challenge self-consistency check')
        for key,value in [('labels',['H']*8),('coordinates',[[0,1]])]:
            changed=copy.deepcopy(result);changed[key]=value
            with self.assertRaises(ValueError):check.validate_aggregate(changed)

    def test_broken_count_reconciliation_rejected(self):
        for field in ('graded_frames','spells'):
            row=self.sample();row['candidate'][field]=-1
            with self.assertRaises(ValueError):check.validate_aggregate(row)
        row=self.sample();row['gap']['stoppage_gaps']=2
        with self.assertRaises(ValueError):check.validate_aggregate(row)


class RunProtocol(unittest.TestCase):
    sample=Integrity.sample
    def run_fixture(self,directory,invalid=False):
        import hashlib
        from gap_liveness import GapApplication
        root=Path(directory);public=root/'public';private=root/'private'
        public.mkdir();private.mkdir()
        check.write_new(public/'freeze.json',{})
        check.write_new(private/'input-map.json',{})
        check.write_new(private/'freeze-identity.json',{})
        fs=frames([1]*4+[2]*4,[True]*4+[False,False,True,True])
        baseline=tuple('HHAAHHAA');candidate=tuple('HHAADDAA')
        summary=Integrity().sample()['gap']
        if invalid:summary['frames_relabelled']=3
        application=GapApplication(candidate,summary,((4,6),),())
        frozen=dict(rows=8,baseline_labels_sha256=hashlib.sha256(''.join(baseline).encode()).hexdigest(),input_sha256=dict(metadata='m',tracking='t',homography='h'))
        paths=dict(metadata='m',tracking='t',homography='h',automatic_tags='tags')
        return root,public,private,fs,baseline,application,frozen,paths

    def test_complete_run_and_read_only_audit_then_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,public,private,fs,baseline,application,frozen,paths=self.run_fixture(d)
            with patch.object(check,'PUBLIC',public),patch.object(check,'PRIVATE',private),patch.object(check,'checked',return_value=(frozen,'commit',paths)),patch('release_runtime.load_source',return_value=(fs,dict(input_sha256=frozen['input_sha256']))) as load,patch('release_runtime.predict_selected',return_value=Frame(labels=baseline)) as predict,patch('gap_liveness.apply_gap_rule',return_value=application) as rule,patch.object(check,'tag_starts',return_value=[5]):
                row=check.run()
                self.assertTrue(check.audit()['verified'])
                self.assertEqual((load.call_count,predict.call_count,rule.call_count),(1,1,1))
                with self.assertRaises(FileExistsError):check.run()
                self.assertEqual(predict.call_count,1)
                altered=copy.deepcopy(row);altered['aggregate']['candidate']['spells']+=1
                (public/'results.json').write_bytes(check.canonical(altered))
                with self.assertRaises(ValueError):check.audit()

    def test_completed_summary_retained_before_count_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root,public,private,fs,baseline,application,frozen,paths=self.run_fixture(d,invalid=True)
            with patch.object(check,'PUBLIC',public),patch.object(check,'PRIVATE',private),patch.object(check,'checked',return_value=(frozen,'commit',paths)),patch('release_runtime.load_source',return_value=(fs,dict(input_sha256=frozen['input_sha256']))),patch('release_runtime.predict_selected',return_value=Frame(labels=baseline)),patch('gap_liveness.apply_gap_rule',return_value=application),patch.object(check,'tag_starts',return_value=[5]):
                with self.assertRaises(ValueError):check.run()
                self.assertTrue((private/'provisional.json').exists())
                self.assertFalse((public/'results.json').exists())

    def test_stop_threshold_is_strict_and_zero_stoppage_stops(self):
        row=self.sample();row['candidate']['label_counts']=dict(H=2,A=1,D=5,X=0);row['candidate']['d_share']=5/8
        self.assertFalse(check.decision(row)['passed'])
        row['candidate']['d_share']=.60;self.assertTrue(check.decision(row)['passed'])
        row['gap']['stoppage_gaps']=0;self.assertFalse(check.decision(row)['passed'])

    def test_change_outside_selected_mask_fails(self):
        with self.assertRaises(ValueError):check.verify_patch('HHH','DHD',[(0,1)],[])
        with self.assertRaises(ValueError):check.verify_patch('HHH','HHH',[(0,1)],[])
        check.verify_patch('HAH','DAD',[(0,1)],[(2,3)])

    def test_exclusive_run_claim_never_restarts(self):
        with tempfile.TemporaryDirectory() as d:
            check.claim(Path(d),'a'*64)
            with self.assertRaises(FileExistsError):check.claim(Path(d),'a'*64)

    def test_public_schema_rejects_nested_traces_and_nonfinite_values(self):
        row=self.sample();row['gap']['trace']=[1,2]
        with self.assertRaises(ValueError):check.validate_aggregate(row)
        row=self.sample();row['gap']['reference_speed_mps']=float('nan')
        with self.assertRaises(ValueError):check.validate_aggregate(row)


if __name__=='__main__':unittest.main()
