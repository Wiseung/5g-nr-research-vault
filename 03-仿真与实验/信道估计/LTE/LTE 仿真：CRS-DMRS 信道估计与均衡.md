---
title: LTE 仿真：CRS-DMRS 信道估计与均衡
aliases:
  - LTE 信道估计均衡实验
type: experiment
status: NEEDS_VERIFICATION
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - stage/仿真
  - topic/信道估计
  - topic/均衡
  - status/待验证
source:
  - "[[LTE 参考信号与导频设计]]"
  - "[[LTE 信道估计算法]]"
  - "[[LTE OFDM 与 SC-FDMA 接收及频域均衡]]"
related:
  - "[[LTE 仿真：Turbo 编解码闭环]]"
---

# LTE 仿真：CRS-DMRS 信道估计与均衡

> [!warning] 状态
> 这是实验设计，不是已执行结果。运行前需写入软件版本、配置快照、随机种子、帧数和错误数；没有这些字段时不得写入性能结论。

## 目标

在相同 LTE 资源网格、信道实现和噪声定义下，比较：

1. 下行 CRS-LS + 插值。
2. 下行 PDSCH UE-specific DM-RS-LS + 局部插值。
3. PUSCH DM-RS-LS + SC-FDMA 频域均衡。
4. 理想 CSI、LS CSI 和可选 LMMSE CSI 下的 ZF/MMSE。

## 固定参数快照

| 类别 | 必填字段 |
|---|---|
| 标准 | 36.211/36.213/36.214 版本、传输模式 |
| 波形 | FDD/TDD、15 kHz、normal/extended CP、FFT、采样率 |
| 资源 | 带宽、PRB、slot/subframe、频率跳变 |
| RS | CRS/DM-RS 类型、端口、PCI、DM-RS 配置、SRS/CSI-RS 开关 |
| 信道 | AWGN/TDL、时延扩展、多普勒、CFO/相位噪声 |
| 估计器 | LS/LMMSE、插值方向、协方差、边界策略 |
| 均衡器 | ZF/MMSE、正则化、弱信道阈值、MIMO 层数 |
| 统计 | seed、帧数、停止条件、BER/BLER 错误数 |

## 分层实验

```text
M0：单位信道、无噪声、理想 CSI
M1：频率选择性、理想 CSI
M2：CRS/DM-RS LS + 插值
M3：MIMO 条件数分桶，比较 ZF/MMSE
M4：PUSCH SC-FDMA FDE + IDFT
M5：CFO/时变/估计失配，标记单抽头失效
```

## 记录指标

- pilot RE NMSE；
- data RE NMSE；
- EVM 和后均衡有效 SINR；
- 软解调 LLR 符号/尺度检查；
- BER、CB-BLER、TB-BLER；
- 运行时间和峰值内存（如测量）。

## 结果表模板

| 场景 | RS/CSI | 估计器 | 均衡器 | SNR | pilot NMSE | data NMSE | EVM | TB-BLER | 帧/错误数 | 状态 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 待运行 | - | - | - | - | - | - | - | - | - | `NEEDS_VERIFICATION` |

## 通过条件

- [ ] 单径无噪声的 FFT/CP/RE 索引闭合。
- [ ] CRS/DM-RS 位置与 36.211 目标版本一致。
- [ ] PUSCH 在 FDE 后按分配子载波顺序 IDFT。
- [ ] ZF/MMSE 的后均衡方差进入 LLR。
- [ ] 所有曲线使用配对信道实现和相同随机策略。

## 证据边界

- `EXPERIMENT + NEEDS_VERIFICATION`：本页全部结果槽位。
- `STANDARD`：RS/波形配置应引用 36.211 条款。
- `PERSONAL_NOTE`：指标和分层设计来自库内估计/均衡实验约定。
