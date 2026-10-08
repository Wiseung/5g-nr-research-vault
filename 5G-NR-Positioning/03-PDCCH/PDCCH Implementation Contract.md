---
title: PDCCH Implementation Contract
aliases:
  - PDCCH 实现契约
  - PDCCH 候选级数据契约
type: implementation-contract
status: seed
created: 2026-09-05
tags:
  - domain/5g-nr
  - channel/pdcch
  - topic/implementation
  - topic/用户关联
  - evidence/personal-note
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TS 38.214
  - 3GPP TS 38.331
  - 用户项目流程说明
related:
  - "[[03-PDCCH/PDCCH Overview|PDCCH Overview]]"
  - "[[03-PDCCH/CORESET|CORESET]]"
  - "[[03-PDCCH/Search Space|Search Space]]"
  - "[[03-PDCCH/CCE REG|CCE REG]]"
  - "[[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]"
  - "[[03-PDCCH/DCI|DCI]]"
  - "[[03-PDCCH/RNTI|RNTI]]"
---

# PDCCH Implementation Contract

> [!abstract] 目录级约定
> 本页提出 `CORESET -> Search Space -> CCE/REG/RE -> PDCCH blind decoding -> DCI/RNTI -> PDSCH/PUSCH` 的候选级数据契约，供后续实现与实验逐步验证。`status: seed` 表示这是设计草案，不代表当前代码已经遵循；它不是某一 Release 的合规证明，未锁定版本的数值、表格和字段继续标记 `NEEDS_EXTERNAL_REFERENCE`。

## 1. 适用范围与证据边界

本契约只覆盖 PDCCH 候选从配置到控制判决的路径，以及它向定位支路交付的资源/时序证据。它不把以下对象混为一谈：

| 对象 | 所属层 | 本契约的处理 | 不应推出的结论 |
|---|---|---|---|
| RRC/SIB 配置 | 配置层 | 版本化保存 CORESET、Search Space、BWP 和 TDD 输入 | 不能从一次 IQ 峰反推完整配置 |
| CCE/REG/RE | 物理资源层 | 保存显式索引和逆映射 | 不能从资源坐标推断 RNTI |
| DCI | 控制信息层 | 按格式和字段规则解析 | 不能把 DCI 当作业务明文 |
| RNTI | 协议上下文层 | 作为 CRC 掩码假设和关联状态 | 不能把 C-RNTI 当作永久用户身份 |
| ToA/TDoA | 观测层 | 接收有效资源和时间基准 | 不能用下行 PDCCH 单独声称 UE 上行定位 |

本页的 `STANDARD + partial` 表示本地标准笔记已经确认职责边界；`EXPERIMENT + NEEDS_VERIFICATION` 表示尚无现场运行结果。具体 Release、条款、表值和工具箱签名未确认时，不在代码或笔记中静默填默认值。

## 2. 端到端所有权图

```text
RRC/SIB/MAC snapshot
        |
        v
CORESET ----> Search Space ----> monitoring occasions
   |                                  |
   v                                  v
REG/CCE/RE mapping ------------> candidate list
                                      |
                                      v
                         DM-RS -> channel estimate -> equalize
                                      |
                                      v
                         LLR -> inverse rate match -> Polar
                                      |
                                      v
                         CRC/RNTI -> DCI format/field checks
                                      |
                                      v
                    resource_snapshot + coding_snapshot
                           |                         |
                           v                         v
                     PDSCH/PUSCH             timing/positioning
```

每个箭头都应有可保存的中间 artifact。最终位置或最终 BLER 不能替代缺失的候选索引、LLR、CRC 和配置快照。

## 3. 配置快照

配置快照是所有候选记录的父版本；RRC/BWP/TDD 发生变化时必须生成新的 `config_id`，不能原地覆盖旧配置。

```js
config_id: ""
release_or_spec_version: "unknown"
cell_id: null
carrier:
  ncellid: null
  scs_hz: null
  bandwidth_hz: null
  point_a: null
bwp:
  id: null
  start_prb: null
  size_prb: null
coresets: []
search_spaces: []
tdd_pattern: "unknown"
fft_cp_sample_rate: "unknown"
source_artifacts: []
effective_from: ""
effective_until: ""
verification_state: "ready|partial|NEEDS_VERIFICATION"
```

字段的单位、索引基准和坐标域要与快照一同保存。`null` 表示未知，不表示零；`unknown` 表示尚未判定，不表示没有该配置。

## 4. 候选记录

候选记录是盲译码器唯一允许消费的物理输入之一。候选之外的资源不应被记为“解码失败”。

```js
candidate_id: ""
event_id: ""
config_id: ""
frame: null
slot: null
monitoring_occasion: ""
coreset_id: null
search_space_id: null
common_or_ue_specific: "common|ue_specific|unknown"
aggregation_level: null
candidate_index: null
first_cce: null
cce_indices: []
reg_indices: []
re_indices:
  dmrs: []
  control: []
  reserved: []
rnti_hypothesis:
  type: "unknown"
  value: null
  source: ""
dci_hypotheses: []
dmrs_quality: null
noise_variance: null
llr_shape: ""
llr_convention: "unknown"
polar_lengths:
  A: null
  K: null
  N: null
  E: null
state: ""
failure_reason: ""
compute_time_us: null
```

候选记录一旦写入不得被后续阶段改写；状态升级应追加判决事件，原始索引、LLR 摘要和失败原因保持可追溯。

## 5. DCI 与资源快照

```js
dci_record:
  candidate_id: ""
  rnti_type: ""
  rnti_value: null
  dci_format: ""
  payload_length: null
  payload_bits_ref: ""
  crc_state: "fail|pass"
  field_valid: false
  missing_fields: []
resource_snapshot:
  direction: "DL|UL|unknown"
  control_frame: null
  control_slot: null
  data_frame: null
  data_slot: null
  bwp_id: null
  prb_indices_local: []
  prb_indices_absolute: []
  symbol_indices: []
  layer_count: null
  dmrs_config_ref: ""
  ptrs_config_ref: ""
coding_snapshot:
  mcs_index: null
  modulation_order: null
  tbs: null
  rv: null
  ndi: null
  harq_process: null
  E: null
snapshot_state: "complete|partial|rejected"
```

`resource_snapshot` 描述“在哪里”，`coding_snapshot` 描述“用什么编码/重传状态”。两者必须共享 `event_id` 和 `config_id`，但不能用缺失字段的默认值伪造完整快照。

## 6. 候选状态机

```text
not_monitored
    └─(occasion 命中)→ occasion_open
occasion_open
    └─(候选生成)→ candidate_generated
candidate_generated
    ├─(越界/重叠/方向非法)→ invalid_candidate
    ├─(无可用观测)→ not_present
    └─(资源合法)→ dmrs_checked
dmrs_checked
    ├─(参考质量不足)→ dmrs_fail
    └─(质量可用)→ decoded
decoded
    ├─(Polar/LLR 失败)→ decode_fail
    └─(得到候选比特)→ crc_checked
crc_checked
    ├─(CRC/RNTI 失败)→ crc_fail
    └─(CRC/RNTI 通过)→ crc_pass
crc_pass
    ├─(格式/字段/资源不合法)→ field_invalid
    └─(全部约束满足)→ valid_dci
valid_dci
    ├─(用户证据不足)→ candidate_only
    └─(跨时隙/协议证据一致)→ associated
```

`not_monitored`、`not_present`、`decode_fail`、`crc_fail` 和 `field_invalid` 必须分开计数。`crc_pass` 只是证据，不是最终接受状态。

## 7. 参考伪代码

```python
for occasion in monitoring_occasions(config, frame_window):
    if not occasion.is_valid:
        emit(not_monitored, reason=occasion.reason)
        continue

    candidates = enumerate_candidates(occasion, config, rnti_context)
    for candidate in candidates:
        record = new_candidate_record(candidate, config)
        if not bounds_ok(record) or not masks_disjoint(record):
            record.state = invalid_candidate
            emit(record)
            continue
        if not tdd_direction_allows(record):
            record.state = invalid_candidate
            record.failure_reason = direction_not_allowed
            emit(record)
            continue

        obs = extract_re(grid_or_iq, record.re_indices)
        dmrs = estimate_from_dmrs(obs, record)
        if not dmrs.usable:
            record.state = dmrs_fail
            emit(record)
            continue

        llr = equalize_and_soft_demod(obs, dmrs, convention)
        for dci_hypothesis in dci_hypotheses(record):
            decoded = inverse_rate_match_and_polar(llr, dci_hypothesis)
            result = check_crc_and_fields(decoded, record, dci_hypothesis)
            emit(result)
            if result.state == valid_dci:
                emit(build_snapshots(result, config))
```

伪代码只表达责任顺序，不替代 38.211/38.212/38.213/38.214 的规范算法；函数签名和数值参数仍需目标 Release/工具箱核验。

## 8. 不变量与最小断言

1. **索引闭合**：`candidate -> CCE -> REG -> RE` 可以正向生成，也可以逆向恢复；任何一层丢失都标 `mapping_incomplete`。
2. **边界合法**：所有 CCE、REG、RE 均落在对应 CORESET/BWP/slot 资源域内，不静默裁剪。
3. **掩码互斥**：DM-RS、控制数据和保留 RE 的交集为空；若标准允许复用，必须保存覆盖优先级。
4. **长度守恒**：保存 `A/K/N/E` 和 LLR 长度；不能把 `E` 当作母码长度 `N`。
5. **时间闭合**：控制 slot 与被调度数据 slot 分开保存，K0/K1 或等效时序字段不能丢失。
6. **证据单向升级**：新证据追加状态，不删除早期候选和拒绝记录。

## 9. 故障注入与定位

| 注入 | 预期首个失败层 | 必须保留的证据 |
|---|---|---|
| CORESET 位图偏一 | mapping | 位图、局部/绝对 PRB、越界计数 |
| Search Space 周期偏一 | occasion | frame/slot、周期/偏移、未监测记录 |
| CCE-to-REG 置换错 | mapping/DM-RS | 正向/逆向置换表、掩码差异 |
| DM-RS 端口或序列错 | dmrs | 参考相关、估计矩阵、端口配置 |
| LLR 符号或尺度错 | decode | 噪声方差、LLR 摘要、K/N/E |
| RNTI 假设错 | crc | RNTI 类型/值/来源、CRC 状态 |
| DCI 位偏移错 | field | payload、格式假设、字段错误名 |
| K0/PRB/符号错 | resource | control/data slot、两份 snapshot |

## 10. 定位支路边界

PDCCH 是下行控制参考。它可以帮助建立小区、时频和调度上下文，也可以作为候选质量的辅助观测；但它不是 UE 上行 TDOA 的直接主观测。定位支路至少要收到：

- `event_id`、C-RNTI/RNTI 证据状态和有效 DCI 的候选坐标；
- 被调度上行资源（通常是 PUSCH/DM-RS/SRS 或项目明确的参考片段）；
- 原始采样起点、采样率、站点时钟和 RF/滤波群时延校准 ID；
- `toa_raw`、`toa_calibrated`、质量标志和不确定度，而不是一个无来源的时间数。

## 11. 证据与当前状态

- `STANDARD + verified-reference`：本地 [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]]、[[02-标准与参考/3GPP/3GPP TS 38.212｜Multiplexing and channel coding|TS 38.212]]、[[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|TS 38.213]]、[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data|TS 38.214]] 摘要，以及目录页引用的 Rel-17 V17.8.0 参考文本。
- `PERSONAL_NOTE`：本项目的 C-RNTI -> PDCCH -> DCI -> PDSCH/PUSCH -> 定位主线。
- `EXPERIMENT + NEEDS_VERIFICATION`：本契约没有现场候选、LLR、CRC 或定位结果。
- `NEEDS_EXTERNAL_REFERENCE`：目标 Release 的精确候选公式、字段位宽、表值、API 签名和一致性测试向量。

## 12. 待实验验证

- [ ] P0：用一份已知 BWP/CORESET/Search Space 快照重建配置和 monitoring occasion。
- [ ] P1：在无噪声单候选下逐项比对 CCE/REG/RE 正向与逆向索引、DM-RS/控制掩码和 LLR 长度。
- [ ] P2：使用正确/错误 RNTI、DCI format 和候选位置，确认 `crc_pass`、`field_invalid`、`valid_dci` 可区分。
- [ ] P3：用有效 DCI 生成 PDSCH/PUSCH `resource_snapshot`/`coding_snapshot`，与发送端真值逐字段比较。
- [ ] P4：加入 AWGN、CFO、多径和配置切换，记录分层失败、P95/P99 延迟和缓存失效行为。
- [ ] P5：接入 RA 驱动的有限 C-RNTI 池和上行参考，验证跨时隙关联及定位时间基准。

## 13. Related Notes

- [[03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[03-PDCCH/CORESET|CORESET]]
- [[03-PDCCH/Search Space|Search Space]]
- [[03-PDCCH/CCE REG|CCE REG]]
- [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
- [[03-PDCCH/DCI|DCI]]
- [[03-PDCCH/RNTI|RNTI]]
- [[04-PDSCH/PDSCH|PDSCH]]
- [[05-定位观测量/Timing Observation|Timing Observation]]
