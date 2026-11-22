"""Aggregate diagnosis artifacts, export figure, and write a Chinese report."""
import hashlib
import json
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from diagnose import LOG, LOCAL, OUT, RUN_ID, dump


def read(name):return json.loads((OUT/name).read_text())
def jsonl(name):return [json.loads(x) for x in (OUT/name).read_text().splitlines()]
def med(xs):return float(np.median(list(xs)))
def quantiles(xs):
    a=np.asarray(list(xs))
    return {str(q):float(np.percentile(a,q)) for q in (0,25,50,75,90,95,99,100)}


rows=jsonl('replay.jsonl');profiles=jsonl('profiles.jsonl');graphs=jsonl('graph_controls.jsonl');history=read('history_analysis.json')
stats={}
for bg in (2,1):
    r=[v for v in rows if v['bg']==bg]
    head=[sum(p['squared_norm_share'] for p in v['parameters'] if p['name'].startswith('head.')) for v in r]
    eta=[t for v in r for t in v['eta_by_iteration']]
    stats[f'bg{bg}']={'gradient_norm_quantiles':quantiles(v['gradient_norm'] for v in r),
        'head_squared_norm_share_quantiles':quantiles(head),'clip_coefficient_quantiles':quantiles(v['clip_coefficient'] for v in r),
        'optimizer_delta_norm_quantiles':quantiles(v['optimizer_delta_norm'] for v in r),
        'max_optimizer_delta_relative_norm':max(v['optimizer_delta_relative_norm'] for v in r),
        'eta_min':min(t['min'] for t in eta),'eta_max':max(t['max'] for t in eta),
        'replay_fidelity':read(f'bg{bg}-replay-fidelity.json')}
profile_summary=[]
for bg in (2,1):
    for ckpt in ('initial','final'):
        for snr in (0.,.5,1.,1.5,2.):
            r=[v for v in profiles if v['bg']==bg and v['checkpoint']==ckpt and v['snr_db']==snr]
            profile_summary.append({'bg':bg,'checkpoint':ckpt,'snr_db':snr,'batches':len(r),
                'gradient_norm_quantiles':quantiles(v['gradient_norm'] for v in r),
                'mean_loss':float(np.mean([v['loss'] for v in r])),
                'clip_fraction':float(np.mean([v['gradient_norm']>1 for v in r]))})
graph_summary=[]
for cid in sorted(set(v['config_id'] for v in graphs),key=lambda x:next(v['B'] for v in graphs if v['config_id']==x)):
    r=[v for v in graphs if v['config_id']==cid]
    graph_summary.append({'config_id':cid,'B':r[0]['B'],'bg':r[0]['bg'],
        'median_eta_gradient_norm':med(v['independent_eta_gradient_norm'] for v in r),
        'median_eta_gradient_rms':med(v['independent_eta_gradient_rms'] for v in r),
        'mean_loss':float(np.mean([v['loss'] for v in r])),
        'row_degrees':r[0]['row_degree_min_mean_max'],'column_degrees':r[0]['col_degree_min_mean_max']})
details={p.stem:json.loads(p.read_text()) for p in OUT.glob('bg*-detail-*.json')}
fd={f'bg{bg}':read(f'bg{bg}-finite-difference.json') for bg in (2,1)}
branch={f'bg{bg}':read(f'bg{bg}-branch-audit.json') for bg in (2,1)}
env=read('environment.json')
summary={'run_id':RUN_ID,'status':'diagnosis_completed','formal_training':False,'production_math_lr_clip_changed':False,
         'replay_statistics':stats,'fixed_snr_profiles':profile_summary,'constant_damping_controls':graph_summary,
         'details':details,'finite_differences':fd,'branch_audits':branch,
         'findings':['Large gradients localize to head parameters and cross-iteration NMS message backpropagation.',
                     'Detaching the SSM state gradient barely changes the observed norms; detaching NMS messages changes the backward definition and removes amplification.',
                     'Mean BCE normalization, finite values and traced/production gradient equivalence checks pass.',
                     'FP64 frozen-feature finite differences validate the specified surrogate in one head-bias direction on two selected batches.',
                     'BG1 has a narrow local region with stable min/sign/clip choices; finite steps can cross many branches.',
                     'Current evidence is bounded engineering diagnosis, not a convergence guarantee or a BLER claim.']}
dump('summary.json',summary)

plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.25,'savefig.dpi':180})
fig,ax=plt.subplots(2,3,figsize=(16,9),layout='constrained')
colors={1:'#d55e00',2:'#0072b2'}
for bg in (2,1):
    r=[v for v in rows if v['bg']==bg]
    ax[0,0].semilogy([v['step'] for v in r],[v['gradient_norm'] for v in r],color=colors[bg],label=f'BG{bg}',alpha=.85)
    ax[0,1].plot([v['step'] for v in r],[100*sum(p['squared_norm_share'] for p in v['parameters'] if p['name'].startswith('head.')) for v in r],color=colors[bg],label=f'BG{bg}')
    d=details[f'bg{bg}-detail-'+('5' if bg==1 else '16')]
    ax[0,2].semilogy([v['T'] for v in d['horizons']],[v['gradient_norm'] for v in d['horizons']],'-o',color=colors[bg],label=f'BG{bg} selected high-norm batch')
    a=d['baseline']['adjoints']
    ax[1,0].semilogy([v['t'] for v in a],[v['eta_grad_norm'] for v in a],'-o',color=colors[bg],markersize=3,label=f'BG{bg}')
    for ckpt,style in [('initial','-o'),('final','--s')]:
        s=[v for v in profile_summary if v['bg']==bg and v['checkpoint']==ckpt]
        ax[1,1].semilogy([v['snr_db'] for v in s],[max(1e-8,v['gradient_norm_quantiles']['50']) for v in s],style,color=colors[bg],label=f'BG{bg} {ckpt}')
ax[0,0].axhline(1,color='black',linestyle=':',label='clip=1')
ax[0,0].set(title='Original 100-step replay, before clipping',xlabel='Optimizer step',ylabel='Global gradient L2 norm');ax[0,0].legend()
ax[0,1].set(title='Head weight+bias contribution',xlabel='Optimizer step',ylabel='Share of squared gradient norm (%)',ylim=(90,100.3));ax[0,1].legend()
ax[0,2].set(title='Same weights/data, shorter unrolling',xlabel='Decoder iterations T',ylabel='Gradient L2 norm');ax[0,2].legend(fontsize=8)
ax[1,0].set(title='T20 loss gradient w.r.t. damping at each t',xlabel='Forward iteration t',ylabel='||d loss / d eta_t||');ax[1,0].legend()
ax[1,1].axhline(1,color='black',linestyle=':');ax[1,1].set(title='Frozen-model SNR probes (4 batches/point)',xlabel='Payload Eb/N0 (dB)',ylabel='Median gradient norm (floor 1e-8)');ax[1,1].legend(fontsize=8)
d=fd['bg1'];q=[v for v in d['differences'] if v['features_frozen']]
ax[1,2].semilogx([v['epsilon'] for v in q],[v['central_difference'] for v in q],'-o',color=colors[1],label='Frozen-feature central difference')
ax[1,2].axhline(d['surrogate_autograd'],color='black',linestyle='--',label='Autograd (FP64)')
ax[1,2].set(title='BG1 head-bias sensitivity, FP64 diagnostic',xlabel='Head-bias perturbation epsilon',ylabel='Directional derivative');ax[1,2].legend(fontsize=8)
fig.suptitle('BG1 gradient diagnosis on RTX 4090: reference equations unchanged',fontsize=15)
fig.savefig(OUT/'gradient_diagnosis.png');fig.savefig(OUT/'gradient_diagnosis.pdf');plt.close(fig)

report=[]
def para(text):report.append(text+'\n\n')
def table(header,body):
    report.append('| '+' | '.join(header)+' |\n|'+ '|'.join(['---']*len(header))+'|\n')
    for row in body:report.append('| '+' | '.join(map(str,row))+' |\n')
    report.append('\n')
def link(path,label):return f'[{label}](./{path.relative_to(LOCAL).as_posix()})'
para('# 2026-11-13 BG1 梯度范数专项诊断')
para(f'RUN_ID：`{RUN_ID}`。RTX 4090 GPU 0，FP32 原训练复跑；TF32/AMP 关闭。commit `{env["git_commit"]}`。本轮完成两配置各100步原样复跑、固定模型/SNR检查、分参数/分轮/分码字梯度分解、无 SSM 的常阻尼对照及数值导数校验。全部为独立诊断，正式训练未启动。')
para('## 结论与证据边界')
para('**当前观测到的 BG1 大范数主要来自 T20 flooding NMS 消息链对阻尼的反向敏感性，梯度集中在阻尼输出 head；没有证据表明是 SSM 状态失控、漏做 BCE 均值归一化，或一次反传实现错误。** 不能仅凭全局范数大或100%裁剪断言训练发散；本轮也没有证明后续长训练稳定。')
para('高范数既存在于初始模型，也存在于100步后的冻结模型。它受噪声难度、具体码字和分段 min/sign/clip 轨迹影响；较大的 BG1 图度数与更强的实测消息链放大相容，但本轮没有测定谱半径，也没有隔离每一种图结构因素，不能把某个度数直接当作唯一因果解释。')
para('## 原运行复现与统计')
para('逐步使用原 seed17、在线样本键、batch8、T20、alpha=0.8、AdamW LR=1e-3、clip=1、统计 detach/状态保留梯度及原 weight-decay 分组。加观察钩子，不改前向或优化设置。两份复跑最终参数与原检查点逐元素一致；loss 最大差异均为0。记录范数时归约路径的末位差异不影响更新。')
table(['配置','范数 p50 / p95 / max','裁剪比例','head 梯度平方范数占比：p50 / min','复跑与原范数最大绝对差'],[
    [f'BG{bg}',f"{stats[f'bg{bg}']['gradient_norm_quantiles']['50']:.5f} / {stats[f'bg{bg}']['gradient_norm_quantiles']['95']:.5f} / {stats[f'bg{bg}']['gradient_norm_quantiles']['100']:.5f}",
     '100%' if bg==1 else '76%',f"{100*stats[f'bg{bg}']['head_squared_norm_share_quantiles']['50']:.4f}% / {100*stats[f'bg{bg}']['head_squared_norm_share_quantiles']['0']:.4f}%",
     f"{stats[f'bg{bg}']['replay_fidelity']['max_gradient_norm_abs_diff']:.8g}"] for bg in (2,1)])
para('BG1 第1步范数为40.2585，原运行最大值在第5步为149.790；每20步窗口的范数中位数依次为48.876/37.084/50.663/62.181/60.344，没有观察到在100步内单调爆增。与训练步数的 Spearman 相关约0.162，与状态绝对值最大值约0.033，与 loss 约0.360，与批次平均 SNR 约−0.365；这些是同一短轨迹上的描述统计，不作独立因果或显著性结论。')
para(f"BG1 的 eta 在全部复跑前向中范围为 [{stats['bg1']['eta_min']:.6f}, {stats['bg1']['eta_max']:.6f}]，仍接近初始化0.05；状态保持原有界。裁剪系数中位数 {stats['bg1']['clip_coefficient_quantiles']['50']:.6f}，最小 {stats['bg1']['clip_coefficient_quantiles']['0']:.6f}。全模型 AdamW 实际更新 L2 范数中位数为 {stats['bg1']['optimizer_delta_norm_quantiles']['50']:.6f}，最大相对参数 L2 范数为 {stats['bg1']['max_optimizer_delta_relative_norm']:.6f}。AdamW 有矩估计与逐坐标归一化，裁剪系数不是简单的有效学习率倍数；全局相对更新小也不证明每个参数或长期优化都稳定。")
para('## 区分 SSM 状态链与 NMS 消息链')
para('诊断 trace 的前向输出及参数梯度与未改动的 NRLink.decode 逐元素一致（四个被选批次最大差异均0）。两个对照只改变反向路径，前向不变、从未优化，也不是生产算法修复：detach_state 每轮切断 h 的历史梯度；detach_messages 每轮切断 U/R 的历史梯度，仍保留 SSM 状态链。后一种已经改变原训练导数定义，不能直接用于正式训练。')
table(['配置/原步号','完整反传','只断 SSM 状态链','只断 NMS 消息链','前向最大差异'],[
    [f"BG{d['bg']} / {d['step_before']}",f"{d['baseline']['gradient_norm']:.6f}",f"{d['counterfactuals'][0]['gradient_norm']:.6f}",f"{d['counterfactuals'][1]['gradient_norm']:.6f}",
     max(x['forward_max_difference'] for x in d['counterfactuals'])] for d in sorted(details.values(),key=lambda d:(d['bg'],d['step_before']))])
para('BG1 第5步切断 NMS 消息链后范数降低约12,677倍，而切断 SSM 状态链几乎没有影响。对应完整反传中，第1/10/20轮 eta 的梯度范数分别为229.446/1.010/0.004295；第1/20轮 R 消息的梯度范数为1063.142/0.001918。该结果直接显示早期消息承受来自后期监督的巨大反向放大；这些范数比值不是局部 Jacobian 谱半径。')
table(['选定批次','T5','T10','T15','T20'],[
    [f"BG{d['bg']} / 步{d['step_before']}"]+[f"{h['gradient_norm']:.6f}" for h in d['horizons']]
    for d in sorted(details.values(),key=lambda d:(d['bg'],d['step_before']))])
para('T 对照在同一模型/输入下按相同“末四轮加权 BCE”规则计算，因此监督时刻随 T 改变；它支持迭代深度与敏感性相关，不能当作相同目标下的纯 Jacobian 测量，更不能作为不同 T 的 BLER 或性能排名。单独分解第17/18/19/20轮 BCE 后，BG1 第5步的未加权参数梯度范数分别为18.464/15.582/72.274/238.655，说明放大也存在于单个监督项，不是四项误相加或漏除15。')
para('## 为什么状态有界仍会出现大梯度')
para('协议将统计特征 detach。固定这些输入时，SSM 状态的历史 Jacobian 就是对角衰减 a=exp(−Delta·lambda)，逐元素介于0和1；状态幅值有界与实测 detach_state 对照相符。但 R/U 仍沿完整译码迭代链保留梯度。')
para('忽略已显式保留的 filler/clip 投影，并将按行广播的阻尼记为对角阵 D，消息的局部递推导数可写成 `J_t ≈ (I−D_t)·alpha·M_t·(G·S−I)+D_t`，其中 G/S 是图 gather/scatter，M_t 是当前 min-sum 分支导数。该式并没有“小于1”的保证；反传包含多个 J_t 的乘积。按 batch 与 B 取均值只规范化损失尺度，不消除这个乘积。这里没有先clip posterior再形成extrinsic，数学定义保持原样。')
para('初始 head 权重约1e−6，也使传入控制器内部的梯度初期较小；head 本身仍直接承受 `d loss/d eta`。因此“head占比高”不能解读成已经证明选择性记忆有效，亦不能据此认为修改 SSM 状态归一化就会解决主要放大。')
para('## 固定 SNR、码字与图对照')
para('冻结原始初始/100步模型，在0/0.5/1/1.5/2 dB每点4个batch8；同配置的初始/最终模型复用相同32帧。共80次批次梯度求值，对应320个独立样本、640帧次评估。各点样本很少，仅作定位，不用于估计正式BLER。')
table(['配置/权重','0 dB','0.5 dB','1.0 dB','1.5 dB','2.0 dB'],[
    [f'BG{bg} / {ckpt}']+[f"{next(v for v in profile_summary if v['bg']==bg and v['checkpoint']==ckpt and v['snr_db']==snr)['gradient_norm_quantiles']['50']:.6g}"
    for snr in (0.,.5,1.,1.5,2.)] for bg in (2,1) for ckpt in ('initial','final')])
para('表中为每点4批次的范数中位数。BG1 已在未训练模型的低SNR区出现大范数，高SNR充分译对后梯度接近零。原0–2dB混合batch常包含多个难码字，解释了为何混合训练每步都可能裁剪；不能从这个小样本反推正式训练应该删掉哪些SNR。')
d=details['bg1-detail-5'];snrs=history['bg1']['expanded_history'][4]['snrs_db']
table(['BG1 步5的样本下标（0起）','SNR dB','单码字平均BCE','单码字全参数梯度范数'],[
    [r['sample'],f"{snrs[r['sample']]:.6f}",f"{r['loss']:.8g}",f"{r['gradient_norm']:.6g}"] for r in d['per_frame']])
para(f"各码字梯度按1/8求和与直接batch梯度的逐参数最大差异仅 {d['per_frame_average_vs_batch_gradient_max_difference']:.8g}。主要贡献来自两个难码字，其中单码字范数902.36和288.61；这验证了batch/B均值没有遗漏。已经收敛到高置信正确译码的码字对当前梯度几乎无贡献。")
para('进一步使用完全相同的常数 eta=0.05，在每轮/每码字/每基行独立放置可求导阻尼叶子，移除 SSM 权重参数化；所有配置均取manifest中的R1/2、1dB、4×batch8，不进行更新。下表为阻尼叶子联合梯度的中位数及RMS，RMS用于说明不是仅因阻尼叶子个数不同。')
table(['配置','阻尼梯度 L2 中位数','阻尼梯度 RMS 中位数','平均BCE','行度 min/mean/max','列度 min/mean/max'],[
    [r['config_id'],f"{r['median_eta_gradient_norm']:.6f}",f"{r['median_eta_gradient_rms']:.6f}",f"{r['mean_loss']:.6f}",
     '/'.join(f'{x:.3g}' for x in r['row_degrees']),'/'.join(f'{x:.3g}' for x in r['column_degrees'])] for r in graph_summary])
para('在这组受限对照里，BG1 两个长度都保持明显更大的阻尼敏感性；同一BG内并不随B单调增加。因此单纯“码长更多信息位所以梯度相加更多”的解释不成立。不同图、长度、filler及错误难度仍相互耦合，不能仅凭本表证明某个度数导致精确多少倍放大。')
para('## 代理梯度、数值精度与分支切换')
para('协议明确采用“统计detach”的代理梯度。为让数值微分检验同一个目标，本检查冻结每轮统计特征，保留全部状态与消息递推，对 head.bias 做中心差分；另记录重算统计的闭环结果但不把它当代理梯度的验收标准。FP64仅用于冻结模型的数值诊断，全部训练仍为FP32。FP64 BCE标签与中间量同精度；诊断脚本局部适配条件累加dtype，未修改生产nr_link.py。')
table(['配置/批次','FP64自动导数','epsilon=1e−9中心差分','相对误差'],[
    [f"BG{bg} / 原步{fd[f'bg{bg}']['step_before']}",f"{fd[f'bg{bg}']['surrogate_autograd']:.9f}",
     f"{next(r for r in fd[f'bg{bg}']['differences'] if r['epsilon']==1e-9 and r['features_frozen'])['central_difference']:.9f}",
     f"{next(r for r in fd[f'bg{bg}']['differences'] if r['epsilon']==1e-9 and r['features_frozen'])['relative_error_vs_surrogate_autograd']:.3g}"] for bg in (2,1)])
para('BG1 在epsilon=1e−3时中心差分为+2.03556，与局部自动导数−38.06160相反；1e−4时为−10.73188。不能用较大步长有限差分的不同方向直接断定autograd错误，也不能把这里的局部导数视为LR=1e−3实际AdamW更新后的收益预测。head.bias一维扰动不是整个AdamW更新方向。')
b=branch['bg1']['records']
table(['BG1 head.bias扰动','符号','最小值索引切换总次数','Q符号切换总次数','Q裁剪状态切换总次数'],[
    [r['epsilon'],r['direction'],r['min_index_changed_total'],r['q_sign_changed_total'],r['q_clip_status_changed_total']] for r in b])
para('次数按所有码字、校验/边及20轮累计，重复轮次不是独立样本。1e−3时约3.7万次最小值索引、6.6–6.8万次Q符号切换；1e−7仍有少量切换，1e−9在这两个方向未观察到切换。结合小扰动数值导数收敛，说明BG1选定轨迹的稳定局部分支区间很窄。该证据不把所有分段非光滑性等同于故障，也没有证明每个训练步都如此。')
para('## 对后续工作的具体建议')
para('1. **保留当前clip=1和原实现作为基准。** 大梯度已定位，但尚无证据支持直接提高阈值；那会改变所有参数的裁剪比例。不要用“提高阈值后不再触发”当问题解决，也不把detach_messages诊断对照并入训练。\n2. **先完成正式pilot和alpha标定。** 目前0–2dB、alpha=0.8是调试设置，包含大量难译码字；正式gamma_ref与同一NMS基线冻结后，重新测梯度分布，避免把调试采样区间当训练结论。\n3. **正式runner保留这次观察字段。** 至少记录裁剪前/后范数与系数、head/其余参数梯度份额、按SNR的批次组成、少量固定批次的eta梯度随t曲线、AdamW实际更新和固定验证BCE。仅100%裁剪报警不足以判断异常。\n4. **如需优化稳定性，独立比较设置。** 先在相同样本流、固定验证集、原T20下比较协议warmup/cosine与当前constant-debug设置；学习率、clip阈值、head参数化或截断反传的改变都应另建实验、分别记录，保持观测数与验证预算一致。截断消息梯度会改变代理梯度定义，需明确标注并重新过对称性/有限性门。\n5. **验证实际优化效果与多种子。** 可先做有界的三种子pilot后试跑，以固定验证BCE、误帧及参数更新稳定性评估；不能仅选择较小梯度的配置。本次未执行这些新调参实验，未启动50k训练。')
para('## 产物、异常与复现')
para(f"{link(OUT/'gradient_diagnosis.png','诊断图 PNG')}；{link(OUT/'gradient_diagnosis.pdf','诊断图 PDF')}；{link(OUT/'summary.json','机器可读汇总')}。")
para('![BG1梯度诊断图](./results/'+RUN_ID+'/gradient_diagnosis.png)')
para(f"原始数据：{link(OUT/'replay.jsonl','逐步分参数/分轮复跑')}；{link(OUT/'history_analysis.json','原历史与SNR重建')}；{link(OUT/'profiles.jsonl','固定SNR梯度')}；{link(OUT/'graph_controls.jsonl','常阻尼图对照')}；详细批次分解、数值差分、分支切换分别保存在同结果目录的 `bg*-detail-*.json`、`bg*-finite-difference.json`、`bg*-branch-audit.json`。诊断快照均注明formal_training=false，不覆盖原训练检查点。")
for stage in ('replay','profiles','detail','finite-difference','finite-difference-retry','finite-difference-fp64','graph-controls','branch-audit'):
    path=LOG/stage;l=json.loads((path/'launch.json').read_text());e=json.loads((path/'exit.json').read_text())
    para(f"- `{stage}`：PID `{l['pid']}`，setsid会话 `{l['session_id']}`，退出码 `{e['returncode']}`；{link(path/'launch.json','实际命令')} / {link(path/'stdout.log','stdout')} / {link(path/'stderr.log','stderr')} / {link(path/'exit.json','退出记录')}。")
para('保留两次FP64诊断入口失败：第一次是自产诊断bundle包含NumPy数组而weights_only读取拒绝，改为仅对该可信自产bundle正常读取；第二次是生产特征计算硬编码FP32，double条件累加发生dtype不匹配，改为诊断脚本内同公式按输入dtype累加。两次失败均未发生优化更新，失败源码、原因和日志保留。成功重跑退出码0，没有降低正确性阈值。原训练检查点继续使用weights_only=True读取。')
para('复跑观察脚本产生一次“requires_grad张量转float”的记录告警，位置在只读比较最终参数差异处，不参与前向/反向或优化；计算结果与原检查点逐元素一致。所有GPU任务采用独立后台监督进程，stdout/stderr直连文件，记录原始退出码，无管道吞错。')
para(f"软件、manifest与原源文件哈希见{link(OUT/'environment.json','环境记录')}及{link(OUT/'environment-freeze.txt','依赖快照')}。本轮只新增诊断脚本、日志、结果和报告；原数学定义、学习率、clip阈值、源文件、原报告及原检查点保持原样。没有Git提交或推送。")
report_path=LOCAL/'20261113-BG1梯度范数专项诊断报告-160241.md'
report_path.write_text(''.join(report))
print(json.dumps({'report':str(report_path),'summary':str(OUT/'summary.json'),'figures':[str(OUT/'gradient_diagnosis.png'),str(OUT/'gradient_diagnosis.pdf')]},ensure_ascii=False))
