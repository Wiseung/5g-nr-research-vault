---
title: Cross-Station Event Association
aliases:
  - 跨站事件关联
  - 多站同一事件判定
  - 事件键与碰撞处理
type: implementation-contract
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/event-association
  - topic/multi-station
  - topic/quality
source:
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[02-PRACH/Random Access Procedure]]"
  - "[[04-PDSCH/UE Resource Extraction]]"
related:
  - "[[07-多站协同/Clock Offset and Drift]]"
  - "[[07-多站协同/Multi-Station Observation Fusion]]"
  - "[[07-多站协同/Synchronization Validation Ledger]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
---

# Cross-Station Event Association

> [!warning] 身份边界
> 跨站事件关联回答“不同站的观测是否可能来自同一个物理发射事件”，不回答“它一定属于哪个 UE”。PRACH 前导、单个相关峰或一次 CRC 通过都不能单独升级为用户身份。

## 1. 一句话定义

跨站关联是将多个 station_observation 按配置、资源、时间、参考序列、协议状态和校准条件组成一个候选 event_id，并把接受、歧义、拒绝和未匹配的替代证据全部保存。

## 2. 为什么关联是独立层

多站同步解决时间坐标能否比较；关联解决比较的两条记录是否对应同一物理事件。即使 ToA 已校准，PRACH 碰撞、PUSCH 重传、MU-MIMO、邻小区同频和峰簇仍可能让最近时间的观测来自不同源。把关联失败交给几何求解器，会产生看似收敛但物理上错误的位置。

## 3. 输入和输出

| 类型 | 最小字段 |
| --- | --- |
| 输入 | station_id、capture_id、config_id、direction、signal_kind、协议坐标、资源快照、峰列表、raw/corrected ToA、clock_model_id、calibration_id |
| 输出 | event_id 候选、候选集合、证据分项、association_state、被拒绝配对、冲突原因、可进入融合的站点集合 |

关联输出应追加到 [[05-定位观测量/Observation Event Schema]] 定义的事件记录，不覆盖原始 station_observation。

## 4. 证据强度分层

| 层级 | 最小证据 | 可支持的结论 | 不能支持的结论 |
| --- | --- | --- | --- |
| candidate | 时间或频率窗口内出现峰 | 可能存在事件 | 同一 UE、可定位 |
| resource_matched | cell/carrier/config、方向和资源一致 | 资源上下文相容 | 同一发射波形 |
| user_associated | C-RNTI/临时标识和跨消息时序闭合 | 用户候选关联 | 站间时间已校准 |
| cross_station_matched | 多站资源、参考序列、时间轨迹相容 | 可组成多站观测候选 | 几何一定正确 |
| tdoa_usable | 校准、协方差、质量和几何门通过 | 允许送入 TDOA | 位置精度已验证 |

状态升级必须记录触发证据和处理版本；不能仅因候选数量变少而自动升级。

## 5. 关联键的优先级

推荐按以下顺序建立候选：

1. cell_id、carrier_id、config_id 和 Release/配置快照兼容；
2. direction 与合法 frame/slot/symbol 或 PRACH occasion 兼容；
3. signal_kind、参考序列、根序列、循环移位或 DM-RS 资源相容；
4. C-RNTI、temporary C-RNTI、RA-RNTI 及状态机时序相容；
5. 峰轨迹、频偏、功率和波形指纹在允许误差内相容；
6. 经过时基和链路校准后的时间差落在物理/场景可行范围；
7. 重复观测、重传序号、端口/层和解码结果没有冲突。

这些是候选证据，不是固定的“打分越高就是真值”。每一项都应保留 pass/fail/unknown，unknown 不能当作 pass。

## 6. 时间门的写法

设站 $i$ 和参考站 $r$ 的校正时间差为 $\Delta t_{i,r}$，站间距离为 $L_{i,r}$。在没有更窄场景约束时，理想传播差满足：

$$
|c\Delta t_{i,r}|\le L_{i,r}.
$$

工程门应把 ToA 协方差、校准不确定度、事件窗口和场景边界纳入松弛区间：

$$
|\Delta t_{i,r}|
\le
\frac{L_{i,r}}{c}
+q_{\alpha}\sigma_{i,r}
+T_{\mathrm{window}}.
$$

$q_{\alpha}$ 和 $T_{\mathrm{window}}$ 不是本项目已验证常数。门通过只能说明“时间上可行”，不能证明两个峰来自同一用户。

## 7. 单事件候选状态机

~~~text
observation_candidate
    -> resource_matched
    -> user_associated
    -> cross_station_matched
    -> calibrated_pending
    -> tdoa_usable

任意状态 -> ambiguous
任意状态 -> rejected
任意状态 -> unmatched
~~~

建议的转移条件：

| 转移 | 必须新增的证据 | 失败动作 |
| --- | --- | --- |
| candidate -> resource_matched | 配置、方向、资源坐标一致 | 保留候选 |
| resource_matched -> user_associated | RAR/Msg3/Msg4 或合法 C-RNTI 时序 | 标 identity_pending |
| user_associated -> cross_station_matched | 多站参考序列和事件窗口相容 | 保留独立站点记录 |
| cross_station_matched -> calibrated_pending | 校准缺失或过期 | 禁止直接融合 |
| calibrated_pending -> tdoa_usable | 校准、协方差、几何门通过 | 进入融合 |

ambiguous 和 rejected 不是删除动作；它们必须带候选和原因。

## 8. PRACH 碰撞和随机接入边界

- 同一 PRACH occasion 内多个 UE 可能使用相同前导，前导索引和相关峰不能唯一标识用户。
- RA-RNTI 描述响应上下文；同一 occasion 的候选仍需 RAPID、RAR 和后续时序匹配。
- 只有 RAR、Msg3/Msg4 和争用解决证据闭合后，才可形成更强的 C-RNTI 关联。
- 不同站看到同一前导，不代表它们看到的是同一个 UE；还要检查峰位置、资源和后续消息。

详细协议链见 [[02-PRACH/Random Access Procedure]] 和 [[02-PRACH/C-RNTI]]。

## 9. PUSCH/DM-RS 重传和多用户边界

关联日志至少保存：

- 传输时刻、slot/symbol、HARQ/重传候选；
- PRB、DM-RS 类型、端口/层和 DCI/RRC 资源快照；
- 同一 C-RNTI 下的不同传输是否允许合并；
- MU-MIMO 或空间层冲突标记；
- 参考序列或解调残差是否支持同一波形假设。

相同 C-RNTI 只能说明协议上下文可能相同，不保证两个峰是同一重传或同一空间层。不同事件应保留不同 event_id，除非有明确的重传/链路关联证据。

## 10. 候选评分的可审计形式

可以定义一个只用于排序的候选代价：

$$
J(a)
=
\sum_j w_j\,\rho_j(a)
+\lambda_{\mathrm{unknown}}N_{\mathrm{unknown}}
+\lambda_{\mathrm{conflict}}N_{\mathrm{conflict}},
$$

其中 $a$ 是一个跨站配对，$\rho_j$ 是标准化的时间、资源、频率或功率差异。权重、鲁棒函数和缺失惩罚必须写入 association_config_id；评分最低不是自动接受，仍需硬性约束和状态门。

建议把证据表同时保存：

| candidate_id | station_ids | resource | time | sequence | identity | calibration | conflicts | state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| null | [] | unknown | unknown | unknown | unknown | unknown | [] | candidate |

## 11. 多事件的全局匹配

当一个窗口内存在多个候选事件时，不要对每个站独立使用贪心最近邻。可构造站点对之间的代价矩阵，并加入：

- 每个站观测至多分配给一个 event_id 的约束；
- 未匹配 dummy 节点，避免为追求满配而强行配对；
- 同一 PRACH occasion 的碰撞容量；
- 重传/重复事件的时间顺序约束；
- 冲突资源或不相容配置的硬拒绝。

实现可以采用匈牙利、最小费用流或其他可解释的匹配方法；具体库和复杂度属于实现选择，当前标 NEEDS_EXTERNAL_REFERENCE。无论采用何种算法，都要保存候选全集、最终分配和未匹配项。

## 12. 关联日志模板

~~~json
association_id: null
event_id: null
association_config_id: null
created_at: null
candidate_observations: []
station_order: []
hard_checks:
  cell_carrier_config: unknown
  direction_time: unknown
  resource_compatibility: unknown
  reference_point: unknown
  calibration_validity: unknown
soft_evidence:
  toa_difference: null
  cfo_difference: null
  power_difference: null
  waveform_similarity: null
  protocol_sequence: null
state: candidate
rejected_alternatives: []
conflict_reasons: []
provenance:
  source_kind: EXPERIMENT
  evidence_status: NEEDS_VERIFICATION
~~~

candidate_observations 的顺序和 station_order 必须稳定；日志中的空列表表示尚未观察到证据，不表示“没有冲突”。

## 13. 与融合层的接口

只有 state 为 cross_station_matched 或更高，且每个站的 reference_point、sample_rate、clock_model_id 和 calibration_id 兼容时，才能交给 [[07-多站协同/Multi-Station Observation Fusion]]。融合层仍需重新检查协方差和几何可行性；关联层不能替下游做质量认证。

## 14. 失败分类

| 失败状态 | 典型原因 | 保留的证据 |
| --- | --- | --- |
| resource_conflict | cell/BWP/RO/PRB 不一致 | 两边配置快照 |
| time_window_conflict | 事件窗不重叠或超物理上界 | raw/corrected 时间 |
| reference_mismatch | 序列起点/FFT 窗定义不同 | reference_point |
| collision_suspected | 同 occasion 多峰/多个候选 | 全峰轨迹和候选集 |
| identity_pending | 没有 RAR/Msg3/Msg4/C-RNTI 闭环 | 协议状态 |
| calibration_pending | 时基或链路校准过期 | calibration_id、有效期 |
| ambiguous | 多个候选同样可行 | 排序和替代配对 |
| rejected | 硬约束冲突或质量门失败 | 决策版本和原因 |

## 15. 回放顺序

~~~text
读取单站 observation
    -> 过滤配置/方向不兼容候选
    -> 生成时间和资源候选边
    -> 计算证据字段与冲突
    -> 做全局匹配或保留未匹配
    -> 写入 association log
    -> 仅把通过状态门的 event_id 交给融合层
~~~

回放必须能在不读取最终位置的情况下重建关联结果；否则位置解会反向泄漏到事件判定。

## 16. 证据与状态

- PERSONAL_NOTE：关联键、状态机和失败分类承接 Observation Event Schema、PRACH 关联和项目交接笔记。
- STANDARD + partial：PRACH/随机接入和 NR 资源角色参考 38.211/38.321 等标准入口；本页不声称标准协议实现完整。
- HYPOTHESIS + NEEDS_VERIFICATION：时间松弛门、候选评分和全局匹配策略尚无本项目正负样本验证。
- EXPERIMENT + NEEDS_VERIFICATION：关联日志模板和状态转移待真实多站回放。

## Related Notes

- [[07-多站协同/Multi-Station Synchronization]]
- [[07-多站协同/Clock Offset and Drift]]
- [[07-多站协同/RF and Digital Delay Calibration]]
- [[07-多站协同/Multi-Station Observation Fusion]]
- [[07-多站协同/Synchronization Validation Ledger]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[02-PRACH/Random Access Procedure]]
- [[02-PRACH/C-RNTI]]
- [[06-TDOA定位/TDOA Measurement Model]]
