---
title: Observation Event Schema
aliases:
  - 定位观测事件数据契约
  - NR 观测量事件 Schema
type: implementation-contract
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/measurement
  - topic/data-contract
  - stage/implementation
source:
  - "[[5G-NR-Positioning/01-NR基础/README]]"
  - "[[5G-NR-Positioning/02-PRACH/Timing Estimation]]"
  - "[[01-专题知识/5G定位/第三方 5G 定位项目接手与数据契约]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
related:
  - "[[05-定位观测量/Observation Taxonomy]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[04-PDSCH/UE Resource Extraction]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[06-TDOA定位/TDOA]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
---

# Observation Event Schema

> [!abstract] 契约边界
> 本页定义项目内部的观测事件结构，不是 3GPP ASN.1、LPP 或 NRPPa 消息格式。它的目标是让每个 ToA/CFO/功率/角度候选都能回到原始 IQ、配置、算法和校准，并让多站融合知道哪些值可以比较、哪些值只能诊断。

## 1. 设计原则

1. **不可变输入，追加式输出**：原始 IQ、原始时间戳和原始峰轨迹不被校正结果覆盖。
2. **上下文先于数值**：没有 signal/resource/time context 的数字不能进入融合。
3. **状态与数值分离**：一个值存在不代表它有效；状态必须独立记录。
4. **缺失不等于零**：未知、未估计、未校准和不适用用不同状态表达。
5. **版本可回放**：schema、config、calibration 和算法版本都要显式化。
6. **站间可关联**：同一 event_id 允许多个 station_observation，但不能凭时间最近强行合并。

## 2. 实体层级和基数

~~~text
capture (1)
  ├─ config_snapshot (1..n, 按配置切换分段)
  │    └─ event (0..n)
  │         ├─ raw_feature (0..n)
  │         ├─ station_observation (0..n)
  │         ├─ calibration_snapshot (0..n)
  │         └─ solution (0..n)
  └─ processing_run (1..n)
~~~

| 实体 | 唯一键 | 说明 | 是否可覆盖 |
| --- | --- | --- | --- |
| capture | capture_id | 原始文件或连续采集段 | 否 |
| config_snapshot | config_id | 解释 IQ 的时频/方向/资源配置 | 否，切换即新版本 |
| event | event_id | 同一物理事件的候选关联 | 只追加关联证据 |
| raw_feature | feature_id | 峰、轨迹、FFT 或 RE 引用 | 否 |
| station_observation | observation_id | 单站、单信号、单估计器输出 | 否 |
| calibration_snapshot | calibration_id | 站点时钟/RF/数字/阵列校准 | 否 |
| solution | solution_id | TDOA/位置/残差派生结果 | 否 |
| processing_run | run_id | 软件、参数和输入快照的组合 | 否 |

## 3. ID 和关联键

### 3.1 事件身份

event_id 表示“当前证据下认为可能是同一个物理事件”的键，不自动等同于 UE 身份。建议用以下证据分层：

| 级别 | 最小证据 | 允许的状态 |
| --- | --- | --- |
| candidate | 时间邻近或单个峰 | observation_candidate |
| resource_matched | 同一 cell/carrier/RO 或资源快照 | resource_matched |
| user_associated | C-RNTI/临时标识和跨消息时序闭合 | user_associated |
| cross_station_matched | 多站参考、资源和峰轨迹一致 | cross_station_matched |
| tdoa_usable | 校准、质量、协方差和几何门通过 | tdoa_usable |

同一个 event_id 可以有多个估计器结果和多个峰策略结果；不要用一个字段把这些候选压成单一真值。

### 3.2 多站关联

跨站合并至少检查：

- cell_id、carrier_id 和 config_id 是否兼容；
- frame/slot/symbol 或 RO/序列上下文是否一致；
- signal.kind、参考序列和资源掩码是否一致；
- 事件间隔是否符合该信号的时序约束；
- 是否存在碰撞、重传、MU-MIMO 或 NLOS 标记；
- 各站时间戳、采样率和校准有效期是否覆盖事件。

任何一项不满足时，可保留独立 observation，但 association_state 应为 ambiguous 或 rejected。

## 4. 推荐的通用封装

以下 YAML 是项目内部最小可扩展封装。没有的字段保留 null 或 unknown；枚举值需要在代码中校验。

~~~json
schema_name: nr_positioning_observation
schema_version: "0.2"
record_type: station_observation
observation_id: null
event_id: null
capture_id: null
processing:
  run_id: null
  algorithm_name: null
  algorithm_version: null
  parameter_hash: null
  created_at: null
context:
  cell_id: null
  carrier_id: null
  direction: null # UL, DL, flexible or unknown
  signal_kind: null # PRACH, PUSCH_DMRS, SRS, PDSCH_DMRS, PDCCH_DMRS, CSI_RS, PRS or UNKNOWN
  payload_or_role: null # reference, control, data, access or unknown
  station_id: null
  config_id: null
  resource_snapshot_id: null
  c_rnti_state: null # none, candidate, temporary, confirmed or unknown
  association_state: null # candidate, resource_matched, user_associated, cross_station_matched, ambiguous or rejected
coordinate:
  frame: null
  subframe: null
  slot: null
  symbol: null
  subcarrier_start: null
  subcarrier_count: null
  reference_point: null # capture_start, ro_start, sequence_start, fft_window_start, external_timebase or unknown
  index_base: null # zero_based, one_based or unknown
  local_or_absolute: null # local, absolute, both or unknown
  sample_rate_hz: null
  capture_sample_start: null
  capture_sample_end: null
feature:
  raw_iq_uri: null
  raw_trace_uri: null
  template_id: null
  peak_index_integer: null
  fractional_samples: null
  fractional_method: null # none, parabolic, template_fit, phase_slope or unknown
  peak_policy: null # strongest, first_detected, cluster or unknown
  peak_power_linear: null
  peak_width_samples: null
  pslr_db: null
  path_count_lower_bound: null
time:
  toa_raw_seconds: null
  toa_corrected_seconds: null
  rtoa_seconds: null
  tdoa_seconds: null
  reference_station_id: null
  correction_status: null # none, partial, complete or unknown
frequency:
  cfo_hz: null
  residual_cfo_hz: null
  sample_rate_offset_ppm: null
  doppler_candidate_hz: null
power:
  signal_power_linear: null
  noise_power_linear: null
  signal_db: null
  noise_db: null
  snr_db: null
  sinr_db: null
  power_reference: null # adc, rf_calibrated, re or unknown
spatial:
  antenna_count: null
  beam_id: null
  phase_difference_rad: null
  aoa_candidate_rad: null
  coordinate_frame: null
calibration:
  calibration_id: null
  clock_bias_seconds: null
  rf_delay_seconds: null
  cable_delay_seconds: null
  filter_group_delay_seconds: null
  digital_delay_seconds: null
  calibration_valid_from: null
  calibration_valid_to: null
quality:
  grade: null # A, B, C, invalid or unknown
  state: null # feature_only, toa_pending, reference_unknown, toa_valid, calibrated_pending, tdoa_usable, rejected or unknown
  uncertainty_std_seconds: null
  covariance_uri: null
  residual_metric: null
  reasons: []
provenance:
  source_kind: null # STANDARD, PERSONAL_NOTE, RESEARCH, EXPERIMENT or HYPOTHESIS
  evidence_status: null # verified, partial, NEEDS_VERIFICATION, NEEDS_EXTERNAL_REFERENCE or TODO
  standard_release: null
  source_note_paths: []
~~~

这份封装故意同时保留 raw 和 corrected 字段。只有 correction_status=complete 且 quality.state 通过门控时，才可把 corrected 值交给 TDOA；否则应保留 raw 值并说明缺口。

## 5. 字段字典

### 5.1 上下文和资源

| 字段 | 类型/单位 | 约束 |
| --- | --- | --- |
| capture_id | 字符串 | 必须能定位原始文件、通道和完整性记录 |
| config_id | 字符串 | 绑定 numerology、SCS、FFT/CP、BWP、TDD 和资源解释 |
| resource_snapshot_id | 字符串 | 绑定 PRB/RE、端口/层、参考信号和生成版本 |
| signal_kind | 枚举 | 必须和 direction、resource snapshot 一致 |
| c_rnti_state | 枚举 | 不能由 PRACH 峰单独置为 confirmed |
| association_state | 枚举 | 与证据级别分开保存，不等于时间质量 |

### 5.2 坐标和时间

| 字段 | 类型/单位 | 约束 |
| --- | --- | --- |
| reference_point | 枚举 | 未知时不允许标记 toa_valid |
| sample_rate_hz | Hz | 必须是当前处理链实际采样率 |
| capture_sample_start/end | 样点 | 明确左闭右开或其他边界约定 |
| peak_index_integer | 样点 | 保存相关轨迹局部索引 |
| fractional_samples | 样点 | 与 fractional_method 成对出现 |
| toa_raw_seconds | 秒 | 由样点和参考点计算，未经硬件/群时延校正 |
| toa_corrected_seconds | 秒 | 无完整校正时保持 null |
| tdoa_seconds | 秒 | 只对同一 event_id 和 reference_station_id 定义 |

### 5.3 质量和证据

| 字段 | 类型/单位 | 约束 |
| --- | --- | --- |
| grade | A/B/C/invalid/unknown | 项目质量等级，不是 3GPP 合规等级 |
| uncertainty_std_seconds | 秒 | 必须说明估计方法和真值/重复试验来源 |
| covariance_uri | 外部引用 | 多站差分优先保存完整协方差 |
| reasons | 字符串数组 | 记录每个降级或拒绝原因 |
| source_kind | 证据枚举 | 说明来源，不把假设写成标准事实 |
| evidence_status | 状态枚举 | 与运行是否完成分开 |

## 6. 状态机

~~~text
recorded
  ↓
feature_only
  ↓ (资源、参考和窗口闭合)
toa_pending
  ├─ 峰/拟合失败 → rejected
  ├─ 参考未知 → reference_unknown
  └─ 时间估计通过 → toa_valid_candidate
                         ↓ (校准存在且在有效期)
                    calibrated_pending
                         ↓ (跨站关联、协方差和几何通过)
                    tdoa_usable
~~~

状态转移必须追加处理记录，不修改历史状态。建议为每次转移保存：

- 输入 observation_id 和 run_id；
- 原状态、目标状态和时间；
- 触发规则版本；
- 通过/失败的字段；
- 操作者或自动化组件标识。

toa_valid_candidate 只是单站候选，不代表已经可以进入多站解算。tdoa_usable 也不等于位置一定正确，它只表示满足当前项目输入门。

## 7. 空值、枚举和版本规则

| 情况 | 推荐表达 | 禁止表达 |
| --- | --- | --- |
| 尚未估计 | null + state=toa_pending | 0 |
| 不适用 | null + reason=not_applicable | 借用别的字段 |
| 参考未知 | null + state=reference_unknown | 假定 capture_start |
| 校准缺失 | corrected=null + correction_status=partial/unknown | corrected=raw |
| 估计失败 | raw 可保留 + state=rejected | 删除失败记录 |
| 标准未核验 | evidence_status=NEEDS_EXTERNAL_REFERENCE | 写 verified |
| 字段升级 | 增加 schema_version 并保留旧字段 | 静默改含义 |

枚举值应集中定义在代码或配置中，文档中的竖线表示候选集合，不是要写入一个未拆分的字符串。

## 8. 多站观测和协方差接口

给定同一 event_id 的 ToA 向量 tau 和参考差分矩阵 D：

$$
\boldsymbol{\Delta\tau}=\mathbf D\boldsymbol{\tau},
\qquad
\mathbf\Sigma_\Delta
=\mathbf D\mathbf\Sigma_\tau\mathbf D^{T}.
$$

schema 至少要能引用：

- ToA 向量的站点顺序；
- reference_station_id；
- D 矩阵或等价 pair 列表；
- 原始 ToA 协方差；
- 被剔除站点及原因；
- 校准版本和有效时间。

如果只保存 pairwise tdoa_seconds 而不保存站点顺序、参考站和协方差，下游很难判断差分是否共享误差。

## 9. 事件关联规则

建议按由强到弱的顺序打分，但保留每项证据：

1. 同一 cell/carrier/config；
2. 同一方向和合法时隙/符号；
3. 同一 RO、参考序列或资源掩码；
4. 相容的 C-RNTI/临时标识状态；
5. 峰簇时间、频率和功率关系；
6. 跨站校准后时间差落在几何可行范围；
7. 重复观测、DM-RS/SRS 结构和解码结果一致。

任何“最近邻配对”都必须把候选集合、门限和被拒绝的替代配对写入关联日志。PRACH 碰撞、PUSCH 重传和 MU-MIMO 不能用 event_id 的字符串格式自动消除。

## 10. 示例：可用与降级记录

### 10.1 单站、尚未校准

~~~json
schema_name: nr_positioning_observation
schema_version: "0.2"
record_type: station_observation
observation_id: obs-001
event_id: evt-001
capture_id: cap-001
context:
  signal_kind: PRACH
  direction: UL
  station_id: station-a
  config_id: cfg-unknown
  association_state: candidate
coordinate:
  reference_point: ro_start
  sample_rate_hz: null
feature:
  peak_index_integer: 1432
  fractional_samples: null
  peak_policy: strongest
time:
  toa_raw_seconds: null
  toa_corrected_seconds: null
  correction_status: unknown
quality:
  grade: C
  state: calibrated_pending
  reasons:
    - sample_rate_unknown
    - hardware_calibration_missing
provenance:
  source_kind: EXPERIMENT
  evidence_status: NEEDS_VERIFICATION
~~~

### 10.2 多站、可送入 TDOA 候选

~~~json
schema_name: nr_positioning_observation
schema_version: "0.2"
record_type: station_observation
observation_id: obs-101
event_id: evt-101
capture_id: cap-101
context:
  signal_kind: PUSCH_DMRS
  direction: UL
  station_id: station-b
  config_id: cfg-101
  resource_snapshot_id: res-101
  association_state: cross_station_matched
coordinate:
  reference_point: sequence_start
  sample_rate_hz: null
time:
  toa_raw_seconds: null
  toa_corrected_seconds: null
  rtoa_seconds: null
frequency:
  cfo_hz: null
calibration:
  calibration_id: cal-101
  clock_bias_seconds: null
quality:
  grade: unknown
  state: calibrated_pending
  uncertainty_std_seconds: null
  reasons:
    - placeholder_until_run
provenance:
  source_kind: EXPERIMENT
  evidence_status: NEEDS_VERIFICATION
~~~

第二个示例只展示结构，不声称已有运行结果；在真实运行前，quality.state 应由规则引擎生成，而不是手工填写。

## 11. 机器校验清单

- [ ] 每个 observation_id 全局唯一且不可复用。
- [ ] event_id、capture_id、config_id、station_id 能在对应索引中解析。
- [ ] signal_kind 与 direction、resource_snapshot 和上游检测状态一致。
- [ ] sample_rate_hz、reference_point、index_base 和边界约定齐全。
- [ ] fractional_samples 与 fractional_method 同时为空或同时有值。
- [ ] toa_corrected_seconds 非空时，correction_status=complete 且 calibration_id 有效。
- [ ] tdoa_seconds 非空时，reference_station_id、event_id 和站点顺序齐全。
- [ ] quality.state=tdoa_usable 时不存在未解决的 calibration_missing、clock_unreliable 或 reference_unknown。
- [ ] source_kind/evidence_status 不把设计模板写成实验结果。
- [ ] 所有 URI、哈希和外部文件引用可回读；失败也保留记录。

## 12. 证据与限制

- PERSONAL_NOTE：字段层级、关联键和状态机是本项目内部工程契约，来源于既有交接、资源提取和多站笔记。
- STANDARD + partial：资源网格、物理信道/参考信号角色和数据参数边界参考 TS 38.211/38.214；本 schema 不替代规范字段。
- EXPERIMENT + NEEDS_VERIFICATION：示例、质量门、阈值和运行状态均需真实代码/采集验证。
- NEEDS_EXTERNAL_REFERENCE：38.215/38.305 的标准测量报告字段、精确参考点和 Release 差异。

## 13. Related Notes

- [[05-定位观测量/Observation Taxonomy]]
- [[05-定位观测量/Standard Positioning Observables]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[02-PRACH/Timing Estimation]]
- [[04-PDSCH/UE Resource Extraction]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[06-TDOA定位/TDOA]]
- [[09-采数实验/Capture Experiment Checklist]]
