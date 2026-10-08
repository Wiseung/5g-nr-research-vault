---
title: 3GPP TS 38.321｜Medium Access Control protocol specification
aliases:
  - 3GPP 38.321
  - NR MAC 协议规范
  - TS 38.321 媒体接入控制
type: reference
status: partial
tags:
  - domain/5g-nr
  - layer/mac
  - evidence/3gpp
  - topic/random-access
  - topic/harq
  - topic/logical-channel
  - process/mac-scheduling
source:
  - 3GPP TS 38.321
related:
  - "[[3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[3GPP TS 38.212｜Multiplexing and channel coding]]"
  - "[[3GPP TS 38.213｜Physical layer procedures for control]]"
  - "[[3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[3GPP TS 38.331｜Radio Resource Control protocol specification]]"
  - "[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]"
  - "[[5G-NR-Positioning/02-PRACH/RAR|RAR]]"
  - "[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]"
  - "[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]"
  - "[[5G-NR-Positioning/03-PDCCH/RNTI|RNTI]]"
---

# 3GPP TS 38.321｜Medium Access Control protocol specification

> [!abstract] 标准职责
> TS 38.321 定义 NR MAC 子层的服务、实体、逻辑信道/传输信道交接、MAC PDU 与 MAC CE、随机接入、HARQ、BSR、SR 和上行功率控制接口。它把 RRC 配置和物理层机会转换为可执行的 MAC 状态与传输请求，但不替代 38.211/212/213/214 的物理映射、编码、时序和数据过程。

## 证据边界与阅读定位

本页是标准阅读入口，当前状态为 `STANDARD + partial`。项目现场 Release、规范版本和勘误尚未锁定；未给出版本化条款、字段位宽、计时器完整表或实现 API 的地方标记 `NEEDS_EXTERNAL_REFERENCE`。本地 PRACH 笔记是流程组织材料，不能替代本规范原文。

建议阅读顺序：

1. 先读 MAC 服务/架构、实体和逻辑信道优先级，再读具体 MAC PDU/CE。
2. 以 §5.1 Random Access Procedure 串起 Msg1、RAR、Msg3、Msg4 和 2-step 分支。
3. 再读 HARQ、BSR、SR、功率控制以及与 RRC/物理层的配置接口。
4. 每项结论记录 `release`、`spec_version`、`clause/table`、配置快照和观测状态。

## MAC 服务与实体

MAC 位于 RLC/PDCP 与物理层之间，向上提供逻辑信道复用/传送，向下使用传输信道和 HARQ/随机接入等过程。典型实体包括：

| 实体/过程 | MAC 负责的接口 | 不应越界推出 |
|---|---|---|
| MAC 主实体 | 小区/BWP、逻辑信道、随机接入、BSR/SR、功率状态协调 | 不从 MAC 状态推断完整 IQ 或 PHY 解码成功 |
| 逻辑信道复用与优先级 | 将 CCCH/DCCH/DTCH 等逻辑信道数据放入 UL-SCH/DL-SCH MAC PDU | 不把逻辑信道 ID 当作业务明文身份 |
| HARQ 实体 | 传输块级新传输/重传状态、软合并交接和反馈请求 | 译码算法与 LLR 坐标由 38.212/实现定义 |
| 随机接入实体 | 选择 RA 类型/资源、发送前导或 MsgA、处理 RAR/MsgB 和争用解决 | 不把 PRACH 检测峰直接标为 C-RNTI |
| BSR/SR/功控接口 | 报告缓冲区需求、请求 UL 资源、维护功率控制状态 | 不虚构报告触发器、定时器数值或现场配置 |

## MAC 配置与数据链

```text
RRC/SIB 配置（38.331）
    ↓
MAC 实体状态、逻辑信道与 RA 配置
    ↓
BSR/SR、调度请求、HARQ、随机接入决策
    ↓
MAC PDU / MAC CE / RAR
    ↓
DL-SCH/UL-SCH（38.212）
    ↓
PDSCH/PUSCH 资源与物理处理（38.211/213/214）
```

MAC 记录应同时保留 `cell_id`、`bwp_id`、`config_id`、帧/时隙、逻辑信道、HARQ 进程、RNTI 上下文和原始 PDU 引用。`null` 是未知，不能解释为 0；配置更新后不能静默复用旧状态。

## 随机接入：4-step 与 2-step

### 4-step（Type-1）主线

```text
Msg1：PRACH preamble / RO
  ↓ RA-RNTI 监测 RAR window
Msg2：RAR（TA、UL grant、Temporary C-RNTI，可能含 BI）
  ↓
Msg3：按 grant 的 PUSCH/UL-SCH（CCCH SDU 或 C-RNTI MAC CE）
  ↓ Temporary C-RNTI 争用解决
Msg4：PDSCH contention resolution
  ↓
C-RNTI 上下文确认或 RA 失败/退避重试
```

CBRA 与 CFRA 的差异来自 RRC/MAC 选择的公共或专用前导/RO、触发原因和完成条件。CFRA 并不自动意味着“没有 Msg3/Msg4”；BFR、HO、SI request 等分支须结合配置和触发原因核验。

### 2-step（Type-2）分支

```text
MsgA = PRACH preamble + 关联 PUSCH
  ↓ MSGB-RNTI 监测 MsgB window
MsgB：successRAR 或 fallbackRAR
  ├─ successRAR：身份/时序条件闭合后完成 RA
  └─ fallbackRAR：TA + UL grant + Temporary C-RNTI，回到 Msg3/Msg4 子链
```

2-step/4-step、CBRA/CFRA 的选择依赖 `RACH-ConfigCommon`、`RACH-ConfigDedicated`、MsgA 配置、触发原因、缓冲区大小、SSB/CSI-RS 质量和上行载波等输入。字段名、枚举、尝试上限和切换条件需按目标 Release 核验，状态为 `NEEDS_EXTERNAL_REFERENCE`。

## RAR、Msg3、Msg4 与标识生命周期

RAR 是 MAC PDU 中的一个或多个响应子 PDU；接收端应先按 RA-RNTI/MSGB-RNTI 找到 PDCCH/PDSCH，再确认 TB-CRC、RAPID、字段范围和时序。RAR 的 Temporary C-RNTI 只表示随机接入阶段的临时上下文。

| 阶段 | 关键 MAC 证据 | 保守状态 |
|---|---|---|
| PRACH/MsgA 已观测 | RO、preamble、载波、时间和检测质量 | `preamble_candidate` |
| RAR/MsgB 命中 | RNTI、TB-CRC、RAPID、TA、grant、临时标识 | `temporary_rnti_candidate` |
| Msg3 或 MsgA UL 已闭合 | grant 资源、UL-SCH/MAC 内容、HARQ/时序 | `contention_pending` |
| Msg4 或 successRAR 身份匹配 | UE Contention Resolution Identity/过程条件 | `c_rnti_confirmed` |

同一 RO 的多个前导共享 RA-RNTI；同一前导可能有多 UE 碰撞。因此 RA-RNTI 只能限制响应上下文，不能直接识别 UE。详细事件链见 [[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]] 和 [[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。

## 逻辑信道复用与 MAC PDU

MAC 将逻辑信道数据、MAC CE 和必要的填充组合为 DL-SCH/UL-SCH MAC PDU。调度器提供可用传输块大小后，复用逻辑应至少依据逻辑信道优先级、优先级预算、可用字节数、LCID/子头和 CE 优先级作决定。具体优先级规则、子头格式和版本化 LCID/eLCID 表不得从经验补齐。

```text
RLC/CCCH/DCCH/DTCH 数据 + MAC CE
    ↓ 逻辑信道优先级与可用 TBS
MAC subheader / SDU / CE / padding
    ↓
DL-SCH 或 UL-SCH
    ↓ 38.212 CRC/LDPC/率匹配
PDSCH/PUSCH 物理承载
```

被动观测至少区分：`pdu_received`、`tb_crc_pass`、`mac_pdu_parsed`、`lcid_known`、`sdu_decrypted_or_visible`。MAC PDU 解析成功不等于 RLC/PDCP 或业务明文可见。

## HARQ、BSR、SR 与功控接口

| 过程 | MAC 输入 | MAC 输出/交接 | 观测边界 |
|---|---|---|---|
| HARQ | 新传输/重传状态、NDI/RV、反馈和进程配置 | 传输块状态、软合并缓冲区引用、ACK/NACK/DTX 事件 | 译码软值和物理 HARQ 时序还需 38.212/38.213 |
| BSR | UL 逻辑信道组缓冲区状态、触发原因和禁止/重置状态 | Short/Truncated/Long BSR 等 MAC CE（具体分支待核） | 不凭 CE 长度猜报告类型 |
| SR | UL 缓冲区/配置授权状态和 SR prohibit/retry 状态 | PUCCH/PUSCH 上的调度请求 | 资源和反馈时机由 RRC/38.213 配置 |
| UL 功控接口 | pathloss、TPC、闭环状态、PUSCH/PUCCH/SRS 上下文 | 发射功率控制状态和 MAC/PHY 参数交接 | 不把接收功率直接当 UE 发射功率 |

HARQ 统计应分开 `transport_block_crc`、`harq_feedback_semantics`、`retransmission_count` 和 `soft_combine_state`。BSR/SR 日志需包含触发事件、逻辑信道组、时隙、资源和 PDU 原始引用；计时器和索引没有目标版本支撑时标 `NEEDS_EXTERNAL_REFERENCE`。

## 输入、输出与实现/观测字段

```yaml
mac_event:
  event_id: ""
  config_id: ""
  release_or_spec_version: "unknown"
  frame: null
  slot: null
  direction: "DL|UL|unknown"
  rnti_type: "RA-RNTI|MSGB-RNTI|TEMPORARY-C-RNTI|C-RNTI|unknown"
  rnti_value: null
  procedure: "random_access|harq|bsr|sr|multiplexing|power_control|unknown"
  logical_channels: []
  harq_process: null
  tb_size: null
  rv: null
  pdu_ref: ""
  crc_state: "unknown"
  mac_parse_state: "unknown"
  association_state: "candidate|temporary|confirmed|ambiguous|rejected"
  evidence: []
```

字段位宽、MAC subheader 端序、CE schema、计时器单位和 HARQ 进程编号必须由目标版本及抓包/参考实现核验。没有 PDU 原始字节或配置快照时，只能输出候选状态。

## 跨规范职责边界

| 主题 | 主要所有者 | MAC 的交接 |
|---|---|---|
| RRC/SIB、BWP、CORESET、SearchSpace、RACH 配置 | [[3GPP TS 38.331｜Radio Resource Control protocol specification]] | 消费配置并建立 MAC 状态；不改写 ASN.1 原文 |
| CRC、LDPC/Polar、码块与率匹配 | [[3GPP TS 38.212｜Multiplexing and channel coding]] | 提供 TB/控制编码输入和输出边界 |
| PDCCH/PDSCH/PUSCH/PRACH RE 映射与波形 | [[3GPP TS 38.211｜Physical channels and modulation]] | 交给物理信道资源和观测 |
| RAR/PRACH 时序、HARQ 反馈、功控 | [[3GPP TS 38.213｜Physical layer procedures for control]] | 提供过程参数和状态；精确时序按版本核验 |
| PDSCH/PUSCH 资源、MCS、TBS、RV | [[3GPP TS 38.214｜Physical layer procedures for data]] | MAC PDU 大小/重传状态与数据过程对齐 |

## 最小核验清单

- [ ] 锁定 `release/spec_version/date`，并记录适用小区、载波和 BWP。
- [ ] 用一条已知 4-step 链验证 `RO -> RA-RNTI -> RAR -> RAPID -> grant/Temporary C-RNTI`。
- [ ] 另用 2-step 样本确认 `MsgA -> MSGB-RNTI -> successRAR/fallbackRAR`，不套 4-step 默认流程。
- [ ] 对 Msg3/Msg4 保存计划资源、实际观测、TB-CRC、MAC PDU 和争用解决身份比较结果。
- [ ] 验证公共/专用逻辑信道复用、MAC CE 解析和 padding 边界；未知 LCID 保留原始字节。
- [ ] 分开统计 HARQ ACK/NACK/DTX、重传次数、BSR/SR 触发和功控状态，不用最终 BLER 代替 MAC 证据。
- [ ] 对字段位宽、完整计时器表、LCID/eLCID、RNTI 范围和厂商实现标 `NEEDS_EXTERNAL_REFERENCE`。

## 原始官方来源

- ETSI TS 138 321 V17.8.0（Release 17 参考入口，版本需按项目实际 Release 复核）：<https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf>
- 3GPP specification portal（TS 38.321，版本列表）：<https://www.3gpp.org/DynaReport/38321.htm>

当前未锁定 Release；上述 V17.8.0 链接仅作为可复核官方入口，不将其字段/条款自动升级为现场事实。`SOURCE_NOTE_PENDING`：本页尚未逐条摘录目标版本的 MAC CE/LCID 表、完整计时器表和全部 2-step/CFRA 特殊分支。

## 关联笔记

- 物理/编码：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.213｜Physical layer procedures for control]]、[[3GPP TS 38.214｜Physical layer procedures for data]]。
- 配置：[[3GPP TS 38.331｜Radio Resource Control protocol specification]]、[[5G-NR-Positioning/03-PDCCH/CORESET|CORESET]]、[[5G-NR-Positioning/03-PDCCH/Search Space|Search Space]]、[[5G-NR-Positioning/03-PDCCH/DCI|DCI]]。
- 随机接入：[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。
- 规范索引：[[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map|3GPP Specification Map]]。
