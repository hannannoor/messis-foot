"""Export HistGradientBoosting heads (sklearn 1.5.1) to plain numpy arrays."""
import pickle, sys
import numpy as np
src, dst = sys.argv[1], sys.argv[2]
blob = pickle.loads(open(src, 'rb').read())
out = {}
for head, clf in blob['models'].items():
    feats, thr, left, right, leaf, val, mleft, roots = [], [], [], [], [], [], [], []
    off = 0
    for it in clf._predictors:
        nodes = it[0].nodes
        if np.any(nodes['is_categorical']): raise ValueError('categorical split')
        roots.append(off)
        feats.append(nodes['feature_idx'].astype(np.int32)); thr.append(nodes['num_threshold'].astype(np.float64))
        left.append(nodes['left'].astype(np.int64) + off); right.append(nodes['right'].astype(np.int64) + off)
        leaf.append(nodes['is_leaf'].astype(bool)); val.append(nodes['value'].astype(np.float64)); mleft.append(nodes['missing_go_to_left'].astype(bool))
        off += len(nodes)
    out.update({f'{head}_{k}': np.concatenate(v) for k, v in dict(feature=feats, threshold=thr, left=left, right=right, leaf=leaf, value=val, missing_left=mleft).items()})
    out[f'{head}_roots'] = np.asarray(roots, np.int64)
    out[f'{head}_baseline'] = np.asarray(clf._baseline_prediction, np.float64).ravel()
np.savez_compressed(dst, names=np.array(blob['names']), **out)
# self-check against sklearn on a probe matrix
z = np.load(sys.argv[3]); X = z['X'][::97].astype(np.float32)
import importlib.util
spec = importlib.util.spec_from_file_location('rt', 'strong_runtime.py'); rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
m = np.load(dst)
for head, clf in blob['models'].items():
    a = clf.predict_proba(X)[:, 1]; b = rt.gbm_proba(m, head, X)
    print(head, 'max abs diff', float(np.abs(a - b).max()))
