# S2* v0：QC 基行级选择性迭代记忆 + flooding NMS

状态：实现规格；没有训练结果或 GPU 基准。库版本、编译器、CUDA/Triton、Mamba-1/2 后端支持均待核实。

本目录不包含完整 NR 编码器。标准图表、CRC、速率匹配必须由经对拍的适配器提供。

## 1. 固定定义

- BG2：R=42 个基行，C=52 个基列，P=197 个非零循环子块。
- N=52Z，M=42Z，E_g=197Z；E_tx 单独表示发送位数。
- 默认 Z=128：N=6656、M=5376、E_g=25216、B_info=1280、A_payload=1264、E_tx=2560、RV0。
- batch 用 b 表示；不要与编码输入 B_info 或 SSM 的 B 参数混淆。
- LLR 定义 L=log(P(c=0|y)/P(c=1|y))，硬判决 1[L<0]。
- 学习阻尼 eta；NMS alpha 由验证集标定后冻结，0.8 只是初始候选。
- 每码字、每基行、每 SSM 层有独立状态；共享全部控制器权重，状态不跨码字继承。

## 2. QC 图和张量

选择 Z 对应的 lifting set，再读取该 set 的整数移位并模 Z。Z=96 用 iLS=1，Z=128 用 iLS=0。

按 (base_row, base_column) 排序非零子块 e，保存 row[e]、col[e]、shift[e]、row_ptr[R+1]。

约定：H[(r,z),(c,(z+s_rc) mod Z)]=1。

gather(X)[b,e,z] = X[b,col[e],(z+shift[e]) mod Z]。

scatter(R)[b,c,j] = sum_{e:col[e]=c} R[b,e,(j-shift[e]) mod Z]。

gather 对应 roll(X_c,-s)，scatter 对应 roll(R_e,+s)。第三方图表的旋转约定必须先对拍。

张量：

| 名称 | 形状 |
|---|---|
| Lch、U、L | [b,52,Z] |
| Q、Rold、Rnew | [b,197,Z] |
| syndrome、resolved | [b,42,Z] |
| dynamic features f | [b,42,8] |
| external condition c | [b,42,8] |
| row embedding | [42,4] |
| controller x | [b,42,16] |
| state | [b,42,layers,expand*d_model,d_state] |
| eta | [b,42,1]，按 row[e] 广播到边 |

不学习 col/z 绝对位置嵌入；结构已通过精确 H 消息传递进入。row embedding 跨 Z 共享，只覆盖同一 BG。
存储只用 P=197 个真实子块，不全局补齐为 R*d_max=420 个子块。

## 3. 精确迭代顺序

初始化 R^0=0、U^0=Lch、全部 h=0。U 保存未饱和的 posterior，L=clip(U,-20,20) 仅用于输出/特征/损失。
每次都将 filler 的 U、L、Q 固定为 +20。

第 t 次迭代使用 t-1 时刻特征：

Q^t = clip(gather(U^{t-1})-R^{t-1},-20,20)。

MS^t_ez = product_{j in same check,j!=e} sign(Q^t_jz) * min_{j!=e}|Q^t_jz|。
sign(0)=+1。用第一/第二最小值实现，正确处理并列最小值。

R^t_ez = clip((1-eta_{r,t}) * alpha * MS^t_ez + eta_{r,t} * R^{t-1}_ez,-20,20)。

U^t = Lch + scatter(R^t)。filler 重新固定为 +20。

注意：不能先 clip(U) 再减 R 形成 extrinsic，否则改变了饱和的 NMS 定义。

## 4. 特征与条件化

硬 syndrome s_rz = XOR_{e:row[e]=r} 1[L_{v(e,z)}<0]。
resolved a_rz = AND_{e:row[e]=r} 1[|L_{v(e,z)}|>1e-6]；filler 为已知位。

输入违反率 u_r = sum_z a_rz*s_rz / max(1,sum_z a_rz)，coverage chi_r=mean_z a_rz。
这是已解析校验中的违反率，不能当作全量 syndrome 早停。

mean_r 以下均在该行关联的所有非 filler 边上计算，分母至少为 1。

f_r=[u, u-u_prev, mean|Q|/20, mean|R|/20,
     mean|R-R_prev|/40, mean max(0,1-|L_aligned|/2), t_completed/20, chi]。

初始 R 差分为零，初始 u_prev=u_initial。统计张量 stop_gradient；状态链保留梯度。
这明确采用截断统计反馈的代理梯度，不是整个闭环的完整导数；连续统计不detach可作单独消融。

每个完整图变量保存观察次数 nu 和 filler 标记 F。非 filler 分为 nu=0、nu=1、nu>=2。
条件 c_r=[u,du,gamma_norm,gamma_known,p_unobserved,p_filler,p_repeated,mean log(1+min(nu,4))/log(5)]。
比例按该基行邻域计算。默认 gamma_norm=gamma_known=0，不输入 oracle SNR。
打开 SNR 条件时，gamma_norm=clip((EbN0_dB-gamma_center)/2,-2,2)，center 为固定训练配置常量。
AWGN v0 不输入 CSI；衰落或有色噪声不属于本实现范围。

控制器输入 x=W_f*[f;row_embedding]+bias，12->16。

每层：

z=RMSNorm(x)；U=tanh(W_u*z+b_u)；G=sigmoid(W_g*z+b_g)，U/G 维度 h=expand*d_model。
Delta=0.25+1.75*sigmoid(W_delta*U+V_delta*c+b_delta)。
Bsel=tanh(W_B*U+b_B)，Csel=tanh(W_C*U+b_C)，均为 d_state 维。
lambda=1/32+(2-1/32)*sigmoid(theta)，维度 [h,d_state]。
a=exp(-Delta[:,:,None]*lambda)。
h_new=a*h_old+(1-a)*Bsel[:,None,:]*U[:,:,None]。
y=sum_state(Csel*h_new)+Dskip*U。
x=x+W_out*(G*y)+b_out。

最后 eta=0.5*sigmoid(W_head*RMSNorm(x)+b_head)。
Delta/B/C 外部条件默认仅直接作用于 Delta；syndrome 已经通过 f 影响所有选择性参数。
V_B/V_C 和 FiLM 是互斥的附加消融，不在默认网络中叠加。
FiLM 对照：z'=(1+0.1*tanh(W_gamma*c))*z+0.1*tanh(W_beta*c)。

这是归一化驱动的 ZOH selective diagonal SSM，不等于官方 Mamba-1/2。
其连续形式为 dh/dtau=-lambda*h+lambda*Bsel*U；每步输入保持常数后得到上式。
因为 |U|<=1、|Bsel|<=1、0<a<1、h0=0，所以逐元素 |h|<=1。

初始化：row embedding用N(0,.02^2)，普通投影用Xavier；norm scale=1，Dskip=1。
lambda的初值对应时间常数tau=[1,2,4,8]（单位：一次译码迭代），即lambda=1/tau；
theta=logit((lambda-1/32)/(2-1/32))。W_delta和V_delta初始为0，b_delta=log(3/4)，故Delta初值=1。
head weight用N(0,1e-6)，b_head=log(1/9)，故eta初值接近.05。

## 5. 损失

信息集合 I 为 K=10Z 个系统位中去掉 filler 后的集合，包含 TB CRC，不包含不存在的 CB CRC。
ell_BCE(t)=mean_{v in I} softplus(-(1-2*c_v)*L_v^t)。
最后四轮监督权重为 [1,2,4,8]/15。

ell_syn(T)=mean_checks (1-product_{v in N(check)} tanh(L_v^T/2))/2。
训练用 FP32；这是辅助校验损失，不提供合法码字保证。

loss=sum_last4 w_t*ell_BCE(t)+lambda_syn(step)*ell_syn(T)+lambda_KD*ell_KD。
lambda_syn 前 5000 步为 0，5000->10000 线性升至 .02，之后 .02。
KD 默认关闭。可选 teacher 为独立 NMS-50，温度 2，权重 .05；teacher 参数不反传，在线产生或缓存。
KD 使用 Bernoulli KL(p_teacher||p_student)，p=sigmoid(-L/temperature)，乘 temperature^2。
只接受 teacher 信息位全正确的训练样本；若没有合格样本，KD 项为 0。

## 6. 速率恢复与停止

适配器提供 tx_to_full[E_tx]，已经包含去交织、circular buffer、固定首 2Z 打孔、RV、跳过 filler。
Lch_v=clip(sum_{j:tx_to_full[j]=v} Lrx_j,-20,20)；nu_v=count(j)。先累加再饱和。
未观察位 Lch=0；filler 固定 +20。
重复的接收噪声独立，逐次产生 Lrx 再累加，不能复制同一个噪声样本。
缓存可按 config 共享，但 nu、filler、索引必须和本批配置一致。

训练固定轮数，不早停，不执行 fallback，完整保留固定四个监督时刻。
推理每轮判断全量 H*hard(L)=0、TB CRC 通过、非 filler 位不存在精确/数值零值歧义。
通过才接受；达到 20 轮仍失败则关闭控制器，eta=0，warm-start 继续 NMS 最多 10 轮。
总上限 30 轮；这不是从 Lch 重启的普通 NMS-30。cold-restart 是单独消融，成本另计。

P_fb=N_enter_fallback/N_frames。
P_rescue=N_fallback_and_final_correct_accepted/N_enter_fallback。
还记录最终失败率、syndrome通过但CRC失败率、CRC通过但信息错误率，以及平均额外迭代数。
失败码块在整体 BLER 中计为错误；不能只报告被接受码块的条件 BLER。

## 7. 前向伪代码

```python
Lch, nu, filler = rate_recover(rx_llr, tx_to_full, config)
graph = graph_cache[(BG, Z)]
R = zeros(b, P, Z)
U = clamp_filler(Lch)
state = zeros(b, Rrows, layers, inner, d_state)
delta_R_summary = zeros(b, Rrows)
u_prev = initial_masked_syndrome(U)
active = ones(b, dtype=bool)
history = []

for t in range(T_neural):
    Q = clip(gather(U) - R, -20, 20)
    Q = force_filler_edges(Q, +20)
    f, c, u_now = features(U, Q, R, delta_R_summary, u_prev, nu, filler, t)
    eta, state_new = controller(f.detach(), c.detach(), state)
    # Eval: freeze state and accepted outputs for inactive frames.
    state = where(active, state_new, state)
    ms = check_node_min1_min2(Q, graph)
    Rnew = clip((1-eta[row])*alpha*ms + eta[row]*R, -20, 20)
    Unew = force_filler_variables(Lch + scatter(Rnew), +20)
    delta_R_summary_new = row_mean_abs(Rnew - R)
    R, U = update_active_or_all_training(R, U, Rnew, Unew, active)
    delta_R_summary = update_active(delta_R_summary_new, active)
    u_prev = update_active(u_now, active)
    if training and t in supervised_times:
        history.append(clip(U, -20, 20))
    if not training:
        active &= ~accept_full_syndrome_crc_and_resolved(U)
        if not active.any(): break

if not training:
    entered_fallback = active.clone()
    # Same NMS code, eta=0, alpha frozen, warm-start R/U; freeze accepted frames.
    R, U, active, extra_iters = nms_continue(R, U, Lch, active, max_additional=10)
    return hard(U), ~active, entered_fallback, extra_iters
return losses(history, labels, graph)
```

固定形状掩码实现可用于正确性；它仍执行 inactive 帧的算术，不能把逻辑停止迭代数当作实际节省。
batch=1 或真实 active compaction 才能直接兑现早停节省，compaction 开销必须计时。

## 8. 训练

- 训练 Z=96/128 的 batch 交替；一个 batch 不混 Z、不 padding。
- 每码字独立采样 SNR。先在验证集找 NMS-20 的 BLER≈0.1 对应 gamma_Z。
- 0->5000 步：T=10，gamma_Z+Uniform(0,1)dB；之后 T=20，gamma_Z+Uniform(-1,1)dB。
- 50k 步是预算初值，batch64 共 3.2M 次在线信道采样；先单种子，再扩至 3 种子。
- BPSK 等效实信道 x=1-2c，sigma^2=1/(2*(A_payload/E_tx)*10^(EbN0/10))，Lrx=2y/sigma^2。
- 全零训练仅在所有控制输入符号不变、消息更新符号等变、filler和速率匹配处理一致时使用。
- 打孔的 L=0 会破坏直接硬 syndrome 特征的逐样本对称性；本规格使用 resolved-mask 和 coverage。
- 标签包含 CRC；通过随机非零有效码字检验对称性和 BLER。
- AdamW，LR warmup1000 后 1e-3 cosine->1e-4，betas(.9,.999)、eps1e-8、weight_decay1e-4。
- bias、norm、lambda 参数不做 weight decay；梯度范数裁剪1；不 dropout；FP32 起步。
- 每 1000 步验证。GPU小时=训练步数*实测秒/步/3600，另加验证、teacher、BLER测试。
- 先预热50步，再测300个含数据生成和反传的完整训练步骤。没有实测前不填写 GPU 小时。

## 9. 资源公式

记 d=d_model，h=expand*d，s=d_state，J=layers，p=12，c=8，o=1。
以下 FLOPs 用一个乘加=2；不把比较/索引/超越函数强行折成 FLOPs。

F_ctrl ≈ T*R*[2pd+J*(6dh+2h(h+2s)+2ch+8hs)+2do]。
F_nms+stats ≈ T*(14E_g+N)，具体细项按实现进一步对账。
特殊函数额外为每基行每步 J*(3h+2s+hs)+o 量级，以及 RMSNorm 的 rsqrt。
Syndrome、CRC、min比较、地址运算和 loss 成本另列。fallback 额外加 T_fb_sample*F_nms_per_iter。

参数数目：
Ptheta=R*4+pd+d+J*(3dh+h^2+3hs+ch+2d+4h+2s)+d+do+o。

推理浮点缓存按 5E_g+3N+R*[Jhs+p+J*(5d+6h+2s)+o] 个/码字规划。
其中5E为 Rold/Rnew/Q/Candidate/absQ，3N为Lch/U/累加缓存。
元数据按每码字4N+M字节，静态展开图8E字节，加4Ptheta字节参数。

训练保存缓存按每码字每轮
A_save=12E_g+6N+R*[p+J*(hs+6d+8h+2s)] 个浮点规划，
另加每码字每轮 (16M+2E_g+M) 字节索引/掩码，以及 AdamW 的额外12Ptheta字节。
这是显式预算模型，不是 PyTorch/Triton 实际峰值保证；allocator/workspace/临时副本另测。

运行 python3 budget_and_invariants.py 复算。默认 T20，Z128：参数1857，状态2688 float/码字，
控制器主项2.92992 MFLOPs，总主项10.12352 MFLOPs/码字；b64训练预算约1.904 GiB。
这不包含实际 allocator/workspace，也不包含反传 FLOPs，不能据此推导时延。

## 10. 消融边界

1. natural_row / degree_bucket 为布局等价性检查；保留原始row ID，不预期改变BLER。
2. row_embedding on/off；row_state vs global pooled state；NMS 的 H 从不移除或故意错位。
3. 单向为默认。双向只能在已观察历史前缀内重跑反向扫描；不允许访问未来迭代特征。
   prefix-bi 每轮重跑长度t前缀，累计O(T^2)，head融合两方向；单独计算开销。
4. d_state in {1,4,8,16}；扩展/layers分别测试，先不联合扫网格。
5. syndrome(含coverage) on/off；SNR on/off；delta-only / delta-B-C / FiLM 三选一。
6. BCE only / +syndrome / +KD；syndrome系数{0,.005,.02,.1}。
7. custom SSM / 官方Mamba-1适配 / 官方Mamba-2适配；版本、step接口、维度限制、后端支持均待核实。
   每轮反馈依赖不变；禁止把预先生成整条特征序列的扫描当作等价在线译码。
   真正Mamba变体的状态/卷积缓存、参数和 FLOPs 重新统计，不套用v0预算。
8. fallback off / warm continuation / cold restart 分开报告；计入完整成本。

## 来源与本地验证

- 标准：https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf
- BG2 表：https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/ldpc/codes/5G_bg2.csv
- Mamba-1：https://arxiv.org/abs/2312.00752
- Mamba-2：https://arxiv.org/abs/2405.21060

budget_and_invariants.py 实际检查了200组小型QC图：gather/scatter伴随关系、编码校验、
打孔条件下的特征/输出符号等变。直接硬syndrome有163个反例；带掩码方案输出误差为0。
输出等变检查采用小型NMS+EMA反馈，不包含完整selective SSM实现。
该结果不能替代NR链路对拍、SSM训练或GPU性能测试。
