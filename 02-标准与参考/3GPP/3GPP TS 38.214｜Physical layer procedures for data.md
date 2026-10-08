---
title: 3GPP TS 38.214｜Physical layer procedures for data
aliases:
  - 3GPP 38.214
  - NR 物理层数据过程
  - TS 38.214 数据过程
type: reference
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - evidence/3gpp
  - topic/data-procedure
  - channel/dl-sch
  - channel/ul-sch
  - stage/link-adaptation
source:
  - 3GPP TS 38.214
related:
  - 3GPP TS 38.211
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TR 38.901
---

# 3GPP TS 38.214｜Physical layer procedures for data

> [!abstract] 标准职责
> TS 38.214 规定 NR 物理层数据过程，包括 PDSCH/PUSCH 的传输、MCS、传输块大小、资源分配、HARQ、CSI 反馈和链路自适应相关过程，是把 DL-SCH/UL-SCH 编码输出与实际数据调度和性能目标连接起来的主要标准入口。

## 阅读定位

38.214 重点回答“数据使用什么资源、调制和编码配置以及传输过程发送”。它与其他标准的职责边界为：

- CRC、LDPC、Polar、码块分段和率匹配：[[3GPP TS 38.212｜Multiplexing and channel coding]]。
- PDSCH/PUSCH 调制、层映射和 RE 映射：[[3GPP TS 38.211｜Physical channels and modulation]]。
- DCI 监测、PUCCH 和控制反馈时序：[[3GPP TS 38.213｜Physical layer procedures for control]]。
- TDL/CDL 信道参数和空间传播模型：[[3GPP TR 38.901｜Channel model]]。

## 调度参数到编码参数的闭包

一次数据传输应沿下面的依赖关系计算，不能把其中某个长度当作独立输入：

```text
资源分配、层数和符号
  ↓
可用 RE 与调制阶数
  ↓
目标传输比特数 E
  ↓
TBS、CRC 和 LDPC 码块参数
  ↓
率匹配、物理映射和接收端逆过程
```

建议为每次传输保存 `resource_snapshot`，包括 BWP、PRB、符号、DM-RS/PTRS 占用、层数和调制阶数。随后保存 `coding_snapshot`，包括 TBS、CRC、码块数、BG、$Z$、$E$ 和 RV。两份快照必须能相互推导和交叉检查。

在不代替标准 TBS 表格的前提下，可用资源预算关系检查数量级：

$$
N_{RE,data}
=N_{RE,total}-N_{RE,DMRS}-N_{RE,PTRS}-N_{RE,reserved}
$$

$$
N_{coded,bits}
\approx N_{RE,data}Q_mN_{layers}
$$

这里 $Q_m$ 是每个调制符号携带的比特数。实际可用 RE、层映射、频域资源、符号集合、UCI 复用和标准取整规则必须使用对应条款精确计算；上式只用于发现明显的资源或数量级错误。

## 主要覆盖范围

| 主题 | 要记录的问题 | 关联笔记 |
|---|---|---|
| PDSCH | 下行数据资源、层数、MCS 和 TB 大小 | [[NR-DL-SCH 编码链]] |
| PUSCH | 上行数据资源、MCS、UL-SCH 与 UCI 复用 | [[NR-UL-SCH 编码链]]、[[NR-UCI 编码链]] |
| MCS | 调制阶数和目标码率索引 | [[编码增益]]、[[BLER 与 BER]] |
| TBS | 传输块大小和资源分配关系 | [[NR-DL-SCH 编码链]]、[[NR-UL-SCH 编码链]] |
| HARQ | 冗余版本、重传与软合并接口 | [[LDPC-率匹配]] |
| CSI | 测量、反馈和链路自适应输入 | [[02 参考信号与导频设计]] |
| 预编码/层 | MIMO 传输和等效信道配置 | [[05 MIMO 信道估计]]、[[09 仿真实验：MIMO 均衡]] |

## 数据链路闭环

```text
DCI 调度和配置
    ↓
资源、层数、MCS、RV 和传输块大小
    ↓
DL-SCH/UL-SCH CRC 与 LDPC 编码
    ↓
率匹配、扰码和调制
    ↓
PDSCH/PUSCH 物理映射
    ↓
信道估计、均衡、软解调和逆率匹配
    ↓
LDPC 译码与 TB-CRC
    ↓
HARQ 反馈和链路自适应更新
```

调度参数必须在发送端编码器、物理映射器、接收端逆率匹配器和译码器之间保持一致。仅改变 MCS 而不重新计算 TBS、$E$、码率和资源，不构成有效的 MCS 对照实验。

## 单次传输参数快照

建议将一次 PDSCH/PUSCH 传输抽象为：

$$
\mathcal{T}=(R_{alloc},\,Q_m,\,\nu,\,MCS,\,TBS,\,RV,\,N_{layers},\,CSI)
$$

其中 $R_{alloc}$ 是资源分配，$Q_m$ 是调制阶数，$\nu$ 是层数。该快照同时用于发送端、接收端和实验日志，避免发送端使用旧 TBS、接收端使用新 RV 的隐性状态错配。

## MCS、码率与 TBS

MCS 通常共同决定调制阶数和目标码率；资源分配、层数和 OFDM 符号数量进一步决定可用传输比特数和 TBS。研究编码性能时应区分：

- 调制阶数变化造成的星座距离变化。
- 码率变化造成的纠错冗余变化。
- 资源数量变化造成的能量和吞吐量变化。
- 传输块长度变化造成的有限块长效应。

不能把一个 MCS 索引直接等同于唯一的 LDPC 码率或唯一的 BLER。

若资源和层数固定，调制和有效码率可用一个近似频谱效率表示：

$$
\eta_{eff}
\approx Q_m R\,N_{layers}
\frac{N_{RE,data}}{N_{RE,total}}
$$

其中 $R$ 是编码率近似值。该关系不是标准 MCS 表的替代，而是用于解释为什么相同 MCS 索引在资源、DM-RS 开销、层数和 TBS 不同的条件下不能直接比较 BLER。

MCS 对照实验至少有两种口径：

- 固定资源，改变 MCS，观察 TBS、码率、调制和 BLER 的联合变化。
- 固定 TBS 或有效码率，改变资源和调制，比较能量、吞吐量和有限块长影响。

两种实验回答不同问题，不能放在同一张曲线中而不标注固定量。

## HARQ 与冗余版本

重传过程通过 RV 和率匹配从 LDPC 母码字选择不同观测，接收端在母码字坐标上合并 LLR：

$$
L_{combined}(i)=
\sum_{t=1}^{T}L_t(i)
$$

这里的索引对齐由 38.212 率匹配规则确定，重传时的信道、功率和 LLR 标定还需要符合具体过程。比较 HARQ 性能时要记录：

- 初传和各次重传的 RV。
- 每次传输的资源、MCS 和信道实现。
- 软合并前后的 LLR。
- TB-CRC 和最终确认状态。

软合并应在母码坐标上执行：

```text
每次传输 LLR
  ↓
按本次 RV 逆率匹配
  ↓
对齐到相同 LDPC 母码坐标
  ↓
与 HARQ 缓冲区累加
  ↓
LDPC 译码与 CB/TB-CRC
```

如果不同传输使用了不同 MCS、码块长度或不兼容的编码参数，不能直接把它们当作同一个软缓冲区累加；应按适用过程重新确认坐标和状态。

在软合并前，两个传输必须满足相同母码坐标解释。设第 $t$ 次传输的逆率匹配映射为 $R_t^{-1}$，则：

$$
\mathbf{L}_{mother}^{(t)}
=R_t^{-1}\left(\mathbf{L}_{physical}^{(t)}\right),
\qquad
\mathbf{L}_{HARQ}
=\sum_{t=1}^{T}\mathbf{L}_{mother}^{(t)}
$$

只有在 $R_t^{-1}$ 的码块划分、基图、提升因子、filler、RV 和 LLR 标定兼容时，上式才有物理意义。直接对不同物理资源位置的 LLR 按数组下标相加，是常见但危险的 HARQ 实现错误。

## CSI 与链路自适应

CSI 反馈用于帮助网络选择调制、码率、层数、预编码或资源。信道估计误差会传递到 CSI、MCS 和最终 BLER，因此仿真应区分：

- 理想 CSI 调度。
- 有估计误差的 CSI 调度。
- CSI 过期、量化或反馈延迟。
- 选定 MCS 后的实际译码 BLER。

把理想 CSI 下的 MCS 性能直接推广到有误差的闭环调度，会高估系统可靠性。

可以将调度选择写成：

$$
(MCS,\,N_{layers},\,\mathbf{W})
=\mathcal{S}(\hat{\mathrm{CSI}},\,\mathrm{buffer},\,\mathrm{resource})
$$

其中 $\hat{\mathrm{CSI}}$ 是带估计误差、量化和反馈延迟的 CSI。实际有效信道为：

$$
\mathbf{H}_{eff}
=\mathbf{H}_{prop}\mathbf{W},
\qquad
\mathrm{BLER}=g(\mathbf{H}_{eff},MCS,TBS,\mathrm{decoder},\mathrm{SNR})
$$

这说明 CSI 误差会通过调度参数和等效信道两条路径影响 BLER，不能只把 CSI 报告误差当作一个独立加性噪声。

链路自适应实验应区分：

1. CSI 测量误差。
2. CSI 反馈延迟和量化误差。
3. 调度器 MCS/层数选择误差。
4. 选定传输参数后的物理层译码误差。

每层都应记录输入和输出，否则最终 BLER 不能说明是信道估计、反馈还是译码器造成的。

## MIMO 和等效信道

数据过程中的层数和预编码决定接收端需要估计和均衡的等效信道：

$$
\mathbf{H}_{eff}[k,m]
=\mathbf{H}_{prop}[k,m]\mathbf{W}[k,m]
$$

应明确报告物理天线数、端口数、空间层数、预编码矩阵和接收机均衡算法。相同 MCS 在不同层数和条件数下可能具有不同 BLER。

对层域均衡，信道矩阵条件数是一个有用的诊断量：

$$
\kappa(\mathbf{H}_{eff})
=\frac{\sigma_{max}(\mathbf{H}_{eff})}
{\sigma_{min}(\mathbf{H}_{eff})}
$$

当 $\sigma_{min}$ 很小时，层间分离对噪声和 CSI 误差更敏感。报告 MIMO 编码性能时应同时保存 $\kappa(\mathbf{H}_{eff})$ 或奇异值统计，避免把空间条件恶化误判为 LDPC 或 MCS 本身的问题。

## 数据过程实验参数

| 参数 | 记录要求 |
|---|---|
| 载波/BWP | 频域资源、SCS 和 BWP |
| PDSCH/PUSCH | 物理信道、符号和 PRB 资源 |
| MCS | 索引、调制阶数和目标码率 |
| TBS | 有效传输块长度及 CRC 口径 |
| LDPC | BG、$Z$、码块数和率匹配长度 |
| MIMO | 天线、层数、预编码和 CSI |
| HARQ | RV、软合并、重传次数 |
| 信道 | AWGN、TDL/CDL、速度和 SNR |
| 指标 | BER、BLER、吞吐量、延迟和资源效率 |

## 常见误区

1. 38.214 的 MCS/TBS 和 38.212 的编码参数必须联动计算。
2. 同一 MCS 在不同资源、层数、信道和 CSI 条件下不保证同一 BLER。
3. HARQ 重传不能只拼接硬比特，应按母码字位置软合并。
4. ideal CSI 与实际估计 CSI 的结果不能混为一个基线。
5. 只报告译码 BLER 不报告吞吐量和重传次数，无法评价数据过程。

## 最小核验

1. 固定 PDSCH 或 PUSCH 资源、MCS、层数、RV 和信道模型。
2. 由数据过程参数计算 TBS、编码输入长度和目标输出长度。
3. 对照 38.212 完成 CRC、LDPC、率匹配和译码闭环。
4. 在理想 CSI 与估计 CSI 下分别统计 BLER、吞吐量和重传次数。
5. 改变 MCS、层数或 RV 时，确认所有相关长度和索引同步更新。
6. 对固定资源扫描 MCS，输出 TBS、$E$、码率、BLER、吞吐量和 HARQ 重传次数。
7. 对初传和多次重传保存每次 RV 逆率匹配后的母码 LLR，验证软合并坐标和数值变化。
8. 在理想 CSI、估计 CSI 和延迟 CSI 三种条件下比较 MCS 选择与实际 BLER。

## 关联标准和笔记

- 编码：[[3GPP TS 38.212｜Multiplexing and channel coding]]。
- 物理映射：[[3GPP TS 38.211｜Physical channels and modulation]]。
- 控制过程：[[3GPP TS 38.213｜Physical layer procedures for control]]。
- 信道模型：[[3GPP TR 38.901｜Channel model]]。
- 数据链：[[NR-DL-SCH 编码链]]、[[NR-UL-SCH 编码链]]。
- 性能实验：[[08 仿真实验：LS 与 MMSE]]、[[09 仿真实验：MIMO 均衡]]。
