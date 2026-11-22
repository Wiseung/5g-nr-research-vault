# S2*：可执行实验协议 v1

日期：2026-11-12。状态：**实验计划；尚无训练结果、完整 NR 链路校验结果或 GPU 实测结果。**

本文件承接父目录的数学定义：flooding NMS + 每个 QC 基行独立状态、权重共享的迭代轴 selective SSM。SSM 只预测阻尼，NMS 的 alpha 在验证集校准后冻结；默认 J=1、d=16、s=4、expand=1、T=20、FP32。它是自定义 normalized-ZOH 对角选择性 SSM，不称作官方 Mamba-1/2 的复现。**本协议的训练码配置与固定 T20/均匀 SNR 训练覆盖父目录的旧 train_Z 和课程训练草案；损失、状态与消息递推不变。**

研究主张限定为：迭代历史是否在相同 NMS 核心、相同迭代数下改善 BLER，或在相同 BLER 下减少实际时间。跨配置泛化是必须检验的边界，不预先当作已实现的能力。Polar 用于链路与 CA-SCL 校验，不存在本方案的 S2-Polar 模型。

## 0. 已可运行的交付物与尚待实现部分

在本目录运行：

```bash
python3 generate_manifest.py
python3 protocol_checks.py
python3 protocol_checks.py --frames 2000000 --errors 200
```

第一条生成 experiment_manifest.json，包含 20 个合法基图选择的 LDPC 标量配置、7 个分场景 Polar 配置、随机种子规则、训练/测量预算。第二条检查 Eb/N0 换算、置信区间、禁止外插的 BLER 交点计算。results_template.json 规定原始统计字段。

这些脚本不实现编码器、译码器、完整标准一致性测试或 GPU 跑分。实际实验 runner 尚待编写；不要把脚本通过写成“NR 链路已通过验证”。后续实验先过第 4 节的校验门，再启动训练。

## 1. 标准参数与实验矩阵

### 1.1 固定命名，解决 K 的歧义

请求中的 512/1024/2048/4096/8448 在本协议定义为 B：包含 TB CRC、尚未补 filler 的单码块输入。A 是纯载荷；K_enc=10Z 或 22Z 是含 filler 的编码器系统输入。F=K_enc-B。二者不能混称 K。

固定单 TB、单 CB、RV=0、完整循环缓冲区、不加 N_ref 截短、QPSK、一个 layer；E_tx 是发送编码比特数。B<=3840 的本表取 CRC16，B>3840 取 CRC24A；所有本表配置无 CB CRC 和分段。A=B-CRC_bits。

BG2 选择条件：A<=292，或 A<=3824 且 R_target<=0.67，或 R_target<=0.25；其余 BG1。BG2 的 K_b 选择 lifting 时按 B 分段为 10/9/8/6，但最终 K_enc 仍是 10Z。按照 TS 38.212 V18.5.0 的第 6.2.2、5.2.2、5.3.2、5.4.2 节冻结参数。

| B（请求的 K） | A | R_target=1/3、1/2、2/3：BG,Z,K_enc,F | R_target=3/4：BG,Z,K_enc,F |
|---:|---:|---|---|
| 512 | 496 | BG2,64,640,128 | BG1,24,528,16 |
| 1024 | 1008 | BG2,104,1040,16 | BG1,48,1056,32 |
| 2048 | 2032 | BG2,208,2080,32 | BG1,96,2112,64 |
| 4096 | 4072 | BG1,192,4224,128 | 同左 |
| 8448 | 8424 | BG1,384,8448,0 | 同左 |

因此“固定 BG1、B=2048、低码率”与“固定 BG2、短块、3/4”不能列为本表的 NR 基图选择结果。可做固定图诊断，但必须另表标记，不与标准模式混合。

QPSK 采用 E_tx=2 ceil(B/(2 R_target))，实际 R_B=B/E_tx，能量换算使用 R_payload=A/E_tx。E_tx 不一定使标称码率精确成立。

| B | E_tx @1/3 | @1/2 | @2/3 | @3/4 |
|---:|---:|---:|---:|---:|
|512|1536|1024|768|684|
|1024|3072|2048|1536|1366|
|2048|6144|4096|3072|2732|
|4096|12288|8192|6144|5462|
|8448|25344|16896|12672|11264|

full Tanner 图：BG1=(46Z,68Z,316Z edges)，BG2=(42Z,52Z,197Z edges)。必须区分全图 N_graph=68Z/52Z 与首 2Z 打孔后循环缓冲区 N_cb=66Z/50Z。例如 BG1 Z=384 的 N_graph=26112，N_cb=25344。本方案计算图复杂度用 N_graph。

这是一组 TS 38.212 **编码内核**实验；没有同时证明 TS 38.214 中 TBS/MCS/资源分配全部匹配。BPSK 只做二进制参考信道，主 NR 链路用 QPSK。

### 1.2 训练与分层测试，避免全笛卡尔积耗尽时间

两份独立模型，不跨 BG 冒充零样本：

* 主模型 A：BG2，B=1024，Z=104，R_target=1/2，AWGN，RV0。
* 模型 B：BG1，B=4096，Z=192，R_target=1/2，同样设置。
* 第 1 层：20 个 LDPC 配置都做零样本筛查，至少覆盖 BLER 约 1e-2 和 1e-3 的区间；同一 BG 用同一来源模型。
* 第 2 层：上述两个主配置做全基线、5/10/20/50 轮和至少两个 1e-4 量级点。
* 第 3 层：上述两个配置，各选择两个预先冻结的 1e-5 附近点；S2、验证集选定的最强传统基线、展开 NMS 做 20M 帧/点。主深测种子预先定为 17，不选测试表现最好的种子；另外两种子先完成 1e-3 至 1e-4 复现，预算允许再补深测。

第 3 层最低为 2 configs × 2 points × 3 decoders × 20M = 240M 次码字译码，不含第 1/2 层。不要承诺 20 配置 × 所有方法 × 所有迭代上限全部到 1e-5。

### 1.3 Polar：CRC 分场景，禁止任意笛卡尔积

| 场景 | A | CRC | K=A+CRC | E_tx | 母码 N | 备注 |
|---|---:|---|---:|---:|---:|---|
|PDCCH|40|24C|64|108|128|固定 RNTI=0x1234|
|PDCCH|80|24C|104|216|256|同上|
|PDCCH|128|24C|152|432|512|同上|
|UCI / PUCCH|53|11|64|128|128|n_PC=0，单段|
|UCI / PUCCH|117|11|128|256|256|同上|
|UCI / PUCCH|245|11|256|512|512|同上|
|UCI / PUCCH，可选|501|11|512|1024|1024|不作为 DL 配置|

N 由 K、E、n_max 和标准选长规则共同确定，不能只手填 N。PDCCH 固定输入交织和 CRC 掩码/解掩码；UCI 固定编码比特交织、可靠性序列及信息/冻结位，保留真实 CRC 检查。前三组 PDCCH 的 E=108/216/432 与聚合级别编码比特数一致；不再做完整盲检测协议。

每配置 CA-SCL L=8/16/32，先无噪声与位级参考，再在瀑布区三个点各 20k 帧做 sanity check。它是独立附属验证，不构成 S2 对 CA-SCL 的性能排名，也不承担本文到 1e-5 的主结论。

## 2. 基线与四条公平对照轨道

### 2.1 主基线与强制补充

| 方法 | 类型/调度 | 作用与限制 |
|---|---|---|
|SPA-F|传统，flooding|稳定的精确/参考 BP；5/10/20/50 轮|
|NMS-L|传统，layered|主要工程强基线；5/10/20/50 轮|
|展开 NMS-F|神经，flooding|主神经基线 1；每基行每轮 alpha 和 eta，各 2RT 参数，T_train=20|
|GNN-F|神经，flooding message passing|主神经基线 2；edge/row 权重共享，图输入与 S2 相同|
|NMS-F|传统，flooding|S2 的直接父算法，必须有；相同底层 NMS 更新代码|
|OMS-L|传统，layered|防止只选择较弱归一化方法；5/10/20/50 轮|
|ECCT/白盒 ECCT|神经，短码专轨|必须完成一个可核实实现；层数不叫 BP 迭代数|
|行级 EMA、MLP、GRU|消融，对应 NMS-F|区分时间记忆、条件化和 SSM 参数化贡献|
|CA-SCL|传统，Polar|只在同一个 Polar 配置比较 L=8/16/32|
|BP-OSD|stretch|不占主论文必做预算|

四个主基线恰好传统/神经各两个；NMS-F/OMS-L 是强制额外对照。经典方法没有待匹配的可训练参数量，不往里面补无意义参数。

GNN 与 ECCT 从公开作者实现开始：先冻结 URL、commit、许可证、原文配置及现有测试，再适配 NR。任何改动都称 adapter，不能未经核对就称“复现原论文数值”。版本、目标 GPU 后端支持、可用优化内核均**待核实**。GNN 共享核心、mask、SNR 条件信息和输出约定；不能以低效通用 scatter 实现充当“最强 GPU GNN”结论。

### 2.2 调参公平

独立 validation split，训练种子 17/29/43。经典候选：NMS alpha=0.60:0.05:1.00；OMS beta={0,0.1,...,1.0}，单位与原始 LLR 一致；每个 schedule、配置和 max_T 独立校准。S2 固定 alpha 使用其source训练配置上的同一 flooding NMS 校准结果，zero-shot目标上不重调alpha、归一化或停止阈值；目标配置specialist可以按目标validation校准。跨配置测试同时给target-tuned强NMS与source-fixed NMS，明确二者信息预算。候选全部在同一组 5 个 SNR 上各 20k 帧校准，然后 top-2 各补到 100k 帧确定。以平均 BLER、平均轮数的字典序选取，冻结后再测。

SPA 使用数值稳定更新，显式记录消息 clipping。所有方法共用 rate recovery、LLR clip=20、已知 filler、停止条件、CRC、多精度口径。神经基线得到与 S2 同样可用的输入信息；如只有 S2 得到 syndrome 特征，必须增加 GNN/MLP 的同信息对照，不能把信息优势归因于 SSM。

### 2.3 四轨分别报告，不能声称同时全部对齐

1. **数据与优化预算轨（主）**：同训练 split、SNR 样本流、有效 batch=64、50k optimizer steps=3.2M 信道观测/次训练，三种子。microbatch 可不同，梯度累积保持观测数与每步 batch 一致。唯一在线样本键由 split/config/train_seed/step/sample_index 决定，不能因 microbatch 改变样本。各方法使用相同验证频率、5 个验证 SNR 点和 checkpoint 选择规则；调参试验总 GPU 时另列。
2. **参数预算轨**：神经模型尽可能接近 S2 的约 1.9k 参数，容差 ±10%；另保留原生较强公开配置。展开 NMS 的 2RT 参数：BG2=1680，BG1=1840，已接近 S2。GNN 缩宽会改变能力，必须同时报告原生配置；离散宽度不能满足容差则列真实差值，不填无用参数。
3. **算术预算轨**：按相同 MAC=2 计数，调轮数/深度到 ±10% FLOPs；若离散轮数不可达，报告相邻两点。比较/exp/tanh、gather/scatter bytes、syndrome/CRC 另列。FLOPs 对齐不等于硬件时间对齐。
4. **实测时延轨（主）**：先用验证集生成各方法候选配置的 BLER–p50/p99 时间 Pareto，再在共同预算选最快满足目标 BLER 者，或预算内最优 BLER 者；锁定策略后只测一次测试集。预算在双方可行的延迟重叠区，公开全部候选点；不得测试集选最有利单点。另报告超时率 P(t>D)，不能把平均时间达标当 p99 达标。

同迭代主对照：S2 vs NMS-F vs 展开 NMS-F，在 T=20，早停/fallback 都关闭。5/10 为同一个 T_train=20 模型的前缀诊断；T=50 属未见迭代外推，时间输入继续采用 t_completed/20，超出训练范围，展开基线复用第 20 层系数，全部明确标注。若要对 T=5/10/50 作独立训练性能主张，必须另做匹配 T_train、相同训练预算的专用模型。

layered 完整访问所有基行一次计一轮，但其更新依赖不同于 flooding，不能将“同为 10 轮”解读为相同算法工作。ECCT 按深度/FLOPs/时延比较，不伪造 BP 轮数。

### 2.4 ECCT 短码专轨，控制单卡代价

共同 NR 配置 BG2 B=512,R=1/2,E=1024。保留 CRC 为外部检查，用 B 维（已去 filler）的 rate-matched LDPC 生成矩阵 G_tx，在 GF(2) 上验证 rank(G_tx)=B，构造 nullspace H_tx 并验证 H_tx G_tx^T=0。发送序列上的有效码与 full-graph rate recovery 对应；H_tx 可能变稠密，此预处理和存储代价必须记录。输入约 1024+(1024-512)=1536 个 bit/check token，实际定义由所选 ECCT 实现确认，**待核实**。

适配不将 CRC 约束并入 H_tx；S2/其他基线也不额外使用该信息。B 个信息位标签中仍包含 CRC，CRC 只在输出端检查。直接 full-graph ECCT 也是合法备选，但不能修改码型来掩盖 OOM。5k steps×64=320k 观测、三种子、S2/GNN/展开 NMS 同配置重训对齐该专轨；短轨统一关闭 syndrome 辅助损失（原定 warmup 不在 5k 步内完成），不能把它与主表 50k 模型当等预算比较。先在 500-step 预跑测资源再锁定可执行配置；OOM/不支持按 N/A 记录原因，不作为 BLER 胜利或通用可扩展性证明。

## 3. 信道、能量与速率恢复

### 3.1 全文唯一 Eb/N0 定义

Eb 是纯载荷 A 比特的能量，不含 CRC/filler，decoder 输入没有 pilot/CP 开销。R=A/E_tx，Q_m=log2(M)，Es=1：

    gamma_s = R Q_m gamma_b
    Es/N0[dB] = Eb/N0[dB] + 10 log10(R Q_m)
    N0 = 1/(R Q_m 10^(Eb/N0[dB]/10))

QPSK：x=[(1-2b0)+j(1-2b1)]/sqrt(2)，w~CN(0,N0)，每实维方差 N0/2。y=h x+w，完美 CSI 时：

    L0 = 2 sqrt(2) Re(h* y)/N0
    L1 = 2 sqrt(2) Im(h* y)/N0

其中 h* 是共轭。AWGN 取 h=1。LLR=log(P0/P1)，硬判决 L<0，BCEWithLogits 使用 -L。

BPSK：x=1-2b，y=x+w，w~N(0,sigma²)，sigma²=N0/2=1/(2R gamma_b)，L=2y/sigma²。必须把 BPSK/QPSK 差别从调制能量归一化中抵消；不能横轴一边按编码比特、一边按载荷比特。单bit全0/全1测试先确认参考库LLR符号；若相反，适配器统一取负，不能直接接入。

对公开曲线，先按原文R_ref与原Eb定义复跑；换算到本协议同一Es/N0时，横轴加10log10(R_ref/R_payload)。若R_ref=B/E，则偏移为10log10(B/A)，例如B1024/A1008约0.0684dB。不能把这段CRC能量差误判为模型增益。

TDL 若启用完整 OFDM，主文另标 waveform Eb/N0=总发送波形能量/(A N0)，明确 pilot、空子载波、CP、发射归一化；以生成波形的实际总能量核算，不沿用无开销公式。主结论以无开销 AWGN/Rayleigh 为准。

### 3.2 Rate matching/recovery 与状态输入

标准顺序：TB CRC→单 CB filler→QC 编码→首 2Z 打孔→循环缓冲选择 RV0、跳 filler→QPSK 编码比特交织→映射。接收端严格逆序：解调/去交织→按 index 累加重复 LLR→恢复首 2Z 和未发送位→filler 强先验。

* 打孔位 L=0，puncture mask=1；不能随机赋值或删掉图节点。
* filler 已知零 L=+20，filler mask=1；每轮再次 pin，不将 filler 纳入载荷 BER/BCE。
* 重复位先累加，再 clipping，记录 repeat_count；不能把每份重复当作不同变量节点。
* 训练和测试共用唯一 index builder，并保存 index SHA256。换率测试时只换标准 index/mask 和合法 Z/BG，不改模型参数。
* 主矩阵未必触发重复；另加低率压力测试（如 R=1/5，按同样 BG 规则重算），只作 recovery 校验，不混入主性能表。RV1/2/3、HARQ 可留后续工作。

### 3.3 衰落必做与可选

必做 coherent i.i.d. symbol Rayleigh：h~CN(0,1)，E|h|²=1，同一码字每个 QPSK 符号独立，完美 CSI + 完美噪声方差给所有方法同一 demapper。S2 默认不开额外 oracle SNR/CSI 输入，信道已通过 LLR 呈现；若加 SNR 条件，所有神经对照也给相同信息。AWGN 训练权重不变测试，再训练 Rayleigh specialist 估计域外损失。

整块准静态 Rayleigh 的 outage 行为不同，另标可选，不与 symbol Rayleigh 混曲线。TDL 是可选第二阶段：固定 TDL-A、100 ns RMS delay、30 Hz Doppler、15 kHz SCS、单天线 OFDM，FFT/CP/pilot 与标准采样定义先由独立链路确认；所有实现版本和后端支持待核实。不得在没有完整 OFDM/CSI/开销定义时只写“TDL 泛化”。

## 4. 先校验再训练：六道可执行门

1. **标量门**：运行本目录脚本，核对全部 BG/Z/K_enc/F/E_tx 与合法 lifting sets；保存 manifest hash。首 2Z 和 filler 位置单独断言。
2. **QC 代数门**：对两个 BG 的每个所用 Z，各 1000 个随机 payload 编码，检查 Hc=0、CRC 和 filler。shift 表 URL/commit/hash 固定，明确矩阵移位符号。父目录 toy test 只覆盖小 QC 代数，不能替代本门。
3. **位级参考门**：独立 MATLAB 或 Sionna 之一作为参考，逐一对照至少 100 个 NR codeword、rate-selection index、交织、恢复 LLR；另一个独立解码实现用于高 SNR sanity。不将两个共享同一错误 index 的实现当独立验证。
4. **无噪声门**：随机 payload、全部主配置无噪声，经 rate matching/恢复后译码；短码 10k 帧、长码至少 1k 帧不得有错误。高码率也要验证；若固定迭代数未收敛，先区分预算不足与链路错误，不直接修改标准映射。
5. **公开曲线门**：先逐项复刻公开 Sionna 5G coding notebook 的原参数（含其码率和能量定义、BP 轮数、list size）；保存 notebook/依赖 commit、原曲线数据或图号。若仅有图，数字化误差范围内对照，不声称逐点复现。至少三个瀑布区点，置信区间或约 ±0.1 dB 工程阈值相容；该阈值是排错门，不是统计定理。随后在本文配置对照独立参考实现。不能拿不同码长/迭代的文献曲线直接校准本文主图。
6. **对称性与梯度门**：对完整 SSM 比较 L(y⊙(-1)^c) 与 L(y)⊙(-1)^c；包含打孔零 LLR、filler、clipping、condition、CRC，通过随机合法码字逐样本检查。resolved-mask syndrome 统计及 coverage 用于避免零值 tie 的控制偏差；精确早停仍用完整 hard syndrome。检查有限损失/梯度、一次训练更新后对称性、随机 payload 验证无性能异常。

任一门失败，都先排链路，不启动大规模训练。参考文献曲线不等于已经校验通过，本协议状态保持 pending，直到产生原始日志。

## 5. 训练预算与损失（固定默认值）

在线生成 payload→CRC→编码→rate match→QPSK/AWGN。纯训练可在严格满足线性码、BMS 信道、符号等变 NMS、符号不变控制器输入、对称 clipping/损失且已过对称性门时使用全零码字。每个神经基线单独验证此条件；不满足的基线训练随机码字，但噪声/SNR/观测预算相同。**全部最终 BLER 测试一律随机 payload，含真实 CRC。**

独立 pilot：Eb/N0=-2:0.5:8 dB，每点 20k 帧，以 NMS-F20 的 BLER=1e-2 交点 gamma_ref 为中心，冻结训练区间 [gamma_ref-1.5,gamma_ref+1.0] dB；每样本均匀采样。交点不被包围则扩 pilot，不能外插。main 表中的 SNR 都是按 A/E_tx 换算。默认不加课程学习；可选课程是前 5k 步先用区间上半部，后续全区间，其他模型也给同样训练样本流。

50k optimizer steps、effective batch64，AdamW，peak LR1e-3，warmup1000，cosine decay 到1e-4，weight_decay1e-4，grad_norm clip1。统计特征 detach、SSM 跨迭代状态不 detach；不跨码字保留状态。最后四轮 soft LLR 的 BCE，监督 B 个信息位（含 TB CRC，不含 filler），权重1/2/4/8归一化；syndrome 软惩罚第5000步前为0，5000–10000线性升到0.02；teacher默认关闭。若开启 NMS50 teacher，蒸馏0.05、temperature2，仅使用 teacher 信息位全部正确的训练样本，没有合格样本时 KD=0；额外 teacher FLOPs/训练时另计，所有神经基线须有同 teacher 对照。

每1000步验证一次，5个冻结 SNR 点（训练区间等间隔取含端点的5点），每点至少20k帧；依平均信息位 BCE（含CRC，不含filler）选checkpoint，最终候选补到每点100k帧。若多次试验调参，公开全部试验及总GPU时；3种子不是调3次后只展示最好一次。50k是预算上限而非已证明足够，必须画学习曲线并注明是否收敛。

软件 lockfile、CUDA/Triton/custom kernel 的支持与实际版本均待目标卡核实。主 FP32 轨记录 TF32/自动混精开关，默认关闭自动降精。4090/5090只选一张用于所有排名，不能跨卡比较；另一张只能单列复现实验。

## 6. 统计：帧数、置信区间、fallback

### 6.1 固定 N 的正式点，不在测试集上挑 SNR

pilot 与正式 test 独立。pilot 冻结 SNR 网格和各点 N：通常0.25 dB步长，目标交点附近0.1 dB。正式测试固定 N 后跑完；未达到预期错误数就报告较宽 CI，不临时删除“不好看”的点。这样可以直接使用固定样本二项区间。若采取按错误数停机，应改用相应序贯区间，不能沿用本协议 Wilson 假设。

| 预期 BLER | 固定 N / 点 | 预期错误帧 | 95% 相对半宽近似 |
|---:|---:|---:|---:|
|1e-2|20k|200|约14%|
|1e-3|200k|200|约14%|
|1e-4|2M|200|约14%|
|1e-5|20M|200|约14%|

1M 帧在1e-4附近约100个错误，95%相对半宽约20%，仍可报告，不能写“足够精确”而不附CI。默认 BLER Wilson 双侧95%；0错误另给单侧精确上界 1-0.05^(1/N)≈3/N，绝不画为BLER=0。

BLER主定义：任一 A 个payload比特错误即frame error。另报 rejected/erasure rate、syndrome-valid且CRC-valid的错误接受率、CRC通过但payload错误率。未通过检查但payload正确仍按payload-BLER记0，同时作为rejection计数；若上层把reject视作失败，另报 service-FER=P(payload error OR rejected)，避免悄悄改变 BLER 分母。

payload BER=总载荷错误bit/(N A)。一帧内bit错误相关，BER CI用frame/shard bootstrap，不能假设 NA 个bit独立。保留32个固定shard的frame count、error count、bit errors和配对方法差异，bootstrap时同时重采样所有方法相同shard；必要时保存frame-level误码计数。配对输入、噪声、衰落对所有方法一致。

种子：训练17/29/43；pilot、validation、test使用不同split字符串生成种子。test seed=SHA256(protocol|split|config|SNR到4位小数|shard)的前64位再取模，不用Python hash。样本流还需独立bit/noise/fade子键，记录实际RNG引擎/版本。各神经种子共用test码字不是3倍独立样本，不合并成3N；分别给CI，汇报中位与范围。

目标Eb/N0只在有统计支持的相邻点之间对log10(BLER)插值，CI由配对shard bootstrap传播；无包围则写N/A，禁止外插。扫描SNR点多重比较不支撑事后挑一个“显著最好点”；主终点预注册为BLER=1e-3的Eb/N0和T20同轮对照，1e-4/1e-5为强验证。

1e-5曲线只能称“在已测区间未观察到明显平层/观察到斜率变化”。若高SNR错误数不足，不作无错误平层结论；更低错误率验证列后续工作。

### 6.2 输出合法性与 fallback 的完整分母

终止/接受：完整 H hard(c)=0、filler一致、TB CRC通过、非filler位无数值零值歧义。不能只看syndrome，也不能把检查通过说成真实码字必然正确。神经20轮结束后失败的码字沿当前消息做额外10轮NMS warm continuation，总上限30；最终仍失败标reject并保留最后软/硬输出用于payload BER/BLER统计。

逐帧保存 need_fallback, fallback_iters, accepted_after_fallback, residual_failure, accepted_wrong, iterations_neural 和 time。定义：

    trigger_rate = N_need_fallback / N_all
    rescue_rate = N_correct_after_fallback_and_prewrong / N_need_fallback
    residual_check_fail = N_rejected_final / N_all
    undetected_error = N_payload_wrong_and_accepted_final / N_all

触发率本身给Wilson CI；按SNR/配置分别报。救回数用仿真真值定义，不把“CRC通过”直接当纠错成功。报告neural-only和S2+fallback整体BLER，所有帧都计分，绝不只统计接受的帧。同轮比较关fallback；整体系统比较加入NMS30基线，且所有方法享有相同总轮数/同后备策略的补充对照。平均轮数=sum(neural+fallback full sweeps)/N，同时给check次数与p99轮数。

固定shape用active mask不保证省算力；如果做compaction，计入gather/重排/host控制/再打包的成本。不要用平均算法轮数推导GPU加速倍数。

## 7. 泛化：必须有逐项数值与参照

全部zero-shot模型参数、归一化、alpha选择规则在source训练后锁定。S2默认共享Z维统计/权重；同BG row embedding固定，graph变Z或rate时仅换标准mapping。**不声称跨BG零样本**。

| 轴 | 来源→目标（一次只变主因素） | 必报数值 |
|---|---|---|
|跨Z/B，BG2|B1024,Z104→B512,Z64及B2048,Z208，R=1/2|每目标BLER曲线、目标1e-3点、对NMS增益|
|跨Z/B，BG1|B4096,Z192→B8448,Z384，R=1/2|同上|
|跨lifting set|BG2 Z104(set6)→Z64(set0)|不能把104→208同set扩展独立当跨family证据|
|跨rate，BG2|B1024,R1/2→1/3,2/3，同BG|3/4切BG，不能放入纯rate泛化|
|跨rate，BG1|B4096,R1/2→1/3,2/3,3/4|同上|
|SNR外推|训练区间外低端gamma_ref-2.5、高端gamma_ref+2.0及冻结网格|外区BLER、CI、与NMS差值；不外插交点|
|信道外推|BG2主配置AWGN→symbol Rayleigh，同rate/CSI口径|Rayleigh目标SNR及域外损失|

为使“掉点”不是把不同码本身难度相减，给六个目标条件训练同预算specialist（三种子）：BG2 B512 R1/2；BG1 B8448 R1/2；BG2 B1024 R2/3；BG1 B4096 R3/4；BG2主配置Rayleigh；BG2主配置宽SNR训练。[宽SNR区间为gamma_ref-2.5到gamma_ref+2.0，其余训练预算相同。]

在同一目标配置c，定义真正训练域损失：

    D(c) = gamma_zero_shot(c, BLER=1e-3) - gamma_specialist(c, BLER=1e-3)

正值表示zero-shot掉点。没有包围目标的曲线则D=N/A，改报固定SNR的BLER比值和CI。其余全矩阵点报告对NMS的增益g(c)=gamma_NMS(c)-gamma_S2(c)，及g(source)-g(target)；后者称“相对NMS增益损失”，不能冒称纯泛化损失。specialist只在选定代表点做，不把它的结果伪装为所有20配置都验证。

SNR外推比较窄区训练与宽区specialist在同一外区测试点的BLER比值；若两条外区曲线不包围1e-3，不强算dB损失。Rayleigh不把AWGN下的SNR门限直接相减当域外损失。

## 8. GPU、时延、显存、功耗的操作步骤

### 8.1 所有测量绑定同一实验身份

保存：GPU型号/UUID、显存、功率限制、时钟/温度、driver、OS、Python/PyTorch/CUDA/Triton/cuDNN、kernel/仓库commit、config/shift/index/weights hash、精度、TF32、batch、T、停止策略、RV、SNR、是否含CRC/fallback/数据搬运。全部实际版本与设备支持待核实；不能由官方文档版本推断目标机版本。记录deterministic flags和原子累加顺序，目标版本是否支持确定性路径待核实；固定环境保留golden LLR/输出向量及hash，跨设备/内核用逐轮数值差异与最终统计CI评估，不许诺仅靠同seed即可跨环境逐bit一致。

算法公平轨：S2和NMS-F使用完全相同图更新核心，S2只增加控制器。默认full-graph不裁图；若公开参考实现剪去未发送的degree-1节点，必须记录实际N/E、启用条件与算法影响，不能将其FLOPs按本协议full-graph公式直接填入。系统公平轨允许合理裁图/布局优化，但逐项验证等价性；非等价的schedule或剪枝作为独立配置比较。给NMS-L/OMS-L/GNN合理的CUDA/稀疏布局优化，公开优化差异；不能拿S2定制Triton和未优化CPU/Python循环比并声称算法优越。相同训练/精度比较与各方法最佳工程配置另表。

### 8.2 三种计时范围，均需记录

1. GPU-event/device-only：输入LLR已在device，计rate recovery、特征/SSM/NMS、syndrome/CRC、早停/compaction/fallback、最终输出；不含噪声生成、H2D/D2H、首次编译、分配。如果CRC实际在CPU，不能谎称该范围覆盖CRC，必须把CPU部分放在下一范围并标记不完整。
2. host-wall/device-resident：输入也已在device，以同步包围完整译码调用，计Python/host调度与可能CPU检查；它是batch1请求延迟的主要系统口径。
3. host-wall/end-to-end：从host输入LLR到host最终输出，含H2D/D2H、必要同步和完整postprocess；pageable/pinned设置一致，单列不混算。

warmup先至少200次，覆盖常见fallback/shape路径，确认无待编译及温度稳定。预先分配buffer。CUDA event的开始/结束和显式同步遵循锁定版本API，**API可用性待核实**。持续吞吐只在整段前后同步，不在每个kernel后同步。

batch1单请求：每轮10k个独立调用，输入池在device，调用前后完成相应同步，保留逐调用event时间与wall时间，5轮；报告p50/p99及跨轮/配对bootstrap区间。10k中约100个样本落于尾1%，不能只报十次均值。测低/瀑布/高三个冻结SNR，fallback与早停开关各一组。固定预算/关早停的profile另测一次，以区别数据相关停机影响。

batch={1,2,4,8,16,32,64,128,256}，每点连续至少1s、5轮，报告batch请求时间与吞吐：

    codewords/s = completed_codewords / elapsed_seconds
    payload Mbps = A * codewords/s / 1e6

若A=1008，同样吞吐与B=1024计法会有差异，必须统一A。另报simulation goodput时应说明正确且按时接受的分母。batch时间/B只是摊销服务成本，不能叫单码字响应p99。OOM处写N/A，不跳过也不外推。CUDA Graphs/编译优化另轨，所有可用基线同样尝试并记录。

显存：warmup后清理无关模型和graph，reset峰值记录器，分别测训练forward+backward+optimizer与推理；报告peak allocated、peak reserved和NVML进程显存（作用域不同）。统计训练GPU时包括数据生成/teacher/验证/失败调参的实际占用，另列单次成功训练时，不用理论FLOPs估GPU时。

### 8.3 NVML J/codeword

先在目标卡查询power/total-energy接口是否支持；读取失败不能用0填充。NVIDIA文档对部分新架构的功率值给出约1秒平均窗口，传感器实际语义与更新频率**待核实**；100ms轮询不等于100ms独立测量。

无并发GPU任务，同温度/时钟/功率设置：idle30s→指定batch和SNR稳态译码30s→idle复核，5轮。workload远长于传感器窗口；统计工作区间完整完成的码字数。若total-energy计数可用，读首尾差；否则对实际时间戳power序列作梯形积分，单位W×s=J。报告二者哪种实际使用，平均窗口重叠值不当成独立样本。

    E_gross = integral P_board(t) dt / N_decoded
    E_incremental = [integral P_board(t)dt - P_idle_mean*T] / N_decoded

gross为主、incremental补充；后者若受噪声变负，标注不可分辨，不裁成有利的零。NVML测量范围是板级/设备API定义范围，不是整机插座能耗；不能拿它与FPGA芯片功耗直接比。所有J/codeword绑定batch、SNR、fallback概率及精度。微秒级单次调用不能直接从NVML读出单次能量。

## 9. 量纲、FLOPs 与显存账本

令R为基行数，N=N_graph，E_g为Tanner边数，T为完整迭代数，J为层数，d为model维度，s为state维度，h=expand*d，p=12，c=8，o=1，MAC=2：

    F_controller ≈ TR {2pd + J[6dh+2h(h+2s)+2ch+8hs] + 2do}
    F_NMS+stats ≈ T (14 E_g + N)

默认每基行每轮3488 FLOPs。这个多项式账本不含全部比较/XOR/exp/索引/CRC指令，不是完整硬件指令量；各方法的FLOPs工具都用相同规则，并另列special ops/bytes。fallback按实际触发轮数加算，不默认为永不触发。

|配置|N_graph / E_g|默认T20近似MFLOPs/码字|参数量|batch64训练显式账本|
|---|---|---:|---:|---|
|BG2 Z104|5408 / 20488|8.77472|1857|约1.559 GiB|
|BG1 Z192|13056 / 60672|20.45824|1873|约4.325 GiB|
|BG1 Z384|26112 / 121344|37.70752|1873|约8.580 GiB|

显存账本详见generator的resources函数，显式包含batch、T、J、d、s、expand；它用FP32张量与保存反传变量的计数，非自动微分框架的保证峰值。推理状态为4 B_batch R J h s bytes，训练还需迭代消息历史及保存张量O(B_batch T E_g)。实际workspace、临时张量、fragmentation、optimizer、编译cache必须用峰值API测量。batch256是否能训练不由状态小就能推出。

量纲检查使用同设备同精度校准的P_eff与BW_eff，而不是凭显卡宣传峰值：

    Q_arithmetic <= P_eff / F
    Q_bandwidth <= BW_eff / D_actual
    t >= max(F/P_eff, D_actual/BW_eff)

这是对所选算术与访问模型的roofline估计；不完整F只能给宽松算术上限，若D用的是张量访问账本而不是实测DRAM访问，它也不是普适严格界。可用未融合实现的D_ledger=4T(4E_g+2N) bytes作初查；缓存/融合可降低DRAM traffic，控制器/CRC等可增加，必须据实际kernel解释。

**纯演算例子，不是4090/5090参数或测速**：假设P_eff=50TFLOP/s、BW_eff=1TB/s，BG2 Z104有F=8.77472MFLOP、D_ledger=7,421,440bytes，于是算术约5.70M cw/s、张量流量约134.7k cw/s、约7.42us/码字（仅该模型的理想带宽项），对应payload约135.8Mbps。它不含launch/同步/exp/CRC/fallback，实际可低很多。若实测超过134.7k，不直接宣布违规，而要解释融合/缓存使D_actual下降；若超过算术上限，先查F计数、精度、漏同步、吞吐分母与GPU配置。所有实测加速倍数均用成对原始时间之比和CI，不预测倍数。

## 10. 消融优先级：对迭代轴有意义的实验

|优先级|消融|必做/可选|公平解释|
|---|---|---|---|
|1|NMS-F→静态eta/EMA/MLP/GRU/SSM|必做|同图更新、同alpha、相同输入；GRU接近参数数目，排除“记忆随便加都行”|
|2|syndrome condition开/关；syndrome loss开/关|必做，2×2|分离信息输入与辅助监督；保留coverage/tie安全处理|
|3|neural-only vs fallback；同总预算NMS30|必做|识别收益是否完全来自额外10轮|
|4|真实QC行记忆分组 vs固定随机边分组 vs全局pool|必做|H不改，只换controller分组；保持组数/参数尽量一致，degree统计另报|
|5|原始存储顺序/QC row-major/随机置换|必做低成本不变量与系统测量|同步重排H索引、row id与embedding后代数输出应一致；预期差异在访存，不能把该置换虚称学到了新约束|
|6|s={2,4,8}, J={1,2}|必做小网格|先单种子筛，再对默认和最佳替代做三种子；参数/FLOPs同报|
|7|FP32 vs BF16混精|可选|FP32累加关键LLR/统计；重新校验误码与稳定性；支持待核实|
|8|bit-axis vsiteration-axis|可选|同数据/参数预算和独立FLOPs/时间轨；不能固定同T解释为同工作量|
|9|单向 vs双向|在线主模型固定单向；离线可选|迭代轴不能看未来迭代。双向须先生成整段轨迹再第二遍译码，全部成本计入；不当作普通开关|
|10|官方Mamba-1 vsMamba-2/SSD|可选|当前自定义SSM不是两者。需独立实现适配、匹配参数/训练预算；官方内核版本/显卡支持待核实，不能将函数替换当算法等价|
|11|INT8|可选，最后做|QAT/校准额外成本另列；不由BF16结论推INT8可用，后端待核实|

前三项与结构分组构成最有价值的论文消融。不能为了列全开关，加入因果泄漏的双向迭代结果。

## 11. 十周、400 GPU小时上限与止损

以下是**资源分配上限，不是运行时间预测**。前两周实测每步seconds和每点cw/s后重算：

    H_train = sum(runs * optimizer_steps * seconds_per_step)/3600
    H_test = sum(N_frames / measured_codewords_per_second)/3600

所有失败试验、teacher、验证、编译/调参占用另计入实际日志。人工工时按每周约20h规划；CPU CA-SCL运行另外记core-hours，不能计为0 GPUh就称零成本。

|周|交付与门限|GPU小时上限|
|---:|---|---:|
|1|manifest、shift/index/CRC、位级和无噪声校验|6|
|2|公开曲线、SPA/NMS/OMS对齐，测一步训练与译码速度|24|
|3|两主配置S2、展开NMS/GNN首轮，完整训练日志|45|
|4|三种子复现、EMA/MLP/GRU时间记忆对照；第一次止损|45|
|5|必做消融、短码ECCT专轨，冻结方法版本|45|
|6|全20配置零样本筛查、6个specialist、Rayleigh；第二次止损|65|
|7|同卡p50/p99、batch曲线、显存、NVML；效率止损|20|
|8|正式2M/20M帧深测，固定采样与CI，不再调方法|120|
|9|五张图表和4–6页草稿，按证据决定PlanB表述|10|
|10|清环境复跑关键点、记录hash、归档和修改|20|
|合计| |400|

例如240M次深测若真实持续吞吐仅1000cw/s约66.7GPUh；若10000cw/s约6.67GPUh。第8周120h还要覆盖第1/2层与多方法。必须按每种方法/配置实际吞吐重算，不能用最快S2吞吐代替SPA/GNN耗时。资源不足先砍optional项和加密网格，保留两个主配置、四主基线、零样本四个轴与最低深测。仍超预算则明确缩小深测配置数和统计主张，不编造1e-5结果或省略CI。

预注册工程决策门（数字是项目管理阈值，不是预期结果）：

* 第4周：在T20、关fallback下，至少一个主配置的S2相对校准NMS-F在1e-3处改善约0.1dB并方向稳定，或达到同BLER时实测时间减少约10%；同时检查GRU/EMA是否已解释全部收益。若三种子均无可信改善、或GRU/EMA等效且更便宜，停止堆SSM深度，转PlanB，不宣称SSM优势。
* 第6周：代表目标specialist gap>0.3dB，或对NMS的正增益在多数目标消失，删“强零样本泛化”主张。允许改为多Z/多rate训练，但必须重新标记训练覆盖范围，不能仍称single-config zero-shot。
* 第7周：包括CRC/fallback后，在共同BLER和两个代表SNR区间，p50/p99均无可信改善，删除“GPU更快”主张，保留时间代价证据；不要只报更大的batch来掩盖batch1退化。若memory控制也无独立收益，进入PlanB全文结构。

PlanB仍围绕已定方向：**“QC行级历史状态与条件化对NR神经NMS译码的影响：公平预算下的实证研究”**。研究问题是结构分组、时间记忆、syndrome输入分别何时有效，以及跨Z/rate时失效边界。保留NMS/展开NMS/GNN、EMA/GRU/SSM、配对CI与完整GPU成本；结果必须有可重复的机制或边界结论，不能仅把一堆负结果换标题。若所有差异都在噪声内，继续排错/缩小问题，不能承诺一定成稿或录用。

PINN、ISAC、FPGA/ASIC无乘法器、跨BG基础模型、任意码长、1e5码长、Polar神经增强、BP-OSD超越均不进主实验；最多future work一句。TDL、INT8、Mamba-2与离线双向是optional，不能挤掉统计有效性。

## 12. 4–6页只用五张图表

1. **表1：预算与记忆对照**。四主基线、S2、必要EMA/GRU行，列参数/训练观测/轮数/FLOPs/训练GPUh及主配置1e-3门限。回答“只是增加参数/训练时间”“任意RNN都一样”。详细码参数用正文短句和仓库manifest承载。
2. **图1：BLER主曲线，两个配置panel**。同轮T20主对照、最强NMS/OMS50、神经基线，CI带/稀疏误差棒，1e-4/1e-5 inset；BER完整数据进仓库。回答“打不赢强传统基线”“深误码率无证据”。
3. **图2：同BLER/同时延Pareto，附fallback小panel**。时间口径为device-resident完整调用，标T和p99；同轮点和含fallback点不同符号，附trigger/residual rate。回答“额外迭代换性能”“只选有利比较口径”“丢弃失败帧”。
4. **图3：泛化与结构消融heatmap**。按跨Z、rate、SNR、Rayleigh列，zero-shot相对specialist掉点/CI，有限代表行含真实分组/随机分组、condition/loss开关；N/A显式标出。回答“只记住单一码”“syndrome信息而非SSM贡献”。完整消融表进仓库，不能靠heatmap隐藏统计分母。
5. **图4：GPU系统曲线，三个panel**。batch1–256 latency–throughput、batch1p50/p99（低/中/高SNR）、J/codeword与峰值显存（表内或标注，避免双轴歧义）。回答“FLOPs更少就说更快”“尾时延/功耗没有测”“大batch掩盖单帧延迟”。

不另外加架构图：模块用正文紧凑文字与一条递推式说明。所有图共享配置id、CI定义和时间口径；原始JSONL、manifest、lockfile、代码commit与绘图脚本归档。图中每个数必须能回溯到raw shard和run id。

## 13. 外部来源与待核实项

* [3GPP TS38.212 V18.5.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf)：基图/CRC/lifting/速率匹配/Polar，冻结此版本而非宣称最新版本。
* [Sionna公开5G coding notebook](https://nvlabs.github.io/sionna/v2.1.0/phy/tutorials/notebooks/5G_Channel_Coding_Polar_vs_LDPC_Codes.html)：公开参考曲线入口；实际依赖/commit与曲线复制待跑。
* [GNN decoding](https://arxiv.org/abs/2207.14742)、[ECCT](https://arxiv.org/abs/2203.14966)：原论文入口，作者仓库与参数适配待冻结核实。
* [NVML device queries](https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html)：power/total-energy传感器语义，实际目标卡支持待核实。
* [PyTorch CUDA semantics](https://docs.pytorch.org/docs/stable/notes/cuda.html)：异步执行、event/synchronization说明，安装版本待核实。

截至本协议生成，没有实际GPU吞吐、p99、J/codeword、训练GPUh或BLER增益。所有“约0.1dB/10%/0.3dB”仅为预先定义的项目止损门，所有资源小时为预算。
