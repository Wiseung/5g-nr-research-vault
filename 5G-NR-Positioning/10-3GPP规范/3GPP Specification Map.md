---
title: 3GPP Specification Map
aliases:
  - 3GPP 规范索引
  - NR 被动定位规范地图
type: reference-index
status: partial
created: 2026-09-04
updated: 2026-09-05
tags:
  - project/5g-nr-positioning
  - domain/3gpp
  - topic/specification
source:
  - 用户项目需求
  - 现有 Vault 3GPP 参考笔记
related:
  - "[[5G NR Passive Positioning Pipeline]]"
  - "[[项目知识地图]]"
  - "[[02-PRACH/Random Access Procedure]]"
  - "[[03-PDCCH/DCI]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.215｜Physical layer measurements]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.321｜Medium Access Control protocol specification]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.331｜Radio Resource Control protocol specification]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]"
---

# 3GPP Specification Map

> [!warning] 版本边界
> 本索引先按“职责和阅读入口”组织，不锁定项目 Release。具体 clause、表格、字段编码和版本差异必须在项目指定的 3GPP 版本中复核；未复核内容标记为 `NEEDS_EXTERNAL_REFERENCE`。

## 规范总览

| 规范 | 主要职责 | 为什么本项目需要看它 | 当前 Vault 入口/状态 |
|---|---|---|---|
| TS 38.211 | 物理信道、信号、调制、资源网格、OFDM、参考信号 | 定义 PRACH/PDCCH/PDSCH/PUSCH/DM-RS 的序列、映射和时频位置 | [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]；`STANDARD + partial` |
| TS 38.212 | CRC、码块分段、LDPC、Polar、率匹配 | 解 DCI、RAR/PDSCH、DL-SCH/UL-SCH 时需要正确逆编码链 | [[02-标准与参考/3GPP/3GPP TS 38.212｜Multiplexing and channel coding]]；`STANDARD + partial` |
| TS 38.213 | 物理层控制过程、PRACH occasion 上下文、PDCCH 监测、HARQ/功控 | 决定何时、在哪些候选和状态下监测 PRACH/PDCCH/RAR | [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control]]；`STANDARD + partial` |
| TS 38.214 | PDSCH/PUSCH 数据过程、MCS/TBS、资源分配、CSI/层 | 把 DCI 字段转换为数据资源、调制和编码参数 | [[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]]；`STANDARD + partial` |
| TS 38.215 | 物理层测量、时间/频率/功率/质量测量 | 核对 UL-RTOA、TADV、参考点和测量口径，与项目自定义 ToA/TDOA 分界 | [[02-标准与参考/3GPP/3GPP TS 38.215｜Physical layer measurements]]；`STANDARD + partial` |
| TS 38.321 | MAC 规范、随机接入、RAR、争用解决、RNTI/MAC CE | PRACH 到临时 C-RNTI/C-RNTI 的协议状态机核心来源 | [[02-标准与参考/3GPP/3GPP TS 38.321｜Medium Access Control protocol specification]]；`STANDARD + partial` |
| TS 38.331 | RRC 配置、SIB1、BWP、CORESET、搜索空间、PRACH/TDD 参数 | 被动接收机通常从 RRC/SIB/设备元数据取得解码所需配置 | [[02-标准与参考/3GPP/3GPP TS 38.331｜Radio Resource Control protocol specification]]；`STANDARD + partial` |
| TS 38.305 | NR 定位架构、定位方法和功能实体 | 区分标准 UL/DL-TDOA、PRS、SRS、Multi-RTT 与本项目定制被动方案 | [[02-标准与参考/3GPP/3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]；`STANDARD + partial` |
| TS 38.355 | Sidelink Positioning Protocol（SLPP） | 连接 UE--UE 或位置服务器--UE 的侧链定位能力、测量和位置请求/响应语境 | [[02-标准与参考/3GPP/3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]；`STANDARD + partial` |
| TS 38.455 | NRPPa/NG-RAN 定位协议接口 | 了解 LMF/NG-RAN 测量与协同信息边界，避免把协议接口当 IQ 接口 | [[02-标准与参考/3GPP/3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]；`STANDARD + partial` |
| TS 36.355 | LTE LPP 定位协议 | 对照 LPP 消息、定位能力和跨代术语；不是 NR PHY 解码主入口 | 尚无专门笔记；`NEEDS_EXTERNAL_REFERENCE` |

## 按项目阶段阅读

### 第一阶段：PRACH/随机接入

1. 38.211：PRACH 序列、格式、资源映射和时频位置。
2. 38.213：PRACH occasion、检测窗口和相关物理过程。
3. 38.321：Msg1/Msg2(RAR)/Msg3/Msg4、争用解决、临时标识和 C-RNTI 状态。
4. 38.331：从 SIB/RRC 获取 PRACH、BWP、TDD 和小区配置。

对应笔记：[[02-PRACH/PRACH Overview]]、[[02-PRACH/Random Access Procedure]]、[[02-PRACH/C-RNTI]]。

### 第二阶段：初始下行与 PDCCH/PDSCH

1. [[01-NR基础/SSB PBCH MIB]]：用 TS 38.211 的 PSS/SSS、SSB/PBCH 映射，TS 38.212 的 BCH 编码和 TS 38.331 的 MIB 建立初始小区上下文。
2. 38.213：依据 MIB/公共 SCS 和目标 Release 表项恢复 CORESET-0、SearchSpace0 及 Type0 CSS 监测语境。
3. 38.331：确认 `pdcch-ConfigSIB1`、CORESET/SearchSpace ASN.1 和 SIB1 配置字段。
4. 38.211：核对 CCE/REG、PDCCH/PDSCH/DM-RS 物理映射。
5. 38.212：核对 DCI Polar/CRC 与 DL-SCH 逆编码。
6. 38.214：从 DCI 恢复 PDSCH/PUSCH 资源、MCS/TBS/RV 等数据过程。

对应笔记：[[01-NR基础/SSB PBCH MIB]]、[[03-PDCCH/CORESET]]、[[03-PDCCH/Search Space]]、[[03-PDCCH/PDCCH Implementation Contract]]、[[03-PDCCH/PDCCH Blind Decoding]]、[[03-PDCCH/DCI]]、[[04-PDSCH/PDSCH]]。

### 第三阶段：测量与定位

1. 38.215：物理层测量和时间参考。
2. 38.305：定位方法、参考信号和架构边界。
3. 38.355：UE--UE/位置服务器--UE 的 SLPP 侧链定位协议和能力/测量消息。
4. 38.455：网络侧 NRPPa 定位协议/测量信息接口。
5. 36.355：LTE LPP 对照，仅在需要跨代定位协议时阅读。

对应笔记：[[05-定位观测量/Timing Observation]]、[[06-TDOA定位/TDOA]]、[[07-多站协同/Multi-Station Synchronization]]。

## Clause 核验表

| 主题 | 首选规范 | clause 状态 | 核验动作 |
|---|---|---|---|
| numerology/资源网格 | 38.211 | `NEEDS_EXTERNAL_REFERENCE` | 锁定 Release 后记录 frame/slot、SCS、RE 坐标条款 |
| PRACH 序列/映射 | 38.211 | `NEEDS_EXTERNAL_REFERENCE` | 核对适用长/短前导、格式和 occasion 映射 |
| PRACH occasion/RAR 上下文 | 38.213 | `NEEDS_EXTERNAL_REFERENCE` | 结合 RRC 配置核对时频资源和响应窗口 |
| Random Access 状态机 | 38.321 | `NEEDS_EXTERNAL_REFERENCE` | 核对 2-step/4-step、CBRA/CFRA、RAR/争用解决字段 |
| CORESET/搜索空间 | 38.331 + 38.213 | `STANDARD + verified-reference (Rel-17 V17.8.0)` | 仍需从实际 SIB/RRC 快照映射候选并确认现场 Release |
| PDCCH CCE/REG | 38.211 | `STANDARD + verified-reference (Rel-17 V17.8.0)` | 参考版本已核对；现场交织、聚合等级和资源索引仍需复核 |
| DCI 编码 | 38.212 | `STANDARD + verified-reference (Rel-17 V17.8.0)` | 参考版本已核对；现场格式长度、CRC 掩码、Polar/率匹配仍需复核 |
| PDSCH 调度/TBS | 38.214 | `NEEDS_EXTERNAL_REFERENCE` | 由 DCI 快照重算资源、MCS、TBS、RV |
| UL/DL 时间测量 | 38.215/38.305 | `STANDARD + partial` | 对照 TUL-RTOA/TADV、定位方法和项目自定义 ToA |
| 侧链定位协议 | 38.355 | `STANDARD + partial` | 核对 SLPP 能力、辅助数据/位置信息请求响应和版本化 ASN.1 |
| NG-RAN 定位协议 | 38.455 | `STANDARD + partial` | 核对 NRPPa 测量、协同信息和 SFN 初始化接口 |
| 跨代定位协议 | 36.355 | `NEEDS_EXTERNAL_REFERENCE` | 仅在需要 LTE LPP 对照时纳入 |

## 规范使用规则

- 标准条款用于定义接口和约束；不把个人笔记的解释直接升级为规范要求。
- 每次代码运行记录 `release_or_toolbox_version`、引用规范版本和配置快照。
- 2-step/4-step、CBRA/CFRA、RNTI 字段和定位测量参考点若未确认，保留多个分支并标 `TODO`。
- 外部规范核对完成后，回写具体 clause 和表号，并在相关原子笔记的证据段同步更新。

## Related Notes

- [[5G NR Passive Positioning Pipeline]]
- [[Current Learning Path]]
- [[02-PRACH/Random Access Procedure]]
- [[02-PRACH/RA-RNTI]]
- [[03-PDCCH/CORESET]]
- [[03-PDCCH/Search Space]]
- [[04-PDSCH/PDSCH]]
- [[05-定位观测量/Timing Observation]]
- [[06-TDOA定位/TDOA]]

## 测量观测层的 Vault 入口（补充）

独立规范页已补入 `02-标准与参考/3GPP`；项目观测接口仍拆分为：

- [[05-定位观测量/Observation Taxonomy]]：标准信号/项目观测的术语边界。
- [[05-定位观测量/Timing Observation]]：ToA、RToA、TDoA、TA 和参考点分离。
- [[05-定位观测量/Quality and Uncertainty]]：测量误差、校准和质量门。
- [[05-定位观测量/Observation Event Schema]]：项目内部字段；不是标准测量报告或 ASN.1。

上述页面和新规范页中的精确条款、表格、ASN.1 字段和 Release 差异仍按各页标记 `NEEDS_EXTERNAL_REFERENCE`；新页提供的是可回查的职责入口，不替代目标版本原文。
