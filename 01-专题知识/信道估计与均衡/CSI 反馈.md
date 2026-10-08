---
title: CSI 反馈
aliases:
  - CSI Feedback
  - 信道状态信息反馈
type: atomic
status: seed
tags:
  - domain/5G
  - domain/MIMO
  - topic/CSI
  - topic/预编码
  - stage/链路自适应
source:
  - 3GPP TS 38.214
simulation:
  - 09 仿真实验：MIMO 均衡
---

# CSI 反馈

> [!abstract] 一句话结论
> CSI 反馈将接收侧测量压缩并传递给调度或预编码实体；量化、测量噪声、反馈时延和信道时间变化会分别造成失配，必须按误差来源建模和验证。

## 反馈链路

抽象流程为：

$$
\hat{\mathbf{H}}[t_{\mathrm{meas}}]
\rightarrow \mathcal{Q}
\rightarrow \mathbf{f}_{\mathrm{CSI}}
\rightarrow \mathcal{D}
\rightarrow \hat{\mathbf{W}}[t_{\mathrm{use}}],
$$

其中 $\mathcal{Q}$ 是量化或码本选择，$\mathcal{D}$ 是调度或预编码决策。真实数据使用的等效信道为：

$$
\mathbf{H}_{\mathrm{eff}}[t_{\mathrm{use}}]
=\mathbf{H}[t_{\mathrm{use}}]
\hat{\mathbf{W}}[t_{\mathrm{meas}}].
$$

即使 $\hat{\mathbf{H}}[t_{\mathrm{meas}}]$ 完全准确，时间差：

$$
\Delta t=t_{\mathrm{use}}-t_{\mathrm{meas}}
$$

也可导致预编码失配。

## 误差分解

反馈测试应将下列因素单独冻结或扫描：

- 测量与估计误差。
- 码本或向量量化误差。
- 反馈传输延迟与处理延迟。
- 反馈丢失、版本不一致和过期状态。
- 预编码应用时的端口/层域转换错误。

将它们都放入一个手工设定的“CSI 误差方差”会掩盖不同机制和可优化位置。

## 与其他概念的关系

- 前置：[[CSI-RS]]通常提供下行 CSI 测量；[[05 MIMO 信道估计]]定义端口域与层域的转换。
- 后续：预编码改变[[MIMO 信道矩阵条件数]]和层域 CSI，继而影响[[ZF 均衡]]、[[MMSE 均衡]]与 BLER。
- 对比：[[SRS]]可提供上行探测；其用于下行时需要额外的互易和射频校准假设。
- 指标：除反馈比特数外，应报告波束增益损失、最差层 SINR、CSI 年龄、吞吐量和 BLER。

## 待验证问题

- [ ] 固定真实信道与测量 CSI，独立扫描量化比特数和反馈时延，比较预编码增益与 BLER。
- [ ] 固定平均 NMSE，比较白化 CSI 误差、相关 CSI 误差与完全过期 CSI 对空间层间干扰的影响。
- [ ] 对每个反馈记录测量时间、使用时间、配置版本和码本版本，注入版本错配验证接收机状态检查。
- [ ] 在 TDD 互易预编码实验中分离传播互易、射频校准和时间老化三个条件。

## 证据与仿真

- 规范入口：[[3GPP TS 38.214｜Physical layer procedures for data]]。
- 关联笔记：[[CSI-RS]]、[[05 MIMO 信道估计]]。
- 实验入口：[[09 仿真实验：MIMO 均衡]]。