---
title: DM-RS
aliases:
  - Demodulation Reference Signal
  - 解调参考信号
type: atomic
status: seed
tags:
  - domain/5G
  - domain/NR
  - topic/参考信号
  - stage/导频设计
  - stage/接收机
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.214
simulation:
  - 08 仿真实验：LS 与 MMSE
---

# DM-RS

> [!abstract] 一句话结论
> DM-RS 是与当前 PDSCH、PUSCH 或其他物理传输关联的解调参考信号；接收机利用它估计当前数据资源需要的等效信道，而不是仅测量一个可供未来使用的平均 CSI。

## 观测对象与基本模型

在 DM-RS 资源元素 $(k_p,m_p)$ 上，已知序列为 $X_{\mathrm{DMRS}}$，接收观测为：

$$
Y[k_p,m_p]=H_{\mathrm{eff}}[k_p,m_p]
X_{\mathrm{DMRS}}[k_p,m_p]+N[k_p,m_p].
$$

逐 RE 的 LS 基线为：

$$
\hat{H}_{\mathrm{LS}}[k_p,m_p]
=\frac{Y[k_p,m_p]}{X_{\mathrm{DMRS}}[k_p,m_p]}.
$$

此处的目标通常是当前数据传输的等效信道 $H_{\mathrm{eff}}$。若数据与 DM-RS 使用不同预编码、端口映射或时间窗口，直接把该估计送给均衡器会产生结构化 CSI 失配。

## 接收机必须保留的配置

- 物理信道、BWP、时隙、OFDM 符号和子载波位置。
- 端口、CDM 或序列复用关系、序列初始化与功率缩放。
- DM-RS 与数据的层、端口和预编码关联。
- 参考信号有效时间、资源掩码和估计质量状态。

端口分离不能只依靠二维 RE 掩码。多个端口可能在相同的时频位置通过码域或序列域复用，接收机必须按照实际配置联合恢复端口信道。

## 与其他概念的关系

- 前置：[[02 参考信号与导频设计]]规定统一的资源、端口和序列抽象；[[3GPP TS 38.211｜Physical channels and modulation]]是映射与序列的规范入口。
- 后续：[[LS 信道估计]]或[[LMMSE 信道估计]]在导频位置得到 CSI，[[二维时频插值]]将其扩展到数据 RE。
- 应用：[[单抽头频域均衡]]、[[ZF 均衡]]和[[MMSE 均衡]]需要与数据域一致的估计 CSI。
- 对比：[[CSI-RS]]服务测量、反馈和波束管理；[[PTRS]]服务相位跟踪。二者不能默认替代 DM-RS 解调 CSI。

## 待验证问题

- [ ] 用无噪声、单位信道的单端口帧逐位置比较发送与接收 DM-RS 序列、资源索引和 LS 输出。
- [ ] 对多端口配置记录训练矩阵秩和条件数，比较正交资源、码域复用和非正交故障注入下的端口串扰。
- [ ] 固定总导频 RE，扫描时间/频率密度，分别报告导频位置 NMSE、数据位置 NMSE、EVM 和 BLER。
- [ ] 强制使 DM-RS 与数据预编码不一致，验证端口域、传播域和层域 CSI 的转换是否被正确处理。

## 证据与仿真

- 规范入口：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.214｜Physical layer procedures for data]]。
- 关联笔记：[[03 信道估计基础]]、[[04 5G 信道估计算法]]。
- 实验入口：[[08 仿真实验：LS 与 MMSE]]、[[09 仿真实验：MIMO 均衡]]。