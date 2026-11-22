"""Executable gate for the formal runner; no formal training budget consumed."""
import argparse
import copy
import gc
import json
from pathlib import Path
import time
import traceback

import numpy as np
import torch

from formal_core import (ROOT,CapturableProduct,InferenceEngine,TrainingEngine,channel_arrays,configure,frozen_config,
    load_checkpoint,loss_parts,lr_at,make_contract,optimizer_for,parameter_hash,post_checks,
    restore_rng,rng_state,save_checkpoint,save_json,source_hashes,syndrome_weight,
    train_batch,training_arrays,validation_shard)
from nr_link import NRLink,sha256
from ssm import RowSSM,training_loss


def cpu_copy(value):
    if torch.is_tensor(value):return value.detach().cpu().clone()
    if isinstance(value,dict):return {k:cpu_copy(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return type(value)(cpu_copy(v) for v in value)
    return value


def equal(a,b,path='root'):
    if torch.is_tensor(a):
        b=b.detach().cpu();assert torch.equal(a,b),(path,float((a-b).abs().max()))
    elif isinstance(a,dict):
        assert a.keys()==b.keys(),path
        for k in a:equal(a[k],b[k],path+'/'+str(k))
    elif isinstance(a,(tuple,list)):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):equal(x,y,path+'/'+str(i))
    else:assert a==b,(path,a,b)


def snapshot(model,opt,row):
    return {'model':cpu_copy(model.state_dict()),'optimizer':cpu_copy(opt.state_dict()),
            'gradients':[cpu_copy(p.grad) for p in model.parameters()],'metrics':row}


def one_config(out,path,cid):
    frozen,cfg=frozen_config(path,cid);link=NRLink(cfg);alpha=frozen['alpha'];bounds=frozen['training_snr_range_db']
    assert torch.equal(link.row_degree,torch.bincount(link.edge_row,minlength=link.rows))
    bounds_checks={str(s):{'lr':lr_at(s),'syndrome':syndrome_weight(s)} for s in [0,1,999,1000,1001,4999,5000,5001,7500,10000,50000]}
    assert lr_at(0)==0 and lr_at(1000)==1e-3 and lr_at(50000)==1e-4
    assert lr_at(1001)<lr_at(1000) and lr_at(1001)>.0009999
    assert syndrome_weight(5000)==0 and syndrome_weight(7500)==.01 and syndrome_weight(10000)==.02
    full=training_arrays(link,17,1,bounds)
    for width in [8,16,32]:
        chunks=[training_arrays(link,17,1,bounds,i,width) for i in range(0,64,width)]
        assert all(np.array_equal(full[j],np.concatenate([v[j] for v in chunks])) for j in range(3))
    cw,info,lch=channel_arrays(link,*full)
    reference_lch,_=link.channel(cw,full[2],np.random.default_rng(0))
    # The noise sequence is supplied explicitly, so compare to the original channel with a tiny RNG adapter.
    class Noise:
        def standard_normal(self,shape):assert tuple(shape)==full[1].shape;return full[1]
    ref,_=link.channel(cw,full[2],Noise());assert torch.equal(ref,lch)
    del reference_lch,ref,cw,lch,info
    prefix={}
    for snr in frozen['validation_snr_db']:
        a=validation_shard(link,snr,0,625);b=validation_shard(link,snr,0,3125)
        assert np.array_equal(a[0],b[0][:625]) and np.array_equal(a[1],b[1][:625]) and torch.equal(a[2],b[2][:625])
        prefix[str(snr)]='exact'
        del a,b
    torch.manual_seed(17);model=RowSSM(link.rows).to(link.device)
    _,info,lch=channel_arrays(link,*training_arrays(link,17,9,bounds,count=8))
    labels=torch.tensor(info,device=link.device,dtype=torch.float32)
    _,h,_=link.decode(lch,alpha=alpha,controller=model,history=True)
    loss_checks={}
    for step in [1,5000,5001,7500,10000]:
        original=training_loss(link,h,info,step)
        adapted=loss_parts(link,h,labels,torch.tensor(syndrome_weight(step),device=link.device))[0]
        assert torch.equal(original,adapted),(cid,step,'loss')
        ga=torch.autograd.grad(original,tuple(model.parameters()),retain_graph=True)
        gb=torch.autograd.grad(adapted,tuple(model.parameters()),retain_graph=True)
        assert all(torch.equal(x,y) for x,y in zip(ga,gb)),(cid,step,'original gradient')
        loss_checks[str(step)]={'loss':float(original.detach()),'gradient_max_error':0.}
    del ga,gb,original,adapted,h,labels,info,lch,model
    gc.collect();torch.cuda.empty_cache()
    print(json.dumps({'event':'original_loss_and_sampling_passed','config':cid}),flush=True)
    # Original eager execution is completed first so BG1 does not retain two full autograd graphs.
    torch.manual_seed(17);model=RowSSM(link.rows).to(link.device);opt=optimizer_for(model)
    engine=TrainingEngine(link,model,alpha,64,'eager');refs={}
    test_steps=[1,2,3,4,5001,7500,10000]
    for step in test_steps:
        info,lch,_,_=train_batch(link,17,step,bounds);row=engine.step(opt,info,lch,step)
        refs[step]=snapshot(model,opt,row)
    del engine,model,opt,info,lch;gc.collect();torch.cuda.empty_cache()
    print(json.dumps({'event':'eager_reference_completed','config':cid}),flush=True)
    torch.manual_seed(17);model=RowSSM(link.rows).to(link.device);opt=optimizer_for(model)
    engine=TrainingEngine(link,model,alpha,64,'cuda-graph')
    contract=make_contract(path,frozen,link,17,'cuda-graph',64)
    checkpoints=out/cid;checkpoints.mkdir()
    replay=[]
    for step in test_steps:
        info,lch,_,_=train_batch(link,17,step,bounds);row=engine.step(opt,info,lch,step)
        equal(refs[step],snapshot(model,opt,row),f'{cid}/graph-eager/{step}')
        replay.append({'step':step,'parameter_max_error':0.,'optimizer_max_error':0.,'gradient_max_error':0.})
        if step==3:checkpoint=save_checkpoint(checkpoints,model,opt,3,contract)
    post=post_checks(link,model,alpha)
    infer=InferenceEngine(link,model,alpha,125)
    _,info,lch=channel_arrays(link,*training_arrays(link,17,10,bounds,count=125))
    with torch.no_grad():
        a=link.decode(lch,alpha=alpha,controller=model)[0];b=infer(lch)
        assert torch.equal(a,b),(cid,'inference graph')
    del engine,infer,model,opt,a,b,info,lch;gc.collect();torch.cuda.empty_cache()
    torch.manual_seed(999);model=RowSSM(link.rows).to(link.device);opt=optimizer_for(model)
    engine=TrainingEngine(link,model,alpha,64,'cuda-graph')
    data=load_checkpoint(checkpoint,model,opt,contract);restore_rng(data['rng'])
    before_rng=rng_state();equal(cpu_copy(data['rng']),before_rng,'RNG restored')
    info,lch,_,_=train_batch(link,17,4,bounds);row=engine.step(opt,info,lch,4)
    equal(refs[4],snapshot(model,opt,row),f'{cid}/checkpoint-next-step')
    result={'status':'passed','batch':64,'loss_original_checks':loss_checks,'schedule':bounds_checks,
            'microbatch_sample_partition':[8,16,32,64],'channel_original_max_error':0.,
            'validation625_3125_prefix':prefix,'graph_eager_updates':replay,
            'checkpoint_next_step_model_optimizer_gradient_max_error':0.,'rng_restore':'exact',
            'inference_graph_original_max_error':0.,'updated_model_checks':post,
            'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
    save_json(checkpoints/'summary.json',result)
    del engine,model,opt,info,lch;gc.collect();torch.cuda.empty_cache()
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--frozen',required=True)
    args=parser.parse_args();configure()
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True);assert not any(out.iterdir())
    started=time.perf_counter();results={}
    try:
        torch.manual_seed(17)
        for zeros in [0,1,2,20]:
            x=torch.randn((8,4,20,13),device='cuda')
            if zeros:x[:,:,0:zeros,:]=0
            x.requires_grad_();grad=torch.randn((8,4,13),device='cuda')
            a=x.prod(2);b=CapturableProduct.apply(x)
            assert torch.equal(a,b)
            ga=torch.autograd.grad(a,x,grad)[0];gb=torch.autograd.grad(b,x,grad)[0]
            assert torch.equal(ga,gb),(zeros,'product derivative')
        del x,a,b,ga,gb,grad
        for cid in ['ldpc_B1024_R1-2_Q2','ldpc_B4096_R1-2_Q2']:
            print(json.dumps({'event':'verifying','config':cid}),flush=True)
            torch.cuda.reset_peak_memory_stats();results[cid]=one_config(out,Path(args.frozen).resolve(),cid)
            print(json.dumps({'event':'config_passed','config':cid,**results[cid]}),flush=True)
        save_json(out/'summary.json',{'status':'passed','configs':results,'source_sha256':source_hashes(),
                  'frozen_inputs_sha256':sha256(Path(args.frozen)),'elapsed_seconds':time.perf_counter()-started,
                  'verify_script_sha256':sha256(Path(__file__))})
    except Exception as exc:
        save_json(out/'failure.json',{'error':repr(exc),'traceback':traceback.format_exc(),'completed_configs':list(results)})
        raise


if __name__=='__main__':main()
