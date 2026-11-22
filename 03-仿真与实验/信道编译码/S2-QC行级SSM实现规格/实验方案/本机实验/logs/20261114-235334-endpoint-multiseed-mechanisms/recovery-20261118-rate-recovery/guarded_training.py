"""Checks-only device adapter for subsequent frozen mechanism training."""
from pathlib import Path
import hashlib,json,os,runpy,sys
import numpy as np
import torch
HERE=Path(__file__).resolve().parent;LOG=HERE.parent;LOCAL=LOG.parent.parent
sys.path.insert(0,str(LOCAL));sys.path.insert(0,str(LOG/'code'))
import formal_core as core
from nr_link import NRLink
_arrays=core.channel_arrays
_channel=NRLink.channel
_cpu={}
_counts={'training_batches':0,'channel_shards':0}
def cpu_link(link):
    if link.cfg['id'] not in _cpu:_cpu[link.cfg['id']]=NRLink(link.cfg,device='cpu')
    return _cpu[link.cfg['id']]
def exact(actual,expected,context,bitwise=True):
    a=actual.detach().cpu().numpy();b=expected.detach().cpu().numpy()
    # Per-frame training SNR uses vector sqrt: CPU SIMD and CUDA differ by
    # up to ~2e-6. Apply the existing check_channel.py absolute1e-5 criterion.
    # Scalar-SNR validation/test retain strict bitwise comparison.
    equal=np.array_equal(a.view(np.uint32),b.view(np.uint32)) if bitwise else bool(np.max(np.abs(a-b))<1e-5)
    if not np.isfinite(a).all() or not np.isfinite(b).all() or not equal:
        p=HERE/f'training-channel-failure-{os.getpid()}.npz'
        np.savez_compressed(p,actual=a,expected=b)
        raise AssertionError(('CPU/CUDA channel disagreement',context,str(p)))
def arrays(link,payload,noise,snrs):
    result=_arrays(link,payload,noise,snrs)
    reference=_arrays(cpu_link(link),payload,noise,snrs)
    assert np.array_equal(result[0],reference[0]) and np.array_equal(result[1],reference[1])
    exact(result[2],reference[2],{'kind':'training','config':link.cfg['id']},bitwise=False)
    _counts['training_batches']+=1
    if _counts['training_batches']%1000==0:print(json.dumps({'event':'cpu_input_guard_counts',**_counts}),flush=True)
    return result
def channel(link,codeword,ebn0_db,rng,noiseless=False):
    if link.device.type=='cpu':return _channel(link,codeword,ebn0_db,rng,noiseless)
    import copy
    reference_rng=copy.deepcopy(rng)
    result=_channel(link,codeword,ebn0_db,rng,noiseless)
    reference=_channel(cpu_link(link),codeword,ebn0_db,reference_rng,noiseless)
    exact(result[0],reference[0],{'kind':'validation','config':link.cfg['id']})
    exact(result[1],reference[1],{'kind':'raw_validation','config':link.cfg['id']})
    _counts['channel_shards']+=1
    return result

core.channel_arrays=arrays
NRLink.channel=channel
print(json.dumps({'event':'external_training_input_guard','path':str(Path(__file__).resolve()),
    'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'gpu_uuid':os.environ.get('CUDA_VISIBLE_DEVICES'),'frozen_sources_unchanged':True,'checks_only':True}),flush=True)
if __name__=='__main__':runpy.run_path(str(LOG/'launch_train_mechanism.py'),run_name='__main__')
