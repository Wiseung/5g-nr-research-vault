"""Regenerate a factual campaign report from completed stages only."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from endpoint import ROOT,LOG,OUT,PLAN,load,save_json
report=ROOT/f"{PLAN['run_id']}-独立终点测试与多种子机制对照进展.md"
link=lambda p,label:f"[{label}]({p.relative_to(ROOT)})"
lines=[f"**独立终点测试、多种子与机制对照：{PLAN['run_id']}**","",
       f"更新时间：{datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}。RTX4090 GPU0，FP32，TF32/AMP关闭，T20，early-stop/fallback关闭。原始commit {PLAN['commit']}，源码以哈希快照为准。","",
       "本轮顺序：已选seed17模型独立细网格pilot→冻结网格与每点200k帧测试→seed29/43同预算复现→静态阻尼、MLP、EMA、GRU机制对照。训练和测试阶段未完成的部分不写成结果。","",
       link(LOG/"preregistration.json","预登记与预算")+" · "+link(LOG/"pipeline_status.json","后台阶段状态")+" · "+link(OUT/"events.jsonl","采样事件日志"),""]
if (OUT/"test_grid_frozen.json").exists():
    grid=load(OUT/"test_grid_frozen.json")
    lines+=["冻结测试网格（由独立pilot确定，正式test不再改点）：","","|配置|Eb/N0/dB|每点N|","|---|---|---:|"]
    for cid,v in grid["configs"].items():lines.append(f"|{cid}|{v['snr_db']}|{v['frames_per_snr']}|")
    lines+=["",link(OUT/"test_grid_frozen.json","冻结网格")+" · "+link(OUT/"pilot_summary.json","pilot摘要"),""]
cohorts=[]
for p in sorted((OUT/"test").glob("*/summary.json")):
    s=load(p)
    if s["status"]=="passed":
        cohorts.append((p.parent.name,s))
        lines += [f"已完成测试 cohort：{p.parent.name}。","","|配置|方法|1e-3门限/dB|相对NMS收益/dB|配对95%CI/dB|bootstrap有效数|","|---|---|---:|---:|---|---:|"]
        for cid,v in s["configs"].items():
            for r in v["methods"]:
                fmt=lambda x:"N/A" if x is None else f"{x:.6f}"
                lines.append(f"|{cid}|{r['method']}|{fmt(r['crossing_db'])}|{fmt(r.get('gain_vs_NMS_db'))}|{r.get('gain_ci95_db')}|{r['bootstrap_valid']}/{r['bootstrap_total']}|")
        lines+=["",link(p,"原始摘要")]
        if (p.parent/"audit_summary.json").exists():lines.append(link(p.parent/"audit_summary.json","独立审计"))
        lines.append("")
        for cid in s["configs"]:
            point_summary=load(p.parent/cid/"summary.json")
            lines+=["|"+cid+"：Eb/N0/dB|方法|错误/N|payload BLER|拒收|service-FER|","|---:|---|---|---:|---:|---:|"]
            for point in point_summary["points"]:
                for row in point["methods"]:
                    lines.append(f"|{point['identity']['snr_db']:.4f}|{row['name']}|{row['payload_frame_errors']}/{row['frames']}|{row['payload_bler']:.7g}|{row['rejected']}|{row['service_frame_errors']/row['frames']:.7g}|")
            lines+=[""]
if cohorts:
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout="constrained")
    p=OUT/"test/seed17"
    for ax,c in zip(axes,PLAN["configs"]):
        file=p/c["config_id"]/"summary.json"
        if not file.exists():continue
        s=load(file)
        for mi,spec in enumerate(s["methods"]):
            xs=[];ys=[]
            for point in s["points"]:
                row=point["methods"][mi];x=point["identity"]["snr_db"];y=row["payload_bler"]
                if y>0:
                    lo,hi=row["bler_ci95"];ax.errorbar(x,y,yerr=[[y-lo],[hi-y]],fmt="o",color=f"C{mi}",capsize=2);xs.append(x);ys.append(y)
                else:ax.scatter(x,row["zero_error_one_sided95_upper"],marker="v",color=f"C{mi}")
            ax.plot(xs,ys,color=f"C{mi}",label=spec["name"])
        ax.axhline(.001,ls=":",color="black");ax.set(yscale="log",xlabel="Eb/N0 (dB)",ylabel="Payload BLER",title=c["config_id"])
        ax.grid(alpha=.2);ax.legend()
    fig.suptitle("Independent fixed-N test / 200k frames per point / T20 / seed17")
    fig.savefig(LOG/"seed17-endpoint.png",dpi=170);fig.savefig(LOG/"seed17-endpoint.pdf");plt.close(fig)
    lines+=["![seed17独立测试曲线]("+str((LOG/"seed17-endpoint.png").relative_to(ROOT))+")",""]
training=[]
for p in sorted((OUT/"training").glob("*/independent_audit.json")):
    d=load(p);s=load(p.parent/"summary.json")
    training.append(d)
    lines.append(f"训练完成并独立审计通过：{d['config_id']} / {d['kind']} / seed{d['seed']}，50000步，320万观测，选中{d['selected_model']['step']}步，裁剪率{s['gradient_clip_fraction']:.3%}。"+link(p,"审计"))
lines+=["","所有方法共享固定test观测，重复译码不能累计成独立样本；三种子各自报告，不能合并分母为3N。门限仅在相邻正BLER观测支持的区间内log插值；bootstrap含无效交点时常规区间标N/A，另保留条件区间及无效比例。区间未包含插值模型误差。","",
"机制架构与训练预算在seed17 test前登记，后续按同一规则完成所有对照，不根据已见test结果调参。尚未覆盖全部论文基线、syndrome2×2、结构分组、fallback、泛化和低BLER深测；这些不能由本轮替代。","",
"本轮没有Git提交或推送。"]
report.write_text("\n".join(lines)+"\n")
save_json(LOG/"report_summary.json",{"status":"updated","report":str(report),"completed_test_cohorts":[n for n,_ in cohorts],"completed_training_runs":len(training)})
print(str(report))

