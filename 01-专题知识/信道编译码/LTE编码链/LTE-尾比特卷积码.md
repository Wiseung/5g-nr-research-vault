---
title: LTE-尾比特卷积码
aliases:
  - LTE Tail-biting convolutional code
  - LTE TBCC
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - code/convolutional
  - process/encoding
  - process/decoding
  - evidence/3gpp
source:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
related:
  - "[[LTE-控制信道编码链]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
---

# LTE-尾比特卷积码

> [!abstract] 一句话结论
> LTE 尾比特卷积码（TBCC）是约束长度 7、码率 1/3 的卷积码；初始移位寄存器状态由输入序列最后 6 个比特决定，使编码开始和结束状态相同，不额外发送传统零尾比特。

## 1. 标准定义

36.212 §5.1.3.1 规定：

- constraint length 为 7；
- coding rate 为 1/3；
- 三路输出流 `d^(0), d^(1), d^(2)` 的每路长度 `D=K`；
- 初始状态由最后 6 个信息比特设定，使 trellis 首尾闭合。

适用主分支包括 BCH、DCI，以及部分控制信息；共享 DL-SCH/UL-SCH 则使用 Turbo，不能按载荷长度自动猜编码器。

## 2. 编码/译码状态

```text
c[0:K-1]
  ↓ 用 c[K-6:K-1] 初始化状态
TBCC trellis（K 步）
  ↓
d^(0), d^(1), d^(2)，每路 K bit
  ↓ 子块交织/控制速率匹配
e[0:E-1]
```

接收端的 Viterbi、BCJR 或其他 trellis 译码器必须采用循环状态约束。把初始状态固定为全零会破坏尾比特闭合，尤其在短 BCH/DCI 块上表现明显。

## 3. TBCC 与 Turbo 的区别

| 项目 | TBCC | Turbo |
|---|---|---|
| constituent 结构 | 单个约束长度 7 卷积码 | 两个 8-state RSC + QPP |
| 每路输出长度 | `D=K` | `D=K+4` |
| 终止 | tail-biting，首尾同态 | trellis termination，增加 4 |
| 典型 LTE 承载 | BCH、DCI、部分控制 | DL-SCH、UL-SCH |
| 速率匹配 | convolutional/control 分支 | turbo 分支，带 RV 圆形缓冲区 |

## 4. CRC 掩码不是编码器状态

BCH 的 CRC16 会按 eNB 发射天线端口配置掩码；DCI 的 CRC16 会按 RNTI 掩码。掩码发生在 TBCC 之前，不能把掩码比特混入卷积编码器的 trellis 状态，也不能在译码后跳过反掩码直接检查 CRC。

## 5. 最小测试

- 用非零 `K≥6` 向量检查初始状态和首尾状态相等。
- 比较 3 路输出长度均为 `K`。
- 对 BCH 测试 1/2/4 发射天线 CRC mask；对 DCI 测试多个 RNTI。
- 做无噪声 Viterbi/BCJR 闭环，再加入控制分支速率匹配。

## 证据与待核验

- `STANDARD`：36.212 V16.6.0 §5.1.3.1、§5.3.1、§5.3.3。
- `PERSONAL_NOTE`：循环状态接口、掩码边界和测试建议。
- `NEEDS_EXTERNAL_REFERENCE`：目标 Release 的全部控制信息分支和实现级译码器性能。

## 关联笔记

- [[LTE-控制信道编码链]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE-Turbo 编码与译码]]
- [[LTE-QPP 交织]]
