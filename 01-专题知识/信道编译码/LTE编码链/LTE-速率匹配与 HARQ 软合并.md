---
title: LTE-速率匹配与 HARQ 软合并
aliases:
  - LTE Turbo rate matching
  - LTE RV circular buffer
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - code/turbo
  - process/rate-matching
  - process/harq
  - evidence/3gpp
source:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
related:
  - "[[LTE-Turbo 编码与译码]]"
  - "[[LTE-CRC 与码块分段]]"
  - "[[LTE-DL-SCH 编码链]]"
---

# LTE-速率匹配与 HARQ 软合并

> [!abstract] 一句话结论
> LTE 速率匹配先对三路编码流做子块交织，再放入圆形缓冲区；DL-SCH/PCH 等 Turbo 分支按 `rv_idx` 选择起点并输出 `E_r` 个比特，接收端必须逆映射到同一母码坐标后累加 LLR，才能进行 HARQ 软合并。

## 1. Turbo 分支的坐标

对码块 `r`：

1. 三路输入为 `d^(0), d^(1), d^(2)`，每路长度 `D=K_r+4`。
2. 各路经过 32 列子块交织，输出长度记为 `K_Π`（含必要 dummy/NULL）。
3. 组成圆形缓冲区 `w`：

$$
K_w=3K_\Pi,
$$

其中系统流、第一校验流、第二校验流按标准顺序放入不同区段；`NULL` 位置不可发送。

4. 依据 `N_cb`、`rv_idx` 和 `k_0` 从圆形缓冲区循环读取，跳过 `NULL`，直到得到 `E_r` 个输出比特。

精确的 `N_IR`、`N_cb`、`k_0` 和 `E_r` 分配依赖传输信道、层数、调制阶数、软缓冲区和 36.212 条款；这里不复制整套设备类别公式。

## 2. RV 的含义

`rv_idx∈{0,1,2,3}` 改变圆形缓冲区的读取起点/坐标选择，不改变 Turbo 母码、QPP 系数或 CB-CRC。初传与重传使用不同 RV 时，接收端必须先按各自映射把 LLR 放回统一母码位置。

## 3. 卷积控制分支

尾比特卷积码和控制信息使用 36.212 §5.1.4.2 的另一套 32 列子块交织与圆形缓冲区。该分支的伪代码从 `j=0` 开始循环读取并跳过 `NULL`，不要把 Turbo 分支的 `k_0(rv_idx)` 公式直接复用到 DCI/控制信息。

## 4. 逆率匹配与软合并

令 `π_r[j]` 是本次发送位置 `j` 对应的母码坐标，接收 LLR 为 `L_r[j]`。逆率匹配初始化为零并累加：

$$
L_{mother}[\pi_r(j)]
\leftarrow L_{mother}[\pi_r(j)]+L_r[j].
$$

对多次传输：

$$
L_{HARQ}(i)=\sum_{t=1}^{T}w_t(i)L_{mother,t}(i),
$$

其中 `w_t` 只有在不同传输的噪声方差/LLR 标度需要校正时才引入；至少要记录是否做过加权。

## 5. 长度和坐标检查

- 每个码块 `E_r` 与标准的 `G` 分配之和必须闭合。
- 逆映射后母码数组长度与 `K_w` 一致，未观测位置保留 0 或规范要求的约束值。
- 重复读取位置必须累加，不能覆盖旧 LLR。
- 码块分段、QPP、子块交织和圆形缓冲区的坐标命名要分层，不能都叫 `i`。

## 6. 最小验证矩阵

| 用例 | 目的 |
|---|---|
| `E_r=K_w`、`rv=0` | 全覆盖、无遗漏 |
| `E_r<K_w` | 打孔/选择和逆映射 |
| `E_r>K_w` | 重复位置 LLR 累加 |
| `rv=0,1,2,3` | 起点与坐标差异 |
| 两次不同 RV | HARQ 软合并后无噪声恢复 |
| 含 filler/NULL | 不把 dummy 当业务证据 |

## 与其他概念的关系

[[LTE-Turbo 编码与译码]] 消费逆率匹配后的三路软信息；[[LTE-CRC 与码块分段]] 提供 `K_r`/filler；[[LTE-DL-SCH 编码链]] 和 [[LTE-UL-SCH 编码链]] 提供 RV、资源和 HARQ 上下文。

## 待验证问题

- [ ] 目标 UE 类别和软缓冲区配置下，`N_cb`/`k_0` 是否与参考实现一致？
- [ ] 多次 RV 传输在相同母码坐标累加后，是否能通过无噪声和有限噪声闭环？

## 7. 证据与待核验

- `STANDARD`：36.212 V16.6.0 §5.1.4.1/§5.1.4.2 的子块交织、圆形缓冲区和选择流程。
- `PERSONAL_NOTE`：逆率匹配 LLR 累加、HARQ 权重和测试矩阵。
- `NEEDS_EXTERNAL_REFERENCE`：目标 UE 类别的 `N_IR/N_cb`、完整 `k_0` 表和层/调制组合。

## 关联笔记

- [[LTE-Turbo 编码与译码]]
- [[LTE-QPP 交织]]
- [[LTE-CRC 与码块分段]]
- [[LTE-DL-SCH 编码链]]
- [[LTE-UL-SCH 编码链]]
