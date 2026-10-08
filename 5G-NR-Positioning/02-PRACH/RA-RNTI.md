---
title: RA-RNTI
aliases:
  - Random Access RNTI
  - 随机接入无线网络临时标识
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/random-access
  - topic/rnti
  - stage/user-association
source:
  - 3GPP TS 38.213
  - 3GPP TS 38.321
  - 3GPP TS 38.211
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]"
  - "[[5G-NR-Positioning/02-PRACH/RAR|RAR]]"
  - "[[5G-NR-Positioning/03-PDCCH/RNTI|RNTI]]"
  - "[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]"
---

# RA-RNTI

## 1. 一句话定义

RA-RNTI 是由 PRACH Occasion 的时域、频域和上行载波上下文推导出的随机接入无线网络临时标识，用于寻址该 Occasion 对应的 RAR。

## 2. 为什么项目需要它

它把物理前导事件映射到 RAR PDCCH 搜索上下文，是从 Msg1 进入 Msg2 的桥梁；它不是 UE 唯一标识，也不是最终 C-RNTI。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 PRACH Detection/Occasion 之后、RAR PDCCH/PDSCH 之前；RAR 解析出的 Temporary C-RNTI 再进入 Msg3/Msg4 和最终 C-RNTI 关联。

## 4. 输入

- RO 的时域索引 s_id、时间索引 t_id、频域索引 f_id。
- 上行载波索引 ul_carrier_id。
- 当前小区、帧/时隙、PRACH 配置和适用 Release。

## 5. 输出

- RA-RNTI 数值和版本/配置来源。
- RAR window 的监测候选、对应 RO 和关联事件键。
- 候选状态（computed、matched、unmatched、ambiguous）。

## 6. 关键参数

s_id、t_id、f_id、ul_carrier_id、RA 类型（2-step/4-step）、RACH Occasion、响应窗口和 RNTI 位宽。公式中的索引定义必须与同一版本的 TS 38.213/38.321 一致。

## 7. 时域位置

RA-RNTI 本身不占用独立时域资源；它在 RO 之后的 RAR window 内作为 PDCCH CRC 掩码假设使用。窗口起止由 RA 配置和 TDD 时序决定。

## 8. 频域位置

RA-RNTI 本身不是频域符号；它指向可能承载 RAR 的 PDCCH/PDSCH 资源。f_id 只描述生成标识的 RO 频域上下文，不能替代 RAR 的 PRB 位置。

## 9. 数学原理

在已锁定的版本中，常见写法为

$$
RA\text{-}RNTI=1+s_{id}+14t_{id}+14\cdot80f_{id}
+14\cdot80\cdot8\,ul\_carrier\_id.
$$

这只是版本化接口的常见形式；s_id、t_id、f_id 的取值域、2-step 分支及特殊载波场景必须回到标准核对。接收端使用该值恢复 RAR PDCCH 的 CRC 掩码，再检查 DCI/资源和 RAPID。

## 10. 3GPP 对应规范

- TS 38.321 §5.1.4：RAR 过程及 RA-RNTI 上下文；公式和字段按项目版本复核。
- TS 38.213 §8.1、§8.2/§8.2A：PRACH Occasion、RAR 监测时机和物理控制过程。
- TS 38.211 §6.3.3.2：RO 物理资源；相关字段来自 RACH-ConfigCommon（TS 38.331，待核）。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

没有专用 RA-RNTI 计算 API。可用 nrPRACHConfig/自定义 RO 枚举生成索引，再将数值作为 nrPDCCHDecode 的 RNTI 假设；函数参数和 RNTI 类型需本机版本核验。

## 12. 本项目中的用途

由 [[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]] 和检测事件计算 RA-RNTI，限定 RAR 搜索窗口；匹配 RAR RAPID 后再把 Temporary C-RNTI 交给 [[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]，不得直接填入 C-RNTI 字段。

## 13. 常见误区

- 把 RA-RNTI 当 UE 身份或长期 C-RNTI。
- 用 PRACH 前导索引单独计算 RA-RNTI，忽略 RO。
- 忽略 ul_carrier_id、跨帧和版本差异。
- RA-RNTI CRC 通过后不检查 RAR 的 RAPID/资源合法性。

## 14. 与相似概念的区别

RA-RNTI 标识 RAR 响应上下文；Temporary C-RNTI 是 RAR 给接入过程的临时 UE 标识；C-RNTI 用于后续专用调度；preamble index 是 RO 内序列编号。四者语义和生命周期不同。

## 15. 代码实现注意事项

- 计算函数输入必须带 config_id、Release 和 RO 原始坐标。
- 保存十进制值及构成索引，便于审计和复算。
- 对同一 RO 生成的候选在 RAR window 内去重，但不合并不同 RO。
- 先做 RNTI CRC，再做 DCI 格式、资源和 RAPID 一致性检查。

## 16. 待实验验证的问题

- 设备或网络元数据能否恢复四个索引和适用载波。
- 2-step/特殊载波下公式是否变化。
- RA-RNTI 候选在现场 PDCCH 盲搜中的误检率和窗口大小。
- RAR MAC PDU 多 RAPID 时的匹配策略。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。
- 后续控制：[[5G-NR-Positioning/03-PDCCH/RNTI|RNTI]]、[[5G-NR-Positioning/03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]。
- 旧笔记：[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]。

## 18. 版本化标准核验

> [!important] 证据边界
> 本节的精确索引域和算式已与 `3GPP TS 38.321 V17.8.0 (Release 17)` §5.1.3（2024-05 版 ETSI 文档）逐项对照；项目现场的 Release、勘误和专用场景仍须重新核验。未锁定版本时，只把 RA-RNTI 当作“由 RO 上下文计算的候选”，不要复制常数或默认索引范围。

在该版本中，RA-RNTI 由发送前导所在 PRACH occasion 计算：

$$
\mathrm{RA\text{-}RNTI}=1+s_{id}+14t_{id}+14\cdot80f_{id}+14\cdot80\cdot8\,ul\_carrier\_id.
$$

| 符号              | 标准语义（V17.8.0）                                                          | 接收端保存方式                        |
| --------------- | ---------------------------------------------------------------------- | ------------------------------ |
| `s_id`          | RO 第一个 OFDM 符号的索引，`0 <= s_id < 14`                                     | 记录帧/时隙/符号三元组及转换版本              |
| `t_id`          | 系统帧内 RO 第一个 slot 的索引，`0 <= t_id < 80`；所用 numerology 由 38.211 的 `mu` 决定 | 保存系统帧号、slot、`mu`，不要只保存数组行号     |
| `f_id`          | 一个时域实例内频域 RO 的索引，`0 <= f_id < 8`                                       | 保存 PRACH 频域起点、FDM 序号和 BWP/载波坐标 |
| `ul_carrier_id` | RA 所用上行载波：NUL 为 `0`，SUL 为 `1`                                          | 保存载波选择原因和 `SUL/NUL` 配置快照       |

公式中的 `s_id/t_id/f_id` 不是前导索引；同一个 RO 内不同前导共享同一 RA-RNTI。`preamble_index` 必须留在关联键中，供后续 RAR 的 RAPID 匹配使用。

### 18.1 RA-RNTI 与 MSGB-RNTI

38.321 V17.8.0 §5.1.3a 对 2-step RA 还定义了由同一 RO 推导的 MSGB-RNTI：

$$
\mathrm{MSGB\text{-}RNTI}=\mathrm{RA\text{-}RNTI}+14\cdot80\cdot8\cdot2.
$$

这是**版本化标准接口**，不是可脱离 Release 的通用常数。2-step 接收端应按 MSGB-RNTI 监测 MsgB；若 MsgB 包含 fallbackRAR，后续可能回到 Msg3；若包含 successRAR，则走成功/争用解决分支。不要用 RA-RNTI 直接代替 MSGB-RNTI，也不要看到任意 PDCCH CRC 通过就把它归入 MsgB。

对于 4-step，RA-RNTI 用于 RAR 的 PDCCH/PDSCH 响应上下文。对于 2-step，RA-RNTI 仍描述 PRACH 事件，但响应寻址通常使用 MSGB-RNTI。对于某些 contention-free beam-failure-recovery 分支，38.321 允许以 C-RNTI 监测恢复搜索空间，且不按普通 CBRA 路径计算/使用 RA-RNTI；该分支必须由 RRC/MAC 触发原因确认，标记为 `NEEDS_VERIFICATION`，不能从一个峰值推断。

### 18.2 上下文唯一性与碰撞边界

建议把 RA-RNTI 计算的输入封装为不可变快照：

```python
ro_context = {
  cell_id, carrier_id, release,
  frame, slot, first_symbol, mu,
  freq_occasion_index, ul_carrier_id,
  preamble_index, ssb_or_csi_rs, capture_id
}
ra_rnti = f(ro_context.first_symbol,
            ro_context.slot_in_system_frame,
            ro_context.freq_occasion_index,
            ro_context.ul_carrier_id,
            ro_context.release)
```

RA-RNTI 的可区分性只覆盖标准定义的 RO 上下文，不覆盖 UE 身份：

| 情况 | RA-RNTI 关系 | 处理 |
|---|---|---|
| 同一 RO、多个前导 | 相同 RA-RNTI、不同 RAPID | 一个 RAR PDU 逐 RAPID 匹配；不能合并成一个 UE |
| 同一 RO、同一前导的多 UE 碰撞 | 相同 RA-RNTI、相同 RAPID | 只能保留碰撞/不可消歧状态 |
| 不同频域 RO | 通常 `f_id` 不同，候选可能不同 | 不得跨 `RO_f` 借用 RAR |
| NUL 与 SUL | `ul_carrier_id` 不同 | 载波必须进入事件键和验证日志 |
| 不同小区/采集窗口 | 数值可能重用 | 必须用 `cell_id + capture_id + frame` 隔离 |

因此，RA-RNTI 是**响应窗口寻址键**，不是身份键。一个通过 RA-RNTI 掩码的 DCI 只能产生 `rar_candidate`，还需要 TB-CRC、RAPID、时序和字段范围共同确认。

## 19. 4-step/2-step 与 CBRA/CFRA 对照

下表只描述跨版本稳定的流程边界；字段是否存在、窗口长度和专用资源由对应 Release 的 RRC 配置决定。

| RA 类型/模式 | Msg1/MsgA 资源 | 响应 RNTI | 是否预期 RAR RAPID | 后续分支 | 证据要求 |
|---|---|---|---|---|---|
| 4-step CBRA | PRACH 前导（Msg1） | RA-RNTI | 是，匹配 `preamble_index` | RAR grant -> Msg3 -> Msg4 | `STANDARD + partial`，需全链闭合 |
| 4-step CFRA | RRC 专用 RO/前导 | RA-RNTI 或恢复场景的 C-RNTI 监测 | 依分支；专用前导不应套 CBRA 碰撞假设 | 可能在 RAR 后直接完成 | `STANDARD + NEEDS_VERIFICATION` |
| 2-step CBRA | PRACH 前导 + 关联 MsgA PUSCH | MSGB-RNTI（由 RO 上下文推导） | MsgB 可为 fallbackRAR 或 successRAR | fallback -> Msg3；success -> 身份匹配/完成 | `STANDARD + partial` |
| 2-step CFRA | 专用前导 + 专用 MsgA PUSCH occasion | MSGB-RNTI/专用恢复上下文 | 由 `CFRA-TwoStep` 分支决定 | 不得复用 CBRA 的随机选择和碰撞结论 | `STANDARD + NEEDS_VERIFICATION` |

`RACH-ConfigCommon`、`RACH-ConfigCommonTwoStepRA` 和 `RACH-ConfigDedicated` 的存在与选择属于 RRC/MAC 配置；被动接收端若只看到 IQ，不能反向假设当前是 CBRA、CFRA、4-step 或 2-step。

## 20. PHY/MAC/RRC 边界

| 层 | 负责的动作 | 输入 | 输出 | 不应越界推断 |
|---|---|---|---|---|
| RRC | 广播/专用 RACH 配置、SSB/CSI-RS 到 RO 映射、2/4-step 和 CFRA 资源 | SIB1、专用 RRC、配置版本 | `rach_config_snapshot` | 不由一次相关峰决定 UE 身份 |
| MAC | 选择 RA 资源、计算 RA-RNTI、启动响应窗口、匹配 RAPID、维护计数器/临时标识 | 配置、触发原因、PHY 检测事件 | `ra_rnti_candidate`、RAR/Msg3 状态 | 不把物理峰幅度当作 C-RNTI |
| PHY | PRACH 发送/检测、PDCCH/PDSCH 解调、CRC 和时频资源判决 | IQ、网格、参考信号和物理配置 | preamble、ToA、PDCCH/PDSCH 候选 | 不直接生成 MAC 身份结论 |
| 观测/定位应用 | 保存事件键、质量和跨站时间 | 各层 artifact | 可追溯 `association_record` | 不把 RA-RNTI 解释成永久用户 ID |

## 21. 时序图：从 RO 到 RAR 监测

```text
时间 ───────────────────────────────────────────────────────────────>
RRC/MAC 配置       [RO/载波/Release 快照]
                         |
PHY                 PRACH RO (Msg1)
                         |  first_symbol, slot, f_id, ul_carrier_id
MAC                 计算 RA-RNTI
                         |---------------- RAR response window ----------------|
PHY/MAC             监测 RA-RNTI PDCCH -> 解 PDSCH -> 解析 RAR
                         |                                   |
                         +-- RAPID 不匹配/CRC 失败 -> candidate_rejected
                                                             |
                                                     Msg3/Msg4 关联链
```

窗口是“从指定 PDCCH occasion 开始的监测范围”，不是固定的绝对毫秒常数。实际起止由 `ra-ResponseWindow`、PDCCH 监测时机、TDD 方向和 Release 决定；未从配置/规范读取时标 `NEEDS_VERIFICATION`。

## 22. 证据状态机（与 UE 协议状态分开）

协议状态描述 UE 应做什么；证据状态描述被动接收端目前**证明了什么**。建议使用以下单向升级，失败可回退到候选但不删除原始 artifact：

| evidence_state | 进入条件 | 必存字段 | 允许的下一状态 |
|---|---|---|---|
| `raw_prach` | IQ 中有捕获窗口 | `capture_id`、样点范围、同步版本 | `ro_resolved` / `rejected` |
| `ro_resolved` | RO 时频坐标与配置一致 | `frame/slot/symbol/f_id`、配置哈希 | `ra_rnti_computed` / `rejected` |
| `ra_rnti_computed` | 公式输入齐全且 Release 已标注 | 四个索引、算式版本、数值 | `rar_candidate` |
| `rar_candidate` | 在窗口内出现 RA-RNTI 假设的 PDCCH | 候选位置、LLR、CRC 结果 | `rar_matched` / `rejected` / `ambiguous` |
| `rar_matched` | PDSCH/TB-CRC 及 RAPID 与前导一致 | RAR 子 PDU、TA、grant、TC-RNTI | `msg3_pending` / `procedure_complete` |
| `msg3_pending` | grant 可解释且观测到对应 PUSCH | PUSCH 资源、DM-RS、UL-SCH 状态 | `contention_resolution` / `ambiguous` |
| `contention_resolution` | Msg4/MsgB 身份与时序条件待判 | 临时/最终 RNTI、身份字段、计时器 | `c_rnti_confirmed` / `rejected` |
| `ambiguous` | 多个候选或字段缺失 | 所有候选及缺口原因 | 只能在新证据到达后重判 |

`CRC pass` 只允许把状态推进到候选；不能跳过 `RAPID` 和资源/时序检查。状态升级应追加事件而不是覆盖早期状态。

## 23. 事件账本最小模式

每个 RA-RNTI 事件至少保存一行（JSON/YAML 均可，下面是字段约定而非已运行结果）：

| 字段 | 说明 |
|---|---|
| `event_id` | `cell/capture/frame/slot/ro_t/ro_f/preamble` 的稳定组合 |
| `release` / `spec_version` | 配置和公式使用的版本；未知时显式 `unknown` |
| `ro_context` | `s_id,t_id,f_id,ul_carrier_id,mu` 与绝对时频坐标 |
| `preamble_index` | RO 内前导索引；碰撞时保留多个候选 |
| `ra_rnti` / `msgb_rnti` | 数值、算式版本和计算状态 |
| `window` | RAR/MsgB 窗口起止及推导来源 |
| `pdcch_candidate` | CORESET、搜索空间、聚合/候选位置、CRC/LLR 摘要 |
| `rar_link` | `RAPID`、TB-CRC、匹配结果、原始 PDU 引用 |
| `quality_flags` | `cfo_unknown`、`collision_risk`、`truncated_window` 等 |
| `evidence_state` | 上表状态；不可用字段写 `NEEDS_VERIFICATION` |
| `failure_reason` | 枚举化原因，不用空字符串掩盖缺失 |

建议把 `ra_rnti` 的计算实现写成纯函数并保留输入回放：

```python
compute_ra_rnti(ro, release):
    require ro.first_symbol, ro.slot_in_frame,
            ro.freq_index, ro.ul_carrier_id
    require release is recorded
    validate domains against the selected specification
    return 1 + s_id + 14*t_id + 14*80*f_id
             + 14*80*8*ul_carrier_id
```

如果域检查失败，输出 `NEEDS_VERIFICATION`，不要截断、取模或自动替换为默认值。

## 24. 负例与最小验证用例

### 负例矩阵

| 注入/现象 | 预期状态 | 不能下的结论 |
|---|---|---|
| `preamble_index` 改变但 RO 不变 | RA-RNTI 不变，RAPID 匹配改变 | “RA-RNTI 能区分 UE” |
| `f_id` 偏一 | 计算值改变，RAR 候选应拒绝 | “PDCCH 没有 RAR” |
| NUL/SUL 标签丢失 | `ra_rnti_pending` | “两条载波可共用一个事件” |
| 只出现错误 RNTI CRC pass | `rar_candidate` 或 `ambiguous` | “RAR 已解码” |
| 同 RO 同前导双峰 | `collision_risk` | “两个峰对应两个确定 UE” |
| CFRA BFR 但套用 CBRA 公式/窗口 | `branch_mismatch` | “网络没有响应” |

### 最小验证（尚未运行）

1. **V0 纯函数**：固定一个已知 RO，逐项回放四个索引；验证公式输入、数值和序列化日志一致。
2. **V1 邻域扰动**：只改变 `s_id/t_id/f_id/ul_carrier_id` 中一个字段，确认候选只在预期上下文变化；边界域值需按锁定 Release 测试。
3. **V2 同 RO 多 RAPID**：生成两个不同前导但同一 RO，确认 RA-RNTI 相同、事件键不同，RAR 解析按 RAPID 分项。
4. **V3 4-step 合成链**：PRACH -> RA-RNTI PDCCH -> RAR PDSCH；注入错误 RAPID、TB-CRC 和窗口，分别得到独立失败原因。
5. **V4 2-step 分支**：使用同一 RO 计算 RA-RNTI 与 MSGB-RNTI，验证只用正确响应 RNTI 才进入 MsgB 解析；字段/偏移按目标 Release 外部核验。

## 25. 证据账本与缺口

- `STANDARD + verified (Release 17 snapshot)`：ETSI [TS 38.321 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf)，§5.1.3/§5.1.3a 的 RA-RNTI、MSGB-RNTI 和索引定义；正式项目需锁定自己的版本。
- `STANDARD + partial`：[[3GPP TS 38.213｜Physical layer procedures for control]]，§8 的物理随机接入和响应监测边界；本地笔记未覆盖全部 Release 表格。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]，PRACH 物理资源/符号接口。
- `PERSONAL_NOTE`：[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]] 的事件键与关联置信度约定。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页的 V0--V4 仅为最小验证设计，当前未记录真实设备或 MATLAB 运行结果。
- `NEEDS_EXTERNAL_REFERENCE`：项目网络的 Release、SUL/多载波启用状态、2-step/CFRA/BFR 分支、RAR 窗口实际 PDCCH 监测时机和专用配置；不能由本地 seed 笔记补齐。
