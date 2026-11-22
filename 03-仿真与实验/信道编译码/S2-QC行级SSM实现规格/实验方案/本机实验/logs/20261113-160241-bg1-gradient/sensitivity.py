"""Finite differences of the specified surrogate, and graph/damping controls."""
import argparse
import copy
import json
from pathlib import Path
import time
from types import MethodType

import numpy as np
import torch
from torch.nn import functional as F

from diagnose import (LOG, LOCAL, OUT, emit, dump, append, config, get_model, input_batch,
                      NRLink, samples, traced, training_loss, build, vector, adjoints)


def double_bce(link, history, info):
    labels=torch.as_tensor(info,device=link.device,dtype=torch.float64)
    return sum(w/15*F.binary_cross_entropy_with_logits(-u[:,:link.b],labels)
               for w,u in zip((1,2,4,8),history))


def typed_features(self, u, q, r, dr, prev_violation, t):
    # Same feature definitions; production's explicit FP32 condition accumulation
    # is changed only here to the diagnostic input dtype to permit FP64 checks.
    violation,coverage=self.masked_violation(u)
    f=torch.stack((violation,violation-prev_violation,self.row_mean(q.abs())/20,
                   self.row_mean(r.abs())/20,dr/40,
                   self.row_mean((1-self.gather(u.clamp(-20,20)).abs()/2).clamp_min(0)),
                   torch.full_like(violation,t/20),coverage),dim=-1)
    counts=self.nu[self.var];cond=[]
    for val in ((counts==0)&~self.filler[self.var],self.filler[self.var],
                (counts>=2)&~self.filler[self.var],torch.log1p(counts.clamp_max(4).float())/np.log(5)):
        total=u.new_zeros(self.rows)
        total.index_add_(0,self.edge_row,val.to(u.dtype).mean(-1))
        cond.append((total/torch.bincount(self.edge_row,minlength=self.rows))[None].expand(len(u),-1))
    zero=torch.zeros_like(violation)
    c=torch.stack((violation,violation-prev_violation,zero,zero,*cond),dim=-1)
    return f.detach(),c.detach(),violation.detach()


def finite_difference():
    for bg in (2,1):
        detail_files=sorted(OUT.glob(f'bg{bg}-detail-*.json'))
        selected=max(json.loads(p.read_text())['step_before'] for p in detail_files)
        # Trusted bundle produced by this diagnostic, including a NumPy info array.
        saved=torch.load(OUT/f'bg{bg}-detail-input-{selected}.pt',weights_only=False)
        link=NRLink(config(bg))
        link.features=MethodType(typed_features,link)
        model=get_model(link).double();model.load_state_dict(saved['model'])
        lch=saved['lch'].to(device=link.device,dtype=torch.float64);info=saved['info']
        _,_,base=traced(link,model,lch)
        frozen=[r['features'] for r in base]
        model.zero_grad(set_to_none=True)
        _,hist,_=traced(link,model,lch,frozen=frozen,store=False)
        loss=double_bce(link,hist,info);loss.backward()
        ad=float(model.head.bias.grad.detach())
        original=model.head.bias.detach().clone()
        rows=[]
        for epsilon in (1e-2,1e-3,1e-4,1e-5,1e-6,1e-7,1e-8,1e-9):
            for freeze in (True,False):
                losses=[]
                with torch.no_grad():
                    for direction in (-1,1):
                        model.head.bias.copy_(original+direction*epsilon)
                        _,h,_=traced(link,model,lch,frozen=frozen if freeze else None,store=False)
                        losses.append(float(double_bce(link,h,info)))
                    model.head.bias.copy_(original)
                fd=(losses[1]-losses[0])/(2*epsilon)
                rows.append({'epsilon':epsilon,'features_frozen':freeze,'central_difference':fd,
                             'forward_difference':(losses[1]-float(loss.detach()))/epsilon,
                             'backward_difference':(float(loss.detach())-losses[0])/epsilon,
                             'relative_error_vs_surrogate_autograd':abs(fd-ad)/max(abs(ad),1e-20)})
        dump(f'bg{bg}-finite-difference.json',{'bg':bg,'step_before':selected,'precision':'FP64 diagnosis only; training remains FP32',
             'parameter':'head.bias','loss':float(loss.detach()),'surrogate_autograd':ad,'differences':rows,
             'interpretation':'frozen features match detach-statistics proxy gradient; recomputed features differentiate the full closed loop and need not agree with the protocol proxy. Finite differences at large epsilon may cross min/sign/clip active branches.'})
        emit('finite_difference',bg=bg,step=selected,autograd=ad,small_epsilon=rows[-2])


def graph_controls():
    # Same R1/2 manifest family, BCE mean over B; independent eta leaves remove SSM parameterization.
    configs=[c for c in build()['ldpc_configs'] if c['target_rate_label']=='1/2' and
             c['B_including_tb_crc'] in (512,1024,2048,4096,8448)]
    for cfg in configs:
        link=NRLink(cfg);model=get_model(link)
        rows=np.bincount(link.rr,minlength=link.rows);cols=np.bincount(link.cc,minlength=link.cols)
        for shard in range(4):
            _,_,info,lch=samples(link,'gradient-graph-control',8,1.0,17,shard)
            _,h,tr=traced(link,model,lch,independent_eta=True)
            loss=training_loss(link,h,info,100);loss.backward()
            grads=torch.stack([r['eta'].grad for r in tr])
            append('graph_controls.jsonl',{'config_id':cfg['id'],'bg':link.bg,'B':link.b,'Z':link.z,'snr_db':1.0,'shard':shard,
              'loss':float(loss.detach()),'independent_eta_gradient_norm':float(grads.norm()),
              'independent_eta_gradient_rms':float(grads.square().mean().sqrt()),
              'shared_scalar_eta_gradient':float(grads.sum()),'eta_grad_by_iteration':adjoints(tr),
              'row_degree_min_mean_max':[int(rows.min()),float(rows.mean()),int(rows.max())],
              'col_degree_min_mean_max':[int(cols.min()),float(cols.mean()),int(cols.max())],
              'constant_eta':0.05,'BCE_reduction':'mean over batch and B including CRC, excluding filler',
              'note':'diagnostic no learning; same nominal rate and SNR, graph/length/error regime remain different'})
        emit('graph_control',config=cfg['id'])


def branch_signature(link, trace):
    signatures=[]
    for row in trace:
        q=row['q'];indices=[];gaps=[]
        for _,edges in link.buckets:
            values,which=q[:,edges,:].abs().topk(2,dim=2,largest=False,sorted=True)
            indices.append(which[:,:,0].flatten());gaps.append((values[:,:,1]-values[:,:,0]).flatten())
        signatures.append({'t':row['t'],'negative':(q<0).flatten(),'clip':(q.abs()>=20).flatten(),
                           'min_index':torch.cat(indices),'min_gap':torch.cat(gaps)})
    return signatures


def branch_audit():
    for bg,selected in ((2,16),(1,5)):
        saved=torch.load(OUT/f'bg{bg}-detail-input-{selected}.pt',weights_only=False)
        link=NRLink(config(bg));link.features=MethodType(typed_features,link)
        model=get_model(link).double();model.load_state_dict(saved['model'])
        lch=saved['lch'].to(device=link.device,dtype=torch.float64)
        with torch.no_grad():
            _,_,baseline=traced(link,model,lch)
            frozen=[r['features'] for r in baseline];base=branch_signature(link,baseline)
            orig=model.head.bias.detach().clone()
            records=[]
            for epsilon in (1e-3,1e-5,1e-7,1e-9):
                for direction in (-1,1):
                    model.head.bias.copy_(orig+direction*epsilon)
                    _,_,trace=traced(link,model,lch,frozen=frozen)
                    sig=branch_signature(link,trace);per_t=[]
                    for a,b in zip(base,sig):
                        per_t.append({'t':a['t'],'min_index_changed':int((a['min_index']!=b['min_index']).sum()),
                             'min_count':a['min_index'].numel(),'q_sign_changed':int((a['negative']!=b['negative']).sum()),
                             'q_clip_status_changed':int((a['clip']!=b['clip']).sum()),'q_count':a['negative'].numel()})
                    records.append({'epsilon':epsilon,'direction':direction,'per_iteration':per_t,
                        'min_index_changed_total':sum(r['min_index_changed'] for r in per_t),
                        'q_sign_changed_total':sum(r['q_sign_changed'] for r in per_t),
                        'q_clip_status_changed_total':sum(r['q_clip_status_changed'] for r in per_t)})
            model.head.bias.copy_(orig)
        dump(f'bg{bg}-branch-audit.json',{'bg':bg,'step_before':selected,'precision':'FP64','features_frozen':True,
             'records':records,'baseline_min_gap_by_iteration':[{'t':r['t'],
                 'fraction_exact_tie':float((r['min_gap']==0).double().mean()),
                 'fraction_gap_le_1e-7':float((r['min_gap']<=1e-7).double().mean())} for r in base]})
        emit('branch_audit',bg=bg,records=[{k:v for k,v in r.items() if k!='per_iteration'} for r in records])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['finite-difference','graph-controls','branch-audit']);a=p.parse_args()
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    {'finite-difference':finite_difference,'graph-controls':graph_controls,'branch-audit':branch_audit}[a.mode]()
    emit('completed',mode=a.mode)
