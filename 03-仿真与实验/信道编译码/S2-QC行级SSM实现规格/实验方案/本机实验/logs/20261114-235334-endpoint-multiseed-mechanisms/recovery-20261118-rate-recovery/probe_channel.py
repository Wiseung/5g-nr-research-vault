"""Retain raw channel and restored LLR; independent CPU rate recovery."""
from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np
import torch
HERE=Path(__file__).resolve().parent; LOG=HERE.parent
sys.path.insert(0,str(LOG/'code'))
import endpoint as e
e.configure(); e.assert_sources()
cid='ldpc_B4096_R1-2_Q2'
registry=e.load(e.OUT/'mlp-seed29_registry.json')
link,models,engines=e.resources(cid,registry['configs'][cid])
original=link.channel
saved={}
def channel(*args,**kwargs):
    out,raw=original(*args,**kwargs)
    saved['raw']=raw
    return out,raw
link.channel=channel
records=[]
for trial in range(64):
    shard=trial%32
    payload,info,lch,digest=e.sample(link,'S2-formal-test-awgn-t20-v1',1.5,shard,6250)
    raw=saved.pop('raw').cpu().numpy()
    actual=lch.cpu().numpy()
    reference=np.zeros_like(actual)
    assert int(link.nu.max())==1
    reference[:,link.tx_np]=raw
    np.clip(reference,-20,20,out=reference)
    reference[:,link.b:link.k]=20
    differences=np.argwhere(actual.view(np.uint32)!=reference.view(np.uint32))
    old=e.OUT/'test/seed17'/cid/'snr-1.5000'/f'shard-{shard:02d}.npz'
    with np.load(old,allow_pickle=False) as z:old_digest=str(z['sample_sha256'])
    row={'trial':trial,'shard':shard,'raw_nonfinite':int((~np.isfinite(raw)).sum()),
         'recovered_nonfinite':int((~np.isfinite(actual)).sum()),'cpu_recover_mismatches':len(differences),
         'sample_sha256':digest,'matches_seed17':digest==old_digest,'pid':os.getpid()}
    records.append(row)
    e.save_json(HERE/'probe_channel.json',records)
    print(json.dumps(row),flush=True)
    if row['raw_nonfinite'] or len(differences) or digest!=old_digest:
        np.savez_compressed(HERE/'raw_and_recover_failure.npz',raw=raw,actual=actual,reference=reference,
                            payload=payload,tx=link.tx_np)
        raise AssertionError('channel mismatch; raw LLR and CPU reference preserved')
    with torch.no_grad():
        for engine in engines:
            # Exercise graph pools between large allocations, without redoing a formal test.
            assert torch.isfinite(engine(lch[:125])).all()
    del raw,actual,reference,differences,payload,info,lch
e.save_json(HERE/'probe_channel_passed.json',{'status':'passed','shards':len(records)})
