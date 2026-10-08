---
title: ZF 均衡
aliases:
  - Zero-Forcing Equalization
  - 零迫均衡
type: atomic
status: seed
tags:
  - domain/OFDM
  - domain/MIMO
  - topic/均衡
  - method/ZF
  - stage/接收机
source:
  - 线性检测理论
simulation:
  - 09 仿真实验：MIMO 均衡
---

# ZF 均衡

> [!abstract] 一句话结论
> ZF 通过求逆或伪逆消除理想模型中的信道耦合，但在深衰落或病态 MIMO 空间方向会显著放大噪声与 CSI 误差，因此不应把“干扰被消除”误解为“检测最可靠”。

## 公式

对 SISO：

$$
\hat{X}_{\mathrm{ZF}}=Y/\hat{H}.
$$

对满列秩 MIMO：

$$
\hat{\mathbf{x}}_{\mathrm{ZF}}
=(\hat{\mathbf{H}}^H\hat{\mathbf{H}})^{-1}
\hat{\mathbf{H}}^H\mathbf{y}.
$$

实现应使用 QR、SVD 或线性求解，不应显式构造逆矩阵。若 $\sigma_{\min}(\hat{\mathbf{H}})$ 太小、CSI 无效或矩阵不满秩，应输出失败/低可靠度状态，而不是静默返回零向量。

## 噪声增强

理想 CSI、白噪声下：

$$
R_{n,\mathrm{ZF}}
=\sigma_n^2
(\mathbf{H}^H\mathbf{H})^{-1}.
$$

小奇异值方向的噪声功率按 $1/\sigma_i^2$ 增长。估计 CSI 时还存在未消除的等效干扰，后均衡方差不能只沿用发送端热噪声方差。

## 与其他概念的关系

- 前置：[[单抽头频域均衡]]给出 OFDM 标量场景，[[MIMO 信道矩阵条件数]]解释 MIMO 求逆稳定性。
- 输入：CSI 来自[[LS 信道估计]]、[[LMMSE 信道估计]]或[[05 MIMO 信道估计]]，其误差会被求逆放大。
- 对比：[[MMSE 均衡]]增加正则化以限制噪声增强；并非在所有高 SNR 场景都显著优于 ZF。
- 后续：[[软输出检测]]需使用逐层后均衡噪声/干扰方差计算 LLR。

## 待验证问题

- [ ] 在理想 CSI 条件下按条件数分桶验证理论后均衡噪声协方差与样本方差的一致性。
- [ ] 固定 SNR 扫描 CSI NMSE，比较 ZF 与 MMSE 的 EVM、BER、BLER 和最差层 SINR。
- [ ] 在 QR、SVD 与 Cholesky 实现中记录求解残差、异常条件数处理和每符号延迟。
- [ ] 对 $\sigma_{\min}$ 阈值触发的擦除、低可靠度与直接输出三种策略比较 LLR 校准和 BLER。

## 证据与仿真

- 主题入口：[[06 OFDM 接收与频域均衡]]。
- 实验入口：[[09 仿真实验：MIMO 均衡]]。