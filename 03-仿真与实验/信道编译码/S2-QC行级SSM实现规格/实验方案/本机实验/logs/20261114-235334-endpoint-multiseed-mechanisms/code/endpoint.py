"""Independent fixed-N T20 paired endpoint pilot/test, with immutable shards."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,gc,hashlib,importlib.metadata,json,math,os,platform,sys,time
import numpy as np
import torch
from torch.nn import functional as F
CODE=Path(__file__).resolve().parent
LOG=CODE.parent
ROOT=LOG.parent.parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT.parent))
from formal_core import configure,source_hashes,frozen_config,parameter_hash,post_checks,save_json
from nr_link import NRLink,crc_attach,sha256
from ssm import RowSSM
from generate_manifest import stable_seed
from protocol_checks import wilson,zero_error_upper,log_bler_crossing
from mechanisms import RowControl
PLAN=json.loads((LOG/"preregistration.json").read_text())
OUT=Path(PLAN["output"])

def now():return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
def load(p):return json.loads(Path(p).read_text())
def immutable(p,data):
    p=Path(p)
    if p.exists():assert load(p)==data,("immutable identity mismatch",str(p))
    else:save_json(p,data)
def extension_hashes():return {str(p):sha256(p) for p in [CODE/"endpoint.py",CODE/"mechanisms.py"]}
def assert_sources():
    proof=load(PLAN["proof"])
    assert proof["status"]=="passed" and proof["source_sha256"]==source_hashes()
    assert sha256(Path(PLAN["frozen_inputs"]))==PLAN["frozen_inputs_sha256"]
    if (LOG/"endpoint_source_frozen.json").exists():assert load(LOG/"endpoint_source_frozen.json")==extension_hashes()
def emit(event,**data):
    rec={"time":now(),"event":event,**data}
    with (OUT/"events.jsonl").open("a") as f:f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(json.dumps(rec,ensure_ascii=False),flush=True)
def registry17():
    entries={}
    for c in PLAN["configs"]:
        entries[c["config_id"]]=[{"name":"NMS","kind":"nms","alpha":c["alpha"]},
            {"name":"S2-seed17","kind":"ssm","alpha":c["alpha"],"seed":17,
             "checkpoint":c["checkpoint"],"checkpoint_sha256":c["checkpoint_sha256"],
             "parameter_sha256":c["parameter_sha256"],"step":c["selected_step"]}]
    return {"cohort":"seed17","configs":entries}
def model_for(link,spec):
    if spec["kind"] in ("nms","static"):return None
    p=Path(spec["checkpoint"]);assert sha256(p)==spec["checkpoint_sha256"]
    d=torch.load(p,weights_only=True,map_location="cpu")
    assert d["contract"]["source_sha256"]==source_hashes()
    assert d["contract"]["config_id"]==link.cfg["id"] and d["contract"]["alpha"]==spec["alpha"]
    model=RowSSM(link.rows) if spec["kind"]=="ssm" else RowControl(link.rows,spec["kind"])
    model=model.to(link.device);model.load_state_dict(d["model"]);model.eval()
    assert parameter_hash(model)==d["parameter_sha256"]==spec["parameter_sha256"]
    assert all(torch.isfinite(x).all() for x in model.parameters())
    if spec["kind"]!="ssm":assert d["contract"]["mechanism_source_sha256"]==sha256(CODE/"mechanisms.py")
    return model
class Engine:
    def __init__(self,link,model,alpha,eta=0.,batch=125):
        self.link,self.model,self.alpha,self.eta,self.batch=link,model,alpha,eta,batch
        self.input=torch.zeros((batch,link.n),device=link.device).masked_fill(link.filler,20)
        stream=torch.cuda.Stream();stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream),torch.no_grad():
            for _ in range(2):self.decode(self.input)
        torch.cuda.current_stream().wait_stream(stream);torch.cuda.synchronize()
        self.graph=torch.cuda.CUDAGraph()
        with torch.no_grad(),torch.cuda.graph(self.graph):
            self.output,_,self.state=self.decode(self.input)
        torch.cuda.synchronize()
    def decode(self,x):return self.link.decode(x,iterations=20,alpha=self.alpha,controller=self.model,eta=self.eta)
    def __call__(self,x):
        assert len(x)<=self.batch
        self.input[:len(x)].copy_(x);self.graph.replay()
        return self.output[:len(x)]

def sample(link,split,snr,shard,n):
    bits=np.random.default_rng(stable_seed(link.cfg["id"],snr,shard,split+"/bits"))
    noise=np.random.default_rng(stable_seed(link.cfg["id"],snr,shard,split+"/noise"))
    payload=bits.integers(0,2,(n,link.a),dtype=np.uint8)
    cw,info=link.encode(payload);lch,_=link.channel(cw,float(snr),noise)
    digest=hashlib.sha256(payload.tobytes()+lch.cpu().numpy().tobytes()).hexdigest()
    return payload,info,lch,digest

def metrics(bits,rejected,crc,bce):
    wrong=bits>0;n=len(bits)
    e=int(wrong.sum())
    rec={"frames":n,"payload_frame_errors":e,"payload_bit_errors":int(bits.sum()),
         "rejected":int(rejected.sum()),"service_frame_errors":int((wrong|rejected).sum()),
         "accepted_wrong":int((wrong&~rejected).sum()),"crc_passed_wrong":int((wrong&crc).sum()),
         "bce_sum":float(bce.astype(np.float64).sum()),"payload_bler":e/n,
         "bler_ci95":list(wilson(e,n))}
    if e==0:rec["zero_error_one_sided95_upper"]=zero_error_upper(n)
    return rec

def evaluate_point(root,link,specs,engines,split,snr,frames):
    assert frames%32==0
    directory=Path(root)/f"snr-{snr:.4f}";directory.mkdir(parents=True,exist_ok=True)
    identity={"config_id":link.cfg["id"],"snr_db":snr,"frames":frames,"shards":32,"split":split,
              "methods":specs,"T":20,"early_stop":False,"fallback":False,
              "core_sha256":source_hashes(),"endpoint_sha256":extension_hashes()}
    immutable(directory/"identity.json",identity)
    if (directory/"summary.json").exists():
        summary=load(directory/"summary.json");assert summary["identity"]==identity
        for file,digest in summary["artifacts_sha256"].items():assert sha256(directory/file)==digest
        return summary
    tic=time.perf_counter();artifacts={};shards=[];n=frames//32
    for shard in range(32):
        p=directory/f"shard-{shard:02d}.npz"
        if not p.exists():
            payload,info,lch,digest=sample(link,split,snr,shard,n)
            biterrors=np.empty((len(specs),n),dtype=np.int32)
            rejected=np.empty((len(specs),n),dtype=bool);crc=np.empty_like(rejected)
            bces=np.empty((len(specs),n),dtype=np.float32);states=[]
            for mi,engine in enumerate(engines):
                maximum=0.
                with torch.no_grad():
                    for begin in range(0,n,engine.batch):
                        end=min(n,begin+engine.batch);u=engine(lch[begin:end])
                        assert torch.isfinite(u).all()
                        maximum=max(maximum,float(engine.state));assert maximum<=1.00001
                        labels=torch.tensor(info[begin:end],device=link.device,dtype=torch.float32)
                        bces[mi,begin:end]=F.binary_cross_entropy_with_logits(-u[:,:link.b],labels,reduction="none").mean(1).cpu().numpy()
                        bits=(u[:,:link.b]<0).cpu().numpy().astype(np.uint8)
                        biterrors[mi,begin:end]=(bits[:,:link.a]!=payload[begin:end]).sum(1)
                        rejected[mi,begin:end]=(~link.accepted(u)).cpu().numpy()
                        crc[mi,begin:end]=(bits==crc_attach(bits[:,:link.a],link.cfg["tb_crc"])).all(1)
                states.append(maximum)
            temp=p.with_suffix(".tmp.npz")
            np.savez_compressed(temp,bit_errors=biterrors,rejected=rejected,crc_ok=crc,bce=bces,
                state_max=np.array(states),sample_sha256=digest,identity=json.dumps(identity,sort_keys=True))
            temp.replace(p)
            p.with_suffix(".npz.sha256").write_text(sha256(p)+"  "+p.name+"\n")
            del lch,info,payload
        assert sha256(p)==p.with_suffix(".npz.sha256").read_text().split()[0]
        with np.load(p,allow_pickle=False) as a:
            assert str(a["identity"])==json.dumps(identity,sort_keys=True)
            assert a["bit_errors"].shape==(len(specs),n) and np.isfinite(a["bce"]).all()
            rows=[metrics(a["bit_errors"][mi],a["rejected"][mi],a["crc_ok"][mi],a["bce"][mi]) for mi in range(len(specs))]
            shards.append({"shard":shard,"sample_sha256":str(a["sample_sha256"]),"methods":rows})
        artifacts[p.name]=sha256(p)
        save_json(OUT/"progress.json",{"time":now(),"status":"sampling","split":split,"config":link.cfg["id"],"snr":snr,
                  "completed_shards":shard+1,"frames":frames,"methods":[v["name"] for v in specs],"pid":os.getpid()})
        if (shard+1)%8==0:emit("shards",split=split,config=link.cfg["id"],snr=snr,done=shard+1)
    combined=[]
    for mi,spec in enumerate(specs):
        keys=["frames","payload_frame_errors","payload_bit_errors","rejected","service_frame_errors","accepted_wrong","crc_passed_wrong","bce_sum"]
        row={k:sum(s["methods"][mi][k] for s in shards) for k in keys}
        row.update(name=spec["name"],payload_bler=row["payload_frame_errors"]/frames,
                   information_bce=row["bce_sum"]/frames,payload_ber=row["payload_bit_errors"]/(frames*link.a),
                   bler_ci95=list(wilson(row["payload_frame_errors"],frames)))
        if row["payload_frame_errors"]==0:row["zero_error_one_sided95_upper"]=zero_error_upper(frames)
        combined.append(row)
    result={"status":"passed","identity":identity,"methods":combined,"shards":shards,
            "seconds":time.perf_counter()-tic,"artifacts_sha256":artifacts}
    assert_sources();save_json(directory/"summary.json",result)
    emit("point_complete",split=split,config=link.cfg["id"],snr=snr,frames=frames,
         errors={r["name"]:r["payload_frame_errors"] for r in combined},seconds=result["seconds"])
    return result

def resources(cid,specs):
    _,cfg=frozen_config(PLAN["frozen_inputs"],cid)
    link=NRLink(cfg);models=[model_for(link,s) for s in specs]
    engines=[Engine(link,m,s["alpha"],s.get("eta",0.)) for s,m in zip(specs,models)]
    return link,models,engines

def bracket(points,mi,target=.001):
    rows=sorted((p["identity"]["snr_db"],p["methods"][mi]["payload_bler"]) for p in points)
    for a,b in zip(rows,rows[1:]):
        if a[1]>=target>=b[1] and a[1]>b[1]>0:return [a[0],b[0]]
    return None

def pilot():
    registry=registry17();immutable(OUT/"seed17_registry.json",registry)
    for cfg in PLAN["configs"]:
        cid=cfg["config_id"];specs=registry["configs"][cid]
        root=OUT/"pilot"/cid;link,models,engines=resources(cid,specs)
        grid=[round(x/10,4) for x in range(round(cfg["pilot_initial_range_db"][0]*10),round(cfg["pilot_initial_range_db"][1]*10)+1)]
        points={snr:evaluate_point(root,link,specs,engines,PLAN["pilot"]["split"],snr,20000) for snr in grid}
        for round_id in range(9):
            missing=[i for i in range(len(specs)) if bracket(points.values(),i) is None]
            if not missing:break
            assert round_id<8,("pilot needs more than preregistered8 refinements",cid)
            added=set()
            rows=sorted(points.items())
            for mi in missing:
                error_grid=[(snr,p["methods"][mi]["payload_bler"]) for snr,p in rows]
                zero_pair=next(((a,b) for a,b in zip(error_grid,error_grid[1:]) if a[1]>=.001 and b[1]==0),None)
                if zero_pair:added.add(round((zero_pair[0][0]+zero_pair[1][0])/2,4))
                elif all(p>=.001 for _,p in error_grid):added.add(round(error_grid[-1][0]+.2,4))
                elif all(p<=.001 for _,p in error_grid):added.add(round(error_grid[0][0]-.2,4))
                else:raise AssertionError(("nonmonotone unbracketed pilot",cid,error_grid))
            assert all(-1<=x<=4 and x not in points for x in added)
            immutable(root/f"refinement-{round_id:02d}.json",{"new_snrs":sorted(added),"reason":"predeclared positive-log-bracket rule","before":{str(s):[v["payload_frame_errors"] for v in p["methods"]] for s,p in rows}})
            for snr in sorted(added):points[snr]=evaluate_point(root,link,specs,engines,PLAN["pilot"]["split"],snr,20000)
        summary={"status":"passed","config_id":cid,"methods":specs,"points":[points[k] for k in sorted(points)],
                 "positive_brackets":{s["name"]:bracket(points.values(),i) for i,s in enumerate(specs)},
                 "unique_channel_observations":len(points)*20000}
        save_json(root/"summary.json",summary)
        del link,models,engines;gc.collect();torch.cuda.empty_cache()
    save_json(OUT/"pilot_summary.json",{"status":"passed","configs":{c["config_id"]:sha256(OUT/"pilot"/c["config_id"]/"summary.json") for c in PLAN["configs"]}})
    emit("pilot_completed")

def freeze():
    assert load(OUT/"pilot_summary.json")["status"]=="passed"
    path=OUT/"test_grid_frozen.json"
    if path.exists():assert sha256(path)==path.with_suffix(".sha256").read_text().split()[0];return
    config_grid={}
    for c in PLAN["configs"]:
        cid=c["config_id"];summary=load(OUT/"pilot"/cid/"summary.json")
        bounds=list(summary["positive_brackets"].values());assert all(b is not None for b in bounds)
        lo=math.floor((min(b[0] for b in bounds)-.1)*10+1e-8)
        hi=math.ceil((max(b[1] for b in bounds)+.1)*10-1e-8)
        grid=sorted(set([round(i/10,4) for i in range(lo,hi+1)]+[x for b in bounds for x in b]))
        config_grid[cid]={"snr_db":grid,"frames_per_snr":200000,"shards":32,"pilot_summary_sha256":sha256(OUT/"pilot"/cid/"summary.json"),"pilot_brackets":summary["positive_brackets"]}
    freeze_data={"status":"frozen_before_test","created_at":now(),"target_bler":.001,"T":20,"early_stop":False,"fallback":False,
                 "split":PLAN["test"]["split"],"configs":config_grid,"registry":registry17(),"core_sha256":source_hashes(),"endpoint_sha256":extension_hashes(),
                 "rule":PLAN["test"]["grid_rule"],"new_grid_after_test_allowed":False}
    save_json(path,freeze_data);path.with_suffix(".sha256").write_text(sha256(path)+"  "+path.name+"\n")
    emit("test_grid_frozen",sha256=sha256(path),configs=config_grid)

def statistics(points,registry):
    specs=registry;n=len(specs);target=.001
    snrs=[p["identity"]["snr_db"] for p in points]
    rows=[]
    for i,spec in enumerate(specs):
        rows.append({"method":spec["name"],"crossing_db":log_bler_crossing([(x,p["methods"][i]["payload_bler"]) for x,p in zip(snrs,points)],target)})
    counts=np.array([[[sh["methods"][mi]["payload_frame_errors"] for sh in p["shards"]] for mi in range(n)] for p in points])
    totals=np.array([[sh["methods"][0]["frames"] for sh in p["shards"]] for p in points])
    rng=np.random.default_rng(PLAN["test"]["bootstrap_seed"]);boots=np.full((PLAN["test"]["bootstrap_replicates"],n),np.nan)
    for rep in range(len(boots)):
        idx=rng.integers(0,32,32)
        rates=counts[:,:,idx].sum(2)/totals[:,idx].sum(1)[:,None]
        for mi in range(n):
            crossing=log_bler_crossing(list(zip(snrs,rates[:,mi].tolist())),target)
            if crossing is not None:boots[rep,mi]=crossing
    for mi,r in enumerate(rows):
        valid=np.isfinite(boots[:,mi]);r["bootstrap_valid"]=int(valid.sum());r["bootstrap_total"]=len(boots)
        r["conditional_bootstrap_ci95_db"]=np.quantile(boots[valid,mi],[.025,.975]).tolist() if valid.any() else None
        r["ci95_db"]=r["conditional_bootstrap_ci95_db"] if valid.all() and r["crossing_db"] is not None else None
        if mi:
            delta=boots[:,0]-boots[:,mi];v=np.isfinite(delta)
            r["gain_vs_NMS_db"]=rows[0]["crossing_db"]-r["crossing_db"] if rows[0]["crossing_db"] is not None and r["crossing_db"] is not None else None
            r["gain_bootstrap_valid"]=int(v.sum())
            r["gain_ci95_db"]=np.quantile(delta[v],[.025,.975]).tolist() if v.all() else None
            r["gain_conditional_ci95_db"]=np.quantile(delta[v],[.025,.975]).tolist() if v.any() else None
    return {"target_bler":target,"methods":rows,"interpolation":"log10(BLER), adjacent positive observed points only; no pseudocount, no extrapolation",
            "ci_scope":"paired32-shard percentile bootstrap, sampling uncertainty conditional on selected models; no training-seed uncertainty or interpolation-model-error coverage",
            "invalid_bootstrap_policy":"any invalid replicate makes ordinary CI N/A; valid-only conditional interval separately disclosed"}

def test(registry_path):
    grid_path=OUT/"test_grid_frozen.json";assert sha256(grid_path)==grid_path.with_suffix(".sha256").read_text().split()[0]
    grid=load(grid_path);registry=load(registry_path);cohort=registry["cohort"]
    immutable(OUT/"test"/cohort/"registry.json",registry)
    summaries={}
    for cid,specs in registry["configs"].items():
        assert specs[0]["kind"]=="nms"
        p=grid["configs"][cid];link,models,engines=resources(cid,specs)
        points=[evaluate_point(OUT/"test"/cohort/cid,link,specs,engines,grid["split"],snr,p["frames_per_snr"]) for snr in p["snr_db"]]
        stats=statistics(points,specs)
        summary={"status":"passed","cohort":cohort,"config_id":cid,"test_grid_sha256":sha256(grid_path),
                 "methods":specs,"points":points,"endpoint":stats,"unique_channel_observations":len(points)*p["frames_per_snr"]}
        save_json(OUT/"test"/cohort/cid/"summary.json",summary);summaries[cid]=stats
        emit("endpoint_result",cohort=cohort,config=cid,statistics=stats)
        del link,models,engines;gc.collect();torch.cuda.empty_cache()
    save_json(OUT/"test"/cohort/"summary.json",{"status":"passed","cohort":cohort,"configs":summaries,
        "test_grid_sha256":sha256(grid_path),"finished_at":now()})

def verify():
    assert_sources();configure()
    env={"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"cuda":torch.version.cuda,
         "device":torch.cuda.get_device_name(0),"GPU":os.environ.get("CUDA_VISIBLE_DEVICES"),
         "packages":{p:importlib.metadata.version(p) for p in ("numpy","scipy","sionna","py3gpp")},"core_sha256":source_hashes(),"endpoint_sha256":extension_hashes()}
    checks={}
    for cid,specs in registry17()["configs"].items():
        link,models,engines=resources(cid,specs)
        split="S2-endpoint-verification-v1"
        payload,info,lch,digest=sample(link,split,1.5,0,256)
        small=sample(link,split,1.5,0,125)
        assert np.array_equal(payload[:125],small[0]) and np.array_equal(info[:125],small[1]) and torch.equal(lch[:125],small[2])
        assert len({stable_seed(cid,1.5,0,s+"/bits") for s in [split,PLAN["pilot"]["split"],PLAN["test"]["split"],"S2-formal-validation-v1"]})==4
        maxerror=0.;unpadded_max=0.
        with torch.no_grad():
            for engine in engines:
                for batch in [1,8,64,125]:
                    got=engine(lch[:batch])
                    eager=engine.decode(engine.input)[0][:batch]
                    error=float((eager-got).abs().max());maxerror=max(maxerror,error);assert torch.equal(eager,got),(cid,batch,error)
                    unpadded_max=max(unpadded_max,float((engine.decode(lch[:batch])[0]-got).abs().max()))
        post=post_checks(link,models[1],specs[1]["alpha"])
        fresh=model_for(link,specs[1])
        with torch.no_grad():assert torch.equal(link.decode(lch[:8],alpha=specs[1]["alpha"],controller=fresh)[0],link.decode(lch[:8],alpha=specs[1]["alpha"],controller=models[1])[0])
        checks[cid]={"status":"passed","graph_eager_max_error":maxerror,"comparison_shape":125,"unpadded_eager_difference_descriptive":unpadded_max,"prefix_exact":True,"reload_exact":True,"post_checks":post,"sample_sha256":digest}
        del link,models,engines,fresh,lch,small;gc.collect();torch.cuda.empty_cache()
    env["status"]="passed";env["configs"]=checks
    save_json(LOG/"endpoint_verification.json",env);emit("endpoint_verification_passed",configs=checks)

def main():
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["verify","pilot","freeze","test"]);p.add_argument("--registry")
    a=p.parse_args();configure();assert_sources()
    if a.mode=="verify":verify()
    else:
        gate=load(LOG/"endpoint_verification.json");assert gate["status"]=="passed" and gate["endpoint_sha256"]==extension_hashes()
        if a.mode=="pilot":pilot()
        elif a.mode=="freeze":freeze()
        else:test(a.registry or OUT/"seed17_registry.json")
if __name__=="__main__":main()

