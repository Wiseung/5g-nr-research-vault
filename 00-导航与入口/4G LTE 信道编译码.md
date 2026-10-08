---
title: 4G LTE 信道编译码
aliases:
  - LTE 信道编码与译码
  - 4G E-UTRA 信道编译码
type: moc
status: partial
created: 2026-09-04
tags:
  - moc/4g-lte
  - domain/4g-lte
  - domain/LTE
  - topic/channel-coding
---

# 4G LTE 信道编译码

> [!abstract] 核心结论
> LTE 的共享数据信道（DL-SCH、UL-SCH）主干采用 Turbo coding；BCH 和 DCI 采用 1/3 尾比特卷积码；CFI、HI、UCI 则按控制信息类型使用块码、重复码或尾比特卷积码。完整链路必须同时追踪 CRC、码块分段、Turbo/TBCC、QPP/子块交织、速率匹配、物理映射、LLR 和 HARQ 软合并。

## 知识总览

| 信息类型 | 典型物理承载 | 编码主干 | 关键笔记 |
|---|---|---|---|
| DL-SCH | PDSCH | Turbo 1/3 | [[LTE-DL-SCH 编码链]] |
| UL-SCH | PUSCH | Turbo 1/3 | [[LTE-UL-SCH 编码链]] |
| BCH | PBCH | 尾比特卷积码 1/3 | [[LTE-控制信道编码链]] |
| DCI | PDCCH | 尾比特卷积码 1/3，CRC 与 RNTI 绑定 | [[LTE-控制信道编码链]] |
| CFI/HI | PCFICH/PHICH | 块码/重复码 | [[LTE-控制信道编码链]] |
| UCI | PUCCH 或 PUSCH | 块码或尾比特卷积码，依格式和载荷而定 | [[LTE-控制信道编码链]] |

LTE 不是 NR 的“低版本 LDPC/Polar”：它的共享数据链有 Turbo 内部交织、终止比特和圆形缓冲区，控制链还存在 RNTI/天线配置相关的 CRC 掩码。

## 编码链总览

### DL-SCH/UL-SCH 数据链

```text
传输块 A
  ↓ TB-CRC24A
码块分段（必要时 CB-CRC24B + filler）
  ↓
Turbo 编码（两路 8-state constituent encoder）
  ↓ QPP 内部交织 + 三路子块交织
圆形缓冲区/速率匹配（按 DL/UL 数据链配置使用 RV）
  ↓ 码块级联
36.211 扰码、调制、层映射、物理资源映射
```

### 控制与广播链

```text
BCH/DCI/UCI/CFI/HI 字段
  ↓ 对应 CRC 或字段保护
尾比特卷积码/块码/重复码
  ↓ 子块交织与控制专用速率匹配
PBCH/PDCCH/PUCCH/PHICH/PCFICH
```

## 推荐学习路径

1. [[信道编码基础]]、[[CRC 校验]]、[[软判决与 LLR]]、[[BLER 与 BER]]。
2. [[LTE-CRC 与码块分段]]：先固定 `A/B/C/K_r/F` 边界。
3. [[LTE-Turbo 编码与译码]]、[[LTE-QPP 交织]]：理解 Turbo 的三路软信息接口。
4. [[LTE-速率匹配与 HARQ 软合并]]：建立 `E_r`、RV 和逆率匹配账本。
5. [[LTE-DL-SCH 编码链]] 与 [[LTE-UL-SCH 编码链]]：连接物理信道资源。
6. [[LTE-控制信道编码链]]、[[LTE 仿真：Turbo 编解码闭环]]：做控制分支和端到端验证。

## LTE 与 NR 的关键差异

| 维度 | LTE | NR |
|---|---|---|
| 共享数据信道 | Turbo | LDPC |
| 典型控制信道 | 尾比特卷积码/块码/重复码 | Polar、小块码等 |
| 码块上限主干 | 6144 bit（36.212） | 由 LDPC 基图和提升因子决定 |
| 内部交织 | Turbo QPP | LDPC/Polar 各自的结构 |
| 终止方式 | Turbo trellis termination；TBCC tail-biting | 由对应码结构决定 |
| HARQ 软合并 | Turbo 圆形缓冲区坐标 | LDPC 率匹配坐标 |

## 长度账本

共享数据信道最小账本：

$$
A\xrightarrow{+L_{TB}}B
\xrightarrow{segmentation}\{K_r\}_{r=0}^{C-1}
\xrightarrow{Turbo}D_r=K_r+4
\xrightarrow{rate\ matching}E_r
\xrightarrow{concat}G=\sum_rE_r.
$$

这里 `D_r` 是每一路 Turbo 输出长度；三路合计为 `3D_r`。`E_r` 是第 `r` 个码块本次实际发送的长度，不能与母码长度或调制符号数混用。

## 验证顺序

```text
无噪声 CRC/分段闭环
  ↓
单码块 Turbo 编码与逆率匹配
  ↓
多码块 CB-CRC 与 filler
  ↓
RV/HARQ LLR 软合并
  ↓
PDSCH/PUSCH 资源映射与真实信道
```

每一层都要记录 `release/spec_version`、承载、`A/B/C/K_r/D_r/E_r/G`、CRC 类型、交织参数、LLR 约定、随机种子和停止规则。

## 当前状态与缺口

| 节点 | 状态 | 下一步 |
|---|---|---|
| 36.212 V16.6.0 规范摘录 | `STANDARD + partial` | 按目标 Release 补充条款/表号 |
| Turbo/TBCC/QPP 原子笔记 | `PERSONAL_NOTE + STANDARD` | 写参考实现并做无噪声向量测试 |
| DL-SCH/UL-SCH 链 | `partial` | 接入 LTE 36.211 物理映射 |
| 控制分支 | `partial` | 按 UCI 格式逐表核验 |
| 仿真 | `EXPERIMENT + NEEDS_VERIFICATION` | 运行并保存帧数、错误数和版本 |

## 来源账本

| 节点 | source_kind | status | 主要内容 |
|---|---|---|---|
| [[3GPP TS 36.212｜Multiplexing and channel coding]] | `STANDARD` | `partial` | CRC、码块分段、Turbo/TBCC、QPP、两类速率匹配和控制分支 |
| [[LTE-CRC 与码块分段]] | `STANDARD + PERSONAL_NOTE` | `partial` | `A/B/C/K_r/F` 与 CB-CRC/filler 边界 |
| [[LTE-Turbo 编码与译码]] | `STANDARD + PERSONAL_NOTE` | `partial` | PCCC、8-state RSC、终止比特和迭代 LLR |
| [[LTE-QPP 交织]] | `STANDARD + PERSONAL_NOTE` | `partial` | `\Pi(i)`、逆置换和交织器边界 |
| [[LTE-速率匹配与 HARQ 软合并]] | `STANDARD + PERSONAL_NOTE` | `partial` | 圆形缓冲区、RV、逆率匹配和 LLR 累加 |
| [[LTE-DL-SCH 编码链]] / [[LTE-UL-SCH 编码链]] | `STANDARD + PERSONAL_NOTE` | `partial` | PDSCH/PUSCH 承载级链路和 HARQ |
| [[LTE-控制信道编码链]] | `STANDARD + PERSONAL_NOTE` | `partial` | BCH、DCI、CFI、HI、UCI 分支 |
| [[LTE 仿真：Turbo 编解码闭环]] | `EXPERIMENT` | `NEEDS_VERIFICATION` | 无噪声、分段、RV/HARQ 和迭代实验设计 |

## 冲突与缺口

- LTE 共享数据的 Turbo 主干与 NR 的 LDPC 主干不可互换；这是设计边界，不是待解决冲突。
- `NEEDS_EXTERNAL_REFERENCE`：完整 QPP `K→(f1,f2)` 表、控制格式位宽、软缓冲区/`N_cb` 细节和目标 Release 的增强分支。
- `NEEDS_VERIFICATION`：译码器迭代性能、HARQ 增益和端到端 BLER 尚无本地运行结果。

## 入口问题

- 为什么 LTE 共享数据使用 Turbo，而 BCH/DCI 使用尾比特卷积码？
- `B>6144` 时 CB-CRC 和 filler 如何改变每个 Turbo 码块的 `K_r`？
- QPP 内部交织和三路子块交织分别解决什么问题？
- RV 只改变发送坐标，还是改变 Turbo 母码本身？
- PUSCH 上 UCI 与 UL-SCH 的复用为什么不能在译码后再猜顺序？
- 为什么无噪声硬比特正确仍不足以证明 LLR 和逆率匹配正确？

## 证据边界

- `STANDARD`：[[3GPP TS 36.212｜Multiplexing and channel coding]] 中已定位的编码分支、CRC、分段和速率匹配条款。
- `PERSONAL_NOTE`：本 MOC 的统一长度/LLR接口和调试顺序。
- `NEEDS_EXTERNAL_REFERENCE`：完整 QPP 参数表、所有控制格式、特定 Release 的软缓冲区和设备 API。

## 关联入口

- [[4G LTE 信道估计与均衡]]
- [[LTE-DL-SCH 编码链]]
- [[LTE-UL-SCH 编码链]]
- [[LTE-控制信道编码链]]
- [[3GPP TS 36.212｜Multiplexing and channel coding]]
