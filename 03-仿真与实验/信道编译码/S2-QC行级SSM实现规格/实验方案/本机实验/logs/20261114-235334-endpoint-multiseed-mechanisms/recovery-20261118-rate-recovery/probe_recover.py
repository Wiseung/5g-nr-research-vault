"""Isolate large-shard CUDA recovery without a decoder or random channel."""
from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
LOCAL=HERE.parents[2]
LOG=HERE.parent
sys.path.insert(0,str(LOG/'code'))
import endpoint as e
e.configure(); e.assert_sources()
_,cfg=e.frozen_config(e.PLAN['frozen_inputs'],'ldpc_B4096_R1-2_Q2')
link=e.NRLink(cfg)
assert int(link.nu.max())==1
raw=torch.ones((6250,link.etx),device=link.device)
reference=np.zeros((6250,link.n),dtype=np.float32)
reference[:,link.tx_np]=1
reference[:,link.b:link.k]=20
records=[]
start=time.monotonic()
for trial in range(100):
    recovered=link.recover(raw)
    actual=recovered.cpu().numpy()
    different=np.argwhere(actual.view(np.uint32)!=reference.view(np.uint32))
    row={'trial':trial,'mismatches':len(different),'nonfinite':int((~np.isfinite(actual)).sum()),
         'elapsed':time.monotonic()-start,'pid':os.getpid()}
    records.append(row)
    if len(different):
        row.update(first_coordinates=different[:20].tolist(),
                   actual=[float(actual[tuple(x)]) for x in different[:20]],
                   bits=[hex(int(actual.view(np.uint32)[tuple(x)])) for x in different[:20]])
        np.savez_compressed(HERE/'isolated_recover_failure.npz',actual=actual,tx=link.tx_np)
    if trial%5==0 or len(different):print(json.dumps(row),flush=True)
    e.save_json(HERE/'probe_recover.json',records)
    if len(different):raise AssertionError('finite all-one input failed rate recovery; retained evidence')
    del recovered,actual,different
print('PASS: 100 full-size recoveries; every output bit matched independent reference',flush=True)
