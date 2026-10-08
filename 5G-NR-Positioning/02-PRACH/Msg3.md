---
title: Msg3
aliases:
  - NR Msg3
  - 随机接入第三消息
  - Msg3 PUSCH
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/random-access
  - channel/pusch
  - topic/user-association
  - stage/receiver
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.214
  - 3GPP TS 38.321
related:
  - "[[5G-NR-Positioning/02-PRACH/RAR|RAR]]"
  - "[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]"
  - "[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]"
  - "[[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]"
  - "[[01-专题知识/信道编译码/NR编码链/NR-UL-SCH 编码链|NR-UL-SCH 编码链]]"
---
# Msg3

## 1. 一句话定义

Msg3 是 4-step 随机接入中 UE 按 RAR 的 UL grant 在 PUSCH 上发送的第三条消息，通常承载 CCCH 相关内容，也可能携带 C-RNTI MAC CE。

## 2. 为什么项目需要它

Msg3 将 RAR 的临时标识和资源授权连接到 UE 的后续争用解决；被动接收机可用其 PUSCH 资源、时序和 MAC 内容增强用户关联，但不能假设每个 Msg3 都明文携带 C-RNTI。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 RAR/Temporary C-RNTI 之后、Msg4 contention resolution 之前；成功关联后，C-RNTI 进入 PDCCH/DCI 和 PDSCH/PUSCH 资源跟踪。

## 4. 输入

- RAR 中与 RAPID 匹配的 UL grant、TA 和 Temporary C-RNTI。
- PUSCH BWP/PRB/符号、MCS/TBS/RV、DM-RS、HARQ 和 UCI 配置。
- TDD UL 可用时隙、采样 IQ 和用户关联候选。

## 5. 输出

- Msg3 PUSCH 资源快照、时序/ToA、DM-RS 质量。
- UL-SCH/CCCH SDU 或 C-RNTI MAC CE 的解析状态（若可见）。
- 供 Msg4 争用解决和 C-RNTI 确认使用的关联证据。

## 6. 关键参数

UL grant 的频域/时域分配、MCS、TBS、RV、HARQ 进程、Temporary C-RNTI、PUSCH DM-RS 端口/序列、TA、UCI 复用和 Msg3 重传限制。具体字段按 TS 38.214/38.321 版本核对。

## 7. 时域位置

Msg3 在 RAR 指定的后续 UL 时机发送，TA 命令会调整 UE 上行发射时刻。捕获端应区分“按 grant 的计划时隙”和“实际观测到的样点峰”。

## 8. 频域位置

Msg3 使用 RAR UL grant 指定的 PUSCH PRB/BWP 和 OFDM 符号，可能发生频域跳变；资源坐标应与 DCI/RAR 快照一致，并保留 DM-RS/PTRS 掩码。

## 9. 数学原理

给定 grant 推出的资源集合 $\mathcal{R}_{g}$，接收机先在 $\mathcal{R}_{g}$ 提取 PUSCH，再进行软解调和 UL-SCH 译码：

$$
\hat{\mathbf{b}}=\mathrm{ULSCHDecode}
\left(\mathrm{Demod}\left(\mathrm{Equalize}(\mathbf{y}_{\mathcal{R}_{g}})\right)\right).
$$

资源命中、DM-RS、TB-CRC 和 MAC 内容需分别判决；C-RNTI MAC CE 只有在正确解析其承载和争用上下文后才可作为标识证据。

## 10. 3GPP 对应规范

- TS 38.321 §5.1.4/§5.1.5：RAR 后 Msg3 传输与 contention resolution，具体段落随 Release 核对。
- TS 38.211：PUSCH、DM-RS 和资源映射（相关 §6.3.1 等子条款待核）。
- TS 38.214：UL grant、MCS、TBS、HARQ 和时域/频域资源。
- TS 38.212：UL-SCH/CRC/LDPC/率匹配；C-RNTI MAC CE 字段属于 TS 38.321。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPUSCHIndices、nrPUSCH、nrPUSCHDMRSIndices、nrPUSCHDMRS：生成/提取 PUSCH 及 DM-RS。
- nrPUSCHDecode、nrULSCHDecoder：软解调和 UL-SCH 译码链。
- MAC CE/CCCH 解析没有本地一键 API；函数属性、输入维度和版本需本机核验，状态 NEEDS_EXTERNAL_REFERENCE。

## 12. 本项目中的用途

利用 RAR grant 定位 Msg3 PUSCH，验证 Temporary C-RNTI、资源、时序和 TB/MAC 字段，再把结果交给 [[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]] 和 [[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]；Msg3 本身不是最终 C-RNTI 的充分条件。

## 13. 常见误区

- 把所有 Msg3 都当作含 C-RNTI MAC CE。
- 把 PUSCH 能量峰当 Msg3，忽略 RAR grant 和 UL 时序。
- 忽略 TA、DM-RS、UCI 复用或重传造成的资源变化。
- 将 Msg3 的 Temporary C-RNTI 与最终 C-RNTI 混写。

## 14. 与相似概念的区别

Msg3 是随机接入消息/一次 PUSCH 传输；RAR 是下行 Msg2；Msg4 是下行争用解决；C-RNTI 是标识；C-RNTI MAC CE 是可能承载在 Msg3 或后续 MAC 中的字段，不能与整个 Msg3 等同。

## 15. 代码实现注意事项

- 从 RAR UL grant 计算资源，不按“典型 Msg3 PRB”硬编码。
- 保存 PUSCH、DM-RS、UL-SCH、UCI 各自掩码和版本。
- 将资源命中、译码、MAC 字段和关联置信度分开输出。
- Msg3 缺失时保留临时状态，不自动判为 C-RNTI 失败。

## 16. 待实验验证的问题

- 当前设备能否捕获完整 Msg3 PUSCH 及 DM-RS。
- RAR grant 到实际 PUSCH 资源映射的 K2/TA 误差。
- CCCH SDU、C-RNTI MAC CE 和重传场景的可见性。
- 多用户同一 RO 时如何区分 Msg3 资源和碰撞。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。
- 后续控制/数据：[[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]、[[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]。
- 旧笔记：[[01-专题知识/信道编译码/NR编码链/NR-UL-SCH 编码链|NR-UL-SCH 编码链]]、[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|现有控制/数据主线]]。

## 18. Msg3 的协议语义与边界

> [!important] ❗ 先区分 Msg3 与 MsgA
> 在 4-step（Type-1）中，Msg3 是 RAR UL grant 指向的 UL-SCH/PUSCH 传输；在 2-step（Type-2）中，PRACH 前导和关联 PUSCH 同时组成 MsgA，只有收到 fallbackRAR 后才可能出现一个后续 Msg3。不能把所有“PRACH 后的 PUSCH”都命名为 Msg3。

`3GPP TS 38.321` 的定义把 Msg3 限定为承载 `C-RNTI MAC CE` 或 `CCCH SDU`、并与 UE Contention Resolution Identity 相关的 UL-SCH 消息。对被动接收机而言，能量峰、DM-RS 或 PUSCH CRC 只能证明 PHY 候选，不能单独证明它是随机接入 Msg3。

### 18.1 4-step/2-step/CBRA/CFRA 对照

| 分支                 | 上行消息                          | PUSCH 资源来源                       | 标识/竞争语义                                  | Msg3 是否必然存在             |
| -------------------- | --------------------------------- | ------------------------------------ | ---------------------------------------------- | ----------------------------- |
| 4-step CBRA          | Msg1 PRACH -> Msg3 PUSCH          | RAR 的 UL grant                      | Temporary C-RNTI，等待 Msg4                    | 是（RAR 成功且 grant 可用时） |
| 4-step CFRA          | 专用 Msg1 PRACH -> 可能的 UL 传输 | RRC 专用资源或 RAR 分支              | 专用前导降低碰撞；是否需要 Msg4 由触发场景决定 | 不一定，需看 CFRA 分支        |
| 2-step CBRA          | MsgA = PRACH + MsgA PUSCH         | `MsgA-PUSCH-Config` 的映射         | MsgB 以 MSGB-RNTI 寻址；失败可 fallback        | MsgA 本身不是 Msg3            |
| 2-step CBRA fallback | MsgA -> fallbackRAR -> Msg3 PUSCH | fallbackRAR UL grant                 | 重新使用 Temporary C-RNTI/争用解决             | 是，若 fallbackRAR 命中       |
| 2-step CFRA          | 专用 MsgA PRACH + PUSCH           | `CFRA-TwoStep` 专用 PUSCH occasion | 由专用资源和 MsgB 分支决定                     | 通常不是标准 4-step Msg3 语义 |

表中“是否”只描述过程结构，不能代替目标 Release 的 `RACH-ConfigDedicated` 和触发原因核验。

## 19. RAR UL grant 到 Msg3 资源的闭环

RAR 给出的 UL grant 是 MAC RAR payload，不是完整的 DCI 0_0。根据已核对的 `TS 38.213 V17.8.0 (Release 17)` §8.3，接收端至少需要以下输入才能展开 PUSCH：

| 资源维度              | 来源                      | 记录要求                      |
| --------------------- | ------------------------- | ----------------------------- |
| UL BWP、SCS、CP、载波 | RRC/38.213                | 保存初始/活动 BWP 和 NUL/SUL  |
| 频域分配/跳频         | RAR grant + 38.213/38.214 | 保存原始 grant 位串和解释版本 |
| 时域分配、K2/处理间隔 | RAR grant + 38.214/38.213 | 不写入未核验默认值            |
| MCS/TBS/RV            | RAR grant + 38.214        | 保留`RV=0` 的版本化依据     |
| DM-RS、层、变换预编码 | RRC/38.211/38.214         | 保存端口、序列和映射类型      |
| TA、TDD UL 符号       | RAR + RRC                 | 同时记录计划时隙和观测样点    |

资源展开应产生一个不可变 `msg3_resource_snapshot`：

```JSON
msg3_resource_snapshot = {
  response_rnti, temporary_c_rnti,
  serving_cell, ul_carrier, bwp_id, scs, cp,
  grant_raw, grant_schema_version,
  slot_plan, symbol_set, prb_set,
  mcs, tbs, rv, harq_process,
  dmrs_snapshot, transform_precoder,
  ta_raw, ta_application_state
}
```

若任一依赖缺失，状态为 `grant_unresolved`；不能根据“典型 Msg3 只占少数 PRB”自行补齐资源。

### 19.1 时域关系

在 38.213 V17.8.0 §8.3 中，若 RAR PDSCH 在 slot `n` 结束，后续 PUSCH 计划时隙可抽象为：

$$
n_{Msg3}=n+k_2+\Delta+2^{\mu}N_{cell\_offset},
$$

其中 `k2`、`Delta`、`mu` 和小区偏移来自相应标准/配置；上式是接口关系，不是允许硬编码的固定延迟。还必须检查 PDSCH 处理时间、PUSCH 准备时间、TDD UL 符号和跨帧边界。

TA 命令改变 UE 的上行发射定时，因而观测到的 PUSCH 峰可能相对“计划 slot/symbol”发生偏移。项目日志应把两者分开：

```JSON
planned_time = (frame, slot, symbol, k2, cell_offset)
observed_time = (capture_id, sample_index, toa_reference, peak_policy)
```

## 20. UL-SCH/MAC PDU 内容

### 20.1 可能承载的内容

| 内容                 | 典型出现条件                                  | 可观察证据                                               | 结论限制                                                     |
| -------------------- | --------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------ |
| UL-CCCH SDU          | CBRA 首次接入等场景                           | UL-SCH 译码 + LCID/SDU                                   | 用于后续 UE Contention Resolution Identity 匹配，不是永久 ID |
| C-RNTI MAC CE        | UE 已有 C-RNTI 且过程要求在后续 UL 传输报告它 | MAC subheader 的 C-RNTI LCID + 16-bit CE（V17.8.0 快照） | 只有正确 MAC PDU 和过程上下文才是标识证据                    |
| 其他 MAC CE/逻辑信道 | BFR、优先级、实现/Release 场景                | LCID/eLCID 与长度字段                                    | 不得因出现 CE 就改写 RA 分支                                 |
| Padding              | 传输块剩余空间                                | LCID=padding 或长度闭合                                  | 不携带用户身份                                               |

一个 Msg3 可以是 CCCH SDU 路径，也可以是 C-RNTI MAC CE 路径；不要在解码器中预设“Msg3 必含 C-RNTI”。`C-RNTI MAC CE` 的 16-bit 宽度来自 V17.8.0 §6.1.3.2，项目 Release 仍须复核。

### 20.2 编码和物理边界

```Markdown
MAC PDU (CCCH/CE)
    ↓ 38.321 disassembly/assembly
UL-SCH TB + TB-CRC
    ↓ 38.212
LDPC/率匹配/扰码
    ↓ 38.211 + 38.214
PUSCH RE + DM-RS + OFDM waveform
```

接收端应分别记录：

1. PUSCH 资源是否命中 `msg3_resource_snapshot`。
2. DM-RS 是否存在且能支持信道估计。
3. UL-SCH/TB-CRC 是否通过。
4. MAC 子头、CCCH/CE 和长度是否解析成功。
5. 这些证据是否满足 Msg4/争用解决的协议条件。

## 21. TC-RNTI、扰码与 HARQ

在已核对的 38.213 V17.8.0 §8.3 中，RAR UL grant 对应的 PUSCH 在提供 Temporary C-RNTI（常用简称 `TC-RNTI`）时使用该标识进行扰码初始化；Msg3 重传由 CRC 掩码为 TC-RNTI 的 DCI 0_0 调度。该事实只说明物理层加扰/重传接口，不等于“TC-RNTI 已升级为 C-RNTI”。

同一规范还规定，无重复配置时该 PUSCH 的 transport block 使用版本化的 RV 规则（V17.8.0 基线为 `RV=0`）；若项目启用 Msg3 repetition、共享频谱或后续 Release 扩展，必须重新读取条款。

建议把 HARQ 证据拆开：

| 事件            | 保存字段                         | 允许升级                  |
| --------------- | -------------------------------- | ------------------------- |
| 首次 grant      | TC-RNTI、grant、HARQ process、RV | `msg3_scheduled`        |
| 首次 PUSCH      | 资源、DM-RS、样点峰、TB-CRC      | `msg3_observed`         |
| 重传 DCI        | CRC mask=TC-RNTI、RV/NDI、资源   | `msg3_retx_candidate`   |
| 软合并/译码     | 母码坐标、LLR、TB-CRC            | `msg3_decoded`          |
| Msg4/后续 PDCCH | TC-RNTI/C-RNTI、身份字段、计时器 | `contention_resolution` |

不要把“PUSCH TB-CRC 通过”直接当作争用解决成功；Msg4 条件仍需满足。

## 22. 时序图：Msg3 到 Msg4

```Markdown
slot/time ──────────────────────────────────────────────────────────>
RAR PDSCH (Msg2) ──[decode + TA/grant/TC-RNTI]──┐
                                                 │
                                                 ├─ k2/processing/TDD/TA
                                                 v
                                      Msg3 PUSCH (UL-SCH)
                                                 │
                          start/restart contentionResolutionTimer
                                                 │
                                                 v
                         PDCCH(TC-RNTI) -> Msg4 PDSCH
                            ├─ UE Contention Resolution Identity match
                            └─ C-RNTI MAC CE / C-RNTI-addressed path
```

如果 Msg3 含 CCCH SDU，Msg4 需要通过 Temporary C-RNTI 寻址并携带匹配的 UE Contention Resolution Identity；如果 Msg3 含 C-RNTI MAC CE，判决条件转为过程规定的 C-RNTI 寻址/新传输条件。具体条件必须按触发原因和 Release 复核，不能只看 Msg4 的 PDSCH CRC。

## 23. Msg3 证据状态机

| 状态                    | 进入条件                 | 必须保存                         | 失败/下一步                         |
| ----------------------- | ------------------------ | -------------------------------- | ----------------------------------- |
| `grant_pending`       | RAR RAPID 已匹配         | 原始 grant、TA、TC-RNTI、BWP     | 资源展开失败 ->`grant_unresolved` |
| `scheduled`           | 时域/频域/TDD 约束通过   | 计划 slot/symbol/PRB、MCS/TBS/RV | 资源冲突 ->`not_transmittable`    |
| `pusch_candidate`     | 目标资源有能量/DM-RS     | IQ 片段、相关/DM-RS 指标         | 无峰 ->`not_observed`             |
| `tb_decoded`          | UL-SCH/TB-CRC 通过       | LLR、码块、CRC、HARQ             | MAC 解析失败 ->`mac_unresolved`   |
| `mac_parsed`          | LCID/SDU/CE 长度闭合     | CCCH 或 C-RNTI CE 原文           | 内容未知 ->`content_unresolved`   |
| `contention_pending`  | Msg3 已发送并启动计时器  | timer、TC-RNTI、候选 Msg4        | 超时/身份不匹配 -> retry/rejected   |
| `contention_evidence` | Msg4/后续 PDCCH 条件满足 | identity、RNTI、时序             | 进入 C-RNTI 状态机                  |

上述是观测证据状态，不替代 UE MAC 的 `Msg3 buffer`、HARQ 和计时器内部状态。

## 24. Msg3 接收伪代码

```python
process_msg3(ro_event, rar, phy_capture, config, release):
    require rar.rapid == ro_event.preamble_index
    tc_rnti = rar.temporary_c_rnti
    grant = parse_rar_ul_grant(rar.ul_grant, config, release)
    if grant.invalid:
        return state("grant_unresolved", reason=grant.error)

    planned = derive_pusch_resources(grant, config, rar.ta, release)
    if not tdd_and_bwp_valid(planned, config):
        return state("not_transmittable", reason="resource_context")

    rx = extract_pusch(phy_capture, planned)
    dmrs = estimate_from_dmrs(rx, planned.dmrs)
    llr = pusch_demodulate(rx, dmrs, planned.noise)
    tb = ulsch_decode(llr, planned.tbs, planned.rv, release)
    if not tb.tb_crc_ok:
        return state("pusch_candidate", reason="tb_crc")

    mac = parse_ul_mac_pdu(tb.bits, release)
    if mac.invalid:
        return state("mac_unresolved", reason=mac.error)
    if mac.has_ccch:
        payload_kind = "ccch"
    elif mac.has_c_rnti_ce:
        payload_kind = "c_rnti_ce"
    else:
        payload_kind = "other_or_unknown"
    return state("contention_pending",
                 tc_rnti=tc_rnti,
                 payload_kind=payload_kind,
                 evidence=[rar, planned, dmrs, tb, mac])
```

解析失败时保留原始 LLR 和资源快照，便于区分 grant 错、DM-RS 错、LLR 错和 MAC 结构错。

## 25. 事件账本

| 字段                                 | 说明                                                |
| ------------------------------------ | --------------------------------------------------- |
| `msg3_event_id`                    | 与`rar_event_id`、RO 和捕获片段关联               |
| `ra_type` / `access_mode`        | `4step/2step-fallback`、`CBRA/CFRA`；未知时标记 |
| `temporary_c_rnti`                 | 原值、来源和有效时间区间                            |
| `grant_raw` / `grant_schema`     | RAR 27-bit 原文及解释版本                           |
| `resource_snapshot`                | BWP、PRB、symbol、MCS、TBS、RV、HARQ、DM-RS         |
| `planned_time` / `observed_time` | 计划资源与实际峰/ToA 分开                           |
| `phy_status`                       | 能量、DM-RS、信道估计、TB-CRC                       |
| `mac_status`                       | LCID、CCCH、C-RNTI CE、padding、长度闭合            |
| `timer_state`                      | contention timer 的启动/重启/超时证据               |
| `evidence_state`                   | 本页状态机值                                        |
| `failure_reason`                   | 结构化原因和原始 artifact 引用                      |

## 26. 负例与最小验证用例

### 负例矩阵

| 场景                                | 预期状态                             | 不应误判                 |
| ----------------------------------- | ------------------------------------ | ------------------------ |
| RAR grant 解析缺 BWP/SCS            | `grant_unresolved`                 | 采用默认 PRB/K2          |
| PUSCH 能量存在但无 DM-RS/资源不匹配 | `pusch_candidate`/`not_observed` | “Msg3 已发送”          |
| TB-CRC 失败                         | 保留 PHY 候选，`tb_decode_failed`  | “RAR/PRACH 失败”       |
| MAC 有 CCCH 但无 C-RNTI CE          | `contention_pending`               | “没有用户标识”         |
| MAC 有 C-RNTI CE 但过程上下文未知   | `content_unresolved`               | 直接确认 C-RNTI          |
| 用 RA-RNTI 解 Msg3 重传 DCI         | `rnti_context_error`               | 解码成功即接受           |
| TA 应用状态未知                     | `timing_unresolved`                | 把样点偏移归因于传播距离 |
| 2-step MsgA PUSCH 当作 Msg3         | `branch_mismatch`                  | 进入 4-step Msg4 状态    |

### 最小验证（设计模板，尚未运行）

1. **M0 资源闭环**：用已知 RAR grant 和配置生成 Msg3 计划资源，逐字段比对 PRB、符号、BWP、MCS/TBS/RV。
2. **M1 无噪声 UL-SCH**：构造 CCCH SDU 和 C-RNTI MAC CE 两个样本，验证 UL-SCH/TB-CRC/MAC LCID 逆过程。
3. **M2 TC-RNTI 加扰**：同一 PUSCH 分别用正确/错误 TC-RNTI 解扰，确认错误标识不应稳定通过 TB-CRC；具体 `c_init` 由目标 Release/38.211 核验。
4. **M3 时序扰动**：注入 K2、TA、TDD 方向和跨帧偏差，确保计划资源错误与 PHY 无峰被分别报告。
5. **M4 Msg4 条件**：对 CCCH 路径构造匹配/不匹配 UE Contention Resolution Identity；对 C-RNTI CE 路径构造正确/错误 PDCCH 寻址，检查状态只在条件闭合时升级。
6. **M5 重传**：构造 TC-RNTI 加扰的 DCI 0_0 和不同 RV，验证 HARQ 软合并坐标不被覆盖。

## 27. 证据账本与缺口

- `STANDARD + verified snapshot`：ETSI [TS 38.213 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf)，§8.1A、§8.3、§8.4；核对 Type-2 MsgA PUSCH、RAR UL grant 调度的 PUSCH、TC-RNTI 加扰/重传和 Msg4 物理边界。
- `STANDARD + verified (Release 17 snapshot)`：ETSI [TS 38.321 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf)，§3.1 Msg3 定义、§5.1.4/§5.1.5、§6.1.3.2；C-RNTI MAC CE/CCCH 与争用解决流程。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.214｜Physical layer procedures for data]]、[[3GPP TS 38.212｜Multiplexing and channel coding]]；物理映射、MCS/TBS、UL-SCH 译码和版本表需与项目配置对齐。
- `PERSONAL_NOTE`：[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]] 的事件交接和定位观测边界。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页 M0--M5 为测试设计，当前没有真实 Msg3 IQ、MAC PDU 或重传结果。
- `NEEDS_EXTERNAL_REFERENCE`：项目网络 Release、Msg3 repetition/共享频谱、具体 RRC BWP/DM-RS 配置、MAC 加密可见性、2-step CFRA/回退条件；不得用默认参数填补。
