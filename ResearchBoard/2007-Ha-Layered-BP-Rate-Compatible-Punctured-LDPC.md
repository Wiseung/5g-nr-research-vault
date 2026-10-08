---
type: literature
title: "Layered BP Decoding for Rate-Compatible Punctured LDPC Codes"
authors:
  - "Jeongseok Ha"
  - "Demijan Klinc"
  - "Jini Kwon"
  - "Steven W. McLaughlin"
year: 2007
venue: "IEEE Communications Letters, 11(5), 440-442"
doi: "10.1109/LCOMM.2007.061962"
url: "http://ieeexplore.ieee.org/document/4202100/"
zotero-key: "WU5VFGGV"
zotero-attachment-key: "UL7MRCVN"
evidence: primary
tags:
  - topic/ldpc
  - process/decoding
  - process/scheduling
  - process/puncturing
  - metric/ber
status: read
---

# Research Problem

[Direct factual extraction] 论文研究 rate-compatible punctured LDPC（RCP-LDPC）在高比例 puncturing 下 BP 收敛变慢的问题。目标是设计 check-node layering，使 punctured variable nodes 尽快获得非零信息，从而在有限最大迭代数下改善 BER。

# Motivation

[Authors' Claims] 作者指出 RCP-LDPC 能在多个码率下工作，但 punctured bits 没有 channel information，常规 BP 需要更多 iterations；在实际 decoder 有 latency/complexity 上限时，这会明显损失 BER（p. 1）。

[My Interpretation] 论文把 layering 视为 puncturing-induced initialization problem：layer 顺序首先恢复 punctured variables，再让后续消息传播利用这些新信息。

# System Model

[Direct factual extraction]

- 母码是 blocklength 2000、rate 0.5 的 irregular LDPC；通过 puncturing 得到 rates 0.6、0.7、0.8 和 0.9。
- 未传输的 punctured variable node 初始 LLR 设为 0。
- 若 punctured variable node 在 conventional BP 的第 k iteration 首次收到非零 message，则称为 k-step recoverable（k-SR），level of recoverability 为 k。
- 为某个 k-SR punctured variable node 提供第一条非零消息的 check node 称为 survived check node；作者按该 level 将其放到 layer L_k，其他 check nodes 放到最后 layer。
- 另测试 ZTE 提出的 structured RCP-LDPC mother code：length 2080、rate 0.5，punctured rate 0.88。
- Channel: 母码实验为 AWGN；ZTE code 实验为 AWGN 和 independent fading，fading channel 的 unit channel gain。
- Metric 是 BER；论文没有报告 BLER/FER。

# Method

[Direct factual extraction]

1. 在最高考虑码率下分析每个 punctured variable node 的 recoverability level 和 survived check node。
2. 按 level 将 survived check nodes 分为 L_1 到 L_K；不负责恢复 punctured variable 的 check nodes 放入 L_{K+1}。
3. 在每个 iteration 中按升序顺序处理这些 layers，使所有 punctured variables 在第一轮尽早获得恢复消息。
4. 与 conventional random layering 比较；作者还构造了 layer size 均匀和 layer size 匹配 proposed distribution 的两种 random layering。

[Evidence boundary] 论文没有在正文中给出完整的 survived-node 计算细节；这里保留作者对 k-SR 和 layering rule 的文字定义。

# Key Equations

[Direct factual extraction] recoverability 的定义可写为：

$$
\text{level}(v)=k
\quad\Longleftrightarrow\quad
v\ \text{在 conventional BP 的第 }k\text{ iteration 首次收到非零 message}.
$$

论文的层分配规则是：

$$
c_i\in L_k
\quad\text{if }c_i\text{ is the survived check node of a }k\text{-SR punctured variable},
$$

其余 check nodes 分到 L_{K+1}。这是 layer construction rule，不是新的 channel-coding parity-check equation。

# Experimental Setup

[Direct factual extraction]

| Item | Value/evidence |
|---|---|
| Mother code | Irregular LDPC, length 2000, rate 0.5 |
| Rates | 0.5, 0.6, 0.7, 0.8, 0.9 |
| Maximum iterations | 15 for BER curves |
| Main channel | AWGN |
| Additional channel | Independent fading, unit channel gain |
| Additional code | ZTE structured code, length 2080, rate 0.5, punctured rate 0.88 |
| Metrics | BER vs E_b/N_0, required E_b/N_0 at BER 10^-4 |
| Baselines | Conventional BP, random-layered BP; two random layer size constructions are nearly indistinguishable |
| Seeds/frames | Not reported |
| Zotero PDF | UL7MRCVN, 3 pages |
| Zotero annotations | None returned |

# Main Results

[Direct factual extraction]

- 母码 rate 0.9、BER=10^-4：proposed layering 相比 random layering 约有 0.7 dB E_b/N_0 gain，相比 conventional BP 约有 0.8 dB gain（Fig. 1, p. 2）。
- rate 0.9、最大迭代数从 10 到 20：最大迭代数为 10 时，proposed 相比 random 和 BP 的 gain 分别约 1.3 dB 和 1.5 dB；最大迭代数为 20 时收益降到约 0.5 dB（Fig. 2, p. 3）。
- ZTE length-2080 rate-compatible code、rate 0.88：在 AWGN 和 fading 图中 proposed layering 优于 random layering 和 conventional BP；fading channel、BER=10^-4 处的 gain 约为 1 dB 和 2 dB（Fig. 3, p. 3）。
- proposed layering 在母码和 punctured rates 上保持不变，论文认为这可降低实现复杂度（pp. 2-3）。

# Comparison With Baselines

- Conventional BP：非 layered 的基线。
- Random LBP：check nodes 随机分层，比较 layer size 均匀与匹配 proposed 的两种构造。
- Proposed LBP：依据 punctured-variable recoverability level 分层。
- [My Interpretation] gain 主要在高 puncturing fraction 和低最大迭代数时变明显；当迭代预算增大，固定 layering 的相对收益会缩小。

# Limitations

- 主要母码和 ZTE code 的统计次数、随机种子、frame stopping rule 未报告。
- 论文只给图上 BER 与 E_b/N_0 结果，没有提供 raw data 或 confidence interval。
- recoverability layer 依赖 puncturing pattern 和母码结构；不能把同一 layer mapping 直接迁移到另一个 parity-check matrix。
- ZTE fading 实验的 fading distribution 只在可读文字中说明为 independent/unit gain，缺少更完整的信道统计细节。
- 论文讨论的是 BER 和 iteration convergence，不是 5G NR 的 CB-BLER/TB-BLER 或 GPU latency。

# Authors' Claims

- 作者声称 proposed check-node layering 比 random layering 和 conventional BP 收敛更快，且在高 puncturing fraction 下 BER 增益更明显（摘要、pp. 2-3）。
- 作者声称在所有考虑 code rates 上都可保持同一 layering，从而降低实现复杂度（p. 2）。
- 作者声称 AWGN 与 fading 仿真都支持该 layering scheme（p. 3）。

# My Interpretation

- “先恢复 punctured variable”是一个可解释的 schedule objective，但 k-SR level 是基于 conventional BP 的结构属性，不一定等价于最小运行时间。
- 该论文的 BER gain 与有限迭代数强相关；如果比较足够大的 iteration cap，需要同时记录相同计算预算下的结果。
- 这个层构造可作为 5G rate-matching/puncturing schedule 的启发，但不能直接当作 NR 规范规则。

# Relation To My Research

- [[LDPC-置信传播译码]]
- [[LDPC-译码迭代次数]]
- [[LDPC-率匹配]]
- [[软判决与 LLR]]
- [[BLER 与 BER]]

# Related Papers

- [[2008-Chang-Lower-Complexity-LBP-LDPC]]：Z-LBP 通过 traversal 和中间值复用降低复杂度。
- [[2025-Jia-Dynamic-Layered-Decoding-Scheduling-LDPC]]：5G NR BG1 中按 check-node error probability 动态排序。
- [[2024-Liu-High-throughput-software-LDPC-decoder-GPU]]：layered MS 的 GPU 实现。

# Open Questions

- recoverability level 能否在 5G NR BG1/BG2、不同 RV 和不同 puncturing pattern 下高效预计算？
- proposed layering 与动态 error-probability scheduling 的组合是否会重复更新或产生不稳定顺序？
- 在相同 BER、BLER、iteration 和 memory traffic 预算下，layering gain 如何公平比较？

# Useful Citations

- Ha et al., “Layered BP Decoding for Rate-Compatible Punctured LDPC Codes,” IEEE Communications Letters, 11(5), 440-442, 2007.
- Zotero item WU5VFGGV; PDF attachment UL7MRCVN.
- DOI: https://doi.org/10.1109/LCOMM.2007.061962
