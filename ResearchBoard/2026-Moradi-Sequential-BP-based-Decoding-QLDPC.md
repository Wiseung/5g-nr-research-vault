---
type: literature
title: "Sequential BP-based Decoding of QLDPC Codes"
authors:
  - "Mohsen Moradi"
  - "Salman Habib"
  - "Vahid Nourozi"
  - "David G. M. Mitchell"
year: 2026
venue: "arXiv preprint (arXiv:2602.13420)"
doi: "10.48550/arXiv.2602.13420"
url: "http://arxiv.org/abs/2602.13420"
zotero-key: "TRDZYAKJ"
zotero-attachment-key: "4B26WBLT"
evidence: primary
tags:
  - topic/qldpc
  - domain/quantum-error-correction
  - process/decoding
  - process/scheduling
status: read
---

# Research Problem

[Direct factual extraction] 论文研究 QLDPC 中标准 flooding BP 容易 non-converge、stall 或受 stabilizer degeneracy 和短环影响的问题。核心问题是：只改变 CN/VN 的更新 schedule，能否在不改变 code 的情况下提高 FER、减少消息传播和 BPGD 的 decimation rounds？

# Motivation

[Authors' Claims] 作者把 QLDPC 的稳定子约束、短环、degeneracy 和 trapping sets 视为 BP 收敛困难的来源，并提出 sequential schedule 作为低成本的改进方向（摘要、pp. 1-3）。

[My Interpretation] 这里的 sequential schedule 与经典 LDPC 中的 layered/shuffled BP 有算法亲缘关系，但 QLDPC 的 syndrome、coset 和 degeneracy 语义不同，不能把其 FER 结果直接当作经典 BLER 结果。

# System Model

[Direct factual extraction]

- 论文采用 CSS/二元 syndrome-domain 视角，H_1 的列对应 variable nodes，行对应 check nodes，输入是 X-syndrome s_x 和 independent Pauli-X error probability p_x。
- Channel prior 的 LLR 为：
  
  $$
  \mu_v=\log\frac{1-p_x}{p_x}.
  $$
  
- 主要 benchmark 包括 HGP code C2 (n=1922, k=50, d=16) 和 code B1 (n=882, k=24, 18 <= d <= 24)。
- Noise model 是 independent X errors/Pauli-X noise；论文没有用通信 SNR、E_b/N_0 或经典 AWGN。
- Output/metric 是 FER、CN-to-VN message count 和 decimation rounds；没有把这些改写为 BER/BLER。
- 论文讨论的是 syndrome matching：若 hard estimate 满足 x_hat H^T=s_x，则提前停止。

# Method

[Direct factual extraction]

1. Standard syndrome-domain BP 使用固定的 flooding message updates。
2. SCNS 按一个固定但随机选取的 CN order 顺序访问 check nodes；一个 global iteration 是一轮 CN sweep。
3. SVNS 按固定但随机选取的 VN order 顺序访问 variable nodes；每次 VN 更新先刷新 incident CN messages，再传播新的 V2C messages。
4. 在 BPGD 中，若 BP 未满足 syndrome，则冻结/decimate 高可靠 variable；SBPGD 用 SCNS 或 SVNS 替换内部 BP。
5. 每轮或每个 sweep 后形成 hard decision、检查 syndrome，成功则 early stop。

# Key Equations

[Direct factual extraction] 论文 p. 3 的 syndrome-domain BP 更新为：

$$
m_{c\to v}
=
2(-1)^{s(c)}
\tanh^{-1}
\left(
\prod_{u\in\partial c\setminus\{v\}}
\tanh\frac{m_{u\to c}}{2}
\right),
$$

$$
m_{v\to c}
=
\mu_v+
\sum_{c'\in\partial v\setminus\{c\}}
m_{c'\to v}.
$$

Marginal belief 和 hard decision 为：

$$
m_v=\mu_v+\sum_{c\in\partial v}m_{c\to v},
\qquad
\hat x_v=
\begin{cases}
1,&m_v<0,\\
0,&m_v\ge 0.
\end{cases}
$$

停止条件是 x_hat H^T=s_x 或达到 iteration cap T。

[Direct factual extraction] 论文的 BPGD/SBPGD 会选取高 |m_v| 的 variable 进行 finite clamping/decimation；SBPGD 只是把其中的 BP 子程序替换成 sequential schedule。

# Experimental Setup

[Direct factual extraction]

| Item | Value/evidence |
|---|---|
| Noise | Independent Pauli-X / X-error model |
| Main codes | C2 (n=1922, k=50, d=16); B1 (n=882, k=24, 18 <= d <= 24) |
| Noise axis | p_x, not SNR |
| Metrics | FER; CN-to-VN message count; decimation count |
| BP iteration caps | Figures compare T=10 and T=100; some BPGD settings use T=50 or T=100 |
| Baselines | Flooding BP, BPGD, BP-OSD-0 |
| Message-count sample | C2 table at T=100; B1 table at T=100 |
| BER/BLER | Not reported; do not substitute FER |
| Seeds/number of trials | Not fully reported in the extracted text |
| Zotero PDF | 4B26WBLT, 6 pages |
| Zotero annotations | None returned |

# Main Results

[Direct factual extraction]

- C2 at p_x=0.04: flooding BP propagates 162376 CN-to-VN messages on average; SCNS-BP 28331; SVNS-BP 24272. This is over 85% lower message traffic for the sequential schedules (Table I, p. 6).
- B1 at p_x=0.04: BP 42153 messages, SCNS 8975, SVNS 9011, approximately 79% lower for the sequential versions (Table II, p. 6).
- For C2 at low p_x, SVNS with T=100 reaches approximately two orders of magnitude lower FER than flooding BP in the shown regime; T=10 still exceeds flooding by up to about one order at p_x=0.04 (Fig. 3, p. 5).
- B1 shows the same direction for small p_x; at p_x=0.04, SVNS does not beat BP-OSD-0 in the reported comparison, a limitation explicitly noted by the paper (Fig. 4, p. 5).
- SBPGD slightly improves or matches BPGD while using substantially fewer decimation steps. For B1 at p_x=0.04, BPGD T=100 averages 1.1469 decimations, while SVNS-BPGD averages 0.0056 at T=100 (Table III, p. 6).

# Comparison With Baselines

- Flooding BP: same Tanner graph and syndrome model, but delayed updates.
- SCNS/SVNS: proposed sequential variants; their asymptotic per-iteration message-passing order is the same as BP, while the sequential schedules can terminate earlier.
- BP-OSD-0: post-processing/linear-system baseline; SVNS can surpass it on some low-p_x regimes but not for every code and point.
- BPGD: decimation baseline; SBPGD changes the schedule inside BPGD and reduces decimation rounds.
- [My Interpretation] Message count and FER are complementary: lower CN-to-VN count suggests less traffic, but it is not a direct hardware runtime measurement.

# Limitations

- CN/VN orders are randomly selected rather than learned or optimized.
- Main evidence is limited to two QLDPC codes and independent X-error/Pauli-X settings.
- Sequential scheduling adds VN refresh work in SCNS/SVNS; message count reduction is not identical to a full operation-count or wall-clock reduction.
- No hardware benchmark, GPU implementation, SNR sweep, BER/BLER curve, or confidence interval is supplied in the extracted paper.
- The paper does not establish performance under general depolarizing, circuit-level, non-CSS, or broader code families.

# Authors' Claims

- 作者声称 SCNS/SVNS 在标准 QLDPC benchmark 上能降低 FER，并且 SBPGD 比 BPGD 使用更少 decimation rounds（摘要、p. 6）。
- 作者声称 C2 (n=1922, k=50, d=16) 上 SVNS-BP 在大致相同的复杂度下超过 BP-OSD-0（摘要；具体曲线见 p. 5）。
- 作者把降低 message traffic 和打破 flooding 的同步/振荡联系起来（pp. 5-6）。
- 这些主张是在给定 QLDPC、p_x、iteration cap 和软件统计设置下提出的，不应外推为所有 QLDPC 译码器都成立。

# My Interpretation

- SCNS/SVNS 的优势很可能来自最新消息在同一 sweep 内传播，而不仅是“顺序”这一标签；这是对算法机制的解释，不是论文证明的普适定理。
- p_x 应被视为物理错误概率，不要把其数值换算成通信领域 SNR。
- 对 QLDPC，满足 syndrome 只说明得到一个有效解；coset/逻辑等价类仍是逻辑错误分析的关键，因此 FER 比单纯 bit error 更合适。

# Relation To My Research

- [[LDPC-置信传播译码]]
- [[LDPC-译码迭代次数]]

[Evidence boundary] Vault 中没有现成 QLDPC Concept Note；本笔记不创建空的 QLDPC 链接，也不把经典 BLER 与 BER 节点当作量子指标节点。

# Related Papers

- [[2026-Wang-Fully-Parallelized-BP-Decoding-Quantum-LDPC]]：量子 LDPC 的 BP-SF syndrome-flip post-processing，噪声和指标不同。
- [[2007-Casado-Informed-Dynamic-Scheduling-LDPC]]：经典 LDPC 的 informed/sequential scheduling 先例，但不能直接比较 FER 数值。

# Open Questions

- 在 depolarizing 或 circuit-level noise 下，固定随机顺序与自适应顺序的收益是否保持？
- 若把 CN/VN 更新并行化，新增 VN refresh 的实际 GPU/ASIC 成本是多少？
- FER、logical error rate 和 syndrome convergence 的关系如何按 coset 正确分解？
- SBPGD 的 finite clamping 值、decimation tie-breaking 和随机种子对结果有多敏感？

# Useful Citations

- Moradi et al., “Sequential BP-based Decoding of QLDPC Codes,” arXiv:2602.13420, 2026, pp. 3-6.
- Zotero item TRDZYAKJ; PDF attachment 4B26WBLT.
- DOI: https://doi.org/10.48550/arXiv.2602.13420
