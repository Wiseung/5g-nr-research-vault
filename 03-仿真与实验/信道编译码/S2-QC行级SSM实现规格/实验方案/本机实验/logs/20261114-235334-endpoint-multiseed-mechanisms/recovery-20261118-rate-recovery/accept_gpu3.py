"""Replay failure shards and selected-model fixed validation on healthy GPU."""
from pathlib import Path
import gc,json,sys
import numpy as np
import torch
from torch.nn import functional as F
from guarded_endpoint import e,install,HERE
install();e.configure();e.assert_sources()
cid='ldpc_B4096_R1-2_Q2'
specs=e.load(e.OUT/'mlp-seed29_registry.json')['configs'][cid]
link,models,engines=e.resources(cid,specs)
records=[]
for shard in (0,5,8,11,16):
    payload,info,lch,digest=e.sample(link,e.PLAN['test']['split'],1.5,shard,6250)
    old_path=e.OUT/'test/seed17'/cid/'snr-1.5000'/f'shard-{shard:02d}.npz'
    with np.load(old_path,allow_pickle=False) as old:
        for mi,engine in enumerate(engines):
            maxstate=0.
            with torch.no_grad():
                for begin in range(0,6250,125):
                    u=engine(lch[begin:begin+125]);assert torch.isfinite(u).all()
                    maxstate=max(maxstate,float(engine.state));assert maxstate<=1.00001
                    if mi==0:
                        labels=torch.tensor(info[begin:begin+125],device=link.device,dtype=torch.float32)
                        bce=F.binary_cross_entropy_with_logits(-u[:,:link.b],labels,reduction='none').mean(1).cpu().numpy()
                        bits=(u[:,:link.b]<0).cpu().numpy().astype(np.uint8)
                        errors=(bits[:,:link.a]!=payload[begin:begin+125]).sum(1)
                        rejection=(~link.accepted(u)).cpu().numpy()
                        crc=(bits==e.crc_attach(bits[:,:link.a],link.cfg['tb_crc'])).all(1)
                        for key,value in [('bce',bce),('bit_errors',errors),('rejected',rejection),('crc_ok',crc)]:
                            assert np.array_equal(value,old[key][0,begin:begin+125]),(shard,key,begin)
            records.append({'shard':shard,'method':specs[mi]['name'],'frames':6250,'finite':True,
                            'state_max':maxstate,'NMS_matches_seed17':True if mi==0 else None,'sample_sha256':digest})
            print(json.dumps(records[-1]),flush=True)
    e.save_json(HERE/'gpu3-health/failure_shards_acceptance.json',records)
    del payload,info,lch

post=e.post_checks(link,models[1],specs[1]['alpha'])
selected=e.model_for(link,specs[1])
assert e.parameter_hash(selected)==e.parameter_hash(models[1])
del selected,engines,models,link;gc.collect();torch.cuda.empty_cache()

# Independent replay of one full 20k-validation shard at all five SNRs,
# for both frozen top-two candidates and NMS; selection is not rerun.
root=e.OUT/'training/bg1-mlp-seed29'
selection=e.load(root/'checkpoint_selection.json')
base=specs[1]
frozen,cfg=e.frozen_config(e.PLAN['frozen_inputs'],cid)
validation=[]
from formal_core import validation_shard
for candidate in [None,*selection['candidates']]:
    step=candidate['step'] if candidate is not None else None
    spec=specs[0] if step is None else dict(base,step=step,checkpoint=str(root/f'checkpoints/step-{step:05d}.pt'),
        checkpoint_sha256=e.sha256(root/f'checkpoints/step-{step:05d}.pt'),parameter_sha256=candidate['model_parameter_sha256'])
    link=e.NRLink(cfg);model=e.model_for(link,spec);engine=e.Engine(link,model,spec['alpha'])
    for snr in frozen['validation_snr_db']:
        payload,info,lch=validation_shard(link,snr,0,625)
        file=root/'validation/20k'/('NMS' if step is None else f'step-{step:05d}')/f'snr-{snr:.4f}-shard-00.npz'
        with np.load(file,allow_pickle=False) as old,torch.no_grad():
            for begin in range(0,625,125):
                u=engine(lch[begin:begin+125]);assert torch.isfinite(u).all()
                labels=torch.tensor(info[begin:begin+125],device=link.device,dtype=torch.float32)
                bce=F.binary_cross_entropy_with_logits(-u[:,:link.b],labels,reduction='none').mean(1).cpu().numpy()
                bits=(u[:,:link.b]<0).cpu().numpy().astype(np.uint8)
                values={'bce':bce,'bit_errors':(bits[:,:link.a]!=payload[begin:begin+125]).sum(1),
                        'rejected':(~link.accepted(u)).cpu().numpy(),
                        'crc_ok':(bits==e.crc_attach(bits[:,:link.a],link.cfg['tb_crc'])).all(1)}
                for key,value in values.items():assert np.array_equal(value,old[key][begin:begin+125]),(step,snr,key)
        validation.append({'step':step,'snr':snr,'frames':625,'all_saved_per_frame_metrics_bitwise_equal':True})
        print(json.dumps(validation[-1]),flush=True)
    del engine,model,link;gc.collect();torch.cuda.empty_cache()
e.save_json(HERE/'gpu3-health/acceptance.json',{'status':'passed','endpoint_frames':31250,
    'endpoint_decodes':62500,'fixed_validation_replay_frames':9375,'failure_shards':records,
    'validation':validation,'post_checks':post,'checkpoint_parameter_reload_exact':True,
    'selected_step_unchanged':specs[1]['step'],'full_training_reexecution':False,
    'validation_scope':'one of 32 shards at all5 SNRs, for NMS and frozen top2; not a complete validation rerun'})
