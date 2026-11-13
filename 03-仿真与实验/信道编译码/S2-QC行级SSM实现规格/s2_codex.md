# Transformer 虽然能实现非迭代并行译码，但其自注意力机制存在致命的 $O(n^2)$ 复杂度瓶颈，导致它无法…

> **Transformer** 虽然能实现非迭代并行译码，但其自注意力机制存在致命的 **$O(n^2)$ 复杂度瓶颈**，导致它无法处理 5G/6G 中的超长码（如码长 $n > 8448$ 的 LDPC 码）。而 **Mamba / SSM（状态空间模型，State Space Models）** 的出现，完美解决了这一痛点。
>
> 将 **Mamba/SSM 与混合序列架构** 引入信道编码与译码（Channel Coding/Decoding），旨在利用其 **“训练时并行、推理时递归、线性复杂度”** 的特性，打造超低时延、超长码支持的下一代神经译码器。
>
> 以下为你详细拆解“跨Mamba/SSM的混合序列架构码架构”的核心原理、设计方案、优势及进阶创新思路。
>
> ---
>
> ### 一、 核心概念：为什么 Mamba/SSM 是天生的“译码器”？
>
> Mamba 的核心是基于连续时间状态空间方程（如 $x'(t) = Ax(t) + Bu(t)$），并通过**选择性机制（Selective State Space）** 实现。它在通信译码中具有三大不可替代的优势：
>
> 1. **线性复杂度 $O(n)$，突破长码瓶颈**：
>    传统 Transformer 处理长序列时，注意力矩阵会撑爆显存。Mamba 无论序列多长，计算量和显存占用均呈线性增长。这使得它成为处理 6G 超长码（如 $n=10^5$ 的 LDPC 或 Polar 码）的唯一可行深度学习架构。
> 2. **极致的推理低延迟（$O(1)$ 递归推理）**：
>    在推理阶段，Mamba 表现为类似 RNN 的递归模型。它不需要像传统 BP/SCL 译码器那样进行几十次串行迭代，只需**一次前向状态扫描**即可输出译码结果，极度契合 6G URLLC（超高可靠低时延通信）的严苛要求。
> 3. **天然的因果性与极化树契合度**：
>    Polar 码的串行消除（SC）译码具有严格的因果依赖（后译码比特依赖先译码比特）。Mamba 的隐状态传递机制与这种因果递归结构天然同构。
>
> ---
>
> ### 二、 什么是“混合序列架构”（Hybrid Sequence Architecture）？
>
> 纯 Mamba 架构在处理信道译码时存在局限：它对**极短程的局部校验约束（Local Parity Checks）** 敏感度不如 CNN，对**全局精确错误定位**不如 Self-Attention。
> 因此，“混合序列架构”通常指将 **Mamba 与 Attention、CNN 或 MLP 进行异构融合**。
>
> #### 典型的混合架构设计模式：
> 1. **Mamba + CNN（局部-全局混合）**：
>    * **CNN 层**：负责提取相邻比特间的局部校验关系（类似于 Min-Sum 算法中的局部消息更新）。
>    * **Mamba 层**：负责在全局序列上扫描，捕获长程错误传播和码字整体的拓扑结构。
> 2. **Mamba + Self-Attention（Jamba 风格）**：
>    * 在深层网络中交替插入 Mamba 块和轻量级 Self-Attention 块。Mamba 负责低成本地压缩长序列上下文，Attention 负责在关键位置进行高精度的错误模式检索。
> 3. **双向 Mamba（Bi-Mamba）**：
>    * 标准 Mamba 是单向因果的，但信道译码通常需要利用整个接收序列的信息。混合架构通常采用**前向 Mamba + 后向 Mamba**的双向扫描，并在末端进行状态融合。
>
> ---
>
> ### 三、 跨 Mamba/SSM 混合码架构的 3 种创新设计方案
>
> 如果你要开展此课题，可以参考以下三种具体的网络架构设计：
>
> #### 架构 A：面向长码的“Mamba-CNN 混合非迭代译码器”
> * **输入**：接收到的对数似然比（LLR）序列。
> * **结构**：
>   * **第一阶段（局部感知）**：使用一维因果卷积（1D Causal CNN）或局部窗口 Attention，提取校验矩阵 $H$ 中局部的稀疏约束。
>   * **第二阶段（全局状态演化）**：将局部特征输入多层 **Bi-Mamba** 模块。Mamba 的选择性扫描机制会自动学习哪些位置的噪声需要被抑制，哪些位置的校验信息需要被保留。
>   * **输出**：直接输出硬判决比特或软输出 LLR。
> * **优势**：彻底摆脱迭代，单次前向传播，推理延迟极低，且支持任意码长。
>
> #### 架构 B：基于 Mamba 的深度展开 BP（Mamba-Unrolled BP）
> * **思路**：不完全抛弃传统迭代译码，而是将 BP 算法的迭代过程“展开”为神经网络层。
> * **结构**：在每一层迭代中，不再使用固定的 $\min$ 或 $\tanh$ 更新规则，而是用一个 **Mamba 模块**来学习变量节点和校验节点之间的消息传递。
> * **优势**：Mamba 的线性复杂度使得展开层数可以做得很深，从而在极低误码率区域（Error Floor）获得超越传统 BP-OSD 的性能。
>
> #### 架构 C：Polar 码的因果 Mamba-SCL 增强架构
> * **思路**：针对 Polar 码，利用 Mamba 的因果递归特性替代或增强 SCL（串行消除列表）译码。
> * **结构**：将 Mamba 的隐状态 $h_t$ 作为路径度量的动态特征。Mamba 可以在不显式存储所有 $L$ 条路径的情况下，通过隐状态隐式地学习路径的置信度，从而大幅降低 SCL 译码的内存开销。
>
> ---
>
> ### 四、 核心痛点与挑战（避坑指南）
>
> 尽管 Mamba 极具潜力，但在通信硬件落地和数学理论上仍面临挑战：
> 1. **离散化与硬件量化困难**：
>    Mamba 的核心是连续状态方程的离散化（如 ZOH）。在 FPGA/ASIC 上实现高精度的状态空间递归极其困难。如何进行**低比特量化（如 4-bit 或更低）** 下的 Mamba 训练，是目前的工程痛点。
> 2. **因果性与双向性的矛盾**：
>    双向 Mamba（Bi-Mamba）虽然提升了性能，但在推理时破坏了 $O(1)$ 的显存优势，且增加了硬件流水线设计的复杂度。
> 3. **混合架构的梯度病态**：
>    Mamba 和 Attention 的梯度尺度差异巨大，联合训练时极易导致某一部分网络梯度消失或爆炸。
>
> ---
>
> ### 五、 进阶创新思路（如何发顶刊/顶会？）
>
> 为了让你的选题更具“不可替代性”，建议在混合 Mamba 架构上叠加以下前沿创新点：
>
> #### 思路一：物理启发的 Mamba（Physics-Informed Mamba）
> * **创新点**：结合你上一个关于 PINNs 的思路。将信道衰落的物理微分方程（如瑞利衰落的随机微分方程 SDE）嵌入到 Mamba 的状态转移矩阵 $A$ 和 $B$ 的学习中。让 Mamba 的隐状态演化**严格遵循物理信道的动态变化**，从而在少导频场景下实现鲁棒的信道估计与译码。
>
> #### 思路二：面向 6G 通感一体化（ISAC）的联合感知与译码 Mamba
> * **创新点**：6G 中通信和雷达感知共享同一套硬件。利用 Mamba 处理长序列的优势，设计一个**双分支混合 Mamba 架构**，同时处理雷达回波序列（感知）和通信数据序列（译码）。通过共享的状态空间模型，实现通感联合处理与干扰消除。
>
> #### 思路三：Mamba 驱动的自适应译码调度（Dynamic Decoding Scheduling）
> * **创新点**：利用 Mamba 的隐状态实时评估译码的收敛程度。如果隐状态表明已经收敛，则触发**提前终止（Early Stopping）**；如果陷入死锁（如 LDPC 的陷阱集），则触发全局扰动或切换译码策略。这种“智能调度”能大幅降低平均功耗。
>
> #### 思路四：硬件感知的轻量化混合 Mamba（Tiny Mamba）
> * **创新点**：针对通信芯片的功耗限制，设计一种**无乘法器（Multiplier-Free）** 或**极低比特量化**的混合 Mamba-CNN 译码器。如果你能证明你的架构在 FPGA 上的能耗和延迟远低于传统的 Min-Sum 硬件实现，这将是工业界极度渴望的成果。
>
> ### 总结
> “跨 Mamba/SSM 的混合序列架构”是目前 **“AI for Communications”** 领域最炙手可热的方向。它完美继承了 Transformer 的全局建模能力，又解决了其计算复杂度爆炸的问题，同时比传统迭代译码器具有更低的推理延迟。
> **建议切入点**：从 **“线性复杂度的长码非迭代译码”** 或 **“Polar 码的因果 Mamba 增强”** 入手，这将是一个极具学术影响力和工业应用前景的顶级课题。
>
> # 角色
> 你是"信道编码理论 × 序列模型 × GPU体系结构"三栖研究者，兼IEEE通信类会议TPC委员。精通3GPP TS 38.212（LDPC BG1/BG2准循环结构与速率匹配、Polar CA-SCL与CRC）、神经译码文献（展开BP/NMS、GNN译码、ECCT及白盒化与基础模型后续）、Mamba-1 selective scan 与 Mamba-2 SSD 的计算差异。你以"可实测、可复现、能按时毕业"为判断标准，拒绝营销式表述。
>
> # 我的情况
> 北邮信通院学硕；目标一篇EI会议小论文（ICCC/ICSP/ICCT，IEEE双栏4–6页）；算力{单卡4090 24GB / 5090 32GB}；技能{PyTorch；CUDA/Triton；Sionna/MATLAB；编码理论；RL}；第一优先级=按时毕业稳中稿。
>
> # 锁定大方向（只在其内部选切口，不推翻）
> 面向5G NR的"结构感知 Mamba/SSM 混合译码器"：算法/结构级创新为主线，GPU上的复杂度—性能—时延实测为支撑证据。
>
> # 必须先接受的前提纠正（不得沿用错误说法）
> 1) 8448是LDPC BG1的K_max（22×384），母码n_max=25344；BG2 K_max=3840；Polar母码≤512(DL)/1024(UL)。n=1e5不属于5G，只能作可选探索性附加实验；
> 2) 经典BP是O(E·iters)、Polar SC是O(n log n)，长码不是经典译码器的瓶颈。禁止用"经典方法做不了长码"作为动机；
> 3) 【新颖性红线】线性复杂度本身不是创新——GNN译码与展开BP早已O(E)线性且带图结构先验。必须给出相对GNN/ECCT/NMS的明确差异化，候选差异化只保留三选一：跨迭代长程记忆 / 规则稠密计算带来的GPU访存优势 / 跨码长码率泛化；
> 4) Mamba的O(1)是每步状态显存，不是整码译码时延；译码是非自回归任务，推理可用并行/分块扫描。禁止照搬"训练并行推理递归"的LLM话术；
> 5) 5G LDPC是准循环码，Tanner图邻居在比特索引上不相邻（跨度为Z的倍数），原始顺序上的1D局部卷积抓不到校验约束；必须显式设计结构注入方式；
> 6) 禁止用隐状态替代SCL的显式列表/路径度量/部分和；5G Polar码长很短，"SCL显存瓶颈"动机不成立；
> 7) 主目标设为"同迭代数打赢NMS/OMS"或"同BLER下迭代数/时延下降"，BP-OSD只作stretch goal；
> 8) "支持任意码长"不成立，跨Z/跨码率泛化必须专门设计并实验验证；
> 9) 砍掉PINN物理嵌入、ISAC、FPGA无乘法器超越Min-Sum等内容，只在future work提一句。
>
> # 候选切口（逐一查新+评估，可提出更优的，但禁止照搬未查新想法）
> S1 结构感知序列化：利用QC-LDPC的Z-block/base-row重排，使1D扫描覆盖校验约束；Δ=结构注入方式 + 规则计算替代GNN不规则访存；
> S2 迭代轴SSM（推荐重点评估）：序列轴=BP迭代次数(10–30)，每步NMS更新+SSM在迭代维度做状态记忆，学习阻尼/调度；Δ=用更少迭代逼近多迭代性能，序列短、易训、指标清晰；
> S3 Syndrome条件化Bi-Mamba：把Hĉ违反度/SNR作为条件注入选择性参数(Δ/B/C)或FiLM，并加syndrome辅助损失与早停；
> S4 Polar CA-SCL增强：Mamba做路径度量预测/自适应L/翻转排序，保留列表与CRC；Δ=同BLER下平均L或时延下降；
> S5 跨码长码率泛化：QC权重共享+结构编码，一次训练覆盖多个Z/K/码率；Δ=泛化能力本身；
> S6 同FLOPs下"稠密规则计算 vs 图scatter/gather"的GPU实测对比（作第二贡献，不作主线）。
>
> # 必须明确回答的6个建模问题（每个切口都要答）
> a) 自回归还是非自回归？输出硬判决还是软LLR？
> b) 码结构如何注入（重排/位置编码/图模块/条件化）？
> c) 是否使用syndrome，用作输入特征、损失项还是早停判据？
> d) 速率匹配（打孔/缩短/重复）与CRC如何处理？
> e) 如何保证输出是合法码字？是否设计"神经+经典fallback"兜底？
> f) 训练在哪个码长/码率/SNR，测试泛化到哪些配置？
>
> # 执行流程（严格分步）
> 1. 信息不足先问≤5个澄清问题，否则声明假设后继续；
> 2. 联网查新2023–2026（Mamba decoding / state space model channel coding / SSM LDPC / Mamba polar / GNN decoder / linear-complexity neural decoder / ECCT scalability / unrolled BP memory），输出对比表：文献(可点击链接)|方法|码型码长|基线|报告增益|与S1–S6差异；明确指出哪些已被做过。查不到标"待核实"，严禁编造；
> 3. 范围裁剪：为4–6页+单卡，必须砍掉什么，砍掉的写进future work；
> 4. 打分表：切口|一句话Δ|新颖度|算法难度|工程难度|预计周数|单卡可行性|撞车风险|会议匹配度；
> 5. Top3展开：中英文题目、核心Δ与最接近工作差异、6个建模问题的答案、技术路线3–5步、预期卖点图表、风险与Plan B、我的技能缺口；
> 6. 自我批判：扮演苛刻TPC委员，至少覆盖"线性复杂度不算创新""只是把Mamba搬来译码""没和GNN公平比""时延优势未实测"四条，据此修正排序；
> 7. 给出唯一推荐+一个备胎+理由+立即可启动的3件具体事。
>
> # 红线
> 单卡可训、纯仿真可完成、5G参数合规、文献可核实、数字有推导或标"待实测"、不许出现"完美解决/唯一可行/顶级课题"这类表述。

<details><summary>21 previous messages</summary>

> 我会先核实最接近的文献、5G NR 参数边界和 Mamba 的计算假设，再按单卡、4–6 页和毕业优先的约束筛选切口。缺失配置先作明确假设；文献结果与待实测目标会分开标注。
>
> <details><summary>Explored a search, ran a command</summary>
>
> <details><summary>Explored 2 files, a search</summary>
>
> - Read `~/.codex/skills/communication-skills/coding/ldpc/SKILL.md`
> - Read `~/.codex/skills/ccf-literature-searcher/SKILL.md`
> - Searched for `LDPC|Mamba|SSM|译码|通信` in `MEMORY.md`
>
> </details>
>
> - Ran `rg --files -g AGENTS.md -g '!node_modules' -g '!\.git' . /Users/macbook/Documents 2>/dev/null`
>
> </details>
>
> 这次采用 `ldpc` 技能核对码结构和速率匹配接口，并用 `ccf-literature-searcher` 做查新。先按一个可执行场景评估：BPSK/AWGN、NR LDPC 单码块、单卡训练，主结果看 CB-BLER；周数暂按每周约 20 小时科研投入估算。
>
> <details><summary>Ran 3 commands, searched the web</summary>
>
> - Ran `cat /Users/macbook/.codex/skills/ccf-common/references/task-modes.md /Users/macbook/.codex/skills/ccf-common/references/privacy-and-evidence.md /Users/macbook/.codex/skills/ccf-literature-searcher/references/search-and-scoring.md`
>
> - Ran `cat AGENTS.md /Users/macbook/.codex/skills/communication-skills/coding/ldpc/references.md`
>
> - Ran `cat /Users/macbook/.codex/skills/ccf-common/references/handoff-modes.md /Users/macbook/.codex/skills/ccf-literature-searcher/references/report-template.md`
>
> Searched the web for `Mamba channel decoding LDPC state space model 2024 2025 2026 -site:mdpi.com`
>
> </details>
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `"Mamba" "LDPC" -site:mdpi.com`
>
> Searched the web for `"SSM" "LDPC" decoding -site:mdpi.com`
>
> Searched the web for `"Hybrid Mamba-Transformer Decoder for Error-Correcting Codes"`
>
> </details>
>
> 查到两篇会直接影响排序的工作：ECCM 已做 Mamba–Transformer 混合、校验结构注入和逐层监督；2026 年的 MMPD 已做图消息传递与双向 Mamba 融合。因此，S1/S3 若只靠重排、syndrome 或 Bi-Mamba，差异化不足。我正在重点核查 S2 与已有记忆式 BP、循环神经 NMS 的距离。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `"LDPC" "memory" "learned damping"`
>
> Searched the web for `https://arxiv.org/html/2605.10681v1`
>
> Searched the web for `"LDPC" "LSTM" "iterations" decoding 2023 2024 2025 -site:mdpi.com`
>
> Searched the web for `"CrossMPT" "2024"`
>
> Searched the web for `"Deep Learning-Assisted Adaptive Dynamic-SCLF"`
>
> Searched the web for `"Mamba" "error correcting" "2026" -site:mdpi.com`
>
> Searched the web for `https://arxiv.org/abs/2411.19092`
>
> Searched the web for `"Graph Neural Networks for Channel Decoding" "2023" "2022"`
>
> Searched the web for `"LDPC" "neural" "2023" "memory" -site:mdpi.com -patent -site:researchgate.net`
>
> </details>
>
> S2 还有一个关键限制：若 SSM 根据第 \(t\) 次译码状态调整下一次更新，输入也随之改变，整个闭环就不能沿迭代轴一次并行扫描。因此，它的可信卖点应是“记忆能否换来更少的有效迭代”。此外，早期 GNN 已验证跨提升因子和码率迁移，S5 也需要更严格的未见配置测试。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `IEEE CIC ICCC 2026 call for papers channel coding 6 pages`
>
> Searched the web for `https://arxiv.org/abs/2405.21060`
>
> Searched the web for `"LDPC" "SSM" "neural" "iteration" -site:mdpi.com`
>
> Searched the web for `"ACE-Grouped Neural Min-Sum Decoding"`
>
> Searched the web for `"ACE-Grouped" "pdf"`
>
> </details>
>
> 又查到更贴近 S2 的工作：ICC 2026 的 ACE-NMS-GRU 已用“每轮可靠度摘要 → GRU 记忆 → 下一轮 NMS 权重”，并按未满足校验比例触发。因此，“SSM 记住迭代历史”也不能直接作为新颖性结论。我会将 S2 收紧为 QC 基行分别维护状态，并要求与相同特征、相同状态粒度的 GRU/MLP 对照，检验增益是否来自记忆机制。
>
> <details><summary>Ran a command, searched the web</summary>
>
> Searched the web for `"Boosted Neural Decoders" "arxiv"`
>
> Searched the web for `https://arxiv.org/html/2605.10681v1`
>
> - Ran `python3 - <<'PY'
> import urllib.request,re
> from html import unescape
> items=[('MMPD','https://arxiv.org/html/2605.10681v1',['To further assess','Fig. 3:','0.45']),('NWD','https://arxiv.org/abs/2411.19092',['Journal reference','Submitted on']),('ECCM','https://arxiv.org/abs/2505.17834',['Submitted on','Journal reference'])]
> for name,url,needles in items:
>     try:
>         src=urllib.request.urlopen(url,timeout=25).read().decode()
>         src=re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>',' ',src)
>         txt=unescape(re.sub(r'<[^>]+>',' ',src))
>         txt=re.sub(r'\s+',' ',txt)
>         for needle in needles:
>             p=txt.find(needle)
>             print(name,needle,txt[max(p-100,0):p+2300] if p>=0 else 'not found')
>     except Exception as e: print(name,type(e).__name__,str(e))
> PY`
>
> </details>
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> 已核实 MMPD 包含 5G LDPC 的显存扩展实验，但其译码性能结论主要来自其他基准码，不能直接等同于“已在 NR 长码上证明 BLER 优势”。接下来我会把“已有直接先例”和“仍可检验的差异”分开，收敛到适合单卡、4–6 页论文的方案。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `"ACE" "GRU" "min-sum" 2026`
>
> Searched the web for `"white" "Error Correction" "Transformer" WECCT`
>
> Searched the web for `"Deep Learning-Assisted Adaptive Dynamic" "SCLF"`
>
> Searched the web for `"ACE-Grouped Neural Min-Sum" pdf`
>
> </details>
>
> 还发现了 2026 年 10 月发表的 CrossMPM：它已用 Tanner 图投影生成选择性扫描参数，进一步压缩了 S1、S3 的新颖空间。现在更值得验证的是：QC 基行各自保留的迭代记忆，能否在相同粒度的 GRU、EMA 和无记忆控制器之外带来收益；若只换成 SSM 而没有额外收益，就不应以“Mamba 译码”作为贡献。
>
> <details><summary>Ran a command, searched the web</summary>
>
> Searched the web for `https://arxiv.org/html/2405.21060v1`
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `'0.45' in https://arxiv.org/html/2605.10681v2`
>
> Searched the web for `https://doi.org/10.1109/ICC59461.2026.11587390`
>
> - Ran `python - <<'PY'
> import urllib.request,re
> u='https://www.ieeevtc.org/vtc2023fall/DATA/2023002717.pdf'
> try:
>  import fitz
>  doc=fitz.open(stream=urllib.request.urlopen(u,timeout=25).read(),filetype='pdf')
>  txt=' '.join(p.get_text() for p in doc)
>  for pat in ['two LDPC','C1','C2']:
>   m=re.search(pat,txt)
>   if m: print(pat,txt[max(0,m.start()-250):m.start()+750])
> except Exception as e: print(type(e).__name__,str(e))
> PY`
>
> </details>
>
> <details><summary>Ran a command</summary>
>
> - Ran `python3 - <<'PY'
> import urllib.request,re
> u='https://www.ieeevtc.org/vtc2023fall/DATA/2023002717.pdf'
> try:
>  import fitz
>  doc=fitz.open(stream=urllib.request.urlopen(u,timeout=25).read(),filetype='pdf')
>  txt=' '.join(p.get_text() for p in doc)
>  for pat in ['two LDPC','C1','C2']:
>   m=re.search(pat,txt)
>   if m: print(pat,txt[max(0,m.start()-250):m.start()+750])
> except Exception as e: print(type(e).__name__,str(e))
> PY`
>
> </details>
>
> 方案已收敛到保留 NMS 校验更新、用微型 SSM 控制缩放与阻尼。还有一个会影响时延结论的关键限制：控制器每轮反馈到下一轮，因此 BP 迭代轴仍有顺序依赖，不能靠 parallel scan 一次并行完成。实验必须证明减少的迭代时间足以抵消控制器开销。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://www.ieeevtc.org/vtc2023fall/DATA/2023002717.pdf`
>
> Searched the web for `https://arxiv.org/abs/2505.17834`
>
> Searched the web for `"ACE-Grouped Neural Min-Sum"`
>
> Searched the web for `"A Foundation Model for Error Correction Codes"`
>
> Searched the web for `https://arxiv.org/abs/2312.00752`
>
> Searched the web for `'Table 5.3.2-1' in https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `https://arxiv.org/html/2605.10681v2`
>
> Searched the web for `'Table 1' in https://arxiv.org/html/2505.17834v1`
>
> Searched the web for `https://arxiv.org/html/2207.14742v1`
>
> Searched the web for `'lifting' in https://arxiv.org/html/2207.14742v1`
>
> Searched the web for `https://openreview.net/pdf?id=6lfnSzJ5qE`
>
> Searched the web for `'64%' in https://openreview.net/pdf?id=6lfnSzJ5qE`
>
> </details>
>
> 最终评估会按“完整图长度、固定打孔后的长度、速率匹配长度”分别记录 NR 参数，避免不同论文的码长口径混用。实验方案也会区分同一 lifting set 内放大 \(Z\) 和跨 lifting set 测试，防止把一般的码长迁移写成更强的泛化结论。
>
> 时延证据中还有一个重要口径差异：ECCM 在 4090 上报告的微秒数，是 batch=512 的总耗时除以码字数，不能当作 batch=1 的译码响应时间。推荐方案会同时测单码块时延和批量吞吐，并把重排、特征统计、早停及 fallback 的开销计入。
</details>

**唯一推荐：收紧后的 S2——“QC 基行级选择性状态记忆辅助 NMS 译码”。备胎：S5——“速率匹配条件化的跨配置泛化”。**

但查新后需要降低预期：**“Mamba 用于译码”“syndrome 条件化”“用循环状态控制下一轮 NMS”都已有直接先例。**你可以争取的贡献，是一个更具体、可被对照实验证伪的判断：

> 在相同特征、相同状态粒度和相近计算预算下，QC 基行级选择性状态记忆，能否比无记忆控制、EMA 和 GRU 更有效地减少 NR LDPC 的译码迭代，并兑现为 GPU 时延收益？

下面按你要求的七步展开。

**1）假设与参数边界**

信息足够，直接继续。默认：

- 采用 **BPSK/AWGN 的 NR 编码级仿真**，准确已知噪声方差；
- 首篇只做 **LDPC BG2、单传输块、单码块**；
- 主指标是信息块 BLER，辅助报告 BER、平均迭代数和 GPU 时延；
- 周数按每周约 **20 小时有效投入**估算，包含复现、实验和写作；
- 下述新方法的性能、显存和时延收益全部 **待实测**。

你的九项纠正全部作为约束。再统一一个容易混淆的长度口径：

| 对象 | BG1 | BG2 |
|---|---:|---:|
| 最大编码输入长度 | \(22\times384=8448\) | \(10\times384=3840\) |
| 完整 Tanner 图变量数 | \(68Z\) | \(52Z\) |
| 固定打孔首 \(2Z\) 后的编码输出长度 | \(66Z\)，最大 25344 | \(50Z\)，最大 19200 |
| 速率匹配后实际发送长度 | \(E_{\rm tx}\) | \(E_{\rm tx}\) |

因此，构造 \(H\)、恢复打孔位和统计译码复杂度时，要说明用的是完整图还是经过等价裁剪的图。Polar 母码长度上限继续采用 DL 512、UL 1024 的边界。依据固定到 TS 38.212 V18.5.0，避免不同版本和论文口径混用。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

Mamba-1 与 Mamba-2 也要区分：前者的核心是输入相关参数与硬件感知 selective scan；后者通过 SSD 和结构化分块，把更多运算转成适合矩阵乘法的形式。**这些长序列计算优势，不能直接推导到只有 10–30 步、且每步存在译码反馈的迭代控制任务。**([arxiv.org](https://arxiv.org/abs/2312.00752))

**2）2023–2026 查新：哪些已经做过**

检索截至 **2026 年 11 月 12 日**。覆盖了你列出的 Mamba decoding、SSM LDPC、Mamba Polar、GNN decoder、linear-complexity neural decoder、ECCT scalability、unrolled BP memory 等方向，并追踪了主要论文的参考文献。

表中“报告增益”均指原文结果，不能移植成你的预期收益；无法核实的码长或数字明确保留。

| 文献，可点击 | 方法 | 码型、码长 | 主要基线 | 原文报告结果及证据边界 | 对 S1–S6 的影响 |
|---|---|---|---|---|---|
| [Neural Adjusted Min-Sum Decoding for LDPC Codes，VTC 2023](https://www.ieeevtc.org/vtc2023fall/DATA/2023002717.pdf) | 学习选择 BP/MS 更新及边权 | 文中 NR LDPC，原文 \([k,n]=[30,150]\)、\([176,528]\) | BP、AMS、NMS、NBP、NNMS | 在部分设置较 NNMS 提升约 0.15–0.4 dB；复杂度略增。([ieeevtc.org](https://www.ieeevtc.org/vtc2023fall/DATA/2023002717.pdf)) | “学习缩放/选择更新规则”已有先例，S2 需要证明历史状态的额外价值 |
| [A Foundation Model for Error Correction Codes，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/093b793f0af498e8fa218eb5445daeb0-Abstract-Conference.html) | 码长无关嵌入、图条件注意力、多码训练 | BCH、Polar、LDPC 等；训练长度不超过 150，测试包含更长码 | 码专用神经译码器、ECCT 等 | 已展示未见码上的 zero-shot 和微调能力；不存在可概括全部设置的统一 dB 增益。([proceedings.iclr.cc](https://proceedings.iclr.cc/paper_files/paper/2024/hash/093b793f0af498e8fa218eb5445daeb0-Abstract-Conference.html)) | S5 不能以“一个模型支持多个码”为创新 |
| [CrossMPT，2024 预印本／ICLR 2025](https://arxiv.org/abs/2405.01033) | magnitude/syndrome 双流、\(H\) 掩码交叉注意力 | 多类线性码；含 BCH(31,16)、LDPC(648,540) 等 | ECCT、BP、其他神经 BP | 报告 BER 与资源效率改善，具体幅度随码而变。([arxiv.org](https://arxiv.org/abs/2405.01033)) | 图结构注入、双流更新已成熟；S1 不能只做结构重排 |
| [Accelerating Error Correction Code Transformers，2024](https://arxiv.org/abs/2410.05911) | 三值权重、注意力头划分、图位置编码 | 多类短码；完整码长清单待核实 | ECCT | 摘要报告约 90% 压缩；能耗数字采用其运算能耗口径，不能视为 GPU 端到端加速。([arxiv.org](https://arxiv.org/abs/2410.05911)) | S6 要区分 FLOPs、估计能耗和实测时延 |
| [White-box Error Correction Code Transformer，PMLR 2025](https://proceedings.mlr.press/v280/zheng25a.html) | Tanner 子空间注意力、稀疏率缩减解释 | BCH、Polar、LDPC 等，主要为几十至百余比特 | ECCT、CrossMPT 等 | BCH(63,45) 上六层模型参数约减少 64%；不代表所有设置 BLER 都更好。([proceedings.mlr.press](https://proceedings.mlr.press/v280/zheng25a.html)) | “白盒化”“结构感知”也需要具体机制与消融 |
| [Hybrid Mamba–Transformer Decoder，ECCM，2025](https://arxiv.org/abs/2505.17834) | Mamba/Transformer 混合、校验结构掩码、逐层监督 | BCH、Polar、LDPC；例如 Polar(128,86)、LDPC(121,60) | BP、ARBP、ECCT、AECCT、CrossMPT | BCH 较强，LDPC 有胜有负；已报告 4090 计时，但采用 batch=512 后折算每码字时间。([arxiv.org](https://arxiv.org/html/2505.17834v1)) | **直接覆盖泛化的“Mamba 混合译码器”选题** |
| [Cross-Attention Message-Passing Transformers for Code-Agnostic Decoding，2025](https://arxiv.org/abs/2507.01038) | FCrossMPT、跨码配置共享及集成译码 | 多码型、码长、码率；完整 NR 配置覆盖待核实 | CrossMPT、基础模型类译码器 | 已提出码长、码率、码型无关模型及未见码实验。([arxiv.org](https://arxiv.org/html/2507.01038v1)) | 再次压缩 S5 的宽泛新颖空间 |
| [ACE-Grouped Neural Min-Sum Decoding with a GRU Hypernetwork，ICC 2026](https://doi.org/10.1109/ICC59461.2026.11587390) | ACE/短环分组 NMS；每轮可靠度摘要进入 GRU，调制下一轮权重；未满足校验比例变化触发 | QC-LDPC；具体码长待核实 | 分组、逐边、boosted 等方案；完整对应关系待核实 | 官方摘要报告 waterfall、error floor 与增量复杂度改善；具体数值待全文核实。([doi.org](https://doi.org/10.1109/ICC59461.2026.11587390)) | **S2、S3 最接近的直接先例：跨迭代记忆控制 NMS 已被做过** |
| [Scalable Mamba-Based Message-Passing Neural Decoder，MMPD，2026](https://arxiv.org/abs/2605.10681) | Tanner 边消息聚合＋双向 Mamba | 性能实验含 LDPC(384,320)、(529,440)、(648,540)、(1056,880)；另有 NR 资源扩展实验 | ECCT、CrossMPT、BP | 摘要在(1056,880)报告较 CrossMPT 约 0.45 dB、显存约缩至 \(1/1.5\)；NR 部分主要验证资源扩展，不能等同于 NR 长码 BLER 优势。([arxiv.org](https://arxiv.org/abs/2605.10681)) | 图结构 Mamba、线性边交互显存均已有直接工作 |
| [CrossMPM，2026-10-28](https://www.mdpi.com/2079-9292/15/21/4986) | Tanner 图投影生成选择性扫描参数，双向扫描 | 短 LDPC 至(529,440)，含 WRAN(384,320) | CrossMPT、ECCM | 在(529,440)较 CrossMPT 报告 FLOPs 降低 48.90%、训练峰值显存降低 54.94%。([mdpi.com](https://www.mdpi.com/2079-9292/15/21/4986)) | **S3 的“syndrome／图信息注入 \(\Delta/B/C\)”已有非常接近的实现** |
| [Neural Window Decoding of SC-LDPC Codes，2024，更新至 2026-11-07](https://arxiv.org/abs/2411.19092) | 结构化训练、阻尼、消息复用、权重切换 | 长度 20,000 的(3,6)规则 SC-LDPC | 加权 MS、sum-product 窗口译码 | 报告约 48% 的**估计计算成本**下降；对象是 SC-LDPC，不能当作 NR 或 GPU 时延结果。([arxiv.org](https://arxiv.org/abs/2411.19092)) | 阻尼、调度、复用历史消息不能直接认领为新概念 |
| [Deep Learning-Assisted Adaptive Dynamic-SCLF，TCCN 2024](https://ieeexplore.ieee.org/abstract/document/10380217) | 学习翻转度量参数＋自适应列表 | Polar；具体码长待全文核实 | D-SCLF/SCLF 相关方案，数字对应基线待核实 | 摘要报告最高 0.35 dB 改善、57.65% 平均复杂度降低等，需按具体配置解读。([ieeexplore.ieee.org](https://ieeexplore.ieee.org/abstract/document/10380217)) | S4 的自适应 \(L\)、翻转排序和学习度量已有密集先例 |

还必须保留一篇窗口外的基础锚点：[Graph Neural Networks for Channel Decoding，2022](https://arxiv.org/abs/2207.14742)。它已经在 NR LDPC 上展示过训练一次后改变 lifting factor 和码率；论文同时明确指出速率匹配会带来训练稳定性问题。**因此，S5 真正值得研究的是速率匹配扰动下的可靠迁移，而非普通权重共享。**([arxiv.org](https://arxiv.org/html/2207.14742v1))

据此，六个原始切口的查新判断是：

| 切口 | 已被覆盖的部分 | 仍可检验的差异 |
|---|---|---|
| S1 | 图结构＋Mamba、双向扫描、低复杂度 | **QC 专用布局是否带来真实 GPU 访存与时延收益** |
| S2 | 循环记忆、可靠度摘要、下一轮权重控制 | **QC 基行分别保留历史，是否优于同粒度 GRU/EMA** |
| S3 | syndrome 双流、图条件选择性参数 | 独立立项价值低，适合作为 S2 输入特征消融 |
| S4 | 学习度量、翻转排序、自适应列表 | 直接的 Mamba＋NR CA-SCL 先例本次未确认；这不构成空白证明 |
| S5 | 跨码长、跨码率、多码共享 | **未见 lifting set 与速率恢复模式下的泛化设计及验证** |
| S6 | 神经译码复杂度、显存比较 | 同算法双实现，隔离布局与访存因素，作为第二贡献 |

**结论是：六个原始表述都不适合原样写成论文创新点。**

**3）把范围裁到 4–6 页和一张显卡能完成**

建议首篇只回答一个问题：

> 给定相同 NR 编码配置，在固定最大迭代预算下，结构化历史控制能否改善 NMS 的 BLER—计算量折中？

范围保留与裁剪如下。

| 保留 | 裁掉，放进 future work |
|---|---|
| BG2、AWGN、单码块 | BG1 全参数覆盖、完整 OFDM/MIMO 接收链 |
| 一种主调度，优先 flooding 便于公平展开 | 同时优化 flooding、layered、动态行调度 |
| 缩放与阻尼中的一个先做，另一个作扩展 | 学更新规则＋调度＋早停策略＋RL 同时学习 |
| 固定迭代 BLER、同 BLER 时延 | error floor 主张、超越 BP-OSD |
| 两个主训练配置、少量留出配置 | 全部 \(Z\)、码率、RV 的大规模联合扫描 |
| FP32 主结果，必要时补一种精度 | 4-bit、FPGA、无乘法器硬件 |
| 小型选择性 SSM | Attention/CNN/Mamba 多模块堆叠、基础模型预训练 |

PINN、ISAC、FPGA 和 \(n=10^5\) 只在 future work 用一句话列出。

建议固定以下实验配置，记为 **P 协议**。这些是拟采用的编码级配置，不是已完成结果：

| 用途 | \(Z\) | 编码输入 \(B=10Z\) | 载荷 \(A=B-16\) | 主发送长度 \(E_{\rm tx}=2B\) |
|---|---:|---:|---:|---:|
| 训练配置 1 | 96 | 960 | 944 | 1920 |
| 训练配置 2 | 128 | 1280 | 1264 | 2560 |
| 留出长度 1 | 192 | 1920 | 1904 | 3840 |
| 留出长度 2 | 256 | 2560 | 2544 | 5120 |

这些载荷使用 TB CRC16，单码块情况下无需额外 CB CRC。BG2 选择、lifting size 和 filler 仍由标准流程计算，不能只手动指定 \(H\)。例如增加 \(A=1208\)、\(B=1224\)、\(Z=128\) 的补充配置，可得到 56 个 filler 位。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

泛化实验还要区分：

- \(96\rightarrow192\)：同一 lifting set 内放大；
- \(128\rightarrow256\)：另一 lifting set 内放大；
- 留出 \(Z=160\)：测试未参与训练的 lifting set。

这三种情形不能混写成同一种“跨码长泛化”。标准表中 96/192 属于 set 1，128/256 属于 set 0，160 属于 set 2。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

训练 SNR 不先猜固定区间。先找出每个配置下 NMS-20 的 waterfall 中心 \(\gamma_Z\)，再采用拟定混合区间：

\[
E_b/N_0\in\gamma_Z+\{-1,-0.5,0,0.5,1\}\ {\rm dB}.
\]

测试覆盖 BLER 约 \(10^{-1}\) 到 \(10^{-3}\) 的区域。明确 \(E_b\) 按载荷 \(A\) 还是按含 CRC 的 \(B\) 归一化；建议全文统一采用 \(R_{\rm payload}=A/E_{\rm tx}\)。

**4）打分与初步排序**

分数为我的选题判断，**不代表录用概率**。新颖度、会议匹配度越高越好；算法和工程难度越高越困难。周数从零启动估算。

| 切口 | 收紧后的一句话 \(\Delta\) | 新颖度 /5 | 算法难度 /5 | 工程难度 /5 | 预计周数 | 单卡可行性 | 撞车风险 | 会议匹配度 /5 |
|---|---|---:|---:|---:|---|---|---|---:|
| **S2\*** | QC 基行级历史状态辅助 NMS，减少达到目标 BLER 所需迭代 | 3 | 2 | 2–3 | 10–12 | 高 | 中高：ACE-NMS-GRU | 4 |
| **S1\*** | QC 校验坐标中的规则扫描布局，改善 GPU 执行效率 | 3 | 4 | 5 | 12–16 | 条件可行 | 高：MMPD/CrossMPM | 3 |
| **S5\*** | 速率恢复条件化的共享 SSM 控制，改善未见配置迁移 | 2–3 | 3 | 3 | 10–14 | 高 | 高：GNN/FECCT 系列 | 4 |
| S3 | syndrome 条件化；作为 S2 特征消融 | 1 | 2 | 2 | 作为附加实验 1–2 | 高 | 很高 | 独立立项 1 |
| S4 | 显式 CA-SCL 上的跨重试记忆辅助列表选择 | 2 | 3 | 4 | 10–14 | 高 | 高：学习 SCLF/自适应列表 | 3 |
| S6 | 同算法不同布局，隔离规则计算与图访存成本 | 独立不评分 | 2 | 4 | 附加 2–4 | 高 | 主贡献不足 | 作为支撑 4 |

初排为 **S2\* > S1\* > S5\***。第六步再按审稿证据和毕业风险修正。

**5）六个建模问题，以及 Top3 的具体方案**

先把全部切口的 a–f 明确落地，避免只给网络名字。

以下 LDPC 方案共享一个标准接口：

> 逆交织／速率恢复 → 完整图 LLR → 译码 → syndrome 与 CRC 检查。

打孔位 LLR 设为 0；重复位 LLR 累加；filler 位设置已知零对应的有限饱和值并携带 mask。CRC 位属于译码对象，不能从测试中悄悄删掉。速率匹配与 CRC 接口遵循标准流程。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

| 切口 | a）任务与输出 | b）结构如何注入 | c）syndrome 如何使用 |
|---|---|---|---|
| S1\* | 非自回归块译码；输出软 LLR 估计，再硬判决 | 按 QC 循环移位展开校验邻域，在校验坐标扫描 | 输入特征＋精确早停；辅助损失仅消融 |
| S2\* | 非自回归块译码；迭代控制因果；输出软 LLR 估计 | 保留 NMS 的 \(H\) 消息传递；每个 QC 基行独立状态、共享控制器 | 每行违反率与变化量作为输入；精确早停 |
| S3 | 非自回归；输出软 LLR 或噪声估计 | 图投影后条件化 Bi-Mamba；不能只拼接原始比特序列 | 条件输入＋早停；是否加软校验损失单独消融 |
| S4 | SC/SCL 内部有因果依赖；网络输出 \(L\)／重试评分，最终输出硬信息位 | 保留极化树、路径度量、部分和、显式列表 | 主要使用 CRC 与列表状态；不强加 LDPC 式 syndrome 损失 |
| S5\* | 非自回归；输出软 LLR 估计 | QC 权重共享＋观察类型 mask＋归一化结构统计 | 分观察类型的违反率输入＋早停 |
| S6 | 与选定主模型相同，建议直接采用 S2\* | 同一算法实现 QC 规则布局和通用图布局 | 两实现使用完全相同的检查与早停 |

| 切口 | d）速率匹配、CRC | e）合法性与 fallback | f）训练、泛化测试 |
|---|---|---|---|
| S1\* | 上述 LDPC 标准接口 | 检查未通过时继续经典 NMS，达到总预算仍失败则上报 | P 协议；\(Z=384\) 可仅补资源测试，不预设性能泛化 |
| S2\* | 同上；主结果 RV0 | 神经控制若干轮后关闭控制器继续 NMS；整体开销完整统计 | P 协议；10/20 轮为主，30 轮作经典参考；码率 \(B/E_{\rm tx}=1/3,2/3\) 少量压力测试 |
| S3 | 同一 LDPC 接口 | 精确检查＋NMS fallback | 与 P 相同，便于判断条件化是否有增量价值 |
| S4 | 选一种 PDCCH 配置，保留 CRC24C、RNTI 处理及标准速率匹配 | 只选择显式列表中的候选；CRC 未通过则增大 \(L\)／重试，上限后失败 | 可选 \(A=40,K=64\)，训练 \(E_{\rm tx}=108/216\)，对应母码 128/256；测试 \(E_{\rm tx}=432\)、母码 512 |
| S5\* | mask 区分打孔、单次观察、重复、filler；RV 进入条件 | 与 S2 相同，各配置分别报告失败率 | 训练 \(Z=96/128\)、\(B/E_{\rm tx}=1/3,1/2\)、RV0；留出 \(Z=160/192/256\)、码率 \(2/3\)、RV2，区分单轴与联合留出 |
| S6 | 两实现完全一致 | 两实现必须得到一致输出与停止行为 | 不增加训练；同一权重在相同配置测 batch=1 和批量吞吐 |

这里的“合法性”必须准确表述：**\(H\hat c=0\) 保证属于 LDPC 码空间，不能保证恢复了发送码字；CRC 也存在漏检。**可实现的保证是：只接受通过既定检查的结果，否则返回失败；fallback 也不能提供零错误保证。([arxiv.org](https://arxiv.org/html/2207.14742v1))

下面展开 Top3。

**方案一：S2\*，首选**

中文题目：

> **QC 基行级选择性状态记忆辅助的 5G NR LDPC 低迭代译码**

英文题目：

> **QC Row-Wise Selective State Memory for Iteration-Efficient 5G NR LDPC Decoding**

核心 \(\Delta\) 只选 **跨迭代历史记忆**。

ACE-NMS-GRU 已经覆盖“可靠度摘要→循环状态→下一轮分组权重”。你拟验证的差异，是把状态放到 **QC 基行粒度**，保留各类校验约束不同的收敛历史，并通过受约束的选择性状态控制缩放或阻尼。**拿到 ACE 全文前，这只能叫候选差异，不能宣布新颖性已成立。**([doi.org](https://doi.org/10.1109/ICC59461.2026.11587390))

拟采用的最小模型如下。第 \(r\) 个基行、第 \(t\) 次迭代提取：

\[
f_{r,t}=
\left[
\text{校验违反率},
\text{违反率变化},
\operatorname{mean}|m|,
\operatorname{mean}|m^{(t)}-m^{(t-1)}|,
\text{观察类型统计}
\right].
\]

维护小型选择性状态：

\[
h_{r,t}
=\bar a(f_{r,t})\odot h_{r,t-1}
+\bar b(f_{r,t})\odot u(f_{r,t}),
\qquad 0<\bar a<1.
\]

控制器输出有界正缩放 \(\alpha_{r,t+1}\) 和阻尼 \(\eta_{r,t+1}\)：

\[
\tilde m_{r}^{(t+1)}
=\alpha_{r,t+1}m_{\mathrm{MS},r}^{(t+1)},
\]

\[
m_r^{(t+1)}
=(1-\eta_{r,t+1})\tilde m_r^{(t+1)}
+\eta_{r,t+1}m_r^{(t)},\quad 0\le\eta<1.
\]

**先只学阻尼或缩放之一。**上述形式是拟议设计，不是论文结果。

这里有三个关键约束：

- 校验节点的符号积、最小值更新仍由 NMS 完成，SSM 不重新学习异或约束。
- 控制器反馈下一轮，因此整个迭代轴仍有顺序依赖，无法一次 parallel scan 完成。
- 若只实现微型 diagonal selective SSM，论文就称 SSM；不应把它包装成完整 Mamba-2。

对全零码字训练，应使用绝对消息、绝对残差和 syndrome 等符号不变特征，并保持正缩放与对称消息更新；再用随机非零码字验证。否则全零训练的有效性没有保证。对称预处理与全零训练是已有神经译码中的重要设计基础。([ieeevtc.org](https://www.ieeevtc.org/vtc2023fall/DATA/2023002717.pdf))

技术路线控制在五步：

1. 对拍 NR 编码、速率恢复、NMS/OMS，固定一种主调度。
2. 建立无记忆 MLP、EMA、同粒度 GRU、全局 SSM、基行 SSM 五组控制器。
3. 先展开 10 轮训练，再测试 10/20 轮；加入历史截断长度消融。
4. 完成固定迭代 BLER，以及包含 fallback 的整体 BLER。
5. 优化共同 NMS 内核和控制器调用，测真实时延。

预期卖点图表：

- **图 1：**结构和控制器接口；
- **图 2：**固定迭代数 BLER，突出 EMA/GRU/SSM 的区别；
- **图 3：**同 BLER 的平均迭代数—时延 Pareto；
- **表 1：**参数、状态、峰值显存、batch=1 的 p50/p95。

主要风险是基行统计过度压缩，或者 GRU/EMA 已足够。Plan B 是先限制为单一阻尼控制，并检查状态粒度是否真正有贡献；若同粒度 GRU/EMA 持续相当，转向 S5，不能靠继续堆模块维持“Mamba 必要性”。

你需要补齐的专项能力主要是 **码字符号对称性、状态控制消融、BLER 置信区间**，无需再扩展到 RL。

**方案二：S1\*，算法与 GPU 风险最高**

中文题目：

> **面向 5G NR QC-LDPC 的校验坐标状态空间混合译码**

英文题目：

> **Check-Aligned State-Space Hybrid Decoding for 5G NR QC-LDPC Codes**

核心 \(\Delta\) 只选 **规则计算的 GPU 执行优势**。

与 MMPD、CrossMPM 的差异不能停留在结构注入，而应落实到：**按 QC 移位组织计算，减少通用边表实现中的中间张量与不规则访问，并证明整体更快。**已有工作已经把 Tanner 消息传递和双向 SSM 结合。([arxiv.org](https://arxiv.org/html/2605.10681v2))

结构注入采用显式校验坐标。对基图非零位置 \((r,c)\)：

\[
u_{r,c,z}
=x_{c,(z+s_{rc})\bmod Z},
\]

其中移位方向必须与实际 \(H\) 的约定一致。把同一个校验涉及的邻居放进同一局部特征，再沿提升坐标 \(z\) 扫描。该设计直接来自 QC 循环置换结构。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

**一个全局比特排列无法一般性地让所有校验邻居都连续。**因此，该方案仍然包含循环移位、变量复制和回聚，必须计入成本；不能声称 gather/scatter 已消失。

技术路线：

1. 实现基于非零 QC 子块的校验坐标布局，保留 degree/padding mask。
2. 在相同布局比较 MLP、短卷积、Bi-SSM，隔离序列模型的作用。
3. 让模块输出 NMS 的校验级可靠度调制，先保留经典消息更新。
4. 实现通用边表与 QC 专用两种执行方式，验证数值一致性。
5. 与优化后的 QC-NMS、同布局 GNN 比较 BLER、访存量和时延。

预期图表：

- 布局示意与中间张量字节数；
- BLER—时延曲线；
- 不同 \(Z\)、batch 下的内核时间分解；
- padding、重排和回聚的成本占比。

风险是 **减少索引开销，却增加复制、padding 和扫描开销**。如果布局有效而 SSM 无增益，只能把贡献归于结构化执行；这会削弱当前“Mamba/SSM 算法创新”主线。

Plan B 是降低 SSM 调用频率，例如每若干轮 NMS 调用一次，并限制在一个 BG、一个码率。你的 CUDA/Triton 技能适合该方案，但需要补齐 **内存流量核算、图布局公平对照和循环边界敏感性分析**。

**方案三：S5\*，备胎**

中文题目：

> **速率匹配条件化状态空间控制的 5G NR LDPC 跨配置泛化译码**

英文题目：

> **Rate-Matching-Conditioned State-Space Control for Cross-Configuration 5G NR LDPC Decoding**

核心 \(\Delta\) 只选 **跨码长码率泛化**。

GNN 已经做过跨 \(Z\)、跨码率；FECCT、FCrossMPT 也已经研究码无关模型。这里需要更窄的假设：

> 跨配置退化的一部分来自观察模式变化；显式区分打孔、重复、filler，并对可靠度统计作结构化归一化，能否改善未见速率恢复模式的迁移？([arxiv.org](https://arxiv.org/html/2207.14742v1))

拟采用 S2 的稳定骨架，但作三项限定：

- 控制器共享权重，不使用绝对 \(z\) 编号的可学习嵌入；
- 按“未观察／单次观察／重复／已知 filler”分别统计可靠度；
- 使用随输入与 mask 一起变换的 QC 结构表示。

可以分析特定循环移位下的等变性，但**等变性不等于跨 \(Z\) 泛化保证**。

技术路线：

1. 建立严格训练／验证／测试配置清单，禁止测试配置参与调参。
2. 按表中的 S5 设置联合训练。
3. 分别测试仅改变 \(Z\)、仅改变码率、仅改变 RV，以及联合留出。
4. 比较同样多配置训练的 GNN、无 mask 控制器、普通归一化控制器。
5. 同时报 zero-shot 与少量微调结果，量化适配成本。

预期图表：

- 训练配置→测试配置的泛化矩阵；
- 未见配置上的 BLER；
- zero-shot 与微调样本量曲线；
- mask 和归一化设计消融。

风险是只得到“多配置训练比单配置好”，这属于预期现象。Plan B 是收缩到 **同一 BG 下跨 lifting set＋特定速率匹配变化**，并如实改写贡献；不能仅靠增加测试配置挽救新颖性。

你需要补齐的是 **配置级数据划分、零样本与微调的严格区分、归一化设计的解释**。它能复用 S2 的大部分编码和训练工程，因此适合备胎。

**6）按苛刻 TPC 的标准批判，再修正排序**

| 审稿意见 | 目前为什么成立 | 最低限度的修正 |
|---|---|---|
| **“线性复杂度不算创新。”** | NMS、展开 BP、GNN 已有稀疏图线性复杂度；MMPD 也已采用边限制交互 | 从创新点删除“大 O 更优”；只保留历史控制、GPU 执行或泛化之一。([arxiv.org](https://arxiv.org/html/2207.14742v1)) |
| **“只是把 Mamba 搬来译码。”** | ECCM、MMPD、CrossMPM 已直接做过 | 必须有具体结构假设，并证明优于同粒度 GRU、EMA、MLP。([arxiv.org](https://arxiv.org/abs/2505.17834)) |
| **“跨迭代记忆也不是新的。”** | ACE-NMS-GRU 已控制下一轮权重 | 核对其全文；比较状态粒度、特征、训练预算与状态预算，避免只换单元。([doi.org](https://doi.org/10.1109/ICC59461.2026.11587390)) |
| **“没有和 GNN 公平比较。”** | 相同参数量不等于相同训练预算、图实现效率或 BLER | 同 \(H\)、速率匹配、训练数据与早停；同时报告资源预算和同 BLER 比较 |
| **“时延优势没测出来。”** | 少迭代不一定更快；批量折算时间也不是单码块响应时间 | batch=1 独立测量；重排、统计、检查和 fallback 全部计时 |
| **“泛化只是换了 \(Z\)。”** | 已有 NR GNN 工作 | 区分 lifting set、码率、RV 和 filler；提供严格留出及联合留出。([arxiv.org](https://arxiv.org/html/2207.14742v1)) |

GPU 证据至少做到以下程度，作为拟议评测协议：

- **主比较：**校准过的 NMS/OMS、学习标量 NMS、同粒度 EMA/GRU、一个 GNN。
- **Transformer 补充：**选一个可训练的短 NR 配置做 ECCT/CrossMPT，长配置资源不足时报告限制。
- **调度一致：**固定迭代图使用相同 schedule；layered 作为强参考时，明确一次迭代的含义。
- **计时一致：**相同硬件、精度、预热、CUDA events 与同步策略，报告 p50/p95。
- **吞吐与响应分开：**batch=1 和批量测试分别报告；编译时间另列。
- **fallback 完整计入：**神经阶段、经典续译码、失败比例分别可追踪。

ECCM 的计时就是一个具体提醒：其测试采用 batch=512、200 个 batch，再除以码字数。该结果支持其批量效率分析，不能直接用作单码块低时延证据。([arxiv.org](https://arxiv.org/html/2505.17834v1))

一个值得提前计算的门槛是：

\[
t_{\rm SSM}\approx
\bar T_{\rm SSM}\,c_{\rm NMS}(1+\rho),
\]

其中 \(\rho\) 为特征统计和控制器相对一次 NMS 的开销。忽略共同固定开销时，想更快必须满足：

\[
\frac{\bar T_{\rm SSM}}{\bar T_{\rm NMS}}
<\frac{1}{1+\rho}.
\]

例如 \(\rho=0.2\)，就需要减少超过约 **16.7%** 的平均迭代才能抵消新增开销。**这是数学算例，不是实测目标或收益承诺。**

误码统计也不要追求超出论文承载能力的结论：

- 主结果做到 BLER 约 \(10^{-3}\)；
- 每点尽量收集 100–200 个块错误并给区间；
- 至少三个训练种子检查方法差异；
- 零错误时给上界，不能画成 BLER=0：由 \((1-p)^N=0.05\)，95% 上界约为 \(3/N\)。

经过上述审查，**毕业优先排序修正为：**

\[
\boxed{\text{S2*}>\text{S5*}>\text{S1*}}
\]

S1 从第二降到第三，原因是执行布局、模型表达和内核优化三个因素难以在短论文中分离，工程风险最高。S5 虽然新颖性空间较窄，但可以复用 S2 工程并及时收缩边界。

S3 合并为消融；S4 暂不启动；S6 随主方案完成。

**7）唯一推荐、备胎与立即启动的三件事**

**推荐 S2\***，理由是它保留可靠的经典骨架、状态规模小、对照清晰，且两周内就能判断核心假设是否值得继续。论文主张应限定为：

> 在指定 NR BG2 配置下，QC 基行级选择性状态记忆改善 NMS 的迭代效率；GPU 测量验证其整体成本。

**备胎 S5\***，理由是复用同一译码器，把研究问题转为速率匹配条件化与未见配置迁移。它同样需要机制消融，不能仅靠增加泛化测试成立。

立即启动这三件事：

1. **建立一个可对拍的 NR 基准。**
   从 \(Z=128,A=1264,B=1280,E_{\rm tx}=2560\) 开始，记录完整图长度 6656、固定打孔后长度 6400；与 MATLAB 或 Sionna 对拍编码、速率恢复、syndrome 和 CRC，再跑校准后的 NMS/OMS。

2. **做最小的“记忆是否有用”实验。**
   相同基行特征下比较静态参数、MLP、EMA、GRU、选择性 SSM，先只控制一种量、展开 10 轮。同时核对 ACE-NMS-GRU 全文；摘要代理实现必须明确标注为代理，不能宣称复现或超越原方法。

3. **设一个两周决策点。**
   同时看固定迭代 BLER、同 BLER 的迭代数、batch=1 总时延。只有当历史状态有稳定增益，且 SSM 相对 EMA/GRU 有可解释优势时，继续 S2；否则及时转入 S5。

**按时毕业的关键，是尽早验证“结构化历史记忆是否必要”，并把无效分支及时停掉。**

> 选题已定为 S2*。请把架构与数学定义敲到"能直接写代码"的粒度，不要泛泛而谈：
> 1) 序列轴选择：比特轴 / 边轴 / Z-block轴 / 迭代轴，列出各自序列长度、每步计算量、能否覆盖校验约束、GPU友好度，选定其一并说明理由；
> 2) 结构注入：给出QC-LDPC的重排规则（按base row/column分组、Z循环移位对齐）、位置编码方案（如(row, col, z)三元组或可学习结构嵌入）、是否跨Z共享权重；若选Polar，说明因子图/部分和依赖如何进入模型；
> 3) 条件化：syndrome违反度、SNR、信道状态如何注入（选择性参数Δ/B/C 还是 FiLM），给出公式；
> 4) 损失函数：BCE + syndrome惩罚项的权重设计；是否用NMS软输出做蒸馏teacher；是否用SNR课程学习；
> 5) 输出与兜底：硬判决后做Hĉ校验，不通过则fallback到NMS；Polar保留CRC。给出fallback触发率的统计方式（这本身是一个好指标）；
> 6) 速率匹配：打孔/缩短/重复位在输入序列中如何表示（掩码/占位/LLR置零），训练与测试如何保持一致；
> 7) 复杂度与显存：给出每码字FLOPs公式与峰值显存公式（含层数、d_model、d_state、expand、batch），并代入我的码长算出数量级；
> 8) 训练细节：在线数据生成、SNR采样范围、是否可用全零码字+对称性假设（说明前提条件）、优化器/LR/梯度裁剪、预计训练步数与GPU时；
> 9) 模块图（文字版）+ 前向伪代码 + 超参初值表；
> 10) 预留消融钩子：重排方式、单/双向、d_state、条件化开关、损失项开关、Mamba-1 vs Mamba-2、fallback开关。
> 所有涉及库版本/后端支持的判断标注"待核实"，不许猜。

<details><summary>13 previous messages</summary>

> 我会把 S2* 固定为可实现的“QC 基行级迭代状态控制器＋NMS”，明确张量形状、更新顺序和 fallback 接口，并按 BG2、\(Z=128\) 的配置核算计算量与显存。训练时长会给出试跑估算方法，不填未经实测的 GPU 小时。
>
> <details><summary>Explored a search, ran a command</summary>
>
> <details><summary>Explored a file, a search</summary>
>
> - Read `~/.codex/skills/communication-skills/coding/ldpc/SKILL.md`
> - Searched for `LDPC|Mamba|SSM|S2|QC|神经译码` in `MEMORY.md`
>
> </details>
>
> - Ran `pwd; rg --files -g 'AGENTS.md' -g '*Mamba*' -g '*mamba*' -g '*S2*' -g '*SSM*' -g '*选题*' .`
>
> </details>
>
> <details><summary>Explored a file, ran 2 commands, searched the web</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `~/.codex/skills/communication-skills/coding/ldpc/references.md`
>
> </details>
>
> - Ran `command -v python3; command -v uv; command -v pdftotext`
>
> - Ran `cat AGENTS.md; ls -d /Users/macbook/.codex/visualizations/2026/11/12/*`
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> </details>
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/ldpc/codes/5G_bg2.csv`
>
> </details>
>
> 实现顺序已经明确：沿迭代轴更新状态，42 个 BG2 基行共享控制器权重、各自保存状态；NMS 仍负责全部图消息更新。另一个要处理的细节是全零训练：打孔位初始 LLR 恰好为零，直接把其硬判决 syndrome 喂给控制器会引入符号对称性问题。我会使用带“已解析校验比例”的 syndrome 特征，并用随机非零码字检验对称性。
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `ls -d 03-仿真与实验 03-仿真与实验/信道编译码; python3 - <<'PY'
> import importlib.util
> for x in ['numpy','torch','scipy']:
>  print(x, bool(importlib.util.find_spec(x)))
> PY`
> - Ran `python3 - <<'PY'
> import urllib.request,csv,io,collections
> u='https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/ldpc/codes/5G_bg2.csv'
> a=list(csv.reader(io.StringIO(urllib.request.urlopen(u,timeout=25).read().decode()),delimiter=';'))
> r=None; edges=[]
> for x in a[2:]:
>  if x[0]:r=int(x[0])
>  edges.append((r,int(x[1]),list(map(int,x[2:10]))))
> deg=collections.Counter(r for r,c,s in edges)
> print('P',len(edges),'rows',len(deg),'cols',max(c for r,c,s in edges)+1,'dmax',max(deg.values()))
> print('row_degrees',[deg[r] for r in range(42)])
> print('row0 set0 shifts',[(c,s[0]%128) for r,c,s in edges if r==0])
> PY`
>
> </details>
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://arxiv.org/abs/2312.00752`
>
> Searched the web for `'50Z' in https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> </details>
>
> <details><summary>Created 2 files, searched the web</summary>
>
> Searched the web for `https://arxiv.org/abs/2405.21060`
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/budget_and_invariants.py` (+144 -0)
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/config.json` (+62 -0)
>
> </details>
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `python3 budget_and_invariants.py`
> - Ran `python3 -m json.tool config.json > /dev/null`
>
> </details>
>
> BG2 基图已核实为 197 个非零循环子块。按 \(Z=128\)、20 轮、\(d=16,s=4\) 核算，控制器状态每码字为 2,688 个 FP32 数，约 10.5 KiB；译码消息和训练反向图占用更大。我也做了小型 QC 代数检查：200 组测试中，163 组暴露了“打孔零值直接做硬 syndrome 特征”的对称性问题；使用解析掩码后，这些测试的符号等变误差为零。这只是代数检查，还不是 NR 译码性能验证。
>
> <details><summary>Created a file, edited a file, searched the web</summary>
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/README.md` (+249 -0)
>
> Searched the web for `site.arxiv.org 2312.00752 Mamba selective state spaces`
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `'Table 5.3.2-1' in https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/README.md` (+9 -1)
>
> </details>
>
> 规格、配置和可复算的预算脚本已落盘。还有两条实现边界会写清：默认控制器是自定义的微型选择性 SSM，不能称为完整 Mamba-1/2；固定形状 batch 即使标记了“已停止”码块，只要仍执行其算术，就没有兑现早停节省。Mamba 后端兼容性和实际 GPU 时长均保留为待核实。
>
> <details><summary>Ran a command, searched the web</summary>
>
> - Ran `python3 - <<'PY'
> from pathlib import Path
> import json
> p=Path('/Users/macbook/Documents/Obsidian Vault/03-仿真与实验/信道编译码/S2-QC行级SSM实现规格')
> json.loads((p/'config.json').read_text())
> for f in p.iterdir():
>  if f.is_file(): print(f.name, f.stat().st_size)
> PY`
>
> Tool call
>
> Tool: open_in_codex
> Status: completed
>
> Searched the web for `https://arxiv.org/abs/2312.00752`
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `'Table 5.3.2-1' in https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> </details>
</details>

固定 **S2* v0：沿迭代轴运行、每个 QC 基行独立保存状态、共享控制器权重；选择性 SSM 输出阻尼系数，flooding NMS 完成图消息更新。**

输出为软 LLR，推理采用 **最多 20 轮神经辅助＋10 轮经典 NMS 续译码**。以下数值是实现初值；性能、实际峰值显存和 GPU 时长均待实测。

完整规格、配置及预算脚本已保存：

- [实现规格 README](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/README.md>)
- [配置 config.json](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/config.json>)
- [预算与代数检查脚本](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/budget_and_invariants.py>)

**1）序列轴：选择迭代轴**

沿用上一轮建议的 BG2、\(Z=128\) 基准。统一记号：

\[
m_b=42,\quad n_b=52,\quad P=197,
\]
\[
N=52Z,\quad M=42Z,\quad E_g=197Z.
\]

其中 \(E_g\) 是 Tanner 图边数，\(E_{\rm tx}\) 是发送长度，不能混用。BG2 的尺寸由标准规定；197 个非零循环子块由基图表逐项计数得到。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

在 \(Z=128\) 时：

\[
N=6656,\quad M=5376,\quad E_g=25216.
\]

设一次 SSM token 更新成本为

\[
C_s=O\!\left(J(dh+h^2+hs)\right),\qquad h=\mathrm{expand}\cdot d,
\]

\(J\) 为层数，\(d=d_{\rm model}\)，\(s=d_{\rm state}\)。

下表中的 GPU 友好度是工程判断，尚非测量结论。

| 序列轴 | 序列长度 | 每个序列步的主要计算 | 如何覆盖校验约束 | GPU 特点 |
|---|---:|---|---|---|
| 比特轴 | \(N=6656\) | 一个变量 token，约 \(C_s\) | 原始顺序扫描无法保证；仍需显式 \(H\) 模块 | 扫描规则，但结构邻域访问仍存在 |
| 边轴 | \(E_g=25216\) | 一个边 token，约 \(C_s\) | 按校验分段后聚合；变量信息被复制，需要回聚 | 序列长，中间张量多 |
| 非零 Z-block 轴 | \(P=197\) | 保留逐位信息时约 \(ZC_s\) | 循环移位对齐＋基行分段聚合 | 子块内规则，仍有移位和回聚 |
| **迭代轴** | **\(T=10\!-\!30\)** | **一轮 NMS＋统计＋42 个状态更新** | **NMS 直接处理完整 \(H\)** | 消息更新可并行，控制矩阵小，需防调用开销 |

这里将 Z-block 明确定义为“非零循环子块”。若定义成变量子块，长度为52，但每个 token 仍包含 \(Z\) 个位置，不能靠压成均值保持完整逐位信息。

**选择迭代轴的理由：**不重新学习校验规则，直接检验“历史控制能否减少迭代”。42 个基行同时更新，各自拥有状态，**不沿42个基行再扫描**。

由于下一轮 NMS 输入取决于上一轮控制结果，整个闭环仍有顺序依赖。Mamba 的并行扫描机制不能消除这条反馈依赖。([arxiv.org](https://arxiv.org/abs/2312.00752))

---

**2）结构注入、张量布局与精确 NMS 更新**

采用完整 BG2 图，不在首版裁剪打孔相关节点。

按 \((r,c)\) 排序所有非零基图元素，保存：

```text
row[P]       基行编号
col[P]       基列编号
shift[P]     当前 lifting set 对应的移位，模 Z
row_ptr[43]  基行分段指针
```

必须先选择正确的 lifting set，再读取移位。例如 \(Z=96\) 使用 set 1，\(Z=128\) 使用 set 0；不能拿同一组整数移位直接改变 \(Z\)。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

固定约定：

\[
H_{(r,z),(c,(z+s_{rc})\bmod Z)}=1.
\]

据此定义两个算子：

\[
\operatorname{Gather}(X)_{e,z}
=X_{c_e,(z+s_e)\bmod Z},
\]

\[
\operatorname{Scatter}(R)_{c,j}
=\sum_{e:c_e=c}R_{e,(j-s_e)\bmod Z}.
\]

概念上分别对应 `roll(-shift)` 和 `roll(+shift)`。循环置换的方向必须与编码器对拍；标准给出了右移单位阵的构造规则。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

主要张量：

| 张量 | 形状 |
|---|---|
| 信道 LLR、未饱和 posterior \(U\)、输出 \(L\) | `[batch, 52, Z]` |
| V2C \(Q\)、C2V \(R\) | `[batch, 197, Z]` |
| syndrome | `[batch, 42, Z]` |
| 动态统计 | `[batch, 42, 8]` |
| 外部条件 | `[batch, 42, 8]` |
| SSM 状态 | `[batch, 42, J, h, s]` |
| 阻尼系数 | `[batch, 42, 1]` |

位置编码采用 **4维可学习基行嵌入**：

\[
e_r\in\mathbb R^4,\qquad
x_r=W_f[f_r;e_r]+b_f.
\]

不加入绝对 \(z\) 嵌入，也不另加列位置嵌入：列关系和循环移位已经进入精确图消息传递。控制器及基行嵌入在不同 \(Z\) 间共享，但仅覆盖同一 BG；这不构成跨 \(Z\) 性能保证。

初始化：

\[
R^{(0)}=0,\qquad U^{(0)}=L^{ch},\qquad H^{SSM,(0)}=0.
\]

LLR 约定为

\[
L=\log\frac{P(c=0\mid y)}{P(c=1\mid y)}.
\]

每轮采用以下固定次序：

\[
Q^{(t)}
=\operatorname{clip}\!\left(
\operatorname{Gather}(U^{(t-1)})-R^{(t-1)},-20,20
\right).
\]

filler 对应的 \(Q\) 强制为 \(+20\)。然后计算标准 Min-Sum：

\[
m^{MS,(t)}_{e,z}
=
\prod_{\substack{e'\in\mathcal N(r_e)\\e'\ne e}}
\operatorname{sign}(Q^{(t)}_{e',z})
\min_{\substack{e'\in\mathcal N(r_e)\\e'\ne e}}
|Q^{(t)}_{e',z}|.
\]

规定 `sign(0)=+1`，通过第一、第二最小值实现排除目标边，并正确处理并列最小值。

控制器仅学习阻尼：

\[
R^{(t)}_{e,z}
=\operatorname{clip}\left[
(1-\eta_{r_e,t})\alpha m^{MS,(t)}_{e,z}
+\eta_{r_e,t}R^{(t-1)}_{e,z},
-20,20
\right],
\]

\[
U^{(t)}=L^{ch}+\operatorname{Scatter}(R^{(t)}),
\qquad
L^{(t)}=\operatorname{clip}(U^{(t)},-20,20).
\]

\(\alpha\) 在验证集校准后冻结；0.8只是初始候选。

**实现细节：保存未饱和的 \(U\)，形成 extrinsic 时先减旧消息再饱和。不能先把 \(U\) 截断，再减旧消息。**所有 filler 的 \(U,L,Q\) 均重新固定为 \(+20\)。

---

**3）条件化与选择性 SSM 的完整公式**

每轮控制使用上一轮结果；不存在未来信息。

先定义精确硬 syndrome：

\[
s_{r,z}
=\bigoplus_{e:r_e=r}
\mathbf1[L_{v(e,z)}<0].
\]

但打孔位初始 LLR 为零。直接把这些零值的任意硬判决用于控制，会破坏逐样本符号对称性。因此控制特征使用解析掩码：

\[
a_{r,z}
=\prod_{e:r_e=r}
\mathbf1[|L_{v(e,z)}|>\epsilon],
\qquad \epsilon=10^{-6},
\]

\[
u_r=
\frac{\sum_z a_{r,z}s_{r,z}}
{\max(1,\sum_z a_{r,z})},
\qquad
\chi_r=\frac1Z\sum_z a_{r,z}.
\]

\(u_r\) 是**已解析校验中的违反率**，\(\chi_r\) 是覆盖比例。早停仍使用全量精确 syndrome，不能用 \(u_r=0\) 替代。

八维动态特征：

\[
f_{r,t}=
\left[
u_r,\ \Delta u_r,\
\frac{\overline{|Q|}_r}{20},\
\frac{\overline{|R|}_r}{20},\
\frac{\overline{|R-R_{\rm prev}|}_r}{40},\
\overline{\max(0,1-|L|/2)}_r,\
\frac{t_{\rm completed}}{20},\
\chi_r
\right].
\]

均值在该基行关联的非 filler 边上计算。初始 \(\Delta u=0\)、消息变化量为零。

另设八维外部条件：

\[
c_r=
[u_r,\Delta u_r,\tilde\gamma,\gamma_{\rm known},
p_{\rm unobs},p_{\rm filler},p_{\rm repeat},\bar\nu_{\log}],
\]

其中 \(\nu_v\) 是位置 \(v\) 的观察次数，

\[
\bar\nu_{\log}
=\overline{\frac{\log(1+\min(\nu_v,4))}{\log5}}.
\]

默认关闭显式 SNR 条件：\(\tilde\gamma=\gamma_{\rm known}=0\)。打开时：

\[
\tilde\gamma=
\operatorname{clip}\left(
\frac{\gamma_{\rm dB}-\gamma_{\rm center}}2,-2,2
\right).
\]

\(\gamma_{\rm center}\) 固定为训练配置常量。AWGN 首版不输入 CSI；估计信道不属于本实现范围。

控制器默认 \(d=16,h=16,s=4,J=1\)。以下对每个基行、每层独立执行：

\[
z_t=\operatorname{RMSNorm}(x_t),
\]

\[
u_t=\tanh(W_uz_t+b_u),\qquad
g_t=\sigma(W_gz_t+b_g),
\]

\[
\Delta_t
=0.25+1.75\,\sigma(W_\Delta u_t+V_\Delta c_t+b_\Delta),
\]

\[
B_t^{s}=\tanh(W_Bu_t+b_B),\qquad
C_t^{s}=\tanh(W_Cu_t+b_C).
\]

形状分别为：

\[
u_t,g_t,\Delta_t\in\mathbb R^h,\qquad
B_t^{s},C_t^{s}\in\mathbb R^s.
\]

状态转移：

\[
\lambda_{i,k}
=\frac1{32}+
\left(2-\frac1{32}\right)\sigma(\theta_{i,k}),
\]

\[
a_{t,i,k}=\exp(-\Delta_{t,i}\lambda_{i,k}),
\]

\[
H_{t,i,k}
=a_{t,i,k}H_{t-1,i,k}
+(1-a_{t,i,k})B^s_{t,k}u_{t,i}.
\]

输出：

\[
y_{t,i}=\sum_k C^s_{t,k}H_{t,i,k}+D_i u_{t,i},
\]

\[
x_t^{out}=x_t+W_o(g_t\odot y_t)+b_o,
\]

\[
\boxed{\eta_{r,t}
=0.5\,\sigma\!\left(
w_\eta^\top\operatorname{RMSNorm}(x_t^{out})+b_\eta
\right)}.
\]

这是**自定义、归一化驱动的 ZOH 选择性对角 SSM**。输入相关参数的思想来自 selective SSM，但上述结构不等同于官方 Mamba-1。([arxiv.org](https://arxiv.org/abs/2312.00752))

它对应每步保持输入的连续方程

\[
\dot H=-\lambda H+\lambda B^su.
\]

由于 \(|u|\le1,|B^s|\le1,0<a<1,H_0=0\)，可直接推出逐元素 \(|H_t|\le1\)。

默认外部条件只直接进入 \(\Delta\)，不额外叠加 FiLM。FiLM 作为互斥对照：

\[
z'_t=
[1+0.1\tanh(W_\gamma c_t)]\odot z_t
+0.1\tanh(W_\beta c_t).
\]

训练时将统计特征 `detach`，但保留 SSM 状态链和译码消息链的梯度。这是**截断统计反馈的代理梯度**；连续统计不 detach 应作为消融。

---

**4）损失：BCE 为主，syndrome 为辅，蒸馏默认关闭**

信息集合 \(\mathcal I\) 包含实际系统输入位及 TB CRC，排除 filler。

由于正 LLR 表示0，送入普通 BCE 的 logit 应为 **\(-L\)**：

\[
\mathcal L_{\rm BCE}^{(t)}
=\frac1{|\mathcal I|}
\sum_{v\in\mathcal I}
\operatorname{softplus}\!\left[-(1-2c_v)L_v^{(t)}\right].
\]

只监督最后四轮：

\[
w=\frac{[1,2,4,8]}{15}.
\]

最终轮软校验损失：

\[
\mathcal L_{\rm syn}
=\frac1M\sum_{a=1}^{M}
\frac{1-\prod_{v\in\mathcal N(a)}
\tanh(L_v^{(T)}/2)}2.
\]

总损失：

\[
\mathcal L
=\sum_{t=T-3}^{T}w_t\mathcal L_{\rm BCE}^{(t)}
+\lambda_{\rm syn}\mathcal L_{\rm syn}
+\lambda_{\rm KD}\mathcal L_{\rm KD}.
\]

初始权重：

- 前5000步：\(\lambda_{\rm syn}=0\)；
- 5000–10000步：线性增加至0.02；
- 此后固定0.02；
- \(\lambda_{\rm KD}=0\)，默认不使用 teacher。

syndrome 损失不能区分正确码字和错误合法码字，也可能在不确定输入处梯度较弱，因此不作为主损失。

可选 teacher 使用独立 NMS-50：

\[
p_T=\sigma(-L_T/\tau),\quad
p_S=\sigma(-L_S/\tau),\quad \tau=2,
\]

\[
\mathcal L_{\rm KD}
=\tau^2\operatorname{KL}
(\operatorname{Bern}(p_T)\|
 \operatorname{Bern}(p_S)).
\]

拟设权重0.05，仅对 teacher 信息位全部正确的训练样本启用；无合格样本时该项为0。teacher 不反传，其计算时间单独统计。

---

**5）输出、接受判据与 fallback**

输出软值 \(L^{(t)}\)，硬判决：

\[
\hat c_v=\mathbf1[L_v<0].
\]

推理接受条件：

\[
A_t=
\mathbf1[
H\hat c^\top=0
\ \land\ \mathrm{CRC通过}
\ \land\ \mathrm{无未解析非filler位}
].
\]

本配置的载荷 \(A=1264\) 使用 TB CRC16；单码块无需额外 CB CRC。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

默认策略：

1. 每轮神经辅助后检查；
2. 20轮内通过则接受；
3. 未通过则关闭控制器，设 \(\eta=0\)；
4. 保留当前消息，继续 NMS 最多10轮；
5. 仍未通过则返回失败标记。

这叫 **warm continuation**。它与从信道 LLR 重启的 NMS-30 不同，必须分别命名。

统计：

\[
P_{\rm fb}
=\frac{N_{\rm enter\ fallback}}{N_{\rm frames}},
\]

\[
P_{\rm rescue}
=\frac{N_{\rm fallback且最终正确接受}}
{N_{\rm enter\ fallback}}.
\]

同时记录：

- fallback 后仍失败的比例；
- syndrome 通过但 CRC 失败的比例；
- CRC 通过却信息错误的比例；
- 平均额外迭代数；
- 神经阶段和 fallback 的总时间。

整体交付块错误率包含声明失败与错误接受；另外报告普通硬判决信息块 BLER，避免统计口径混淆。

\[
\mathbb E[t_{\rm total}]
=\mathbb E[t_{\rm neural}]
+P_{\rm fb}\mathbb E[t_{\rm fallback}\mid{\rm fb}].
\]

校验通过只证明满足对应约束，不能保证恢复了发送码字。模型没有“必然输出正确合法码字”的保证。

---

**6）速率匹配：恢复到完整图，保留观察类型**

由标准适配器产生映射：

\[
g:\{0,\ldots,E_{\rm tx}-1\}\rightarrow
\{0,\ldots,N-1\}.
\]

它必须已经包含逆交织、RV 起点、循环缓冲选择、首 \(2Z\) 固定打孔及 filler 跳过。上述操作是标准编码链路的一部分。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

输入恢复：

\[
L_v^{ch}
=\operatorname{clip}\left(
\sum_{j:g(j)=v}L_j^{rx},-20,20
\right),
\]

\[
\nu_v=\#\{j:g(j)=v\}.
\]

| 位置类型 | 输入 LLR | 标记 |
|---|---|---|
| 未发送／打孔 | 0 | \(\nu=0,F=0\) |
| 单次观察 | 接收 LLR | \(\nu=1,F=0\) |
| 重复观察 | 各次独立观察 LLR 累加后饱和 | \(\nu\ge2,F=0\) |
| 已知零 filler／缩短位 | \(+20\) | \(F=1\) |

不要用 `inf`；不要把 filler 与打孔混为一类。重复发送应产生独立噪声，不能复制同一个带噪 LLR。

训练和测试共用同一恢复函数、同一符号约定、同一掩码定义。默认训练 RV0、无重复；若测试 RV2、filler 或重复而训练未包含，必须明确标为分布外测试，不能直接宣称通用支持。

---

**7）FLOPs 与峰值显存：公式及数量级**

以下仅针对上面定义的自定义 SSM，**不能套给官方 Mamba-1/2**。

记：

\[
h=\mathrm{expand}\cdot d,\quad p=12,\quad c=8,\quad o=1.
\]

这里 \(p=8\)维统计＋4维基行嵌入。

按一次乘加计2 FLOPs，控制器每码字主项：

\[
F_{\rm ctrl}\approx
Tm_b
\left[
2pd+
J\left(
6dh+2h(h+2s)+2ch+8hs
\right)+2do
\right].
\]

对应于输入投影、门控投影、选择性参数投影、状态更新和输出投影。

在本实现账本中：

\[
F_{\rm NMS}\approx T(7E_g+N),
\]

\[
F_{\rm stats}\approx7TE_g,
\]

因此

\[
\boxed{
F_{\rm word}\approx
T(14E_g+N)+F_{\rm ctrl}
}.
\]

比较、异或、索引、饱和、CRC，以及 `exp/tanh/sigmoid` 单独统计，不强行折算为普通 FLOPs。激活函数调用量约为

\[
Tm_b\{J(3h+2s+hs)+o\}.
\]

上述还不含训练反向传播与损失计算。batch 成本为 \(B F_{\rm word}\)。

默认 \(T=20,J=1,d=h=16,s=4\)：

| \(Z\) | 完整图长度 \(N\) | 边数 \(E_g\) | 控制器主项 | NMS＋统计主项 | 合计/码字 |
|---:|---:|---:|---:|---:|---:|
| 128 | 6656 | 25216 | 2.930 MFLOPs | 7.194 MFLOPs | **10.124 MFLOPs** |
| 256 | 13312 | 50432 | 2.930 MFLOPs | 14.387 MFLOPs | **17.317 MFLOPs** |
| 384 | 19968 | 75648 | 2.930 MFLOPs | 21.581 MFLOPs | **24.511 MFLOPs** |

这些是预算脚本计算值。**状态小不等于额外计算免费**：统计和控制器必须尽可能复用 NMS 已读取的数据；时延收益仍需测量。

参数数目为

\[
\begin{aligned}
P_\theta={}&4m_b+pd+d\\
&+J(3dh+h^2+3hs+ch+2d+4h+2s)\\
&+d+do+o.
\end{aligned}
\]

默认共 **1857个参数**。

控制状态显存：

\[
M_{\rm state}=4Bm_bJhs
\]

字节，FP32 下每码字 **10.5 KiB**。

显存必须拆成张量账本和后端额外占用，不能给一个虚假的“精确峰值”。定义

\[
S=m_b[Jhs+p+J(5d+6h+2s)+o].
\]

一个显式缓存预算为

\[
M_{\rm infer,ledger}
=4B(5E_g+3N+S)
+B(4N+M)+8E_g+4P_\theta.
\]

训练每轮保存量按

\[
A_{\rm save}
=12E_g+6N+
m_b[p+J(hs+6d+8h+2s)]
\]

个浮点数规划：

\[
\begin{aligned}
M_{\rm train,ledger}\approx{}&
M_{\rm infer,ledger}
+4BT A_{\rm save}\\
&+BT(16M+2E_g+M)+12P_\theta.
\end{aligned}
\]

其中包含了消息、控制器激活、归约索引、掩码及 AdamW 状态的预算。实际峰值为

\[
\boxed{
M_{\rm peak}
=M_{\rm ledger}
+M_{\rm workspace}
+M_{\rm allocator}
+M_{\rm data}
}.
\]

后面三项及自动微分实际保存张量需要 profile，当前预算不是上界。

| 配置 | 推理张量预算 | 训练张量预算 |
|---|---:|---:|
| \(Z=128,B=1\) | 0.83 MiB | 0.030 GiB |
| \(Z=128,B=64\) | 40.5 MiB | **1.90 GiB** |
| \(Z=128,B=128\) | 80.8 MiB | **3.81 GiB** |
| \(Z=256,B=64\) | 78.3 MiB | **3.74 GiB** |
| \(Z=384,B=64\) | 116.1 MiB | **5.58 GiB** |

预算支持从 batch64 起步；24GB/32GB 上的实际峰值和后端兼容性仍待核实。

---

**8）在线数据、对称性与训练预算**

主训练配置：

- \(Z=96,128\)，不同 \(Z\) 的 batch 交替；
- 一个 batch 内固定 \(Z\)，不做跨长度 padding；
- \(A=10Z-16\)，TB CRC 后 \(K=10Z\)；
- \(E_{\rm tx}=2K\)，RV0；
- 首轮只做 AWGN。

BPSK 等效实信道：

\[
x_j=1-2c_j,\qquad y_j=x_j+n_j,
\]

\[
\sigma^2=
\frac1{2R_{\rm payload}10^{\gamma_{\rm dB}/10}},
\qquad
R_{\rm payload}=\frac A{E_{\rm tx}},
\]

\[
L_j^{rx}=\frac{2y_j}{\sigma^2}.
\]

按载荷码率归一化，不能训练用 \(A/E_{\rm tx}\)、画图时改用 \(K/E_{\rm tx}\)。

SNR 范围先通过经典基线确定：将 NMS-20 达到 BLER 约0.1的 SNR 记为 \(\gamma_Z\)。

| 阶段 | 迭代数 | 每码字独立采样的 SNR |
|---|---:|---|
| 0–5000步 | 10 | \(\gamma_Z+\mathcal U(0,1)\) dB |
| 5000–50000步 | 20 | \(\gamma_Z+\mathcal U(-1,1)\) dB |

这是拟采用课程，不预设绝对 SNR 数字。

**全零码字训练可以使用，但需满足以下条件：**

对任意有效码字 \(c\)，软译码映射应满足

\[
D((-1)^c\odot L)=(-1)^c\odot D(L).
\]

本设计通过以下方式保持：

- 控制输入采用绝对消息、残差幅度及符号不变的校验特征；
- 阻尼和缩放不依赖发送码字符号；
- filler 对所有有效码字均为零；
- 打孔零值不直接进入任意硬判决 syndrome 特征；
- 状态每个码字重置，不携带上一帧信息。

仍必须用随机非零有效码字验证输出等变性和 BLER。已运行的小型 QC 检查仅验证代数关系，不能替代完整 NR 检验。

训练初值：

- AdamW：峰值 LR \(10^{-3}\)，warmup1000步，cosine降至 \(10^{-4}\)；
- betas \((0.9,0.999)\)，eps \(10^{-8}\)；
- weight decay \(10^{-4}\)，bias、norm和衰减参数不衰减；
- 梯度范数裁剪1；
- FP32，无 dropout；
- 计划50000步，batch64，即320万次在线信道采样；
- 先完成一个种子，再扩至三个种子；
- 每1000步验证。

GPU 小时不能根据 FLOPs 猜。先预热50步，测300个含数据生成、前向、反向和优化器更新的完整步骤：

\[
H_{\rm train}
=\frac{5000\,t_{10}+45000\,t_{20}}{3600}.
\]

仅作预算换算：

| 实测加权平均秒/步 | 单种子50000步 | 三种子 |
|---:|---:|---:|
| 0.1 | 1.39小时 | 4.17小时 |
| 0.5 | 6.94小时 | 20.83小时 |
| 1.0 | 13.89小时 | 41.67小时 |

这些**不是4090或5090性能预测**，且不包含验证、teacher和最终低 BLER 测试。GPU 时长待实测。

---

**9）模块图、前向伪代码和初始化**

文字模块图：

```text
接收 LLR
   │
逆交织 / 速率恢复 ──→ 观察次数、filler mask
   │
完整图 Lch，[batch,52,Z]
   │
   ┌──────────────── 迭代 t ──────────────────┐
   │ U、旧C2V → QC对齐 → extrinsic Q          │
   │                  │                       │
   │        行级统计 + syndrome + mask        │
   │                  │                       │
   │    共享SSM控制器 ↔ 各基行独立状态         │
   │                  │ eta                   │
   │ Q → 精确MS更新 → 阻尼 → 新C2V → 回聚U    │
   └──────────────────────────────────────────┘
   │
完整 H 校验 + TB CRC
   ├─通过：接受输出
   └─20轮未通过：关闭控制器 → NMS续译最多10轮
```

前向伪代码：

```python
Lch, nu, filler = rate_recover(rx_llr, tx_to_full, config)
graph = graph_cache[(BG, Z)]

R = zeros(batch, 197, Z)
U = force_filler(Lch, +20)
state = zeros(batch, 42, J, h, s)

delta_R = zeros(batch, 42)
u_prev = masked_syndrome_rate(U)
active = ones(batch, bool)
supervised = []

for t in range(T_neural):
    Q = clip(gather(U, graph) - R, -20, 20)
    Q = force_filler_edges(Q, +20)

    f, cond, u_now = row_features(
        U, Q, R, delta_R, u_prev, nu, filler, t
    )
    eta, state_new = controller(
        f.detach(), cond.detach(), state
    )

    ms = check_update_min1_min2(Q, graph)
    Rnew = clip(
        (1 - eta[:, row]) * alpha * ms
        + eta[:, row] * R,
        -20, 20
    )
    Unew = force_filler(
        Lch + scatter(Rnew, graph), +20
    )
    delta_new = row_mean_abs(Rnew - R)

    # 训练：全部更新；推理：冻结已接受码块
    R, U, state = update_training_or_active(
        Rnew, Unew, state_new, R, U, state, active
    )
    delta_R, u_prev = update_active_statistics(
        delta_new, u_now, active
    )

    if training and t in last_four_iterations:
        supervised.append(clip(U, -20, 20))

    if not training:
        accepted = full_syndrome_crc_and_resolved(U)
        active &= ~accepted
        if not active.any():
            break

if training:
    return compute_loss(supervised, labels, graph)

entered_fallback = active.clone()
U, R, active, extra_iters = nms_continue(
    Lch=Lch, U=U, R=R,
    active=active, alpha=alpha,
    eta=0, max_additional=10
)
return hard(U), ~active, entered_fallback, extra_iters
```

固定形状 batch 仅通过 mask 冻结输出，仍可能执行全部算术。**不能把逻辑停止迭代数直接当作 GPU 节省。**batch1 或实际 active compaction 的耗时应分别测量。

超参初值：

| 项目 | 默认值 |
|---|---|
| schedule | flooding |
| 主迭代／额外 fallback | 20／10 |
| \(J,d,s,\mathrm{expand}\) | 1、16、4、1 |
| 基行嵌入 | 4维 |
| 时间卷积 | 不使用，等价 kernel=1 |
| \(\eta_{\max}\)、初始 \(\eta\) | 0.5、约0.05 |
| \(\Delta_{\min},\Delta_{\max},\Delta_0\) | 0.25、2、1 |
| 初始时间常数，单位为迭代 | 1、2、4、8 |
| LLR clip | 20 |
| batch | 64 |

初始化落实为：

\[
\lambda_k=1/\tau_k,\qquad
\theta_{i,k}
=\operatorname{logit}
\frac{\lambda_k-1/32}{2-1/32}.
\]

设 \(W_\Delta=V_\Delta=0\)，\(b_\Delta=\log(3/4)\)，得到初始 \(\Delta=1\)。

head权重采用标准差 \(10^{-3}\) 的小随机数，

\[
b_\eta=\log(1/9),
\]

得到初始阻尼约0.05。普通投影使用 Xavier，基行嵌入标准差0.02，norm scale和 \(D\) 初始化为1。

---

**10）消融钩子与不可混淆的边界**

| 钩子 | 实现方式 | 解释边界 |
|---|---|---|
| 重排 | natural-row／degree-bucket存储 | 保留原始row ID时应数值等价，主要比较执行成本 |
| 结构编码 | row embedding开关；逐行状态／全局池化状态 | 检验基行粒度是否必要 |
| 单／双向 | 默认单向；双向仅扫描已观察历史前缀 | 禁止访问未来迭代特征 |
| 状态维度 | \(s\in\{1,4,8,16\}\) | 同时报状态和参数量 |
| 条件化 | 无外部条件／\(\Delta\)-only／\(\Delta,B,C\)／FiLM | 一次只换一种 |
| syndrome | 同时关闭动态和条件中的 \(u,\Delta u\) | coverage可保留为可靠度特征 |
| SNR | 开／关，另测条件估计偏差 | 所有学习基线获得相同信息 |
| 损失 | BCE／＋syndrome／＋KD | 分开识别增益来源 |
| 梯度 | statistics detach／连续统计不断梯度 | 硬 syndrome本身仍不可导 |
| fallback | off／warm continuation／cold restart | 独立统计整体成本 |
| 记忆对照 | MLP、EMA、GRU、SSM | 相同输入与基行粒度 |

双向前缀版本需要每轮重扫已有历史，累计成本可能达到 \(O(T^2)\)，不属于默认方案。用完整20轮特征训练双向模型、再声称在线控制，是未来信息泄漏。

GRU 对照建议做两组：参数预算相近、附加状态预算相近。两者未必能同时匹配，不能仅用“相同 hidden size”宣布公平。

Mamba-1 与 Mamba-2 消融应真正替换模块，重新统计参数、卷积缓存、状态和时间。Mamba-2 的 SSD 计算结构不同，不能套用本答复预算，也不能引用其其他任务速度直接推导本任务速度。([arxiv.org](https://arxiv.org/abs/2405.21060))

以下均标记 **待核实**：PyTorch/CUDA/Triton具体版本，官方 Mamba-1/2 的 step接口、训练梯度支持、维度限制、编译支持和4090/5090后端兼容性。

当前已经完成的是规格、配置、资源算术和200组小型 QC 代数检查；**尚未完成完整 SSM 译码器训练、NR链路对拍或GPU基准。**首个实现里程碑应是“固定阻尼退化版本与参考 NMS 对拍”，通过后再打开选择性状态。

> 基于已敲定的架构，设计可直接执行的实验方案，要求基线公平、指标可测、数字可复现。
>
> # 1 码型与信道矩阵（符合TS 38.212）
> LDPC：BG2短码(K=512/1024)+BG1中长码(K=2048/4096/8448)，速率匹配到{1/3,1/2,2/3,3/4}；
> Polar：N=128/256/512(可选1024)+CRC{11,24}；
> 信道：AWGN为主，瑞利/TDL作泛化验证；BPSK/QPSK为主。
>
> # 2 基线（≥4个，传统与神经各半）
> 传统：SPA flooding、NMS/OMS layered（迭代数5/10/20/50分别报告）、CA-SCL(L=8/16/32)；
> 神经：ECCT或白盒ECCT、GNN/展开NMS至少一个；BP-OSD作为stretch。
> 公平性口径：参数量、训练数据量、训练步数、FLOPs分别对齐并说明；必须同时给出"同迭代数"和"同时延"两种对比，不能只挑对自己有利的口径。
>
> # 3 指标（三组）
> A 性能：BLER/BER–Eb/N0（下探到1e-4~1e-5）、目标BLER所需Eb/N0、错误平层区、平均迭代数、fallback触发率；
> B 复杂度：参数量、每码字FLOPs、峰值显存、训练GPU时；
> C 系统：GPU吞吐(codewords/s与Mbps)、单码字时延p50/p99、batch=1→256的时延—吞吐曲线、能耗J/codeword（说明NVML采样口径）。
>
> # 4 测量与统计方法学（写清每一步）
> Eb/N0与SNR换算必须含码率与调制阶数，给出公式并全篇统一；LLR符号约定统一；仿真链路先用公开文献曲线校验正确性；每个BLER点保证足够错误帧数（1e-4量级需1e6帧量级），说明帧数与置信区间；warmup+CUDA同步+是否含数据搬运；重复次数与随机种子。
>
> # 5 消融（按性价比排序，标必做/可选）
> 序列重排（原始 vs 结构感知 vs 随机）；单向vs双向；d_state与层数；syndrome条件化开关；损失项开关；Mamba-1 vs Mamba-2；比特轴vs迭代轴；fallback开关；精度（FP32/BF16/INT8）。
>
> # 6 泛化实验（这是差异化证据，必做）
> 训练单一Z/K → 测试其他Z/K；训练单一码率 → 测试其他码率；训练SNR区间外测试；AWGN训练→衰落测试。逐项报告掉点幅度。
>
> # 7 量纲自检（强制）
> 用FLOPs公式粗估吞吐上限，再与实测对照；任何超出量纲估算的数字必须解释。禁止无依据的加速倍数，禁止与FPGA/ASIC做不同口径对比。
>
> # 8 里程碑与止损
> 按周计划（数据管线→基线对齐→主模型→消融→泛化→硬件实测→写作）+每项GPU时；第几周中期检查；出现什么信号（打不过NMS/泛化崩/时延无优势）就切Plan B；Plan B必须仍能产出4–6页论文（如降级为"结构注入方式对神经译码器影响的系统性实证研究"）。
>
> # 9 图表清单
> 4–6页只放5张图表，逐张说明证明什么、回应哪条质疑。

<details><summary>29 previous messages</summary>

> 我会先把这批码长、码率和 Polar CRC 组合映射到合法的 NR 配置，再分成论文必做矩阵和扩展矩阵，避免一次铺开超出单卡预算。基线、低 BLER 统计、GPU 计时和能耗测量都会落实到可记录的字段与停止条件。
>
> <details><summary>Explored 7 files, 2 searches</summary>
>
> - Searched for `LDPC|Mamba|SSM|神经译码|GPU|实验` in `MEMORY.md`
> - Read `./config.json`
> - Searched for `##|FLOP|state|fallback|budget|参数` in `README.md`
> - Read `~/.codex/skills/communication-skills/coding/ldpc/references.md`
> - Read `~/.codex/skills/communication-skills/coding/ldpc/SKILL.md`
> - Read `~/.codex/skills/communication-skills/coding/polar/SKILL.md`
> - Read `~/.codex/skills/communication-skills/coding/polar/references.md`
> - Read `~/.codex/skills/communication-skills/acceleration/gpu-profiling/SKILL.md`
> - Read `~/.codex/skills/communication-skills/acceleration/gpu-profiling/references.md`
>
> </details>
>
> 我会补用 Polar 与 GPU profiling 技能核对标准和测量口径。这里有两处需要调整：\(K=512/1024\) 未必等于 \(10Z\)；而 BG1、\(K\approx2048\) 在部分目标码率下不符合 NR 基图选择规则。实验清单会显式记录载荷、CRC、filler 和实际码率，并按标准选择 BG。
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `site.docs.nvidia.com "nvmlDeviceGetPowerUsage" "1 second"`
>
> Searched the web for `https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html`
>
> Searched the web for `https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html`
>
> Searched the web for `https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html`
>
> </details>
>
> 标准核对后，两个边界已明确：短块在目标码率 \(3/4\) 时通常需要切到 BG1，不能把 BG2 强制结果记作 NR 合规配置；CRC11 和 CRC24C 也分别对应不同的 Polar 使用场景。它们会分组测试，CA-SCL 用作 Polar 校验基线，不与 LDPC 主模型直接比输赢。
>
> <details><summary>Explored a file, a list, ran a command</summary>
>
> <details><summary>Explored a file, a list</summary>
>
> - Read `./budget_and_invariants.py`
> - Listed files in `03-仿真与实验`
>
> </details>
>
> - Ran `python3 - <<'PY'
> import urllib.request,csv,io,hashlib
> u='https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/ldpc/codes/5G_bg1.csv'
> b=urllib.request.urlopen(u,timeout=25).read()
> a=list(csv.reader(io.StringIO(b.decode()),delimiter=';'))
> print('BG1 nonzero blocks',len(a)-2,'table_sha256',hashlib.sha256(b).hexdigest())
> PY`
>
> </details>
>
> Context compaction
>
> Source: automatic
> Status: completed
>
> 我会把方案落成配置清单、统计口径和分周预算，并生成可运行的参数校验脚本。主线固定为 QC 行级迭代轴 SSM；Polar 单列为链路校验实验，不与 LDPC 混在一张性能排名里。
>
> <details><summary>Ran a command, searched the web</summary>
>
> - Ran `pwd && rg --files '03-仿真与实验/信道编译码/S2-QC行级SSM实现规格'`
>
> Searched the web for `site.etsi.org 138212 18.5.0 base graph 3824 0.67 292`
>
> </details>
>
> <details><summary>Explored 3 files</summary>
>
> - Read `~/.codex/skills/communication-skills/acceleration/gpu-profiling/SKILL.md`
> - Read `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/budget_and_invariants.py`
> - Read `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/config.json`
>
> </details>
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html`
>
> Searched the web for `site.nvlabs.github.io/sionna "5G Channel Coding" "Polar"`
>
> </details>
>
> 公平比较需要分开两条口径：同迭代数主比 S2* 与 flooding NMS；与 layered NMS/OMS 的效率比较则按实测时延。参数量、训练数据量和 FLOPs 也会分别设对照，避免声称这些预算能同时对齐。
>
> <details><summary>Created 2 files, searched the web</summary>
>
> Searched the web for `https://nvlabs.github.io/sionna/v2.1.0/phy/tutorials/notebooks/5G_Channel_Coding_Polar_vs_LDPC_Codes.html`
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/generate_manifest.py` (+269 -0)
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/protocol_checks.py` (+72 -0)
>
> </details>
>
> Stream error
>
> Reconnecting 1/5
> stream disconnected before completion: Transport error: network error: error decoding response body
>
> <details><summary>Created 2 files, edited a file</summary>
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/README.md` (+389 -0)
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/generate_manifest.py` (+1 -1)
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/results_template.json` (+58 -0)
>
> </details>
>
> 参数清单已生成，几处标准边界会明确标出：短块在 3/4 码率下需切换到 BG1，不能算作“同一 BG 的跨码率泛化”；BG1 的完整 Tanner 图有 68Z 个变量节点，首 2Z 打孔后的循环缓冲区才是 66Z。低误码区采用独立预跑后冻结帧数的方案，每点同时给置信区间。
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `python3 generate_manifest.py`
> - Ran `python3 protocol_checks.py`
> - Ran `python3 - <<'PY'
> from urllib.request import urlopen
> from pathlib import Path
> url='https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf'
> p=Path('/tmp/s2-ts138212v180500.pdf')
> if not p.exists():
>     p.write_bytes(urlopen(url,timeout=45).read())
> print('standard_pdf',p,len(p.read_bytes()))
> urls=[('nvml','https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html'),('sionna','https://nvlabs.github.io/sionna/v2.1.0/phy/tutorials/notebooks/5G_Channel_Coding_Polar_vs_LDPC_Codes.html')]
> for name,u in urls:
>     try:
>         response=urlopen(u,timeout=30)
>         txt=response.read().decode('utf-8','replace')
>         Path('/tmp/s2-'+name+'.html').write_text(txt)
>         print(name,response.status,len(txt),response.url)
>     except Exception as exc:
>         print(name,type(exc).__name__,str(exc))
> PY`
>
> </details>
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `python3 - <<'PY'
> import generate_manifest as g
> for bg,z in [(2,104),(1,192),(1,384)]:
>     x=g.resources(bg,z,64)
>     print(bg,z,x['parameters'],round(x['training_planning_bytes']/2**30,3),round(x['inference_planning_bytes']/2**20,3))
> PY`
> - Ran `python3 - <<'PY'
> from urllib.request import Request, urlopen
> from pathlib import Path
> urls=[('standard','https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf'),('nvml','https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html'),('sionna','https://nvlabs.github.io/sionna/v2.1.0/phy/tutorials/notebooks/5G_Channel_Coding_Polar_vs_LDPC_Codes.html'),('standardzip','https://www.3gpp.org/ftp/Specs/archive/38_series/38.212/38212-i50.zip')]
> for name,url in urls:
>     try:
>         response=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20)
>         raw=response.read()
>         ext='pdf' if name=='standard' else 'zip' if name=='standardzip' else 'html'
>         p=Path('/tmp/s2-'+name+'.'+ext)
>         p.write_bytes(raw)
>         print(name,response.status,len(raw),response.url,p)
>     except Exception as exc:
>         print(name,type(exc).__name__,str(exc))
> PY`
>
> </details>
>
> <details><summary>Explored a search, ran a command</summary>
>
> <details><summary>Explored a search</summary>
>
> - Searched for `时间|20|time|特征|clip|CRC|loss|teacher` in `README.md`
>
> </details>
>
> - Ran `python3 -m py_compile generate_manifest.py protocol_checks.py`
>
> </details>
>
> <details><summary>Explored a search, ran 2 commands</summary>
>
> - Ran `pdftotext -layout /tmp/s2-standard.pdf /tmp/s2-standard.txt`
>
> <details><summary>Explored a search</summary>
>
> - Searched for `3824|0.67|292|1088|1013|640|560|192|one second` in `s2-standard.txt`
>
> </details>
>
> - Ran `python3 - <<'PY'
> from html.parser import HTMLParser
> from pathlib import Path
> class Text(HTMLParser):
>     def __init__(self): super().__init__(); self.items=[]
>     def handle_data(self,d):
>         if d.strip(): self.items.append(d.strip())
> for name in ['nvml','sionna']:
>     p=Text(); p.feed(Path('/tmp/s2-'+name+'.html').read_text())
>     Path('/tmp/s2-'+name+'.txt').write_text('\n'.join(p.items))
>     print(name,'text extracted')
> PY`
>
> </details>
>
> <details><summary>Explored a file, 2 searches, searched the web</summary>
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> <details><summary>Explored a file, 2 searches</summary>
>
> - Read `/tmp/s2-standard.txt`
> - Searched for `second|Ampere|TotalEnergyConsumption|GetPowerUsage` in `s2-nvml.txt`
> - Searched for `num_iter|list_size|k =|n =|ebno|Eb/N0|50|k=|n=` in `s2-sionna.txt`
>
> </details>
>
> </details>
>
> 消融里还有两个需要收紧的地方：迭代轴的双向模型会接触未来迭代信息，只能作为另计完整成本的离线方案；存储顺序随机置换若同步保留图和行标识，输出应保持不变，主要测试的是访存。算法层面的结构消融会另做“真实 QC 行分组 vs 随机边分组”，两者不混用。
>
> <details><summary>Explored a search</summary>
>
> - Searched for `旧 train|5 次验证|payload BCE|135.8|合计|checkpoint_selection` in `README.md`
>
> </details>
>
> <details><summary>Edited 2 files</summary>
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/README.md` (+12 -12)
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/generate_manifest.py` (+1 -1)
>
> </details>
>
> <details><summary>Edited 2 files, ran a command</summary>
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/README.md` (+4 -2)
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/protocol_checks.py` (+7 -0)
> - Ran `python3 - <<'PY'
> from pathlib import Path
> from hashlib import sha256
> import json
> import generate_manifest as g
> import protocol_checks as p
> root=Path.cwd()
> m=g.build(); print(g.validate(m))
> manifest=json.dumps(m,ensure_ascii=False,indent=2)+'\n'
> (root/'experiment_manifest.json').write_text(manifest)
> print(json.dumps(p.self_check(),ensure_ascii=False))
> print('deterministic_manifest:',manifest==json.dumps(g.build(),ensure_ascii=False,indent=2)+'\n')
> for filename in ['experiment_manifest.json','results_template.json']:
>     json.loads((root/filename).read_text())
>     print('JSON parsed:',filename)
> records=[]
> for name,file,url in [('TS38.212','/tmp/s2-standard.pdf',m['sources']['standard']),('NVML','/tmp/s2-nvml.html',m['sources']['NVML']),('Sionna notebook','/tmp/s2-sionna.html',m['sources']['sionna_validation'])]:
>     raw=Path(file).read_bytes()
>     records.append({'name':name,'url':url,'retrieved_date':'2026-11-12','bytes':len(raw),'sha256':sha256(raw).hexdigest(),'scope':'source_read_only_not_local_decoder_validation'})
> (root/'source_verification.json').write_text(json.dumps({'status':'external_sources_read_no_experiment_results','sources':records},ensure_ascii=False,indent=2)+'\n')
> for x in ['README.md','generate_manifest.py','protocol_checks.py','experiment_manifest.json','results_template.json','source_verification.json']:
>     f=root/x
>     print(x, f.stat().st_size, sha256(f.read_bytes()).hexdigest()[:16])
> PY`
>
> </details>
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/README.md` (+1 -1)
>
> Tool call
>
> Tool: open_in_codex
> Status: completed
>
> </details>
>
> 配置和统计校验已通过：20 个 LDPC、7 个 Polar 标量配置，以及噪声换算、BLER 插值和置信区间检查。深测预算也已算清：两个主配置、三个译码器、各两个 1e-5 附近点，共需至少 2.4 亿次码字译码。400 GPU 小时是计划上限，需用第二周测得的速度重算；目前没有训练或 GPU 性能结果。
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/README.md` (+1 -1)
>
> </details>
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://arxiv.org/abs/2207.14742`
>
> Searched the web for `https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf`
>
> Searched the web for `https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm`
>
> </details>
</details>

**建议按“两套主训练配置、四个主基线、分层低误码测试”执行。**重点验证迭代记忆的收益，GPU结果决定是否保留时延优势主张。

已保存为：

- [完整实验协议](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/README.md>)
- [实验配置清单](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/experiment_manifest.json>)
- [配置生成脚本](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/generate_manifest.py>)、[统计校验脚本](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/protocol_checks.py>)
- [结果字段模板](<./03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/results_template.json>)

**已运行通过配置、能量换算和统计校验；完整NR链路、训练和GPU测试尚未运行。**所有库版本、目标卡接口及后端支持均标记为“待核实”。

**1．码型矩阵：先统一“K”的含义**

将你给出的512/1024等统一解释为 **\(B\)：含TB CRC、不含filler的输入长度**。另外记录：

\[
A=\text{载荷长度},\quad K_{\rm enc}=10Z\text{或}22Z,\quad
F=K_{\rm enc}-B.
\]

按标准基图选择规则计算，得到下表；原先指定的“BG1、2048低码率”和“BG2短块、3/4”需要调整。([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

| 请求的 \(K\)，本方案记为 \(B\) | 载荷 \(A\) | 码率1/3、1/2、2/3：BG/Z/\(K_{\rm enc}\)/F | 码率3/4 |
|---:|---:|---|---|
|512|496|BG2 / 64 / 640 / 128|BG1 / 24 / 528 / 16|
|1024|1008|BG2 / 104 / 1040 / 16|BG1 / 48 / 1056 / 32|
|2048|2032|BG2 / 208 / 2080 / 32|BG1 / 96 / 2112 / 64|
|4096|4072|BG1 / 192 / 4224 / 128|同左|
|8448|8424|BG1 / 384 / 8448 / 0|同左|

固定单TB、单CB、RV0、完整循环缓冲区、QPSK。发送长度：

\[
E_{\rm tx}=2\left\lceil\frac{B}{2R_{\rm target}}\right\rceil .
\]

同时保存标称码率、实际 \(B/E_{\rm tx}\)、实际载荷率 \(A/E_{\rm tx}\)。这是**TS 38.212编码内核实验**，不额外宣称TBS/MCS和资源分配完整合规。

训练两份独立模型：

| 模型 | 唯一训练配置 | 主用途 |
|---|---|---|
|A|BG2，\(B=1024,Z=104,R=1/2\)，AWGN|短码主结果、跨Z/码率/信道|
|B|BG1，\(B=4096,Z=192,R=1/2\)，AWGN|中长码验证、\(B=8448\)外推|

**不把BG2→BG1算作零样本泛化。**

测试分三层：

- **全矩阵筛查**：20个LDPC配置，覆盖约 \(10^{-2}\) 至 \(10^{-3}\)。
- **完整主对照**：两个训练配置，全部主基线，深入 \(10^{-4}\)。
- **深测**：两个主配置，各两个 \(10^{-5}\) 附近点，仅保留S2、验证集选定的最强传统方法、展开NMS。

最后一层已经需要：

\[
2\times2\times3\times20\,000\,000
=2.4\times10^8
\]

次码字译码，不能将所有配置、基线和迭代数全部铺到 \(10^{-5}\)。

Polar单列为CA-SCL链路校验，CRC分场景配置，保留列表和真实CRC检查：([etsi.org](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf))

| 场景 | CRC | \((A,E_{\rm tx},N)\) |
|---|---|---|
|PDCCH|CRC24C|固定RNTI；(40,108,128)、(80,216,256)、(128,432,512)|
|UCI/PUCCH|CRC11|(53,128,128)、(117,256,256)、(245,512,512)|
|UCI，可选|CRC11|(501,1024,1024)|

每组测CA-SCL \(L=8/16/32\)。**S2没有Polar版本，因此不与CA-SCL跨码型排名。**

信道安排：AWGN主实验，**相干逐符号Rayleigh泛化必做**；TDL完整OFDM链路可选。QPSK主测，BPSK用于能量与LLR一致性检查。

**2．基线与公平性：分四条对照，不能同时“全部对齐”**

| 方法 | 定位 | 迭代/深度 |
|---|---|---|
|SPA flooding|主传统基线1|5/10/20/50|
|NMS layered|主传统基线2|5/10/20/50|
|展开NMS flooding|主神经基线1|主训练T=20|
|GNN decoder|主神经基线2|原生配置及预算匹配配置|
|NMS flooding|强制直接对照|与S2共用NMS更新核心|
|OMS layered|强制强传统对照|5/10/20/50|
|ECCT/白盒ECCT|强制短码专轨|按深度/FLOPs/时延比较|
|EMA、MLP、GRU控制器|核心消融|与S2相同输入和图更新|
|BP-OSD|stretch|不占必做预算|

GNN和ECCT从可核实的作者方法开始，适配NR后明确标为adapter；不直接声称复现原论文数字。([arxiv.org](https://arxiv.org/abs/2207.14742))

四条公平轨分别报告：

| 轨道 | 固定什么 | 允许变化什么 |
|---|---|---|
|数据/训练预算，主轨|相同观测、有效batch64、50k步、三种子|模型结构|
|参数预算|神经参数尽量匹配，目标±10%|宽度/层数；另保留原生强配置|
|算术预算|统一MAC=2，FLOPs目标±10%|迭代数/深度；特殊函数和访存另列|
|实际时延，主轨|同卡、同精度、相同完整调用范围|验证集选择迭代数/早停策略|

经典方法不做参数量匹配。离散宽度或轮数无法满足±10%时，报告真实差距，不填充无用参数或计算。

具体执行：

- **同迭代数主结论**：S2 vs NMS-F vs 展开NMS-F，T=20，关闭早停和fallback。
- **同时延主结论**：验证集生成BLER–p50/p99 Pareto曲线，在共同预算内选择策略，冻结后测试；同时报告超时率。
- layered与flooding完整扫图一次都记一轮，但明确更新依赖不同。
- ECCT的层数不叫BP迭代数。
- 神经T=5/10可作为T20模型的前缀诊断；T=50明确属于迭代外推，不能混成专门训练结果。

NMS参数搜索建议 \(\alpha=0.60:0.05:1.00\)，OMS搜索 \(\beta=0:0.1:1.0\)。各schedule与迭代上限独立校准，候选使用相同验证样本。**零样本测试的S2不得在目标配置重调alpha、归一化或停止阈值。**

ECCT限定共同短码配置 \(B=512,R=1/2\)，单列5k步×64观测的预算轨；S2/GNN/展开NMS也按该预算重训。若OOM，记录N/A与原因，不当作BLER优势。

训练默认采用已定SSM：\(J=1,d=16,s=4,\mathrm{expand}=1\)，T20、FP32，阻尼可学、alpha冻结。50k步、有效batch64、种子17/29/43；AdamW，峰值LR \(10^{-3}\)，warmup1000步，衰减至 \(10^{-4}\)，梯度范数裁剪1。teacher关闭，syndrome损失按原定义warmup至0.02。

**3．三组指标及其分母**

| 组别 | 必报内容 |
|---|---|
|性能|payload BLER/BER、目标BLER门限、平均/尾部迭代数、fallback触发率、最终拒绝率、错误接受率|
|复杂度|参数量、每码字算术量及特殊操作、实际图边数、峰值allocated/reserved显存、训练及调参GPU时|
|系统|cw/s、payload Mbps、batch1 p50/p99、batch1–256曲线、J/codeword|

统一：

\[
\mathrm{BLER}
=\frac{\#\{\text{任一载荷bit错误的帧}\}}{N_{\rm frames}},
\qquad
\mathrm{BER}
=\frac{N_{\rm payload\ bit\ errors}}{A\,N_{\rm frames}}.
\]

拒绝帧不丢弃。另报上层服务失败率：

\[
\mathrm{service\ FER}
=P(\text{载荷错误}\ \lor\ \text{最终拒绝}).
\]

fallback采用神经20轮后warm continuation NMS额外最多10轮，加入**NMS30**预算对照：

\[
p_{\rm fb}=\frac{N_{\rm trigger}}{N_{\rm all}},\qquad
p_{\rm residual}=\frac{N_{\rm final\ reject}}{N_{\rm all}}.
\]

同时报告neural-only与含fallback整体结果，不能仅统计接受的帧。CRC和syndrome通过也可能错误接受，仿真中必须用真实载荷统计。

**4．测量与统计步骤**

统一能量定义：\(E_b\)按**载荷A**计，\(Q_m=\log_2M\)，\(R=A/E_{\rm tx}\)，\(E_s=1\)：

\[
\frac{E_s}{N_0}=RQ_m\frac{E_b}{N_0},
\]

\[
(E_s/N_0)_{\rm dB}
=(E_b/N_0)_{\rm dB}+10\log_{10}(RQ_m).
\]

QPSK复噪声 \(w\sim\mathcal{CN}(0,N_0)\)，每实维方差 \(N_0/2\)。统一：

\[
L=\log\frac{P(b=0|y)}{P(b=1|y)},\quad
\hat b=\mathbf1[L<0],\quad
\text{BCE logit}=-L.
\]

打孔LLR置0；filler固定已知零并加mask；重复先累加再clip。所有方法共用rate-recovery索引。

执行顺序：

1. **参数和代数检查**：BG/Z/filler/CRC/交织索引；随机码字检查 \(Hc=0\)。
2. **独立实现对拍**：至少100组码字、发送索引和恢复LLR；明确参考库LLR符号。
3. **无噪声检查**：全部配置通过；完整SSM再检查符号对称性。
4. **公开曲线复跑**：先复刻公开Sionna coding notebook的原参数及能量定义，再切本文参数。它提供可追溯的公开参考入口，实际复跑仍待完成。([nvlabs.github.io](https://nvlabs.github.io/sionna/v2.1.0/phy/tutorials/notebooks/5G_Channel_Coding_Polar_vs_LDPC_Codes.html))
5. **独立pilot冻结正式SNR与帧数**，随后正式测试不再调方法。

训练SNR由pilot决定：寻找NMS-F20在BLER \(10^{-2}\)的门限 \(\gamma_{\rm ref}\)，训练均匀采样

\[
[\gamma_{\rm ref}-1.5,\ \gamma_{\rm ref}+1.0]\ \mathrm{dB}.
\]

正式测试通常0.25dB间隔，交点附近0.1dB；不预填未经测量的瀑布区位置。

帧数安排：

| BLER量级 | 固定帧数/点 | 预期错误帧 |
|---:|---:|---:|
|\(10^{-2}\)|20k|200|
|\(10^{-3}\)|200k|200|
|\(10^{-4}\)|2M|200|
|\(10^{-5}\)|20M|200|

采用Wilson双侧95%区间；零错误给单侧精确上界，不能画成BLER=0。Wilson与二项精确区间的统计口径参照NIST。([itl.nist.gov](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm))

脚本已验证：

- 2M帧、200错误：BLER \(10^{-4}\)，95%区间约 \([8.707\times10^{-5},1.149\times10^{-4}]\)。
- 1M帧、零错误：单侧95%上界约 \(2.996\times10^{-6}\)。

BER区间按帧或shard bootstrap，避免将一帧内bit当作独立样本。所有方法共用码字、噪声、衰落；分32个固定shard保存。三种训练seed共享测试集时，不合并成独立的3N帧。

目标门限只在相邻有效点间对 \(\log_{10}\mathrm{BLER}\)插值；未包围目标就报N/A。测到 \(10^{-5}\)仍不能证明不存在更低区域的error floor。

GPU操作顺序固定为：

- 同一卡、精度和功率设置，预分配buffer，warmup至少200次。
- **device-only event时间**、**device-resident完整调用wall时间**、**含H2D/D2H的wall时间**分别测。
- 包含rate recovery、特征、SSM、译码、syndrome/CRC、compaction和fallback；CPU执行的检查必须进入wall时间。
- batch1每轮10k次独立调用，共5轮，保留逐调用时间；在低/瀑布/高三个SNR测试。
- batch取1/2/4/8/16/32/64/128/256；每点持续至少1s、5轮。
- 采用明确的CUDA同步边界，避免异步执行造成低估；实际API和后端支持待核实。([docs.pytorch.org](https://docs.pytorch.org/docs/2.15/notes/cuda.html))

吞吐统一：

\[
Q=\frac{N_{\rm completed}}{t},\qquad
\mathrm{Mbps}=\frac{AQ}{10^6}.
\]

batch时间除batch只能叫摊销成本，不能叫单码字响应时延。

NVML采用30s稳态窗口、5轮：

\[
E_{\rm gross/cw}=\frac{\int P(t)\,dt}{N_{\rm completed}}.
\]

总能量计数可用时读取首尾差，否则对功率时间戳积分；gross为主、扣空闲功耗为辅。NVML文档说明部分架构返回约1秒平均功率，因此100ms轮询不等于100ms独立测量；目标卡支持和传感器窗口**待核实**。([docs.nvidia.com](https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html))

**5．消融按性价比排序**

| 顺序 | 实验 | 要求 |
|---:|---|---|
|1|NMS→静态阻尼/EMA/MLP/GRU/SSM|必做，判断是否需要SSM参数化|
|2|syndrome条件×syndrome损失，2×2|必做，分离输入信息和辅助监督|
|3|fallback开/关，加NMS30|必做，排除额外轮数贡献|
|4|真实QC行分组/随机边分组/全局池化|必做，检验结构注入|
|5|原始/QC row-major/随机存储顺序|必做低成本检查与系统测量|
|6|\(d_{\rm state}=2/4/8\)，层数1/2|必做小网格，先单seed筛查|
|7|FP32/BF16|可选，需重新验证误码稳定性|
|8|比特轴/迭代轴|可选，同数据及参数预算，另比FLOPs/时间|
|9|单向/双向|在线固定单向；双向仅作离线额外流程|
|10|Mamba-1/Mamba-2|可选，独立适配与预算匹配|
|11|INT8|最后做，额外计QAT/校准成本|

两个边界必须写清：

- 同步置换H索引、行标识和embedding的**存储重排**应保持算法输出不变；结构贡献要用“改变控制器分组”检验。
- 迭代轴双向不能读取未来迭代。两遍离线方法可以研究，但完整轨迹生成和第二遍译码都要计时。

当前自定义SSM也不能直接标为官方Mamba-1或Mamba-2；相关内核支持均待核实。

**6．泛化：逐项报告损失，不能直接相减不同码的门限**

| 泛化轴 | 必做目标 |
|---|---|
|跨Z/K，BG2|1024/Z104→512/Z64、2048/Z208，固定1/2|
|跨Z/K，BG1|4096/Z192→8448/Z384，固定1/2|
|跨码率，BG2|1024：1/2→1/3、2/3|
|跨码率，BG1|4096：1/2→1/3、2/3、3/4|
|SNR区间外|训练下界再低1dB、上界再高1dB及冻结网格|
|AWGN→Rayleigh|同码型、码率、相干解调和CSI口径|

BG2的104→208同属lifting family；104→64另提供跨family证据。短块3/4切BG，不放进纯跨码率结论。

选六个代表目标训练同预算specialist：跨长度两个、跨码率两个、Rayleigh一个、宽SNR一个。定义：

\[
D(c)=\gamma_{\rm zero\text{-}shot}(c)
-\gamma_{\rm specialist}(c),
\quad \mathrm{BLER}=10^{-3}.
\]

这才是同一目标条件下的泛化掉点。其余配置报告相对target-tuned NMS的增益及增益损失，并另给source-fixed NMS，区分参数迁移与目标调参。

全部目标测试锁定SSM权重、源alpha、归一化和停止阈值；未包围门限时报告固定SNR的BLER比值与CI。

**7．量纲自检：先列账本，再与实测解释**

沿用已定架构，令基行数 \(R_b\)、边数 \(E_g\)、\(h=\mathrm{expand}\,d\)，默认 \(p=12,c=8,o=1\)：

\[
F_{\rm ctrl}\approx TR_b
\left\{2pd+
J[6dh+2h(h+2s)+2ch+8hs]+2do\right\},
\]

\[
F_{\rm NMS+stats}\approx T(14E_g+N_{\rm graph}).
\]

这是算术规划量；比较、XOR、exp、索引和CRC另列。

| 配置，T20 | 近似MFLOPs/码字 | 参数 | batch64训练张量账本 |
|---|---:|---:|---:|
|BG2 Z104|8.775|1857|1.559 GiB|
|BG1 Z192|20.458|1873|4.325 GiB|
|BG1 Z384|37.708|1873|8.580 GiB|

显存列是**规划账本**，实际workspace与自动微分保存量必须测。

使用同设备、同精度校准的算力和带宽：

\[
Q\lesssim\min\left(\frac{P_{\rm eff}}F,
\frac{\mathrm{BW}_{\rm eff}}{D_{\rm actual}}\right).
\]

仅作演算：假设50TFLOP/s、1TB/s，BG2 Z104未融合访问账本约7.42MB/码字，对应带宽项约134.7k cw/s，即**135.8Mbps载荷吞吐**。这不是显卡测速或预测。

超过访问账本估计时，检查融合和缓存是否降低实际DRAM流量；超过算术估计时，检查漏算、精度、同步及分母。所有加速倍数来自成对实测，不与FPGA/ASIC做不同范围比较。

**8．十周计划与止损**

以下为**400 GPU小时的分配上限**；第二周用实测秒/step和cw/s重算。

| 周 | 交付 | GPU小时上限 |
|---:|---|---:|
|1|标准参数、CRC、索引、位级与无噪声检查|6|
|2|公开曲线、传统基线、速度预跑|24|
|3|两主配置模型与神经基线首轮|45|
|4|三seed、EMA/MLP/GRU对照，首次止损|45|
|5|必做消融、短码ECCT|45|
|6|全矩阵泛化、六个specialist|65|
|7|时延、吞吐、显存、能耗|20|
|8|固定帧数低BLER正式测试|120|
|9|五张图表、论文与Plan B整合|10|
|10|锁环境复跑、归档、修改|20|

时间预算使用：

\[
H_{\rm train}=\frac{\sum S_i t_{{\rm step},i}}{3600},
\qquad
H_{\rm test}=\frac{\sum N_i/Q_i}{3600}.
\]

失败调参、验证、teacher另计；CPU CA-SCL另记core-hours。

预设管理门限，均不代表预期增益：

- **第4周**：三seed均不能支持同轮改善，或EMA/GRU已解释全部收益，停止增加SSM复杂度。参考决策线为 \(10^{-3}\)处约0.1dB或同BLER时间约10%的改善。
- **第6周**：代表目标specialist gap超过约0.3dB，或多数目标丢失对NMS增益，删除强零样本主张；多配置重训必须重新标注训练覆盖范围。
- **第7周**：完整CRC/fallback流程下p50/p99无可信优势，删除GPU加速主张。

Plan B题目可收敛为：

**《QC行级历史状态与条件化对NR神经NMS译码的影响：公平预算下的实证研究》**

保留结构分组、EMA/GRU/SSM、跨配置边界和完整硬件代价。它需要可复现的机制或失效边界，不能仅把无差异结果换标题。TDL、INT8、Mamba-2、Polar神经增强、BP-OSD优先让位于主实验和统计有效性。

**9．论文只放五张图表**

| 图表 | 内容 | 回应的质疑 |
|---|---|---|
|表1|主基线与EMA/GRU/SSM的参数、训练预算、FLOPs、门限|只是增加参数或训练量；任意RNN都一样|
|图1|两个主配置BLER曲线、CI、低误码inset|没有强传统对照；深误码区无证据|
|图2|同时延/同BLER Pareto，附fallback率|额外迭代换性能；只挑有利口径|
|图3|泛化损失及核心结构/条件消融heatmap|只记住单一码；贡献来自额外输入|
|图4|batch曲线、batch1 p50/p99、能耗与显存|FLOPs代替测速；大batch掩盖尾时延|

完整BER、所有迭代点、原始shard、逐调用时间、功率日志和配置hash进仓库。

现在可直接先运行配置与统计脚本，再完成两个主配置的位级对拍；通过后做500步训练和译码速度预跑，据此确定400小时预算能覆盖的正式测试规模。