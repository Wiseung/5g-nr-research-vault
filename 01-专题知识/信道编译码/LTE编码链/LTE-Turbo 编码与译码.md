---
title: LTE-Turbo 编码与译码
aliases:
  - LTE Turbo code
  - LTE PCCC 译码
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - code/turbo
  - process/encoding
  - process/decoding
  - method/迭代译码
  - evidence/3gpp
source:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
related:
  - "[[LTE-QPP 交织]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
  - "[[软判决与 LLR]]"
---

# LTE-Turbo 编码与译码

> [!abstract] 一句话结论
> LTE Turbo 是并行级联卷积码（PCCC）：两个 8-state constituent RSC 编码器通过一个 QPP 内部交织器并行处理同一信息序列，输出系统位和两路校验位；每个码块随后加入 trellis termination，再进入 Turbo 专用速率匹配。

## 1. 编码器结构

```text
                  ┌─ 8-state RSC ─→ z_k ─┐
c_k ─→ x_k ───────┤                       ├→ 三路输出
  │               └─ QPP Π ─→ 8-state RSC ─→ z'_k
  └──────────────────────────────────────── x_k
```

36.212 §5.1.3.2 给出 constituent code 的生成多项式：

$$
G(D)=\left[1,\frac{g_1(D)}{g_0(D)}\right],
\quad
g_0(D)=1+D^2+D^3,
\quad
g_1(D)=1+D+D^3.
$$

编码率为 1/3。对输入长度 `K` 的码块，三路信息位/校验位流的每一路长度为：

$$
D=K+4,
$$

其中 `+4` 来自 trellis termination；三路合计不是简单的 `3K`。

## 2. 终止比特

规范规定：

1. 前三组尾比特终止第一 constituent encoder，同时关闭第二编码器。
2. 后三组尾比特终止第二 constituent encoder，同时关闭第一编码器。
3. 尾比特按系统/校验流交错排列到 `d^(0), d^(1), d^(2)`。

因此实现不能把 Turbo 当作无终止的 `K` 个三元组。发送端和译码端必须使用同一尾比特坐标；具体六组尾比特的排列以 36.212 §5.1.3.2.2 为准。

## 3. 迭代译码接口

Turbo 译码器通常由两个 SISO constituent decoder 交替运行（Log-MAP、Max-Log-MAP 或其工程近似属于实现选择）。每次迭代交换外信息：

$$
L^{(t)}_{ext,1}
\rightarrow \Pi
\rightarrow L^{(t)}_{a,2}
\rightarrow \Pi^{-1}
\rightarrow L^{(t+1)}_{a,1}.
$$

这里的 `L` 必须包含系统位、对应校验位和先验信息的明确符号约定。译码器输出至少应区分：

| 输出 | 含义 |
|---|---|
| `L_post` | 后验 LLR |
| `hard_bits` | 硬判决信息位 |
| `iterations` | 实际迭代次数 |
| `cb_crc` | 码块 CRC 结果（适用时） |
| `stop_reason` | 达到最大迭代、CRC 成功、综合检查或数值异常 |

## 4. 与信道估计/均衡的接口

均衡器必须把后均衡噪声方差传给软解调器，再由软解调器生成 Turbo 所需 LLR：

$$
L_b=\log\frac{P(b=0\mid y)}{P(b=1\mid y)}.
$$

如果 ZF 深衰落造成的噪声增强被忽略，Turbo 译码器会收到过度自信的错误 LLR；增加迭代次数不能替代正确的均衡方差。

## 5. 数值与状态约定

- 明确 `LLR>0` 支持比特 0 还是比特 1。
- 对 `tanh/atanh`、指数和无穷 LLR 做稳定裁剪。
- 两个 constituent decoder 的路径/状态不能共享可变数组而互相覆盖。
- 迭代停止以 CB-CRC/TB-CRC 或明确的收敛规则为准，不把一次硬判决相同当成必然正确。

## 6. 最小闭环

```text
非零 payload
  ↓ CRC/分段
Turbo encode（含尾比特）
  ↓ rate matching
无噪声调制/软解调
  ↓ inverse rate matching
Turbo decode（0 次、1 次、多次迭代）
  ↓ CB/TB CRC
恢复原 payload
```

测试必须覆盖单码块、多码块、filler、`E<K_w`、重复发送和不同 RV；只测试全零输入可能掩盖系统位/校验位顺序错误。

## 与其他概念的关系

[[LTE-CRC 与码块分段]] 决定 `K` 和 filler；[[LTE-QPP 交织]] 决定第二 constituent encoder 的输入顺序；[[LTE-速率匹配与 HARQ 软合并]] 决定收到的三路 LLR；物理层均衡器提供其噪声尺度。

## 待验证问题

- [ ] 选定的 Log-MAP/Max-Log-MAP 量化和停止规则在目标码块长度下是否稳定？
- [ ] 后均衡 LLR 的符号与尺度是否通过非零 payload、单比特翻转和 CRC 测试？

## 证据与待核验

- `STANDARD`：36.212 V16.6.0 §5.1.3.2 的 PCCC、生成多项式和 `D=K+4`。
- `PERSONAL_NOTE`：SISO 迭代接口、LLR 传播、数值稳定性和测试方法。
- `NEEDS_EXTERNAL_REFERENCE`：具体 Log-MAP/Max-Log-MAP 实现的量化、窗口和性能比较。

## 关联笔记

- [[LTE-QPP 交织]]
- [[LTE-CRC 与码块分段]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE-DL-SCH 编码链]]
- [[LTE-UL-SCH 编码链]]
- [[软输出检测]]
