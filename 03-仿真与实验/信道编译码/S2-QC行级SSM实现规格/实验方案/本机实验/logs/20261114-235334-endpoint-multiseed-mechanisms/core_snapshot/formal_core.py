"""FP32 protocol-v1 training primitives, stateless samples and CUDA graph replay."""
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np
import torch
from torch.nn import functional as F

from nr_link import NRLink, sha256
from ssm import RowSSM

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from generate_manifest import stable_seed,build

TRAIN_SPLIT='S2-formal-train-v1'
VALID_SPLIT='S2-formal-validation-v1'
TOTAL=50000
BATCH=64


def save_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.tmp-{os.getpid()}')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    with temp.open('rb') as f:os.fsync(f.fileno())
    temp.replace(path)


def configure():
    assert os.environ.get('CUBLAS_WORKSPACE_CONFIG')==':4096:8','set CUBLAS_WORKSPACE_CONFIG before importing torch'
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.use_deterministic_algorithms(True)
    assert torch.cuda.is_available()


def lr_at(step):
    if not 0<=step<=TOTAL:raise ValueError(step)
    if step<=1000:return 1e-3*step/1000
    return 1e-4+.5*(1e-3-1e-4)*(1+math.cos(math.pi*(step-1000)/(TOTAL-1000)))


def syndrome_weight(step):return .02*min(1.,max(0.,(step-5000)/5000))


class CapturableProduct(torch.autograd.Function):
    """FP32 prod(dim2), with PyTorch2.9.1's exact two backward branches.

    FunctionsManual.cpp prod_backward checks total_zeros.sum().item(), which
    cannot be captured. Select the same division/exclusive-cumprod branch on
    the device instead. Forward and both arithmetic branches are unchanged.
    Only first-order training derivatives are required by this runner.
    """
    @staticmethod
    def forward(ctx,x):
        result=x.prod(2);ctx.save_for_backward(x,result)
        return result

    @staticmethod
    def backward(ctx,grad):
        x,result=ctx.saved_tensors;grad=grad.unsqueeze(2)
        ones=torch.ones_like(x[:,:,:1])
        normal=torch.cat((ones,x[:,:,:-1]),2).cumprod(2)
        reverse=torch.cat((ones,x[:,:,1:].flip((2,))),2).cumprod(2).flip((2,))
        safe=grad*(normal*reverse)
        fast=grad*(result.unsqueeze(2)/x)
        return torch.where((x==0).any(),safe,fast)


def loss_parts(link,history,labels,coefficient):
    bce=sum(weight/15*F.binary_cross_entropy_with_logits(-u[:,:link.b],labels)
            for weight,u in zip((1,2,4,8),history))
    soft=torch.tanh(link.gather(history[-1])/2)
    products=[CapturableProduct.apply(soft[:,edges]).flatten(1) for _,edges in link.buckets]
    syndrome=(1-torch.cat(products,dim=1)).mean()/2
    return bce+coefficient*syndrome,bce,syndrome


def frozen_config(path,cid):
    path=Path(path).resolve();data=json.loads(path.read_text())
    assert sha256(path)==path.with_suffix('.sha256').read_text().split()[0]
    manifest=json.loads((ROOT.parent/'experiment_manifest.json').read_text())
    assert manifest==build() and sha256(ROOT.parent/'experiment_manifest.json')==data['manifest_sha256']
    calibration=path.parent/'calibration/summary.json'
    assert sha256(calibration)==data['calibration_summary_sha256']
    f=next(c for c in data['configs'] if c['config_id']==cid)
    cfg=next(c for c in manifest['ldpc_configs'] if c['id']==cid)
    assert f['full_config']==cfg
    assert len(f['validation_snr_db'])==5
    return f,cfg


def source_hashes():
    paths=[ROOT/n for n in ('formal_core.py','train_formal.py','nr_link.py','ssm.py')]
    paths += [ROOT.parent/'experiment_manifest.json',ROOT.parent/'README.md']
    return {str(p):sha256(p) for p in paths}


def parameter_vector(model):return torch.cat([p.detach().flatten() for p in model.parameters()])
def parameter_hash(model):return hashlib.sha256(parameter_vector(model).cpu().numpy().tobytes()).hexdigest()


def optimizer_for(model):
    decay=[];no_decay=[]
    for name,p in model.named_parameters():
        (no_decay if name.endswith('bias') or 'norm' in name or name=='theta' else decay).append(p)
    return torch.optim.AdamW([{'params':decay,'weight_decay':1e-4},
                              {'params':no_decay,'weight_decay':0.}],lr=0.,betas=(.9,.999),eps=1e-8,foreach=False)


def training_arrays(link,seed,step,bounds,begin=0,count=BATCH):
    """A frame owns3 independent PCG64 streams, regardless of batching."""
    payload=np.empty((count,link.a),dtype=np.uint8)
    noise=np.empty((count,link.etx//2,2),dtype=np.float32)
    snrs=np.empty(count,dtype=np.float64)
    for j,index in enumerate(range(begin,begin+count)):
        key=f'{TRAIN_SPLIT}/seed-{seed}/step-{step}/sample-{index}'
        def generator(stream):return np.random.default_rng(stable_seed(link.cfg['id'],0.,0,key+'/'+stream))
        payload[j]=generator('bits').integers(0,2,link.a,dtype=np.uint8)
        noise[j]=generator('noise').standard_normal((link.etx//2,2)).astype(np.float32)
        snrs[j]=generator('snr').uniform(*bounds)
    return payload,noise,snrs


def channel_arrays(link,payload,noise,snrs):
    cw,info=link.encode(payload)
    bits=torch.tensor(cw[:,link.tx_np],device=link.device,dtype=torch.float32)
    symbols=(1-2*bits).reshape(len(bits),-1,2)/np.sqrt(2)
    n0=torch.as_tensor(1/(link.a/link.etx*2*10**(snrs/10)),device=link.device,dtype=torch.float32)
    if n0.ndim==1:n0=n0[:,None,None]
    llr=(2*np.sqrt(2)*(symbols+torch.tensor(noise,device=link.device)*torch.sqrt(n0/2))/n0).flatten(1)
    return cw,info,link.recover(llr)


def train_batch(link,seed,step,bounds):
    payload,noise,snrs=training_arrays(link,seed,step,bounds)
    digest=hashlib.sha256(payload.tobytes()+noise.tobytes()+snrs.tobytes()).hexdigest()
    _,info,lch=channel_arrays(link,payload,noise,snrs)
    return info,lch,snrs,digest


def validation_shard(link,snr,shard,total):
    # total625 and3125 must share the same prefix (verified before training).
    bits=np.random.default_rng(stable_seed(link.cfg['id'],snr,shard,VALID_SPLIT+'/bits'))
    rng=np.random.default_rng(stable_seed(link.cfg['id'],snr,shard,VALID_SPLIT+'/noise'))
    payload=bits.integers(0,2,(total,link.a),dtype=np.uint8)
    cw,info=link.encode(payload)
    lch,_=link.channel(cw,float(snr),rng)
    return payload,info,lch


class TrainingEngine:
    def __init__(self,link,model,alpha,microbatch=64,backend='cuda-graph'):
        assert BATCH%microbatch==0
        self.link=link;self.model=model;self.alpha=alpha;self.batch=microbatch;self.backend=backend
        self.input=torch.zeros((microbatch,link.n),device=link.device).masked_fill(link.filler,20)
        self.labels=torch.zeros((microbatch,link.b),device=link.device)
        self.coefficient=torch.tensor(0.,device=link.device)
        self.graph=None
        if backend=='cuda-graph':
            stream=torch.cuda.Stream();stream.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(stream):
                for _ in range(2):
                    model.zero_grad(set_to_none=True)
                    _,h,_=link.decode(self.input,alpha=alpha,controller=model,history=True)
                    loss_parts(link,h,self.labels,self.coefficient)[0].backward()
            torch.cuda.current_stream().wait_stream(stream);torch.cuda.synchronize()
            model.zero_grad(set_to_none=True)
            self.graph=torch.cuda.CUDAGraph()
            with torch.cuda.graph(self.graph):
                self.output,h,self.state=link.decode(self.input,alpha=alpha,controller=model,history=True)
                self.loss,self.bce,self.syndrome=loss_parts(link,h,self.labels,self.coefficient)
                self.loss.backward()
            torch.cuda.synchronize()

    def backward(self,lch,labels,step):
        self.input.copy_(lch);self.labels.copy_(labels);self.coefficient.fill_(syndrome_weight(step))
        if self.graph is not None:self.graph.replay()
        else:
            self.model.zero_grad(set_to_none=True)
            self.output,h,self.state=self.link.decode(self.input,alpha=self.alpha,controller=self.model,history=True)
            self.loss,self.bce,self.syndrome=loss_parts(self.link,h,self.labels,self.coefficient)
            self.loss.backward()
        return self.loss,self.bce,self.syndrome,self.state

    def step(self,optimizer,info,lch,step):
        labels=torch.tensor(info,device=self.link.device,dtype=torch.float32)
        aggregates=lch.new_zeros(4)
        accumulated=None
        for begin in range(0,BATCH,self.batch):
            end=begin+self.batch
            loss,bce,syn,state=self.backward(lch[begin:end],labels[begin:end],step)
            aggregates[:3]+=torch.stack((loss.detach(),bce.detach(),syn.detach()))*(self.batch/BATCH)
            aggregates[3]=torch.maximum(aggregates[3],state.detach())
            if self.batch!=BATCH:
                if accumulated is None:accumulated=[p.grad.detach().clone()*(self.batch/BATCH) for p in self.model.parameters()]
                else:
                    for a,p in zip(accumulated,self.model.parameters()):a.add_(p.grad,alpha=self.batch/BATCH)
        if accumulated is not None:
            for p,a in zip(self.model.parameters(),accumulated):p.grad.copy_(a)
        gradients=torch.cat([p.grad.flatten() for p in self.model.parameters()])
        assert torch.isfinite(aggregates).all() and torch.isfinite(gradients).all(),'nonfinite loss/gradient'
        assert float(aggregates[3])<=1.00001,'SSM state bound'
        head_sq=sum(p.grad.square().sum() for n,p in self.model.named_parameters() if n.startswith('head.'))
        share=float(head_sq/gradients.square().sum().clamp_min(1e-30))
        norm=float(torch.nn.utils.clip_grad_norm_(self.model.parameters(),1.,foreach=False))
        after=float(torch.linalg.vector_norm(torch.cat([p.grad.flatten() for p in self.model.parameters()])))
        assert np.isfinite(norm) and np.isfinite(after) and after<=1.00001,(norm,after)
        lr=lr_at(step)
        for group in optimizer.param_groups:group['lr']=lr
        before=parameter_vector(self.model).clone();optimizer.step();updated=parameter_vector(self.model)
        assert torch.isfinite(updated).all(),'nonfinite parameters'
        values=aggregates.cpu().tolist()
        return {'loss':values[0],'information_bce_last4':values[1],'soft_syndrome_loss':values[2],
                'syndrome_weight':syndrome_weight(step),'state_abs_max':values[3],'lr':lr,
                'gradient_norm_before_clip':norm,'gradient_norm_after_clip':after,'gradient_clipped':norm>1.,
                'clip_coefficient':min(1.,1/(norm+1e-6)),'head_gradient_squared_fraction':share,
                'parameter_update_l2':float(torch.linalg.vector_norm(updated-before)),
                'parameter_norm_l2':float(torch.linalg.vector_norm(updated))}


class InferenceEngine:
    def __init__(self,link,model,alpha,batch=125):
        self.batch=batch
        self.input=torch.zeros((batch,link.n),device=link.device).masked_fill(link.filler,20)
        stream=torch.cuda.Stream();stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream),torch.no_grad():
            for _ in range(2):link.decode(self.input,alpha=alpha,controller=model)
        torch.cuda.current_stream().wait_stream(stream);torch.cuda.synchronize()
        self.graph=torch.cuda.CUDAGraph()
        with torch.no_grad(),torch.cuda.graph(self.graph):
            self.output,_,self.state=link.decode(self.input,alpha=alpha,controller=model)
        torch.cuda.synchronize()

    def __call__(self,lch):
        assert len(lch)<=self.batch
        self.input[:len(lch)].copy_(lch);self.graph.replay()
        return self.output[:len(lch)]


def rng_state():
    s=np.random.get_state()
    return {'python':random.getstate(),'numpy':(s[0],s[1].tolist(),s[2],s[3],s[4]),
            'torch_cpu':torch.get_rng_state(),'torch_cuda':torch.cuda.get_rng_state_all()}


def restore_rng(state):
    random.setstate(state['python']);s=state['numpy']
    np.random.set_state((s[0],np.array(s[1],dtype=np.uint32),s[2],s[3],s[4]))
    torch.set_rng_state(state['torch_cpu'].cpu())
    torch.cuda.set_rng_state_all([s.cpu() for s in state['torch_cuda']])


def save_checkpoint(out,model,optimizer,step,contract):
    directory=Path(out)/'checkpoints';directory.mkdir(exist_ok=True)
    path=directory/f'step-{step:05d}.pt'
    assert not path.exists(),f'immutable checkpoint already exists: {path}'
    data={'model':model.state_dict(),'optimizer':optimizer.state_dict(),'global_step':step,
          'observations':step*BATCH,'schedule':{'last_step':step,'total_steps':TOTAL,'warmup':1000,
                                               'next_lr':lr_at(step+1) if step<TOTAL else None},
          'rng':rng_state(),'contract':contract,'parameter_sha256':parameter_hash(model)}
    temporary=path.with_suffix(f'.tmp-{os.getpid()}');torch.save(data,temporary)
    with temporary.open('rb') as f:os.fsync(f.fileno())
    temporary.replace(path);digest=sha256(path)
    path.with_suffix('.pt.sha256').write_text(digest+'  '+path.name+'\n')
    save_json(Path(out)/'latest_checkpoint.json',{'path':str(path.resolve()),'sha256':digest,'global_step':step})
    return path


def load_checkpoint(path,model,optimizer,contract):
    path=Path(path)
    assert sha256(path)==path.with_suffix('.pt.sha256').read_text().split()[0]
    data=torch.load(path,weights_only=True,map_location='cpu')
    assert data['contract']==contract,'checkpoint contract/source/data mismatch'
    step=data['global_step'];assert data['observations']==step*BATCH
    assert data['schedule']=={'last_step':step,'total_steps':TOTAL,'warmup':1000,'next_lr':lr_at(step+1) if step<TOTAL else None}
    model.load_state_dict(data['model']);optimizer.load_state_dict(data['optimizer'])
    assert parameter_hash(model)==data['parameter_sha256']
    assert all(g['lr']==lr_at(step) for g in optimizer.param_groups)
    return data


def make_contract(frozen_path,frozen,link,seed,backend,microbatch):
    return {'protocol':'S2-v1','config_id':link.cfg['id'],'seed':seed,'total_steps':TOTAL,'effective_batch':BATCH,
            'microbatch':microbatch,'backend':backend,'dtype':'FP32','TF32':False,'AMP':False,'deterministic':True,
            'alpha':frozen['alpha'],'snr_range_db':frozen['training_snr_range_db'],
            'validation_snr_db':frozen['validation_snr_db'],'training_split':TRAIN_SPLIT,'validation_split':VALID_SPLIT,
            'frozen_inputs_sha256':sha256(Path(frozen_path)), 'source_sha256':source_hashes(),
            'index_sha256':link.index_hash,'shift_sha256':link.shift_hash,
            'packages':{p:importlib.metadata.version(p) for p in ('torch','numpy','scipy','sionna','py3gpp')},
            'optimizer':'AdamW foreach=False betas(.9,.999) eps1e-8, protocol decay exclusions, clip1',
            'training_payload':'random with real TB CRC','teacher':False,'T':20}


def post_checks(link,model,alpha):
    payload,noise,snrs=training_arrays(link,17,0,(.5,1.5),count=8)
    cw,_,lch=channel_arrays(link,payload,noise,snrs)
    sign=torch.tensor(1-2*cw.astype(np.float32),device=link.device)
    with torch.no_grad():
        base=(lch*4).clamp(-20,20).masked_fill(link.filler,20)
        u,_,state=link.decode(base,alpha=alpha,controller=model)
        signed,_,_=link.decode(base*sign,alpha=alpha,controller=model)
        error=float((signed-u*sign).abs().max())
        assert error<2e-4 and float(state)<=1.00001,(error,state)
        clean,_=link.channel(cw,0.,np.random.default_rng(19),noiseless=True)
        decoded,_,_=link.decode(clean,alpha=alpha,controller=model)
        errors=int(np.any((decoded[:,:link.a]<0).cpu().numpy()!=payload,axis=1).sum())
        rejected=int((~link.accepted(decoded)).sum())
        assert errors==rejected==0,(errors,rejected)
    return {'frames':len(payload),'symmetry_max_abs_error':error,'state_abs_max':float(state),
            'noiseless_payload_errors':errors,'noiseless_rejected':rejected}


def evaluate(out,link,model,alpha,snrs,step,frames=20000):
    """Immutable frame records; 32 shared shards, independent of training/pilot.

    100k extends each 625-frame shard to3125 without changing its prefix.
    Returned scores use final-iteration BCE over B including CRC, no filler.
    """
    from protocol_checks import wilson,zero_error_upper
    assert frames in (20000,100000)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    identity={'config_id':link.cfg['id'],'model_parameter_sha256':parameter_hash(model) if model is not None else None,
              'alpha':alpha,'step':step,'frames_per_snr':frames,'split':VALID_SPLIT,
              'source_sha256':source_hashes(),'snr_db':snrs,'T':20,'early_stop':False,'fallback':False}
    summary_path=out/'summary.json'
    if summary_path.exists():
        saved=json.loads(summary_path.read_text());assert saved['identity']==identity
        for file,digest in saved['artifacts_sha256'].items():assert sha256(out/file)==digest
        return saved
    started=time.perf_counter();engine=InferenceEngine(link,model,alpha)
    rows=[];artifacts={};total=frames//32
    for snr in snrs:
        shards=[]
        for shard in range(32):
            name=f'snr-{snr:.4f}-shard-{shard:02d}.npz';path=out/name
            if path.exists():
                with np.load(path,allow_pickle=False) as saved:
                    assert str(saved['identity'])==json.dumps(identity,sort_keys=True)
                    bce=saved['bce'];biterrors=saved['bit_errors'];rejected=saved['rejected'];crc_ok=saved['crc_ok']
                    assert len(bce)==total
            else:
                payload,info,lch=validation_shard(link,snr,shard,total)
                bces=[];errors=[];rejects=[];crcs=[]
                with torch.no_grad():
                    for begin in range(0,total,engine.batch):
                        end=min(total,begin+engine.batch);u=engine(lch[begin:end])
                        labels=torch.tensor(info[begin:end],device=link.device,dtype=torch.float32)
                        bces.append(F.binary_cross_entropy_with_logits(-u[:,:link.b],labels,reduction='none').mean(1).cpu().numpy())
                        bits=(u[:,:link.b]<0).cpu().numpy().astype(np.uint8)
                        from nr_link import crc_attach
                        crcs.append((bits==crc_attach(bits[:,:link.a],link.cfg['tb_crc'])).all(1))
                        errors.append((bits[:,:link.a]!=payload[begin:end]).sum(1))
                        rejects.append((~link.accepted(u)).cpu().numpy())
                bce=np.concatenate(bces);biterrors=np.concatenate(errors);rejected=np.concatenate(rejects);crc_ok=np.concatenate(crcs)
                temporary=path.with_suffix(f'.tmp-{os.getpid()}.npz')
                np.savez_compressed(temporary,bce=bce,bit_errors=biterrors,rejected=rejected,crc_ok=crc_ok,
                                    identity=json.dumps(identity,sort_keys=True))
                temporary.replace(path)
            if frames==100000:
                prefix=out.parent.parent/'20k'/out.name/name
                if prefix.exists():
                    with np.load(prefix,allow_pickle=False) as old:
                        for key,value in [('bce',bce),('bit_errors',biterrors),('rejected',rejected),('crc_ok',crc_ok)]:
                            assert np.array_equal(old[key],value[:625]),f'validation extension prefix differs {key}'
            wrong=biterrors>0
            shards.append({'shard':shard,'frames':total,'bce_sum':float(bce.astype(np.float64).sum()),
                           'payload_frame_errors':int(wrong.sum()),'payload_bit_errors':int(biterrors.sum()),
                           'rejected':int(rejected.sum()),'service_frame_errors':int((wrong|rejected).sum()),
                           'accepted_wrong':int((wrong&~rejected).sum()),'crc_passed_wrong':int((wrong&crc_ok).sum())})
            artifacts[name]=sha256(path)
        counts={key:sum(s[key] for s in shards) for key in shards[0] if key not in ('shard','frames')}
        row={'snr_db':snr,'frames':frames,**counts,'information_bce':counts['bce_sum']/frames,
             'payload_bler':counts['payload_frame_errors']/frames,
             'bler_ci95':wilson(counts['payload_frame_errors'],frames),'shards':shards}
        if not counts['payload_frame_errors']:row['zero_error_one_sided95_upper']=zero_error_upper(frames)
        rows.append(row)
        print(json.dumps({'event':'validation_snr','step':step,'frames':frames,'snr':snr,
                          'bce':row['information_bce'],'errors':row['payload_frame_errors']},ensure_ascii=False),flush=True)
    result={'status':'passed','identity':identity,'points':rows,
            'mean_information_bce':float(np.mean([r['information_bce'] for r in rows])),
            'elapsed_seconds':time.perf_counter()-started,'artifacts_sha256':artifacts,
            'purpose':'checkpoint-selection validation, not independent formal BLER test'}
    save_json(summary_path,result)
    del engine
    return result
