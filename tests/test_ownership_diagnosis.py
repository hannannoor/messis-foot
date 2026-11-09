from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
import numpy as np

from gap_solver.motion import motion_frame
import release_runtime
try:
    import ownership_diagnosis as diagnosis
except ImportError:
    diagnosis=None


def codes(text):return np.asarray(['HADX'.index(value) for value in text],dtype=np.uint8)


class OwnershipDiagnosis(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(diagnosis,'All-state analyzer is missing')

    def trace(self):
        return diagnosis.InferenceTrace(
            emissions=((0.,-20.,-20.),(0.,0.,0.),(-20.,-20.,0.),(-20.,-20.,0.),(-20.,0.,-20.),(-20.,0.,-20.)),
            periods=(1,)*6,observed=(True,False,True,True,True,True),usable=(True,False,True,True,True,True),
            latent=tuple('HXDDAA'),final=tuple('HHDDAA'),raw_codes=(0,0,2,2,1,1),
            memory_owner=(3,)*6,memory_age=(10.,)*6,segments=((0,1),(2,6)),policy_counts={})

    def test_input_only_trace_matches_release_and_unsupported_carry(self):
        home=[(21.,20.),(22.,20.),(23.,20.)];away=[(80.,40.),(81.,40.),(82.,40.)]
        frames=[motion_frame(1,(21.+i*.02,20.),home,away) for i in range(25)]
        frames[10]=replace(frames[10],geometry_valid=False)
        frames += [motion_frame(0,None,home,away)]+[motion_frame(2,None,home,away) for _ in range(6)]
        trace=diagnosis.prepare_inference(frames);released=release_runtime.predict_selected(frames)
        self.assertEqual(trace.latent,released.latent);self.assertEqual(trace.final,released.labels)
        self.assertEqual(trace.latent[-6:],tuple('XXXXXX'))
        self.assertEqual(trace.final[-6:],tuple('DDDDDD'))
        self.assertEqual(trace.final[25],'X')
        self.assertEqual(trace.segments,((0,10),(11,25)))
        with self.assertRaises(ValueError):diagnosis.prepare_inference([replace(frames[0],dead_evidence=True)])

    def test_all_state_episodes_carry_and_reference_mask_isolation(self):
        trace=self.trace();before=trace
        report=diagnosis.analyze_case(trace,codes('DDHAXH'))
        self.assertEqual(report['support']['known'],5)
        self.assertEqual(report['supported_error_frames'],4)
        self.assertEqual(report['carried_error_frames'],1)
        self.assertEqual(report['families']['missed_D']['frames'],1)
        self.assertEqual(report['families']['false_D']['frames'],2)
        self.assertEqual(report['families']['false_D']['episodes'],2)
        self.assertEqual(report['families']['ownership_swap']['frames'],1)
        changed=diagnosis.analyze_case(trace,codes('DDHXXH'))
        self.assertEqual(report['input_path_sha256'],changed['input_path_sha256'])
        self.assertEqual(report['input_segments'],changed['input_segments'])
        self.assertEqual(trace,before)
        self.assertEqual(sum(v['frames'] for v in report['families'].values()),4)

    def test_repairs_have_literal_supported_only_eligibility(self):
        trace=self.trace();repairs=diagnosis.diagnostic_repairs(trace,codes('DDHAXH'))
        self.assertEqual(repairs['supported_liveness_repair'],tuple('DHHAAA'))
        self.assertEqual(repairs['supported_ownership_repair'],tuple('HHDDAH'))
        for labels in repairs.values():
            self.assertEqual(labels[1],'H');self.assertEqual(labels[4],'A')
        self.assertEqual(trace.final,tuple('HHDDAA'))

    def test_spell_split_merge_collision_and_no_overlap_counts(self):
        split=diagnosis.spell_diagnosis(codes('HHHHHH'),codes('HHDHHH'),[1]*6)
        self.assertEqual((split['n_gt'],split['n_pred']),(1,2))
        self.assertEqual(split['split_reference_spells'],1)
        self.assertEqual(split['merge_prediction_spells'],0)
        at=split['per_iou']['0.5'];self.assertEqual((at['n_matched'],at['n_missed'],at['n_spurious']),(1,0,1))
        at=split['per_iou']['0.7'];self.assertEqual((at['n_matched'],at['n_missed'],at['n_spurious']),(0,1,2))
        self.assertEqual(at['unmatched_gt']['below_threshold_overlap'],1)
        merge=diagnosis.spell_diagnosis(codes('HHHDHHH'),codes('HHHHHHH'),[1]*7)
        self.assertEqual(merge['merge_prediction_spells'],1)
        self.assertEqual(merge['per_iou']['0.3']['unmatched_gt']['qualifying_consumed'],1)
        none=diagnosis.spell_diagnosis(codes('HHH'),codes('AAA'),[1]*3)
        self.assertEqual(none['per_iou']['0.5']['unmatched_gt']['no_same_team_overlap'],1)
        for value in (split,merge,none):
            for row in value['per_iou'].values():
                self.assertEqual(row['n_matched']+row['n_missed'],value['n_gt'])
                self.assertEqual(row['n_matched']+row['n_spurious'],value['n_pred'])
                self.assertEqual(sum(row['unmatched_gt'].values()),row['n_missed'])
                self.assertEqual(sum(row['unmatched_pred'].values()),row['n_spurious'])

    def test_unknown_holes_and_periods_do_not_merge_spells(self):
        for gt,pred,periods in ((codes('HHHXHHH'),codes('HHHHHHH'),[1]*7),
                                (codes('HHHHHH'),codes('HHHHHH'),[1]*3+[2]*3)):
            value=diagnosis.spell_diagnosis(gt,pred,periods)
            self.assertEqual((value['n_gt'],value['n_pred']),(2,2))
            self.assertEqual(value['mean_f1'],1.)

    def test_counterfactual_scores_and_zero_support(self):
        trace=self.trace();reference=codes('DDHAXH');report=diagnosis.analyze_case(trace,reference)
        repairs=diagnosis.diagnostic_repairs(trace,reference)
        baseline=diagnosis.spell_diagnosis(reference,codes('HHDDAA'),trace.periods)
        for name,labels in repairs.items():
            expected=diagnosis.spell_diagnosis(reference,codes(labels),trace.periods)
            actual=report['counterfactuals'][name]
            self.assertAlmostEqual(actual['spell_f1_delta'],expected['mean_f1']-baseline['mean_f1'])
        zero=diagnosis.analyze_case(trace,codes('XXXXXX'))
        self.assertEqual(zero['support']['known'],0)
        self.assertIsNone(zero['baseline']['metrics']['accuracy'])
        self.assertIsNone(zero['baseline']['spells']['mean_f1'])
        with self.assertRaises(ValueError):diagnosis.analyze_case(trace,[0,1])

    def constant_trace(self,emission,label,n=120,memory=1):
        return diagnosis.InferenceTrace(emissions=(emission,)*n,periods=(1,)*n,observed=(True,)*n,
            usable=(True,)*n,latent=tuple(label*n),final=tuple(label*n),raw_codes=('HAD'.index(label),)*n,
            memory_owner=(memory,)*n,memory_age=(1.,)*n,segments=((0,n),),policy_counts={})

    def test_observed_interior_emission_and_swap_memory_cross_tabs(self):
        trace=self.constant_trace((0.,1.,0.),'A')
        live=diagnosis.analyze_case(trace,codes('H'*120))
        row=live['strata']['observed_interior_beyond2s']
        self.assertEqual(row['family_emission_evidence']['ownership_swap'],
            dict(frames=20,local_reference_favoring=0,local_wrong_favoring=20,local_near_zero=0))
        self.assertEqual(row['memory_evaluable_ownership_swaps'],20)
        self.assertEqual(row['ownership_swaps_with_opposed_memory'],20)
        dead=diagnosis.analyze_case(trace,codes('D'*120))['strata']['all_known']
        self.assertEqual(dead['ownership_swaps_with_opposed_memory'],0)
        self.assertEqual(dead['memory_evaluable_ownership_swaps'],0)
        self.assertEqual(dead['family_emission_evidence']['missed_D']['local_wrong_favoring'],120)

    def test_legacy_HA_queries_include_false_D_and_agreements_retain_decomposition_ties(self):
        report=diagnosis.analyze_case(self.constant_trace((0.,-1.,1.),'D'),codes('H'*120))
        query=report['legacy_HA_queries']
        self.assertEqual(query['frames'],120);self.assertEqual(query['selected_D_frames'],120)
        # For constant D-preferred emissions, a forced owner can use the whole
        # segment, an end-attached run, or a one-row island. End runs matter.
        def forced_loss(i,loss):return min(120*loss,(i+1)*loss+32,(120-i)*loss+32,loss+64)
        expected=sum(forced_loss(i,1)-forced_loss(i,2) for i in range(120))
        self.assertAlmostEqual(query['margins']['full']['total'],expected)
        agreement=diagnosis.analyze_case(self.constant_trace((1e8,1e8-1e-5,0.),'H',n=1),codes('H'))['agreement']['H']
        self.assertEqual(agreement['numerical_tie_frames'],1)
        for key in ('prefix_before','local','future','full','emission_margin','switch_margin'):
            self.assertEqual(agreement['margins'][key]['n'],1)
        self.assertEqual(agreement['margins']['full']['near_zero'],0)

    def test_all_state_boundary_destination_matching_and_run_separation(self):
        trace=self.trace();gt=codes('HDHAXH')
        report=diagnosis.analyze_case(trace,gt)
        a,b=diagnosis._evaluation(gt,codes('HHDDAA'),trace.periods)
        runs=diagnosis.official.valid_runs(a);filled=diagnosis.official.fill_abstentions(b,runs)
        for tolerance in (12,25):
            expected={k:0 for k in ('n_gt','n_pred','n_matched','n_missed','n_spurious')}
            for run in runs:
                result=diagnosis.official.transition_scores(diagnosis.official.transitions(a,[run]),
                    diagnosis.official.transitions(filled,[run]),tolerance,typed='to')
                for k in expected:expected[k]+=result[k]
            actual=report['all_state_boundaries'][str(tolerance)]
            self.assertEqual({k:actual[k] for k in expected},expected)
            self.assertEqual(actual['matched_latency_denominator'],actual['n_matched'])
            self.assertEqual((actual['n_gt'],actual['n_pred'],actual['n_matched']),(3,1,1))

    def test_all_five_historical_IoUs_and_mean_gate_precede_queries(self):
        trace=self.constant_trace((0.,1.,0.),'A',n=5);reference=codes('AAAAA')
        expected=dict(frames=5,known=5,n_gt=1,n_pred=1,n_matched=1,n_missed=0,n_spurious=0,
            mean_f1=1.,per_iou={str(t):dict(n_matched=1,n_missed=0,n_spurious=0,f1=1.) for t in (.3,.4,.5,.6,.7)})
        diagnosis.analyze_case(trace,reference,expected_parity={'wcsf':expected})
        for kind in ('iou','mean'):
            import copy
            wrong=copy.deepcopy(expected);entries=[]
            if kind=='iou':wrong['per_iou']['0.7']['f1']=.5
            else:wrong['mean_f1']=.5
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                diagnosis.analyze_case(trace,reference,expected_parity={'wcsf':wrong},on_evaluation=entries.append)
            self.assertEqual(entries,['baseline_metric'])


if __name__=='__main__':unittest.main()
