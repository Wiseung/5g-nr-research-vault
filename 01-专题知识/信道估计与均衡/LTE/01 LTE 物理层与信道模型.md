---
title: LTE 物理层与信道模型
aliases:
  - LTE OFDM 信道模型
  - E-UTRA 物理层模型
  - LTE 物理层与信道模型
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - domain/OFDM
  - topic/信道模型
  - topic/物理层
  - stage/建模
source:
  - "[[3GPP TS 36.211｜Physical channels and modulation]]"
related:
  - "[[LTE 参考信号与导频设计]]"
  - "[[LTE 信道估计算法]]"
  - "[[LTE OFDM 与 SC-FDMA 接收及频域均衡]]"
---

# LTE 物理层与信道模型

> [!abstract] 一句话结论
> LTE 下行以 OFDMA 为主、上行 PUSCH 采用 DFT-spread OFDM（通常称 SC-FDMA）；在循环前缀覆盖最大时延且一个 OFDM/SC-FDMA 符号内信道近似不变时，可以在频域使用逐子载波单抽头模型，再把参考信号估计的 CSI 交给均衡器。

## 前置知识

- [[00 5G 信道估计与均衡前置知识#傅里叶分析与数字信号处理]]：FFT/IFFT、循环卷积和频域索引。
- [[00 5G 信道估计与均衡前置知识#OFDM 与循环前缀]]：CP 覆盖和 ISI/ICI 边界。
- [[00 5G 信道估计与均衡前置知识#MIMO 与空间信道]]：端口、层和矩阵维度。

## 1. LTE 与 NR 的边界

这份笔记只记录 LTE/E-UTRA 的接收机抽象。它沿用库内 [[01 5G 物理层与信道模型]] 的线性观测和 OFDM 推导，但不把 NR 的 numerology、DM-RS 映射或 Polar/LDPC 编码假设带入 LTE。

| 维度 | LTE | 与估计/均衡的影响 |
|---|---|---|
| 下行多址 | OFDMA | 数据 RE 可按子载波独立均衡 |
| 上行多址 | SC-FDMA/DFT-s-OFDM | 先频域均衡，再取已分配子载波并 IDFT |
| 基本子载波间隔 | 常规 LTE 为 15 kHz | 决定相干带宽与符号时长尺度 |
| PRB | 12 个连续子载波，180 kHz | 参考信号、调度和插值通常以 PRB 为单位组织 |
| CP | normal/extended | 决定是否可把线性卷积近似成循环卷积 |
| 下行解调参考 | CRS 或 PDSCH UE-specific RS | 取决于传输模式和对应端口 |
| 上行解调参考 | PUSCH DM-RS | 与 PUSCH 分配和 SC-FDMA 符号位置绑定 |

表中 LTE 的物理接口是 `STANDARD`；“通常”表示接收机的工程路径，不代表所有 Release/传输模式只有一种实现。

## 2. 帧、slot 与资源网格

以常规 15 kHz 配置为主：

- 一个无线帧为 10 ms，含 10 个 1 ms 子帧。
- 一个子帧含两个 0.5 ms slot。
- 一个 PRB 在频域含 12 个子载波，带宽为 180 kHz。
- normal CP 一个 slot 含 7 个 OFDM 或 SC-FDMA 符号；extended CP 含 6 个。

这些数值来自 36.211 §4、§5.2.3 和 §6.2.3（`STANDARD`，基准版本 V16.6.0）。带宽、特殊子帧、窄带增强功能和其他子载波间隔应按目标配置另行核对。

将一个资源网格元素写为：

$$
\mathrm{RE}=(k,l,p),
$$

其中 `k` 是子载波索引，`l` 是 slot 内符号索引，`p` 是天线端口。数据、参考信号和保留 RE 必须由显式掩码区分：

$$
\mathcal R_{all}=\mathcal R_{data}\,\dot\cup\,\mathcal R_{RS}\,\dot\cup\,\mathcal R_{reserved}.
$$

`PERSONAL_NOTE`：这个互斥并集是实现检查不变量；标准中的具体映射仍由 36.211 对应条款给出。

## 3. 下行 OFDMA 观测模型

CP 去除、FFT、资源提取和同步正确时，单天线/单层数据 RE 可写为：

$$
Y[k,l]=H[k,l]X[k,l]+N[k,l].
$$

对多天线下行，若接收端有 `N_r` 根天线、发送层数为 `N_s`：

$$
\mathbf y[k,l]=\mathbf H[k,l]\mathbf x[k,l]+\mathbf n[k,l],
\quad
\mathbf H\in\mathbb C^{N_r\times N_s}.
$$

参考信号测到的往往是含有端口映射、预编码和功率缩放的等效信道 `H_eff`，不能脱离发送链解释成某一条物理路径系数。这一解释沿用库内 5G 笔记的 `PERSONAL_NOTE` 约定。

## 4. 上行 SC-FDMA 模型

LTE PUSCH 的典型发送链为：

```text
编码比特 → 调制 → 层映射 → M 点 DFT
       → 连续子载波映射 → N 点 IFFT → CP → 信道
```

对一个层和一个 SC-FDMA 符号，令 `M` 为分配的子载波数，`N` 为 IFFT 大小，变换预编码可抽象为：

$$
X_{DFT}[k]=\sum_{m=0}^{M-1}x[m]e^{-j2\pi km/M},
\quad k=0,\ldots,M-1.
$$

接收端的等效路径为：

```text
CP 去除 → N 点 FFT → 取 PUSCH 所占子载波
       → 逐子载波均衡 → M 点 IDFT → 软解调
```

在 localized mapping 且同步/CP 条件满足时，均衡后的频域符号可以逐点处理；IDFT 只是恢复 DFT-spread 前的调制符号顺序。若发生频率跳变，应按每个 slot 的实际 PRB 映射分别建立索引。

## 5. 循环前缀与单抽头条件

设离散信道冲激响应长度为 `L_h`，FFT 长度为 `N`，CP 长度为 `N_CP`。常用充分条件为：

$$
N_{CP}\ge L_h-1.
$$

还需要满足：

1. FFT 窗口位于有效 CP 区间内。
2. 一个符号期间信道变化足够小，或变化造成的 ICI 已被单独建模。
3. CFO、采样偏差和相位噪声已校正，或作为额外干扰项保留。

若这些条件不满足，频域模型应写成带非对角项的形式：

$$
\mathbf y=(\mathbf H_{diag}+\mathbf H_{ICI})\mathbf x+\mathbf n+\mathbf i_{ISI}.
$$

此时仅替换 `H_hat` 不能修复 ICI/ISI；需要同步、ICI 感知均衡或块处理。此段为 `PERSONAL_NOTE`，实验结论需在 [[仿真实验：不同信道模型]] 或 LTE 专用实验中核验。

## 6. 与编码链的接口

物理层接收机把均衡后的符号转换为软比特，交给 LTE 编译码链：

```text
36.211 资源解映射
    ↓
CRS/DM-RS 信道估计
    ↓
ZF/MMSE 或其他检测
    ↓
软解调 LLR（含有效噪声方差）
    ↓
36.212 逆率匹配、Turbo/TBCC 译码、CRC
```

`LLR` 的符号、调制比特顺序、归一化和 RE 排列必须在 LTE 端到端测试中固定；只看星座图或硬比特无法证明编码器接口正确。

## 7. 核验清单

- [ ] 子载波、PRB、slot、CP 和 FFT 索引采用同一份配置。
- [ ] 下行 CRS/UE-specific RS 与上行 DM-RS 未混用。
- [ ] SC-FDMA 的 DFT/IDFT 长度与实际 PUSCH 分配一致。
- [ ] CP 不足、CFO、时变和频率跳变会触发显式状态，而不是静默进入单抽头路径。
- [ ] 均衡器输出携带后均衡噪声方差或协方差。
- [ ] LLR 经过解扰、逆率匹配后再进入 Turbo/TBCC 译码器。

## 与其他概念的关系

本页给出波形和坐标；[[LTE 参考信号与导频设计]] 给出可观测点；[[LTE 信道估计算法]] 负责从参考点重构 CSI；[[LTE OFDM 与 SC-FDMA 接收及频域均衡]] 使用 CSI 形成软符号。

## 待验证问题

- [ ] 目标 Release 的特殊子帧、窄带和增强型配置是否改变当前单抽头假设？
- [ ] 实际接收机的 FFT 缩放和定时窗口是否与实验模型一致？

## 证据与待核验

- `STANDARD`：36.211 V16.6.0 §4、§5.2、§5.3、§6.2、§6.12 的帧、资源、SC-FDMA 和 OFDM 接口。
- `PERSONAL_NOTE`：线性观测模型、CP 充分条件、MIMO 维度和接收机状态划分。
- `NEEDS_EXTERNAL_REFERENCE`：目标设备的具体 FFT 缩放、同步窗口、传输模式和特殊子帧表。

## 关联笔记

- [[LTE 参考信号与导频设计]]
- [[LTE 信道估计算法]]
- [[LTE OFDM 与 SC-FDMA 接收及频域均衡]]
- [[LTE MIMO 信道估计与均衡]]
- [[LTE-DL-SCH 编码链]]
- [[LTE-UL-SCH 编码链]]
