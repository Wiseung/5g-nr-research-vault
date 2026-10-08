---
title: LTE-控制信道编码链
aliases:
  - LTE BCH DCI UCI 编码
  - LTE 控制信息编码链
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - channel/pbch
  - channel/pdcch
  - channel/pucch
  - code/convolutional
  - process/encoding
  - evidence/3gpp
source:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
  - "[[3GPP TS 36.211｜Physical channels and modulation]]"
related:
  - "[[LTE-尾比特卷积码]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
---

# LTE-控制信道编码链

> [!abstract] 一句话结论
> LTE 控制与广播信息不是一个统一编码分支：BCH/DCI 使用尾比特卷积码，CFI 使用固定块码，HI 使用重复码，UCI 根据类型和承载方式使用块码或尾比特卷积码。控制 CRC 的掩码还可能携带天线配置或 RNTI 语义。

## 1. 分支总表

| 信息 | 物理承载 | CRC/附加字段 | 编码 | 速率匹配/映射 |
|---|---|---|---|---|
| BCH | PBCH | 24 bit TB，CRC16；按 eNB 天线端口掩码 | TBCC 1/3 | convolutional/control RM |
| DCI | PDCCH | CRC16；按 RNTI 掩码 | TBCC 1/3 | convolutional/control RM |
| CFI | PCFICH | 由 CFI 值映射固定输入 | block code 1/16 | 规范码字表 |
| HI | PHICH | 控制字段 | repetition 1/3 | 规范重复/正交映射 |
| UCI | PUCCH/PUSCH | 依 UCI 类型 | block code 或 TBCC 1/3 | PUCCH/PUSCH 专用流程 |

表中编码分支和速率比来自 36.212 §5.1.3 的控制信息表（`STANDARD`）。完整 UCI 格式、位宽和资源分配需要目标 Release 的具体子条款。

## 2. BCH/PBCH

36.212 §5.3.1 的抽象链：

```text
BCH transport block（A=24 bit）
  ↓ CRC16
CRC parity 与 eNB 天线端口掩码组合
  ↓ TBCC 1/3，D=K
  ↓ convolutional rate matching
  ↓ 36.211 PBCH 资源映射
```

CRC mask 由发射天线端口数决定；接收端必须先根据候选端口反掩码，再做 CRC 检查。PBCH 的物理资源和调制映射属于 36.211，不能只用 36.212 的编码输出测试替代。

## 3. DCI/PDCCH

```text
DCI payload A
  ↓ CRC16
CRC 与 RNTI bitwise mask
  ↓ TBCC 1/3
  ↓ convolutional rate matching
  ↓ 36.211 PDCCH REG/CCE 映射
```

RNTI 掩码是候选判决的一部分：盲检接收端对每个候选聚合等级/位置形成 LLR、TBCC 译码，再用对应 RNTI 检查 CRC。`crc_fail`、`wrong_candidate`、`resource_invalid` 和 `llr_invalid` 应分别记录。

## 4. CFI 与 HI

- CFI 的编码由 36.212 §5.3.4 的固定码字表给出；不要把它送入 TBCC。
- HI 的主干是重复码，物理映射/正交序列由相关条款决定。
- `CFI=1/2/3` 是字段语义，不等于编码器输入长度或 PDCCH 的 DCI 位宽。

## 5. UCI

UCI 可能包含 HARQ-ACK、RI、CQI/PMI 等。其编码取决于：

1. PUCCH 或 PUSCH 承载。
2. 字段类型和载荷长度。
3. 是否与 UL-SCH 同时存在。
4. TDD/FDD、层数、调制和可用资源。

在 PUSCH 上，UCI 通常先独立编码得到 `q`，再与 UL-SCH 的 `f` 通过数据/控制复用和 channel interleaver 形成发送序列。接收端必须按同一 `mux_index` 分离，不能凭长度切片。

## 6. 控制接收机接口

| 输入/输出 | 必须显式记录 |
|---|---|
| 候选 | RNTI、聚合等级、资源位置、格式 |
| 软信息 | LLR 符号、尺度、均衡方差 |
| TBCC | 循环初始状态、三路流、译码器状态 |
| CRC | CRC 类型、mask、反掩码顺序 |
| 结果 | `decode_success`、`crc_fail`、`dtx`、`candidate_ambiguous` |

## 7. 最小验证顺序

1. 无噪声 BCH：分别测试 1/2/4 天线 mask。
2. 无噪声 DCI：测试多个 RNTI 和候选坐标。
3. CFI/HI 固定码字和重复映射。
4. 单类 UCI，再加入 PUSCH UL-SCH 复用。
5. 接入 LTE 参考信号估计和均衡，验证 LLR 误差如何影响控制 CRC。

## 证据与待核验

- `STANDARD`：36.212 §5.1.3、§5.3.1、§5.3.3--§5.3.5 的编码分支、CRC 和控制流程；36.211 的 PBCH/PDCCH/PUCCH 物理映射。
- `PERSONAL_NOTE`：候选状态、掩码边界、复用索引和验证顺序。
- `NEEDS_EXTERNAL_REFERENCE`：全部 UCI 载荷阈值、PUCCH 格式位宽、控制资源/正交序列表和 Release 增强分支。

## 关联笔记

- [[LTE-尾比特卷积码]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE-UL-SCH 编码链]]
- [[LTE 参考信号与导频设计]]
- [[3GPP TS 36.212｜Multiplexing and channel coding]]
