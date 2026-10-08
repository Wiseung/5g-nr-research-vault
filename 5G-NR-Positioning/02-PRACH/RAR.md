---
title: RAR
aliases:
  - Random Access Response
  - 随机接入响应
  - Msg2
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/random-access
  - channel/pdsch
  - topic/mac
  - stage/user-association
source:
  - 3GPP TS 38.321
  - 3GPP TS 38.213
  - 3GPP TS 38.214
related:
  - "[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]"
  - "[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]"
  - "[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]"
  - "[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]"
  - "[[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]"
---

# RAR

## 1. 一句话定义

RAR（Random Access Response）是网络在 Msg2 中发送的 MAC 响应，通常包含与 RAPID 匹配的 Timing Advance、UL grant 和 Temporary C-RNTI。

## 2. 为什么项目需要它

RAR 是从 PRACH 物理事件走向可调度 UE 上行和临时标识的关键证据；没有 RAR，不能把前导可靠升级为 C-RNTI 候选。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 RA-RNTI 寻址的 PDCCH/PDSCH 之后、Msg3 之前：PDCCH 给出 PDSCH 资源，PDSCH 解码得到 RAR MAC PDU，再由 UL grant 定位 Msg3。

## 4. 输入

- RO/RA-RNTI 和 RAR window。
- RA-RNTI 寻址的 PDCCH/DCI、PDSCH 资源、DM-RS 和编码参数。
- 解码后的 MAC PDU 比特及其 RAPID 子 PDU。

## 5. 输出

- RAPID 与 preamble index 的匹配结果。
- Timing Advance、UL grant、Temporary C-RNTI、backoff/竞争相关字段（若存在）。
- Msg3 资源快照、关联状态和 MAC/PHY 失败原因。

## 6. 关键参数

RAR window、RA-RNTI、RAPID、TA 命令位宽/解释、UL grant 字段、Temporary C-RNTI、MAC PDU 子头和填充、PDSCH MCS/TBS/RV。字段长度和位序必须按 TS 38.321 版本解析。

## 7. 时域位置

RAR 在对应 RO 后的响应窗口内下行发送；同一 MAC PDU 可包含多个 RAPID 响应。TA 命令影响后续 Msg3 的上行时序，但不改写已测 PRACH ToA。

## 8. 频域位置

RAR 的 PDSCH 频域资源由 RA-RNTI 掩码的 PDCCH DCI 调度，可能位于公共搜索空间/BWP；应保存 CORESET、搜索空间、PRB、符号和 BWP 坐标。

## 9. 数学原理

可把 RAR 匹配写成约束集合

$$
\mathcal{A}_{RAR}=\{(RO,p):\mathrm{RAPID}(p)=\mathrm{preamble\_index}(RO)\}.
$$

只有 PDCCH CRC、PDSCH/TB-CRC、RAPID、资源时序和字段范围同时成立，才接受一个 RAR。单独的 CRC pass 或单独的 TA 数值不足以建立关联。

## 10. 3GPP 对应规范

- TS 38.321 §5.1.4：Random Access Response；§6.2.3：RAR MAC PDU/子 PDU 格式；具体版本待核。
- TS 38.213 §8.2/§8.2A：RAR 物理响应时机。
- TS 38.214：PDSCH 资源、MCS/TBS/RV 的解释。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPDCCHSpace、nrPDCCHDecode：寻找和解码 RA-RNTI 寻址的 PDCCH。
- nrPDSCHIndices、nrPDSCHDMRSIndices、nrPDSCHDecode、nrDLSCHDecoder：恢复 PDSCH 软比特和 TB。
- RAR MAC PDU 子头/字段没有本地一键 API，应实现版本化解析器；所有 API 输入维度标记 NEEDS_EXTERNAL_REFERENCE。

## 12. 本项目中的用途

按 RA-RNTI 搜索 RAR，验证 RAPID 与前导一一匹配，保存 TA/UL grant/Temporary C-RNTI，再驱动 [[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]；只有后续争用解决成功，才将标识升级到 [[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。

## 13. 常见误区

- 把 RAR 的 Temporary C-RNTI 直接当最终 C-RNTI。
- 只解一个 RAR 子 PDU，忽略同一 MAC PDU 的多个 RAPID。
- 把 TA 命令当接收 ToA 或传播距离。
- PDCCH CRC 通过后不验证 PDSCH/TB-CRC 和 MAC 字段。

## 14. 与相似概念的区别

RAR 是 MAC 响应消息；RA-RNTI 是其 PDCCH 寻址掩码；RAPID 是其中匹配前导的子字段；Temporary C-RNTI 是过程中的临时标识；Msg3 是 RAR grant 指向的后续 PUSCH。

## 15. 代码实现注意事项

- 先保存 PDCCH/PDSCH 的候选级原始软信息，再解析 MAC。
- 采用位级解析并记录端序、子头长度和版本。
- 将 RAPID 匹配、TB-CRC、字段范围和时序判决分开记录。
- RAR 解码失败不能回写成 PRACH 检测失败。

## 16. 待实验验证的问题

- 现场能否捕获公共搜索空间中的 RA-RNTI PDCCH 和完整 RAR PDSCH。
- 当前设备是否可见 MAC 字段、是否有加密/丢包遮挡。
- 多 RAPID、RAR 重传和不同 MCS 下的解析鲁棒性。
- TA/UL grant 与后续 Msg3 资源命中率。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。
- 后续数据：[[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]、[[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]。
- 旧笔记：[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]、[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|现有控制/数据主线]]。

## 18. RAR 的可解析层次

> [!important] 解析顺序
> RAR 不是“一个含有 TA 的字段”，而是 `RA-RNTI/MSGB-RNTI 寻址的 PDCCH -> PDSCH -> DL-SCH MAC PDU -> MAC subPDU -> RAPID/固定 payload` 多层对象。必须逐层保存成功/失败原因；PDCCH CRC 通过不能代替 PDSCH TB-CRC，也不能代替 RAPID 匹配。

### 18.1 4-step MAC RAR（Release 17 快照）

已核对 `3GPP TS 38.321 V17.8.0 (Release 17)` §6.2.2--§6.2.3 的字段如下。这里的位宽是该版本的核验结果，不应未经版本核对复制到未来 Release 或厂商私有格式。

| 层级/字段 | 位数（V17.8.0） | 语义 | 解析动作 |
|---|---:|---|---|
| MAC subheader `E` | 1 | 后面是否还有 MAC subPDU | 继续/结束子头遍历 |
| MAC subheader `T` | 1 | `0` 表示 BI，`1` 表示 RAPID | 选择子头分支 |
| MAC subheader `R` | 1 | 保留位，应为 0 | 非 0 标记 malformed |
| `BI`（若 `T=0`） | 4 | 小区过载退避指示 | 按目标版本表映射为 backoff；不猜毫秒值 |
| `RAPID`（若 `T=1`） | 6 | 随机接入前导标识 | 与 `preamble_index` 精确匹配 |
| MAC RAR `R` | 1 | 保留位，应为 0 | 非 0 标记 malformed |
| `Timing Advance Command` | 12 | TA 索引，交给 38.213 解释 | 记录原始值和 TAG/版本，不换算距离 |
| `UL Grant` | 27 | RAR 所授权的上行资源 | 交给 38.213 §8.3/38.214 解释 |
| `Temporary C-RNTI` | 16 | 随机接入期间使用的临时标识 | 进入 `temporary_rnti_pending` |

固定 RAR payload 在该版本按 7 octets 对齐（`1+12+27+16=56` bit）。子头和 payload 的端序、跨 octet 拼接必须以标准图和抓包字节序为准；表格只说明字段边界，不授权任意 bit packing。

`BI-only` 子头可以出现在 MAC PDU 开头；它不是一个没有 payload 的“空 RAR”，而是退避控制信息。一个 MAC PDU 可以包含多个 RAPID 子 PDU，接收端应遍历至 `E=0` 并保存每个子 PDU 的原始 offset。

### 18.2 2-step MsgB 的 fallbackRAR 与 successRAR

2-step RA 的 MsgB 也通过 PDCCH/PDSCH 传输，但 MAC payload 可能是两种语义不同的结构：

| 子类型 | 主要字段 | 后续动作 | 证据状态 |
|---|---|---|---|
| `fallbackRAR` | 与 MAC RAR 类似：R、TA、27-bit UL grant、16-bit Temporary C-RNTI | 命中 RAPID 后回到 Msg3 发送路径 | `STANDARD + verified snapshot`，版本仍需复核 |
| `successRAR` | UE Contention Resolution Identity、TA、C-RNTI，以及条件出现的 HARQ/PUCCH 控制字段 | 身份匹配后直接完成 2-step 过程 | `STANDARD + partial`；条件字段按 Release 核验 |

在 V17.8.0 的 `successRAR` 图中，UE Contention Resolution Identity 为 48 bit，C-RNTI 为 16 bit；还存在 TPC、PUCCH Resource Indicator、HARQ Feedback Timing Indicator，以及共享频谱场景的可选 `ChannelAccess-CPext`。这些字段不是 4-step MAC RAR 的通用字段，不能用一个固定长度解析所有 MsgB。

MsgB 的子头还引入 `T1/T2/S` 语义，用于区分 RAPID、BI 和后续 MAC SDU。若项目尚未锁定 2-step Release，应把 MsgB 解析器接口写成版本化 schema，遇到未知 eLCID/保留位时输出 `NEEDS_EXTERNAL_REFERENCE`，而不是按 4-step 偏移硬切。

## 19. RAR 解码流水线与验收门

```text
RO + preamble event
    |
    +--> derive RA-RNTI (4-step) / MSGB-RNTI (2-step)
    |
PDCCH candidate in response window
    +--> resource/CORESET/search-space check
    +--> DCI CRC masked by response RNTI
    +--> DCI field/range check
    |
PDSCH extraction
    +--> DM-RS/channel estimate/equalization
    +--> DL-SCH inverse rate matching + TB-CRC
    |
MAC PDU parser
    +--> subheader E/T/R/(BI|RAPID)
    +--> RAPID ↔ preamble_index match
    +--> RAR payload (TA, UL grant, Temporary C-RNTI)
    +--> Msg3/fallback or contention-resolution state
```

建议为每层设独立验收门：

| 门 | 成功条件 | 失败输出 |
|---|---|---|
| `R0` 响应上下文 | RO、RNTI、窗口和 PDCCH 监测时机一致 | `context_missing` |
| `R1` PDCCH | 资源和 RNTI-CRC 通过 | `pdcch_rejected` |
| `R2` PDSCH | DM-RS、资源、TB-CRC 通过 | `pdsch_decode_failed` |
| `R3` 子头 | E/T/R 和 octet 边界合法 | `malformed_subheader` |
| `R4` RAPID | 至少一个 RAPID 与本地前导匹配 | `rapid_mismatch` |
| `R5` payload | TA/grant/TC-RNTI 字段范围及长度合法 | `rar_payload_invalid` |
| `R6` 过程交接 | grant 可生成 Msg3/回退资源 | `grant_unusable` |

任何门失败都不应反写为“PRACH 未检测到”。

## 20. 字段语义与 PHY/MAC/RRC 边界

| 字段/对象 | 所属层 | 允许的解释 | 明确禁止的解释 |
|---|---|---|---|
| RA-RNTI/MSGB-RNTI | MAC 上下文 + PDCCH CRC 接口 | 选择响应候选 | UE 永久身份 |
| `RAPID` | MAC subheader | 匹配 RO 内前导索引 | 直接等于 C-RNTI |
| TA command | MAC payload，按 38.213 应用 | 调整后续 UL 发射定时 | 接收 ToA、传播距离或已校准距离 |
| UL grant | MAC payload，按 38.213/214 解释 | 生成 Msg3 PUSCH 资源与 HARQ 输入 | DCI 原始比特或任意 PUSCH 配置 |
| Temporary C-RNTI | MAC 状态 | 在争用解决前寻址 Msg3/Msg4 | 已确认的最终 C-RNTI |
| PDSCH/PUSCH RE | PHY | 提取/解调和质量测量 | MAC 字段存在性的独立证明 |
| RACH-Config* | RRC | 配置 RO、窗口、CFRA/2-step 资源 | 从 IQ 峰值反推完整配置 |

RAR PDSCH 由 38.211/38.213 的物理资源过程承载，MAC payload 格式由 38.321 规定，UL grant 的具体位解释依赖 38.213/38.214；三者不能合并为一个“RAR 解码函数”而不记录边界。

## 21. TA 与 UL grant 的后续约束

### TA

RAR 中 TA 是索引，不是以秒或米表示的测量量。网络/UE 按 38.213 的定时提前过程将其应用于对应 TAG；接收机应保存：

```js
ta_raw_index
ta_spec_version
ta_tag_id (if available)
ta_application_state = pending | applied | ignored | unknown
toa_observation_reference = RO_start | capture_start | other
```

`ta_raw_index` 与 PRACH 相关峰的 `toa_observation` 是两个不同事件。若把二者相加或互换，会在定位链中产生系统性双计数。

### UL grant

27-bit UL grant 不是普通 PDCCH DCI 0_0 的完整替代。解析时至少需要：

| 依赖 | 由谁提供 | 缺失时 |
|---|---|---|
| 初始/活动 UL BWP 大小与 SCS | RRC/38.213 | `grant_context_missing` |
| 频域资源分配规则、跳频标志 | 38.213/38.214 + BWP | 不猜 PRB |
| 时域分配、K2/处理间隔 | 38.213/38.214 | 标 `NEEDS_VERIFICATION` |
| MCS/TBS、RV、HARQ | RAR + 38.214 | 只保存原始 grant，不生成伪资源 |
| TA、TDD UL 符号和载波 | RAR + 配置 | 不能确认 PUSCH 时刻 |

## 22. 时序图：4-step RAR 与 2-step MsgB

```text
4-step (Type-1)
RO/Msg1 ────────┐
                └─> RA-RNTI PDCCH/PDSCH ──> RAR (RAPID, TA, grant, TC-RNTI)
                                                       └─> Msg3 PUSCH
                                                               └─> TC-RNTI Msg4 PDSCH

2-step (Type-2)
RO + MsgA PUSCH ─┐
                 └─> MSGB-RNTI PDCCH/PDSCH ──> fallbackRAR ─> Msg3
                                           └─> successRAR (identity + C-RNTI) ─> complete
```

窗口起点是规范定义的 PDCCH 监测时机，不是“收到 IQ 后立即开始”；跨帧、TDD、测量间隙和 BWP 切换都要进入时间账本。

## 23. 位级解析伪代码

```python
decode_rar(candidate, ro_event, release):
    assert candidate.response_rnti in {ro_event.ra_rnti, ro_event.msgb_rnti}
    if not pdcch_crc_ok(candidate, candidate.response_rnti):
        return rejected("pdcch_crc")
    if not dci_resource_valid(candidate.dci, release):
        return rejected("dci_field_or_resource")
    tb = decode_pdsch(candidate, release)
    if not tb.crc_ok:
        return rejected("pdsch_tb_crc")

    subpdus = parse_octet_aligned_subheaders(tb.mac_pdu, release)
    if subpdus.error:
        return rejected("malformed_subheader")
    matches = []
    for subpdu in subpdus:
        if subpdu.type == "BI":
            record_backoff(subpdu.bi, release)
        elif subpdu.type == "RAPID":
            if subpdu.rapid == ro_event.preamble_index:
                if subpdu.kind == "RAR":
                    payload = parse_rar_payload(subpdu.payload, release)
                    matches.append(payload)
                elif subpdu.kind in {"fallbackRAR", "successRAR"}:
                    matches.append(parse_msgb_payload(subpdu, release))
    if len(matches) == 0:
        return rejected("rapid_mismatch")
    if len(matches) > 1:
        return ambiguous("duplicate_rapid")
    return accepted(matches[0], evidence=[candidate, tb, subpdus])
```

解析器必须保留原始 MAC PDU、子头 offset、版本 schema 和每个失败门；不要只返回 `(ta, grant, tc_rnti)` 三元组。

## 24. RAR 事件账本

| 字段 | 记录要求 |
|---|---|
| `rar_event_id` | 与 `ro_event_id`、PDCCH 候选和捕获片段可互相追溯 |
| `response_rnti` | RA-RNTI 或 MSGB-RNTI、计算版本 |
| `window_position` | PDCCH monitoring occasion、帧/slot/符号 |
| `pdcch_snapshot` | CORESET/search-space、候选、聚合、LLR、CRC |
| `pdsch_snapshot` | PRB、符号、DM-RS、MCS/TBS/RV、TB-CRC |
| `mac_pdu_raw` | 原始字节/bit、端序和抓包偏移 |
| `subheader_list` | E/T/R、BI/RAPID、offset、保留位检查 |
| `rapid_match` | matched/unmatched/duplicate/unknown |
| `ta` | 原始 TA、TAG、应用状态，禁止直接换算距离 |
| `ul_grant` | 原始 27-bit（若适用）及解析 schema/资源快照 |
| `temporary_c_rnti` | 数值、来源、有效区间和下一状态 |
| `evidence_state` | `rar_candidate`/`rar_matched`/`grant_usable` 等 |
| `failure_reason` | 结构化枚举和缺失字段 |

## 25. 负例与最小验证

### 负例

| 场景 | 应发生的判决 | 不应发生的判决 |
|---|---|---|
| RA-RNTI CRC 通过、PDSCH TB-CRC 失败 | `pdsch_decode_failed` | 把 TA/TC-RNTI 设为有效 |
| TB-CRC 通过但 RAPID 不等于本地前导 | `rapid_mismatch` | 跨 RO 绑定 RAR |
| 同 PDU 两个相同 RAPID | `duplicate_rapid/ambiguous` | 任选一个 payload |
| 保留位 `R=1` 或 E 链断裂 | `malformed_subheader` | 继续按默认长度读字段 |
| 将 BI 当 RAPID | `subheader_type_error` | 生成 Msg3 grant |
| TA 原始值存在但 TAG/版本缺失 | `ta_unresolved` | 换算传播距离 |
| grant 资源超出活动 BWP | `grant_unusable` | 按截断 PRB 发送/定位 |
| 2-step successRAR 按 4-step RAR 解析 | `branch_mismatch` | 误造 Temporary C-RNTI |

### 最小验证（设计模板，尚未运行）

1. **R0 合成子头**：构造 BI-only、单 RAPID、多个 RAPID 和 padding，验证 E/T/R 分支、offset 和 octet 对齐。
2. **R1 固定 payload**：以 V17.8.0 字段图生成已知 TA/grant/TC-RNTI，逐 bit 回读；再用目标项目 Release 复核位宽。
3. **R2 协议门**：分别注入 PDCCH CRC、PDSCH TB-CRC、RAPID 错误，确认失败原因不串层。
4. **R3 grant 闭环**：将有效 grant 交给 Msg3 资源计算，检查 BWP、TDD UL、TA 和时域间隔；不填写未验证 K2。
5. **R4 MsgB 分支**：构造 fallbackRAR 与 successRAR 两条样本，验证不会互用 4-step parser，成功分支能产生下一状态。
6. **R5 丢包回放**：删除一个子 PDU 或截断 PDSCH，确认原始 `rar_candidate` 保留、状态转为 `ambiguous`/`rejected`，而非删除 PRACH 事件。

## 26. 证据账本与缺口

- `STANDARD + verified (Release 17 snapshot)`：ETSI [TS 38.321 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf)，§6.2.2、§6.2.3、§6.2.3a、§5.1.4/§5.1.4a；包含 4-step RAR、fallbackRAR、successRAR 的字段图和过程语义。
- `STANDARD + partial`：[[3GPP TS 38.213｜Physical layer procedures for control]] §8.2/§8.2A/§8.3；RAR/MsgB 窗口、UL grant 和 PUSCH 时序的完整版本表待核。
- `STANDARD + partial`：[[3GPP TS 38.214｜Physical layer procedures for data]]；MCS/TBS、PUSCH 资源和 HARQ 解释需与项目 Release 对齐。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]；PDSCH/DM-RS/资源网格属于 PHY 物理边界。
- `PERSONAL_NOTE`：[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]] 和 [[5G-NR-Positioning/02-PRACH/Msg3|Msg3]] 的事件键与交接约定。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页 R0--R5 仅为合成/回放设计，当前未记录现场 RAR MAC PDU、真实 MCS 或 MsgB 结果。
- `NEEDS_EXTERNAL_REFERENCE`：项目网络 Release、RAR window 实际边界、MAC 子头扩展/eLCID、2-step successRAR 条件字段、加密/抓包可见性；不得用 V17.8.0 快照静默覆盖。
