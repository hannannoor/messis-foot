import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
try:
    from gap_solver.input_contract import write_new_report,protect_report_path
except ImportError:
    write_new_report=protect_report_path=None
from gap_solver.candidate_cli import protect_output


class AuditOutputSafety(unittest.TestCase):
    def test_two_report_writers_cannot_overwrite_each_other(self):
        self.assertIsNotNone(write_new_report,'exclusive report writer missing')
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report.json'
            def attempt(value):
                try:write_new_report(out,{'writer':value},());return True
                except (FileExistsError,ValueError):return False
            with ThreadPoolExecutor(2) as pool:results=list(pool.map(attempt,[1,2]))
            self.assertEqual(sorted(results),[False,True])

    def test_dangling_report_link_is_rejected(self):
        self.assertIsNotNone(write_new_report,'exclusive report writer missing')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'report.json';target=root/'uncreated.json'
            try:out.symlink_to(target)
            except OSError as error:
                if getattr(error,'winerror',None)==1314:self.skipTest('Windows account lacks symlink creation privilege; junction and hardlink cases still run')
                raise
            with self.assertRaises(ValueError):write_new_report(out,{},())
            self.assertFalse(target.exists())

    @unittest.skipUnless(os.name=='nt','Windows junction test')
    def test_junction_ancestor_rejected_without_path_is_junction(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);actual=root/'actual';actual.mkdir();link=root/'junction'
            result=subprocess.run(['cmd','/c','mklink','/J',str(link),str(actual)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            try:
                with self.assertRaises(ValueError):protect_output(link/'candidate',())
                self.assertIsNotNone(protect_report_path,'report path protection missing')
                with self.assertRaises(ValueError):protect_report_path(link/'report.json',())
                python311=Path(r'C:\Users\leonj\anaconda3\envs\football\python.exe')
                if python311.exists():
                    code='import sys;sys.path.insert(0,'+repr(str(Path(__file__).resolve().parents[1]))+');from gap_solver.candidate_cli import protect_output\ntry:protect_output('+repr(str(link/'child'))+',())\nexcept ValueError:sys.exit(0)\nsys.exit(2)'
                    result=subprocess.run([str(python311),'-I','-S','-c',code],capture_output=True,text=True)
                    self.assertEqual(result.returncode,0,result.stderr)
            finally:link.rmdir()  # Remove only the junction entry, never its target.

if __name__=='__main__':unittest.main()
