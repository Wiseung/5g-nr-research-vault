---
title: 3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)
aliases:
  - 3GPP 38.455
  - NRPPa
  - NG-RAN 定位控制面协议
type: reference
status: partial
created: 2026-09-05
tags:
  - domain/5g-nr
  - layer/positioning-protocol
  - evidence/3gpp
  - topic/nrppa
  - topic/control-plane
  - topic/measurement-transfer
  - process/protocol-transaction
source:
  - "3GPP TS 38.455 V18.8.0 (Release 18)"
  - "[[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]]"
  - "[[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]"
  - "[[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]"
  - "[[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]"
related:
  - "[[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]"
  - "[[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]"
  - "[[3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[3GPP TS 38.213｜Physical layer procedures for control]]"
  - "[[3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[3GPP TS 38.215｜Physical layer measurements]]"
  - "[[3GPP TS 38.321｜Medium Access Control protocol specification]]"
  - "[[3GPP TS 38.331｜Radio Resource Control protocol specification]]"
  - "[[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]"
  - "[[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]"
  - "[[5G-NR-Positioning/05-定位观测量/Timing Observation]]"
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA]]"
---

# 3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)

> [!abstract] 标准职责
> TS 38.455 规定 NG-RAN 节点与 LMF 之间的控制面无线网络层信令过程。NRPPa 通过 NGAP 提供的下层服务交换定位相关信息，包括 E-CID、OTDOA 信息、定位信息、测量信息、TRP 信息、PRS/辅助信息以及定位激活/预配置等过程；它是网络侧定位控制面协议，不是 UE 侧 LPP/SLPP，也不是第三方接收机的 IQ 或 ToA 数据格式。

> [!warning] 版本边界
> 本页以 ETSI `3GPP TS 38.455 V18.8.0 (2026-07), Release 18` 为参考快照。现场 Release、gNB/NG-RAN 支持的过程和可选 IE 尚未锁定；表格中的消息/IE 名称按该快照复核，精确存在条件、扩展和版本差异仍需 `NEEDS_EXTERNAL_REFERENCE`。本页不把 NRPPa 与 `TS 38.355` 的 SLPP 或跨代 LPP 混称。

## 阅读定位

本标准回答“LMF 如何请求 NG-RAN 节点提供定位支持或测量，以及 NG-RAN 节点如何返回结果/失败/更新”。建议按下列入口阅读：

| 入口 | 读取重点 | 项目用途 |
| --- | --- | --- |
| §1--§3 | Scope、引用、实体和缩写 | 确认协议端点及术语 |
| §4 | 过程书写原则、前后向兼容和符号约定 | 设计接收端的消息/IE/错误处理 |
| §5--§7 | NRPPa 服务、下层 NGAP、协议功能 | 建立模块、事务和承载边界 |
| §8 | Elementary、Location/Measurement/Assistance/Management procedures | 追踪请求、响应、报告、更新和失败 |
| §9.1 | 消息功能定义与内容 | 核对方向、必选/可选 IE 和过程字段 |
| §9.2--§9.3 | IE 定义、ASN.1 和 PDU 结构 | 实现版本化编解码器和反向解析 |
| §10 | 未知、未预见和错误协议数据处理 | 将语法、语义、临界性和 Cause 分层记录 |

38.455 的协议阅读应与 [[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]] 配套：38.305 负责定位架构、方法和操作语义，38.455 负责 LMF/NG-RAN 节点之间的控制面消息。

## 核心实体与事务

| 实体/状态 | NRPPa 中的职责 | 观测边界 |
| --- | --- | --- |
| LMF | 定位服务器；发起请求、配置/激活测量，接收信息并用于位置估计 | 项目位置解算器不自动等同 LMF |
| NG-RAN node | gNB 或 ng-eNB；执行/协调请求的定位支持、测量和报告 | 设备采集站不自动等同 NG-RAN node |
| gNB | NR 定位测量、SRS/PRS/TRP 信息和目标 UE 相关配置的网络节点 | 真实测量结果需来自 gNB/协议或明确的项目采集路径 |
| ng-eNB | E-UTRA 相关定位信息/测量的 NG-RAN 节点 | LTE 分支需按对应字段和规范版本核验 |
| TRP/RP/TP | NG-RAN 节点管理的传输/接收点；测量结果通常与 TRP ID 关联 | `station_id` 与 TRP ID 不应无证据直接互换 |
| AMF/NGAP | 提供 NRPPa 下层传输；AMF 对 NRPPa PDU 透明路由 | NGAP 信令不是测量数值或原始 IQ |
| gNB-CU | split gNB 场景下的 NRPPa 终止点 | 需从部署架构快照确认 |

38.305 将 NRPPa 事务分为两类：

- **UE-associated procedure**：与特定 UE 相关，包含定位信息、E-CID 定位信息和测量预配置等过程；
- **non-UE-associated procedure**：适用于 NG-RAN 节点及其 TRP，包含 OTDOA、辅助信息、TRP、测量和 PRS 信息等过程。

同一 LMF 与 NG-RAN 节点之间可以并行执行多个 NRPPa 过程。发起方生成的 `NRPPa Transaction ID` 用来把属于同一过程的请求、成功/失败响应及后续报告关联起来；不能用时间邻近或单个测量值替代事务 ID。

## 承载与通用流程

```text
LMF 选择定位方法/测量任务
    ↓ NRPPa PDU
NGAP over NG-C（AMF 透明路由）
    ↓
NG-RAN node / gNB-CU
    ↓
配置 UE SRS、查询 TRP/PRS、执行或安排测量
    ↓
NRPPa response / report / update / failure
    ↓ NGAP over NG-C
LMF 接收标准测量上下文并计算/合并位置
```

NRPPa 不直接规定 LMF 如何从测量求位置；例如 UL-TDOA 的几何解算方法超出定位方法本身的协议交换边界。项目若使用多站 IQ 生成被动 ToA/TDOA，应另存 `capture_id`、采样坐标、校准和协方差，不把结果伪装成 NRPPa PDU。

## 过程与消息族

| 过程族 | 典型消息/方向 | 主要用途 |
| --- | --- | --- |
| E-CID 测量 | `E-CID MEASUREMENT INITIATION REQUEST/RESPONSE/FAILURE`、`E-CID MEASUREMENT REPORT`、`...TERMINATION COMMAND` | 请求、报告和结束 E-CID 测量 |
| OTDOA 信息 | `OTDOA INFORMATION REQUEST/RESPONSE/FAILURE` | 交换 OTDOA/PRS 相关小区/传输点信息 |
| 定位信息 | `POSITIONING INFORMATION REQUEST/RESPONSE/FAILURE/UPDATE` | 请求或更新目标 UE 的 SRS/定位信息 |
| TRP 信息 | `TRP INFORMATION REQUEST/RESPONSE/FAILURE` | 查询 NG-RAN 节点托管的 TRP 信息 |
| 测量信息 | `MEASUREMENT REQUEST/RESPONSE/FAILURE`、`MEASUREMENT REPORT/UPDATE/ABORT/FAILURE INDICATION` | 配置、报告、更新或终止定位测量 |
| 定位激活 | `POSITIONING ACTIVATION REQUEST/RESPONSE/FAILURE`、`POSITIONING DEACTIVATION` | 激活/停用 UE 的相关 SRS 传输 |
| PRS 配置 | `PRS CONFIGURATION REQUEST/RESPONSE/FAILURE` | 配置或更新 DL-PRS 传输 |
| 测量预配置 | `MEASUREMENT PRECONFIGURATION REQUIRED/CONFIRM/REFUSE`、`MEASUREMENT ACTIVATION` | 预配置并激活/停用 measurement gap 或 PRS processing window |
| SRS 资源保留 | `SRS INFORMATION RESERVATION NOTIFICATION` | 在定位有效区域保留/释放 SRS 信息 |
| 辅助信息 | `ASSISTANCE INFORMATION CONTROL/FEEDBACK` | 控制和反馈定位辅助信息广播 |
| 管理/错误 | `ERROR INDICATION` | 报告不能用特定失败消息表达的通用错误 |

消息方向、响应是否允许为空、周期报告/按需报告、可选 IE 和错误条件必须以目标 Release 的 §8/§9 表格为准。消息名本身不代表过程已经成功执行。

## UL-TDOA 的 NRPPa 观测链

38.305 V18.5.0 的 UL-TDOA 过程以不同 TRP 对 UE 上行 SRS 的 UL-RTOA（可选 UL-SRS-RSRP、UL-SRS-RSRPP、UL-RSCP 等）测量为基础，使用 NRPPa 将配置和结果与 LMF 交换。典型顺序为：

```text
LMF → serving gNB：POSITIONING INFORMATION REQUEST
    ↓
gNB → LMF：POSITIONING INFORMATION RESPONSE / FAILURE
    ↓（SRS 配置或更新）
LMF → gNB/TRP：MEASUREMENT REQUEST
    ↓
gNB/TRP：执行多 TRP 上行测量
    ↓
gNB → LMF：MEASUREMENT RESPONSE / REPORT / UPDATE / FAILURE
```

### 定位信息消息的字段类别

V18.8.0 `POSITIONING INFORMATION REQUEST`/`RESPONSE`/`UPDATE` 表中可见的字段类别包括：

- `NRPPa Transaction ID`；
- `Requested SRS Transmission Characteristics`、`UE Reporting Information`、`UE TEG Information Request`；
- `Time Window Information SRS List`、`Requested SRS Preconfiguration Characteristics List`；
- `SRS Configuration`、`SFN Initialisation Time`、`UE Tx TEG Association List`；
- `SRS Transmission Status`、`New NR CGI`/`New Cell Identity`、`Positioning Validity Area Cell List`；
- `SRS Preconfiguration List`、`Remote UE-Indication`/`Remote UE Status`。

这些字段用于交换 UE 的上行定位配置和状态，不等于第三方接收端从采样中估计出的 ToA。`SFN Initialisation Time`、UE Tx TEG 关联和 SRS 配置需要与 RRC/MAC 生效时间闭合。

### 测量消息的字段类别

`MEASUREMENT REQUEST`/`RESPONSE`/`REPORT`/`UPDATE` 等消息的关键字段类别包括：

| 字段类别 | 例子 | 作用 |
| --- | --- | --- |
| 事务/测量标识 | `NRPPa Transaction ID`、`LMF Measurement ID`、`RAN Measurement ID` | 关联 LMF 请求、RAN 实例和后续报告 |
| TRP 资源 | `TRP ID`、`TRP Measurement Request/Response/Report List` | 指定测量点及每点结果 |
| 测量配置 | `Search Window Information`、`SRS Configuration`、`Report Characteristics`、`Measurement Periodicity` | 定义窗口、SRS 和按需/周期报告 |
| 测量数量 | `TRP Measurement Quantities`、`Measurement Time Occasion`、`Measurement Amount` | 指定 UL-RTOA、UL-AoA、功率等测量内容 |
| 时间/调度 | `SFN Initialisation Time`、`System Frame Number`、`Slot Number`、`Response Time` | 绑定测量时间上下文 |
| 质量/失败 | `Measurement Characteristics Request Indicator`、`Cause`、`Criticality Diagnostics` | 请求质量信息并表达失败/诊断 |

### TRP 测量结果与项目映射

V18.8.0 `TRP Measurement Result` 的测量结果类别包括 `UL Angle of Arrival`、`UL SRS-RSRP`、`UL RTOA Measurement`、`gNB Rx-Tx Time Difference`、`Z-AoA`、`Multiple UL-AoA`、`UL SRS-RSRPP` 和 `UL RSCP`，并可带：

- `Time Stamp`、`Measurement Quality`、`Measurement Beam Information`；
- `SRS Resource type`、`ARP ID`、`LoS/NLoS Information`；
- `Mobile TRP Location Information`、`Measured Frequency Hops`；
- `Aggregated Positioning SRS Resource ID List` 及相关资源/坐标上下文。

这些是 NRPPa 标准消息中的结果类别。项目内部应另存 raw/corrected ToA、采样率、峰策略、滤波群时延、站间时钟偏置、校准版本和协方差；标准字段有值也不表示项目已经满足标准测量参考点或报告条件。

## 消息、IE 与 ASN.1 边界

V18.8.0 将 NRPPa PDU 分为 `initiatingMessage`、`successfulOutcome` 和 `unsuccessfulOutcome`。每类 PDU 都包含过程代码、临界性、`NRPPa Transaction ID` 和过程值；过程值内部由该消息允许的 `ProtocolIE-Container` 组成。规范第 9.3 的 ASN.1 优先于第 9.1/9.2 表格中的结构描述，但条件存在规则仍需按表格核对。

通用实现账本至少保存：

- `Message Type`、`Procedure Code` 和 `Criticality`；
- `NRPPa Transaction ID`；
- 消息允许的 IE 名称、存在状态、未知 IE 和扩展；
- `Cause`、`Criticality Diagnostics` 和失败方向；
- 原始 NGAP 容器引用、ASN.1/PER 解码器版本和解码状态。

不要把 ASN.1/PER 的编码位数、IE ID 或数组索引从某个版本复制到另一个版本；目标版本不明时，只登记可读名称并标记 `NEEDS_EXTERNAL_REFERENCE`。

## 与相邻规范的职责边界

| 问题 | 主要规范 | 38.455 的边界 |
| --- | --- | --- |
| 物理信道、PRS/SRS/DM-RS、调制、RE/端口和波形 | [[3GPP TS 38.211｜Physical channels and modulation]] | NRPPa 只交换定位控制/结果相关信息，不定义物理映射 |
| PDCCH 监测、控制时序、HARQ 和功率过程 | [[3GPP TS 38.213｜Physical layer procedures for control]] | 只引用控制/时序上下文，不替代 PDCCH 过程 |
| PDSCH/PUSCH 数据、MCS、TBS、CSI 和调度 | [[3GPP TS 38.214｜Physical layer procedures for data]] | 不定义数据传输或业务译码 |
| L1 测量量、参考点、窗口、时间/功率/角度口径 | [[3GPP TS 38.215｜Physical layer measurements]] | NRPPa 携带/报告测量，测量定义归 38.215 |
| MAC、随机接入、MAC CE、SRS/PC5 激活交接 | [[3GPP TS 38.321｜Medium Access Control protocol specification]] | 不把 PRACH/MAC 事件直接写成 NRPPa 定位结果 |
| RRC、SIB、BWP、TDD、RACH、SRS/PRS 配置 | [[3GPP TS 38.331｜Radio Resource Control protocol specification]] | 以 RRC 配置作为消息中的资源/状态输入 |
| Stage 2 架构、定位方法、LMF/UE/NG-RAN 角色 | [[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]] | 38.455 实现其中 LMF↔NG-RAN 控制面信令 |
| UE-UE/UE-LMF 侧链定位协议 | [[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]] | SLPP 与 NRPPa 端点、承载和消息分开 |

## 实现与观测字段

### NRPPa 消息账本

```yaml
nrppa_message:
  spec_number: "38.455"
  spec_version: "V18.8.0"
  release: "Release 18"
  direction: "LMF_TO_NG_RAN|NG_RAN_TO_LMF"
  association_mode: "UE_ASSOCIATED|NON_UE_ASSOCIATED|unknown"
  procedure_name: null
  message_type: null
  procedure_code: null
  criticality: null
  nrppa_transaction_id: null
  lmf_measurement_id: null
  ran_measurement_id: null
  target_ue_ref: null
  trp_ids: []
  ies:
    present: []
    unknown: []
    extensions: []
  ngap_container_ref: null
  asn1_decode_state: "unknown"
  cause: null
  criticality_diagnostics: null
  source_pdf_title: "NR Positioning Protocol A (NRPPa)"
  evidence_status: NEEDS_EXTERNAL_REFERENCE
```

`lmf_measurement_id`、`ran_measurement_id`、`trp_ids` 和 `ies` 只在对应消息/版本存在时填入；未知、不适用和未解析不能用零值混淆。

### 项目观测事件

NRPPa 消息与项目的采样/观测事件需要通过引用关联，而不是共用字段名。沿用 [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]] 的最小字段：

```yaml
observation_event:
  event_id: null
  observation_id: null
  capture_id: null
  station_id: null
  protocol_message_ref: null
  config_id: null
  signal_kind: null # SRS, PUSCH_DMRS, PRACH, PRS or UNKNOWN
  direction: null # UL, DL or unknown
  reference_point: null
  sample_rate_hz: null
  raw_iq_uri: null
  raw_trace_uri: null
  measurement_timestamp: null
  peak_index_integer: null
  fractional_samples: null
  peak_policy: null
  toa_raw_seconds: null
  toa_corrected_seconds: null
  rtoa_seconds: null
  tdoa_seconds: null
  clock_bias_seconds: null
  rf_delay_seconds: null
  filter_group_delay_seconds: null
  calibration_id: null
  uncertainty_std_seconds: null
  quality_state: null
  association_state: null
  source_kind: PERSONAL_NOTE
  evidence_status: NEEDS_VERIFICATION
```

标准 NRPPa 结果（例如 UL-RTOA、时间戳和质量）与项目 `toa_raw_seconds`/`tdoa_seconds` 不应共用一列。只有在 UE/NG-RAN/TRP、SRS、参考点、版本、事务和报告路径均闭合时，项目事件才可作为标准结果的对照，而不是自动成为标准报告。

## 最小核验清单

- [ ] 锁定目标 Release、ETSI/3GPP 版本、PDF 标题、发布日期和引用章节。
- [ ] 确认 LMF、NG-RAN node、gNB/ng-eNB、TRP/RP/TP、AMF 和 split gNB 终止点。
- [ ] 为每个事务记录 UE-associated/non-UE-associated、方向、`NRPPa Transaction ID` 和并行实例。
- [ ] 核对下层 NGAP/NG-C 路由，确认 AMF 透明转发，不把 NGAP 当测量数据。
- [ ] 按 §8/§9 核对请求、成功/失败响应、报告、更新、终止、激活和错误消息的方向与条件。
- [ ] 对 UL-TDOA 核对 SRS 配置、SRS 传输时间、测量 TRP、UL-RTOA 及质量/时间戳字段。
- [ ] 对每个消息保存 `LMF Measurement ID`、`RAN Measurement ID`、TRP 列表和原始 IE/PDU 引用（适用时）。
- [ ] 将 38.211/215 的物理信号与测量定义、38.321/331 的 MAC/RRC 配置和 NRPPa 消息分层。
- [ ] 对 ASN.1/PER 解码保存版本、扩展、未知 IE、Cause、Criticality Diagnostics 和解码状态。
- [ ] 项目 raw IQ、ToA/TDOA、校准、协方差和事件关联字段独立于标准协议字段。
- [ ] 未有真实 NGAP/NRPPa PDU、配置快照、编解码向量和现场测量前，不宣称互操作、标准合规或定位精度。

## 原始来源与证据账本

| 来源 | 证据类型 | 用途 | 当前状态 |
| --- | --- | --- | --- |
| [ETSI TS 38.455 V18.8.0 PDF](https://www.etsi.org/deliver/etsi_ts/138400_138499/138455/18.08.00_60/ts_138455v180800p.pdf) | `STANDARD` | §1、§4--§10 的 Scope、模块、过程、消息/IE、ASN.1 和错误处理 | `verified snapshot` |
| [3GPP TS 38.455 archive](https://www.3gpp.org/ftp/Specs/archive/38_series/38.455/) | `STANDARD` | 查询后续/历史 Release 和变更 | `Release 15--19 可见` |
| [ETSI TS 38.305 V18.5.0 PDF](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf) | `STANDARD` | 核对 NRPPa 在 NG-RAN 定位架构中的角色、事务类型和 UL-TDOA 流程 | `verified snapshot` |
| [ETSI TS 38.215 V17.2.0 PDF](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf) | `STANDARD + partial` | 核对 UL-RTOA、SRS、时间戳、参考点和质量测量语义 | `Release 17 快照` |
| [[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]] | `PERSONAL_NOTE` | 项目规范职责地图和阅读顺序 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]] | `PERSONAL_NOTE` | 标准测量主体与项目被动观测边界 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]] | `PERSONAL_NOTE` | 项目事件字段；不是 NRPPa ASN.1 | `partial` |

### 版本与未决项

- `STANDARD + partial`：本页以 V18.8.0 Release 18 为参考快照；现场 Release 和可选过程未锁定。
- `NEEDS_EXTERNAL_REFERENCE`：目标版本的完整 IE 条件、ASN.1 扩展、消息大小/编码细节、Cause/criticality 行为、后续 Release 差异和设备私有扩展。
- `NEEDS_VERIFICATION`：项目是否能取得 NGAP/NRPPa PDU、RRC/MAC/SRS 配置、标准测量报告和可关联的真实 TRP/UE 事件。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页未运行 ASN.1/PER 编解码、NGAP 互操作、UL-TDOA 测量或定位精度实验。

## 关联笔记

- [[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]
- [[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]
- [[3GPP TS 38.211｜Physical channels and modulation]]
- [[3GPP TS 38.213｜Physical layer procedures for control]]
- [[3GPP TS 38.214｜Physical layer procedures for data]]
- [[3GPP TS 38.215｜Physical layer measurements]]
- [[3GPP TS 38.321｜Medium Access Control protocol specification]]
- [[3GPP TS 38.331｜Radio Resource Control protocol specification]]
- [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]
- [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]
- [[5G-NR-Positioning/05-定位观测量/Timing Observation]]
- [[5G-NR-Positioning/06-TDOA定位/TDOA]]
