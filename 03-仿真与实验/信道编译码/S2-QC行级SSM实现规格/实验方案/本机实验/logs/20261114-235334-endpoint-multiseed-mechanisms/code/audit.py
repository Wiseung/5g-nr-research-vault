"""Independent artifact aggregation gates, no optimizer updates."""
from pathlib import Path
import argparse,gc,hashlib,json,math,sys
import numpy as np
import torch
from scipy.stats import binomtest
from endpoint import ROOT,LOG,OUT,PLAN,load,metrics,model_for,registry17,extension_hashes,immutable
from formal_core import source_hashes,lr_at,syndrome_weight,parameter_hash,post_checks,configure,save_json
from nr_link import NRLink,sha256
from mechanisms import RowControl
from ssm import RowSSM
def finite(v):
    if torch.is_tensor(v):return bool(torch.isfinite(v).all())
    if isinstance(v,dict):return all(finite(x) for x in v.values())
    if isinstance(v,(tuple,list)):return all(finite(x) for x in v)
    return True
def endpoint_audit(scope):
    if scope=="pilot":directory=OUT/"pilot"
    else:directory=OUT/"test"/scope
    summaries=sorted(directory.glob("*/snr-*/summary.json"));assert summaries
    total=0;points=0;paired_compare=0
    for p in summaries:
        s=load(p);identity=s["identity"]
        assert identity["T"]==20 and not identity["early_stop"] and not identity["fallback"]
        assert identity["core_sha256"]==source_hashes() and identity["endpoint_sha256"]==extension_hashes()
        expectedN=20000 if scope=="pilot" else 200000
        assert identity["frames"]==expectedN
        if scope!="pilot":
            grid=load(OUT/"test_grid_frozen.json")
            assert identity["split"]==grid["split"]
            assert identity["snr_db"] in grid["configs"][identity["config_id"]]["snr_db"]
        sums=[{} for _ in identity["methods"]]
        verified_rows=[[] for _ in identity["methods"]]
        shards=[]
        for sh in range(32):
            filename=f"shard-{sh:02d}.npz";file=p.parent/filename
            assert sha256(file)==s["artifacts_sha256"][filename]
            with np.load(file,allow_pickle=False) as a:
                assert str(a["identity"])==json.dumps(identity,sort_keys=True)
                assert a["bit_errors"].shape==(len(sums),expectedN//32)
                assert np.isfinite(a["bce"]).all() and a["state_max"].max()<=1.00001
                for mi in range(len(sums)):
                    rec=metrics(a["bit_errors"][mi],a["rejected"][mi],a["crc_ok"][mi],a["bce"][mi])
                    assert rec==s["shards"][sh]["methods"][mi]
                    verified_rows[mi].append(rec)
                    for k in ["frames","payload_frame_errors","payload_bit_errors","rejected","service_frame_errors","accepted_wrong","crc_passed_wrong","bce_sum"]:
                        sums[mi][k]=sums[mi].get(k,0)+rec[k]
                if scope not in ("pilot","seed17"):
                    original=OUT/"test/seed17"/identity["config_id"]/p.parent.name/filename
                    with np.load(original,allow_pickle=False) as b:
                        assert str(a["sample_sha256"])==str(b["sample_sha256"])
                        for k in ["bit_errors","rejected","crc_ok","bce"]:assert np.array_equal(a[k][0],b[k][0]),("NMS changed across cohorts",file,k)
                    paired_compare+=1
        for mi,rec in enumerate(sums):
            rec={k:sum(v[k] for v in verified_rows[mi]) for k in rec}
            assert all(rec[k]==s["methods"][mi][k] for k in rec)
            ci=binomtest(rec["payload_frame_errors"],rec["frames"]).proportion_ci(method="wilson")
            assert np.allclose([ci.low,ci.high],s["methods"][mi]["bler_ci95"],rtol=0,atol=2e-12)
        total+=expectedN;points+=1
    if scope=="pilot":assert load(OUT/"pilot_summary.json")["status"]=="passed"
    else:
        summary=load(directory/"summary.json");assert summary["status"]=="passed"
        for cid in summary["configs"]:
            expected=load(OUT/"test_grid_frozen.json")["configs"][cid]["snr_db"]
            assert len(list((directory/cid).glob("snr-*/summary.json")))==len(expected)
    result={"status":"passed","scope":scope,"points":points,"channel_observations":total,
            "paired_baseline_shards_reproduced":paired_compare,"CI_check":"independent SciPy Wilson","sources_unchanged":True}
    save_json(directory/"audit_summary.json",result);print(json.dumps(result,ensure_ascii=False))
def training_audit(path):
    root=Path(path);s=load(root/"summary.json");c=load(root/"contract.json")
    assert s["status"]=="formal_50k_completed" and s["steps"]==50000 and s["observations"]==3200000
    assert c["source_sha256"]==source_hashes()
    assert s["checkpoint_reload_max_error"]==0 and s["all_training_loss_gradients_parameters_finite"]
    rows={}
    for p in sorted((root/"segments").glob("*/train_history.jsonl")):
        for line in p.read_text().splitlines():
            r=json.loads(line);assert r["step"] not in rows or r==rows[r["step"]];rows[r["step"]]=r
    assert sorted(rows)==list(range(1,50001))
    for step,r in rows.items():
        assert r["lr"]==lr_at(step) and r["syndrome_weight"]==syndrome_weight(step) and r["observations"]==step*64
        assert all(math.isfinite(r[k]) for k in ["loss","gradient_norm_before_clip","gradient_norm_after_clip","parameter_update_l2","parameter_norm_l2","state_abs_max"])
        assert r["state_abs_max"]<=1.00001 and r["gradient_norm_after_clip"]<=1.00001 and r["parameter_update_l2"]>0
    assert len({r["sample_sha256"] for r in rows.values()})==50000
    matched_training_samples=None
    if "mechanism" in c:
        short="bg2" if "B1024" in c["config_id"] else "bg1"
        if c["seed"]==17:
            parent=ROOT/("results/20261113-214206-formal50k-bg2-seed17" if short=="bg2" else "results/20261114-165401-bg1-formal50k-seed17")
        else:parent=OUT/"training"/f"{short}-ssm-seed{c['seed']}"
        reference={}
        for p in (parent/"segments").glob("*/train_history.jsonl"):
            for line in p.read_text().splitlines():
                r=json.loads(line);reference[r["step"]]=r["sample_sha256"]
        assert sorted(reference)==list(range(1,50001))
        assert all(rows[step]["sample_sha256"]==digest for step,digest in reference.items())
        matched_training_samples=50000*64
    hashes={}
    checkpoints=list((root/"checkpoints").glob("*.pt"))
    for p in checkpoints:
        assert sha256(p)==p.with_suffix(".pt.sha256").read_text().split()[0]
        d=torch.load(p,weights_only=True,map_location="cpu")
        assert d["contract"]==c and finite(d["model"]) and finite(d["optimizer"])
        assert all(int(v["step"])==d["global_step"] for v in d["optimizer"]["state"].values())
        digest=hashlib.sha256(torch.cat([v.flatten() for v in d["model"].values()]).numpy().tobytes()).hexdigest()
        assert digest==d["parameter_sha256"];hashes[d["global_step"]]=digest
    decoded=0;files=0
    for p in sorted((root/"validation").glob("*/*/summary.json")):
        v=load(p);identity=v["identity"];frames=identity["frames_per_snr"];step=identity["step"]
        assert identity["model_parameter_sha256"]==(hashes[step] if step is not None else None)
        for file,digest in v["artifacts_sha256"].items():assert sha256(p.parent/file)==digest
        for row in v["points"]:
            n=errors=rejects=bits=service=accepted=crcwrong=0;bce=0.
            for sh in range(32):
                file=f"snr-{row['snr_db']:.4f}-shard-{sh:02d}.npz"
                with np.load(p.parent/file,allow_pickle=False) as a:
                    assert len(a["bce"])==frames//32 and np.isfinite(a["bce"]).all()
                    wrong=a["bit_errors"]>0;rej=a["rejected"]
                    n+=len(wrong);errors+=int(wrong.sum());rejects+=int(rej.sum());bits+=int(a["bit_errors"].sum())
                    service+=int((wrong|rej).sum());accepted+=int((wrong&~rej).sum());crcwrong+=int((wrong&a["crc_ok"]).sum());bce+=float(a["bce"].astype(np.float64).sum())
                    if frames==100000:
                        with np.load(root/"validation/20k"/p.parent.name/file,allow_pickle=False) as b:
                            for key in ["bce","bit_errors","rejected","crc_ok"]:assert np.array_equal(a[key][:625],b[key])
            assert n==frames and errors==row["payload_frame_errors"] and rejects==row["rejected"] and bits==row["payload_bit_errors"]
            assert service==row["service_frame_errors"] and accepted==row["accepted_wrong"] and crcwrong==row["crc_passed_wrong"]
            assert math.isclose(bce/n,row["information_bce"],rel_tol=1e-14,abs_tol=1e-16)
            decoded+=n
        files+=1
    selection=load(root/"checkpoint_selection.json");step=selection["selected"]["step"]
    checkpoint=root/f"checkpoints/step-{step:05d}.pt"
    spec={"name":c.get("mechanism","ssm")+f"-seed{c['seed']}","kind":c.get("mechanism","ssm"),"seed":c["seed"],
          "alpha":c["alpha"],"checkpoint":str(checkpoint),"checkpoint_sha256":sha256(checkpoint),
          "parameter_sha256":selection["selected"]["model_parameter_sha256"],"step":step}
    configure()
    frozen=load(PLAN["frozen_inputs"]);cfg=next(x["full_config"] for x in frozen["configs"] if x["config_id"]==c["config_id"])
    link=NRLink(cfg);model=model_for(link,spec);post=post_checks(link,model,c["alpha"])
    result={"status":"passed","config_id":c["config_id"],"seed":c["seed"],"kind":spec["kind"],"steps":50000,
            "checkpoints":len(checkpoints),"validation_score_files":files,"decoded_validation_records":decoded,
            "selected_model":spec,"post_checks":post,"observations_matched_to_SSM_same_seed":matched_training_samples}
    save_json(root/"independent_audit.json",result);print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["endpoint","training"]);p.add_argument("--scope");p.add_argument("--output")
    a=p.parse_args()
    if a.mode=="endpoint":endpoint_audit(a.scope)
    else:training_audit(a.output)

