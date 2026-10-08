---
type: literature
title: "Informed Dynamic Scheduling for Belief-Propagation Decoding of LDPC Codes"
authors:
  - "Andres I. Vila Casado"
  - "Miguel Griot"
  - "Richard D. Wesel"
year: 2007
venue: "2007 IEEE International Conference on Communications"
doi: "10.1109/ICC.2007.158"
url: "http://ieeexplore.ieee.org/document/4288829/"
zotero-key: "ZBIQ3D3D"
zotero-attachment-key: "7KNIPJW5"
evidence: primary
tags:
  - topic/ldpc
  - process/decoding
  - process/scheduling
  - metric/fer
status: read
---

# Research Problem

[Direct factual extraction] 论文研究 sequential BP 中“下一条消息或下一个 check node 应该先更新什么”的问题。目标是在不改变 BP 消息生成函数的前提下，用当前消息 residual 动态选择更新顺序，从而减少迭代、改善 FER，并处理 trapping-set errors。

# Motivation

[Authors' Claims] 作者指出 flooding 使用同一批旧信息，标准 sequential schedule 虽然收敛更快，但仍需决定更新顺序。论文以 RBP、node-wise RBP 和 approximate residual schedule 解决该问题（pp. 1-2）。

[My Interpretation] 这是后续动态 layered scheduling 的重要经典参照：它同时揭示了“少迭代”和“低 error floor”可能需要不同程度的贪心策略。

# System Model

[Direct factual extraction]

- 二部 Tanner graph 有 N 个 variable nodes 和 M 个 check nodes；消息为 LLR。
- 基础更新为：

  $$
  m_{v_j\to c_i}=C_j+\sum_{c_a\in N(v_j)\setminus c_i}m_{c_a\to v_j},
  $$
  
  $$
  m_{c_i\to v_j}=2\tanh^{-1}\left(
  \prod_{v_b\in N(c_i)\setminus v_j}
  \tanh\frac{m_{v_b\to c_i}}{2}
  \right).
  $$
  
- 主要仿真为 AWGN 下的 binary LDPC；核心 setting 是 IEEE 802.11n blocklength 1944、rate 1/2，sub-matrix size 54x54；另测试 802.11n rate 5/6（pp. 4-6）。
- E_b/N_0=1.75 dB 用于 rate-1/2 迭代曲线；rate-5/6 图使用固定 SNR=6.0 dB。论文的横轴/文字同时出现 E_b/N_0 与 SNR，不能混作同一归一化定义。
- MIMO/antenna/CSI 不适用；decoder 输入是 AWGN LLR。
- Metric 是 FER，不是 BER 或 BLER。

# Method

[Direct factual extraction]

1. 标准 sequential schedule（SSS）以固定顺序更新 check nodes；论文用 LBP 作为 SSS baseline。
2. RBP 定义每条消息的 residual，优先传播 residual 最大的 C2V message。
3. Node-wise RBP 把同一 check node 的全部 C2V messages 一起更新，降低 RBP 的过度贪心。
4. 用 min-BP 两个最小可靠度近似 check-node 输出，得到 approximate residual；对应算法是 ARBP 和 node-wise ARBP。
5. Parallel node-wise ARBP 一次更新 residual 最大的 p 个 check nodes，以获得部分并行吞吐量。

# Key Equations

[Direct factual extraction] RBP residual 定义为：

$$
r(m_k)=\lVert f_k(\mathbf m)-m_k\rVert.
$$

在 LLR message space 中，residual 是更新前后 LLR 的绝对差。Approximate residual 为：

$$
r^{(a)}(m_k)=\lVert f_k^{(a)}(\mathbf m)-m_k\rVert,
$$

其中 f_k^(a) 用 min-BP 只保留两个最小 incoming reliability 来估计 check-node 输出；实际传播仍使用 full update equations（p. 4）。

论文对 scheduling 的 algorithmic complexity 口径是：一次 informed iteration 以完成与 flooding/SSS 相同数量的 message 或 check-node updates 计数。合适的 sequential update equation 可以使 message-generation operations per iteration 与 flooding 相当，但 residual 计算和优先队列排序增加额外开销（p. 4）。

# Experimental Setup

[Direct factual extraction]

| Item | Value/evidence |
|---|---|
| Channel | AWGN |
| Main code | IEEE 802.11n, N=1944, rate 1/2, sub-matrix 54x54 |
| Additional code | IEEE 802.11n rate 5/6 |
| Fixed point | E_b/N_0=1.75 dB for rate-1/2 iteration curves |
| High-rate point | SNR=6.0 dB for rate-5/6 iteration plot |
| Metrics | FER vs iterations, FER vs E_b/N_0/SNR, message/Soft-XOR complexity |
| Baselines | Flooding, SSS (LBP), RBP, ARBP, node-wise RBP, node-wise ARBP, parallel node-wise ARBP |
| Seeds/frames | Not reported in the extracted paper |
| Zotero PDF | 7KNIPJW5, 6 pages |
| Zotero annotations | None returned |

# Main Results

[Direct factual extraction]

- 在 E_b/N_0=1.75 dB 的 rate-1/2 setting，RBP 在 4 iterations 的 FER 大致等于 SSS/LBP 在 13 iterations；但约 19 iterations 后曲线交叉，RBP 的大迭代 FER 变差（Fig. 1, p. 5）。
- Node-wise RBP 在 18 iterations 的 FER 大致等于 SSS/LBP 在 50 iterations，并在全部展示迭代区间优于 SSS/LBP（p. 5）。
- ARBP 与 exact-residual RBP 的曲线几乎不可区分；parallel node-wise ARBP 用 p=54 时只有较小性能损失（p. 5）。
- 802.11n rate-1/2 的 50-iteration node-wise ARBP 相比 flooding/SSS 有更低 FER；rate-5/6 也显示 node-wise ARBP 的收益（Figs. 3-4, pp. 5-6）。
- 这些结果是 FER 结果，不是 BER 或 BLER 结果。

# Comparison With Baselines

- Flooding 提供高并行但使用旧消息。
- SSS/LBP 提供固定顺序的 sequential baseline。
- RBP 更贪心，短 iteration 速度快，但可能加重 difficult errors。
- ARBP 用 min-BP 近似 residual，目标是减小 residual 计算复杂度而保持性能。
- Node-wise ARBP 在较少 greediness、trapping-set recovery 和部分并行之间折中。

# Limitations

- Informed schedule 的 residual 计算和排序带来额外 per-iteration cost；论文没有给出一个脱离实现选择的统一 wall-clock 优势。
- parallel node-wise ARBP 的 check nodes 可能共享 variable nodes，存在 memory clash 和合并更新的硬件问题。
- 主要证据来自旧的 802.11n 结构化码，不能直接代表 5G NR BG1/BG2。
- 仿真统计次数、随机种子和完整 frame stopping rule 未报告。
- RBP 的短迭代优势与大迭代性能优势不同，不能只用一个 iteration 点下结论。

# Authors' Claims

- 作者声称 informed update sequences 比 standard sequential schedules 需要更少 iterations，并能解决部分 standard trapping-set errors（摘要、pp. 1-3）。
- 作者声称 node-wise RBP 在大迭代数下同时取得更好的 FER；ARBP 可以接近 exact residual 的性能（pp. 3-5）。
- 作者声称 node-wise ARBP 的部分并行版本只有小的性能退化，具有实现吸引力（pp. 4-6）。
- 作者同时承认 residual computation/ordering 增加复杂度，具体 trade-off 依赖实现（pp. 4, 6）。

# My Interpretation

- RBP 的曲线交叉说明“更快达到某一 FER”和“最终 error floor 更低”不是同一个目标。
- Node-wise grouping 可能通过减少单边贪心造成的错误传播来改善 trapping-set behavior；这是对论文现象的解释，不是独立证明。
- 若与 5G 动态 schedule 比较，必须重新定义 iteration、message update count 和 layer aggregation。

# Relation To My Research

- [[LDPC-置信传播译码]]
- [[LDPC-Min-Sum 译码]]
- [[LDPC-译码迭代次数]]
- [[QC-LDPC 结构]]
- [[软判决与 LLR]]

# Related Papers

- [[2008-Chang-Lower-Complexity-LBP-LDPC]]：在 QC-LDPC 上处理 layered schedule 的复杂度/部分并行问题。
- [[2025-Jia-Dynamic-Layered-Decoding-Scheduling-LDPC]]：用 check-node error probabilities 动态排序。
- [[2026-Moradi-Sequential-BP-based-Decoding-QLDPC]]：相似的 sequential message-passing 思路，但为 QLDPC。

# Open Questions

- 在 5G NR BG1/BG2 的 puncturing、rate matching 和非规则 degree 下，node-wise residual 是否仍然稳定？
- residual priority queue 的实际功耗和存储访问成本是否抵消迭代减少？
- 对 trapping set 的改善能否用可重复的 error-pattern 分类和置信区间报告？

# Useful Citations

- Casado, Griot, and Wesel, “Informed Dynamic Scheduling for Belief-Propagation Decoding of LDPC Codes,” IEEE ICC 2007, pp. 932-937.
- Zotero item ZBIQ3D3D; PDF attachment 7KNIPJW5.
- DOI: https://doi.org/10.1109/ICC.2007.158
