"""Durable ordered campaign; failed gates stop downstream work and preserve logs."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,os,shutil,subprocess,sys,time,traceback
LOG=Path(__file__).resolve().parent;ROOT=LOG.parent.parent;CODE=LOG/"code"
sys.path.insert(0,str(CODE));sys.path.insert(0,str(ROOT))
from endpoint import PLAN,OUT,load,save_json,immutable,now,registry17
from nr_link import sha256
PY=PLAN["python"]
def emit(event,**kw):
    print(json.dumps({"time":now(),"event":event,**kw},ensure_ascii=False),flush=True)
def elapsed_hours():
    total=12.820297449166667 # conservative interrupted-stage charge, including downtime
    for p in LOG.glob("*/launch.json"):
        if p.parent.name=="pipeline":continue
        a=load(p);e=p.parent/"exit.json"
        if e.exists():
            end=load(e)["finished_at"];start=a.get("started_at")
            if start:total+=(datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds()
    return total/3600
def update(stage):
    launches={}
    for p in LOG.glob("*/launch.json"):
        a=load(p);e=p.parent/"exit.json"
        launches[p.parent.name]={"pid":a.get("pid"),"session":a.get("session_id"),"exit":load(e) if e.exists() else None}
    progress=load(OUT/"progress.json") if (OUT/"progress.json").exists() else None
    current=load(LOG/stage/"launch.json") if (LOG/stage/"launch.json").exists() else {}
    cmd=current.get("command",[])
    if "--output" in cmd:
        output=Path(cmd[cmd.index("--output")+1])
        if (output/"progress.json").exists():progress=load(output/"progress.json")
    save_json(LOG/"pipeline_status.json",{"status":"running","time":now(),"active_stage":stage,"stages":launches,
              "progress":progress,"completed_stage_wall_hours":elapsed_hours(),"free_disk_GiB":shutil.disk_usage(ROOT).free/2**30,"pid":os.getpid()})
def wait(name):
    directory=LOG/name;last=0.
    while not (directory/"exit.json").exists():
        if time.monotonic()-last>=60:
            update(name);a=load(directory/"launch.json");pid=a.get("pid")
            if pid and not Path(f"/proc/{pid}").exists():
                time.sleep(2)
                if not (directory/"exit.json").exists():raise RuntimeError((name,"process disappeared without exit record"))
            emit("monitor",stage=name,pid=pid,progress=load(LOG/"pipeline_status.json")["progress"])
            last=time.monotonic()
        time.sleep(5)
    result=load(directory/"exit.json");assert result["returncode"]==0,(name,result)
    emit("stage_passed",stage=name,**result);return result
def stage(name,command):
    if not (LOG/name).exists():
        assert elapsed_hours()<PLAN["scope_gpu_hour_cap"],"campaign resource cap reached"
        assert shutil.disk_usage(ROOT).free>12*2**30,"less than12GiB disk space; retaining all prior files"
        result=subprocess.run([sys.executable,"-B",str(LOG/"runner.py"),"launch","--name",name,"--",*command],cwd=ROOT,capture_output=True,text=True,check=True)
        emit("launched",stage=name,runner=result.stdout.strip())
    else:assert load(LOG/name/"launch.json")["command"]==command,(name,"command changed")
    return wait(name)
def code(name,*args):return [PY,"-B","-u",str(CODE/name),*map(str,args)]
def training(kind,seed,c):
    cid=c["config_id"];short="bg2" if "B1024" in cid else "bg1"
    name=f"{short}-{kind}-seed{seed}"
    output=OUT/"training"/name
    cmd=[PY,"-B","-u",str(ROOT/"train_formal.py")] if kind=="ssm" else [PY,"-B","-u",str(LOG/"launch_train_mechanism.py"),"--mechanism",kind]
    cmd+=["--output",str(output),"--config-id",cid,"--frozen",PLAN["frozen_inputs"],"--proof",PLAN["proof"],
          "--seed",str(seed),"--batch","64","--microbatch","64","--backend","cuda-graph","--stop-after","50000"]
    if name=="bg1-mlp-seed29":cmd += ["--resume"]
    stage("train-"+name,cmd)
    stage("audit-"+name,code("audit.py","training","--output",output))
    result=load(output/"independent_audit.json");assert result["status"]=="passed"
    return result["selected_model"]
def test_registry(registry):
    name=registry["cohort"];path=OUT/(name+"_registry.json");immutable(path,registry)
    stage("test-"+name,code("endpoint.py","test","--registry",path))
    stage("audit-test-"+name,code("audit.py","endpoint","--scope",name))
    stage("report-"+name,code("report.py"))
try:
    wait("pilot")
    stage("audit-pilot",code("audit.py","endpoint","--scope","pilot"))
    # This only verifies implementations; it is not a full ablation training run.
    stage("verify-mechanisms",code("verify_mechanisms.py"))
    hashes={str(p.relative_to(ROOT)):sha256(p) for p in CODE.glob("*") if p.is_file()}
    immutable(LOG/"campaign_code_frozen_before_test.json",{"time":load(LOG/"verify-mechanisms/exit.json")["finished_at"],"sha256":hashes})
    stage("freeze-test",code("endpoint.py","freeze"))
    test_registry(registry17())
    for seed in [29,43]:
        registry={"cohort":f"seed{seed}","configs":{}}
        for c in PLAN["configs"]:
            selected=training("ssm",seed,c)
            registry["configs"][c["config_id"]]=[{"name":"NMS","kind":"nms","alpha":c["alpha"]},selected]
        test_registry(registry)
    stage("calibrate-static",code("calibrate_static.py"))
    static=load(OUT/"static_registry.json")
    test_registry(static)
    for kind in ["mlp","ema","gru"]:
        for seed in [17,29,43]:
            registry={"cohort":f"{kind}-seed{seed}","configs":{}}
            for c in PLAN["configs"]:
                selected=training(kind,seed,c)
                registry["configs"][c["config_id"]]=[{"name":"NMS","kind":"nms","alpha":c["alpha"]},selected]
            test_registry(registry)
    stage("report-final",code("report.py"))
    # Verify immutable prior archives without including new files in their inventories.
    prior={}
    for run in ["20261113-214206-formal50k","20261114-165401-bg1-formal50k","20261114-233643-formal50k-analysis"]:
        index=ROOT/"logs"/run/"artifact_sha256.json";entries=load(index)
        assert sha256(index)==index.with_suffix(".sha256").read_text().split()[0]
        bad=[p for p,d in entries.items() if not (ROOT/p).exists() or sha256(ROOT/p)!=d];assert not bad,bad[:10]
        prior[run]=len(entries)
    saved=load(LOG/"campaign_code_frozen_before_test.json")["sha256"]
    assert all(sha256(ROOT/p)==d for p,d in saved.items())
    subprocess.run(["git","diff","--check"],cwd=ROOT,check=True)
    record={"status":"completed","finished_at":now(),"elapsed_stage_wall_hours":elapsed_hours(),"prior_archives_verified":prior,
            "training_runs":22,"test_cohorts":13,"no_git_commit_push":True,"report":load(LOG/"report_summary.json")["report"]}
    save_json(LOG/"completion_audit.json",record)
    files=[p for p in OUT.rglob("*") if p.is_file()]
    files += [p for p in LOG.rglob("*") if p.is_file() and "pipeline" not in p.relative_to(LOG).parts and p.name not in ["pipeline_status.json","artifact_sha256.json","artifact_sha256.sha256"]]
    files.append(Path(record["report"]))
    index=LOG/"artifact_sha256.json";save_json(index,{str(p.relative_to(ROOT)):sha256(p) for p in sorted(set(files))})
    index.with_suffix(".sha256").write_text(sha256(index)+"  "+index.name+"\n")
    save_json(LOG/"pipeline_status.json",record);emit("completed",**record)
except Exception as exc:
    failure={"status":"failed","time":now(),"error":repr(exc),"traceback":traceback.format_exc(),"preserved":True}
    save_json(LOG/"pipeline_failure.json",failure);save_json(LOG/"pipeline_status.json",failure);raise

