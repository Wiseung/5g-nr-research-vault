"""Bounded gradient diagnosis, no changes to production decoder or training settings."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import torch
from torch.nn import functional as F

LOG = Path(__file__).resolve().parent
LOCAL = LOG.parents[1]
RUN_ID = LOG.name
OUT = LOCAL / 'results' / RUN_ID
ORIGINAL = '20261113-152035-s2qc-4090-'
sys.path.insert(0, str(LOCAL))
from nr_link import NRLink, sha256
from ssm import RowSSM, training_loss
from run_local import environment, rng_for
from train_smoke import samples
sys.path.insert(0, str(LOCAL.parent))
from generate_manifest import build


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def emit(event, **data):
    print(json.dumps({'event': event, **data}, ensure_ascii=False, allow_nan=False), flush=True)


def append(name, value):
    with (OUT / name).open('a') as f:
        f.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')


def vector(model):
    return torch.cat([p.grad.detach().flatten() if p.grad is not None else torch.zeros_like(p).flatten()
                      for p in model.parameters()])


def param_stats(model):
    rows = []
    for name, p in model.named_parameters():
        g = p.grad
        rows.append({'name': name, 'elements': p.numel(), 'parameter_norm': float(p.detach().norm()),
                     'gradient_norm': float(g.norm()) if g is not None else 0.0,
                     'gradient_abs_max': float(g.abs().max()) if g is not None else 0.0})
    total2 = sum(r['gradient_norm'] ** 2 for r in rows)
    for r in rows:
        r['squared_norm_share'] = r['gradient_norm'] ** 2 / max(total2, 1e-300)
    return rows


def get_model(link, checkpoint='initial'):
    torch.manual_seed(17)
    model = RowSSM(link.rows).to(link.device)
    if checkpoint == 'final':
        model.load_state_dict(torch.load(LOCAL / 'results' / (ORIGINAL + ('bg1' if link.bg == 1 else 'bg2') + '-smoke') / 'smoke_checkpoint.pt', weights_only=True)['model'])
    return model


def config(bg):
    cid = 'ldpc_B4096_R1-2_Q2' if bg == 1 else 'ldpc_B1024_R1-2_Q2'
    return next(c for c in build()['ldpc_configs'] if c['id'] == cid)


def input_batch(link, step):
    snrs = rng_for(link.cfg['id'], f'smoke-train/seed-17/step-{step}', stream='snr').uniform(0, 2, 8)
    _, _, info, lch = samples(link, 'smoke-train', 8, snrs, 17, step)
    return snrs, info, lch


def history_analysis():
    from scipy.stats import spearmanr, pearsonr
    result = {}
    for bg in (2, 1):
        link_id = config(bg)['id']
        rows = [json.loads(x) for x in (LOCAL / 'results' / (ORIGINAL + f'bg{bg}-smoke') / 'train_history.jsonl').read_text().splitlines()]
        expanded = []
        for r in rows:
            snr = rng_for(link_id, f'smoke-train/seed-17/step-{r["step"]}', stream='snr').uniform(0, 2, 8)
            expanded.append({**r, 'snr_mean_db': float(snr.mean()), 'snr_median_db': float(np.median(snr)),
                             'snr_fraction_0_1': float((snr < 1).mean()), 'snrs_db': snr.tolist()})
        g = np.log10([r['gradient_norm_before_clip'] for r in rows])
        correlations = {}
        for key in ('step', 'loss', 'snr_mean_db', 'snr_min_db', 'snr_max_db', 'snr_fraction_0_1', 'state_abs_max'):
            v = [r[key] for r in expanded]
            correlations[key] = {'spearman': float(spearmanr(g, v).statistic), 'pearson_log10grad': float(pearsonr(g, v).statistic)}
        windows = []
        for begin in range(0, 100, 20):
            a = expanded[begin:begin+20];gr=np.array([r['gradient_norm_before_clip'] for r in a])
            windows.append({'steps': [begin+1, begin+20], 'median_gradient': float(np.median(gr)),
                            'max_gradient': float(gr.max()), 'clip_fraction': float((gr > 1).mean()),
                            'mean_loss': float(np.mean([r['loss'] for r in a]))})
        result[f'bg{bg}'] = {'correlations': correlations, 'windows': windows,
                             'expanded_history': expanded, 'top5_steps': sorted(rows, key=lambda r:r['gradient_norm_before_clip'], reverse=True)[:5]}
    dump('history_analysis.json', result)


def replay():
    history_analysis()
    for bg in (2, 1):
        link=NRLink(config(bg)); model=get_model(link)
        decay, no_decay = [], []
        for name, p in model.named_parameters():
            (no_decay if name.endswith('bias') or 'norm' in name or name == 'theta' else decay).append(p)
        optimizer=torch.optim.AdamW([{'params':decay,'weight_decay':1e-4}, {'params':no_decay,'weight_decay':0.0}], lr=1e-3)
        original=[json.loads(x) for x in (LOCAL/'results'/(ORIGINAL+f'bg{bg}-smoke')/'train_history.jsonl').read_text().splitlines()]
        maxstep=max(original,key=lambda r:r['gradient_norm_before_clip'])['step']
        saved_steps={1,20,50,100,maxstep}
        max_loss_diff=max_norm_diff=0.0
        for step in range(1,101):
            if step in saved_steps:
                torch.save({'model':model.state_dict(),'step_before':step,'formal_training':False},OUT/f'bg{bg}-before-{step}.pt')
            snrs,info,lch=input_batch(link,step)
            cache=[]
            def hook(module, inputs, outputs):
                eta,state=outputs
                eta.retain_grad();state.retain_grad();cache.append((eta,state))
            handle=model.register_forward_hook(hook)
            optimizer.zero_grad(set_to_none=True)
            _,history,state=link.decode(lch,controller=model,history=True)
            loss=training_loss(link,history,info,step)
            loss.backward(); handle.remove()
            assert torch.isfinite(loss) and all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
            params=param_stats(model);g=vector(model);norm=float(g.norm())
            pre={n:p.detach().clone() for n,p in model.named_parameters()}
            clipped=float(torch.nn.utils.clip_grad_norm_(model.parameters(),1.0))
            optimizer.step()
            delta=torch.cat([(p.detach()-pre[n]).flatten() for n,p in model.named_parameters()])
            max_loss_diff=max(max_loss_diff,abs(float(loss.detach())-original[step-1]['loss']))
            max_norm_diff=max(max_norm_diff,abs(norm-original[step-1]['gradient_norm_before_clip']))
            row={'bg':bg,'step':step,'loss':float(loss.detach()),'gradient_norm':norm,'original_gradient_norm':original[step-1]['gradient_norm_before_clip'],
                 'original_loss':original[step-1]['loss'],'snrs_db':snrs.tolist(),'state_abs_max':float(state),
                 'parameters':params,'eta_by_iteration':[{'t':t+1,'mean':float(e.detach().mean()),'min':float(e.detach().min()),'max':float(e.detach().max()),
                      'eta_adjoint_norm':float(e.grad.norm()),'eta_adjoint_abs_max':float(e.grad.abs().max()),
                      'state_adjoint_norm':float(h.grad.norm())} for t,(e,h) in enumerate(cache)],
                 'clip_coefficient':min(1.0,1.0/(clipped+1e-6)), 'optimizer_delta_norm':float(delta.norm()),
                 'optimizer_delta_relative_norm':float(delta.norm()/torch.cat([v.flatten() for v in pre.values()]).norm()),
                 'cosine_negative_gradient_optimizer_delta':float(F.cosine_similarity(-g,delta,dim=0))}
            append('replay.jsonl',row)
            if step==1 or step%20==0:emit('replay',bg=bg,step=step,gradient_norm=norm,head_share=sum(p['squared_norm_share'] for p in params if p['name'].startswith('head.')),
                                          original_gradient=original[step-1]['gradient_norm_before_clip'])
            del cache,loss,history
        final=get_model(link,'final')
        differences={n:float((p.detach()-dict(final.named_parameters())[n]).abs().max()) for n,p in model.named_parameters()}
        dump(f'bg{bg}-replay-fidelity.json',{'max_loss_abs_diff':max_loss_diff,'max_gradient_norm_abs_diff':max_norm_diff,
                 'parameter_max_abs_diff_to_original_checkpoint':differences,'saved_before_steps':sorted(saved_steps),
                 'note':'Replay adds observation hooks only; numerical drift is measured, not assumed absent.'})


def traced(link, model, lch, *, T=20, mode='normal', frozen=None, independent_eta=False, store=True):
    """Same forward equations. detach modes change backward paths only and are diagnostic controls."""
    u=lch;r=lch.new_zeros((len(lch),link.p,link.z));state=None
    prev,_=link.masked_violation(u);dr=lch.new_zeros((len(lch),link.rows));history=[];trace=[]
    for t in range(T):
        if mode=='detach_messages' and t>0:
            u=u.detach();r=r.detach()
        q=(link.gather(u)-r).clamp(-20,20).masked_fill(~link.edge_nonfiller.bool(),20)
        if frozen is None:f,c,now=link.features(u,q,r,dr,prev,t)
        else:f,c,now=frozen[t]
        if mode=='detach_state' and state is not None:state=state.detach()
        if independent_eta:
            eta=torch.full((len(lch),link.rows,1),0.05,device=link.device,dtype=lch.dtype,requires_grad=True)
            state=None
        else:eta,state=model(f,c,state)
        candidate=link.minsum(q)
        damping=eta[:,link.edge_row]
        new=((1-damping)*0.8*candidate+damping*r).clamp(-20,20)
        dr=link.row_mean((new-r).abs()).detach()
        nextu=(lch+link.scatter(new)).masked_fill(link.filler,20)
        if store:
            row={'t':t+1,'eta':eta,'state':state,'q':q,'ms':candidate,'r':new,'u':nextu,
                 'features':(f.detach(),c.detach(),now.detach())}
            for key in ('eta','state','q','ms','r','u'):
                if row[key] is not None and row[key].requires_grad:row[key].retain_grad()
            trace.append(row)
        r,u,prev=new,nextu,now
        if t>=T-4:history.append(u.clamp(-20,20))
    return u.clamp(-20,20),history,trace


def adjoints(trace):
    result=[]
    for row in trace:
        d={'t':row['t'],'eta_mean':float(row['eta'].detach().mean())}
        for key in ('eta','state','q','ms','r','u'):
            x=row[key]
            if x is None:continue
            d[key+'_rms']=float(x.detach().square().mean().sqrt())
            d[key+'_abs_max']=float(x.detach().abs().max())
            if x.grad is not None:
                d[key+'_grad_norm']=float(x.grad.norm())
                d[key+'_grad_abs_max']=float(x.grad.abs().max())
        result.append(d)
    return result


def probe_grad(link,model,info,lch,mode='normal',T=20,independent_eta=False):
    model.zero_grad(set_to_none=True)
    u,history,trace=traced(link,model,lch,T=T,mode=mode,independent_eta=independent_eta)
    loss=training_loss(link,history,info,100)
    loss.backward()
    result={'loss':float(loss.detach()),'gradient_norm':float(vector(model).norm()),'parameters':param_stats(model),
            'adjoints':adjoints(trace),'payload_frame_errors':int(((u[:,:link.a]<0).cpu().numpy()!=info[:,:link.a]).any(1).sum())}
    if independent_eta:result['independent_eta_gradient_norm']=float(torch.cat([r['eta'].grad.flatten() for r in trace]).norm())
    return result,u.detach(),trace


def profiles():
    for bg in (2,1):
        link=NRLink(config(bg))
        for checkpoint in ('initial','final'):
            model=get_model(link,checkpoint)
            for snr in (0.0,0.5,1.0,1.5,2.0):
                for shard in range(4):
                    _,_,info,lch=samples(link,'gradient-fixed-snr',8,snr,17,shard)
                    model.zero_grad(set_to_none=True)
                    _,history,state=link.decode(lch,controller=model,history=True)
                    loss=training_loss(link,history,info,100);loss.backward()
                    append('profiles.jsonl',{'bg':bg,'checkpoint':checkpoint,'snr_db':snr,'shard':shard,
                        'loss':float(loss.detach()),'gradient_norm':float(vector(model).norm()),
                        'parameters':param_stats(model),'state_abs_max':float(state)})
                emit('profile',bg=bg,checkpoint=checkpoint,snr=snr)


def detail():
    for bg in (2,1):
        link=NRLink(config(bg))
        original=[json.loads(x) for x in (LOCAL/'results'/(ORIGINAL+f'bg{bg}-smoke')/'train_history.jsonl').read_text().splitlines()]
        maxstep=max(original,key=lambda r:r['gradient_norm_before_clip'])['step']
        for selected in (1,maxstep):
            model=get_model(link);model.load_state_dict(torch.load(OUT/f'bg{bg}-before-{selected}.pt',weights_only=True)['model'])
            _,info,lch=input_batch(link,selected)
            # Verify traced forward and gradients against unchanged NRLink.decode.
            model.zero_grad(set_to_none=True)
            reference,history,_=link.decode(lch,controller=model,history=True)
            loss=training_loss(link,history,info,100);loss.backward();gref=vector(model).clone()
            baseline,u,trace=probe_grad(link,model,info,lch)
            difference=float((u-reference.detach()).abs().max());gdiff=float((vector(model)-gref).abs().max())
            assert difference<2e-4 and gdiff<max(1e-4,float(gref.abs().max())*2e-4),(difference,gdiff)
            frozen=[r['features'] for r in trace]
            torch.save({'info':info,'lch':lch.cpu(),'features':[(f.cpu(),c.cpu(),n.cpu()) for f,c,n in frozen],
                        'model':model.state_dict(),'bg':bg,'step_before':selected,'formal_training':False},OUT/f'bg{bg}-detail-input-{selected}.pt')
            counter=[]
            for mode in ('detach_state','detach_messages'):
                value,other,_=probe_grad(link,model,info,lch,mode=mode)
                value.update(mode=mode,forward_max_difference=float((other-u).abs().max()))
                assert value['forward_max_difference']<2e-4
                counter.append(value)
            horizons=[]
            for T in (5,10,15,20):
                v,_,_=probe_grad(link,model,info,lch,T=T);horizons.append({'T':T,**v})
            components=[]
            for t in range(17,21):
                model.zero_grad(set_to_none=True)
                _,h,tr=traced(link,model,lch)
                target=torch.tensor(info,device=link.device,dtype=lch.dtype)
                component=F.binary_cross_entropy_with_logits(-h[t-17][:,:link.b],target)
                component.backward()
                components.append({'supervised_t':t,'unweighted_bce':float(component.detach()),
                                   'gradient_norm':float(vector(model).norm()),'head_bias_gradient':float(model.head.bias.grad),
                                   'adjoints':adjoints(tr)})
            # Per-frame gradients must sum (with 1/batch) to the batch mean gradient.
            per=[];summed=torch.zeros_like(gref)
            for i in range(8):
                model.zero_grad(set_to_none=True)
                _,h,_=link.decode(lch[i:i+1],controller=model,history=True)
                l=training_loss(link,h,info[i:i+1],100);l.backward();g=vector(model).clone();summed+=g/8
                per.append({'sample':i,'loss':float(l.detach()),'gradient_norm':float(g.norm()),'head_bias_gradient':float(model.head.bias.grad)})
            alignment=float(summed.norm()/(sum(p['gradient_norm'] for p in per)/8))
            dump(f'bg{bg}-detail-{selected}.json',{'bg':bg,'step_before':selected,'baseline':baseline,'traced_forward_max_difference':difference,
                    'traced_gradient_max_difference':gdiff,'counterfactuals':counter,'horizons':horizons,
                    'loss_components':components,'per_frame':per,'per_frame_average_vs_batch_gradient_max_difference':float((summed-gref).abs().max()),
                    'per_frame_gradient_alignment_ratio':alignment})
            emit('detail',bg=bg,step=selected,gradient=baseline['gradient_norm'],
                 detach_state=counter[0]['gradient_norm'],detach_messages=counter[1]['gradient_norm'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['replay','profiles','detail']);args=parser.parse_args()
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    if args.mode=='replay':
        OUT.mkdir(exist_ok=False)
        env=environment(OUT,args)
        env['source_sha256'][str(Path(__file__).resolve())]=sha256(Path(__file__).resolve())
        dump('environment.json',env)
        dump('run_spec.json',{'scope':'gradient diagnosis','formal_training':False,'replay_steps_per_config':100,
             'replay_lr':1e-3,'replay_clip_norm':1.0,'replay_batch':8,'T':20,'seed':17,
             'diagnostic_controls':'detach_state / detach_messages backward-only, same forward; never optimized',
             'frozen_models':'original initial/final checkpoints; no optimizer updates in probes'})
    try:
        {'replay':replay,'profiles':profiles,'detail':detail}[args.mode]()
        emit('completed',mode=args.mode)
    except Exception:
        dump(args.mode+'-failure.json',{'traceback':traceback.format_exc()});raise


if __name__=='__main__':main()
