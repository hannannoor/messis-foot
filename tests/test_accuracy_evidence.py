import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from gap_solver.accuracy_protocol import PARAMETERS,SPLITS,CONTROLS,select_validation,digest
from gap_solver.temporal_protocol import digest as model_digest
from gap_solver.tactical_model import FROZEN_MODEL
try:
    from accuracy_evidence import portable_require_files,assert_public_report,EvidenceGuard,boundary_summary,engine
except ImportError:
    portable_require_files=assert_public_report=EvidenceGuard=boundary_summary=engine=None


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class EvidenceChecks(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(EvidenceGuard,'strict frozen-evidence entry guard missing')

    def test_portable_file_keys_and_collision_detection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bytes';p.write_bytes(b'abc');expected={'cache\\file.bin':file_hash(p)}
            portable_require_files(expected,{'cache/file.bin':p})
            with self.assertRaises(ValueError):portable_require_files(expected|{'cache/file.bin':file_hash(p)},{'cache/file.bin':p})

    def test_publication_schema_rejects_disguised_or_oversized_arrays(self):
        assert_public_report({'metrics':{'confusion':[[1,0,0,0],[0,2,0,0],[0,0,3,0]]}})
        assert_public_report({'metrics':{'confusion':[[1,0,0,0],[0,2,0,0],[0,0,3,0],[0,0,0,0]]}})
        for value in [{'transitions':[[12,0,1]]},{'ball_xy':[[1,2]]},{'labels':['H','A']},{'unknown':['H','A']},{'confusion':[[0]*4]*100}]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):assert_public_report(value)

    def test_boundary_latency_has_known_units_and_no_event_locations(self):
        import numpy as np
        gt=np.array([0]*30+[1]*30,dtype=np.uint8);pred=np.array([0]*32+[1]*28,dtype=np.uint8)
        result=boundary_summary(gt,pred,np.ones(60,dtype=np.uint8))
        row=result['25']
        self.assertEqual(row['n_matched'],1)
        self.assertEqual(row['mean_abs_latency_frames'],2.)
        self.assertAlmostEqual(row['mean_abs_latency_seconds'],.08)
        assert_public_report(result)


class WarmEvidence(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(EvidenceGuard,'strict frozen-evidence entry guard missing')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.real_root=engine.ROOT;self.real_work=engine.WORK;self.real_reports=engine.REPORTS
        self.addCleanup(self.restore)
        self.root=Path(self.temp.name)/'code';self.root.mkdir();self.work=self.root.parent/'scores';self.reports=self.root/'reports/accuracy-first'
        engine.ROOT=self.root;engine.WORK=self.work;engine.REPORTS=self.reports
        manifest=json.loads((self.real_root/'benchmark/skillcorner/frozen/freeze-manifest.json').read_text())
        for name in [*manifest['source_sha256'],'benchmark/skillcorner/frozen/temporal-selected.json','benchmark/skillcorner/frozen/freeze-manifest.json']:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(self.real_root/name,dest)
        inputs={}
        for stage,cohorts in SPLITS.items():
            for cohort,ids in cohorts.items():
                for match in ids:
                    for suffix in ('.metadata.json','.features.npz','.reference.npz'):
                        prefix=self.root.parent/('external-reference/cache/'+str(match) if cohort=='dfl' else 'independent-reference/cache/'+str(match)+'-detected')
                        p=Path(str(prefix)+suffix);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((cohort+str(match)+suffix).encode())
                    if cohort=='dfl':
                        folder=self.root.parent/'external-reference/raw';folder.mkdir(parents=True,exist_ok=True)
                        for kind in ('matchinformation','positions'):(folder/f'{kind}-{match}.xml').write_text('<synthetic/>')
                    inputs[f'{cohort}-{match}']={k:file_hash(p) for k,p in engine.input_paths(cohort,match).items()}
        core=dict(schema_version=1,split=SPLITS,settings=[dict(id=n,weight=w,switch_cost=c) for n,w,c in PARAMETERS],
            source_sha256={k:file_hash(p) for k,p in engine.source_paths().items()},input_sha256=inputs,
            temporal_artifact_sha256=manifest['artifact_sha256'],tactical_artifact_sha256=FROZEN_MODEL['artifact_sha256'])
        self.reports.mkdir(parents=True);(self.reports/'comparison-freeze.json').write_text(json.dumps(core))
        self.core=core;self.guard=EvidenceGuard()
        self.make_cases('validation')
        rows=self.guard.verified_receipts('validation',core)
        selected=select_validation([r for r in rows if r['regime']=='natural'])
        selected.update(experiment_sha256=digest(core),fresh_holdout=False,
            validation_receipt_sha256={p.name:file_hash(p) for p in (self.reports/'validation').glob('*.json')})
        (self.reports/'selection.json').write_text(json.dumps(selected));self.selected=selected
        self.make_cases('regression',selected)

    def restore(self):engine.ROOT=self.real_root;engine.WORK=self.real_work;engine.REPORTS=self.real_reports

    def make_cases(self,stage,selected=None):
        settings=[n for n,_,_ in PARAMETERS] if stage=='validation' else [selected['selected_id']]
        for cohort,ids in SPLITS[stage].items():
            for match in ids:
                for regime in ('natural','masked'):
                    archive,metadata=engine.case_paths(cohort,match,regime);archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(f'{cohort}{match}{regime}'.encode())
                    ident=engine.identity(self.core,cohort,match,regime);sha=file_hash(archive)
                    metadata.write_text(json.dumps(dict(identity=ident,archive_sha256={'scores':sha},rows=3)))
                    expected=ident|dict(stage=stage,score_archive_sha256=sha,settings=settings)
                    if selected is not None:expected['selection_sha256']=digest(selected)
                    variants={name:{'metrics':{'spell_f1_mean':.6 if name=='w0-c0' else .4,'macro_f1':.5}} for name in (*CONTROLS,*settings)}
                    out=self.reports/stage/f'{cohort}-{match}-{regime}.json';out.parent.mkdir(parents=True,exist_ok=True)
                    out.write_text(json.dumps(dict(identity=expected,cohort=cohort,match=match,regime=regime,stage=stage,variants=variants)))

    def test_self_consistent_replaced_model_does_not_reuse_old_experiment(self):
        self.guard.core();p=self.root/'benchmark/skillcorner/frozen/temporal-selected.json';m=p.with_name('freeze-manifest.json')
        artifact=json.loads(p.read_text());artifact['temperature']*=1.01;p.write_text(json.dumps(artifact));manifest=json.loads(m.read_text());manifest['artifact_sha256']=model_digest(artifact);m.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):self.guard.core()

    def test_selection_parameters_and_decision_are_rederived_not_trusted(self):
        self.assertEqual(self.guard.verified_selection(self.core)['selected_id'],'w0-c0')
        path=self.reports/'selection.json'
        for key,value in [('weight',1.),('switch_cost',32.),('validation_improved',False)]:
            path.write_text(json.dumps(self.selected|{key:value}))
            with self.subTest(key=key):
                with self.assertRaises(ValueError):self.guard.verified_selection(self.core)
        path.write_text(json.dumps(self.selected))

    def test_warm_selection_and_summary_reject_changed_provider_or_archive(self):
        self.guard.verified_summary_inputs(self.core)
        p=self.root.parent/'external-reference/cache/J03WQQ.features.npz';before=p.read_bytes();p.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.guard.verified_selection(self.core)
        p.write_bytes(before)
        archive,_=engine.case_paths('dfl','J03WQQ','natural');before=archive.read_bytes();archive.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.guard.verified_selection(self.core)
        archive.write_bytes(before)
        p=self.root.parent/'independent-reference/cache/2007448-detected.features.npz';p.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.guard.verified_summary_inputs(self.core)

if __name__=='__main__':unittest.main()
