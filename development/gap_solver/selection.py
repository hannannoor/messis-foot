"""Development-only external augmentation and portable export helpers; no challenge inputs."""
from dataclasses import replace
import numpy as np
from .tactical import FEATURE_NAMES


def ball_mask(periods,rate,seed=1729):
    periods=np.asarray(periods)
    if periods.ndim!=1 or not len(periods) or not np.isin(periods,[1,2]).all() or not 0<=rate<=1:
        raise ValueError('invalid external masking request')
    mask=np.zeros(len(periods),dtype=bool)
    target=round(rate*len(periods))
    stops=np.empty(len(periods),dtype=np.int32)
    starts=np.r_[0,np.flatnonzero(periods[1:]!=periods[:-1])+1,len(periods)]
    for first,stop in zip(starts,starts[1:]):
        stops[first:stop]=stop
    rng=np.random.RandomState(seed)
    durations=(5,15,50,125)
    count=0
    while count<target:
        first=int(rng.randint(len(periods)))
        stop=min(int(stops[first]),first+durations[int(rng.randint(len(durations)))])
        candidates=np.flatnonzero(~mask[first:stop])+first
        chosen=candidates[:target-count]
        mask[chosen]=True
        count+=len(chosen)
    return mask


def mask_frames(frames,mask):
    if len(frames)!=len(mask):
        raise ValueError('external observation mask dimensions differ')
    return [replace(f,ball_x=None,ball_y=None,home_distance=None,away_distance=None) if hidden else f
            for f,hidden in zip(frames,mask)]


def export_tree(classifier):
    if list(classifier.classes_)!=[0,1,2] or classifier.n_features_in_!=len(FEATURE_NAMES):
        raise ValueError('external state classifier needs the declared feature schema and H/A/D targets')
    tree=classifier.tree_
    values=tree.value[:,0,:].astype(float)
    values/=values.sum(axis=1,keepdims=True)
    return dict(feature_names=list(FEATURE_NAMES),children_left=tree.children_left.tolist(),
                children_right=tree.children_right.tolist(),feature=tree.feature.tolist(),
                threshold=tree.threshold.tolist(),probabilities=values.tolist())
