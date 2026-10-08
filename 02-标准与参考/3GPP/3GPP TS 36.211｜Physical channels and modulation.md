---
title: 3GPP TS 36.211｜Physical channels and modulation
aliases:
  - 3GPP 36.211
  - LTE 物理信道与调制
  - E-UTRA 物理层
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
  - topic/physical-channel
  - topic/reference-signal
source:
  - 3GPP TS 36.211 V16.6.0
related:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
  - "[[LTE 物理层与信道模型]]"
  - "[[LTE 参考信号与导频设计]]"
---

# 3GPP TS 36.211｜Physical channels and modulation

> [!abstract] 标准职责
> TS 36.211 规定 E-UTRA 的物理信道、物理信号、资源网格、调制、参考信号和 OFDM/SC-FDMA 波形。它把 [[3GPP TS 36.212｜Multiplexing and channel coding]] 输出的比特连接到 LTE 的时频资源和接收机输入。

## 本页的核验范围

本页以 ETSI 公布的 `3GPP TS 36.211 V16.6.0 (2021-08), Release 16` 为核验基准。LTE 早期 Release 与后续增强功能可能有不同的物理信道或配置字段；下文只把已定位到章节的接口写成 `STANDARD`，不把实现选择写成规范要求。

## 已核对的接口

| 主题 | 核对结论 | 条款 | 证据级别 |
|---|---|---|---|
| 帧结构 | 10 ms 无线帧由 10 个 1 ms 子帧组成；15 kHz、7.5 kHz、2.5 kHz 等配置的 slot 关系由帧结构条款给出 | §4.1、§4.2 | `STANDARD` |
| LTE 资源块 | 15 kHz 常规 LTE PRB 在频域含 12 个子载波、带宽 180 kHz；上行 normal CP 每 slot 7 个 SC-FDMA 符号，extended CP 为 6 个 | §5.2.3、§6.2.3 | `STANDARD` |
| 下行波形 | 下行采用 OFDM 基带生成，循环前缀长度随 CP 配置变化 | §6.12 | `STANDARD` |
| 上行波形 | PUSCH 经过调制、层映射、transform precoding、预编码、资源映射和 SC-FDMA 生成 | §5.3.2--§5.6 | `STANDARD` |
| CRS | 小区专用参考信号在天线端口 0--3 上配置；15 kHz 下按 `v_shift=N_cell_ID mod 6` 进行频域移位 | §6.10.1 | `STANDARD` |
| PDSCH UE-specific RS | 只在对应 PDSCH 所占 PRB 上发送，并且只有与相应端口/传输关联时才是有效的解调参考 | §6.10.3 | `STANDARD` |
| PUSCH DM-RS | PUSCH 解调参考信号由上行参考序列生成并映射到资源；传统 normal CP 的主 DM-RS 符号为 `l=3`，extended CP 为 `l=2` | §5.5.2.1 | `STANDARD` |
| SRS | 支持 basic 和 additional sounding reference signal，用于上行探测；序列和资源映射独立于 PUSCH DM-RS | §5.5.3 | `STANDARD` |
| CSI-RS | 下行 CSI-RS 使用端口 15 及以上的端口集合，服务于 CSI 测量和反馈配置 | §6.10.5 | `STANDARD` |

## 物理层到编码层的边界

```text
36.212 编码/率匹配输出
        ↓
36.211 扰码、调制、层映射和物理资源映射
        ↓
OFDM 或 SC-FDMA 波形
        ↓
接收端 FFT/资源提取/参考信号处理
        ↓
软解调 LLR → 36.212 逆率匹配与译码
```

36.211 不单独决定传输块 CRC、Turbo 码块分段或 DCI 的 CRC 掩码；这些应回到 36.212 的对应承载条款。反过来，36.212 的 `E` 或 `G` 也不能直接当作资源网格坐标，必须经过物理信道的调制阶数、层数和 RE 映射。

## 实现时必须保留的坐标

对每一个数据或参考信号 RE，建议保存以下字段：

| 字段 | 含义 |
|---|---|
| `subframe`, `slot`, `l` | 时间位置 |
| `k`, `n_PRB` | 频域子载波和 PRB 位置 |
| `antenna_port` | 物理天线端口或参考信号端口 |
| `layer`, `codeword` | 空间层和码字归属 |
| `signal_type` | data、CRS、DM-RS、CSI-RS、SRS 或 reserved |
| `local_index`, `absolute_index` | 局部资源网格与载波绝对坐标 |

数组维度正确并不代表映射正确。发送端和接收端应使用同一份资源掩码与索引表验证覆盖、互斥和顺序。

## 版本与功能边界

- `STANDARD`: 本页的条款、PRB/CP、参考信号和波形接口均以 V16.6.0 为基准。
- `NEEDS_EXTERNAL_REFERENCE`: 具体传输模式、CSI-RS 配置索引、完整端口表、带宽组合、特殊子帧和增强型 BL/CE 功能需要按目标 Release 的表格逐项核对。
- `PERSONAL_NOTE`: 接收机中的 LS/LMMSE、ZF/MMSE 和软输出方差属于算法解释，不是 36.211 的规范性规定。

## 原始来源

- [ETSI TS 136 211 V16.6.0 PDF](https://www.etsi.org/deliver/etsi_ts/136200_136299/136211/16.06.00_60/ts_136211v160600p.pdf)，访问日期：2026-09-04。
- [3GPP Specification 36.211](https://www.3gpp.org/dynareport/36211.htm)，用于版本索引；具体条款以 ETSI PDF 为准。

## 证据与待核验

- `STANDARD + partial`：本页列出的章节、资源网格、参考信号和波形接口已按 V16.6.0 PDF 定位。
- `NEEDS_EXTERNAL_REFERENCE`：目标 Release 的完整映射表、传输模式、特殊子帧和设备实现参数尚未逐项复核。

## 关联笔记

- [[LTE 物理层与信道模型]]
- [[LTE 参考信号与导频设计]]
- [[LTE 信道估计算法]]
- [[LTE OFDM 与 SC-FDMA 接收及频域均衡]]
- [[4G LTE 信道估计与均衡]]
