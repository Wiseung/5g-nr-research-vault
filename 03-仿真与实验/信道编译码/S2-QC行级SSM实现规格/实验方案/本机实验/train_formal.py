"""Protocol-v1 formal runner: 50k x64; immutable checkpoints and exact resume."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time
import traceback
from zoneinfo import ZoneInfo

import numpy as np
import torch

from formal_core import (ROOT,BATCH,TOTAL,TrainingEngine,configure,evaluate,frozen_config,
    load_checkpoint,lr_at,make_contract,optimizer_for,parameter_hash,post_checks,
    restore_rng,save_checkpoint,save_json,source_hashes,train_batch)
from nr_link import NRLink,sha256
from run_local import environment
from ssm import RowSSM


def emit(out,event,**data):
    row={'time':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'event':event,**data}
    with (out/'events.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(json.dumps(row,ensure_ascii=False),flush=True)


def proof_gate(path,frozen):
    proof=json.loads(Path(path).read_text())
    assert proof['status']=='passed'
    assert proof['source_sha256']==source_hashes(),'unverified formal source change'
    assert proof['frozen_inputs_sha256']==sha256(Path(frozen))
    assert set(proof['configs'])=={'ldpc_B1024_R1-2_Q2','ldpc_B4096_R1-2_Q2'}
    assert all(v['status']=='passed' for v in proof['configs'].values())
    return sha256(Path(path))


def history(out,step):
    rows={}
    for path in sorted((out/'segments').glob('*/train_history.jsonl')):
        for line in path.read_text().splitlines():
            row=json.loads(line)
            if row['step']<=step:rows[row['step']]=row
    assert sorted(rows)==list(range(1,step+1)),'missing committed training history'
    return list(rows.values())


def final_selection(out,link,model,optimizer,contract,frozen):
    candidates=[]
    for step in range(1000,TOTAL+1,1000):
        path=out/f'validation/20k/step-{step:05d}/summary.json'
        data=json.loads(path.read_text())
        candidates.append({'step':step,'mean_information_bce':data['mean_information_bce']})
    candidates.sort(key=lambda r:(r['mean_information_bce'],r['step']))
    chosen=candidates[:2]
    save_json(out/'validation/top2_frozen.json',{'rule':'mean information BCE then earlier step',
              'candidates':candidates,'top2':chosen,'frozen_before_extension':True})
    extended=[]
    for candidate in chosen:
        step=candidate['step'];load_checkpoint(out/f'checkpoints/step-{step:05d}.pt',model,optimizer,contract)
        metrics=evaluate(out/f'validation/100k/step-{step:05d}',link,model,frozen['alpha'],
                         frozen['validation_snr_db'],step,100000)
        extended.append({'step':step,'mean_information_bce':metrics['mean_information_bce'],
                         'model_parameter_sha256':parameter_hash(model)})
    baseline=evaluate(out/'validation/100k/NMS',link,None,frozen['alpha'],frozen['validation_snr_db'],None,100000)
    extended.sort(key=lambda r:(r['mean_information_bce'],r['step']))
    result={'status':'passed','candidates':extended,'selected':extended[0],
            'NMS_mean_information_bce':baseline['mean_information_bce'],
            'scope':'selection validation; no independent test or formal BLER improvement claim'}
    save_json(out/'checkpoint_selection.json',result)
    load_checkpoint(out/f'checkpoints/step-{TOTAL:05d}.pt',model,optimizer,contract)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--config-id',required=True,choices=['ldpc_B1024_R1-2_Q2','ldpc_B4096_R1-2_Q2'])
    parser.add_argument('--frozen',required=True);parser.add_argument('--proof',required=True)
    parser.add_argument('--seed',type=int,default=17);parser.add_argument('--batch',type=int,default=64)
    parser.add_argument('--microbatch',type=int,default=64)
    parser.add_argument('--backend',choices=['cuda-graph','eager'],default='cuda-graph')
    parser.add_argument('--stop-after',type=int,default=TOTAL)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.batch!=64 or not 1<=args.stop_after<=TOTAL or 64%args.microbatch:
        parser.error('protocol requires batch64, stop1..50000, microbatch divides64')
    configure();torch.manual_seed(args.seed);np.random.seed(args.seed)
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    if not args.resume and any(out.iterdir()):parser.error('new output must be empty')
    if args.resume and not (out/'latest_checkpoint.json').exists():parser.error('missing resume checkpoint')
    proof_sha=proof_gate(args.proof,args.frozen)
    frozen,cfg=frozen_config(args.frozen,args.config_id)
    link=NRLink(cfg);model=RowSSM(link.rows).to(link.device);optimizer=optimizer_for(model)
    contract=make_contract(args.frozen,frozen,link,args.seed,args.backend,args.microbatch)
    if args.resume:assert json.loads((out/'contract.json').read_text())==contract
    else:
        save_json(out/'contract.json',contract)
        env=environment(out,args)
        env.update(source_sha256=source_hashes(),deterministic=True,CUBLAS_WORKSPACE_CONFIG=os.environ['CUBLAS_WORKSPACE_CONFIG'])
        save_json(out/'environment.json',env)
        save_json(out/'verification_gate.json',{'path':str(Path(args.proof).resolve()),'sha256':proof_sha})
    segment_id=datetime.now().strftime('%Y%m%d-%H%M%S')+f'-{os.getpid()}'
    segment=out/'segments'/segment_id;segment.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();step=0
    save_json(segment/'invocation.json',{'argv':sys.argv,'pid':os.getpid(),'session_id':os.getsid(0),
              'cwd':str(Path.cwd()),'resume':args.resume,'stop_after':args.stop_after})
    try:
        emit(out,'building_training_engine',backend=args.backend,microbatch=args.microbatch)
        engine=TrainingEngine(link,model,frozen['alpha'],args.microbatch,args.backend)
        if args.resume:
            latest=json.loads((out/'latest_checkpoint.json').read_text())
            data=load_checkpoint(latest['path'],model,optimizer,contract)
            assert sha256(Path(latest['path']))==latest['sha256']
            step=data['global_step'];restore_rng(data['rng'])
            emit(out,'resumed',global_step=step,next_lr=lr_at(step+1) if step<TOTAL else None,
                 checkpoint=latest['path'],parameter_sha256=parameter_hash(model))
        else:
            save_checkpoint(out,model,optimizer,0,contract)
        assert step<=args.stop_after
        # Validation identities bind scores and frame artifacts to exact source and parameters.
        if step==0:
            baseline=evaluate(out/'validation/20k/NMS',link,None,frozen['alpha'],frozen['validation_snr_db'],None)
            initial=evaluate(out/'validation/20k/step-00000',link,model,frozen['alpha'],frozen['validation_snr_db'],0)
            emit(out,'initial_validation',initial_bce=initial['mean_information_bce'],NMS_bce=baseline['mean_information_bce'])
        elif step%1000==0:
            evaluate(out/f'validation/20k/step-{step:05d}',link,model,frozen['alpha'],frozen['validation_snr_db'],step)
        torch.cuda.reset_peak_memory_stats()
        first=step+1
        for step in range(first,args.stop_after+1):
            tick=time.perf_counter()
            info,lch,snrs,digest=train_batch(link,args.seed,step,frozen['training_snr_range_db'])
            row=engine.step(optimizer,info,lch,step)
            torch.cuda.synchronize()
            row.update(step=step,seconds=time.perf_counter()-tick,observations=step*64,
                       snr_min_db=float(snrs.min()),snr_max_db=float(snrs.max()),sample_sha256=digest,
                       peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
            with (segment/'train_history.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            if step==first or step%100==0 or step==args.stop_after:emit(out,'train_step',**row)
            if step%100==0 or step==args.stop_after:
                assert contract['source_sha256']==source_hashes(),'training source changed during run'
                save_checkpoint(out,model,optimizer,step,contract)
                save_json(out/'progress.json',{'status':'training','global_step':step,'target':args.stop_after,
                          'observations':step*64,'last_training_record':row,'pid':os.getpid()})
            if step%1000==0:
                metrics=evaluate(out/f'validation/20k/step-{step:05d}',link,model,frozen['alpha'],frozen['validation_snr_db'],step)
                emit(out,'checkpoint_validation',step=step,mean_information_bce=metrics['mean_information_bce'])
        post=post_checks(link,model,frozen['alpha'])
        latest=json.loads((out/'latest_checkpoint.json').read_text())
        reloaded=RowSSM(link.rows).to(link.device);reload_opt=optimizer_for(reloaded)
        load_checkpoint(latest['path'],reloaded,reload_opt,contract)
        info,lch,_,_=train_batch(link,args.seed,0,frozen['training_snr_range_db'])
        with torch.no_grad():
            a=link.decode(lch[:8],alpha=frozen['alpha'],controller=model)[0]
            b=link.decode(lch[:8],alpha=frozen['alpha'],controller=reloaded)[0]
        reload_error=float((a-b).abs().max());assert reload_error==0
        del engine,reloaded,reload_opt,a,b;torch.cuda.empty_cache()
        selection=final_selection(out,link,model,optimizer,contract,frozen) if step==TOTAL else None
        rows=history(out,step)
        grad=np.array([r['gradient_norm_before_clip'] for r in rows])
        latest_valid=(step//1000)*1000
        initial=json.loads((out/'validation/20k/step-00000/summary.json').read_text())
        final=json.loads((out/f'validation/20k/step-{latest_valid:05d}/summary.json').read_text())
        summary={'status':'formal_50k_completed' if step==TOTAL else 'short_acceptance_passed',
                 'config_id':args.config_id,'seed':args.seed,'batch':64,'microbatch':args.microbatch,
                 'steps':step,'observations':step*64,'formal_protocol':True,'budget_steps':TOTAL,
                 'mean_step_seconds':float(np.mean([r['seconds'] for r in rows])),
                 'mean_step_seconds_after_first10':float(np.mean([r['seconds'] for r in rows[10:] or rows])),
                 'peak_allocated_bytes':max(r['peak_allocated_bytes'] for r in rows),
                 'peak_reserved_bytes':max(r['peak_reserved_bytes'] for r in rows),
                 'gradient_clip_fraction':float(np.mean(grad>1)),
                 'gradient_norm_quantiles':{str(q):float(np.quantile(grad,q)) for q in [0,.25,.5,.75,.9,.95,.99,1]},
                 'initial_validation_mean_bce':initial['mean_information_bce'],
                 'latest_periodic_validation_step':latest_valid,'latest_validation_mean_bce':final['mean_information_bce'],
                 'post_checks':post,'checkpoint_reload_max_error':reload_error,'checkpoint':latest,
                 'checkpoint_selection':selection,'segment_elapsed_seconds':time.perf_counter()-started,
                 'all_training_loss_gradients_parameters_finite':True,
                 'limitations':['selection validation is not independent formal BLER test',
                                'seed29/43 and matched baselines remain separate work']}
        save_json(segment/'summary.json',summary);save_json(out/'summary.json',summary)
        if step==1001:save_json(out/'short_acceptance.json',summary)
        save_json(out/'progress.json',{'status':summary['status'],'global_step':step,'target':args.stop_after,'pid':os.getpid()})
        emit(out,'completed',**summary)
    except Exception as exc:
        save_json(segment/'failure.json',{'error':repr(exc),'traceback':traceback.format_exc(),'last_attempted_step':step})
        emit(out,'failed',error=repr(exc),last_attempted_step=step)
        raise


if __name__=='__main__':main()
