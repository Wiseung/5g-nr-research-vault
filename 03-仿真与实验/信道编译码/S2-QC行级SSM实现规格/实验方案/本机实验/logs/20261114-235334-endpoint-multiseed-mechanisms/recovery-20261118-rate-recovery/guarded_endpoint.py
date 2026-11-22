"""External fail-closed input checks; executes the frozen endpoint unchanged."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
import torch
HERE=Path(__file__).resolve().parent;LOG=HERE.parent
sys.path.insert(0,str(LOG/'code'))
import endpoint as e

_original_sample=e.sample
_cpu_links={}
def guarded_sample(link,split,snr,shard,n):
    payload,info,lch,digest=_original_sample(link,split,snr,shard,n)
    key=link.cfg['id']
    if key not in _cpu_links:_cpu_links[key]=e.NRLink(link.cfg,device='cpu')
    cpu=_cpu_links[key]
    cw,expected_info=cpu.encode(payload)
    noise=np.random.default_rng(e.stable_seed(key,snr,shard,split+'/noise'))
    expected,_=cpu.channel(cw,float(snr),noise)
    actual=lch.cpu().numpy();reference=expected.numpy()
    if not np.isfinite(actual).all() or not np.array_equal(actual.view(np.uint32),reference.view(np.uint32)):
        failure=HERE/f'guard-failure-{os.getpid()}-{key}-{snr:.4f}-{shard:02d}.npz'
        np.savez_compressed(failure,actual=actual,expected=reference,payload=payload)
        raise AssertionError(('CPU/CUDA channel disagreement; no substitution/retry',str(failure)))
    assert np.array_equal(info,expected_info)
    assert digest==hashlib.sha256(payload.tobytes()+reference.tobytes()).hexdigest()
    baseline=e.OUT/'test/seed17'/key/f'snr-{snr:.4f}'/f'shard-{shard:02d}.npz'
    if split==e.PLAN['test']['split']:
        with np.load(baseline,allow_pickle=False) as old:assert digest==str(old['sample_sha256']),(key,snr,shard,'seed17 sample mismatch')
    record={'event':'independent_cpu_channel_guard','config':key,'snr':snr,'shard':shard,'frames':n,
            'sample_sha256':digest,'bitwise_equal':True,'pid':os.getpid()}
    print(json.dumps(record),flush=True)
    return payload,info,lch,digest

def install():
    e.sample=guarded_sample
    print(json.dumps({'event':'external_endpoint_guard','path':str(Path(__file__).resolve()),
         'sha256':e.sha256(Path(__file__)),'gpu_uuid':os.environ.get('CUDA_VISIBLE_DEVICES'),
         'frozen_sources_unchanged':True,'checks_only':True}),flush=True)

if __name__=='__main__':
    install();e.main()
