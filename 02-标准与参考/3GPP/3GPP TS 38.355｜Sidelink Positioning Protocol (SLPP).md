---
title: 3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)
aliases:
  - 3GPP 38.355
  - NR 侧链定位协议
  - SLPP
type: reference
status: partial
created: 2026-09-05
tags:
  - domain/5g-nr
  - layer/positioning-protocol
  - evidence/3gpp
  - topic/slpp
  - topic/sidelink-positioning
  - process/protocol-session
source:
  - "3GPP TS 38.355 V18.8.0 (Release 18)"
  - "[[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]]"
  - "[[5G-NR-Positioning/00-项目总览/Current Learning Path]]"
  - "[[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]"
related:
  - "[[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]"
  - "[[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]"
  - "[[3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[3GPP TS 38.213｜Physical layer procedures for control]]"
  - "[[3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[3GPP TS 38.215｜Physical layer measurements]]"
  - "[[3GPP TS 38.321｜Medium Access Control protocol specification]]"
  - "[[3GPP TS 38.331｜Radio Resource Control protocol specification]]"
  - "[[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]"
  - "[[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]"
  - "[[5G-NR-Positioning/05-定位观测量/Timing Observation]]"
---

# 3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)

> [!abstract] 标准职责
> TS 38.355 规定 NR Sidelink Positioning Protocol（SLPP），用于 UE 与 UE、以及 UE 与 LMF 之间的侧链定位/测距协议交互。ETSI V18.8.0 的范围、功能、过程和 ASN.1 结构覆盖 SL-AoA、SL-RTT、SL-TDOA、SL-TOA 等侧链方法的能力、辅助数据和位置信息转移；它不替代 NR PC5 物理信号、L1 测量定义、RRC/MAC 配置或 NG-RAN 与 LMF 的 NRPPa 控制面。

> [!warning] 版本边界
> 本页以 ETSI `3GPP TS 38.355 V18.8.0 (2026-08), Release 18` 为参考快照。`TS 38.355` 在该官方版本的标题是 **Sidelink Positioning Protocol (SLPP)**；项目文档中不要把它写成 LTE LPP 或 NRPP。跨代 LTE LPP 的入口是 TS 37.355，TS 36.355 在当前 Release 主要转引该规范。具体方法字段、ASN.1 扩展和现场设备支持仍需按目标版本核对。

## 阅读定位

本标准回答“侧链端点如何建立定位会话、交换能力/辅助数据/位置或测量信息，以及如何确认、重传和结束事务”。建议顺序如下：

| 入口 | 读取重点 | 当前项目用途 |
| --- | --- | --- |
| §1--§3 | Scope、引用、术语和缩写 | 先确认端点、PC5 和 SLPP 名称 |
| §4.1.1 | SLPP configuration、session 和 transaction | 建立会话/事务关联键 |
| §4.1.3 | SL-TDOA、SL-TOA、SL-AoA、SL-RTT 方法入口 | 选择方法并区分测量类型 |
| §4.1.4 | 通用消息字段和消息类型 | 设计协议快照和去重/确认状态 |
| 第 5 章 | capability、assistance data、location information、error/abort 过程 | 复现消息时序和结束条件 |
| 第 6 章 | PDU、格式、参数和 ASN.1 | 做版本化编解码器与向量核验 |

协议阅读应和 [[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]] 配套：38.305 说明定位架构和方法在系统中的角色，38.355 说明侧链协议会话；两者都不等于项目内部的 IQ/ToA/TDOA 事件格式。

## 核心实体与协议关系

| 实体 | SLPP 中的角色 | 项目边界 |
| --- | --- | --- |
| SL Target UE | 被一个或多个 SL Anchor UE 支持测量距离、方向或位置的目标 UE | 不因第三方站检测到 PC5 信号就自动获得该身份 |
| SL Anchor UE | 发送/接收定位参考信号、提供测量或定位相关信息的参考 UE | 需要 PC5 和侧链配置，不能默认用 NG-RAN 上行站替代 |
| SL Server UE | 选择方法、分发辅助数据和/或计算目标位置的 UE；目标/锚点 UE 在支持时也可承担此角色 | 协议服务器角色不等同离线 TDOA 求解器 |
| LMF | 在 LMF-involved 场景参与侧链定位服务 | LMF 与 NG-RAN 节点的控制面协作另由 38.305/38.455 组织 |
| Endpoint A/B | 一次 SLPP 事务的协议端点，可为 UE-UE 或位置服务器-UE | 端点方向、上层触发和承载需随消息记录 |

SLPP 会话用于一次位置请求；一个会话可以包含一个或多个事务，事务可串行或并行。事务通过 `transactionID` 关联请求与响应，所有属于同一会话的消息通过 `sessionID` 归组。会话/事务状态不能仅以收到一条消息推断完成。

## 三类核心信息转移

### 能力转移

能力过程用于让端点交换 SLPP 及定位方法能力。典型方向为 `RequestCapabilities` 到 `ProvideCapabilities`；也允许端点主动发送能力指示。能力不代表本次已产生测量值，只表示相应协议/方法可以被支持或报告。

### 辅助数据转移

辅助数据过程用于让一端请求、另一端提供定位所需的侧链参考和方法上下文。`ProvideAssistanceData` 可以分多条消息发送；最后一条通过 `endTransaction` 表示事务结束。未请求的辅助数据是否允许传送、具体方法字段和有效期应按目标版本 ASN.1/字段说明核验。

### 位置信息转移

位置转移过程用于请求或交付测量数据和/或位置估计。典型方向为 `RequestLocationInformation` 到 `ProvideLocationInformation`，也可有无需先请求的交付。请求中的方法、QoS 和结果类型与实际提供的数据必须分别记录，不能将一条测量值直接当作位置估计。

## 定位方法

ETSI V18.8.0 在 SLPP 中定义以下基于 NR PC5 信号的方法：

| 方法 | 语义入口 | 观测边界 |
| --- | --- | --- |
| SL-TDOA | 利用多个侧链参考源/锚点的时间差形成相对位置约束 | 需要多个端点、共同事件和时间参考；项目多站 NG-RAN UL-TDOA 不自动等同 |
| SL-TOA | 利用目标 UE 信号在多个侧链参考 UE 的到达时间相关量 | 参考点、时钟、带宽和首径策略须单独记录 |
| SL-AoA | 由侧链接收端阵列测量方向/角度 | 阵列几何、相位校准和坐标系不可省略 |
| SL-RTT | 基于侧链双方时序交互的往返时间 | 没有双向消息和处理时序时，不能把单向峰差命名为 RTT |

这些方法是协议支持范围，不是现场可见性或定位精度承诺。标准方法名与项目观测名应遵守 [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]] 的五项角色检查：谁发射、谁测量、测量什么、参考是什么、结果如何使用。

## 通用消息字段与状态

ETSI V18.8.0 的 `SLPP-Message` 通用字段包括：

| 字段 | 用途 | 项目记录 |
| --- | --- | --- |
| `sessionID` | 标识同一 SLPP 会话 | 作为会话关联键，保留原始编码引用 |
| `transactionID` | 标识同一事务 | 关联请求、响应和后续消息 |
| `endTransaction` | 指示当前消息是否为该事务最后一条消息 | 记录结束状态，不以文件结束替代 |
| `sequenceNumber` | 支持重复消息检测 | 与重传/去重状态一起保存 |
| `acknowledgement` | 请求确认或指出被确认的序号 | 区分确认、超时和重传 |
| `slpp-MessageBody` | 携带能力、辅助数据、位置信息或方法主体 | 保存消息类型和方法分支 |

协议状态可抽象为：

```text
session_started
    ↓
capability_pending → capability_exchanged
    ↓
assistance_pending → assistance_received
    ↓
location_request → location_or_measurement_received
    ↓
endTransaction / Abort / error
```

这个状态图是项目阅读辅助，不是对所有实现时序的强制替代。确认、重传、重复检测和 Abort 需要按第 5 章过程文字及第 6 章消息字段实现。

## 与相邻规范的职责边界

| 问题 | 主要规范 | 38.355 的边界 |
| --- | --- | --- |
| NR/PC5 物理信号、调制、资源网格和参考信号 | [[3GPP TS 38.211｜Physical channels and modulation]] | SLPP 消费已配置的侧链参考，不重写物理映射 |
| PDCCH/控制资源、监测时机、HARQ 和功率控制 | [[3GPP TS 38.213｜Physical layer procedures for control]] | 不把 SLPP 消息当作 PDCCH 控制过程 |
| PDSCH/PUSCH 数据、MCS、TBS、CSI 和调度 | [[3GPP TS 38.214｜Physical layer procedures for data]] | 不定义数据物理层译码或调度闭包 |
| L1 测量量、参考点、时间/功率/角度定义 | [[3GPP TS 38.215｜Physical layer measurements]] | 侧链协议携带/关联测量结果，测量定义归测量规范 |
| MAC、PC5 服务、资源激活和随机接入 | [[3GPP TS 38.321｜Medium Access Control protocol specification]] | 不从 MAC/PRACH 事件直接推出 SLPP 会话完成 |
| RRC、SIB、BWP、TDD 和侧链/参考信号配置 | [[3GPP TS 38.331｜Radio Resource Control protocol specification]] | 配置来源、生效时刻和版本由 RRC 快照记录 |
| Stage 2 定位架构、方法角色和系统流程 | [[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]] | 本页负责侧链协议会话和消息，不替代架构规范 |
| NG-RAN 节点与 LMF 控制面定位信令 | [[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]] | NRPPa 是 38.455 的职责，不与 SLPP 混称 |

## 实现与观测字段

### 协议快照

下列结构是项目的最小协议登记，不是完整 ASN.1 定义；方法专用字段需要按目标 Release 扩展。

```yaml
slpp_protocol_snapshot:
  spec_number: "38.355"
  spec_version: "V18.8.0"
  release: "Release 18"
  protocol_name: "SLPP"
  source_pdf_title: "Sidelink Positioning Protocol (SLPP); Protocol Specification"
  source_clause: null
  endpoint_a: null
  endpoint_b: null
  transport: "PC5-U or LMF-related transport; verify"
  session_id: null
  transaction_id: null
  message_type: null
  sequence_number: null
  end_transaction: null
  acknowledgement: null
  message_body_type: null
  positioning_method: null # SL_AOA, SL_RTT, SL_TDOA, SL_TOA or unknown
  asn1_decode_state: "unknown"
  duplicate_state: "unknown"
  retransmission_state: "unknown"
  evidence_status: NEEDS_EXTERNAL_REFERENCE
```

协议字段要与 `capture_id`、原始 PDU、编解码器版本和承载层引用绑定。`V18.8.0` 的公共字段已由官方快照核对，但消息主体的完整方法字段、扩展和条件仍应以项目锁定版本复核。

### 项目观测事件

SLPP 信令和项目内部 IQ/定位观测不是同一数据结构。事件字段沿用 [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]，至少保留：

```yaml
observation_event:
  event_id: null
  observation_id: null
  capture_id: null
  station_id: null
  protocol_snapshot_id: null
  config_id: null
  direction: null # PC5, UL, DL or unknown
  signal_kind: null # SL_PRS, PRACH, SRS, PUSCH_DMRS or UNKNOWN
  reference_point: null
  sample_rate_hz: null
  raw_iq_uri: null
  raw_trace_uri: null
  toa_raw_seconds: null
  toa_corrected_seconds: null
  rtoa_seconds: null
  tdoa_seconds: null
  measurement_timestamp: null
  clock_bias_seconds: null
  rf_delay_seconds: null
  filter_group_delay_seconds: null
  calibration_id: null
  quality_state: null
  association_state: null
  source_kind: PERSONAL_NOTE
  evidence_status: NEEDS_VERIFICATION
```

`event_id` 只表示当前证据下可能属于同一物理事件，不能仅凭 `sessionID` 或时间最近就宣称同一 UE。未完成 PC5/协议/校准闭环时，结果保持 `candidate` 或 `feature_only`。

## 最小核验清单

- [ ] 锁定目标 Release、ETSI/3GPP 版本、PDF 标题、发布日期和引用章节。
- [ ] 确认协议端点是 UE-UE 还是 Location Server-UE，并记录 SL Target/Anchor/Server UE 角色。
- [ ] 对每个会话记录 `sessionID`、事务 `transactionID`、消息序号、确认、重传和 `endTransaction` 状态。
- [ ] 分别核对 capability、assistance data、location information、unsolicited delivery、Abort 和 error 流程。
- [ ] 对 SL-AoA/SL-RTT/SL-TDOA/SL-TOA 保存参考信号、资源、时间参考、阵列/坐标和质量上下文。
- [ ] 将 SLPP 事务与 38.305 架构、38.455 NRPPa 控制面和 RRC/MAC 配置分开登记。
- [ ] 将 38.211/38.215 的物理信号/测量定义与协议字段分开；不把协议字段当 raw IQ 或 ToA。
- [ ] 对 ASN.1/PER 编解码保存版本、扩展、未知字段和原始 PDU，不按默认值静默填充。
- [ ] 没有 PC5 捕获、协议 PDU、配置快照和向量测试前，不宣称设备支持、互操作或定位精度。
- [ ] 现场多站结果继续使用 `NEEDS_VERIFICATION`，并保留时钟、RF、滤波、数字链校准和协方差字段。

## 原始来源与证据账本

| 来源 | 证据类型 | 用途 | 当前状态 |
| --- | --- | --- | --- |
| [ETSI TS 38.355 V18.8.0 PDF](https://www.etsi.org/deliver/etsi_ts/138300_138399/138355/18.08.00_60/ts_138355v180800p.pdf) | `STANDARD` | §1、§4、§5、§6 的 SLPP 范围、实体、方法、事务和字段 | `verified snapshot` |
| [3GPP TS 38.355 archive](https://www.3gpp.org/ftp/Specs/archive/38_series/38.355/) | `STANDARD` | 追踪后续/历史 Release，确认版本标题和变更 | `Release 18/19 可见` |
| [ETSI TS 38.305 V18.5.0 PDF](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf) | `STANDARD` | 核对 SLPP 在 NG-RAN 定位架构中的 UE-terminated 角色 | `verified snapshot` |
| [ETSI TS 38.215 V17.2.0 PDF](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf) | `STANDARD + partial` | 物理层测量、参考点和时间/功率/角度口径入口 | `Release 17 快照` |
| [[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]] | `PERSONAL_NOTE` | 当前项目的规范职责和阅读阶段 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]] | `PERSONAL_NOTE` | 标准方法与项目观测命名边界 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]] | `PERSONAL_NOTE` | 项目事件字段；不是 SLPP ASN.1 | `partial` |

### 版本与未决项

- `STANDARD + partial`：本页的协议字段和方法入口以 V18.8.0 Release 18 快照为基准；换用 V18.x、V19.x 或现场实现时须重新核验。
- `NEEDS_EXTERNAL_REFERENCE`：方法专用 ASN.1、IE 存在条件、扩展字段、完整编码/解码行为、跨 Release 变更和设备私有扩展。
- `NEEDS_VERIFICATION`：项目设备是否接收/解析 PC5/SLPP、是否能得到侧链配置和原始 PDU、协议事务能否与观测事件关联。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页未运行 ASN.1/PER 向量、PC5 互操作、SL 定位或测量精度实验。

## 关联笔记

- [[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]
- [[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]
- [[3GPP TS 38.211｜Physical channels and modulation]]
- [[3GPP TS 38.213｜Physical layer procedures for control]]
- [[3GPP TS 38.214｜Physical layer procedures for data]]
- [[3GPP TS 38.215｜Physical layer measurements]]
- [[3GPP TS 38.321｜Medium Access Control protocol specification]]
- [[3GPP TS 38.331｜Radio Resource Control protocol specification]]
- [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]
- [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]
- [[5G-NR-Positioning/05-定位观测量/Timing Observation]]
