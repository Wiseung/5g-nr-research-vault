---
title: LTE 参考信号与导频设计
aliases:
  - LTE CRS DM-RS SRS
  - LTE 参考信号
  - LTE 参考信号与导频设计
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - topic/参考信号
  - topic/导频设计
  - stage/导频设计
source:
  - "[[3GPP TS 36.211｜Physical channels and modulation]]"
related:
  - "[[LTE 信道估计算法]]"
  - "[[LTE OFDM 与 SC-FDMA 接收及频域均衡]]"
---

# LTE 参考信号与导频设计

> [!abstract] 一句话定义
> LTE 参考信号是接收机可以按小区、UE、端口和配置重构的已知物理层序列；CRS、PDSCH UE-specific RS（下文简称下行 DM-RS）、PUSCH DM-RS、CSI-RS 与 SRS 的观测对象和使用时机不同，不能用一个“LTE 导频”接口替代。

## 前置知识

- [[LTE 物理层与信道模型]]：资源网格、端口和 CP/波形。
- [[00 5G 信道估计与均衡前置知识#随机过程与相关函数]]：相干时间、相干带宽和插值假设。
- [[00 5G 信道估计与均衡前置知识#MIMO 与空间信道]]：端口、层和空间正交性。

## 1. 信号到任务的映射

| 信号 | 方向 | 主要用途 | 典型 CSI 结果 | 规范入口 |
|---|---|---|---|---|
| CRS | 下行 | 小区级参考、传统 PDSCH 解调、测量 | 小区专用端口信道或其等效版本 | 36.211 §6.10.1 |
| PDSCH UE-specific RS / 下行 DM-RS | 下行 | 与特定 PDSCH 传输关联的解调 | 当前 PDSCH 端口/层的等效信道 | 36.211 §6.10.3 |
| PUSCH DM-RS | 上行 | PUSCH 相干解调 | 当前 UE、层和分配 PRB 的上行信道 | 36.211 §5.5.2.1 |
| PUCCH DM-RS | 上行 | PUCCH 相干解调 | PUCCH 资源对应的信道 | 36.211 §5.5.2.2 |
| SRS | 上行 | 频率选择性探测、调度和 CSI | 可供后续调度使用的上行测量 | 36.211 §5.5.3 |
| CSI-RS | 下行 | CSI 测量、反馈和空间配置 | 端口/空间测量，不等同于当前数据 DM-RS | 36.211 §6.10.5 |

“当前解调”和“未来调度”是两个不同的时间边界：DM-RS 更接近当前数据，CSI-RS/SRS 可能存在测量到使用之间的延迟。把 CSI-RS 当作当前 PDSCH 的唯一解调导频属于 `NEEDS_VERIFICATION`，必须结合传输模式和高层配置。

## 2. CRS 的资源网格特征

36.211 §6.10.1 给出 CRS 的序列和映射。对 15 kHz LTE，频域位置可抽象为：

$$
k=6m+(v+v_{shift})\bmod 6,
\qquad v_{shift}=N_{ID}^{cell}\bmod 6.
$$

符号位置 `l` 和 `v` 还取决于 CP、天线端口 `p` 以及 slot 内位置；端口 0--3 的 RE 在同一位置不能被其他端口的数据覆盖。这里的公式和端口范围是 `STANDARD`；不要用固定的“每个 PRB 四个导频”假设替代完整映射，因为 CP、端口数、MBSFN/特殊子帧和带宽边界会改变可用 RE。

CRS 估计的接收流程：

```text
由 PCI、slot、符号和端口重构 CRS 序列
        ↓
按 (k,l,p) 提取接收 RE
        ↓
相关/LS 估计
        ↓
跨频率、跨时间插值
        ↓
供 PDSCH 均衡或测量使用
```

## 3. 下行 UE-specific RS / DM-RS

36.211 §6.10.3 规定下行 UE-specific RS：

- 只在相应 PDSCH 传输占用的 PRB 上发送。
- 只有当 PDSCH 与对应天线端口/传输模式关联时，参考信号才是有效的 PDSCH 解调参考。
- 端口、序列初始化、频域移位和符号位置随传输模式与配置变化。

因此下行 DM-RS 的估计结果通常更接近 `H_eff`：

$$
Y_{DMRS}=H_{eff}X_{DMRS}+N.
$$

如果接收机把 DM-RS 的端口解释成 CRS 端口，或把非分配 PRB 的 DM-RS 外推到整个带宽，均属于坐标域错误，不是插值器可以修复的问题。

## 4. 上行 PUSCH DM-RS

PUSCH DM-RS 在每个相关的 PUSCH 资源上生成并映射。对传统 15 kHz 配置，主 DM-RS 的 slot 内符号位置为：

| CP | 典型主 DM-RS 符号 `l` | 证据 |
|---|---:|---|
| normal CP | 3 | 36.211 §5.5.2.1.2 `STANDARD` |
| extended CP | 2 | 36.211 §5.5.2.1.2 `STANDARD` |

它覆盖当前 PUSCH 分配的频域资源，接收端可先在 FFT 域提取对应 RE，再进行 LS/LMMSE 和频率插值。序列基于上行参考序列族、循环移位、组/序列跳变等配置；完整序列表和 DCI 字段应按目标 Release 核对。

## 5. SRS 与 CSI-RS 的用途边界

### SRS

36.211 §5.5.3 区分 basic 和 additional SRS，支持周期或非周期探测。SRS 主要回答“基站在后续调度时看到的上行频率/空间信道是什么”，并不自动等价于当前 PUSCH DM-RS。需要记录测量时间戳：

$$
\hat{\mathbf H}_{SRS}(t_0)\longrightarrow
\text{调度/预编码决策 at }t_1,
\qquad \Delta t=t_1-t_0.
$$

### CSI-RS

36.211 §6.10.5 的 CSI-RS 端口从 15 开始，端口数量、频域密度和 CDM/配置由高层信令决定。CSI-RS 可用于 CSI 测量和反馈，但在当前 PDSCH 解调中应优先使用与该 PDSCH 传输关联的 CRS 或 UE-specific RS，除非目标传输模式明确规定其他关系。

## 6. 统一观测模型

对任一已知参考符号 `X_p`，单端口观测可写成：

$$
Y_p=X_pH_p+N_p,
\qquad
\hat H_{LS,p}=\frac{Y_p}{X_p},
\quad X_p\ne0.
$$

多端口复用时，令 `S` 为参考序列/正交码矩阵：

$$
\mathbf y=\mathbf S\mathbf h+\mathbf n.
$$

端口分离前应检查 `S` 的维度、归一化和互相关；把不同端口的 RE 直接平均会把空间串扰混入 CSI。

## 7. 设计权衡

| 设计维度 | 增加参考信号的收益 | 代价或风险 |
|---|---|---|
| 时间密度 | 跟踪更快的时变信道 | 数据 RE 减少、控制开销增加 |
| 频率密度 | 减少频率选择性插值误差 | 频谱开销和功率分配变化 |
| 端口/序列正交性 | 降低端口间干扰 | 可用正交资源与实现复杂度增加 |
| 参考信号功率 | 降低 pilot LS 方差 | 总功率约束、PAPR 和数据功率变化 |
| 观测时效 | 减小 CSI 老化 | 反馈/调度时延和信令开销增加 |

导频开销可用简化指标表示：

$$
\eta_{pilot}=\frac{|\mathcal R_{RS}|}{|\mathcal R_{all}|},
\qquad
\eta_{data}=1-\eta_{pilot}-\eta_{reserved}.
$$

这是 `PERSONAL_NOTE` 的比较指标，不是标准定义；实验必须说明分母是整个资源网格、分配 PRB 还是有效数据 RE。

## 8. 接收机提取伪代码

```text
输入：LTE 配置、PCI/UE 标识、slot/subframe、端口、接收资源网格 Y
1. 根据参考信号类型生成 (k,l,p) 位置集合和已知序列 X
2. 校验位置不与数据/保留 RE 冲突
3. 提取 Y[k,l,p]，检查 X 非零、功率和序列长度
4. 做端口相关或逐 RE LS
5. 按时间/频率域插值到数据 RE
6. 输出 H_hat、端口/层元数据、时间戳和质量标志
```

## 与其他概念的关系

参考信号位置决定 [[LTE 信道估计算法]] 的采样几何；估计结果进入 [[LTE OFDM 与 SC-FDMA 接收及频域均衡]]；SRS/CSI-RS 的测量时效还会影响 [[LTE MIMO 信道估计与均衡]]。

## 待验证问题

- [ ] 目标传输模式使用 CRS 还是 UE-specific RS 作为当前 PDSCH 解调参考？
- [ ] 具体 Release 的 DM-RS/CSI-RS 配置是否包含额外端口或特殊子帧例外？

## 证据与待核验

- `STANDARD`：CRS、UE-specific RS、PUSCH DM-RS、SRS、CSI-RS 的章节和基本用途来自 36.211 V16.6.0。
- `PERSONAL_NOTE`：观测模型、开销指标、端口分离和时间戳接口沿用库内估计笔记。
- `NEEDS_EXTERNAL_REFERENCE`：完整 CRS/DM-RS/CSI-RS 位置表、所有传输模式、序列跳变字段和特殊子帧例外。

## 关联笔记

- [[LTE 信道估计算法]]
- [[LTE OFDM 与 SC-FDMA 接收及频域均衡]]
- [[LTE MIMO 信道估计与均衡]]
- [[LTE 物理层与信道模型]]
- [[3GPP TS 36.211｜Physical channels and modulation]]
