---
type: literature
title: "Lower-Complexity Layered Belief-Propagation Decoding of LDPC Codes"
authors:
  - "Yuan-Mao Chang"
  - "Andres I. Vila Casado"
  - "Mau-Chung Frank Chang"
  - "Richard D. Wesel"
year: 2008
venue: "2008 IEEE International Conference on Communications"
doi: "10.1109/ICC.2008.225"
url: "http://ieeexplore.ieee.org/document/4533261/"
zotero-key: "HTUEV386"
zotero-attachment-key: "PX3SYPZG"
evidence: primary
tags:
  - topic/ldpc
  - process/decoding
  - process/scheduling
  - process/parallelism
  - metric/fer
status: read
---

# Research Problem

[Direct factual extraction] 论文提出 Zigzag Layered Belief Propagation（Z-LBP），解决 high-rate、small-to-medium blocklength QC-LDPC 中传统 C-LBP 无法保持部分并行 sequential behavior 的问题，同时减少每个 iteration 的 check-node message computation。

# Motivation

[Authors' Claims] 作者指出 QC-LDPC 的 circulant 结构可支持部分并行，LBP 比 flooding 收敛更快；但高码率短中码长的 parity-check sub-matrix 含多条 cyclic-shift diagonal，部分并行 C-LBP 会退化成 flooding（pp. 1-3）。

[My Interpretation] Z-LBP 的核心不是改变 BP 的固定点，而是改变 variable-node traversal 方向和中间值复用方式，使“最新消息”和“并行存取”同时尽量保留。

# System Model

[Direct factual extraction]

- QC-LDPC parity-check matrix 由 p x p circulant sub-matrices 构成；消息在 Tanner graph 的 variable/check nodes 之间传递。
- Check-node message 使用 log-domain SPA 的 phi 运算；Z-LBP 通过 forward/backward intermediate values 分布式地计算同一 check node 的所有 C2V messages。
- Main code: IEEE 802.11n blocklength 1944、rate 1/2、check-node degrees 7/8；sub-matrix size 54x54。
- High-rate partial-parallel case: IEEE 802.15.3c blocklength 1440、rate 14/15、check-node degree 45、15 个 sub-matrices。
- Channel: AWGN。E_b/N_0=1.75 dB 用于 802.11n rate-1/2 迭代/FER 曲线；high-rate 802.15.3c 迭代图使用 E_b/N_0=6.0 dB。
- Metric 是 FER；论文没有 BER/BLER 曲线。

# Method

[Direct factual extraction]

1. 初始化所有 C2V message 为 0，V2C message 为 channel information，并建立每个 CN 的 forward values。
2. 奇数 iteration 以反向顺序更新 variable nodes，偶数 iteration 以正向顺序更新。
3. 对当前 variable node，利用对应 CN 的 forward/backward values 生成全部 C2V messages，再生成 V2C messages。
4. 奇数 iteration 更新 backward intermediate，偶数 iteration 更新 forward intermediate；因此不必同时保存两套完整 intermediate。
5. 对含多条 shift diagonals 的高码率 QC-LDPC，按 sub-matrix column 更新并预计算必要的 forward/backward values，以避免 memory access conflict。

# Key Equations

[Direct factual extraction] 论文 p. 2 给出的 check-node log-domain update 为：

$$
m_{c_i\to v_j}
=
\left(
\prod_{v_b\in N(c_i)\setminus v_j}
\operatorname{sgn}(m_{v_b\to c_i})
\right)
\phi^{-1}
\left(
\sum_{v_b\in N(c_i)\setminus v_j}
\phi(|m_{v_b\to c_i}|)
\right),
$$

其中：

$$
\phi(x)=-\log\tanh\frac{x}{2}.
$$

Soft-XOR operator 定义为：

$$
x\otimes y=\phi^{-1}\left(\phi(|x|)+\phi(|y|)\right),
$$

并结合输入符号恢复 signed message。

对 degree d_c 的 check node，论文给出的 Soft-XOR 数量为：

| Schedule | Soft-XORs for all C2V messages |
|---|---:|
| Flooding / C-LBP | 3(d_c-2) |
| V-LBP | d_c(d_c-2) |
| Z-LBP | 2(d_c-2) |

Z-LBP 还把 memory 从 flooding 的约 2N_E intermediate values 降为约 N_E（p. 3）；这里 N_E 是 Tanner graph edge count。

# Experimental Setup

[Direct factual extraction]

| Item | Value/evidence |
|---|---|
| Main code | IEEE 802.11n, N=1944, rate 1/2, sub-matrix 54x54 |
| High-rate code | IEEE 802.15.3c, N=1440, rate 14/15, d_c=45, 15 sub-matrices |
| Channel | AWGN |
| SNR | E_b/N_0=1.75 dB for 802.11n; E_b/N_0=6.0 dB for high-rate partial-parallel figures |
| Metrics | FER vs iterations, FER vs E_b/N_0, Soft-XOR operation count |
| Baselines | Flooding, C-LBP, V-LBP, Z-LBP |
| Seeds/frames | Not reported |
| Zotero PDF | PX3SYPZG, 6 pages |
| Zotero annotations | None returned |

# Main Results

[Direct factual extraction]

- 802.11n rate-1/2、固定 E_b/N_0=1.75 dB：Z-LBP 的 FER 收敛比 flooding 快；50-iteration Z-LBP 的复杂度约等于 33-iteration flooding/C-LBP。
- 在同一 setting，Z-LBP 的性能比 flooding 好约 0.15 dB，与 C-LBP 基本无差异；相对于 V-LBP，论文报告约 0.2 dB coding gain（p. 4）。
- 对 rate-1/2、check degree 7/8，Z-LBP 的 Soft-XOR 复杂度约比 V-LBP 低 3.5 倍，按 operation count 衡量的 convergence speed 约比 V-LBP 快 2.5 倍。
- IEEE 802.15.3c rate-14/15 部分并行 setting：Z-LBP 每个 CN 约 114 Soft-XORs，V-LBP 1935，flooding 129；Z-LBP 在 50 iterations 下比 flooding 约快 0.125 dB，比 V-LBP 约好 0.5 dB（pp. 5-6）。
- 这些结果均为 FER，不是 BER/BLER。

# Comparison With Baselines

- Flooding：高并行，但使用同一轮的旧信息。
- C-LBP：check-node-centric layered schedule；在高码率单 sub-matrix-row 结构下，部分并行实现会退化为 flooding。
- V-LBP：variable-node-centric layered schedule，消息计算较多。
- Z-LBP：保留 sequential traversal，同时用 forward/backward reuse 减少 C2V computation。
- [My Interpretation] Soft-XOR 数量是论文的代理复杂度；它没有直接测量硬件 wall-clock、memory bandwidth 或 energy。

# Limitations

- 论文的高率部分针对特定 QC-LDPC 结构；不应外推到任意非 QC 或多层冲突结构。
- 部分并行 Z-LBP 为预计算 forward/backward values，因而不完全使用每一步的最新信息；论文认为性能影响不显著，但没有统一硬件 benchmark。
- 主要结果使用旧的 802.11n/802.15.3c 码和有限 fixed SNR 点，缺少 5G NR BG1/BG2、LLR quantization、seed 和统计规则。
- Soft-XOR operation count 不能直接替代具体 GPU/ASIC 的周期数和功耗。

# Authors' Claims

- 作者声称 Z-LBP 在高率短中码长 QC-LDPC 上仍可部分并行，并比 flooding/C-LBP/V-LBP 需要更少 check-node operations（摘要、pp. 3-6）。
- 作者声称 Z-LBP 保持 LBP 的更快收敛和更低 FER，同时降低每 iteration complexity（摘要、结论）。
- 作者声称当 sub-matrix 每行/列最多一个 1 时，Z-LBP 的性能与 C-LBP 相同；在多 diagonal 高率结构中，C-LBP 的部分并行实现退化为 flooding（pp. 5-6）。

# My Interpretation

- Z-LBP 的 operation reduction 与 sequential information reuse 是耦合的；只比较 iteration 数会低估它相对于 flooding 的收益，应该同时比较 Soft-XOR 或真实 cycle count。
- 论文报告的 dB gain 是固定码、固定迭代/复杂度匹配下的图上结果，不能直接当成普遍 coding gain。
- 对 5G NR，需要重新确认 base graph 的层冲突、lifting factor 和 row degree 是否满足同样的 memory-access 假设。

# Relation To My Research

- [[QC-LDPC 结构]]
- [[LDPC-置信传播译码]]
- [[LDPC-Min-Sum 译码]]
- [[LDPC-译码迭代次数]]
- [[软判决与 LLR]]

# Related Papers

- [[2007-Casado-Informed-Dynamic-Scheduling-LDPC]]：informed residual schedule，比较另一种顺序选择。
- [[2024-Liu-High-throughput-software-LDPC-decoder-GPU]]：在 GPU memory hierarchy 上实现 layered MS。
- [[2007-Ha-Layered-BP-Rate-Compatible-Punctured-LDPC]]：punctured LDPC 的 layering 设计。

# Open Questions

- 在 5G NR BG1/BG2 的真实 layer 划分下，Z-LBP 的前后向复用能否保持无冲突访问？
- 把 Soft-XOR 计数换成 GPU instruction、register pressure 和 memory transaction 后，复杂度排序是否仍成立？
- 预计算导致的 stale information 在高码率和短 blocklength 下是否会增加 error floor？

# Useful Citations

- Chang et al., “Lower-Complexity Layered Belief-Propagation Decoding of LDPC Codes,” IEEE ICC 2008, pp. 1155-1160.
- Zotero item HTUEV386; PDF attachment PX3SYPZG.
- DOI: https://doi.org/10.1109/ICC.2008.225
