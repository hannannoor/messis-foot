import csv,json,tempfile,unittest,shutil
from pathlib import Path
from test_input_contract import fixture
try:
    import ball_gap_candidate as cli
except ImportError:
    cli=None


def positive_fixture(root):
    meta,raw,quality=fixture(root,500)
    players=[(side+str(i),side) for side in ('h','a') for i in range(3)]
    text='<Match><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height></FieldSize>'
    text+='<Team id="a"><Name>Athletic Club</Name></Team><Team id="h"><Name>Barcelona</Name></Team>'
    text+=''.join(f'<Player id="{p}" teamId="{side}"/>' for p,side in players)
    for channel,name,unit in [('x','position_x','normalized'),('y','position_y','normalized'),('s','speed_kph','kph')]:
        text+=f'<Channel id="{channel}"><Name>{name}</Name><Unit>{unit}</Unit></Channel>'
    text+=''.join(f'<PlayerChannel id="{p}{c}" playerId="{p}" channelId="{c}"/>' for p,_ in players for c in 'xys')
    text+='<DataFormatSpecification startFrame="1" endFrame="500" separator=":"><StringRegister name="frameCount"/><SplitRegister separator=";">'
    for p,_ in players:
        text+='<SplitRegister separator=",">'+''.join(f'<PlayerChannelRef playerChannelId="{p}{c}"/>' for c in 'xys')+'</SplitRegister>'
    text+='</SplitRegister><SplitRegister separator=",">'+''.join(f'<BallChannelRef channelId="{c}"/>' for c in 'xys')+'</SplitRegister></DataFormatSpecification></Match>'
    meta.write_text(text);lines=[]
    positions=';'.join(f'{(.2 if side=="h" else .8)+int(p[1:])*.01},{(.3 if side=="h" else .6)+int(p[1:])*.01},0' for p,side in players)
    for i in range(500):
        if 100<=i<200:ball='nan,nan,nan'
        elif i<300:ball=f'{.2+.0001*(i%10)},.3,0'
        elif i<400:ball=f'{.8+.0001*(i%10)},.6,0'
        else:ball='.5,.5,0'
        lines.append(f'{i+1}:{positions}:{ball}\n')
    raw.write_text(''.join(lines));return meta,raw,quality


class BallGapCandidate(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(cli,'accepted opt-in ball-gap CLI absent')

    def test_positive_HAD_missing_evidence_and_exact_control_outputs_are_reproducible(self):
        import soft_candidate
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=positive_fixture(root)
            first=cli.run_source(*inputs,root/'one',scope='synthetic');second=cli.run_source(*inputs,root/'two',scope='synthetic')
            old=soft_candidate.run_source(*inputs,root/'old',scope='synthetic')
            self.assertEqual(first['csv_sha256'],second['csv_sha256'])
            self.assertEqual(first['setting'],'w0-c32-neutral-missing')
            self.assertFalse(first['target_accuracy_measured']);self.assertEqual(first['policy_diagnostics']['neutral_active_usable_rows'],100)
            for name in ('incumbent','carry','agreement','agreement-plus-carry'):
                self.assertEqual(first['csv_sha256'][name+'.csv'],old['csv_sha256'][name+'.csv'])
            with (root/'one/submission.csv').open(newline='') as h:rows=list(csv.DictReader(h))
            self.assertEqual([int(r['frame']) for r in rows],list(range(500)));self.assertEqual({r['label'] for r in rows},set('HAD'))
            self.assertTrue(all(r['label']=='H' for r in rows[100:200]))
            with (root/'one/uncertainty.csv').open(newline='') as h:rows=list(csv.DictReader(h))
            self.assertTrue(all(r['neutralized']=='1' and r['ball_available']=='0' for r in rows[100:200]))

    def test_both_prior_candidate_generations_and_unowned_outputs_are_preserved(self):
        import soft_candidate
        from gap_solver.candidate_cli import run_source as old_four
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inputs=fixture(root)
            for name,run in [('four',old_four),('soft',soft_candidate.run_source)]:
                out=root/name;run(*inputs,out,scope='synthetic');before={p.name:p.read_bytes() for p in out.iterdir()}
                with self.assertRaises(ValueError):cli.run_source(*inputs,out,scope='synthetic')
                self.assertEqual({p.name:p.read_bytes() for p in out.iterdir()},before)
            out=root/'user';out.mkdir();(out/'keep').write_text('keep')
            with self.assertRaises(ValueError):cli.run_source(*inputs,out,scope='synthetic')
            self.assertEqual((out/'keep').read_text(),'keep')

    def test_changed_policy_or_evidence_cannot_use_selected_artifact(self):
        real=cli.ROOT
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);value,_=cli.selected_artifact();names=set(value['source_sha256'])|set(value['evidence_file_sha256'])|{'benchmark/ball-gap/selected.json'}
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(real/name,p)
            cli.ROOT=root
            try:
                cli.selected_artifact()
                p=root/'ball_gap_policy.py';before=p.read_bytes();p.write_bytes(before+b'\n# changed\n')
                with self.assertRaises(ValueError):cli.selected_artifact()
                p.write_bytes(before);(root/'reports/ball-gap/summary.json').write_text('{}')
                with self.assertRaises(ValueError):cli.selected_artifact()
            finally:cli.ROOT=real

if __name__=='__main__':unittest.main()
