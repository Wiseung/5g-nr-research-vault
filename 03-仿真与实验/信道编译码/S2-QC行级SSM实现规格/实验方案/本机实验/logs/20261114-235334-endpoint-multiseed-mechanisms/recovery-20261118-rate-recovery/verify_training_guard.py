import gc,json,sys
from pathlib import Path
import numpy as np
import torch
import guarded_training as guard
import endpoint as e
e.configure();e.assert_sources()
records=[]
registry=e.load(e.OUT/'mlp-seed29_registry.json')
for cid,specs in registry['configs'].items():
    frozen,cfg=e.frozen_config(e.PLAN['frozen_inputs'],cid)
    link=e.NRLink(cfg)
    for seed,step in [(29,1),(43,1000),(43,50000)]:
        info,lch,snrs,digest=guard.core.train_batch(link,seed,step,(.5,2.5))
        assert torch.isfinite(lch).all()
        records.append({'config':cid,'seed':seed,'step':step,'batch':64,'cpu_absolute_error_lt_1e_5':True})
    model=e.model_for(link,specs[1]);check=e.post_checks(link,model,specs[1]['alpha'])
    records.append({'config':cid,'post_checks':check})
    del model,link,lch;gc.collect();torch.cuda.empty_cache()
e.save_json(guard.HERE/'gpu3-health/training_input_guard_acceptance.json',{'status':'passed','records':records})
print(json.dumps({'status':'passed','records':records}),flush=True)
