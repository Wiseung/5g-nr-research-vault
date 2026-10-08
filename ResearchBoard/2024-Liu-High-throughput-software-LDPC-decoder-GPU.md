---
type: literature
title: "High-throughput software LDPC decoder on GPU"
authors:
  - "Zhanxian Liu"
  - "Ling Zhao"
year: 2024
venue: "EURASIP Journal on Advances in Signal Processing, 2024:91"
doi: "10.1186/s13634-024-01190-8"
url: "https://asp-eurasipjournals.springeropen.com/articles/10.1186/s13634-024-01190-8"
zotero-key: "JPQF9BWQ"
zotero-attachment-key: "FN78U9ZC"
evidence: primary
tags:
  - topic/ldpc
  - domain/5g-nr
  - process/decoding
  - process/gpu
  - metric/throughput
status: read
---

# Research Problem

[Direct factual extraction] 论文研究如何在 GPU 上实现高吞吐、可扩展的 5G NR LDPC 软件译码器。重点是降低 check-node update 的片上存储开销、减少分支/同步和内存访问瓶颈，同时保持 layered normalized Min-Sum 的译码流程。

# Motivation

[Authors' Claims] 作者认为新一代通信系统需要更高的 flexibility 和 scalability，GPU 可以提供并行吞吐，但片上 memory、global memory 和 CN update 的比较操作会限制性能（pp. 1-4）。

[My Interpretation] 这篇论文的主要贡献是实现与 memory hierarchy 的共同设计；27.63 Gbps 等结果不能脱离 GPU 型号、迭代数、是否计入 host-device transfer 和代码尺寸解读。

# System Model

[Direct factual extraction]

- 5G NR LDPC 使用由 BG1/BG2 构造的 QC parity-check matrix H；提升后矩阵为 m_b Z 乘 n_b Z。
- 论文把 BG1/BG2 的 inherent rates 写为 1/3 和 1/5，并说明通过 puncturing 可获得更高 code rates；BG1 的信息长度范围给为 500 到 8448，rate 范围为 1/3 到 8/9（p. 2）。
- Layered MS 中 C_j 是第 j 个接收 bit 的 LLR，L_j 是 layered message，R_ij 是 CN-to-VN message，U_ij 是当前 V2C message。
- Channel model: 算法说明使用 AWGN-channel LLR；论文的 BER Figure 3 未在可提取正文中给出完整数值 SNR 轴。
- MIMO、载波、带宽、天线和 CSI 条件未报告。
- 译码结果包括 hard decision；论文实验同时涉及 5G NR code 和 WiMax (1944, 972) code。

# Method

[Direct factual extraction]

1. 初始化 L_j=C_j，R_ij^(0)=0。
2. 对当前 layer 计算 U_ij=L_j-R_ij 的 V2C message。
3. 用 normalized Min-Sum 产生 C2V message，并用 L_j=U_ij+R_ij 立即写回 layered message。
4. 以 prefix/suffix 的 forward-backward 中间值计算 CN update，避免保存完整的额外中间数组。
5. 将 PCM 预取到 shared memory；短中码的 layered/C2V message 放入 shared memory，V2C、FB intermediate 和 R 尽量使用 registers；长码的 C2V message 使用 global memory。
6. 使用 loop unrolling、intra-frame parallelism 和可选 asynchronous streams；实验还报告早停配置。

# Key Equations

[Direct factual extraction] 论文 pp. 2-3 的 layered normalized Min-Sum 形式为：

$$
L_j^{(0)}=C_j,\qquad R_{ij}^{(0)}=0.
$$

$$
U_{ij}^{(t)}=L_j^{(t)}-R_{ij}^{(t-1)}.
$$

$$
R_{ij}^{(t)}
=
\alpha
\left(
\prod_{j'\in\phi(i)\setminus j}\operatorname{sgn}(U_{ij'}^{(t)})
\right)
\min_{j'\in\phi(i)\setminus j}|U_{ij'}^{(t)}|.
$$

$$
L_j^{(t)}=U_{ij}^{(t)}+R_{ij}^{(t)}.
$$

论文以 prefix minimum 和 suffix minimum 的 forward/backward 合并得到每条边所需的最小幅度。对一个 degree d_c 的 CN，文中讨论 two-minimum 方法约需 4d_c 次 comparison；FB 过程由 forward、backward 和 merging 三部分组成，并用 registers 保存不需要跨迭代保留的中间量（pp. 3-7）。

# Experimental Setup

[Direct factual extraction]

| Item | Value/evidence |
|---|---|
| Decoder | Layered normalized Min-Sum, 8-bit GPU message representation |
| GPU | RTX3070 and RTX4090 |
| GPU/compiler | CUDA toolkit 11.4 on Windows 10 |
| RTX4090 large code | Matrix 17664 x 26112, code (26112, 8448), Z=384, edges=121344, max row degree 19 |
| Other codes | Matrix 972 x 1944, Z=81; matrix 1472 x 2176, Z=32 |
| CPU comparison | Floating-point layered and flooding LDPC decoder |
| Iteration setting | Table 2 uses five layered iterations; other Table 3 comparisons include the listed iteration counts |
| Metrics | BER curve, latency, throughput, TNDC |
| Channel/SNR | AWGN is used for LLR formulation; numeric SNR range is not stated in extracted text |
| BLER/FER | Not reported as the headline metric |
| Transfer | Table 2 reports excluding and including data transfer process (DTP), with Ns=1 and Ns=3 streams |
| Seeds/data | Not reported; paper says no datasets were generated/analyzed |
| Zotero PDF | FN78U9ZC, 12 pages |
| Zotero annotations | None returned |

# Main Results

[Direct factual extraction]

- RTX4090、(26112, 8448) code、five layered iterations、excluding DTP：latency 0.484 ms，throughput 27.63 Gbps（Table 2, p. 9）。
- 同一 large-code setting including DTP：Ns=1 时 1.667 ms、8.02 Gbps；Ns=3 时 3.760 ms、10.67 Gbps（Table 2, p. 9）。
- 采用 early termination 后，论文结论报告 RTX4090 上 (1944, 972) 和 (26112, 8448) 的 throughput 分别达到 73 Gbps 和 38 Gbps，latency 小于 0.5 ms（p. 11）。这是与固定五次迭代表格不同的设置。
- Figure 3 比较了 8-bit GPU decoder 与 floating-point CPU decoder 的 BER 表现；正文没有提供曲线的逐点数值。
- Table 3 的 normalized decoding cost 和相对 works 的 speedup 为 1.18 倍到 12.4 倍，具体值依赖平台、代码、迭代数和是否 flooding。

# Comparison With Baselines

- GPU two-minimum CN update implementations：论文将其作为主要架构对照。
- CPU layered/flooding decoder：用于 BER、latency/throughput 对比。
- Previous GPU/CPU works：包括 GTX660Ti、TITAN X、GTX1080Ti、RTX2080Ti、Titan RTX 和 i7-4960HQ 等平台。
- [Direct factual extraction] 论文将与 work [6] 的 2.66 倍 throughput speedup 归因于 CN update 方法和 on-chip memory allocation；与 [7] 的最高 12.4 倍、与 [8] 的 2.18 倍和与 [9] 的 1.83 倍也是平台与实现条件下的 table comparison。
- [My Interpretation] 这些不是统一硬件、统一功耗和统一 transfer accounting 的严格算法优劣结论。

# Limitations

- headline throughput 大多不包含 DTP；应用端延迟必须查看包含 DTP 的列。
- GPU 与对照工作的型号、代码尺寸、迭代数和量化方式并不完全一致，TNDC 只能部分缓解可比性问题。
- BER 图的完整 SNR、帧数、错误数、随机种子和置信区间未报告。
- 论文报告片上存储和寄存器分配，但没有 occupancy、功耗或 energy/bit 的完整分析。
- 长码的 C2V message 需要 global memory，说明 memory pressure 仍随码长变化。

# Authors' Claims

- 作者声称 memory-reduced FB approach 可以降低 CN update 的额外 memory overhead（摘要、pp. 3-4）。
- 作者声称通过 optimized on-chip memory allocation 和并行映射，在 RTX4090 上可得到多十 Gbps throughput（摘要、pp. 9-11）。
- 作者声称 early termination 后大码在 RTX4090 上 latency 小于 0.5 ms（p. 11）。
- 以上 claims 依赖论文列出的 GPU、CUDA、量化和迭代设置，不能直接外推到其他实现。

# My Interpretation

- 对该论文而言，算法复杂度的关键瓶颈不是 Tanner graph 的渐近阶数，而是每条 CN update 的 comparison、register、shared-memory 和 global-memory 行为。
- 27.63 Gbps 与 38 Gbps 是不同停止策略下的数字；将它们混成一个结果会错误描述实验条件。
- 8-bit GPU BER 与 floating-point CPU BER 的接近程度需要从 Figure 3 逐点读取，当前不能用文字证据替代图像数据。

# Relation To My Research

- [[QC-LDPC 结构]]
- [[LDPC-基图选择]]
- [[LDPC-提升因子 Z]]
- [[LDPC-置信传播译码]]
- [[LDPC-Min-Sum 译码]]
- [[LDPC-译码迭代次数]]
- [[软判决与 LLR]]
- [[BLER 与 BER]]

# Related Papers

- [[2008-Chang-Lower-Complexity-LBP-LDPC]]：layered schedule 的低复杂度与部分并行。
- [[2025-Sy-Demystifying-5G-Polar-and-LDPC-Codes]]：5G NR LDPC 流程和译码算法综述。
- [[2007-Ha-Layered-BP-Rate-Compatible-Punctured-LDPC]]：有限迭代下的 layered schedule 设计。

# Open Questions

- 在相同 GPU、功耗、DTP accounting 和代码尺寸下，FB 与 two-minimum 的真实 energy/bit 差异是多少？
- 8-bit quantization 在低 BER/高码率 BG1 场景是否会产生 error floor？
- 如何把寄存器数、active warps、shared-memory bank conflict 和 row degree 统一纳入 decoder autotuning？
- early termination 的平均迭代分布和 BER/BLER 统计如何同时报告？

# Useful Citations

- Liu and Zhao, “High-throughput software LDPC decoder on GPU,” EURASIP Journal on Advances in Signal Processing, 2024:91, pp. 2-11.
- Zotero item JPQF9BWQ; PDF attachment FN78U9ZC.
- DOI: https://doi.org/10.1186/s13634-024-01190-8
