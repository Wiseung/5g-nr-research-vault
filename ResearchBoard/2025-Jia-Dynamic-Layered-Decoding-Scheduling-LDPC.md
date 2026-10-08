---
type: literature
title: "Dynamic Layered Decoding Scheduling for LDPC Codes Aided by Check Node Error Probabilities"
authors:
  - "Chenyuan Jia"
  - "Dongxu Chang"
  - "Ruiyuan Wang"
  - "Guanghui Wang"
  - "Guiying Yan"
  - "Cunquan Qu"
year: 2025
venue: "arXiv preprint (arXiv:2506.13507)"
doi: "10.48550/arXiv.2506.13507"
url: "http://arxiv.org/abs/2506.13507"
zotero-key: "BZ3DBE8S"
zotero-attachment-key: "HCZRRGWU"
evidence: primary
tags:
  - topic/ldpc
  - domain/5g-nr
  - process/decoding
  - process/scheduling
status: read
---

# Research Problem

[Direct factual extraction] 论文研究 layered belief propagation（LBP）中 check-node 更新顺序如何选择，目标是在有限迭代数和高吞吐约束下提高译码效率。作者提出根据 check-node error probability 排序的 Dyn-EBP 和 Dyn-PEBP。

# Motivation

[Authors' Claims] 论文指出 flooding 延迟使用当前迭代的新信息，LBP 能通过顺序更新加快收敛，但固定或启发式顺序仍有改进空间。作者引用的动机是优先更新 error probability 较低的 check nodes 可改善收敛（p. 1）。

[My Interpretation] 这种问题属于 schedule/iteration trade-off，而非改变 parity-check matrix 或译码目标；因此结果应主要与相同码和相同迭代预算的 scheduling baseline 比较。

# System Model

[Direct factual extraction]

- 采用 5G NR LDPC base graph 1（BG1），并在 QC layer-based scheduling 下对 lifted graph 中对应的 check nodes 做 error-probability 聚合（p. 4）。
- 论文讨论 V2C/C2V 消息、check-node error probability 和每个 check node 的更新计数 l_i。
- Figure 3 的横轴明确使用 E_s/N_0；读取到的文字没有为这些曲线完整说明调制、噪声归一化、CSI 或 fading 参数。
- 因而本笔记只记录 E_s/N_0，不把该图未经证明地改写为 E_b/N_0 或泛称 SNR。
- Blocklength/rate settings include (1482, 0.386), (1170, 0.4681), (1320, 0.4) and (2640, 0.4)（Fig. 3）。
- No MIMO, carrier, bandwidth or antenna setting is reported in the readable text.

# Method

[Direct factual extraction]

1. Dyn-EBP 根据 check-node error probability 选择当前最小者。
2. 每个 check node 在一个 iteration 内最多被更新一次；完成 layer/CN 更新后重新计算受影响节点的 error probability。
3. Dyn-PEBP 不再使用严格的每轮一次限制，而是为已更新次数加入 penalty，再以贪心顺序继续选择。
4. LBP 的 layer 约束和 QC layer 级聚合保留；改变的是动态更新顺序。

[Evidence boundary] 论文 pp. 2-3 没有文本层，是扫描图。因此 error probability 的完整推导、图中数值曲线的每个点以及算法中对应的若干中间式不能从当前 PDF 文本可靠恢复。

# Key Equations

[Direct factual extraction] 可从 p. 4 可靠读取的 Dyn-PEBP 定义是：

$$
\widetilde{p}_{\epsilon}^{c_i}=p_{\epsilon}^{c_i}+f(l_i),
\qquad
f(l_i)=\gamma l_i,
\qquad \gamma\in[0,1].
$$

论文说明 gamma 越接近 0 越贪心，gamma=1 对应 Dyn-EBP；仿真中经验最优约为 gamma=0.35（p. 4）。

图的复杂度分析令 Tanner graph 边数为：

$$
E=\bar d_v N=\bar d_c M.
$$

论文分别把 V2C 和 C2V 更新记为 O(E)，error-probability 计算涉及平均节点度，priority-queue/Fibonacci-heap 重排用于降低排序成本，并给出 Dyn-EBP/Dyn-PEBP 每 iteration 的总体阶数为 O(E \bar d_v \bar d_c)（p. 4）。

[Evidence boundary] p_epsilon^(c_i) 的未加 penalty 计算式位于扫描的 pp. 2-3；本笔记不以 OCR 猜测该式。

# Experimental Setup

[Direct factual extraction]

| Item | Value/evidence |
|---|---|
| Code | 5G NR BG1, QC layer-based schedule |
| Maximum iterations | 5 |
| Dyn-PEBP coefficient | gamma empirically set near 0.35 |
| RD-RBP coefficient | beta=0.95 |
| Blocklength/rate | 1482/0.386, 1170/0.4681, 1320/0.4, 2640/0.4 |
| Horizontal axis | E_s/N_0 |
| Primary metric | BLER |
| BER | Not reported |
| Channel details | Not fully recoverable from readable text |
| Frames/errors/seed | Not reported |
| Baselines | LBP, LPHD, RD-RBP, method in [11], and other dynamic/offline scheduling references |
| Zotero PDF | HCZRRGWU, 5 pages |
| Zotero ordinary note | Comment: 5 pages, 4 figures |
| Zotero annotations | None returned |

# Main Results

[Direct factual extraction] 论文 p. 4-5 的文字和 Figure 3 说明，在四组不同 blocklength/rate 下，error-probability-based scheduling 的 BLER 曲线优于 LBP、LPHD、method [11] 和 RD-RBP；作者将其归因于优先更新低 error-probability check nodes。

[Evidence boundary] 读取到的 Figure 3 是页面中可提取的图像/表格混合内容，论文没有在可读正文中给出每个设置的统一 dB gain 表。因此这里不填写未经图像精确读数支持的数值增益。

# Comparison With Baselines

- LBP: 固定的 layered baseline。
- LPHD: least-punctured and highest-degree scheduling。
- RD-RBP: residual-decaying-based residual BP，论文设置 beta=0.95。
- Method in [11]: 以先前 error-probability insight 为基础的方法。
- Dyn-EBP/Dyn-PEBP: 论文提出的动态方法，均固定最大 5 iterations。
- [Direct factual extraction] 这些曲线在代码、BG1 和最大迭代次数上被放在同一组 Figure 3 中，但页面扫描限制了逐点数值复核。

# Limitations

- pp. 2-3 是无文本层的扫描图；关键 error-probability 推导无法从当前文本可靠抄录。
- 论文没有提供可直接复现 Figure 3 的帧数、错误数、随机种子、调制和完整信道描述。
- E_s/N_0 与其他论文常见的 E_b/N_0 不可直接横向比较。
- 复杂度分析给出渐近阶数，但没有 GPU/CPU runtime、内存带宽或实际 energy-per-bit 结果。
- 论文只在 BG1 和 5 iteration 设定下展示主要实验，schedule 对其他图结构的泛化仍需验证。

# Authors' Claims

- 作者声称 Dyn-EBP 与 Dyn-PEBP 在多种 5G NR LDPC blocklength 和 code rate 下优于已有动态及 offline schedules（摘要、p. 5）。
- 作者声称优先更新低 error-probability check nodes 能带来更高的 decoding efficiency（摘要、p. 1）。
- 作者把 gamma≈0.35 报告为 Dyn-PEBP 的较佳经验设置，把 gamma=1 解释为 Dyn-EBP（p. 4）。
- 以上是作者的实验和解释主张，不等于在当前笔记中完成了独立复现。

# My Interpretation

- Dyn-PEBP 的 penalty 是“置信度排序”和“更新公平性”之间的连续旋钮；这是对算法结构的解释，不是作者额外声称的理论定理。
- 若要公平复现，应同时固定 E_s/N_0 定义、layer 聚合方法、5 iteration、停止规则和 puncturing 初始状态。
- 因为扫描页缺少公式和 raw data，当前可以确认方法框架和比较对象，但不能确认每条曲线的精确 gain。

# Relation To My Research

- [[LDPC-置信传播译码]]
- [[LDPC-译码迭代次数]]
- [[LDPC-基图选择]]
- [[QC-LDPC 结构]]
- [[BLER 与 BER]]
- [[软判决与 LLR]]

# Related Papers

- [[2007-Casado-Informed-Dynamic-Scheduling-LDPC]]：residual/informed scheduling 的早期经典基线。
- [[2008-Chang-Lower-Complexity-LBP-LDPC]]：LBP 的复杂度和部分并行实现。
- [[2026-Moradi-Sequential-BP-based-Decoding-QLDPC]]：把 sequential scheduling 研究扩展到 QLDPC，但噪声模型和指标不同。

# Open Questions

- 扫描的 pp. 2-3 中 p_epsilon^(c_i) 的精确定义是否依赖独立错误假设、LLR 或 syndrome？
- 各 blocklength/rate 的 modulation、channel 和统计样本数是什么？
- 动态重排的实际 wall-clock overhead 是否抵消减少的迭代数？
- 在 BG2、不同 Z_c、量化 LLR 或 GPU 并行硬件上，gamma≈0.35 是否仍然稳定？

# Useful Citations

- Jia et al., “Dynamic Layered Decoding Scheduling for LDPC Codes Aided by Check Node Error Probabilities,” arXiv:2506.13507, 2025, pp. 1, 4-5.
- Zotero item BZ3DBE8S; PDF attachment HCZRRGWU.
- Zotero ordinary note: Comment: 5 pages, 4 figures.
- DOI: https://doi.org/10.48550/arXiv.2506.13507
