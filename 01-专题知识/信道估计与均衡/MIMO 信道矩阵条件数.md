---
title: MIMO 信道矩阵条件数
aliases:
  - MIMO Channel Matrix Condition Number
  - 空间信道条件数
type: atomic
status: seed
tags:
  - domain/MIMO
  - topic/空间信道
  - topic/均衡
  - metric/condition-number
  - stage/验证
source:
  - 矩阵分析与 MIMO 检测
simulation:
  - 09 仿真实验：MIMO 均衡
---

# MIMO 信道矩阵条件数

> [!abstract] 一句话结论
> MIMO 信道矩阵条件数衡量空间模态的可分离程度；最小奇异值很小时，ZF 会强烈放大噪声和 CSI 误差，MMSE 通常更稳健，但平均 NMSE 不能替代条件数分桶分析。

## 定义

对 $\mathbf{H}\in\mathbb{C}^{N_r\times N_t}$ 作奇异值分解：

$$
\mathbf{H}=\mathbf{U}\mathbf{\Sigma}\mathbf{V}^H,
$$

其中非零奇异值按 $\sigma_1\geq\cdots\geq\sigma_r>0$ 排列。二范数条件数为：

$$
\kappa_2(\mathbf{H})=
\frac{\sigma_1}{\sigma_r}.
$$

当 $\mathbf{H}$ 不满列秩时，$\sigma_r=0$，条件数可视为无穷大。对每个子载波和 OFDM 符号，均应基于均衡器实际使用的层域等效信道：

$$
\mathbf{H}_{\mathrm{eff}}[k,m]
=\mathbf{H}_{\mathrm{port}}[k,m]\mathbf{W}[k,m],
$$

而不是混用传播信道、端口域信道和层域信道。

## 与线性均衡的关系

理想白噪声下 ZF 输出噪声协方差为：

$$
R_{n,\mathrm{ZF}}
=\sigma_n^2
(\mathbf{H}^H\mathbf{H})^{-1}.
$$

其最大噪声增强方向与 $1/\sigma_r^2$ 有关。条件数大表明模态差异大，但最终错误率还受整体增益、SNR、调制阶数、CSI 误差和层数影响；不能仅凭条件数判断单个帧必然失败。

有效秩可结合阈值定义：

$$
r_{\mathrm{eff}}(\tau)
=\#\{i:\sigma_i\geq\tau\sigma_1\}.
$$

阈值 $\tau$ 应记录在实验日志中，因为不同阈值回答的是不同的可用空间层问题。

## 与其他概念的关系

- 前置：[[05 MIMO 信道估计]]定义端口、天线和层域矩阵；[[空间相关性]]常导致奇异值更不均衡。
- 后续：[[ZF 均衡]]对小奇异值最敏感，[[MMSE 均衡]]通过正则化抑制噪声增强。
- 误差：[[信道估计误差]]会扰动最小奇异值，因此应同时记录真实 CSI 与估计 CSI 的条件数。
- 指标：[[MSE 与 NMSE]]应按条件数分桶，结合[[EVM]]、[[BLER 与 BER]]和后均衡 SINR 解读。

## 待验证问题

- [ ] 以 $\kappa<5$、$5\le\kappa<20$、$20\le\kappa<100$、$\kappa\ge100$ 分桶，比较 ZF/MMSE 的后均衡方差、EVM 与 BER。
- [ ] 分别对真实 CSI 与估计 CSI 计算条件数，检查估计误差是否会错误地掩盖病态子载波。
- [ ] 固定平均条件数，改变整体信道增益与 SNR，确认条件数不是独立于信噪比的完整性能指标。
- [ ] 扫描空间层数与有效秩，记录层数超过可分离模态时的检测状态和 BLER。

## 证据与仿真

- 主题入口：[[05 MIMO 信道估计]]、[[06 OFDM 接收与频域均衡]]。
- 实验入口：[[09 仿真实验：MIMO 均衡]]。