---
title: NR-DL-SCH 编码链
aliases:
  - 5G NR 下行共享信道编码链
  - DL-SCH LDPC 编码流程
type: atomic
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - channel/dl-sch
  - code/ldpc
  - process/encoding
  - process/decoding
  - evidence/3gpp
source:
  - 3GPP TS 38.212
  - 3GPP TS 38.211
  - 3GPP TS 38.214
simulation:
  - 仿真-无噪声编解码闭环
  - 仿真-LDPC-AWGN-BLER
---

# NR-DL-SCH 编码链

> [!abstract] 一句话结论
> DL-SCH 承载下行数据信息，典型物理链路是传输块 CRC、码块分段、LDPC 编码、率匹配、扰码、调制和 PDSCH 映射；接收端按相反方向恢复软信息并进行 LDPC 译码和 CRC 检查。

## 适用范围

DL-SCH 是下行共享信道的传输信道，经过物理层处理后通常映射到 PDSCH。它承载来自 MAC 层的下行传输块，具体传输块大小、调制阶数、码率和资源数量由调度和物理层过程共同确定。

本笔记关注 LDPC 数据链路，不展开 PDSCH DM-RS、资源网格分配和波形生成的全部细节。相关物理映射应结合 [[3GPP TS 38.211｜Physical channels and modulation]] 和 [[3GPP TS 38.214｜Physical layer procedures for data]] 阅读。

## 从调度资源到 $E$

在不考虑具体标准边界的理想记账下，PDSCH 可用编码比特数可近似写成：

$$
E_{\mathrm{ideal}}
=Q_m\,\nu\,N_{\mathrm{RE,data}}
$$

其中 $Q_m=\log_2M$ 是每个调制符号的编码比特数，$\nu$ 是传输层数，$N_{\mathrm{RE,data}}$ 是扣除 DM-RS、PTRS、控制区域和其他不可用于数据的 RE 后的可用数据 RE 数量。实际规范流程还会受到资源粒度、层映射、码块分配和率匹配规则约束，因此该式用于建立数量级关系，不能替代 38.214 的 TBS 和资源计算。

调度参数对编码链的影响可以写成：

$$
(N_{\mathrm{PRB}},N_{\mathrm{sym}},Q_m,\nu)
\longrightarrow N_{\mathrm{RE,data}}
\longrightarrow E
\longrightarrow (A,C,\mathrm{BG},Z,E_r)
$$

因此，$A$ 和 $E$ 不是可以任意独立指定的两个物理链路变量。若要独立研究码率，应明确这是抽象编码仿真，还是符合 PDSCH 调度约束的端到端仿真。

## 发送端流程

```text
MAC 传输块 A
    ↓
传输块 CRC 附加
    ↓
码块分段与必要的 CB-CRC 附加
    ↓
LDPC 基图选择
    ↓
选择提升因子 Z 并插入 filler bits
    ↓
LDPC 编码
    ↓
每个码块率匹配到 E_r
    ↓
码块级联得到 E 个比特
    ↓
PDSCH 数据扰码
    ↓
调制
    ↓
PDSCH 资源映射与发送
```

上图中每个阶段的输入输出长度都必须由参数明确约束。尤其要区分：

- $A$：传输块中的有效输入比特数。
- $B$：传输块 CRC 附加后的比特数。
- $C$：码块数量。
- $E_r$：第 $r$ 个码块的率匹配输出长度。
- $E=\sum_r E_r$：级联后的总传输比特数。
- $Z$：LDPC 提升因子，不是目标传输长度。

## 接收端流程

```text
PDSCH 解映射
    ↓
信道估计、均衡和软解调
    ↓
PDSCH 解扰
    ↓
按码块分离 LLR
    ↓
逆率匹配与软信息合并
    ↓
LDPC 译码
    ↓
移除 filler bits 和 CB-CRC
    ↓
码块级联
    ↓
传输块 CRC 检查
    ↓
交付 MAC 或触发 HARQ 反馈
```

接收端不能只对硬判决比特做译码。LDPC 译码器的输入通常是软信息 LLR；率匹配中被打孔的位置以无信息软值表示，重复发送的位置要按照标准索引合并软信息。

## CRC 与码块分段

传输块先附加 TB-CRC。若长度超过 LDPC 单个码块能够处理的范围，则进行分段，并为各码块附加 CB-CRC。每个码块独立经过 LDPC 编码和率匹配，接收端完成码块译码后再重新级联并检查传输块 CRC。

TB-CRC 与 CB-CRC 的用途不同：

| 检查对象 | 作用 |
|---|---|
| CB-CRC | 判断单个码块是否恢复正确 |
| TB-CRC | 判断整个下行传输块是否可交付 |
| HARQ 状态 | 根据传输块可靠性形成 ACK/NACK 等反馈 |

具体 CRC 类型、长度和比特顺序必须以适用版本的 TS 38.212 为准。

## 基图、提升因子和率匹配的关系

基图选择决定 LDPC 的宏观结构，提升因子 $Z$ 将基图展开为实际校验矩阵，率匹配再按照资源分配得到每个码块的发送长度 $E_r$：

```text
码块长度 K'
    ↓
BG1 或 BG2
    ↓
允许集合中的 Z
    ↓
QC-LDPC 校验矩阵
    ↓
母码字
    ↓
RV 相关的率匹配
    ↓
E_r 个发送比特
```

$K'$、$Z$、母码字长度和 $E_r$ 必须同时一致。只改变率匹配输出长度而不重新计算对应的接收索引，会导致译码失败或码块边界错位。

## 调度参数到编码参数

DL-SCH 编码器通常不是独立决定所有参数，而是接收数据过程提供的调度结果。一个可复现的参数依赖关系是：

```text
时隙、BWP、PRB 和 OFDM 符号资源
    ↓
层数、调制阶数、DM-RS 开销和可用 RE 数
    ↓
目标传输比特数 E 与传输块大小 A
    ↓
TB-CRC、码块分段、BG 和 Z
    ↓
每个码块的 E_r、RV 和率匹配索引
```

因此，编码链中的 $A$ 和 $E$ 不能随意独立设置。改变 PRB 数、层数、调制阶数或 DM-RS 开销，通常会改变可用资源和 TBS，进而改变分段、码率和率匹配结果。

## 长度账本

建议为每个传输块保存一行长度账本：

| 阶段 | 变量 | 应满足的关系 |
|---|---|---|
| MAC 输入 | $A$ | 原始传输块长度 |
| TB-CRC 后 | $B$ | $B=A+L_{TB}$ |
| 分段后 | $C,K',F$ | $C K'=B+C L_{CB}+F$ |
| LDPC 母码 | $N$ | 由 BG、$Z$ 和码结构决定 |
| 率匹配后 | $E_r$ | 第 $r$ 个码块的目标输出长度 |
| 级联后 | $E$ | $E=\sum_r E_r$ |
| 调制输入 | $E$ | $E$ 必须能按调制阶数和层数分配 |

如果某一行无法闭合，应先停止链路，输出中间参数，而不是继续执行到译码器再用 BLER 反推原因。

## 传输块、码块和物理信道的边界

一个传输块可能包含多个 LDPC 码块，而一个 PDSCH 传输通常把多个码块的率匹配输出级联后统一扰码和调制。接收端必须维护三种边界：

- **传输块边界**：TB-CRC 覆盖范围和 HARQ 判决范围。
- **码块边界**：CB-CRC、LDPC 图和逆率匹配缓冲区范围。
- **物理映射边界**：数据 RE、层、调制符号和码比特的排列。

边界混淆时，常见现象是单个码块看似能译码，但 TB-CRC 始终失败，或者只有改变 PDSCH 资源数量时才出现错位。

## 接收机状态机

可将接收端的处理状态记录为：

```text
resource_invalid
    ↓
llr_ready
    ↓
codeblock_demultiplexed
    ↓
ldpc_decoded
    ↓
cb_crc_checked
    ↓
tb_reassembled
    ↓
tb_crc_pass / tb_crc_fail
    ↓
ACK / NACK 或丢弃
```

`resource_invalid`、`llr_invalid`、`ldpc_not_converged`、`cb_crc_fail` 和 `tb_crc_fail` 应分开统计。它们都可能最终表现为 TB-BLER，但修复路径完全不同。

可以把接收状态看作逐级收缩候选集合的过程：

$$
\mathcal{Y}
\supseteq\mathcal{Y}_{\mathrm{resource}}
\supseteq\mathcal{Y}_{\mathrm{LLR}}
\supseteq\mathcal{Y}_{\mathrm{LDPC}}
\supseteq\mathcal{Y}_{\mathrm{CB\text{-}CRC}}
\supseteq\mathcal{Y}_{\mathrm{TB\text{-}CRC}}
$$

每一层都应有自己的失败计数。这样可以区分“没有得到合法资源输入”“得到软信息但没有收敛”和“得到合法码字但 CRC 不通过”等不同故障。

## HARQ 软合并的可靠性

对第 $t$ 次传输，先用该次 RV 和率匹配索引得到母码字坐标上的 LLR $L_t(i)$，再进行合并：

$$
L_{\mathrm{HARQ}}(i)
=\sum_{t=1}^{T}w_t(i)L_t(i)
$$

理想标定时 $w_t(i)$ 可取 1；当不同传输的噪声方差、均衡增益或量化尺度不同，应使用与可信度一致的权重。直接拼接硬判决比特无法利用互补 RV 的可靠性。

若各次观测条件独立且 LLR 已按真实噪声方差标定，联合证据的对数似然比满足：

$$
L(i\mid y_1,\ldots,y_T)=\sum_{t=1}^{T}L_t(i)
$$

若第 $t$ 次观测使用了未标定的软值 $\widetilde L_t(i)=s_tL_t(i)$，则 $w_t(i)$ 必须反映各次观测的相对可信度，否则软合并可能比单次传输更差。

## 建议的 DL-SCH 实验矩阵

| 实验 | 固定项 | 变化项 | 主要观察 |
|---|---|---|---|
| 结构闭环 | 无噪声、固定资源 | 单码块/多码块 | 长度、CRC 和重组 |
| 率匹配 | 固定码图和信道 | RV、$E$ | 逆率匹配与软合并 |
| 信道性能 | 固定链路参数 | SNR | CB-BLER/TB-BLER |
| 调度影响 | 固定 SNR | MCS、PRB、层数 | TBS、码率和吞吐量 |
| CSI 对照 | 固定调度 | 理想/估计 CSI | LLR 质量和译码损失 |

## HARQ 与冗余版本

同一个传输块的重传可以使用不同冗余版本（RV）。RV 改变率匹配从循环缓冲区取出的起始位置，使不同次传输暴露出母码字的不同部分。接收端按相同 RV 恢复 LLR 并进行软合并，然后再译码。

因此，第一次传输和重传不能简单地把硬判决比特拼接起来。正确的 HARQ 合并对象是对应母码字位置上的软信息。

## 端到端接口检查

| 接口 | 必须检查的内容 |
|---|---|
| MAC 到编码器 | $A$、传输块内容和 CRC 输入范围 |
| 分段到 LDPC | $C$、$K'$、CB-CRC 和 filler bits |
| 编码到率匹配 | BG、$Z$、母码字长度和 RV |
| 率匹配到调制 | 总比特数 $E$ 与调制输入长度 |
| 软解调到译码器 | LLR 符号、幅度、顺序和噪声方差 |
| 译码到 MAC | TB-CRC、译码失败状态和 HARQ 结果 |

## 常见误区

1. DL-SCH 是传输信道，PDSCH 是承载它的物理信道，二者名称不能互换。
2. 率匹配输出长度 $E$ 不等于 LDPC 母码字长度。
3. 只验证无噪声编码输出，不能验证 RV、软合并和 LLR 接口。
4. TB-CRC 通过不表示每个中间码块都经过了独立的 CB-CRC 检查。
5. 不能用下行和上行的资源参数直接互换来构造编码链；UL-SCH 还涉及 PUSCH 上的 UCI 复用。
6. `A`、`B`、`K'` 和 `E` 都是长度，但它们对应不同处理阶段，不能用一个变量在代码中复用。
7. TB-CRC 失败不一定意味着 LDPC 图错误，也可能来自物理资源、LLR 标定或码块重组错误。

## 最小验证

1. 固定一个传输块和随机种子，记录 $A$、$B$、$C$、$Z$、$E_r$ 和 $E$。
2. 在无噪声条件下完成发送端和接收端全链路，检查输出与输入一致。
3. 检查每个码块的率匹配长度和总级联长度。
4. 在 AWGN 下扫描 SNR，分别记录 CB-CRC、TB-CRC、BER 和 BLER。
5. 改变 RV 并进行软合并，确认重传后性能优于只使用单次传输的对照组。
6. 保存每个码块的母码字坐标、RV 索引和 LLR 合并前后摘要，检查重复位置确实发生累加。
7. 对资源参数、MCS、层数和 DM-RS 开销各改变一次，确认 TBS、$E$ 和编码参数同步变化。

## 关联笔记

- 上位概念：[[信道编码基础]]、[[5G 信道编译码]]。
- 结构：[[LDPC-基图选择]]、[[LDPC-码块分段]]、[[LDPC-提升因子 Z]]、[[QC-LDPC 结构]]。
- 处理：[[LDPC-率匹配]]、[[LDPC-置信传播译码]]。
- 性能：[[LDPC-译码迭代次数]]、[[BLER 与 BER]]。
