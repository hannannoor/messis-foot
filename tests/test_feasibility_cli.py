import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'inspect_temporal_feasibility.py'


class FeasibilityCLI(unittest.TestCase):
    def execute(self,*args):return subprocess.run([sys.executable,'-I','-S',str(SCRIPT),*map(str,args)],capture_output=True,text=True)

    def test_published_artifact_and_strict_exit_without_input_mutation(self):
        source=ROOT/'benchmark/skillcorner/frozen/temporal-selected.json';before=hashlib.sha256(source.read_bytes()).hexdigest()
        result=self.execute(source,'--fail-on-impossible')
        self.assertEqual(result.returncode,1,result.stderr)
        data=json.loads(result.stdout);self.assertEqual(data['provably_impossible_policies'],1)
        self.assertEqual(data['policies'][0]['status'],'provably_impossible')
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)

    def test_fixed_draft_grid_exposes_all_27_impossible_policies(self):
        result=self.execute(ROOT/'benchmark/skillcorner/trained-draft.json','--grid')
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout);self.assertEqual(len(data['policies']),27)
        self.assertEqual(data['provably_impossible_policies'],27)

    def test_malformed_json_model_and_nonstandard_nan_return_json_errors(self):
        for text in ('{','{}','{"schema_version":1,"model":NaN}'):
            with tempfile.TemporaryDirectory() as d:
                source=Path(d)/'bad.json';source.write_text(text)
                result=self.execute(source)
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertIn('error',json.loads(result.stdout))
                self.assertNotIn('Traceback',result.stderr)

    def test_isolated_stdlib_execution_does_not_import_training_packages(self):
        command="import runpy,sys;sys.argv="+repr([str(SCRIPT),str(ROOT/'benchmark/skillcorner/frozen/temporal-selected.json')])+"\ntry:runpy.run_path(sys.argv[0],run_name='__main__')\nfinally:assert not any(n in sys.modules for n in ('numpy','pandas','sklearn','scipy'))"
        result=subprocess.run([sys.executable,'-I','-S','-c',command],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['provably_impossible_policies'],1)
