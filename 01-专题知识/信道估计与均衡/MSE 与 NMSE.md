---
title: MSE 与 NMSE
aliases:
  - Mean Squared Error and Normalized Mean Squared Error
  - 均方误差与归一化均方误差
type: atomic
status: seed
tags:
  - domain/通信系统
  - topic/信道估计
  - topic/性能分析
  - metric/mse
  - metric/nmse
  - stage/验证
source:
  - 信号估计理论
simulation:
  - 08 仿真实验：LS 与 MMSE
  - 09 仿真实验：MIMO 均衡
---

# MSE 与 NMSE

> [!abstract] 一句话结论
> MSE 测量估计误差的绝对能量，NMSE 将误差相对化为信道能量的比例；二者都必须说明估计对象、资源范围、样本聚合方式和是否包含深衰落样本。

## 定义

对标量信道：

$$
\mathrm{MSE}=E\left[|\hat{h}-h|^2\right].
$$

对向量或矩阵信道：

$$
\mathrm{MSE}_{\mathbf{H}}
=E\left[\|\hat{\mathbf{H}}-\mathbf{H}\|_F^2\right].
$$

归一化均方误差定义为：

$$
\mathrm{NMSE}
=\frac{E\left[\|\hat{\mathbf{H}}-\mathbf{H}\|_F^2\right]}
{E\left[\|\mathbf{H}\|_F^2\right]}.
$$

以 dB 表示时：

$$
\mathrm{NMSE}_{\mathrm{dB}}=10\log_{10}(\mathrm{NMSE}).
$$

## 有限样本统计

对 $Q$ 个可比较样本，推荐使用总能量比：

$$
\widehat{\mathrm{NMSE}}
=\frac{\sum_{q=1}^{Q}\|\hat{\mathbf{H}}_q-\mathbf{H}_q\|_F^2}
{\sum_{q=1}^{Q}\|\mathbf{H}_q\|_F^2}.
$$

先对每个样本计算相对误差再简单平均，会让信道能量接近零的样本获得过大权重。若研究深衰落风险，应保留该类分桶指标，但不得与总体 NMSE 混为同一数值。

## 报告范围

每个 MSE/NMSE 曲线至少记录：

- 估计对象：标量 RE、端口域矩阵、天线域矩阵或层域等效信道。
- 资源范围：仅导频位置、数据位置、边界资源或完整资源网格。
- 聚合范围：帧、时隙、子载波、端口、信道实现与 SNR 点。
- 信道功率和 FFT 的归一化约定。
- 是否使用生成器内部真实协方差、真实噪声方差或真实信道作为 oracle 信息。

导频位置 NMSE 低并不推出数据位置 NMSE 低；端口域 NMSE 低也不必然推出层域均衡或 BLER 最优。

## 与其他概念的关系

- 前置：[[信道估计误差]]是 $\hat{\mathbf{H}}-\mathbf{H}$；[[估计器偏差与方差]]分解平均误差来源。
- 应用：[[LS 信道估计]]、[[LMMSE 信道估计]]和[[二维时频插值]]使用 NMSE 比较估计质量。
- 后续：[[EVM]]量化符号层残差，[[BLER 与 BER]]量化端到端可靠性；三者不能互相替代。
- MIMO：[[MIMO 信道矩阵条件数]]和误差相关性会使相同平均 NMSE 产生不同均衡损失。

## 待验证问题

- [ ] 对每条估计曲线同时输出导频位置、数据位置和边界资源 NMSE，并检查三者是否被混用。
- [ ] 固定平均 NMSE，改变误差偏差、时频相关性或空间相关性，比较 EVM、LLR 校准和 BLER。
- [ ] 按真实信道能量、条件数与 CSI 年龄分桶，报告均值与 90/99 分位误差。
- [ ] 对比样本比值与逐帧相对误差均值，说明深衰落样本权重变化对结论的影响。

## 证据与仿真

- 主题入口：[[07 信道估计误差与性能分析]]。
- 实验入口：[[08 仿真实验：LS 与 MMSE]]、[[09 仿真实验：MIMO 均衡]]。
