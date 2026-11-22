"""Meaningful pretraining gate for new control architectures."""
from pathlib import Path
import copy,gc,json,sys,time
import numpy as np
import torch
from endpoint import ROOT,LOG,OUT,PLAN,load,emit,assert_sources,Engine,now
from mechanisms import RowControl,SPECS,StaticEta
from formal_core import (TrainingEngine,InferenceEngine,configure,frozen_config,train_batch,parameter_hash,
    optimizer_for,post_checks,save_checkpoint,load_checkpoint,make_contract,save_json)
from nr_link import NRLink,sha256
from ssm import RowSSM
from verify_formal import cpu_copy,equal,snapshot
from train_mechanism import mechanism_sources
configure();assert_sources()
assert load(LOG/"statistics_verification.json")["status"]=="passed"
result={"status":"passed","mechanism_sources":mechanism_sources(),"definitions":SPECS,"checks":{}}
attempt=OUT/"mechanism-verification"/now().replace(":","-")
for spec in PLAN["configs"]:
    cid=spec["config_id"];f,cfg=frozen_config(PLAN["frozen_inputs"],cid);link=NRLink(cfg)
    base=sum(p.numel() for p in RowSSM(link.rows).parameters());result["checks"][cid]={}
    for kind in ["mlp","ema","gru"]:
        torch.manual_seed(17);model=RowControl(link.rows,kind).cuda();params=sum(p.numel() for p in model.parameters())
        assert abs(params/base-1)<=.1,(kind,params,base)
        opt=optimizer_for(model);engine=TrainingEngine(link,model,f["alpha"],64,"eager");refs={}
        for step in [1,2,3,4]:
            info,lch,_,_=train_batch(link,17,step,f["training_snr_range_db"])
            row=engine.step(opt,info,lch,step);refs[step]=snapshot(model,opt,row)
        reference_post=post_checks(link,model,f["alpha"])
        del engine,model,opt,info,lch;gc.collect();torch.cuda.empty_cache()
        torch.manual_seed(17);model=RowControl(link.rows,kind).cuda();opt=optimizer_for(model)
        engine=TrainingEngine(link,model,f["alpha"],64,"cuda-graph")
        checkpoint_dir=attempt/cid/kind;checkpoint_dir.mkdir(parents=True,exist_ok=False)
        contract=make_contract(PLAN["frozen_inputs"],f,link,17,"cuda-graph",64)
        contract.update(mechanism=kind,mechanism_source_sha256=sha256(Path(__file__).with_name("mechanisms.py")),
                        mechanism_runner_sha256=sha256(Path(__file__).with_name("train_mechanism.py")))
        for step in [1,2,3,4]:
            info,lch,_,_=train_batch(link,17,step,f["training_snr_range_db"])
            row=engine.step(opt,info,lch,step)
            got=snapshot(model,opt,row)
            for key in ["model","optimizer","gradients"]:equal(refs[step][key],got[key],kind+"/"+key)
            for key in ["loss","information_bce_last4","soft_syndrome_loss","gradient_norm_before_clip","gradient_norm_after_clip","state_abs_max"]:
                assert row[key]==refs[step]["metrics"][key],(kind,key,row[key],refs[step]["metrics"][key])
            if step==3:save_checkpoint(checkpoint_dir,model,opt,step,contract)
        post=post_checks(link,model,f["alpha"])
        del engine,model,opt,info,lch;gc.collect();torch.cuda.empty_cache()
        model=RowControl(link.rows,kind).cuda();opt=optimizer_for(model)
        engine=TrainingEngine(link,model,f["alpha"],64,"cuda-graph")
        load_checkpoint(checkpoint_dir/"checkpoints/step-00003.pt",model,opt,contract)
        info,lch,_,_=train_batch(link,17,4,f["training_snr_range_db"])
        row=engine.step(opt,info,lch,4);got=snapshot(model,opt,row)
        for key in ["model","optimizer","gradients"]:equal(refs[4][key],got[key],kind+"/resume/"+key)
        # Full forward/autograd at auxiliary-loss schedule boundaries.
        engine.coefficient.fill_(.02)
        loss,bce,syn,state=engine.backward(lch,torch.tensor(info,device="cuda",dtype=torch.float32),10000)
        assert torch.isfinite(loss) and all(torch.isfinite(p.grad).all() for p in model.parameters())
        del engine;gc.collect();torch.cuda.empty_cache()
        inference=InferenceEngine(link,model,f["alpha"])
        with torch.no_grad():
            got=inference(lch[:8]);ref=link.decode(inference.input,alpha=f["alpha"],controller=model)[0][:8]
            assert torch.equal(got,ref),(cid,kind,"inference")
        result["checks"][cid][kind]={"status":"passed","parameters":params,"SSM_parameters":base,"ratio":params/base,
            "four_graph_eager_updates_exact":True,"checkpoint_next_update_exact":True,"inference_exact":True,
            "syndrome_full_weight_finite":True,"post_checks":post}
        emit("mechanism_verified",config=cid,kind=kind,parameters=params)
        del inference,model,opt,info,lch,refs,got,ref;gc.collect();torch.cuda.empty_cache()
    # Validate the actual scalar-eta inference path, preserving host scalar arithmetic.
    _,lch,_,_=train_batch(link,17,7,f["training_snr_range_db"])
    payload=np.random.default_rng(20261115).integers(0,2,(8,link.a),dtype=np.uint8)
    cw,_=link.encode(payload);sign=torch.tensor(1-2*cw.astype(np.float32),device=link.device)
    clean,_=link.channel(cw,0.,np.random.default_rng(19),noiseless=True)
    for eta in [0.,.05,.5]:
        scalar_engine=Engine(link,None,f["alpha"],eta)
        with torch.no_grad():
            g=scalar_engine(lch[:8]);ref=link.decode(scalar_engine.input,alpha=f["alpha"],eta=eta)[0][:8]
            assert torch.equal(g,ref),(cid,eta,"scalar graph/eager")
            a=link.decode(lch[:8],alpha=f["alpha"],eta=eta)[0]
            b=link.decode(lch[:8]*sign,alpha=f["alpha"],eta=eta)[0]
            assert float((b-a*sign).abs().max())<2e-4,(cid,eta,"symmetry")
            decoded=link.decode(clean,alpha=f["alpha"],eta=eta)[0]
            assert np.array_equal((decoded[:,:link.a]<0).cpu().numpy(),payload)
            assert bool(link.accepted(decoded).all())
        del scalar_engine;gc.collect();torch.cuda.empty_cache()
    result["checks"][cid]["static_eta"]={"status":"passed","scalar_graph_eager_exact":True,"symmetry_and_noiseless":"passed"}
    del link,lch;gc.collect();torch.cuda.empty_cache()
save_json(LOG/"mechanism_verification.json",result)
print(json.dumps(result,ensure_ascii=False,indent=2))

