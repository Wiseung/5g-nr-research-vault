---
title: 3GPP TS 36.212｜Multiplexing and channel coding
aliases:
  - 3GPP 36.212
  - LTE 复用与信道编码
  - E-UTRA 信道编译码
type: reference
status: partial
created: 2026-09-04
verified_at: 2026-09-04
release: Release 16
spec_version: V16.6.0
tags:
  - domain/4g-lte
  - domain/LTE
  - layer/physical-layer
  - evidence/3gpp
  - topic/channel-coding
  - topic/rate-matching
source:
  - 3GPP TS 36.212 V16.6.0
related:
  - "[[3GPP TS 36.211｜Physical channels and modulation]]"
  - "[[LTE-DL-SCH 编码链]]"
  - "[[LTE-Turbo 编码与译码]]"
---

# 3GPP TS 36.212｜Multiplexing and channel coding

> [!abstract] 标准职责
> TS 36.212 规定 E-UTRA 的 CRC、码块分段、尾比特卷积码、Turbo 码、速率匹配、码块级联、控制信息编码以及上行数据/控制复用。它是 LTE 编译码链的主要标准入口。

## 本页的核验范围

基准为 `3GPP TS 36.212 V16.6.0 (2021-08), Release 16`。LTE 的基础链路在不同 Release 中保持相同的主干，但控制格式、增强型短 TTI、侧链路和 BL/CE 分支会增加额外条款；未逐表核验的字段保留 `NEEDS_EXTERNAL_REFERENCE`。

## 编码分支总表

| 承载或控制信息 | 编码方案 | 母码率/典型边界 | 条款 | 证据级别 |
|---|---|---|---|---|
| UL-SCH、DL-SCH、PCH、MCH | Turbo coding | 1/3；每个码块含三路输出和 trellis termination | §5.1.3.2、§5.2.2、§5.3.2 | `STANDARD` |
| BCH | Tail-biting convolutional coding | 约束长度 7、1/3；PBCH CRC 为 16 bit 并按天线配置掩码 | §5.1.3.1、§5.3.1 | `STANDARD` |
| DCI | Tail-biting convolutional coding | 1/3；CRC16 与 RNTI 绑定 | §5.1.3.1、§5.3.3 | `STANDARD` |
| CFI | Block code | 规范给出 1/16 分支和码字表 | §5.1.3、§5.3.4 | `STANDARD` |
| HI | Repetition code | 规范给出 1/3 分支 | §5.1.3、§5.3.5 | `STANDARD` |
| UCI | Block code 或 tail-biting convolutional code | 取决于 UCI 类型、载荷长度和承载方式 | §5.1.3、§5.2.2.6、§5.2.3、§5.2.4 | `STANDARD`，具体格式待核验 |

LTE 主干没有 NR 的 Polar/LDPC 分支。把 NR 的 `BG/Z` 或 Polar `N/K` 账本直接搬到 LTE，会丢失 Turbo 的内部交织、终止比特和循环缓冲区状态。

## 已核对的长度不变量

对一条 LTE 共享信道 Turbo 链，建议保留以下变量：

| 变量 | 含义 |
|---|---|
| `A` | 传输块有效载荷长度 |
| `L_TB` | 传输块 CRC 长度；DL/UL-SCH 采用 24 bit CRC-A |
| `B=A+L_TB` | TB-CRC 后长度 |
| `C` | 码块数 |
| `K_r` | 第 `r` 个码块输入长度，含适用的 CB-CRC 和 filler |
| `D_r=K_r+4` | Turbo 每路编码输出长度，包含 trellis termination |
| `E_r` | 第 `r` 个码块的速率匹配输出长度 |
| `G=Σ_r E_r` | 码块级联后的物理信道编码比特数 |

通用分段边界为：若 `B≤6144`，则 `C=1` 且不附加 CB-CRC；若 `B>6144`，每个码块附加 24 bit CRC-B，并按规范允许的 `K` 集合分配长度。Filler 置于第一个码块开头，进入编码器时作为 `NULL`，不是有效业务比特。

## 编码链与可逆边界

```text
TB/控制字段
    ↓ CRC（必要时掩码）
码块分段 + CB-CRC + filler
    ↓
Turbo 或尾比特卷积编码
    ↓
子块交织 + 循环缓冲区 + 速率匹配
    ↓
码块级联/控制复用
    ↓
36.211 调制、层映射和资源映射
```

接收端必须在软信息域逆转这些边界。尤其是：

1. 重复位置的 LLR 要累加，不能覆盖。
2. Turbo 码的三路系统/校验流要按同一交织和圆形缓冲区坐标恢复。
3. 只有通过 TB-CRC（以及适用时 CB-CRC）的结果才可交付上层。

## 标准事实与实现约定

| 类别 | 示例 | 记录方式 |
|---|---|---|
| `STANDARD` | 编码分支、CRC 多项式、6144 上限、`D=K+4` | Release、章节、表号 |
| `PERSONAL_NOTE` | Log-MAP/Max-Log-MAP 译码器、迭代停止策略、LLR 归一化 | 注明为实现选择 |
| `EXPERIMENT` | Turbo 迭代次数与 BLER 曲线 | 保存参数、种子、帧数和错误数 |
| `NEEDS_EXTERNAL_REFERENCE` | 完整 QPP 参数表、所有控制格式位宽、目标 Release 的软缓冲区规则 | 不填猜测值 |

## 原始来源

- [ETSI TS 136 212 V16.6.0 PDF](https://www.etsi.org/deliver/etsi_ts/136200_136299/136212/16.06.00_60/ts_136212v160600p.pdf)，访问日期：2026-09-04。
- [3GPP Specification 36.212](https://www.3gpp.org/dynareport/36212.htm)，用于版本索引；具体条款以 ETSI PDF 为准。

## 证据与待核验

- `STANDARD + partial`：本页列出的编码分支、CRC、分段和速率匹配接口已按 V16.6.0 PDF 定位。
- `NEEDS_EXTERNAL_REFERENCE`：完整 QPP 参数表、所有控制格式和目标 Release 的软缓冲区规则尚未逐项复核。

## 关联笔记

- [[LTE-Turbo 编码与译码]]
- [[LTE-尾比特卷积码]]
- [[LTE-QPP 交织]]
- [[LTE-CRC 与码块分段]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE-DL-SCH 编码链]]
- [[LTE-UL-SCH 编码链]]
- [[LTE-控制信道编码链]]
- [[4G LTE 信道编译码]]
