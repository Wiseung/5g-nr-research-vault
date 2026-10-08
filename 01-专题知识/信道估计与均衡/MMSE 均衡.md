---
title: MMSE 均衡
aliases:
  - Minimum Mean Square Error Equalization
  - 最小均方误差均衡
type: atomic
status: seed
tags:
  - domain/OFDM
  - domain/MIMO
  - topic/均衡
  - method/MMSE
  - stage/接收机
source:
  - 线性 MMSE 检测理论
simulation:
  - 09 仿真实验：MIMO 均衡
---

# MMSE 均衡

> [!abstract] 一句话结论
> MMSE 均衡通过噪声和干扰统计在残余干扰与噪声增强之间折中；其收益依赖正确的信号、热噪声、干扰和 CSI 误差口径，错误的正则化参数会直接损害软输出可靠度。

## 标量与矩阵形式

若标量信道 $Y=HX+N$，信号功率为 $\sigma_x^2$、噪声功率为 $\sigma_n^2$，则：

$$
\hat{X}_{\mathrm{MMSE}}
=\frac{\hat{H}^*}
{|\hat{H}|^2+\sigma_n^2/\sigma_x^2}Y.
$$

对 MIMO，若信号协方差为 $R_{xx}$、有效干扰协方差为 $R_{vv}$：

$$
\mathbf{G}_{\mathrm{MMSE}}
=R_{xx}\hat{\mathbf{H}}^H
\left(
\hat{\mathbf{H}}R_{xx}\hat{\mathbf{H}}^H+R_{vv}
\right)^{-1}.
$$

当 $R_{xx}=\sigma_x^2\mathbf{I}$、$R_{vv}=\sigma_n^2\mathbf{I}$ 时，可改写为常见正则化形式。该简化不再覆盖彩色干扰和显著 CSI 误差。

## CSI 误差的接口

若 $\hat{\mathbf{H}}=\mathbf{H}+\widetilde{\mathbf{H}}$，实际接收模型含有：

$$
\widetilde{\mathbf{H}}\mathbf{x}+\mathbf{n}.
$$

在近似条件下，这部分可并入 $R_{vv}$。必须注明 $R_{vv}$ 中的估计误差项是样本估计、模型后验、保守上界还是仿真 oracle；禁止把生成器内部真实误差协方差伪装成部署可得信息。

## 与其他概念的关系

- 前置：[[单抽头频域均衡]]、[[MIMO 信道矩阵条件数]]与[[信道估计误差]]。
- 输入：[[LMMSE 信道估计]]可输出后验误差近似，但该估计器的误差协方差不等于均衡器完整的有效干扰协方差。
- 对比：[[ZF 均衡]]对应忽略正则化的零迫极限；低 SNR、深衰落或高条件数时 MMSE 往往更稳健。
- 后续：[[软输出检测]]必须知道均衡增益与输出残差方差，不能假设均衡输出已经是单位增益白噪声模型。

## 待验证问题

- [ ] 在理想 CSI、白噪声条件下，扫描 SNR 与条件数，确认 MMSE 向 ZF 接近的高 SNR 区域和显著收益的低 SNR 区域。
- [ ] 独立扫描热噪声方差、CSI 误差方差和正则化参数失配，比较 EVM、LLR 校准和 BLER。
- [ ] 在彩色干扰下比较白化 MMSE 与广义 MMSE，验证数值结果和输出协方差是否一致。
- [ ] 对每层输出有效增益、后均衡方差和状态标记，接入[[仿真-LLR 符号验证]]检查软值可靠度。

## 证据与仿真

- 主题入口：[[06 OFDM 接收与频域均衡]]、[[05 MIMO 信道估计]]。
- 实验入口：[[09 仿真实验：MIMO 均衡]]、[[仿真-LLR 符号验证]]。