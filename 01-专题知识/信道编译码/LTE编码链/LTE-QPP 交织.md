---
title: LTE-QPP 交织
aliases:
  - LTE Turbo 内部交织器
  - Quadratic permutation polynomial interleaver
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - code/turbo
  - process/interleaving
  - method/QPP
  - evidence/3gpp
source:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
related:
  - "[[LTE-Turbo 编码与译码]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
---

# LTE-QPP 交织

> [!abstract] 一句话结论
> LTE Turbo 内部交织器用二次置换多项式把输入比特重排到第二个 constituent encoder；置换系数 `f1/f2` 由码块长度 `K` 决定，必须从适用版本的 36.212 表 5.1.3-3 取值。

## 1. 数学表达

36.212 §5.1.3.2.3 给出：

$$
c'_i=c_{\Pi(i)},
\qquad
\Pi(i)=(f_1 i+f_2 i^2)\bmod K,
\quad i=0,1,\ldots,K-1.
$$

`f1`、`f2` 不是可任意调参的“最佳值”，而是与 `K` 绑定的标准表项。当前笔记不复制完整表，以免把版本/索引抄错；实现应保存 `spec_version` 和表号。

## 2. 方向和逆置换

发送端与标准定义一致地构造 `c'`；若 `c'_i=c_{Π(i)}`，接收端第二 constituent decoder 的外信息应按同一映射回到第一 decoder 的坐标：

$$
L_{ext,1}[\Pi(i)]\leftarrow L_{ext,2}[i],
\qquad
L_{ext,1}[j]=L_{ext,2}[\Pi^{-1}(j)].
$$

关键不是变量名，而是发送端、两路译码器和逆率匹配共同使用同一份显式索引表。不要凭 `argsort` 的默认方向猜测逆置换。

## 3. 与子块交织的区别

| 交织器 | 位置 | 目的 | 参数来源 |
|---|---|---|---|
| QPP 内部交织 | Turbo 两个 constituent encoder 之间 | 打散相邻错误、形成并行观测 | `K,f1,f2`，36.212 §5.1.3.2.3 |
| Turbo 速率匹配子块交织 | 每路编码输出到圆形缓冲区之前 | 改善打孔/重复后的可靠性分布 | 36.212 §5.1.4.1.1 |
| 控制/TBCC 子块交织 | 卷积编码控制分支 | 对齐控制速率匹配 | 36.212 §5.1.4.2.1 |
| PUSCH channel interleaver | UL-SCH/UCI 复用后 | 映射到 SC-FDMA 符号和层 | 36.212 §5.2.2.8 |

这几种置换的输入输出域不同，不能共用一个 `interleave()` 而不带类型和长度元数据。

## 4. 单元测试

- 对每个允许 `K` 验证 `Π(i)` 落在 `[0,K-1]`。
- 验证 `Π` 是双射，且 `inverse(Π(i))` 恢复 `i`。
- 用脉冲向量检查位置而非只检查随机比特的汉明重量。
- 对 Turbo 无噪声闭环分别打开/关闭 QPP，确认关闭时测试会失败而不是被全零向量掩盖。

## 5. 证据与待核验

- `STANDARD`：36.212 V16.6.0 §5.1.3.2.3 的二次置换形式和表号。
- `PERSONAL_NOTE`：逆置换接口、类型化索引和测试方法。
- `NEEDS_EXTERNAL_REFERENCE`：完整 `K→(f1,f2)` 表、增强型 Release 分支和硬件布局优化。

## 关联笔记

- [[LTE-Turbo 编码与译码]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE-CRC 与码块分段]]
