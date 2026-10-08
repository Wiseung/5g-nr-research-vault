---
title: Synchronization Validation Ledger
aliases:
  - 多站同步验证台账
  - 站间校准实验清单
  - 同步验收矩阵
type: experiment-protocol
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/synchronization
  - topic/calibration
  - topic/reproducibility
  - stage/verification
source:
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[07-多站协同/Clock Offset and Drift]]"
  - "[[07-多站协同/RF and Digital Delay Calibration]]"
  - "[[07-多站协同/Cross-Station Event Association]]"
  - "[[07-多站协同/Multi-Station Observation Fusion]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
related:
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[06-TDOA定位/TDOA Validation Ledger]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[03-仿真与实验/5G定位/仿真：多站 UL-TDOA 协同定位]]"
---

# Synchronization Validation Ledger

> [!warning] 实验状态
> 本页是同步与校准实验的预注册台账。所有结果单元初始为空；没有真实 IQ、运行配置、原始日志和可回放脚本时，不填写偏置、漂移、RMSE、覆盖率或位置精度。

## 1. 一句话定义

同步验证台账把“时钟是否可比、链路延迟是否已校准、事件是否能跨站关联、TDOA 输入是否闭合”拆成分层实验，并为每次运行保存配置、原始证据、指标和失败原因。

## 2. 验证目标

1. 证明站点时间戳和采样坐标可以在明确条件下比较。
2. 量化固定偏置、采样率偏差、慢漂移和重锁跳变。
3. 识别 RF/天线/线缆/数字滤波延迟及其频率依赖。
4. 验证同一事件的跨站关联不会因碰撞、重传或错配而静默升级。
5. 生成带站序、参考站和协方差的 TDOA 输入包。

这些目标是工程验收目标，不是 3GPP 合规声明。

## 3. 证据层级

| 层级 | 内容 | 可支持的结论 |
| --- | --- | --- |
| V0 元数据 | 站点、时钟源、频率、采样率、版本 | 配置是否完整 |
| V1 时基 | PPS/PTP/触发日志、锁定状态 | 时间轴事件是否可回放 |
| V2 回环 | 公共源/线缆/端口交换 | 站间固定差和重复性 |
| V3 长时 | 多时刻、温度、重锁 | 漂移和有效期候选 |
| V4 事件 | 同一 PRACH/PUSCH/SRS 的多站观测 | 关联与校正是否闭合 |
| V5 融合 | TDOA、协方差和几何前置检查 | 输入包是否可交下游 |
| V6 现场 | 真实设备和已知位置/轨迹 | 仅在配置和真值充分时支持现场结论 |

较高层级不能覆盖较低层级缺失。例如有一个现场定位坐标，不代表 V2 回环已经通过。

## 4. 场景矩阵

| 编号 | 场景 | 固定因素 | 注入/变化 | 主要出口 |
| --- | --- | --- | --- | --- |
| S0 | 配置完整性 | 站点、频率、采样率、处理链 | 无 | config_snapshot |
| S1 | 短时公共源 | 同一参考源、短窗口 | 多次重复 | 固定差、重复性 |
| S2 | 端口/线缆交换 | 同一参考源 | 交换路径和站序 | 方向/闭合残差 |
| S3 | 频率和带宽 | 同一设备链 | 频点、带宽、PRB 掩码 | 频变延迟 |
| S4 | 长时漂移 | 参考源和处理链 | 时间、温度、负载 | offset/drift 模型 |
| S5 | 重锁/断链 | 可控时基 | 失锁、恢复、重启 | 分段和降级状态 |
| S6 | 已知事件 | 三站或四站、同一波形 | PRACH/PUSCH/SRS | event_id 关联 |
| S7 | 多峰/NLOS | 事件和配置固定 | 多径、遮挡、峰策略 | 关联和质量 |
| S8 | 缺站/坏站 | 同一事件 | 删除或污染一站 | 降级和替代站集 |
| S9 | 端到端输入 | 完整校准链 | 真实/仿真事件 | bundle/TDOA 快照 |

S6-S9 与 [[06-TDOA定位/TDOA Validation Ledger]] 的 T0-T9 场景相互引用，不把两套编号混为一套结果。

## 5. 每次运行的配置快照

~~~json
run_id: null
parent_run_id: null
scenario_id: null
created_at: null
operator_or_automation: null
software_version: null
hardware_versions: []
station_ids: []
station_coordinates: null
coordinate_frame: null
reference_station_id: null
clock_sources: {}
lock_policy: null
center_frequency_hz: null
bandwidth_hz: null
sample_rates_hz: {}
ddc_profiles: {}
filter_profiles: {}
reference_planes: {}
signal_kind: null
resource_snapshot_id: null
event_association_config_id: null
calibration_ids: []
random_seed: null
input_artifacts: []
output_artifacts: []
status: planned
~~~

如果任何字段在运行时未知，写 null 并在 missing_fields 中列出；不要用默认值补齐配置快照。

## 6. 原始证据清单

- 每站原始 IQ、通道顺序、数据类型和文件边界。
- 采集起止时间、样点计数、丢样/溢出和时间戳原文。
- 时钟锁定、PPS/PTP/触发、重锁和设备重启日志。
- 参考源、线缆、功分器、衰减器和端口连接图。
- 频率、带宽、采样率、DDC、抽取、滤波和窗口配置。
- 原始相关轨迹、峰列表、峰策略、门限和模板版本。
- 校准表、calibration_id、测量时间、温度和有效期。
- 事件关联候选、被拒绝替代、最终 station_order 和 bundle。

最终图、最终坐标或汇总 CSV 不能替代以上证据。

## 7. 指标定义

### 7.1 时基指标

设公共参考事件的相对时间误差为 $e_{i,k}$：

$$
e_{i,k}
=\widehat b_{i,k}-b_{i,\mathrm{ref},k}.
$$

至少报告均值、标准差、RMSE、分位数、有效样本数和时间区间。若使用线性漂移模型，还报告斜率、拟合残差和分段边界。

### 7.2 延迟指标

记录总延迟、重复性、端口交换闭合误差、频率斜率、带宽敏感性和校准失效率。时域峰与频域相位斜率若同时使用，分别报告，不先合并成一个“真值”。

### 7.3 关联指标

| 指标 | 定义边界 |
| --- | --- |
| candidate_recall | 已知事件进入候选集合的比例 |
| false_association_rate | 错配候选被升级的比例 |
| ambiguity_rate | 多个候选无法区分的比例 |
| unmatched_rate | 没有跨站配对的比例 |
| collision_preservation | 碰撞样本仍保留多候选的比例 |
| calibration_gate_rate | 通过校准有效期门的比例 |

在没有已知真值标签时，只能报告候选数量和人工审计结果，不能虚构 recall 或 false rate。

### 7.4 融合指标

报告有效站率、协方差正定/秩检查、D 矩阵一致性、TDOA 物理门通过率、bundle 重放一致性和处理延迟。位置 RMSE 属于下游 TDOA/现场实验指标，不能由同步台账单独声称。

## 8. 建议的通过条件写法

每个场景都应把阈值写成配置，而不是散落在代码里：

~~~json
acceptance:
  residual_bias_seconds: null
  residual_std_seconds: null
  drift_ppm: null
  outlier_rate: null
  max_relock_gap_seconds: null
  association_false_rate: null
  tdoa_gate_rate: null
  threshold_source: TODO
  approved_by: TODO
~~~

阈值未由项目需求、设备规格或预注册实验确定时，保持 TODO。通过条件必须同时说明适用的频率、带宽、采样率、温度、峰策略和站点数量。

## 9. 运行记录模板

~~~json
run_id: null
scenario_id: S1
start_time: null
end_time: null
input_snapshot_ref: null
calibration_snapshot_refs: []
raw_artifact_refs: []
processing_run_ref: null
metrics:
  offset_bias_seconds: null
  offset_std_seconds: null
  drift_ppm: null
  delay_repeatability_seconds: null
  association_state_counts: {}
  valid_station_rate: null
  tdoa_gate_rate: null
  processing_latency_ms: null
failures: []
deviations_from_plan: []
status: planned
evidence_status: NEEDS_VERIFICATION
~~~

运行状态 planned/running/complete/rejected 只描述实验记录，不代表算法质量等级。

## 10. 故障定位矩阵

| 观察到的失败 | 优先检查层 | 应保留的证据 |
| --- | --- | --- |
| 偏置恒定且可重复 | 参考面/线缆/时钟零点 | 回环峰、端口图、校准表 |
| 偏置随时间线性变化 | 采样率/时钟漂移 | 长时轨迹、温度、锁定日志 |
| 重锁后突跳 | 时基分段 | 重锁事件、前后计数 |
| 只在某频点变化 | 数字滤波/RF 群时延 | 频率响应、处理链版本 |
| 单站正常、跨站错配 | 事件关联 | 候选全集和替代配对 |
| TDOA 超站间距离上界 | 符号/单位/事件/unwrap | ToA 向量、D 矩阵、单位 |
| 协方差奇异 | 重复 pair/共享参考 | 原始协方差和矩阵秩 |
| 位置解不稳定 | 几何/异常站 | GDOP、残差和站点剔除 |

失败应归档到首次出现的层，不能只在最终位置层写“定位失败”。

## 11. 回放和复现顺序

~~~text
读取 run_id 和配置快照
    -> 校验原始文件与时间戳边界
    -> 重建 clock segment 和 delay calibration
    -> 重放单站峰和 raw/corrected ToA
    -> 重放事件候选与替代配对
    -> 生成 station bundle、D 矩阵和协方差
    -> 对照原始输出的状态、数值和失败原因
~~~

回放脚本应能在没有最终位置结果的情况下复原同步和关联层；否则无法定位误差来源。

## 12. 与其他台账的映射

| 本页场景 | 对应页面 | 关系 |
| --- | --- | --- |
| S1-S5 | [[07-多站协同/Clock Offset and Drift]] | 时基偏置、漂移和重锁 |
| S1-S3/S6 | [[07-多站协同/RF and Digital Delay Calibration]] | 参考面和链路延迟 |
| S6-S8 | [[07-多站协同/Cross-Station Event Association]] | 事件候选和碰撞 |
| S6-S9 | [[07-多站协同/Multi-Station Observation Fusion]] | bundle、D 和协方差 |
| T0-T9 | [[06-TDOA定位/TDOA Validation Ledger]] | 解算/几何/鲁棒层 |
| 采数元数据 | [[09-采数实验/Capture Experiment Checklist]] | 原始文件和设备契约 |

## 13. 空结果与报告纪律

结果表使用 null、unknown 或 TODO 表示未运行/未定义：

| run_id | scenario | station_set | clock_bias | drift | delay | association | tdoa_gate | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| null | S0-S9 | null | null | null | null | null | null | planned |

不得将理论预期、设备宣传值、示例 YAML 或一次未复核的坐标填入结果列。若只完成静态文档检查，报告“文档/结构校验通过”，不要报告同步精度。

## 14. 当前待办

- TODO：确认每站硬件时间戳的起点、单位、回绕和丢样语义。
- TODO：准备公共参考源/回环连接图和端口交换方案。
- TODO：确定频率、带宽、采样率、滤波和温度扫描范围。
- TODO：构造 PRACH 碰撞、PUSCH 重传和多峰的带标签回放。
- TODO：预注册同步残差、关联错误率和 TDOA 门限。
- TODO：运行 S1-S5，再进入 S6-S9；每一层保存原始证据。

## 15. 证据与状态

- PERSONAL_NOTE：场景分层、记录模板和故障矩阵承接项目交接、采数、观测和 TDOA 台账。
- STANDARD + partial：TS 38.215/38.305 仅提供定位测量角色和术语边界；本页不定义标准合规阈值。
- HYPOTHESIS + NEEDS_VERIFICATION：同步方案选择、温度模型和事件关联门限尚无本项目实测。
- EXPERIMENT + NEEDS_VERIFICATION：S0-S9 尚未运行，结果表保持空值。

## Related Notes

- [[07-多站协同/Multi-Station Synchronization]]
- [[07-多站协同/Clock Offset and Drift]]
- [[07-多站协同/RF and Digital Delay Calibration]]
- [[07-多站协同/Cross-Station Event Association]]
- [[07-多站协同/Multi-Station Observation Fusion]]
- [[06-TDOA定位/TDOA Validation Ledger]]
- [[06-TDOA定位/TDOA Measurement Model]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[09-采数实验/Capture Experiment Checklist]]
