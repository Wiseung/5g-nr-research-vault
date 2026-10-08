---
title: PTRS
aliases:
  - Phase Tracking Reference Signal
  - 相位跟踪参考信号
type: atomic
status: seed
tags:
  - domain/5G
  - domain/NR
  - topic/参考信号
  - topic/相位噪声
  - stage/接收机
source:
  - 3GPP TS 38.211
simulation:
  - 08 仿真实验：LS 与 MMSE
---

# PTRS

> [!abstract] 一句话结论
> PTRS 用于跟踪 OFDM 符号上的公共相位误差，主要补偿相位噪声或残余频率误差的共同相位旋转；它不是用于恢复任意频率选择性信道，也不能单独消除所有 ICI。

## 相位跟踪模型

若某个 OFDM 符号的主要失真近似为公共相位旋转 $\phi[m]$，则：

$$
Y[k,m]\approx e^{j\phi[m]}H[k,m]X[k,m]+I_{\mathrm{ICI}}[k,m]+N[k,m].
$$

在已有信道预测或同符号参考的条件下，可用 PTRS 资源集合 $\mathcal{P}_{\mathrm{PTRS}}$ 构造相位估计：

$$
\hat{\phi}[m]
=\arg\left(
\sum_{k\in\mathcal{P}_{\mathrm{PTRS}}}
Y[k,m]X_{\mathrm{PTRS}}[k,m]^*
\hat{H}_{\mathrm{ref}}[k,m]^*
\right).
$$

随后用 $e^{-j\hat{\phi}[m]}$ 旋转该符号数据。该式依赖参考 CSI 的准确性；强 ICI、深衰落或频率相关相位误差会使单个公共相位模型失配。

## 与频偏和多普勒的边界

- 载波频偏可导致共同相位项以及 ICI；PTRS 通常只处理前者。
- [[多普勒扩展]]导致传播信道时间变化和 ICI，不等价于本振相位噪声。
- [[DM-RS]]估计调制相关 CSI，PTRS 在 CSI 基础上提供更细粒度的相位跟踪。
- 高多普勒、频偏和相位噪声可以同时出现，实验必须逐项打开，不能通过 PTRS 收益直接推断某一种失真占主导。

## 与其他概念的关系

- 前置：[[02 参考信号与导频设计]]中的 PTRS 时间/频率密度和关联端口；[[时变信道]]中的符号时间尺度。
- 后续：[[单抽头频域均衡]]和[[软输出检测]]应接收已校正相位以及反映残余失真的可靠度。
- 指标：除 NMSE 外还应看公共相位误差、ICI 功率、EVM、LLR 校准和 BLER。
- 对比：增加 DM-RS 密度主要改善时频 CSI 采样；增加 PTRS 密度主要改善共同相位跟踪，二者的资源替代关系需由失真模型决定。

## 待验证问题

- [ ] 分别注入仅多普勒、仅频偏、仅相位噪声及组合失真，比较 PTRS 前后的相位误差、ICI、EVM 和 BLER。
- [ ] 固定 PTRS 开销，扫描时间/频率密度，按 OFDM 符号和子载波记录残余相位误差分布。
- [ ] 固定总参考信号 RE，对比增加 PTRS 与增加 DM-RS 在不同失真主导场景下的边际收益。
- [ ] 对高阶 QAM 记录后均衡方差和 LLR 校准，检查相位校正后是否仍出现过度自信的软信息。

## 证据与仿真

- 规范入口：[[3GPP TS 38.211｜Physical channels and modulation]]。
- 关联笔记：[[02 参考信号与导频设计]]、[[06 OFDM 接收与频域均衡]]。
- 实验入口：[[08 仿真实验：LS 与 MMSE]]、[[仿真-LLR 符号验证]]。