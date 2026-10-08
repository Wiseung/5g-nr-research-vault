---
title: 3GPP TS 38.331｜Radio Resource Control protocol specification
aliases:
  - 3GPP 38.331
  - NR RRC 协议规范
  - TS 38.331 无线资源控制
type: reference
status: partial
tags:
  - domain/5g-nr
  - layer/rrc
  - evidence/3gpp
  - topic/system-information
  - topic/bwp
  - topic/rach-config
  - topic/pdcch-config
  - process/rrc-state
source:
  - 3GPP TS 38.331
related:
  - "[[3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[3GPP TS 38.212｜Multiplexing and channel coding]]"
  - "[[3GPP TS 38.213｜Physical layer procedures for control]]"
  - "[[3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[3GPP TS 38.321｜Medium Access Control protocol specification]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]"
  - "[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]"
  - "[[5G-NR-Positioning/03-PDCCH/CORESET|CORESET]]"
  - "[[5G-NR-Positioning/03-PDCCH/Search Space|Search Space]]"
  - "[[5G-NR-Positioning/03-PDCCH/DCI|DCI]]"
---

# 3GPP TS 38.331｜Radio Resource Control protocol specification

> [!abstract] 标准职责
> TS 38.331 定义 NR RRC 协议、RRC 状态和消息、系统信息（MIB/SIB）、小区选择/重选、载波与 BWP、RACH/PRACH、TDD、CORESET/SearchSpace、测量与重配置等配置接口。它向 MAC、物理层和定位相关过程提供半静态上下文，但不替代 38.211/212/213/214/321 对波形、编码、物理过程和 MAC 状态的定义。

## 证据边界与阅读定位

本页状态为 `STANDARD + partial`。项目现场的 Release、ASN.1 版本、扩展字段和设备厂商私有行为尚未锁定；未逐条核验的字段、枚举、位宽和编码不得作为实现事实，统一标记 `NEEDS_EXTERNAL_REFERENCE`。RRC ASN.1 的字段名来自规范导航或本地配置笔记时，仍需回到目标版本原文确认。

阅读建议：

1. 先确认 RRC 状态和消息承载，再读取 MIB/SIB1 及其他系统信息。
2. 从 ServingCellConfigCommon/ServingCellConfig 追踪载波、BWP、RACH、TDD、CORESET、SearchSpace 和 PDSCH/PUSCH 配置。
3. 将 RRC 配置快照交给 MAC 与物理层，保留生效时刻、版本和小区/BWP 上下文。
4. 对 ASN.1 扩展、`lateNonCriticalExtension`、版本分支和厂商私有 IE 只做保守解析。

## RRC 状态与消息

RRC 状态描述 UE 与小区控制连接的阶段；常用导航语境包括 `RRC_IDLE`、`RRC_INACTIVE` 和 `RRC_CONNECTED`。状态名本身不证明已捕获对应消息，状态迁移必须以 RRC 消息、系统信息或可靠设备信令证据为依据。

| 对象 | 典型作用 | 观测边界 |
|---|---|---|
| MIB | 提供初始同步/系统信息获取所需的最小广播入口 | 不等于完整 SIB1 或全部小区配置 |
| SIB1 | 提供小区接入、公共 RACH、SI 调度和基础 serving-cell 线索 | 字段版本、编码和扩展需按 Release 核验 |
| 其他 SI/SIB | 提供按需系统信息，如邻区、测量或其他公共配置 | 未捕获时不能用默认值补齐 |
| RRCSetup/Resume/Reconfiguration | 建立、恢复或更新 UE 专用配置 | 不能将一次重配置快照用于之前时隙 |
| RRCRelease/拒绝/重建 | 结束、拒绝或修复 RRC 上下文 | 需记录消息方向、原因和生效时间 |

```text
广播 MIB/SIB
    ↓
小区公共配置
    ↓ RRCSetup/Resume/Reconfiguration
UE 专用配置与状态
    ↓
MAC/PHY 运行时快照（按生效时间切换）
```

精确消息字段、完整状态迁移、定时器和 ASN.1 编解码规则需引用目标 Release 的条款，当前为 `NEEDS_EXTERNAL_REFERENCE`。

## 系统信息与配置链

```text
MIB / SIB1 / 其他 SI
  ├─ 载波、频点、SCS、TDD 和公共 BWP
  ├─ RACH-ConfigCommon / PRACH occasion / 前导组
  ├─ CORESET0 / SearchSpace0 / 公共 PDCCH
  └─ SI 调度、接入限制和测量线索
          ↓
ServingCellConfigCommon
          ↓
专用 BWP、CORESET、SearchSpace、PUCCH/PUSCH/PDSCH 和测量配置
          ↓
MAC/PHY 过程参数与候选资源
```

被动接收端应保留原始 RRC PDU、解码结果、配置版本、`cell_id`、`serving_cell`、BWP ID 和 `effective_from/effective_until`。仅有一个字段（如 `prach-ConfigurationIndex`）不足以重建完整 PRACH 或 MAC 行为。

## 载波、BWP、PRACH 与 TDD 配置

### 载波与 BWP

RRC 为服务小区提供载波和 BWP 上下文；活动 BWP、初始 BWP、上行/下行载波、Point A、SCS、CP、带宽和频域偏移共同决定局部索引如何映射到绝对资源。日志必须分开保存：

```yaml
carrier:
  cell_id: null
  ncellid: null
  ul_carrier: "NUL|SUL|unknown"
  point_a: null
  scs_hz: null
bwp:
  id: null
  direction: "DL|UL|unknown"
  start_prb: null
  size_prb: null
  cp: "normal|extended|unknown"
  active_from_slot: null
```

字段单位、索引基准、初始/活动 BWP 切换条件和跨载波调度需要目标版本核验；不得把 BWP 局部 PRB 直接当载波绝对子载波。

### RACH/PRACH

RRC 的 `RACH-ConfigCommon`、`RACH-ConfigDedicated` 及 2-step 相关配置为 MAC 随机接入实体提供公共/专用资源和过程输入，包括 PRACH occasion、前导集合、SSB/CSI-RS 映射、响应窗口、尝试上限、功率/退避和 MsgA 资源等。以下是职责链，不是字段完整表：

```text
RRC common/dedicated RACH config
    ↓
MAC 选择 2-step/4-step、CBRA/CFRA、载波、SSB/CSI-RS、RO 和 preamble
    ↓
38.213/38.211 解释 PRACH 时频资源与检测过程
    ↓
38.321 处理 RAR/MsgB、Msg3、Msg4 和争用解决
```

2-step 与 4-step、CBRA 与 CFRA 的互斥/优先关系以及专用资源字段必须结合目标版本和触发原因核验。相关工程化状态见 [[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]] 和 [[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]。

### TDD 与符号方向

RRC 提供 TDD 上下行模式、周期和符号方向等配置线索；物理过程再依据 38.213/38.214 计算特定 slot/symbol 可用性。观测记录应保存 `frame/slot/symbol_set/direction`，区分 `DL`、`UL`、`flexible` 与 `unknown`。不能把灵活符号静默当作 PDCCH 或 PUSCH。

## CORESET、SearchSpace 与 DCI 配置接口

RRC 的 `ControlResourceSet` 描述 CORESET 资源上下文，`SearchSpace` 描述监测时机、聚合等级和候选数量等规则；二者共同进入 38.213 的 PDCCH 监测和 38.211 的 CCE/REG/RE 映射。RRC 配置不包含每个时隙必然存在的 DCI，也不等于已解码的 RNTI。

```text
ControlResourceSet + SearchSpace (RRC)
    ↓
CORESET 频域/时域资源与 CCE/REG 映射上下文
    ↓
Search Space monitoring occasion / candidate
    ↓
PDCCH blind decoding + RNTI/CRC
    ↓
DCI 字段解释（38.212/213/214）
```

配置快照至少保存 `controlResourceSetId`、`searchSpaceId`、BWP、频域位图、duration、监测周期/偏移、聚合等级/候选、common/UE-specific 语境和生效 slot。字段位图编码、候选上限、CORESET0 特殊规则和 ASN.1 版本均标 `NEEDS_EXTERNAL_REFERENCE`。详见 [[5G-NR-Positioning/03-PDCCH/CORESET|CORESET]]、[[5G-NR-Positioning/03-PDCCH/Search Space|Search Space]] 与 [[5G-NR-Positioning/03-PDCCH/DCI|DCI]]。

## 配置输入输出与实现/观测字段

```yaml
rrc_config_snapshot:
  config_id: ""
  release_or_spec_version: "unknown"
  source_message: "MIB|SIB1|SI|RRCSetup|RRCResume|RRCReconfiguration|unknown"
  cell_id: null
  serving_cell: null
  rrc_state: "IDLE|INACTIVE|CONNECTED|unknown"
  effective_from: ""
  effective_until: ""
  carrier_refs: []
  bwp_refs: []
  rach_ref: ""
  tdd_ref: ""
  coreset_refs: []
  search_space_refs: []
  pdsch_pusch_refs: []
  measurement_refs: []
  asn1_decode_state: "complete|partial|failed|unknown"
  verification_state: "ready|partial|NEEDS_EXTERNAL_REFERENCE"
```

实现层应另存原始 ASN.1/字节串引用、解码器版本、扩展字段和未知 IE。不要把 ASN.1 字段版本写成“已核验实现”；没有目标版本和实际消息时，保留 `SOURCE_NOTE_PENDING`。

## 跨规范职责边界

| 主题 | 主要所有者 | RRC 的交接 |
|---|---|---|
| 载波/BWP/CORESET/SearchSpace/PRACH/TDD 配置 | 本规范 38.331 | 产生配置快照；不决定每次 PDCCH/PRACH 是否成功 |
| MAC 服务、随机接入、RAR、HARQ、BSR/SR | [[3GPP TS 38.321｜Medium Access Control protocol specification]] | 提供公共/专用配置和状态输入 |
| 物理信道、参考信号、资源网格 | [[3GPP TS 38.211｜Physical channels and modulation]] | 提供物理参数，不由 ASN.1 字段直接替代映射条款 |
| CRC、LDPC/Polar、率匹配 | [[3GPP TS 38.212｜Multiplexing and channel coding]] | 配置承载类型和参数上下文，不定义编码实现细节 |
| PRACH/PDCCH/HARQ/功控物理过程 | [[3GPP TS 38.213｜Physical layer procedures for control]] | 提供过程配置，精确时序/候选规则按版本计算 |
| PDSCH/PUSCH、MCS、TBS、层/CSI | [[3GPP TS 38.214｜Physical layer procedures for data]] | 提供 BWP、资源和专用配置，字段解释由数据过程完成 |

## 最小核验清单

- [ ] 锁定目标 Release、38.331 文档版本、ASN.1 编解码器版本和消息来源。
- [ ] 从 MIB/SIB1/专用 RRC 消息重建 `config_id`，记录生效时刻，不覆盖旧快照。
- [ ] 核对活动 BWP、载波/Point A、SCS/CP、NUL/SUL 与 TDD 符号方向。
- [ ] 用 RACH 配置覆盖 4-step/2-step、CBRA/CFRA、RO、前导、窗口和 MsgA/fallback 分支；缺字段保持 `NEEDS_EXTERNAL_REFERENCE`。
- [ ] 用 CORESET + SearchSpace 快照重建 PDCCH monitoring occasion/candidate，并与 [[5G-NR-Positioning/03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]] 对齐。
- [ ] 验证 RRC 配置更新、BWP 切换和状态迁移不会继续使用过期 MAC/PHY 参数。
- [ ] 对 ASN.1 扩展、厂商 IE、字段位宽、枚举、完整定时器和工具箱 API 标记 `NEEDS_EXTERNAL_REFERENCE`。

## 原始官方来源

- ETSI TS 138 331 V17.8.0（Release 17 参考入口，版本需按项目实际 Release 复核）：<https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/17.08.00_60/ts_138331v170800p.pdf>
- 3GPP specification portal（TS 38.331，版本列表）：<https://www.3gpp.org/DynaReport/38331.htm>

当前未锁定现场 Release；上述 V17.8.0 链接仅用于回到官方原文。`SOURCE_NOTE_PENDING`：本页尚未逐条摘录目标版本的 ASN.1 模块、完整 IE/扩展、状态定时器和全部载波聚合/测量专用分支。

## 关联笔记

- MAC 与随机接入：[[3GPP TS 38.321｜Medium Access Control protocol specification]]、[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]。
- PDCCH：[[5G-NR-Positioning/03-PDCCH/CORESET|CORESET]]、[[5G-NR-Positioning/03-PDCCH/Search Space|Search Space]]、[[5G-NR-Positioning/03-PDCCH/DCI|DCI]]、[[5G-NR-Positioning/03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]。
- 物理/编码：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.213｜Physical layer procedures for control]]、[[3GPP TS 38.214｜Physical layer procedures for data]]。
- 规范索引：[[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map|3GPP Specification Map]]。
