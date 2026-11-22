"""Read-only device configuration; standalone GPU0 memory transport probe."""
from pathlib import Path
import json,os,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'recovery-20261118-rate-recovery'
torch.set_num_threads(4)
torch.use_deterministic_algorithms(True)
torch.backends.cuda.matmul.allow_tf32=False
torch.backends.cudnn.allow_tf32=False
chunks=[];records=[]
for pattern in range(2):
    source=np.random.default_rng(11223+pattern).integers(0,256,size=256*1024*1024,dtype=np.uint8)
    host=torch.from_numpy(source)
    if pattern==0:
        free,total=torch.cuda.mem_get_info()
        count=min(80,int((free-2*1024**3)//host.numel()))
        chunks=[torch.empty_like(host,device='cuda') for _ in range(count)]
    for i,chunk in enumerate(chunks):chunk.copy_(host)
    torch.cuda.synchronize()
    for i,chunk in enumerate(chunks):
        actual=chunk.cpu().numpy()
        bad=np.flatnonzero(actual!=source)
        row={'pattern':pattern,'chunk':i,'device_ptr':hex(chunk.data_ptr()),'mismatches':len(bad),
             'first_byte_offsets':bad[:20].tolist(),'expected':source[bad[:20]].tolist(),
             'actual':actual[bad[:20]].tolist(),'pid':os.getpid()}
        records.append(row)
        if len(bad) or i%8==0:print(json.dumps(row),flush=True)
    (OUT/'probe_vram.json').write_text(json.dumps(records,indent=2)+'\n')
bad=sum(r['mismatches'] for r in records)
print(json.dumps({'status':'failed' if bad else 'passed','bytes_checked':len(records)*host.numel(),'mismatches':bad}),flush=True)
assert bad==0,'standalone host/device byte copy mismatch'
