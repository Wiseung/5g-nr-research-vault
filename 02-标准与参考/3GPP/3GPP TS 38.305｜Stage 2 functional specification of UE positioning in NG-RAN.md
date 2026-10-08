---
title: 3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN
aliases:
  - 3GPP 38.305
  - NG-RAN UE 定位 Stage 2
  - NR 定位架构与定位方法
type: reference
status: partial
created: 2026-09-05
tags:
  - domain/5g-nr
  - layer/positioning
  - evidence/3gpp
  - topic/positioning-architecture
  - topic/positioning-method
  - process/positioning
source:
  - "3GPP TS 38.305 V18.5.0 (Release 18)"
  - "[[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]]"
  - "[[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]"
  - "[[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]"
related:
  - "[[3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[3GPP TS 38.213｜Physical layer procedures for control]]"
  - "[[3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[3GPP TS 38.215｜Physical layer measurements]]"
  - "[[3GPP TS 38.321｜Medium Access Control protocol specification]]"
  - "[[3GPP TS 38.331｜Radio Resource Control protocol specification]]"
  - "[[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]"
  - "[[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]"
  - "[[5G-NR-Positioning/05-定位观测量/Timing Observation]]"
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA]]"
---

# 3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN

> [!abstract] 标准职责
> TS 38.305 规定 NG-RAN UE 定位功能的 Stage 2 架构、功能实体、定位方法、状态/操作和支持这些方法的消息流程。ETSI V18.5.0 的范围限定在 NG-RAN Access Stratum，并覆盖 NR PC5 下、有覆盖和无覆盖场景中的 ranging 与 sidelink positioning；它不规定定位结果在核心网或 RRM 中的后续使用，也不替代具体物理层、测量协议或位置算法。

> [!warning] 版本边界
> 本页以 ETSI `3GPP TS 38.305 V18.5.0 (2025-04), Release 18` 为参考快照。项目尚未锁定现场 Release；方法清单、接口字段、状态分支和条款编号在换版后必须重新核对。`STANDARD + partial` 只表示参考快照中已定位的职责和流程入口，不表示现场 NG-RAN 已支持或项目已实现。

## 阅读定位

本标准回答“谁参与定位、采用什么方法、测量/辅助数据如何在 UE、NG-RAN 与 LMF 之间流动”。建议按以下顺序阅读：

| 入口 | 读取重点 | 对项目的用途 |
| --- | --- | --- |
| §1 | Stage 2 范围与 NG-RAN Access Stratum 边界 | 防止把核心网定位服务或算法实现写成 38.305 内容 |
| §§4.1--4.3 | 定位的测量/位置估计两步、方法角色和标准方法 | 区分发射源、测量主体、标准方法与项目被动观测 |
| §§5.1--5.4 | 5GS 定位架构、UE/NG-RAN/LMF/TRP/PRU 功能 | 建立实体和控制面关系 |
| §§6.1--6.5 | NR-Uu、NG-C、NL1、RRC、MAC、LPP、NRPPa 等承载边界 | 追踪定位消息如何穿过网络，而不是把协议当作 IQ 接口 |
| §§7.1--7.2 | 通用 LPP 与 NRPPa 事务/过程 | 识别能力、辅助数据、测量和位置结果的流程顺序 |
| 第 8 章 | 各定位方法的信息转移和方法特定过程 | 重点对照 §8.10 Multi-RTT、§8.12 DL-TDOA、§8.13 UL-TDOA |

标准所说的定位通常包含两个主要步骤：信号测量，以及基于测量计算位置估计和可选速度。测量可由 UE 或 serving ng-eNB/gNB 执行，位置估计可在 UE 或 LMF 完成；“测量值存在”不等于“项目第三方接收站已具备同一标准测量主体”。

## 核心实体与职责

| 实体 | 38.305 中的职责轮廓 | 项目观测边界 |
| --- | --- | --- |
| UE | 按选定方法测量下行/侧链信号，或接收辅助数据并提供位置测量/估计 | 被动第三方站不自动等同于 UE 测量主体 |
| gNB | 为目标 UE 提供定位相关信息，可管理多个 TRP，并可执行/汇报上行测量 | gNB 的标准测量结果与项目站的 raw IQ/ToA 需分列 |
| ng-eNB | 为目标 UE 提供 E-UTRA 相关定位测量和信息 | LTE 分支不能用 NR 物理字段替代 |
| TRP/TP/RP | 发射/接收定位参考或承担测量的传输、接收点；一个 NG-RAN 节点可管理多个点 | 站点坐标、参考面和接收链校准属于项目输入，不能从名称推断 |
| LMF | 接收定位请求，选择方法，交换能力/辅助数据，协调 UE/NG-RAN 测量并计算/合并位置结果 | 项目离线 TDOA 解算器不自动等同 LMF |
| PRU | 在已知位置执行参考测量或发送 SRS，帮助位置服务器得到校正信息 | 公共校准源/回环可作为项目校准对象，但不应冒充 PRU 标准流程 |
| AMF/5GC | 承接位置服务请求并为 LMF、NG-RAN 提供控制面路径；具体核心网服务不由本页定义 | 不把 AMF/NGAP 路由字段当成物理测量字段 |
| SLP/E-SMLC | 与用户面或 E-UTRA 互通的相关定位实体；其细节由相应规范负责 | 只有实际接入相应协议时才建立关联 |

## 架构与通用流程

```text
位置服务请求
    ↓
AMF / 5GC 将请求交给 LMF
    ↓
LMF 获取 UE/NG-RAN 能力，选择一种或多种定位方法
    ↓
LMF 下发辅助数据或请求配置
    ├─ LPP / RRC / MAC → UE 或服务小区
    └─ NRPPa → NG-RAN 节点及其 TRP
    ↓
UE 或 NG-RAN 测量定位参考/无线信号
    ↓
测量结果、质量/不确定度和方法上下文返回 LMF
    ↓
UE 或 LMF 计算/合并位置估计及可选速度
    ↓
结果按上层位置服务路径返回
```

同一定位任务可以组合多个方法，标准也允许不同过程按串行或并行方式运行。上图只表达角色边界，不表示项目目前已完成任何网络接口互操作。具体位置算法、双曲线解算和精度保证不由 38.305 的方法章节替代。

## 标准定位方法与项目关系

ETSI V18.5.0 的方法清单包含网络辅助 GNSS、LTE OTDOA/E-CID、NR E-CID、Multi-RTT、DL-AoD、DL-TDOA、UL-TDOA、UL-AoA，以及 NR PC5 上的 SL-RTT、SL-AoA、SL-TDOA、SL-TOA 等。方法名称带有测量主体和参考信号前提，不能由一个相关峰或一组站间时间差自动升级得到。

| 方法/对象 | 标准中的典型测量主体和输入 | 项目保守命名 |
| --- | --- | --- |
| DL-TDOA | UE 测量多个 NR TRP 的 DL RSTD，并结合 TRP 地理坐标和相对下行定时 | 第三方站监听下行源差异；不能直接写成 UE DL-TDOA |
| UL-TDOA | 多个 TRP 对 UE 上行 SRS 测量 UL-RTOA 等结果，LMF 使用这些结果估计 UE 位置 | 无 LMF/gNB 配置与报告闭环时写 `passive_ul_toa/rtoa/tdoa_candidate` |
| Multi-RTT | UE 与多个传输点执行双向时序交互 | 被动单向监听不能默认称 RTT |
| PRS 相关观测 | 下行 PRS 资源、TRP/TP 定时和地理信息 | 可作下行参考候选，但不自动提供 UE 身份 |
| SRS/定位 SRS | UE 上行 SRS 配置、多个测量点、参考时间和报告路径 | 可作上行多站观测候选，标准测量名称须按 38.215/38.455 核验 |
| PRACH 相关峰 | 随机接入前导、RO、根序列/循环移位和检测窗口 | 事件触发/粗 ToA；不能直接推出 C-RNTI 或标准 UL-RTOA |
| SL 定位/测距 | NR PC5 侧链信号和 UE 间协作 | 当前项目第三方 NG-RAN 监听不自动覆盖 |

### UL-TDOA 的标准流程入口

在 V18.5.0 §8.13 中，UL-TDOA 使用不同 TRP 对 UE 上行信号的 UL-RTOA 测量，并可带 UL-SRS-RSRP、UL-SRS-RSRPP 或 UL-RSCP 等量。为获得上行测量，TRP 需要知道测量期间 UE SRS 的特性；LMF 可要求 serving gNB 配置 SRS，gNB 将配置结果返回 LMF，LMF 再把必要信息提供给测量 TRP。gNB 也可能因为资源不可用而返回空配置或失败。

V18.5.0 §8.13.2.2 列出的 NG-RAN 到 LMF 结果类别包括：

- 测量对应的 NCGI 和 TRP ID；
- UL-RTOA、UL-SRS-RSRP、UL-SRS-RSRPP、UL-RSCP；
- UL AoA（方位/俯仰，若该方法组合需要）；
- SRS resource type、测量时间戳、每项质量、beam information、LoS/NLoS 信息；
- ARP ID、移动 TRP 信息、测量频率跳变和聚合定位 SRS 资源等可选上下文。

上述是标准结果的字段类别，不是项目内部 `raw_iq_uri`、峰值索引、滤波群时延或校准字段。38.215 负责各测量量的定义和参考点，38.455 负责 NG-RAN 与 LMF 间的 NRPPa 承载。

## 与相邻规范的职责边界

| 问题 | 主要规范 | 38.305 的位置 |
| --- | --- | --- |
| PRACH/PDCCH/PDSCH/PUSCH、PRS/SRS/DM-RS 的序列、调制、RE/端口和波形 | [[3GPP TS 38.211｜Physical channels and modulation]] | 只选择定位方法所需信号及其系统角色，不重写物理映射 |
| PDCCH 监测、控制时序、HARQ/功控及部分资源控制 | [[3GPP TS 38.213｜Physical layer procedures for control]] | 提供定位流程所需的控制过程背景 |
| PDSCH/PUSCH 资源、MCS、TBS、CSI 和数据过程 | [[3GPP TS 38.214｜Physical layer procedures for data]] | 说明定位参考可能依赖的数据/资源上下文 |
| L1 测量量、测量主体、参考点、窗口和报告口径 | [[3GPP TS 38.215｜Physical layer measurements]] | 选择并组合测量方法；不替代单个测量定义 |
| MAC 随机接入、MAC CE、SRS 激活和调度交接 | [[3GPP TS 38.321｜Medium Access Control protocol specification]] | 通过通用过程引用 MAC 行为；不把 PRACH 峰写成 MAC 身份 |
| RRC/SIB、RACH、TDD、BWP、CORESET/SearchSpace、SRS/PRS 配置 | [[3GPP TS 38.331｜Radio Resource Control protocol specification]] | 需要这些配置来解释 UE/NG-RAN 定位操作 |
| UE/LMF 或 UE/UE 的侧链定位协议 | [[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]] | 38.305 只规定架构中的协议角色和承载关系 |
| LMF/NG-RAN 节点控制面定位信令 | [[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]] | 38.305 规定其在 NG-C/NGAP 路径中的位置 |

## 实现与观测字段

### 标准定位上下文

下面是项目用于记录标准解释所需的字段集合；它不是 38.305 的 ASN.1 消息定义，也不暗示每个字段在所有方法中都存在。

```yaml
positioning_context:
  capture_id: null
  config_id: null
  release_or_spec_version: "unknown"
  standard_clause: null
  target_ue_ref: null
  positioning_method: null # NR_E-CID, MULTI_RTT, DL_TDOA, UL_TDOA, UL_AOA or unknown
  measurement_entity: null # UE, gNB, TRP, RP, PRU, third_party_station or unknown
  serving_cell_id: null
  ng_ran_node_id: null
  lmf_ref: null
  trp_ids: []
  reference_signal: null # PRS, SRS, DM-RS, PRACH or unknown
  assistance_data_ref: null
  resource_config_ref: null
  measurement_quantities: []
  measurement_timestamp: null
  quality_ref: null
  uncertainty_ref: null
  coordinate_system: null
  report_path: null # LPP, NRPPa, RRC, project_event or unknown
  procedure_state: null
  standard_status: NEEDS_EXTERNAL_REFERENCE
```

### 项目观测事件

项目内部字段应沿用 [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]，并和标准字段分开：

```yaml
observation_event:
  event_id: null
  observation_id: null
  capture_id: null
  station_id: null
  signal_kind: null # PRACH, PUSCH_DMRS, SRS, PRS or UNKNOWN
  direction: null # UL, DL or unknown
  config_id: null
  reference_point: null
  sample_rate_hz: null
  raw_iq_uri: null
  peak_index_integer: null
  fractional_samples: null
  peak_policy: null # strongest, first_detected, cluster or unknown
  toa_raw_seconds: null
  toa_corrected_seconds: null
  rtoa_seconds: null
  tdoa_seconds: null
  calibration_id: null
  clock_bias_seconds: null
  rf_delay_seconds: null
  filter_group_delay_seconds: null
  cfo_hz: null
  snr_db: null
  uncertainty_std_seconds: null
  association_state: null
  quality_state: null
  source_kind: PERSONAL_NOTE
  evidence_status: NEEDS_VERIFICATION
```

`toa_raw_seconds`、`rtoa_seconds` 和 `tdoa_seconds` 有值，不代表它们满足 38.215 的参考点、SRS、测量主体和报告要求。缺少标准配置/报告链时，项目结果保持 `project_observation_only` 或 `NEEDS_EXTERNAL_REFERENCE`。

## 最小核验清单

- [ ] 锁定目标 Release、ETSI/3GPP 版本、发布日期和本次引用的章节/表格。
- [ ] 对定位请求记录 target UE、serving cell、NG-RAN node、LMF、TRP/TP/RP 和测量主体。
- [ ] 将标准方法（DL/UL-TDOA、Multi-RTT、AoA、PRS/SRS）与项目被动 `ToA/RToA/TDoA candidate` 分开命名。
- [ ] 从 38.331/RRC 与 38.321/MAC 快照闭合 PRS/SRS/PRACH、TDD、BWP 和生效时刻。
- [ ] 对 UL-TDOA 核对 SRS 配置、测量 TRP、参考时间、UL-RTOA 口径、时间戳和质量字段。
- [ ] 对 DL-TDOA 核对 UE 测量主体、TRP 坐标/相对定时和 DL-PRS 配置，不能用第三方下行峰替代。
- [ ] 对 LPP/SLPP/NRPPa/NGAP/RRC 记录协议终止点和承载路径，不把协议 PDU 当原始 IQ。
- [ ] 对项目 ToA/TDOA 保存 raw/corrected 分离、参考面、时钟/RF/滤波/数字校准和协方差引用。
- [ ] 不把一个 PRACH 相关峰、一个 CRC 通过或一个 C-RNTI 候选升级为唯一 UE 或定位结果。
- [ ] 未运行真实 IQ、标准互操作或重复测量前，不填写现场精度、检测率和实时延迟结果。

## 原始来源与证据账本

| 来源 | 证据类型 | 用途 | 当前状态 |
| --- | --- | --- | --- |
| [ETSI TS 38.305 V18.5.0 PDF](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf) | `STANDARD` | §1、§4、§5、§6、§7、§8 的范围、架构、方法与流程入口 | `verified snapshot` |
| [[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]] | `PERSONAL_NOTE` | 当前项目的规范职责地图和阅读顺序 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]] | `PERSONAL_NOTE` | 发射源、测量主体、参考信号与项目命名边界 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Timing Observation]] | `PERSONAL_NOTE` | ToA/RToA/TDoA、峰策略、参考点和校准字段 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]] | `PERSONAL_NOTE` | 项目内部事件结构；不是 38.305/ASN.1 消息 | `partial` |
| [[3GPP TS 38.215｜Physical layer measurements]] | `STANDARD + partial` | UL-RTOA、PRS、SRS、TADV 等测量语义和参考点入口 | `Release 17 快照` |
| [[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]] | `STANDARD + partial` | LMF/NG-RAN 控制面定位信令入口 | `Release 18 快照` |

### 版本与未决项

- `STANDARD + partial`：本页引用的是 V18.5.0 参考快照；未锁定项目现场 Release，不能把其表格或可选分支泛化到所有网络。
- `NEEDS_EXTERNAL_REFERENCE`：目标 Release 的完整 ASN.1、方法能力矩阵、测量误差/精度要求、所有可选 IE、RRC/MAC 配置字段和 38.305 与其他版本的变更记录。
- `NEEDS_VERIFICATION`：项目是否能捕获/解析标准 LPP、SLPP、NRPPa、SRS/PRS 及标准报告；第三方被动 UL-TDOA 是否满足标准测量主体和参考点。
- `EXPERIMENT + NEEDS_VERIFICATION`：真实站点同步、RF/数字链延迟、ToA/TDOA/位置误差、标准互操作和实时延迟均未在本页产生结果。

## 关联笔记

- [[3GPP TS 38.211｜Physical channels and modulation]]
- [[3GPP TS 38.213｜Physical layer procedures for control]]
- [[3GPP TS 38.214｜Physical layer procedures for data]]
- [[3GPP TS 38.215｜Physical layer measurements]]
- [[3GPP TS 38.321｜Medium Access Control protocol specification]]
- [[3GPP TS 38.331｜Radio Resource Control protocol specification]]
- [[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]
- [[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]
- [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]
- [[5G-NR-Positioning/05-定位观测量/Timing Observation]]
- [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]
- [[5G-NR-Positioning/06-TDOA定位/TDOA]]
- [[5G-NR-Positioning/07-多站协同/Multi-Station Synchronization]]
