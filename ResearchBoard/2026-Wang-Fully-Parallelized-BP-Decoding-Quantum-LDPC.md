---
type: literature
title: "Fully Parallelized BP Decoding for Quantum LDPC Codes Can Outperform BP-OSD"
authors:
  - "Ming Wang"
  - "Ang Li"
  - "Frank Mueller"
year: 2026
venue: "IEEE International Symposium on High-Performance Computer Architecture (HPCA) 2026; arXiv preprint"
doi: "10.48550/arXiv.2507.00254"
url: "http://arxiv.org/abs/2507.00254"
zotero-key: "8VW2PY6E"
zotero-attachment-key: "94TG4URT"
evidence: primary
tags:
  - topic/qldpc
  - domain/quantum-error-correction
  - process/decoding
  - process/parallelism
  - metric/logical-error-rate
status: read
---

# Research Problem

[Direct factual extraction] 论文研究如何在 QLDPC 译码中保留 BP 的低复杂度和并行性，同时处理 BP 因 degeneracy、trapping sets 和 oscillating bits 而 non-converge 的问题。目标是用 syndrome-flip speculative post-processing 接近或超过 BP-OSD 的 logical error rate，并降低 latency。

# Motivation

[Authors' Claims] 作者认为 BP-OSD 的 Gaussian elimination 带来高计算开销，而 qLDPC 的 BP failures 往往集中在少数 oscillating bits。若围绕这些 bits 生成多个独立尝试，就可以在硬件友好的并行执行下逃离 BP 的局部停滞（pp. 1-2, 5）。

[My Interpretation] 这是把“后处理”从矩阵消元转换成并行的多次短 BP；它牺牲了候选尝试数量，却可能降低关键路径延迟。

# System Model

[Direct factual extraction]

- 论文讨论 CSS/stabilizer qLDPC。X/Z stabilizers 用稀疏 H_X/H_Z 表示，并满足 H_X H_Z^T=0（pp. 2-3）。
- BP 输入是 syndrome s、每个 error mechanism 的 prior，以及 H；code capacity model 中每个 data qubit 独立施加 X、Y、Z error，概率均为 p/3。
- Circuit-level model 用 Stim 生成 syndrome-extraction circuit、detector error model 和 parity-check matrix；每个 column 对应一个 error mechanism，每一行对应 detector event。
- 主要代码包括 bivariate bicycle codes，如 J144,12,12K、J288,12,18K、J154,6,16K、J126,12,10K，以及 SHYPS (n=225, k=16, d=8)。
- Metric 是 logical error rate（LER）和 circuit-level 的 LER per round；不是经典 BER/BLER。
- Physical error rate 为 p；论文没有通信 SNR 或 E_b/N_0。

# Method

[Direct factual extraction]

1. 先运行带 oscillation tracking 的 BP；统计每个 bit 在多轮 hard decision 中翻转的次数。
2. 选取 top |Phi| 个最常翻转的 bits 作为候选集合 Phi。
3. 对候选 bit 组合 t 构造修改后的 syndrome s' = s XOR t H^T，并对每个 s' 独立运行短深度 BP。
4. 任意 trial 成功满足 syndrome 后，将输出中的 t 翻回；由于候选试验彼此独立，可并行运行。
5. Code-capacity model 使用候选 weight 不超过 1 的所有 trial；circuit-level model 对每个 weight 随机采样 ns 个 trial，最多 weight w_max。
6. 论文实现 serial CPU、parallel CPU 和 estimated GPU 版本；GPU 版本受现有 CUDA-Q batch API 限制。

# Key Equations

[Direct factual extraction] 论文 p. 4 给出的 normalized Min-Sum BP 形式包括：

$$
l_{v_i}^{ch}=\log\frac{1-p_{v_i}}{p_{v_i}},
$$

$$
l_{v_i\to c_j}
=
l_{v_i}^{ch}
+
\sum_{c_{j'}\in N(v_i)\setminus c_j}
l_{c_{j'}\to v_i},
$$

$$
l_{c_j\to v_i}
=
(-1)^{s_j}\alpha
\left(
\prod_{v_{i'}\in N(c_j)\setminus v_i}
\operatorname{sign}(l_{v_{i'}\to c_j})
\right)
\min_{v_{i'}\in N(c_j)\setminus v_i}
|l_{v_{i'}\to c_j}|.
$$

输出 marginal LLR 为：

$$
l_i^{out}=l_{v_i}^{ch}+\sum_{c_{j'}\in N(v_i)}l_{c_{j'}\to v_i}.
$$

BP-SF 的 syndrome modification 与 restoration 可概括为：

$$
s'=s\oplus tH^T,\qquad \hat e_{\mathrm{final}}=\hat e\oplus t.
$$

Circuit-level 的 logical error rate per round 定义为：

$$
\mathrm{LER}_{\mathrm{round}}=1-(1-\mathrm{LER})^{1/d},
$$

其中 d 是 syndrome-extraction rounds。

# Experimental Setup

[Direct factual extraction]

| Item | Code-capacity model | Circuit-level model |
|---|---|---|
| Noise | X/Y/Z independently with probability p/3 per data qubit | Errors injected across gates and measurements; Stim-generated detector model |
| Main examples | J154,6,16K and J288,12,18K bivariate bicycle codes | J144,12,12K; J288,12,18K; coprime BB; SHYPS |
| BP | Min-Sum with adaptive damping alpha_i=1-2^(-i) | Same family; layered BP used in many comparisons |
| Candidate policy | All trial vectors of weight at most 1 | ns random trial vectors per weight 1 through w_max |
| Example parameters | J154: |Phi|=8, BP cap 50; at most 450 BP iterations serially, 100 effective iterations if parallel |
| Circuit example | Not applicable | J144 uses w_max=6, ns=5, up to 3100 BP iterations |
| Baselines | BP, BP-OSD-0, BP-OSD-10 | BP1000-OSD10, BP1000, BP10000 and variants |
| Metrics | LER | LER and LER per round; latency and BP iteration count |
| Samples | At least 100 logical errors per point unless noted | 10000 or 100000 shots in complexity study; 20000 syndromes per physical-error-rate point in implementation benchmark |
| SNR/BER/BLER | Not applicable/reported | Not applicable/reported |
| Zotero PDF | 94TG4URT, 14 pages | Zotero annotations: none returned |

# Main Results

[Direct factual extraction]

- Code-capacity J154,6,16K：BP-SF 的 LER 低于 baseline BP 和 BP-OSD，且不需要 OSD post-processing；J288,12,18K 上 BP-SF 与 BP-OSD 的 LER 相近（pp. 6-7）。
- Circuit-level J144,12,12K：BP-SF 的 LER 略高于 BP1000-OSD10，但仍可比；其设置为 w_max=6、ns=5，最多约 3100 BP iterations（p. 7）。
- Circuit-level J154,6,16K：低 physical error-rate 区域中 BP-SF 与 BP-OSD 相近，高 physical error-rate 区域 BP-SF 更差但仍低于 baseline BP（pp. 7-8）。
- J126,12,10K：增加 ns 和 w_max 可让 BP-SF 略低于 BP-OSD，但代价是最多约 10000 BP iterations（p. 8）。
- Complexity/latency：J288,12,18K 的平均 BP-SF latency 约为 BP-OSD 的 0.63 倍；只看 initial BP 失败的样本，post-processing latency 约为 BP-OSD 的 0.1 倍（p. 9）。
- Abstract 对 J144,12,12K 报告平均 latency 约为 BP-OSD 的 70%；post-processing 并行化后，平均 latency 比 single-process implementation 降 55%，maximum latency 可到 18%（metadata abstract；具体条件见论文实现章节）。

# Comparison With Baselines

- BP：每个 iteration 约 O(N)；提供无 post-processing 的基础性能。
- BP-OSD：在 BP 后做 ordered statistics decoding，Gaussian elimination 约 O(N^3)，是主要 error-rate/latency baseline。
- BP-OSD-0、BP-OSD-10：通过 BP 迭代数和 OSD order 区分，例如 BP1000-OSD10。
- BP-SF：以 |Phi|、w_max、ns 控制候选数量；serial iteration count 是保守复杂度口径，真正并行 latency 更低。
- [My Interpretation] BP-SF 的“更快”来自并行关键路径，而不是候选总工作量必然更少；论文同时报告两种口径。

# Limitations

- “第一个满足 syndrome 的候选”直接返回，依赖作者对低错误率和高距离下 coset 风险的假设；不等同于显式 maximum-likelihood 选择。
- Circuit-level parity-check matrix 的 error mechanisms 数量可能远大于 qubit 数，候选 weight-1 策略不能直接照搬 code-capacity。
- GPU 结果是 estimated/pessimistic 版本：oscillation statistics 先在 CPU 计算，CUDA-Q batch decode 还可能等待整个 batch。
- 不同代码、noise model、BP iterations 和 OSD order 的 LER 不能直接横向合并。
- 本文使用 qLDPC 专用 LER；没有经典通信链路中的 SNR、BER 或 BLER。

# Authors' Claims

- 作者声称 BP-SF 可以在多种 bivariate bicycle/QLDPC code 上达到与 BP-OSD 相近或更低的 LER（摘要、pp. 5-8）。
- 作者声称候选 trial 可独立并行，因而能显著降低 average latency（摘要、pp. 1-2, 9-10）。
- 作者声称 BP-SF 不需要 BP-OSD 的 Gaussian elimination，并适合 real-time/resource-constrained QEC（摘要、pp. 1-2）。
- 作者声称 oscillation bits 与真实 error locations 有相关性；Figure 3 使用 top 50 bits、约 8000 error mechanisms 和 1000 decoding failures 作分析（p. 5）。

# My Interpretation

- BP-SF 是一种 syndrome-domain 的 Chase-like ensemble；它保留 BP 的局部更新，同时用输入扰动打破对称停滞。
- LER per round 只适用于有 d 轮 syndrome extraction 的 circuit-level 定义，不能与单轮 code-capacity LER 混成一个指标。
- BP-SF 的复杂度应至少同时报告总 trial 数、serial cumulative iterations 和并行 critical-path latency，否则“高效”含义不完整。

# Relation To My Research

- [[LDPC-置信传播译码]]
- [[LDPC-Min-Sum 译码]]
- [[LDPC-译码迭代次数]]

[Evidence boundary] Vault 中没有 QLDPC Concept Note；本笔记不创建悬空的 QLDPC 概念链接，也不把经典 BLER 与 BER 节点映射到 LER。

# Related Papers

- [[2026-Moradi-Sequential-BP-based-Decoding-QLDPC]]：sequential BP/SCNS/SVNS，噪声和 post-processing 不同。
- [[2007-Casado-Informed-Dynamic-Scheduling-LDPC]]：经典 LDPC 的 informed scheduling 先例，不能直接比较 LER。

# Open Questions

- 在同一硬件上并行 BP-SF 与 BP-OSD 时，candidate generation、memory copy 和 early return 的真实关键路径是多少？
- “有效 syndrome”到“正确 logical coset”的概率如何随 code distance、physical error rate 和候选 weight 变化？
- GPU 是否能在每个 BP iteration 内并行追踪 oscillation 并直接批量生成 syndrome candidates？
- 对 circuit-level 噪声，ns 和 w_max 的收益是否能用固定总算力或固定 latency 预算比较？

# Useful Citations

- Wang, Li, and Mueller, “Fully Parallelized BP Decoding for Quantum LDPC Codes Can Outperform BP-OSD,” arXiv:2507.00254, 2026, pp. 1-10.
- Zotero item 8VW2PY6E; PDF attachment 94TG4URT.
- DOI: https://doi.org/10.48550/arXiv.2507.00254
