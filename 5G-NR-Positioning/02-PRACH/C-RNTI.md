---
title: C-RNTI
aliases:
  - Cell Radio Network Temporary Identifier
  - 小区无线网络临时标识
  - UE 专用 C-RNTI
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/rnti
  - topic/user-association
  - channel/pdcch
  - stage/control-decoding
source:
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TS 38.321
  - 用户项目流程说明
related:
  - "[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]"
  - "[[5G-NR-Positioning/02-PRACH/RAR|RAR]]"
  - "[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]"
  - "[[5G-NR-Positioning/03-PDCCH/RNTI|RNTI]]"
  - "[[5G-NR-Positioning/03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]"
  - "[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|现有控制/数据主线]]"
---

# C-RNTI

## 1. 一句话定义

C-RNTI（Cell Radio Network Temporary Identifier）是连接期间用于 UE 专用控制和数据寻址的临时标识，通常通过 PDCCH/DCI 的 CRC 掩码及相关协议状态体现，而非在 PRACH 前导中明文发送。

## 2. 为什么项目需要它

C-RNTI 是从随机接入事件进入 PDCCH 盲搜、DCI 解析和 UE 资源提取的关键关联键。项目目标是从 PRACH→RAR→Msg3/Msg4 证据建立有限候选，而不是声称 PRACH 直接“解出” C-RNTI。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 Random Access contention resolution 成功之后，作为 PDCCH/DCI 的 RNTI 假设，驱动 PDSCH/PUSCH 资源快照、单用户信号提取和后续 ToA/TDOA 支路。

## 4. 输入

- RA 事件键、RAR 的 Temporary C-RNTI、Msg3/Msg4 和 C-RNTI MAC CE（若可见）。
- PDCCH 搜索空间、DCI 格式、候选位置和跨时隙连续性。
- 现场配置、捕获 IQ、PDSCH/PUSCH/DM-RS 资源证据。

## 5. 输出

- C-RNTI 数值、来源消息、有效时间区间和关联置信度。
- candidate、confirmed、expired、ambiguous、rejected 状态。
- 供 PDCCH CRC 假设和 UE 资源掩码使用的 RNTI 候选池。

## 6. 关键参数

RNTI 值（通常 16 bit）、来源（RAR 临时标识、MAC CE、争用解决、历史候选）、生命周期/重用、搜索空间、DCI 格式、CRC 长度和跨帧连续性。具体 RNTI 类型和状态转换需按 TS 38.321/38.213 版本核对。

## 7. 时域位置

C-RNTI 没有独立的时域符号；它在后续 PDCCH 候选的 CRC 判决中生效，时间范围由 RA 状态、连接上下文和候选老化策略决定。一次 CRC 通过不能证明跨时隙持续有效。

## 8. 频域位置

C-RNTI 不占固定频域 RE；它关联的 DCI 可能位于不同 CORESET/搜索空间，DCI 再调度 PDSCH/PUSCH 的 PRB。应把 C-RNTI 与每个候选的时频坐标分开保存。

## 9. 数学原理

对译码得到的控制比特 $\hat{\mathbf a}$ 和候选 RNTI r，接受判据可抽象为

$$
\mathrm{CRC}(\hat{\mathbf a})\oplus\mathrm{mask}(r)=\mathbf 0,
$$

并附加 DCI 格式、字段范围、资源可解释性和时序连续性约束。若从 RA 链得到的是 Temporary C-RNTI，应先标为临时候选，不能把 CRC 通过值直接升级为 confirmed C-RNTI。

## 10. 3GPP 对应规范

- TS 38.321 §5.1.5：contention resolution；§6.1.3：C-RNTI MAC CE 等字段，具体版本/子条款待核。
- TS 38.213：PDCCH 监测、搜索空间和 RNTI 相关控制过程。
- TS 38.212：DCI CRC、Polar、率匹配和译码；TS 38.211：PDCCH 物理映射。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPDCCHDecode、nrDCIDecode：候选 PDCCH/DCI 解码及 RNTI 假设。
- nrPDCCHSpace：生成 CORESET/搜索空间候选资源。
- nrPDSCHDecode、nrDLSCHDecoder：用有效 DCI 驱动数据译码。
- 没有“从 PRACH 自动获得 C-RNTI”的官方单函数；RA 状态、MAC 解析和候选池逻辑需自定义，API 版本标记 NEEDS_EXTERNAL_REFERENCE。

## 12. 本项目中的用途

将 [[5G-NR-Positioning/02-PRACH/RAR|RAR]] 的 Temporary C-RNTI、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]、Msg4 和后续 DCI 连续性组合成 C-RNTI 关联；确认后交给 [[5G-NR-Positioning/03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]，再进入 PDSCH/UE Resource Extraction。

## 13. 常见误区

- 写成“通过 PRACH 直接解出 C-RNTI”。
- 把 RA-RNTI 或 Temporary C-RNTI 当最终 C-RNTI。
- 把一个错误 RNTI 的 CRC 偶然通过视为用户确认。
- 忽略 RNTI 重用、老化、配置切换和跨帧一致性。

## 14. 与相似概念的区别

RA-RNTI 标识 RAR 响应上下文；Temporary C-RNTI 只在随机接入阶段临时使用；C-RNTI 服务连接期间 UE 专用寻址；SI-RNTI、P-RNTI、TC-RNTI 等公共/临时 RNTI 有不同搜索空间和语义。

## 15. 代码实现注意事项

- 维护 RNTI 候选的来源、置信度、有效期和证据链。
- 对每个 PDCCH 候选记录所有 RNTI 假设，不只保留通过者。
- 用 CRC、字段合法性、资源闭包、HARQ/时序和后续数据联合判决。
- C-RNTI 确认状态不得覆盖原始 PRACH/RA 事件和临时标识。

## 16. 待实验验证的问题

- 当前工程所谓“已解出 C-RNTI”对应哪一条消息边界。
- RAR/Msg3/Msg4 是否可见，是否有安全或设备遮挡。
- 已知正确 RNTI、错误 RNTI、错误资源下的 PDCCH 误检率。
- C-RNTI 老化和重用策略在连续监测中的最佳窗口。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]。
- 后续控制/数据：[[5G-NR-Positioning/03-PDCCH/RNTI|RNTI]]、[[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]、[[5G-NR-Positioning/03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]、[[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]。
- 旧笔记：[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]、[[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]。

## 18. C-RNTI 生命周期：不要把“出现”当作“确认”

> [!important] 核心边界
> C-RNTI 是过程状态和 PDCCH 寻址上下文，不是 PRACH 前导中的明文身份。一个 RAR 中的 Temporary C-RNTI（常写作 `TC-RNTI`）只能把事件推进到临时状态；只有争用解决或 2-step successRAR 的条件闭合，才可把它写成 `C-RNTI confirmed`。被动接收端还应保留确认后的老化/重用不确定性。

### 18.1 状态与合法转移

| 状态 | 进入条件 | 允许使用的 RNTI | 退出条件 |
|---|---|---|---|
| `ABSENT` | 尚未建立 UE 专用上下文，或临时标识已丢弃 | RA-RNTI/MSGB-RNTI 只用于响应候选 | 匹配 RAR/fallbackRAR 或已有 C-RNTI 证据 |
| `TEMPORARY_CANDIDATE` | RAR RAPID 匹配且 payload 可解析 | Temporary C-RNTI 仅用于本次 RA | grant/Msg3 资源闭合；否则拒绝 |
| `TEMPORARY_ACTIVE` | UE/观测端接受 TA、UL grant 和临时标识 | TC-RNTI 寻址 Msg3 重传/Msg4 | Msg3 发送后启动争用解决计时器 |
| `CONTENTION_PENDING` | Msg3 已发送，等待 Msg4/后续 PDCCH | TC-RNTI（CCCH 路径）或 C-RNTI（CE 路径条件） | identity match、C-RNTI path、超时 |
| `CONFIRMED` | 争用解决成功，或 successRAR 明确给出 C-RNTI 并匹配身份 | C-RNTI 用于专用 PDCCH/PDSCH/PUSCH | RRC/MAC 释放、重配置、长时间无证据或重用冲突 |
| `EXPIRED/REVOKED` | 计时器超时、RA 失败、配置切换或证据冲突 | 不再把该值作为有效候选 | 新 RA 尝试建立新上下文 |
| `AMBIGUOUS` | 多个候选共享相同资源/CRC，无法消歧 | 候选池中保留但不作为唯一 RNTI | 需要额外 Msg4/后续 DCI 证据 |

`EXPIRED` 的具体时限和网络释放触发点依赖协议上下文；本页只定义观测端的保守状态，不自行发明老化毫秒数。

### 18.2 三条常见确认路径

| 路径 | 输入事件 | 成功判据 | 结果 |
|---|---|---|---|
| 4-step CBRA、CCCH Msg3 | RAR 的 RAPID/TA/grant/TC-RNTI；Msg3 含 UL-CCCH SDU；Msg4 以 TC-RNTI 寻址 | Msg4 MAC PDU 含 UE Contention Resolution Identity，且与 Msg3 CCCH SDU（按标准比较规则）匹配 | 设置 `C-RNTI = TC-RNTI`，丢弃 Temporary C-RNTI |
| 4-step、C-RNTI MAC CE Msg3 | Msg3 含 C-RNTI MAC CE；过程规定的后续 PDCCH 以 C-RNTI 寻址 | 触发原因和新传输/恢复条件满足 | 争用解决成功，丢弃 Temporary C-RNTI；C-RNTI CE 是已有标识证据 |
| 2-step successRAR | MsgA 含 CCCH；MsgB successRAR 含 UE Contention Resolution Identity 和 C-RNTI | identity 与 MsgA CCCH 匹配，且 successRAR TB/时序有效 | 直接设置 successRAR 中的 C-RNTI，完成 RA |

2-step fallbackRAR 不是第四条独立确认路径：它提供 TA、UL grant 和 Temporary C-RNTI，随后回到 Msg3/Msg4 子链。CFRA、BFR、HO 和 SI request 可能采用不同完成条件，需保留 `trigger` 并标记 `NEEDS_VERIFICATION`。

## 19. C-RNTI MAC CE 与 UE Contention Resolution Identity

已核对 `3GPP TS 38.321 V17.8.0 (Release 17)` §6.1.3.2--§6.1.3.3：

| MAC CE | V17.8.0 快照 | 用途 | 不是 |
|---|---:|---|---|
| C-RNTI MAC CE | 固定 16 bit，单一 C-RNTI 字段 | Msg3/MsgA 在已有上下文中报告 UE 的 C-RNTI | 任意 PUSCH 上出现的 16-bit 值 |
| UE Contention Resolution Identity MAC CE | 固定 48 bit；承载 UL-CCCH SDU 的前 48 bit（若更长） | Msg4/MsgB 对比本 UE 发送的 CCCH | C-RNTI 数值 |

以上位宽是 V17.8.0 的标准快照；项目 Release、LCID/eLCID 表及加密/抓包可见性必须再次核验。接收端应保存原始 MAC subheader、CE payload 和比较输入，而不是只保存一个 `match=true`。

## 20. RNTI 用途与 PDCCH 边界

在 V17.8.0 §7.1 的用法表中，相关 RNTI 的角色可归纳为：

| RNTI | 典型承载/阶段 | 观测用途 | 证据限制 |
|---|---|---|---|
| RA-RNTI | RAR 的 DL-SCH/PDSCH 响应 | 从 RO 限定 RAR PDCCH 候选 | 不识别 UE |
| MSGB-RNTI | 2-step MsgB 的 DL-SCH/PDSCH 响应 | 限定 MsgB window 候选 | 不等于 C-RNTI |
| Temporary C-RNTI/TC-RNTI | 争用解决 DL、Msg3 UL | 连接临时阶段的 PDCCH CRC 假设 | 超时/成功后应丢弃 |
| C-RNTI | 动态专用 DL-SCH/UL-SCH；也可触发某些 PDCCH order | 建立后续用户资源快照 | 单次 CRC pass 仍可能误检 |

PDCCH 候选的基本接受条件可抽象为：

$$
\mathrm{CRC}(\hat{\mathbf a})\oplus\mathrm{mask}(r)=\mathbf 0,
\qquad r\in\{\mathrm{RA\text{-}RNTI},\mathrm{MSGB\text{-}RNTI},\mathrm{TC\text{-}RNTI},\mathrm{C\text{-}RNTI}\}.
$$

但真正的 `valid_dci` 还需要搜索空间/CORESET、DCI 格式、字段范围、时频资源可解释性和前后时隙连续性。`CRC pass` 只创建候选，不直接改变生命周期状态。

## 21. Msg4 争用解决判决

### 21.1 CCCH SDU 路径

4-step CBRA 中，Msg3 若含 CCCH SDU，接收端应按以下顺序核验：

1. Msg3 PUSCH 的 grant、TC-RNTI、资源、DM-RS 和 UL-SCH/TB-CRC 有效。
2. 争用解决计时器在 Msg3 发送后启动，并在规范允许的重传时机重启。
3. 在计时器运行期间监测以 TC-RNTI 寻址的 PDCCH。
4. 对相应 PDSCH 解码并验证 TB-CRC。
5. 解析 UE Contention Resolution Identity MAC CE，与 Msg3 CCCH SDU 的标准比较片段一致。
6. 只有全部通过才设置 `C-RNTI = TC-RNTI` 并丢弃临时标识。

任何一层失败都保留 `contention_pending` 或 `rejected`，不能因为 Msg4 PDSCH CRC 通过就确认 C-RNTI。

### 21.2 C-RNTI MAC CE 路径

如果 Msg3 含 C-RNTI MAC CE，38.321 的判决依赖触发原因：例如由 MAC/RRC 发起的常规过程需要 C-RNTI 寻址且包含新传输 UL grant；某些 BFR/PDCCH order 分支只需检测 C-RNTI 寻址。被动接收端应把触发原因和条件写入证据账本，不得用一个统一的 `Msg4 identity` 规则覆盖所有路径。

## 22. 生命周期时序图

```text
时间 ───────────────────────────────────────────────────────────────>
PRACH/Msg1 ─> RA-RNTI PDCCH/PDSCH (RAR) ─> TC-RNTI + grant
                                              |
                                              v
                                   Msg3 PUSCH / C-RNTI CE or CCCH
                                              |
                         start ra-ContentionResolutionTimer
                                              |
                PDCCH(TC-RNTI) -> Msg4 identity match
                      |                                  |
             mismatch/timeout                      match / C-RNTI path
                      v                                  v
               discard TC-RNTI                 C-RNTI = TC-RNTI or explicit C-RNTI
               backoff/retry                   discard TC-RNTI; enter CONFIRMED
                                                          |
                                      subsequent C-RNTI DCI continuity / aging
```

2-step successRAR 在图中插入另一条直接分支：`MsgA -> MSGB-RNTI -> successRAR(identity + C-RNTI) -> CONFIRMED`；fallbackRAR 则回到 TC-RNTI/Msg3 子链。

## 23. PHY/MAC/RRC/应用分层

| 层 | C-RNTI 相关责任 | 观测输出 | 不应越界 |
|---|---|---|---|
| RRC | 配置 RACH、CFRA、BWP、搜索空间和连接状态 | 配置/触发快照 | 不由 RRC 字段直接证明空口已确认 |
| MAC | 创建/保存/丢弃 Temporary C-RNTI，处理 Msg3/Msg4 和 CE | 生命周期事件、计时器、身份匹配 | 不把 PHY 相关峰当 C-RNTI |
| PHY | 以候选 RNTI 做 PDCCH CRC、解码 PDSCH/PUSCH、提供 HARQ/ToA | 候选级 CRC、资源、软比特 | 不决定争用解决语义 |
| 观测应用 | 维护有限候选池、连续性和不确定度 | `association_record`、质量和老化 | 不把单次 CRC 通过升级为永久用户 ID |

## 24. 候选评分与连续性

为避免错误 RNTI 偶然通过 CRC，可把证据评分拆成可解释项（权重不预设）：

$$
Q(r)=w_1 I_{RAR}+w_2 I_{RAPID}+w_3 I_{grant}+w_4 I_{Msg3}
     +w_5 I_{Msg4}+w_6 I_{continuity}-w_7 I_{conflict}.
$$

其中每个 $I$ 都应有原始 artifact 支撑；`Q` 只是项目的关联排序，不是 3GPP 合规分数。最低规则建议为：

- `RAR`：PDCCH/PDSCH/TB-CRC 通过且 RAPID 匹配。
- `grant`：UL grant 在目标 BWP/TDD 中可解释。
- `Msg3`：PUSCH 资源/DM-RS/UL-SCH 证据成立。
- `Msg4`：身份匹配或 C-RNTI 路径条件成立。
- `continuity`：后续 DCI 的 RNTI、资源和时序在窗口内一致。

若只有 PDCCH CRC 或单个后续 DCI，状态最高为 `candidate_only`；若多个候选共享同一资源，标 `ambiguous`，不强行选最大分数。

## 25. C-RNTI 状态转移伪代码

```text
update_c_rnti(state, event, release):
    if event.kind == "rar" and event.rapid_match and event.tc_rnti_valid:
        state.tc_rnti = event.tc_rnti
        state.phase = "TEMPORARY_ACTIVE"
        append_evidence(state, event)
        return state

    if state.phase == "TEMPORARY_ACTIVE" and event.kind == "msg3":
        state.msg3_payload_kind = classify_msg3(event.mac_pdu)
        state.phase = "CONTENTION_PENDING"
        start_or_restart_timer(state, event.timer_snapshot)
        return state

    if state.phase == "CONTENTION_PENDING":
        if event.kind == "msg4" and state.msg3_payload_kind == "ccch":
            if event.rnti == state.tc_rnti and event.identity_matches:
                state.c_rnti = state.tc_rnti
                state.tc_rnti = None
                state.phase = "CONFIRMED"
            elif event.tb_crc_ok:
                state.phase = "AMBIGUOUS"
        elif event.kind == "pdcch" and state.msg3_payload_kind == "c_rnti_ce":
            if event.rnti == event.reported_c_rnti and event.path_condition_ok:
                state.phase = "CONFIRMED"
                state.tc_rnti = None
        elif event.timer_expired:
            state.tc_rnti = None
            state.phase = "EXPIRED/RETRY"
        return state

    if event.kind == "success_rar" and event.identity_matches:
        state.c_rnti = event.explicit_c_rnti
        state.phase = "CONFIRMED"
        return state

    return append_evidence(state, event, phase="CANDIDATE_ONLY")
```

伪代码中的 `path_condition_ok` 必须由触发原因和目标 Release 的 38.321 条款计算；不能写成永真。

## 26. C-RNTI 事件账本

| 字段 | 内容 |
|---|---|
| `association_id` | 与 RO、RAR、Msg3/Msg4 和后续 DCI 的稳定关联键 |
| `rnti_value` | 数值、类型（RA/MSGB/TC/C）、来源和版本 |
| `source_event` | RAR、Msg3 C-RNTI CE、Msg4 identity、successRAR、后续 DCI |
| `protocol_phase` | `rar/msg3/contention/connected/expired` |
| `trigger` | RRC、MAC、PDCCH order、HO、BFR、SI request 等 |
| `pdcch_evidence` | 搜索空间、CORESET、候选、CRC、DCI 格式/字段 |
| `mac_evidence` | RAPID、TC-RNTI、CCCH、C-RNTI CE、identity、TB-CRC |
| `resource_closure` | PDSCH/PUSCH PRB、符号、BWP、MCS/TBS/RV、HARQ |
| `timer` | response/contention timer 的启动、重启、过期和来源 |
| `continuity` | 后续 DCI 数量、时间间隔、资源一致性和冲突 |
| `state` | `candidate/temporary/confirmed/expired/ambiguous/revoked` |
| `confidence` | 规则结果或评分；不替代标准判决 |
| `failure_reason` | 结构化缺口，保留原始 artifact 引用 |

推荐把同一数值在不同生命周期的记录分开，不要用一个可变字典覆盖历史：

```text
event_001: RA-RNTI -> rar_candidate
event_002: RAPID match -> temporary_c_rnti
event_003: Msg3 CCCH -> contention_pending
event_004: Msg4 identity match -> c_rnti_confirmed
event_005: later release/timeout -> expired_or_unknown
```

## 27. 负例与最小验证用例

### 负例矩阵

| 场景 | 预期状态 | 禁止的结论 |
|---|---|---|
| PRACH 峰但没有 RAR | `preamble_only` | PRACH 已给出 C-RNTI |
| RAR 有 TC-RNTI 但 Msg3 不可见 | `TEMPORARY_CANDIDATE` | TC-RNTI 已是 C-RNTI |
| Msg3 TB-CRC 过但 Msg4 identity 不匹配 | `AMBIGUOUS/RETRY` | C-RNTI confirmed |
| Msg4 PDSCH CRC 过但寻址 RNTI 错 | `rejected` | identity 自动匹配 |
| C-RNTI CE 16-bit 值出现于错误 MAC PDU | `candidate_only` | 该值属于目标 UE |
| 2-step successRAR 当作 4-step Msg4 | `branch_mismatch` | 复制 TC-RNTI 生命周期 |
| 单次后续 DCI CRC 偶然通过 | `candidate_only` | 长期用户确认 |
| C-RNTI 数值在不同小区/时间重用 | 按 cell/capture 隔离 | 跨小区合并用户 |
| timer 过期后仍看到旧 RNTI | `expired_or_reused_candidate` | 旧值仍有效 |

### 最小验证（设计模板，尚未运行）

1. **C0 纯状态机**：输入 RAR->Msg3 CCCH->Msg4 matching identity，验证 `ABSENT -> TEMPORARY -> CONFIRMED` 且丢弃 TC-RNTI。
2. **C1 不匹配**：仅修改 Msg4 identity 一个 bit，确认进入 `RETRY/REJECTED`，不产生 C-RNTI。
3. **C2 CE 路径**：构造 Msg3 C-RNTI MAC CE 与正确/错误 C-RNTI-addressed PDCCH，验证 `path_condition_ok` 不被 CRC 单独替代。
4. **C3 2-step**：构造 MsgA CCCH + successRAR identity/C-RNTI 和 fallbackRAR 两个样本，检查两条分支不混淆。
5. **C4 错误候选**：错误 RNTI、错误 CORESET、错误 DCI 字段和错误资源各注入一次，统计 `candidate_only`/`rejected`，不记录虚构成功率。
6. **C5 老化/重用**：在不同 cell/capture/frame 使用相同数值，验证候选隔离、过期和重用冲突标记。
7. **C6 连续性**：对单个确认候选删除中间一个 DCI，确认状态降级为 `continuity_gap` 而不是静默维持永久绑定。

## 28. 证据账本与缺口

- `STANDARD + verified (Release 17 snapshot)`：ETSI [TS 38.321 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf)，§3.1 Msg3 定义、§5.1.4/§5.1.5/§5.1.6、§6.1.3.2/§6.1.3.3、§7.1；核对 Msg4 争用解决、C-RNTI/UE Contention Resolution Identity 位宽、RNTI 用途和临时标识丢弃。
- `STANDARD + verified snapshot`：ETSI [TS 38.213 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf)，§8.3--§8.4；核对 TC-RNTI 加扰、Msg3 重传、Msg4 PDSCH 和物理时序接口。
- `STANDARD + partial`：[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.214｜Physical layer procedures for data]]；PDCCH/PDSCH/PUSCH 编码、映射和资源快照需与项目 Release 对齐。
- `PERSONAL_NOTE`：[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]] 的跨消息关联约定。
- `EXPERIMENT + NEEDS_VERIFICATION`：C0--C6 仅为状态机/协议门测试设计，当前没有真实 C-RNTI 关联结果。
- `NEEDS_EXTERNAL_REFERENCE`：项目网络 Release、CFRA/BFR/HO/SI request 的完成条件、RRC 连接释放/重用规则、PDCCH 候选连续性窗口、MAC 加密和设备抓包可见性；不能从单个 RNTI 数值推断。
