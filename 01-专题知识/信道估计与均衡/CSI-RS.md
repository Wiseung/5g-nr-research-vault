---
title: CSI-RS
aliases:
  - Channel-State Information Reference Signal
  - 信道状态信息参考信号
type: atomic
status: seed
tags:
  - domain/5G
  - domain/NR
  - topic/参考信号
  - topic/CSI
  - stage/导频设计
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.214
simulation:
  - 09 仿真实验：MIMO 均衡
---

# CSI-RS

> [!abstract] 一句话结论
> CSI-RS 为下行信道、端口或波束提供测量观测，典型用途是 CSI 反馈、波束管理和链路自适应；它的测量时刻与数据使用时刻可能不同，因此必须处理量化和时延造成的 CSI 老化。

## 测量链路

抽象地，UE 基于 CSI-RS 得到测量量：

$$
\mathcal{M}_{\mathrm{CSI}}
=\mathcal{Q}\left(
\hat{\mathbf{H}}_{\mathrm{CSI\text{-}RS}},
\mathcal{C}_{\mathrm{RS}},t_{\mathrm{meas}}
\right),
$$

其中 $\mathcal{Q}$ 代表候选波束、秩、预编码或质量信息的测量和量化过程。发送端若在 $t_{\mathrm{use}}$ 使用反馈结果，则需要区分：

$$
\Delta t=t_{\mathrm{use}}-t_{\mathrm{meas}},
$$

引起的时间老化，与量化误差和测量噪声是不同误差源。

## 不能与解调 CSI 混用的原因

CSI-RS 与当前 PDSCH/PUSCH 的资源、端口、预编码或时间位置可能不同。它可以为预编码或调度提供长期/短期测量，但不能仅因“都是已知导频”就替代[[DM-RS]]在当前传输中的解调估计。若试图复用，必须显式证明：

- 测量与数据的信道域、端口和预编码关系一致。
- CSI 仍处于有效时间范围内。
- 时频位置之间的插值或预测误差可接受。

## 与其他概念的关系

- 前置：[[02 参考信号与导频设计]]中的端口、时间、频率与功率配置；[[CDL 信道模型]]中的阵列和角度结构。
- 后续：[[CSI 反馈]]把测量压缩为可用的预编码或质量信息；[[05 MIMO 信道估计]]将其连接到层域等效信道。
- 对比：[[DM-RS]]优先支持当前数据解调；[[SRS]]通常用于上行探测；[[PTRS]]专注符号级相位跟踪。
- 指标：应联合报告波束增益、秩选择准确率、反馈比特数、CSI 年龄和最终 BLER，不能只报告测量 NMSE。

## 待验证问题

- [ ] 分别冻结量化精度和反馈时延，测量二者对预编码增益、层间干扰和 BLER 的独立影响。
- [ ] 扫描 CSI-RS 端口数和候选波束数，记录测量开销、端口分离条件数和反馈开销。
- [ ] 在 TDL 与 CDL 场景下比较相同测量开销的波束/秩选择稳定性，并记录阵列配置和空间相关性。
- [ ] 将过期 CSI 与当前 DM-RS CSI 分别输入预编码和均衡模块，验证接口不会误把测量 CSI 当作实时解调 CSI。

## 证据与仿真

- 规范入口：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.214｜Physical layer procedures for data]]。
- 关联笔记：[[05 MIMO 信道估计]]、[[CSI 反馈]]。
- 实验入口：[[09 仿真实验：MIMO 均衡]]。