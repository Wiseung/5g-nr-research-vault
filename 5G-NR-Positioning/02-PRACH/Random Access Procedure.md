---
title: Random Access Procedure
aliases:
  - NR 随机接入流程
  - Random Access
  - RA 状态机
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/random-access
  - channel/prach
  - topic/protocol
  - stage/user-association
source:
  - 3GPP TS 38.321
  - 3GPP TS 38.213
  - 3GPP TS 38.211
  - 3GPP TS 38.331
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Overview|PRACH Overview]]"
  - "[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]"
  - "[[5G-NR-Positioning/02-PRACH/RAR|RAR]]"
  - "[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]"
  - "[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]"
  - "[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]"
---

# Random Access Procedure

## 1. 一句话定义

Random Access Procedure 是 UE 通过 PRACH 发起接入、接收 RAR、发送 Msg3 并完成争用解决/标识确认的跨 PHY、MAC 和 RRC 的过程。

## 2. 为什么项目需要它

项目必须沿这条过程链把一个前导事件逐步关联到临时 C-RNTI 和最终 C-RNTI；只看 Msg1 只能证明接入尝试，不能证明用户身份或后续 PDCCH 可用。

## 3. 它位于整个 5G 空口链路的什么位置

它承接 PRACH Detection/Timing Estimation，覆盖 Msg1→RAR（Msg2）→Msg3→Msg4 contention resolution，成功后把 C-RNTI 候选交给 PDCCH/DCI 盲搜；2-step RA 则以 MsgA/MsgB 分支替代部分 4-step 消息。

## 4. 输入

- RACH-ConfigCommon、TDD/载波/BWP 配置和 RA 类型。
- 检测到的 RO、前导索引、ToA、功率和 SSB/beam 关联。
- RAR PDCCH/PDSCH 候选、RAR MAC 字段、UL grant 和临时标识。

## 5. 输出

- RA 状态（RA_IDLE、MSG1_DETECTED、RAR_WINDOW、TEMP_C_RNTI、MSG3_PENDING、CONTENTION_RESOLUTION、C_RNTI_CONFIRMED 等）。
- RAPID、TA、UL grant、Temporary C-RNTI、Msg3/Msg4 事件和失败原因。
- 可供后续 PDCCH 搜索的有限 C-RNTI 候选及关联置信度。

## 6. 关键参数

2-step/4-step、CBRA/CFRA、preambleTransMax、powerRampingStep、ra-ResponseWindow、contentionResolutionTimer、backoffIndicator、RAR MAC PDU 限制、SSB/RO 映射和临时 RNTI 生命周期。具体枚举和计时器单位按版本化 TS 38.321/38.331 核对。

## 7. 时域位置

Msg1 在 RO 发送；Msg2 在 RO 后的 RAR window 内由 RA-RNTI 寻址；Msg3 按 RAR 的 UL grant 在后续 UL 时隙发送；Msg4 在 contention resolution timer 范围内下发。实际 K2、TDD 可用 UL 符号和跨帧边界须由配置计算。

## 8. 频域位置

Msg1 使用 PRACH RO；RAR 使用由 RA-RNTI 调度的 PDSCH；Msg3 使用 RAR 指定的 PUSCH PRB、符号、MCS 和 DM-RS。各阶段资源可能跨 BWP，必须保留绝对/局部频域坐标。

## 9. 数学原理

可用状态转移表示为

$$
s_{k+1}=\Phi(s_k,o_k,c_k),
$$

其中 $o_k$ 是观测（相关峰、PDCCH/PDSCH CRC、MAC 字段），$c_k$ 是配置。只有满足 RAPID、时序、字段合法性和争用解决条件，状态才从候选升级为 confirmed；单个 CRC 通过不足以完成转移。

## 10. 3GPP 对应规范

- TS 38.321 §5.1：Random Access Procedure；重点核对 §5.1.3 前导发送、§5.1.4 RAR、§5.1.5 Contention Resolution，及 §6.1.3/§6.2.3 MAC CE/RAR 格式。
- TS 38.213 §8：PRACH/RAR 物理过程和时序；具体子条款随 Release 复核。
- TS 38.211 §6.3.3：PRACH 物理映射；TS 38.331：RACH-ConfigCommon 字段。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

没有一个官方函数替代完整 MAC 随机接入状态机。可组合 nrPRACHConfig、nrPRACHDetect、nrPDCCHSpace、nrPDCCHDecode、nrPDSCHDecode 和自定义 RAR/MAC 解析器；对象输入、RAR 载荷和版本行为均标记 NEEDS_EXTERNAL_REFERENCE。

## 12. 本项目中的用途

把检测到的前导事件按状态机推进到 RAR、Msg3、Msg4 和 C-RNTI；失败时保留 candidate_associated/ambiguous，而不是把 PRACH 峰直接送入 [[5G-NR-Positioning/03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]。

## 13. 常见误区

- 把 PRACH 检测成功写成 Random Access 完成。
- 把 RAR 中 Temporary C-RNTI 直接称为最终 C-RNTI。
- 把 4-step 流程套用到 2-step 或 CFRA。
- 忽略同一 RAR MAC PDU 中多个 RAPID。

## 14. 与相似概念的区别

Random Access Procedure 是过程；PRACH/Preamble 是 Msg1 物理承载；RAR 是 Msg2 MAC 响应；Msg3 是按 grant 发送的首次 UL 传输；Contention Resolution 是 Msg4 阶段；C-RNTI 是过程成功后的 UE 专用寻址标识。

## 15. 代码实现注意事项

- 用显式状态机和超时，不用一串布尔变量隐式推断。
- 每次转移记录输入快照、配置版本、时间窗口和失败原因。
- 对同一 RO 的多个 RAPID、碰撞和重传保持独立事件。
- 将 PHY CRC、MAC 字段解析和协议状态判决分层统计。

## 16. 待实验验证的问题

- 当前网络的 RA 类型、CBRA/CFRA 和 MsgA/MsgB 支持。
- 被动设备能否连续捕获 RAR、Msg3、Msg4 及其加扰/DM-RS。
- RAR window、contention timer 和 TDD UL 调度的实际边界。
- 状态机在丢包、重传、碰撞和 C-RNTI 重用时的行为。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Overview|PRACH Overview]]、[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。
- 后续控制：[[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]、[[5G-NR-Positioning/03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]。
- 旧笔记：[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]、[[03-仿真与实验/5G定位/仿真：PRACH 检测与 RA 事件关联|RA 事件仿真]]。

## 18. Type-1/Type-2 的标准基线

> [!important] 术语边界
> `3GPP TS 38.213 V17.8.0 (Release 17)` §8 从物理层角度把随机接入分为 Type-1 和 Type-2：Type-1 对应 4-step 的 Msg1、RAR（Msg2）、必要时的 RAR-granted PUSCH（Msg3）和争用解决 PDSCH（Msg4）；Type-2 对应 PRACH + PUSCH 组成的 MsgA、MsgB 响应，以及必要时的 fallback RAR/PUSCH 和争用解决。MAC 的完整变量、重试和完成条件由 38.321 §5.1 定义。

因此，“四条消息”不是所有随机接入的固定模板：

| 物理类型 | 空口事件链 | 主要响应标识 | 本页默认解释 |
|---|---|---|---|
| Type-1 | Msg1 PRACH -> Msg2 RAR -> Msg3 PUSCH -> Msg4 PDSCH | RA-RNTI、Temporary C-RNTI | 4-step CBRA 主线 |
| Type-2 | MsgA(PRACH+PUSCH) -> MsgB | MSGB-RNTI（或特定 C-RNTI 恢复路径） | 2-step CBRA/CFRA 分支 |

项目若只捕获 PRACH，最多进入 `MSG1_DETECTED`/`MSGA_PREAMBLE_DETECTED`；不能把未观测的 RAR、Msg3、Msg4 补写为事实。

## 19. RRC 配置到 MAC 选择

随机接入不是由一个 `prach-ConfigurationIndex` 字段独立决定。建议先把配置分成三层：

| 配置来源 | 代表对象 | 决定的内容 | 证据标签 |
|---|---|---|---|
| 小区公共 RRC | `RACH-ConfigCommon`、`RACH-ConfigCommonTwoStepRA`、`MsgA-ConfigCommon` | RO、前导集合、SSB/CSI-RS 映射、窗口、计数器、2/4-step 可用性 | `STANDARD + partial` |
| 专用 RRC | `RACH-ConfigDedicated` 的 `cfra`/`cfra-TwoStep` | CFRA 专用 RO、前导和 MsgA PUSCH 资源 | `STANDARD + partial` |
| MAC/PHY 动态状态 | 触发原因、SS-RSRP、pathloss、TDD、BWP、功率/退避计数器 | 选择具体 RA 类型、SSB、载波、前导和时机 | `NEEDS_VERIFICATION`（若无网络配置） |

在 38.331 V17.0.0（Release 17 基线）中，`RACH-ConfigDedicated` 的 `cfra` 与 `cfra-TwoStep` 是互斥的专用分支；两者都缺失时才走 contention-based RA。不要因为看见一个 `ra-PreambleIndex` 就把它标成 CFRA，必须同时确认触发原因和对应专用资源。

### 19.1 资源选择决策表

| 决策问题 | 4-step | 2-step | 观测端需要的输入 |
|---|---|---|---|
| 是否有专用前导/RO | `cfra`/BFR/HO 配置 | `cfra-TwoStep`/BFR 配置 | RRC 配置快照、触发原因 |
| 是否需要按 payload 大小分组 | `ra-Msg3SizeGroupA`/Group B | `ra-MsgA-SizeGroupA`/Group B | MAC buffer 大小、pathloss |
| 是否共享 4/2-step RO | 由 common 配置决定 | `msgA-SSB-SharedRO-MaskIndex` 等 | RO 映射周期、FDM/时域索引 |
| 首选 UL 载波 | NUL 或 SUL | NUL 或 SUL | `rsrp-ThresholdSSB-SUL`、载波配置 |
| 失败后是否切换类型 | 不适用 | 达到 `msgA-TransMax` 且配置允许时可切 4-step | 计数器、专用/公共配置 |

缺少任一输入时，输出 `branch_unknown`，而不是选择默认 4-step。

## 20. 4-step CBRA 的协议状态机

下表是对 38.321 §5.1.1--§5.1.6 的工程化映射；状态名属于本项目个人记录，不是 3GPP 的枚举。

| 状态 | 进入条件 | MAC/PHY 动作 | 超时/失败转移 |
|---|---|---|---|
| `RA_IDLE` | 无进行中的 RA | 等待 RRC、PDCCH order 或 MAC 触发 | 保持；不代表小区无 UE |
| `RA_INIT` | 触发 RA | 清空 Msg3/MSGA buffer；初始化计数器/退避；选择 NUL/SUL 和 BWP | 配置不全 -> `RA_ABORTED_CONFIG` |
| `RESOURCE_SELECTED` | SSB/CSI-RS、Group、RO、preamble 选定 | 固化 `ro_context` 和功率目标 | 无合法 RO -> `RA_RESELECT` |
| `MSG1_TX` | PRACH 资源可用 | 发送 preamble；计算 RA-RNTI | LBT/资源失败 -> 计数/重选 |
| `RAR_WINDOW` | Msg1 发送结束 | 在 `ra-ResponseWindow` 监测 RA-RNTI PDCCH/PDSCH | 窗口到期 -> backoff/retry 或 `RA_FAILED` |
| `RAR_MATCHED` | TB-CRC、RAPID 与本地前导一致 | 应用 TA；保存 UL grant/Temporary C-RNTI | 字段/资源非法 -> `RAR_REJECTED` |
| `MSG3_PENDING` | grant 可展开 | 计算 PUSCH 资源和 UL-SCH MAC PDU | 资源冲突 -> `RA_RESELECT` |
| `MSG3_TX` | PUSCH 计划时机到达 | 发送 Msg3；启动/重启 contention timer | 无 PUSCH/CRC 失败 -> 保留候选或重传 |
| `CONTENTION_RESOLUTION` | Msg3 已发送 | 监测 Temporary C-RNTI 的 Msg4 PDCCH/PDSCH | 匹配身份 -> `RA_SUCCESS`；超时 -> retry |
| `RA_SUCCESS` | 争用解决条件成立 | 丢弃 Temporary C-RNTI；保留/确认 C-RNTI；通知上层 | 完成后回 `RA_IDLE` |
| `RA_BACKOFF` | 响应/争用失败且可重试 | 使用 BI/退避和计数器选下一 RO | 达到 `preambleTransMax` -> `RA_FAILED` |

在 V17.8.0 的初始化流程中，MAC 会清空 Msg3/MSGA buffer、把前导传输计数器和功率爬升计数器设为初始值、把退避设为 0；这些初值属于 Release 核验快照，不得硬编码到跨版本实现。

### 20.1 4-step CFRA 差异

CFRA 的专用前导由 RRC 与 SSB/CSI-RS 绑定，降低同前导碰撞的概率；但“专用前导 = 一定没有 Msg3/Msg4”并不成立。38.321 对专用前导在 RAR 命中后的完成动作与 CBRA 不同，且 BFR、HO、SI request 等触发原因还会改变后续行为。观测端应记录：

```js
access_mode = CFRA
trigger = handover | beam_failure_recovery | reconfiguration | other
dedicated_resource_source = rach-ConfigDedicated / BeamFailureRecoveryConfig
contention_resolution_required = true | false | unknown
```

没有触发原因时，`cfra_direct_complete` 只能是 `NEEDS_VERIFICATION`。

## 21. 2-step CBRA/CFRA 状态机

2-step 的关键差异是 MsgA 同时占用 PRACH 和关联 PUSCH，响应使用 MSGB-RNTI。其工程状态可写为：

| 状态 | 进入条件 | 必存证据 | 失败/分支 |
|---|---|---|---|
| `MSGA_RESOURCE_SELECTED` | 选定 SSB、Group、RO、preamble、PUSCH occasion | PRACH/PUSCH 映射、MsgA grant、功率 | 无合法映射 -> `RA_RESELECT` |
| `MSGA_TX` | PRACH 与 PUSCH 资源均有效 | preamble、MsgA PUSCH、DM-RS、RV/配置 | LBT/窗口失败 -> 计数 |
| `MSGB_WINDOW` | MsgA 发送结束 | MSGB-RNTI、`msgB-ResponseWindow` | 超时 -> backoff/retry |
| `MSGB_SUCCESS` | successRAR 身份匹配，或 C-RNTI 路径条件成立 | UE Contention Resolution Identity、C-RNTI、TA | 完成 -> `RA_SUCCESS` |
| `MSGB_FALLBACK` | fallbackRAR RAPID 匹配 | TA、UL grant、Temporary C-RNTI | 进入 4-step Msg3/Msg4 子链 |
| `MSGA_RETRY` | MsgB 失败且计数未达上限 | `msgA-TransMax`、BI、backoff | 达上限且允许 -> `TYPE_SWITCH_4STEP` |
| `TYPE_SWITCH_4STEP` | 2-step 尝试上限且 common/dedicated 允许 | 新 RA type、buffer/计数器重置 | 重新进入 `RA_INIT` |

2-step CFRA 使用专用前导和 `CFRA-TwoStep` PUSCH 资源；不能把 CBRA 的随机前导、Group A/B 和碰撞统计直接套用。`successRAR`、`fallbackRAR` 的字段和 HARQ/PUCCH 条件按 MsgB schema 解析，见 [[5G-NR-Positioning/02-PRACH/RAR|RAR]]。

## 22. RA-RNTI、临时标识和消息交接

```text
RRC common/dedicated config
        |
        v
PRACH RO + preamble (Msg1)       MsgA = PRACH + PUSCH (2-step)
        |                                   |
        +--> RA-RNTI                        +--> MSGB-RNTI
        |                                   |
        v                                   v
RAR PDCCH/PDSCH (Msg2)             MsgB PDCCH/PDSCH
        |                                   |
        +--> RAPID + TA + UL grant + TC-RNTI
        |                                   +--> successRAR (C-RNTI)
        v                                   +--> fallbackRAR -> Msg3
Msg3 PUSCH (UL-SCH)
        |
        v
Msg4 PDSCH / UE Contention Resolution Identity
        |
        v
C-RNTI confirmed or retry/backoff
```

每条箭头都应附带 `event_id`、时间窗口、资源快照和证据状态。仅有箭头左端的物理峰时，不得创建右端的标识字段。

## 23. 时间线与计时器

```text
时间 ───────────────────────────────────────────────────────────────>
4-step:  RO/Msg1  |<---- ra-ResponseWindow ---->|  RAR/Msg2
                         [TA + UL grant + TC-RNTI]
                                                   |-- processing/K2/TA --> Msg3
                                                                               |<-- ra-ContentionResolutionTimer -->|
                                                                               Msg4/identity

2-step:  RO + MsgA(PUSCH) |<------ msgB-ResponseWindow ------>| MsgB
                                      | successRAR -> complete
                                      | fallbackRAR -> grant -> Msg3 -> contention resolution
```

计时器的单位、起始 PDCCH occasion、测量间隙处理和跨帧映射来自 RRC/38.213/38.321 的版本化规则。日志至少保存 `start_reference`、`start_slot`、`expiry_reference` 和 `config_source`，不要只存一个“经过毫秒数”。

## 24. 协议状态与证据状态双账本

协议状态（UE 应采取的动作）和证据状态（被动端已证明的事实）必须分开：

| 协议状态 | 对应最低证据状态 | 可以说什么 | 不能说什么 |
|---|---|---|---|
| `MSG1_TX` | `preamble_detected` | 某 RO/前导有接入尝试 | 已收到 RAR |
| `RAR_WINDOW` | `ra_rnti_computed` | 正在监测候选窗口 | RAR 一定存在 |
| `RAR_MATCHED` | `rar_matched` | RAPID/TA/grant/TC-RNTI 可解析 | C-RNTI 已确认 |
| `MSG3_TX` | `msg3_observed` | grant 对应 PUSCH 候选存在 | 争用解决成功 |
| `CONTENTION_RESOLUTION` | `contention_pending` | 正在等待身份闭合 | 临时标识就是永久身份 |
| `RA_SUCCESS` | `c_rnti_confirmed` 或 `procedure_complete` | 本次 RA 的成功证据闭合 | 未来所有帧都属于该 UE |

证据状态建议采用单调追加的事件流：`raw -> parsed -> matched -> confirmed`；若后续发现冲突，追加 `ambiguous/revoked`，不删除历史状态。

## 25. 分支感知伪代码

```python
handle_ra_event(event, config, release):
    branch = classify_ra_type_and_mode(config, event.trigger)
    if branch.unknown:
        return evidence("branch_unknown", reason=branch.missing)

    state = init_or_resume(branch, event)
    if state.is_new:
        flush_msg3_and_msga_buffers()
        init_counters_and_backoff(config, release)

    if branch.type == "4step":
        ro = select_ro_and_preamble(event, config, release)
        preamble = detect_prach(ro, event.iq)
        if not preamble.accepted:
            return evidence("preamble_rejected", reason=preamble.reason)
        ra_rnti = compute_ra_rnti(ro, release)
        rar = monitor_and_decode_rar(ra_rnti, ro.window, event.iq, release)
        if not rar.rapid_matches(preamble.index):
            return evidence("rar_rejected", reason="rapid_mismatch")
        if rar.is_cfra_direct_complete:
            return evidence("procedure_complete", evidence=[preamble, rar])
        msg3 = process_msg3_from_rar(rar, config, release, event.iq)
        return await_contention_resolution(msg3, rar.temporary_c_rnti,
                                           config, release)

    # Type-2: MsgA includes PRACH and associated PUSCH.
    msg_a = detect_and_decode_msga(event, config, release)
    msgb_rnti = compute_msgb_rnti(msg_a.ro, release)
    msgb = monitor_msgb(msgb_rnti, msg_a.window, event.iq, release)
    if msgb.success_identity_matches(msg_a):
        return evidence("procedure_complete", evidence=[msg_a, msgb])
    if msgb.fallback_rapid_matches(msg_a.preamble_index):
        return await_contention_resolution(
            process_msg3_from_fallback(msgb, config, release, event.iq),
            msgb.temporary_c_rnti, config, release)
    if msgb.window_expired:
        return retry_or_switch_to_4step(state, config, release)
    return evidence("msgb_pending")
```

函数名仅为项目伪代码；没有本地实现或实测结果时，标记 `EXPERIMENT + NEEDS_VERIFICATION`。

## 26. 事件账本：一行闭合一个 RA 尝试

| 字段 | 内容 |
|---|---|
| `ra_attempt_id` | 一次初始化到成功/失败的稳定 ID；重传保留同一 ID 并递增 attempt |
| `trigger` | PDCCH order、RRC、MAC、HO、BFR、SI request 等 |
| `ra_type` / `access_mode` | `4step/2step`、`CBRA/CFRA`、未知原因 |
| `config_snapshot` | RACH-ConfigCommon/Dedicated、BWP、TDD、Release |
| `ro_event` | 帧、slot、symbol、FDM、载波、SSB/CSI-RS、preamble |
| `response_rnti` | RA-RNTI 或 MSGB-RNTI、算式版本 |
| `window_timer` | RAR/MsgB/争用窗口的开始、结束、来源 |
| `rar_or_msgb` | PDCCH/PDSCH 候选、TB-CRC、MAC 子 PDU、RAPID/identity |
| `ta_and_grant` | 原始 TA、UL grant、解析 schema、应用状态 |
| `temporary_c_rnti` | 数值、来源、有效区间、是否丢弃 |
| `msg3_or_msga` | PUSCH 资源、DM-RS、UL-SCH/MAC、ToA |
| `msg4_or_success` | RNTI 寻址、identity match、TB-CRC、HARQ |
| `c_rnti_state` | `absent/candidate/confirmed/expired/ambiguous` |
| `evidence_state` | 被动端证据状态，不等同协议 state |
| `failure_reason` | 结构化枚举、缺失字段、原始 artifact 路径 |

推荐为每条状态转移写一条不可变事件：

```js
{attempt_id, seq, protocol_state, evidence_state,
 timestamp_ref, input_artifacts, guard_result,
 output_artifacts, release, failure_reason}
```

## 27. 负例与故障定位矩阵

| 现象/注入 | 应定位到 | 不应归因 |
|---|---|---|
| PRACH 峰存在但 RRC branch 不明 | `branch_unknown` | 默认 4-step |
| RA-RNTI 计算错误 | RO/配置映射 | “网络未发 RAR” |
| RAR PDCCH CRC 过、PDSCH TB-CRC 失败 | PHY/PDSCH | PRACH 检测失败 |
| RAPID 与前导不匹配 | RAR 关联 | TC-RNTI 不存在 |
| RAR grant 超出 BWP/TDD | 38.213/214 资源解释 | Msg3 丢失 |
| Msg3 PUSCH 有能量但 MAC CRC 失败 | UL-SCH/信道估计 | Msg4 身份错误 |
| Msg4 CRC 过但 identity 不匹配 | 争用解决 | C-RNTI 已确认 |
| `msgB-ResponseWindow` 到期 | 2-step 响应/重试 | MsgA 一定未发送 |
| 达 `preambleTransMax` | MAC RA problem | 小区无覆盖 |
| 同 RO 同前导多 UE | collision/ambiguous | 每个峰都有独立 RNTI |
| C-RNTI 候选长期无后续 DCI | 候选老化/捕获缺口 | 立即确认或删除历史 |

## 28. 最小验证用例（按门推进）

| 门 | 用例 | 必须验证 | 当前状态 |
|---|---|---|---|
| `F0` | 单 RO、单前导、无噪声 | preamble、RO、RA-RNTI 公式回放 | 待运行 |
| `F1` | 4-step RAR | PDCCH/PDSCH、RAPID、TA、grant、TC-RNTI | 待运行 |
| `F2` | 4-step Msg3/Msg4 | PUSCH 资源、UL-SCH、identity、timer | 待运行 |
| `F3` | 2-step successRAR | MsgA、MSGB-RNTI、identity/C-RNTI 完成 | 待运行 |
| `F4` | 2-step fallbackRAR | fallback -> Msg3 -> contention resolution | 待运行 |
| `F5` | CBRA collision | 同 RO 同前导不可消歧，保留 ambiguous | 待运行 |
| `F6` | CFRA/BFR | 专用资源和触发原因不套 CBRA 状态 | 待运行 |
| `F7` | 超时/重试 | BI、backoff、计数器和 2->4-step 切换 | 待运行 |

每门都应保存真值配置、原始 IQ/软比特、解析 artifact、状态流和失败注入记录。F0/F1 未通过前，不运行全空间盲搜；F2/F3 未通过前，不把 C-RNTI 候选送入长期用户资源跟踪。

## 29. 证据账本与缺口

- `STANDARD + verified snapshot`：ETSI [TS 38.321 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf)，§5.1.1--§5.1.6；核对 RA 初始化、资源选择、RAR、MsgB、争用解决、重试和完成动作。
- `STANDARD + verified snapshot`：ETSI [TS 38.213 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf)，§8.1、§8.1A、§8.2A、§8.3、§8.4；核对 Type-1/Type-2 物理消息链和 RAR-granted PUSCH/Msg4 边界。
- `STANDARD + partial`：[[3GPP TS 38.331｜Radio Resource Control protocol specification]]（以外部版本化 ASN.1 为准，`SOURCE_NOTE_PENDING`），`RACH-ConfigCommon`、`MsgA-ConfigCommon`、`RACH-ConfigDedicated` 的字段存在性和条件。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.214｜Physical layer procedures for data]]；PRACH/PUSCH/PDSCH 资源、MCS/TBS、DM-RS 和 HARQ 接口。
- `PERSONAL_NOTE`：[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]] 的跨层事件账本约定。
- `EXPERIMENT + NEEDS_VERIFICATION`：F0--F7 仅为验收模板，尚未接入真实网络/设备或 MATLAB 运行结果。
- `NEEDS_EXTERNAL_REFERENCE`：项目实际 Release、2-step/4-step 开关、CBRA/CFRA/BFR 触发原因、窗口/计时器参数、共享 RO、SUL、Msg3 repetition、加密/抓包可见性；不得从一个 PRACH 峰自动填充。
