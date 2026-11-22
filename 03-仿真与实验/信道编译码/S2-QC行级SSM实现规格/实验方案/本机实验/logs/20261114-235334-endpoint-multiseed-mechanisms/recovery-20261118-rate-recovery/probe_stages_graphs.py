"""Independent host reference and per-operation capture of original channel."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
import torch
HERE=Path(__file__).resolve().parent; LOG=HERE.parent
sys.path.insert(0,str(LOG/'code'))
import endpoint as e
e.configure();e.assert_sources()
cid='ldpc_B4096_R1-2_Q2';split=e.PLAN['test']['split'];snr=1.5;shard=0;n=6250
_,cfg=e.frozen_config(e.PLAN['frozen_inputs'],cid);link,models,engines=e.resources(cid,e.load(e.OUT/'mlp-seed29_registry.json')['configs'][cid])
payload=np.random.default_rng(e.stable_seed(cid,snr,shard,split+'/bits')).integers(0,2,(n,link.a),dtype=np.uint8)
cw,info=link.encode(payload)
host_bits=cw[:,link.tx_np].astype(np.float32)
host_normal=np.random.default_rng(e.stable_seed(cid,snr,shard,split+'/noise')).standard_normal((n,link.etx//2,2)).astype(np.float32)
cpu_bits=torch.from_numpy(host_bits)
cpu_symbols=(1-2*cpu_bits).reshape(n,-1,2)/np.sqrt(2)
cpu_n0=torch.as_tensor(1/(link.a/link.etx*2*10**(snr/10)),dtype=torch.float32)
cpu_noise=torch.from_numpy(host_normal)*torch.sqrt(cpu_n0/2)
cpu_raw=(2*np.sqrt(2)*(cpu_symbols+cpu_noise)/cpu_n0).flatten(1).numpy()
cpu_recovered=np.zeros((n,link.n),np.float32);cpu_recovered[:,link.tx_np]=cpu_raw
np.clip(cpu_recovered,-20,20,out=cpu_recovered);cpu_recovered[:,link.b:link.k]=20
cpu_digest=hashlib.sha256(payload.tobytes()+cpu_recovered.tobytes()).hexdigest()
with np.load(e.OUT/'test/seed17'/cid/'snr-1.5000/shard-00.npz') as z:old_digest=str(z['sample_sha256'])
print(json.dumps({'cpu_sample_sha256':cpu_digest,'seed17_sample_sha256':old_digest,'equal':cpu_digest==old_digest}),flush=True)
records=[]
for trial in range(8):
    bits=torch.tensor(cw[:,link.tx_np],device=link.device,dtype=torch.float32)
    symbols=(1-2*bits).reshape(n,-1,2)/np.sqrt(2)
    n0=torch.as_tensor(1/(link.a/link.etx*2*10**(snr/10)),device=link.device,dtype=bits.dtype)
    normal=torch.tensor(host_normal,device=link.device)
    noise=normal*torch.sqrt(n0/2)
    raw=(2*np.sqrt(2)*(symbols+noise)/n0).flatten(1)
    restored=link.recover(raw)
    stages=[('bits',bits,host_bits),('symbols',symbols,cpu_symbols.numpy()),('normal',normal,host_normal),
            ('noise',noise,cpu_noise.numpy()),('raw',raw,cpu_raw),('restored',restored,cpu_recovered)]
    row={'trial':trial,'stages':{},'pid':os.getpid()}
    for name,value,ref in stages:
        actual=value.cpu().numpy()
        bad=~np.isclose(actual,ref,atol=1e-5,rtol=0)
        different=actual.view(np.uint32)!=ref.view(np.uint32)
        record={'nonfinite':int((~np.isfinite(actual)).sum()),'unequal_bits':int(different.sum()),
                'max_absolute_error':float(np.abs(actual-ref).max()),'bad_gt_1e_5':int(bad.sum())}
        if bad.any():
            coords=np.argwhere(bad)[:10]
            record.update(coordinates=coords.tolist(),actual=[float(actual[tuple(x)]) for x in coords],
                          expected=[float(ref[tuple(x)]) for x in coords])
            if not (HERE/f'stage_failure_{name}.npy').exists():np.save(HERE/f'stage_failure_{name}.npy',actual)
        row['stages'][name]=record
    actual=restored.cpu().numpy()
    row['sample_sha256']=hashlib.sha256(payload.tobytes()+actual.tobytes()).hexdigest()
    records.append(row);e.save_json(HERE/'probe_stages_graphs.json',records)
    print(json.dumps(row),flush=True)
    del stages,bits,symbols,n0,normal,noise,raw,restored,actual,value,ref,bad,different
