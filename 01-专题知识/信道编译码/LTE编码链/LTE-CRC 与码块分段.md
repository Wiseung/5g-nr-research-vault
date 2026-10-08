---
title: LTE-CRC 与码块分段
aliases:
  - LTE TB CRC CB CRC
  - LTE Turbo 码块分段
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - code/turbo
  - process/crc
  - process/segmentation
  - evidence/3gpp
source:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
related:
  - "[[LTE-Turbo 编码与译码]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
---

# LTE-CRC 与码块分段

> [!abstract] 一句话结论
> LTE 共享数据信道先对传输块附加 CRC24A；当含 TB-CRC 的长度超过 6144 bit 时，按规范允许的码块大小分段，并给每个码块附加 CRC24B。filler 只用于凑齐 Turbo 可用长度，必须保留为 `NULL` 语义。

## 1. CRC 多项式

36.212 §5.1.1 定义的常用多项式为：

$$
g_{CRC24A}(D)=D^{24}+D^{23}+D^{18}+D^{17}+D^{14}+D^{11}+D^{10}+D^7+D^6+D^5+D^4+D^3+D+1,
$$

$$
g_{CRC24B}(D)=D^{24}+D^{23}+D^6+D^5+D+1,
$$

$$
g_{CRC16}(D)=D^{16}+D^{12}+D^5+1,
\qquad
g_{CRC8}(D)=D^8+D^7+D^4+D^3+D+1.
$$

`STANDARD`：DL-SCH/UL-SCH 的传输块使用 CRC24A；多码块时的 CB-CRC 使用 CRC24B；BCH/DCI 等控制分支按各自条款选择 CRC16。CRC 是错误检测，不是纠错码。

## 2. 长度变量

| 符号 | 定义 |
|---|---|
| `A` | TB 有效载荷长度 |
| `L_TB` | TB CRC 长度 |
| `B=A+L_TB` | TB-CRC 后长度 |
| `Z=6144` | 最大码块尺寸（36.212 §5.1.2） |
| `C` | 码块数量 |
| `L_CB` | 每码块 CRC 长度，多码块时为 24 |
| `B'` | 分段并附加 CB-CRC 后总长度 |
| `K_r` | 第 `r` 个码块的实际输入长度 |
| `F` | filler 数量 |

## 3. 分段规则

抽象规则：

```text
若 B ≤ 6144：C=1，L_CB=0，B'=B
若 B > 6144：L_CB=24，C=ceil(B/(6144-24))，B'=B+C·24
从 36.212 的允许 K 集合选择 K+ / K-
按 C+、C- 分配码块，必要时在第一个码块开头加入 F 个 filler
```

更一般地，分段必须满足：

$$
\sum_{r=0}^{C-1}K_r=B'+F,
\qquad
F\ge0,
$$

并且每个 `K_r` 属于适用版本的允许 Turbo 交织块长集合。不要把 6144 当成“必须每块正好 6144”；它是上限，实际 `K_r` 由分段表和 `B'` 共同决定。

36.212 还规定 `B<40` 时会引入 filler。filler 在 CRC 计算时按 0 处理，进入编码器时为 `NULL`，译码后不能作为业务比特交付。

## 4. 发送与接收边界

```text
A bit payload
  ↓ CRC24A
B bits
  ↓ segmentation + optional CRC24B + filler
C 个 c_r[0:K_r-1]
  ↓ Turbo
每个码块独立率匹配
```

接收端先逆率匹配并完成每个码块 Turbo 译码，再检查 CB-CRC、去除 filler、按原顺序拼接，最后检查 TB-CRC24A。

## 5. 可逆性检查

- `C=1` 且 `B≤6144` 时不得无条件添加 CRC24B。
- filler 只出现在规定的第一个码块开头，不能占用新的业务索引。
- `K_r`、CB-CRC 和 filler 位置必须同时传给 Turbo、速率匹配和译码器。
- 只检查 TB-CRC 不能定位某个码块的分段错误；应分别记录 `cb_crc_fail[r]`。

## 6. 最小测试向量

| 用例 | 应检查 |
|---|---|
| `B=40` | 无额外 CB-CRC，长度闭合 |
| `B=6144` | 单码块上限边界 |
| `B=6145` | 进入多码块分支并添加 CB-CRC |
| `B<40` | filler 位置和 `NULL` 语义 |
| 多码块不等长 | `K+ / K- / C+ / C- / F` 计数 |

## 证据与待核验

- `STANDARD`：36.212 V16.6.0 §5.1.1--§5.1.2 的 CRC、多码块和 6144 上限。
- `PERSONAL_NOTE`：长度守恒、状态命名和测试边界。
- `NEEDS_EXTERNAL_REFERENCE`：目标 Release 的完整允许 `K` 表和增强型分支。

## 关联笔记

- [[LTE-Turbo 编码与译码]]
- [[LTE-QPP 交织]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE-DL-SCH 编码链]]
- [[LTE-UL-SCH 编码链]]
