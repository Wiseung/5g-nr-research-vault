"""Independent bounded early-LR comparison, after pilot and alpha freeze.

This is not the protocol50k runner. Bounds stay at500 steps, effective batch8.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import torch
from torch.nn import functional as F

from nr_link import NRLink, sha256
from run_local import ROOT, dump, emit, environment, rng_for
from ssm import RowSSM, training_loss
from train_smoke import samples
from protocol_checks import wilson, zero_error_upper

SETTINGS=("constant_1e-3","protocol_warmup1000")
SEEDS=(17,29,43)


def vector(model):
    return torch.cat([p.detach().flatten() for p in model.parameters()])


def vector_hash(model):
    return hashlib.sha256(vector(model).cpu().numpy().tobytes()).hexdigest()


def evaluation(link,model,alpha,fixed,out,tag,batch=64):
    points=[];arrays={}
    with torch.no_grad():
        for point_id,(snr,payload,info,lch) in enumerate(fixed):
            errors=[];bits=[];reject=[];bces=[]
            for start in range(0,len(payload),batch):
                end=min(len(payload),start+batch)
                u,_,state=link.decode(lch[start:end],alpha=alpha,controller=model)
                assert torch.isfinite(u).all() and float(state)<=1.00001
                labels=torch.tensor(info[start:end],device=link.device,dtype=torch.float32)
                bces.append(F.binary_cross_entropy_with_logits(-u[:,:link.b],labels,reduction='none').mean(1).cpu().numpy())
                wrong=(u[:,:link.a]<0).cpu().numpy()!=payload[start:end]
                errors.append(wrong.any(1));bits.append(wrong.sum(1));reject.append((~link.accepted(u)).cpu().numpy())
            wrong=np.concatenate(errors);bit=np.concatenate(bits);rej=np.concatenate(reject);bce=np.concatenate(bces)
            n=len(payload);e=int(wrong.sum())
            row={'snr_db':snr,'frames':n,'information_bce':float(bce.mean(dtype=np.float64)),
                 'payload_frame_errors':e,'payload_bit_errors':int(bit.sum()),'rejected':int(rej.sum()),
                 'service_frame_errors':int((wrong|rej).sum()),'accepted_wrong':int((wrong&~rej).sum()),
                 'bler_ci95':wilson(e,n)}
            if e==0:row['zero_error_one_sided95_upper']=zero_error_upper(n)
            points.append(row)
            for name,data in (('frame_errors',wrong),('bit_errors',bit),('rejected',rej),('bce',bce)):
                arrays[f'point{point_id}_{name}']=data
    np.savez_compressed(out/(tag+'.npz'),**arrays)
    result={'points':points,'mean_information_bce':float(np.mean([p['information_bce'] for p in points])),
            'total_payload_frame_errors':sum(p['payload_frame_errors'] for p in points),'frames':sum(p['frames'] for p in points)}
    dump(out/(tag+'.json'),result)
    return result


def post_checks(link,model,alpha,snr):
    payload,cw,info,lch=samples(link,'calibrated-optimization-postcheck',16,snr,seed=17)
    sign=torch.tensor(1-2*cw.astype(np.float32),device=link.device)
    base=(lch*4).clamp(-20,20).masked_fill(link.filler,20)
    with torch.no_grad():
        u,_,state=link.decode(base,alpha=alpha,controller=model)
        signed,_,_=link.decode(base*sign,alpha=alpha,controller=model)
        symmetry=float((signed-u*sign).abs().max())
        assert symmetry<2e-4 and float(state)<=1.00001,(symmetry,state)
        clean,_=link.channel(cw,0.,np.random.default_rng(19),noiseless=True)
        decoded,_,_=link.decode(clean,alpha=alpha,controller=model)
        errors=int(np.any((decoded[:,:link.a]<0).cpu().numpy()!=payload,axis=1).sum())
        rejected=int((~link.accepted(decoded)).sum())
        assert errors==rejected==0,(errors,rejected)
    return {'frames':len(payload),'symmetry_max_abs_error':symmetry,'state_abs_max':float(state),
            'noiseless_payload_errors':errors,'noiseless_rejected':rejected}


def run_one(link,frozen,setting,seed,fixed,out,args):
    out.mkdir(parents=True,exist_ok=False)
    torch.manual_seed(seed)
    model=RowSSM(link.rows).to(link.device)
    initial_hash=vector_hash(model)
    alpha=frozen['alpha'];low,high=frozen['final_pilot']['training_snr_range_db']
    decay=[];no_decay=[]
    for name,p in model.named_parameters():
        (no_decay if name.endswith('bias') or 'norm' in name or name=='theta' else decay).append(p)
    optimizer=torch.optim.AdamW([{'params':decay,'weight_decay':1e-4},
                                {'params':no_decay,'weight_decay':0.}],lr=1e-3)
    spec={'config_id':link.cfg['id'],'formal_training':False,'setting':setting,'seed':seed,
          'steps':args.steps,'batch':8,'T':20,'alpha':alpha,'alpha_calibrated':True,
          'training_snr_range_db':[low,high],'validation_snr_db':frozen['final_pilot']['validation_snr_db'],
          'validation_frames_per_snr':256,'validation_batch':64,'clip_norm':1.,
          'initial_parameters_sha256':initial_hash,'optimizer':'AdamW beta(.9,.999) eps1e-8',
          'lr_rule':'1e-3' if setting==SETTINGS[0] else '1e-3*step/1000, steps1..500 only',
          'syndrome_loss_weight':0.,'early_stop':False,'fallback':False,
          'calibration_summary_sha256':sha256(Path(args.calibration)),
          'limitations':['500-step early optimization diagnostic','batch8; formal budget is64',
                         '256 validation frames per SNR; formal validation requires20k/100k',
                         'full cosine schedule not reached','no formal BLER improvement claim']}
    dump(out/'run_spec.json',spec)
    emit(out,'started',**spec)
    initial=evaluation(link,model,alpha,fixed,out,'validation-0000')
    records=[];validation_history=[{'step':0,**initial}]
    initial_vector=vector(model).clone()
    eta_trace=[]
    eta_recording=False
    def record_eta(module,inputs,output):
        if eta_recording:
            eta_trace.append(output[0].detach())
    eta_hook=model.register_forward_hook(record_eta)
    torch.cuda.reset_peak_memory_stats()
    total_start=time.perf_counter()
    for step in range(1,args.steps+1):
        torch.cuda.synchronize();start=time.perf_counter()
        key=f'calibrated-opt-train/seed-{seed}/step-{step}'
        snrs=rng_for(link.cfg['id'],key,stream='snr').uniform(low,high,8)
        _,_,info,lch=samples(link,'calibrated-opt-train',8,snrs,seed=seed,step=step)
        input_hash=hashlib.sha256(info.tobytes()+lch.cpu().numpy().tobytes()+snrs.tobytes()).hexdigest()
        lr=1e-3 if setting==SETTINGS[0] else 1e-3*step/1000
        for group in optimizer.param_groups:group['lr']=lr
        optimizer.zero_grad(set_to_none=True)
        eta_trace.clear();eta_recording=True
        _,history,state=link.decode(lch,alpha=alpha,controller=model,history=True)
        eta_recording=False
        loss=training_loss(link,history,info,step)
        assert torch.isfinite(loss),(step,'loss')
        loss.backward()
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()),(step,'gradient')
        head_sq=sum(p.grad.square().sum() for name,p in model.named_parameters() if name.startswith('head.'))
        all_sq=sum(p.grad.square().sum() for p in model.parameters())
        head_share=float(head_sq/all_sq.clamp_min(1e-30))
        grad=float(torch.nn.utils.clip_grad_norm_(model.parameters(),1.))
        assert np.isfinite(grad) and float(state)<=1.00001,(step,grad,state)
        grad_after=float(torch.sqrt(sum(p.grad.square().sum() for p in model.parameters())))
        assert np.isfinite(grad_after) and grad_after<=1.00001,(step,'clip',grad_after)
        previous=vector(model).clone()
        optimizer.step()
        current=vector(model)
        assert torch.isfinite(current).all(),(step,'parameters')
        update=float(torch.linalg.vector_norm(current-previous))
        eta_values=torch.stack(eta_trace).flatten()
        eta_stats=torch.quantile(eta_values,torch.tensor([0.,.1,.5,.9,1.],device=link.device)).cpu().tolist()
        torch.cuda.synchronize()
        row={'step':step,'loss':float(loss.detach()),'lr':lr,'gradient_norm_before_clip':grad,
             'gradient_norm_after_clip':grad_after,'clip_coefficient':min(1.,1./(grad+1e-6)),
             'gradient_clipped':grad>1.,'head_gradient_squared_fraction':head_share,
             'parameter_update_l2':update,'parameter_displacement_from_initial_l2':float(torch.linalg.vector_norm(current-initial_vector)),
             'parameter_norm_l2':float(torch.linalg.vector_norm(current)),'state_abs_max':float(state),
             'eta_min_p10_median_p90_max':eta_stats,'eta_mean':float(eta_values.mean()),
             'snr_min_db':float(snrs.min()),'snr_max_db':float(snrs.max()),'snr_mean_db':float(snrs.mean()),
             'seconds':time.perf_counter()-start,'input_sha256':input_hash,
             'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
        records.append(row)
        with (out/'train_history.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        if step==1 or step%25==0:emit(out,'train_step',**row)
        if step in (250,args.steps):
            val=evaluation(link,model,alpha,fixed,out,f'validation-{step:04d}')
            validation_history.append({'step':step,**val});emit(out,'validation',step=step,**val)
    eta_hook.remove()
    post=post_checks(link,model,alpha,(low+high)/2)
    path=out/'checkpoint-final.pt'
    torch.save({'model':model.state_dict(),'optimizer':optimizer.state_dict(),'step':args.steps,'run_spec':spec},path)
    reloaded=RowSSM(link.rows).to(link.device)
    saved=torch.load(path,weights_only=True)
    reloaded.load_state_dict(saved['model'])
    restored_decay=[];restored_no_decay=[]
    for name,p in reloaded.named_parameters():
        (restored_no_decay if name.endswith('bias') or 'norm' in name or name=='theta' else restored_decay).append(p)
    restored_optimizer=torch.optim.AdamW([{'params':restored_decay,'weight_decay':1e-4},
                                         {'params':restored_no_decay,'weight_decay':0.}],lr=1e-3)
    restored_optimizer.load_state_dict(saved['optimizer'])
    original_state=optimizer.state_dict();restored_state=restored_optimizer.state_dict()
    assert original_state['param_groups']==restored_state['param_groups']
    for index,values in original_state['state'].items():
        for key,value in values.items():
            restored_value=restored_state['state'][index][key]
            assert torch.equal(value,restored_value) if isinstance(value,torch.Tensor) else value==restored_value
    with torch.no_grad():
        replay=fixed[0][3][:8]
        before=link.decode(replay,alpha=alpha,controller=model)[0]
        after=link.decode(replay,alpha=alpha,controller=reloaded)[0]
        reload_error=float((before-after).abs().max());assert reload_error==0
    gradients=np.array([r['gradient_norm_before_clip'] for r in records])
    summary={'status':'completed','formal_training':False,'config_id':link.cfg['id'],'seed':seed,'setting':setting,
             'steps':args.steps,'batch':8,'observations':8*args.steps,'alpha':alpha,
             'parameters':sum(p.numel() for p in model.parameters()),
             'mean_step_seconds':float(np.mean([r['seconds'] for r in records])),
             'mean_step_seconds_after_first50':float(np.mean([r['seconds'] for r in records[50:] or records])),
             'elapsed_seconds':time.perf_counter()-total_start,
             'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
             'initial_validation':initial,'final_validation':validation_history[-1],
             'validation_history':validation_history,'gradient_clip_fraction':float((gradients>1).mean()),
             'gradient_norm_quantiles':dict(zip(('min','p10','p25','median','p75','p90','p95','p99','max'),
                                               np.quantile(gradients,[0,.1,.25,.5,.75,.9,.95,.99,1]).tolist())),
             'head_gradient_squared_fraction_median':float(np.median([r['head_gradient_squared_fraction'] for r in records])),
             'final_parameter_displacement_l2':records[-1]['parameter_displacement_from_initial_l2'],
             'post_checks':post,'checkpoint_reload_max_error':reload_error,'checkpoint_sha256':sha256(path),
             'optimizer_reload_state_exact':True,
             'initial_parameters_sha256':initial_hash,'final_parameters_sha256':vector_hash(model)}
    dump(out/'summary.json',summary);emit(out,'completed',**{k:v for k,v in summary.items() if k not in ('initial_validation','final_validation','validation_history')})
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--calibration',required=True)
    parser.add_argument('--steps',type=int,default=500)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if not 1<=args.steps<=500:parser.error('bounded comparison requires1..500 steps')
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()) and not args.resume:parser.error('output must be empty or explicit --resume')
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    manifest=json.loads((ROOT.parent/'experiment_manifest.json').read_text())
    calibration=json.loads(Path(args.calibration).read_text());assert calibration['status']=='completed'
    env=environment(out,args);env['source_sha256'][str(Path(__file__).resolve())]=sha256(Path(__file__))
    dump(out/'environment.json',env)
    results=[]
    try:
        for frozen in calibration['configs']:
            cid=frozen['config_id'];link=NRLink(next(c for c in manifest['ldpc_configs'] if c['id']==cid))
            fixed=[]
            for snr in frozen['final_pilot']['validation_snr_db']:
                payload,_,info,lch=samples(link,f'calibrated-opt-validation/{snr:.4f}',256,snr,seed=0)
                fixed.append((snr,payload,info,lch))
            baseline_dir=out/cid/'baseline';baseline_dir.mkdir(parents=True,exist_ok=True)
            baseline=evaluation(link,None,frozen['alpha'],fixed,baseline_dir,'NMS_F20')
            for seed in SEEDS:
                pair=[]
                for setting in SETTINGS:
                    directory=out/cid/f'seed-{seed}'/setting
                    if (directory/'summary.json').exists() and args.resume:
                        result=json.loads((directory/'summary.json').read_text())
                    else:
                        result=run_one(link,frozen,setting,seed,fixed,directory,args)
                    pair.append(result);results.append(result)
                    gc.collect();torch.cuda.empty_cache()
                    dump(out/'partial_summary.json',results)
                assert pair[0]['initial_parameters_sha256']==pair[1]['initial_parameters_sha256']
                histories=[]
                for setting in SETTINGS:
                    histories.append([json.loads(s) for s in (out/cid/f'seed-{seed}'/setting/'train_history.jsonl').read_text().splitlines()])
                assert [r['input_sha256'] for r in histories[0]]==[r['input_sha256'] for r in histories[1]],'unpaired training observations'
                assert pair[0]['initial_validation']==pair[1]['initial_validation'],'unpaired initialization/validation'
            del fixed,link
            gc.collect();torch.cuda.empty_cache()
        summary={'status':'completed','formal_training':False,'runs':results,'pairing_verified':True,
                 'total_optimizer_steps':len(results)*args.steps,'observations':len(results)*args.steps*8}
        dump(out/'summary.json',summary);emit(out,'completed',run_count=len(results),total_optimizer_steps=summary['total_optimizer_steps'])
    except Exception as exc:
        dump(out/'failure.json',{'error':repr(exc),'traceback':traceback.format_exc(),'completed_runs':len(results)})
        raise

if __name__=='__main__':main()
