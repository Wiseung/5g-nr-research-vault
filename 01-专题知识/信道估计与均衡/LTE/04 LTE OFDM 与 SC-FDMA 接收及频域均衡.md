---
title: LTE OFDM 与 SC-FDMA 接收及频域均衡
aliases:
  - LTE 频域均衡
  - LTE OFDMA SC-FDMA 接收机
  - LTE OFDM 与 SC-FDMA 接收及频域均衡
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - domain/OFDM
  - topic/均衡
  - topic/检测
  - method/ZF
  - method/MMSE
  - stage/接收机
source:
  - "[[LTE 物理层与信道模型]]"
  - "[[LTE 信道估计算法]]"
  - "[[06 OFDM 接收与频域均衡]]"
related:
  - "[[LTE MIMO 信道估计与均衡]]"
  - "[[LTE-控制信道编码链]]"
---

# LTE OFDM 与 SC-FDMA 接收及频域均衡

> [!abstract] 一句话结论
> LTE 下行在 CP、同步和准静态条件满足时适合逐 RE 单抽头均衡；LTE 上行的 SC-FDMA 接收通常在 FFT 域对分配子载波做频域均衡，再经 IDFT 恢复调制符号。ZF 消除理想线性信道的失真但会放大深衰落噪声，MMSE 通过正则化在噪声增强和残余失真之间折中。

## 前置知识

- [[LTE 物理层与信道模型]]：OFDM/SC-FDMA 波形、CP 和资源索引。
- [[LTE 信道估计算法]]：参考 RE 到数据 RE 的 CSI。
- [[LTE MIMO 信道估计与均衡]]：多层矩阵检测和条件数。

## 1. 两条接收链

### 下行 PDSCH/PDCCH

```text
同步与定时
  ↓
CP 去除 → FFT
  ↓
资源网格提取（CRS/DM-RS/数据）
  ↓
参考信号估计 H_hat
  ↓
单层或 MIMO ZF/MMSE
  ↓
软解调、解扰、LTE 36.212 译码
```

### 上行 PUSCH

```text
同步与定时
  ↓
CP 去除 → FFT
  ↓
提取 PUSCH 分配子载波与 DM-RS
  ↓
频域 LS/LMMSE + 单抽头 FDE
  ↓
按分配顺序取 M 个子载波 → M 点 IDFT
  ↓
软解调、解扰、UL-SCH/Turbo 译码
```

上行链中的 `M` 是当前 PUSCH 分配的子载波数，不应误用系统 FFT 大小 `N`。频率跳变时两个 slot 的分配索引和 CSI 需分别保存。

## 2. 单抽头模型与 ZF

对单层数据 RE：

$$
Y=\hat H X+\tilde H X+N.
$$

理想 CSI 下 ZF 为：

$$
\hat X_{ZF}=\frac{Y}{\hat H},
\qquad |\hat H|>\epsilon.
$$

`\epsilon` 是实现保护阈值，不是 LTE 标准参数。若 `|H|` 很小，输出噪声方差近似为：

$$
\sigma^2_{n,out}≈\frac{\sigma_n^2}{|\hat H|^2},
$$

因此深衰落子载波会出现噪声和估计误差增强。比起硬裁剪，更稳妥的做法是把弱信道标记传给软解调器，或切换到 MMSE。

## 3. 标量 MMSE

在 `E[|X|^2]=\sigma_x^2`、`E[|N|^2]=\sigma_n^2` 的白噪声模型下：

$$
\hat X_{MMSE}
=\frac{\hat H^*}{|\hat H|^2+\sigma_n^2/\sigma_x^2}Y.
$$

它不是简单的信道逆：

- 深衰落时正则化项限制增益，降低噪声增强。
- 高 SNR 或 `\sigma_n^2/\sigma_x^2\to0` 时趋近 ZF。
- 输出存在收缩增益，LLR 计算不能继续假定输出等于原始 `X`。

若噪声或干扰是彩色的，不能把 `R_nn` 随意替换成标量；应使用广义 MMSE 或先白化。

## 4. MIMO 线性均衡

对一个 RE 或一组同域资源：

$$
\mathbf y=\mathbf H\mathbf x+\mathbf n,
\quad
\mathbf y\in\mathbb C^{N_r\times1},
\quad
\mathbf x\in\mathbb C^{N_s\times1}.
$$

ZF 和白噪声 MMSE 的常用形式：

$$
\mathbf W_{ZF}=(\mathbf H^H\mathbf H)^{-1}\mathbf H^H,
$$

$$
\mathbf W_{MMSE}
=\left(\mathbf H^H\mathbf H+
\frac{\sigma_n^2}{\sigma_x^2}\mathbf I\right)^{-1}\mathbf H^H.
$$

彩色噪声的统一形式为：

$$
\mathbf W
=R_{xx}\mathbf H^H
(\mathbf H R_{xx}\mathbf H^H+R_{nn})^{-1}.
$$

实现用 QR/Cholesky/正则化求解，不显式求逆。要记录 `\sigma_{min}(H)`、条件数、正则化项和有效层数；LTE 的 CRS/DM-RS 端口解释错误会让矩阵看似可逆但物理意义错误。

## 5. 后均衡噪声与软输出

线性均衡器输出 `\hat x=W y` 时，噪声传播为：

$$
R_{n,out}=W R_{nn}W^H.
$$

若还要把信道估计误差作为等效干扰，令 `H=H_hat+E`：

$$
\hat{\mathbf x}
=W\hat H\mathbf x+W\mathbf n+W\mathbf E\mathbf x.
$$

最后一项通常与数据相关，不能总是并入独立白噪声。实际软解调至少应接收：

| 字段 | 作用 |
|---|---|
| `x_hat` | 均衡符号 |
| `R_n_out` 或每层方差 | LLR 尺度和置信度 |
| `gain` | MMSE 收缩或单层增益 |
| `valid_mask` | 弱/无效 RE 处理 |
| `domain` | CRS/DM-RS 估计对应的端口/层域 |

常用 LLR 约定为：

$$
L_b=\log\frac{P(b=0\mid y)}{P(b=1\mid y)}.
$$

LTE 36.212 的 Turbo/TBCC 译码器不负责修正均衡器的 LLR 符号或尺度；这些必须在物理层接口测试中闭合。

## 6. 无效资源与边界策略

| 情况 | 建议状态 | 处理 |
|---|---|---|
| `|H_hat|<epsilon` | `weak_channel` | MMSE、限幅或降低 LLR 置信度 |
| 参考 RE 缺失 | `rs_missing` | 不插值越界；报告缺失原因 |
| CP 不足/CFO/ICI | `single_tap_invalid` | 切换块均衡或上游同步修复 |
| MIMO `sigma_min` 很小 | `ill_conditioned` | MMSE/降层/非线性检测 |
| 估计时间戳过期 | `stale_csi` | 重新估计或扩大干扰方差 |
| UCI/数据资源重叠 | `resource_conflict` | 按 36.212 复用索引分离 |

## 7. 接收机验证顺序

1. 单径、无噪声、单位信道，验证 FFT/CP/资源索引。
2. AWGN + 理想 CSI，分别核对 ZF 和 MMSE 符号输出。
3. 加入 CRS/DM-RS LS 估计，比较 pilot 与 data RE NMSE。
4. 加入时频选择性和 MIMO 条件数分桶，观察后均衡方差。
5. 传递带方差的 LLR 到 [[LTE-Turbo 编码与译码]]，做无噪声和低 SNR 闭环。

每一步只引入一个新变量，并记录 FFT 缩放、符号功率、噪声定义、调制比特顺序和随机种子。

## 与其他概念的关系

[[LTE 信道估计算法]] 提供 `H_hat` 和有效掩码；本页把它转换为符号与后均衡协方差；[[LTE-Turbo 编码与译码]] 和 [[LTE-控制信道编码链]] 消费软 LLR。

## 待验证问题

- [ ] 在目标 MIMO 条件数和估计误差下，ZF/MMSE 的差异是否能由后均衡方差解释？
- [ ] PUSCH 的 SC-FDMA FDE+IDFT 实现是否在频率跳变和多层配置下保持符号顺序？

## 8. 证据与待核验

- `STANDARD`：OFDMA/SC-FDMA 波形和 LTE 资源边界来自 36.211 V16.6.0。
- `PERSONAL_NOTE`：ZF/MMSE、噪声协方差传播、CSI 误差分解和状态机沿用库内均衡笔记。
- `NEEDS_EXTERNAL_REFERENCE`：具体传输模式的预编码码本、层数上限、设备级弱信道阈值和非线性检测器性能。

## 关联笔记

- [[LTE 信道估计算法]]
- [[LTE MIMO 信道估计与均衡]]
- [[ZF 均衡]]
- [[MMSE 均衡]]
- [[软输出检测]]
- [[LTE-DL-SCH 编码链]]
- [[LTE-UL-SCH 编码链]]
