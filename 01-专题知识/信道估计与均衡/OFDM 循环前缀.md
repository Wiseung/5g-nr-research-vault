---
title: OFDM 循环前缀
aliases:
  - Cyclic Prefix
  - CP
type: atomic
status: seed
tags:
  - domain/OFDM
  - topic/循环前缀
  - topic/信道模型
  - stage/接收机
source:
  - 3GPP TS 38.211
simulation:
  - 08 仿真实验：LS 与 MMSE
---

# OFDM 循环前缀

> [!abstract] 一句话结论
> 循环前缀将有效 OFDM 符号末尾的一段复制到前面；当它覆盖有效多径记忆且同步窗口落在保护区内时，线性卷积可在 FFT 后表示为逐子载波的复数乘法。

## 定义与作用

设一个有效 OFDM 符号有 $N$ 个采样，离散信道冲激响应有效长度为 $L_h$。发送端在符号前复制最后 $N_{\mathrm{CP}}$ 个采样。满足：

$$
N_{\mathrm{CP}}\geq L_h-1
$$

且 FFT 窗口未跨出 CP 保护区时，去 CP 后的接收向量可写成：

$$
\mathbf{r}=\mathbf{C}_h\mathbf{x}+\mathbf{w},
$$

其中 $\mathbf{C}_h$ 是循环矩阵。单位化 DFT 将其对角化：

$$
\mathbf{Y}=\mathbf{F}\mathbf{r}
=\operatorname{diag}(H[0],\ldots,H[N-1])\mathbf{X}+\mathbf{W}.
$$

因此，CP 的直接作用是隔离相邻 OFDM 符号并使多径信道近似可由一个子载波一个系数描述；它不提高导频 SNR，也不校正频偏或相位噪声。

## 成立边界

单抽头模型还要求信道在一个有效符号内近似静态、残余载波频偏足够小，并且收发双方使用一致的 FFT 窗口和缩放约定。CP 长度满足上述不等式只是必要条件之一。

若 CP 不足或窗口越出 CP，频域模型一般变为：

$$
Y[k]=H[k]X[k]+\sum_{q\ne k}G[k,q]X[q]+I_{\mathrm{ISI}}[k]+W[k].
$$

非对角项代表 ICI，$I_{\mathrm{ISI}}$ 代表相邻符号泄漏。此时仅改善 $\hat{H}[k]$ 不能恢复完整接收模型。

## 与其他概念的关系

- 前置：[[01 5G 物理层与信道模型]]中的 DFT、线性卷积和时域多径模型。
- 解释：[[频率选择性衰落]]通过时延抽头形成频率响应；[[TDL 信道模型]]给出可用于检查 $L_h$ 的离散抽头接口。
- 后续：[[单抽头频域均衡]]、[[ZF 均衡]]和[[MMSE 均衡]]都以频域近似对角模型为基础。
- 对比：[[多普勒扩展]]、频偏和相位噪声可在 CP 足够长时仍产生 ICI，不能归因于 CP 不足。

## 待验证问题

- [ ] 在无噪声、理想 CSI 条件下扫描 $N_{\mathrm{CP}}-(L_h-1)$，分别记录 ISI 功率、ICI 非对角能量占比和均衡后 EVM。
- [ ] 固定 CP 足够长，只引入 CP 内与 CP 外两类定时偏移，验证前者主要产生子载波相位斜率，后者产生 ISI/ICI。
- [ ] 在相同总时隙长度下比较不同 CP 开销，联合报告有效数据 RE、NMSE、BLER 和有效吞吐量。

## 证据与仿真

- 理论与模型：[[01 5G 物理层与信道模型]]、[[06 OFDM 接收与频域均衡]]。
- 规范入口：[[3GPP TS 38.211｜Physical channels and modulation]]。
- 实验入口：[[08 仿真实验：LS 与 MMSE]]。