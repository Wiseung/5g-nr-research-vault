---
title: LS 信道估计
aliases:
  - Least Squares Channel Estimation
  - 最小二乘信道估计
type: atomic
status: seed
tags:
  - domain/通信系统
  - topic/信道估计
  - method/LS
  - stage/接收机
source:
  - 最小二乘估计
simulation:
  - 08 仿真实验：LS 与 MMSE
---

# LS 信道估计

> [!abstract] 一句话结论
> LS 在已知导频观测模型下选择最小化残差能量的信道参数，不需要信道二阶统计先验；其噪声敏感性、可辨识性和数值稳定性由导频矩阵的秩与条件数决定。

## 观测模型与解

令：

$$
\mathbf{y}=\mathbf{X}\mathbf{h}+\mathbf{n},
$$

其中 $\mathbf{y}\in\mathbb{C}^{Q\times1}$ 是导频观测，$\mathbf{X}\in\mathbb{C}^{Q\times P}$ 是已知训练矩阵，$\mathbf{h}\in\mathbb{C}^{P\times1}$ 是待估信道。LS 定义为：

$$
\hat{\mathbf{h}}_{\mathrm{LS}}
=\arg\min_{\mathbf{h}}
\|\mathbf{y}-\mathbf{X}\mathbf{h}\|_2^2.
$$

当 $\mathbf{X}$ 满列秩时：

$$
\hat{\mathbf{h}}_{\mathrm{LS}}
=(\mathbf{X}^H\mathbf{X})^{-1}\mathbf{X}^H\mathbf{y}.
$$

实现应使用 QR、SVD 或线性方程求解，避免显式求逆。对单位模单端口导频，逐 RE 特例为：

$$
\hat{H}_{\mathrm{LS}}=Y/X,
\qquad X\ne0.
$$

## 条件与误差

LS 的可辨识条件是：

$$
\operatorname{rank}(\mathbf{X})=P.
$$

在零均值白噪声、模型正确且 $\mathbf{X}$ 满列秩的条件下，LS 无偏，误差协方差为：

$$
R_e=\sigma_n^2(\mathbf{X}^H\mathbf{X})^{-1}.
$$

若导频索引、端口关系、预编码域或信道在训练窗口内的静态假设错误，LS 会把无法解释的结构化项投影为 CSI 偏差；这不是简单增大导频能量即可解决的问题。

## 与其他概念的关系

- 前置：[[DM-RS]]或其他已知参考信号提供 $\mathbf{X}$；[[02 参考信号与导频设计]]决定其时频空间布局。
- 对比：[[LMMSE 信道估计]]通过二阶统计抑制方差，但依赖协方差和噪声先验。
- 后续：导频位置 LS 常需经过[[二维时频插值]]才能给出数据 RE CSI；[[MSE 与 NMSE]]应分别统计这两个阶段。
- 应用：[[ZF 均衡]]和[[MMSE 均衡]]使用的 CSI 域、端口顺序和噪声口径必须与 LS 输出一致。

## 待验证问题

- [ ] 在无噪声、满秩、已知导频条件下验证残差和估计误差接近数值精度，而非只看最终 BER。
- [ ] 扫描训练矩阵条件数，在相同总训练能量下比较误差协方差、NMSE 和端口串扰。
- [ ] 固定导频位置，分别注入白噪声、导频索引错位和预编码失配，确认噪声方差与结构化偏差的曲线形态不同。
- [ ] 将逐点 LS 与 QR/SVD 联合 LS 在病态矩阵上比较，记录求解残差、延迟和失败状态。

## 证据与仿真

- 主题入口：[[03 信道估计基础]]、[[04 5G 信道估计算法]]。
- 实验入口：[[08 仿真实验：LS 与 MMSE]]。