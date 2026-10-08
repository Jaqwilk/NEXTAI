"""Existing frozen-source/target models with preregistered native confidence and DTW."""
import numpy as np
import torch
from torch.nn import functional as F

from .har01_core import Candidate as NativeReference, Session as NativeSession, unit, rbf


def banded_dtw_scores(keys,observation):
    paths=keys.reshape(-1,32,2).astype(np.float64)
    query=observation.reshape(32,2).astype(np.float64)
    local=32*np.sum((paths[:,:,None,:]-query[None,None,:,:])**2,axis=-1)
    count=len(paths)
    costs=np.full((count,33,33),np.inf);lengths=np.zeros((count,33,33),dtype=np.int16)
    costs[:,0,0]=0.;rows=np.arange(count)
    for i in range(1,33):
        for j in range(max(1,i-4),min(32,i+4)+1):
            previous=np.column_stack((costs[:,i-1,j-1],costs[:,i-1,j],costs[:,i,j-1]))
            route=np.argmin(previous,axis=1)
            costs[:,i,j]=previous[rows,route]+local[:,i-1,j-1]
            prior_lengths=np.column_stack((lengths[:,i-1,j-1],lengths[:,i-1,j],lengths[:,i,j-1]))
            lengths[:,i,j]=prior_lengths[rows,route]+1
    distances=costs[:,32,32]/lengths[:,32,32]
    return 1/(1+distances)


class Candidate(NativeReference):
    def __init__(self,seed,arm,recipe,source_arrays=None):
        if arm=='native_shift':
            raise ValueError('HAR temporal shift is not an ASM arm')
        super().__init__(seed,'native_raw' if arm=='native_dtw' else arm,recipe,source_arrays)
        self.route,self.arm=arm,arm
        self.margin_threshold=0.

    def new_session(self,size):
        return Session(self,size)

    def calibrate(self,legal_episodes):
        samples=[]
        for writes,queries,labels in legal_episodes:
            session=self.new_session(len({row[1] for row in writes}))
            for row in writes:
                session.ingest(row)
            for query,(truth,target_source) in zip(queries,labels,strict=True):
                handle,score,margin,value=session.ranked(query)
                if not np.isfinite((score,margin)).all():
                    raise ValueError('Nonfinite ASM calibration confidence')
                samples.append((score,margin,value,session.sources[handle],truth,target_source))
        scores=np.asarray([row[0] for row in samples]);margins=np.asarray([row[1] for row in samples])
        known=np.asarray([row[4]!=-1 for row in samples]);absent=~known
        correct=np.asarray([(row[2],row[3])==(row[4],row[5]) for row in samples])
        choices=[]
        for threshold in self.recipe['threshold_grid']:
            for margin in self.recipe['margin_grid']:
                accepted=(scores>=threshold)&(margins>=margin)
                choices.append(dict(threshold=threshold,margin_threshold=margin,
                                    accuracy=float(np.mean((accepted&correct)|(~accepted&absent))),
                                    known_false_abstention=float(np.mean(~accepted[known])),
                                    absent_rejection=float(np.mean(~accepted[absent]))))
        eligible=[choice for choice in choices if choice['known_false_abstention']<=.02 and choice['absent_rejection']>=.95]
        selected=max(eligible or choices,key=lambda row:(row['accuracy'],row['absent_rejection'],-row['threshold'],-row['margin_threshold']))
        self.threshold,self.margin_threshold=selected['threshold'],selected['margin_threshold']
        self.report.update(calibration_grid=choices,calibration_choice=selected,calibration_feasible=bool(eligible),
                           calibration_answer_semantics='current value AND source; UNKNOWN-1/None; train-only absolute score AND top2 margin')


class Session(NativeSession):
    def ranked(self,observation):
        if observation.shape!=(64,) or observation.dtype!=np.float32 or not np.isfinite(observation).all():
            raise ValueError('ASM query only finite64 public coordinates')
        system=self.system
        if self.cached is not None:
            with torch.inference_mode():
                embedded=F.normalize(system.model(torch.as_tensor(observation,device=system.device)),dim=-1)
                decoded=self.cached.decoded(embedded)
                cosine=(self.cached.keys[:len(self.cached.handles)]@decoded).numpy()
            scores=(1+np.clip(cosine,-1,1))/2
            handles=self.cached.handles;values=self.cached.labels
        else:
            if system.route.startswith('source_'):
                features=system.source_features(observation[None])[0]
                projected=features@system.adapter[:-1]+system.adapter[-1]
            elif system.route=='target_kernel':
                features=rbf(observation[None],system.landmarks,system.bandwidth)[0]
                projected=features@system.weights[:-1]+system.weights[-1]
            elif system.route=='target_ridge_pca':
                projected=(observation@system.weights[:-1]+system.weights[-1])@system.projection
            else:
                projected=observation
            keys=self.keys[:len(self.handles)]
            scores=(banded_dtw_scores(keys,observation) if system.route=='native_dtw'
                    else (1+np.clip(keys@unit(projected),-1,1))/2)
            handles=self.handles;values=self.values
        if len(scores)<2:
            raise ValueError('ASM top2 confidence needs at least two legal memory entries')
        first=int(np.argmax(scores));second=float(np.partition(scores,-2)[-2])
        return handles[first],float(scores[first]),float(scores[first]-second),int(values[first])

    def read(self,observation):
        handle,score,_,value=self.ranked(observation)
        return handle,score,value

    def answer(self,observation):
        handle,score,margin,value=self.ranked(observation)
        accepted=score>=self.system.threshold and margin>=self.system.margin_threshold
        return value if accepted else -1,handle,score,value,self.sources[handle] if accepted else None
