---
title: 3GPP TS 38.213｜Physical layer procedures for control
aliases:
  - 3GPP 38.213
  - NR 物理层控制过程
  - TS 38.213 控制过程
type: reference
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - evidence/3gpp
  - topic/control-procedure
  - channel/dci
  - channel/uci
source:
  - 3GPP TS 38.213
related:
  - 3GPP TS 38.211
  - 3GPP TS 38.212
  - 3GPP TS 38.214
---

# 3GPP TS 38.213｜Physical layer procedures for control

> [!abstract] 标准职责
> TS 38.213 规定 NR 物理层控制过程，包括控制资源、搜索空间、PDCCH/DCI 相关接收、功率控制、HARQ 反馈、PUCCH/UCI 过程以及部分测量和接收行为，是把控制信息编码结果放入实际协议过程的主要标准入口。

## 阅读定位

38.213 重点回答“终端在什么资源、什么时机、依据什么配置接收或发送控制信息”。它通常不单独定义 DCI 的 Polar 编码细节，也不替代物理信道的具体 RE 映射：

- DCI/PBCH/UCI 的 CRC、Polar 和率匹配：[[3GPP TS 38.212｜Multiplexing and channel coding]]。
- PDCCH、PUCCH、PBCH 的调制和资源映射：[[3GPP TS 38.211｜Physical channels and modulation]]。
- 数据调度、MCS 和 PDSCH/PUSCH 过程：[[3GPP TS 38.214｜Physical layer procedures for data]]。

## 控制配置的来源链

控制过程的输入通常来自多个层级，不能把所有参数写成一个静态常量：

```text
RRC 配置
    ↓
搜索空间、CORESET、PUCCH 资源和反馈规则
    ↓
MAC/物理层动态状态
    ↓
时隙、RNTI、HARQ 进程和监测候选
    ↓
38.212 编码参数与 38.211 物理资源
```

每次控制传输都应记录配置版本、当前时隙和动态状态。否则相同 DCI 或 UCI 比特在不同搜索空间、反馈时机或 HARQ 状态下可能对应不同物理过程。

可以把控制过程表示为配置、监测、候选判决和反馈状态的组合状态机：

$$
s_{t+1}
=\Phi\left(s_t,\,c_{RRC},\,c_{MAC},\,\mathbf{y}_t\right)
$$

其中 $s_t$ 包含当前时隙、HARQ 进程、RNTI 和已接收数据状态，$c_{RRC}$、$c_{MAC}$ 是配置状态，$\mathbf{y}_t$ 是当前物理观测。控制译码器输出的比特只有在状态机接受候选后，才会成为有效的协议动作。

## 主要覆盖范围

| 主题 | 要记录的问题 | 关联笔记 |
|---|---|---|
| PDCCH/CORESET | 控制资源、CORESET 和搜索空间如何配置 | [[NR-DCI 编码链]] |
| DCI 接收 | 候选、聚合等级、RNTI 和盲检测 | [[NR-DCI 编码链]] |
| PUCCH | UCI 资源、格式、时机和反馈过程 | [[NR-UCI 编码链]] |
| HARQ-ACK | ACK/NACK/DTX 的生成、时序和反馈 | [[NR-UCI 编码链]] |
| 功率控制 | PUCCH、PUSCH、SRS 等上行控制过程 | [[3GPP TS 38.214｜Physical layer procedures for data]] |
| 测量与报告 | 与控制相关的测量或报告配置 | [[02 参考信号与导频设计]] |

## DCI 盲检测链路

```text
配置的搜索空间和候选
    ↓
PDCCH 资源解映射
    ↓
信道估计、均衡和软解调
    ↓
按候选进行解扰和逆率匹配
    ↓
Polar 译码
    ↓
CRC 与 RNTI 掩码检查
    ↓
接受有效 DCI 或丢弃候选
```

盲检测的计算量不仅由 Polar 列表大小决定，还与候选数量、聚合等级、CORESET、搜索空间周期和终端监测规则有关。仿真时应区分：

- 正确候选译码失败。
- 错误候选误检。
- 未监测候选。
- CRC 通过但字段语义不合法。

可将候选监测建模为状态机：

```text
进入监测时机
    ↓
生成搜索空间候选
    ↓
逐候选解映射与 Polar 译码
    ├── 输入/资源无效：记录 invalid_candidate
    ├── CRC 失败：丢弃候选
    └── CRC 通过：检查 RNTI、格式和字段约束
    ↓
接受合法 DCI 或报告未检测到
```

`CRC pass`、`valid DCI` 和 `no detection` 是不同状态，统计时不能合并。

设搜索空间候选集合为 $\mathcal{C}_t$，对候选 $h$ 定义：

$$
q_h
=\mathbf{1}\left[
\mathrm{CRC}_{RNTI_h}(\hat{\mathbf{a}}_h)=0
\right]
$$

结合资源和字段语义后的有效候选集合为：

$$
\mathcal{C}_{valid}
=\left\{h\in\mathcal{C}_t:
q_h=1,\ h\text{ 的资源、格式和字段约束均满足}
\right\}
$$

因此：

$$
|\mathcal{C}_{valid}|=0\Rightarrow\text{未检测到有效 DCI},
\qquad
|\mathcal{C}_{valid}|\ge1\Rightarrow\text{进入协议消歧和调度处理}
$$

CRC 通过本身不是完整的控制接受条件；多个候选同时通过时还需要依据搜索空间、RNTI、格式和时序规则处理。

## UCI 与 HARQ-ACK

UCI 过程通常需要同时记录内容和时序：

```text
下行数据接收
    ↓
PDSCH 解码与 TB-CRC 判定
    ↓
生成 HARQ-ACK/NACK/DTX 状态
    ↓
根据反馈时机选择 PUCCH 或 PUSCH
    ↓
UCI 编码、率匹配和物理映射
```

ACK/NACK 语义不能等同于普通比特错误。DTX、漏检 PDCCH、PDSCH 解码失败和 UCI 发送失败可能触发不同的协议行为。

建议建立 HARQ-ACK 事件表：

| 事件 | 需要保存的状态 |
|---|---|
| PDCCH 未检测 | 搜索空间、候选和监测结果 |
| PDSCH 译码成功 | TB-CRC、HARQ 进程和反馈时机 |
| PDSCH 译码失败 | 失败原因、RV、软合并状态 |
| UCI 生成 | ACK/NACK/DTX 语义和字段顺序 |
| UCI 发送/接收 | PUCCH/PUSCH 资源、编码分支和译码状态 |

事件表有助于区分控制链失败和数据链失败，而不是只从最终 ACK 推断原因。

对 HARQ 反馈，可以将发送语义 $s$ 和接收语义 $\hat{s}$ 分离统计：

$$
P_{\mathrm{semantic\ error}}
=P(\hat{s}\ne s,\;s,\hat{s}\in\{\mathrm{ACK},\mathrm{NACK}\})
$$

$$
P_{\mathrm{DTX}}
=P(\hat{s}=\mathrm{DTX}\mid s\in\{\mathrm{ACK},\mathrm{NACK}\})
$$

ACK 被误判为 NACK 与 NACK 被误判为 ACK 的协议代价不同，DTX 也不能简单计入普通比特错误。仿真日志应保存原始数据 CRC、HARQ 进程、反馈时机、UCI 译码状态和最终语义。

## PUCCH 与 PUSCH 的控制接口

控制过程需要确定：

- UCI 的传输时机和资源。
- PUCCH format 或 PUSCH 承载方式。
- HARQ-ACK、SR、CSI 等字段的优先级。
- UCI 与 UL-SCH 的复用关系。
- 功率控制和可用资源。

这些过程决定了 [[NR-UCI 编码链]] 的输入长度和目标输出长度，但具体编码分支仍需回到 38.212。

## 功率控制与接收性能

功率控制会改变接收端的 SNR、LLR 质量和 UCI/数据之间的干扰关系。做编码性能仿真时，必须说明：

- 使用理想功率还是闭环功率控制。
- UCI 与 UL-SCH 是否共享资源和功率。
- 上行控制信道的目标接收质量。
- 噪声和干扰功率如何定义。

否则同一 Polar 或短块编码器在不同控制过程配置下的 BLER 不可直接比较。

功率控制实验还要说明 SNR 的观测位置：发射符号归一化前、信道输出端、均衡器输入端或软解调器使用的等效噪声方差。不同定义会改变 LLR 尺度，即使平均接收功率相同，译码性能也可能不同。

对使用 LLR 的控制译码，接收质量至少可抽象为：

$$
L_b=\log\frac{P(b=0\mid y)}{P(b=1\mid y)},
\qquad
\mathrm{Var}(L_b)\text{ 随有效接收质量变化}
$$

因此控制过程的功率、资源和干扰配置会通过 $L_b$ 影响 Polar、短块码或其他译码分支。不能只在发射端比较功率，而不检查均衡器输出和软解调器实际使用的噪声方差。

## 标准核验表

| 项目 | 记录内容 |
|---|---|
| 版本 | Release、版本号和日期 |
| 控制对象 | PDCCH、PUCCH、HARQ、SR、CSI 等 |
| 配置输入 | RRC/MAC/物理层相关参数 |
| 时序 | 时隙、符号、反馈和监测时机 |
| 资源 | CORESET、搜索空间、PUCCH/PUSCH 资源 |
| 编码接口 | 载荷长度、目标长度和率匹配参数 |
| 判决 | CRC、ACK/NACK/DTX 和失败状态 |
| 条款定位 | 章节、表格、图号和交叉引用 |

## 常见误区

1. 38.213 规定控制过程，不等于完整定义 PDCCH/UCI 的编码器。
2. DCI 盲检测不是只运行一次 Polar 译码，而是对配置候选执行监测和筛选。
3. ACK/NACK/DTX 必须按协议语义统计，不能只合并为 BER。
4. PUCCH 资源、搜索空间和反馈时序错误会被误判为编码器性能问题。
5. 只记录默认配置而不记录 RRC/MAC 输入，无法复现控制过程。

## 最小核验

1. 固定一个 CORESET、搜索空间、PDCCH 候选和 RNTI。
2. 记录正确候选、错误候选、聚合等级和监测时机。
3. 验证无噪声条件下正确 DCI 可通过 CRC，错误 RNTI 不通过。
4. 固定 PDSCH 解码结果，分别构造 ACK、NACK 和 DTX 的 UCI 反馈。
5. 在 AWGN 下区分 DCI BLER、UCI 语义错误和反馈时序错误。
6. 对同一 DCI 比特在不同搜索空间候选和监测时机下验证候选生成与资源解映射。
7. 对 ACK、NACK、DTX 和 PDCCH 漏检分别统计事件数、译码结果和协议后果。

## 关联标准和笔记

- 编码与率匹配：[[3GPP TS 38.212｜Multiplexing and channel coding]]。
- 物理映射：[[3GPP TS 38.211｜Physical channels and modulation]]。
- 数据过程：[[3GPP TS 38.214｜Physical layer procedures for data]]。
- DCI：[[NR-DCI 编码链]]。
- UCI：[[NR-UCI 编码链]]。
- 基础指标：[[BLER 与 BER]]、[[软判决与 LLR]]。

## 项目应用关联

- 第三方 TDD 监测与 PDCCH/PDSCH 候选解析：[[5G 定位与 TDOA｜MOC]]、[[NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]。
