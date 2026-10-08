---
title: EVM
aliases:
  - Error Vector Magnitude
  - 误差矢量幅度
type: atomic
status: seed
tags:
  - domain/通信系统
  - topic/性能分析
  - metric/evm
  - stage/验证
source:
  - 调制误差测量
simulation:
  - 08 仿真实验：LS 与 MMSE
  - 09 仿真实验：MIMO 均衡
---

# EVM

> [!abstract] 一句话结论
> EVM 衡量均衡或解调后的复符号相对参考星座的误差大小，适合定位信道估计、均衡、同步和相位跟踪造成的符号层损失，但不直接等价于 BER、BLER 或 CSI NMSE。

## 定义

对已完成时间、频率、相位和增益对齐的参考符号 $s_q$ 与接收符号 $z_q$，RMS EVM 可定义为：

$$
\mathrm{EVM}_{\mathrm{RMS}}
=\sqrt{
\frac{\sum_q|z_q-s_q|^2}
{\sum_q|s_q|^2}
}.
$$

以百分比或 dB 表示时应明确转换约定，例如：

$$
\mathrm{EVM}_{\mathrm{dB}}
=20\log_{10}(\mathrm{EVM}_{\mathrm{RMS}}).
$$

若评估前执行了最佳复数缩放、公共相位补偿或判决导向校正，必须说明。不同对齐方式测量的是不同误差层级，不能直接比较。

## 诊断价值与局限

EVM 位于 CSI 与译码之间：

$$
\text{信道估计/均衡误差}
\rightarrow\text{符号 EVM}
\rightarrow\text{软解调 LLR}
\rightarrow\text{BER/BLER}.
$$

EVM 异常而导频位置 NMSE 正常，常提示数据位置插值、均衡、相位跟踪或资源索引问题。EVM 正常但 BLER 异常，常提示 LLR、译码、率匹配或统计口径问题。

## 与其他概念的关系

- 前置：[[信道估计误差]]和[[二维时频插值]]影响数据 RE CSI；[[ZF 均衡]]、[[MMSE 均衡]]影响符号残差。
- 并列：[[MSE 与 NMSE]]测量 CSI 误差，EVM 测量符号误差；两者不应互相替代。
- 后续：[[软输出检测]]从符号与方差生成 LLR，[[BLER 与 BER]]衡量译码后可靠性。
- 相位：[[PTRS]]可降低公共相位误差，其收益应同时反映在相位误差、EVM 和 BLER 上。

## 待验证问题

- [ ] 用理想 CSI、估计 CSI、错误 CSI 三个对照组验证 EVM 能否分离 CSI 与均衡损失。
- [ ] 分别引入频偏、相位噪声、CP 不足和时频插值误差，绘制 EVM 的子载波/符号/空间层分布。
- [ ] 固定平均 EVM，改变误差相关性和 LLR 方差标定，观察 BER/BLER 是否不同。
- [ ] 明确参考星座、对齐规则、资源掩码和是否包含导频、保护带、深衰落擦除资源。

## 证据与仿真

- 主题入口：[[06 OFDM 接收与频域均衡]]、[[07 信道估计误差与性能分析]]。
- 实验入口：[[08 仿真实验：LS 与 MMSE]]、[[09 仿真实验：MIMO 均衡]]。