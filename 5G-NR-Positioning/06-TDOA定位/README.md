---
title: 06-TDOA定位
aliases:
  - TDOA 定位解算层
  - NR 被动多站定位
type: directory-index
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/tdoa
  - topic/geometric-solver
  - stage/positioning
source:
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - 用户项目第三阶段目标
related:
  - "[[06-TDOA定位/TDOA]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[06-TDOA定位/TDOA Robust Estimation]]"
  - "[[06-TDOA定位/TDOA Geometry Quality]]"
  - "[[06-TDOA定位/TDOA Validation Ledger]]"
  - "[[05-定位观测量/README]]"
  - "[[07-多站协同/README]]"
---

# 06-TDOA定位

> [!abstract] 目录边界
> 本目录负责把已经通过观测质量门的多站 ToA/RToA 变成可审计的 TDOA 几何约束、位置解和诊断结果。它不重新定义 PRACH/PUSCH 的资源提取，不把一个相关峰自动升级为标准 UL-RTOA，也不把一次坐标输出包装成已验证的定位精度。
>
> GNSS、地图匹配和机器学习定位不在本目录的第一版范围内；如后续引入，应作为独立的先验/融合层记录，不能回写覆盖 TDOA 原始观测。

## 1. 这一层回答什么问题

上游 [[05-定位观测量/README]] 已经回答：

- 哪个 event_id 被哪些站观测到；
- 每站的参考点、样点、toa_raw、toa_corrected 和不确定度是什么；
- 校准、事件关联和质量状态是否允许跨站比较。

本目录继续回答：

1. 如何固定 TDOA 的符号、单位、参考站和差分矩阵；
2. 如何把站点坐标与时间差写成二维/三维几何方程；
3. 如何选择初值、权重、约束、迭代求解器和停止条件；
4. 如何处理协方差、异常站、NLOS、近共线几何和多解；
5. 如何把每次解算结果记录为可回放、可拒绝、可比较的输出。

## 2. 目录地图

| 笔记 | 责任 | 主要产物 | 当前状态 |
| --- | --- | --- | --- |
| [[06-TDOA定位/TDOA]] | 总入口、协议边界和端到端链路 | 术语、输入输出、阶段门、相邻页 | partial |
| [[06-TDOA定位/TDOA Measurement Model]] | 测量方程和差分表示 | ToA/TDOA 向量、差分矩阵、协方差和钟差模型 | PERSONAL_NOTE + NEEDS_VERIFICATION |
| [[06-TDOA定位/TDOA Geometry and Solvers]] | 几何方程和数值解算 | Jacobian、WLS、约束、初值和求解诊断 | PERSONAL_NOTE + NEEDS_VERIFICATION |
| [[06-TDOA定位/TDOA Robust Estimation]] | 异常与退化场景 | 鲁棒权重、NLOS/坏站、剔除和替代候选 | HYPOTHESIS + NEEDS_VERIFICATION |
| [[06-TDOA定位/TDOA Geometry Quality]] | 可观测性和站点布局 | rank、条件数、GDOP-like、协方差和几何门 | PERSONAL_NOTE + NEEDS_VERIFICATION |
| [[06-TDOA定位/TDOA Validation Ledger]] | 实验与报告契约 | T0-T9 场景、指标、结果表和失败分类 | EXPERIMENT + NEEDS_VERIFICATION |

## 3. 端到端数据流

~~~text
05/07 层：event_id + 多站校准 ToA + 协方差 + 站点坐标
    ↓
TDOA Measurement Model：固定参考站/差分矩阵/符号/单位
    ↓
Geometry and Solvers：h(x)、J(x)、WLS、约束和停止规则
    ↓
Robust Estimation：质量权重、残差门、坏站和 NLOS 候选
    ↓
Geometry Quality：rank、条件数、几何质量和协方差诊断
    ↓
输出 solution：位置、残差、有效站、协方差、状态和证据
    ↓
Validation Ledger：与真值/回环/现场数据的分层验证
~~~

每一步都追加新记录，不覆盖上游 raw 值。解算器接收到 calibrated_pending、reference_unknown 或 event_link_ambiguous 时，应返回可诊断的拒绝状态，而不是把缺失字段当作零。

## 4. 最小输入契约

进入几何求解前，至少要有：

| 输入 | 必需字段 | 失败状态 |
| --- | --- | --- |
| 事件 | event_id、信号方向/类型、事件时间范围 | event_incomplete |
| 站点 | station_id、坐标、坐标系、天线参考点 | geometry_unknown |
| 时间 | 同一参考点的 toa_corrected_seconds 或明确的项目 RToA | calibrated_pending |
| 差分 | reference_station_id、差分定义、单位和站点顺序 | difference_undefined |
| 质量 | 每站状态、标准差/协方差、拒绝原因 | quality_missing |
| 配置 | config_id、calibration_id、算法版本 | provenance_incomplete |

只有 event_id、参考点、带宽/滤波配置、校准有效期和站点顺序兼容时，才可把多个单站记录组成同一 TDOA 向量。字段详情见 [[05-定位观测量/Observation Event Schema]]。

## 5. 输出契约

每次解算至少应输出：

| 类别 | 字段示例 |
| --- | --- |
| 身份 | solution_id、event_id、run_id |
| 几何 | coordinate_frame、dimension、station_ids_used、reference_station_id |
| 观测 | tdoa_seconds、tdoa_covariance、输入 observation_id 列表 |
| 求解器 | 名称/版本、初值、约束、迭代次数、停止原因 |
| 质量 | 加权代价、逐方程残差、标准化残差、rank、条件数、几何状态 |
| 异常 | 被剔除站、替代站集合、剔除原因和重算次数 |
| 结果 | 位置估计、局部协方差/误差椭圆（若可解释）、状态 |
| 证据 | source_kind、evidence_status、配置/校准引用 |

position_estimate 为空并不表示没有价值：若保留了 TDOA、残差和失败原因，该记录仍可用于同步或事件关联诊断。

## 6. 阅读顺序

1. 先读 [[05-定位观测量/Timing Observation]]，确认 ToA 的参考点和校准符号。
2. 读 [[05-定位观测量/Observation Event Schema]]，确认 event_id、协方差和状态字段。
3. 读 [[07-多站协同/Multi-Station Synchronization]]，确认站间时基、RF/数字链和有效期。
4. 读 [[06-TDOA定位/TDOA Measurement Model]]，固定差分表示和误差模型。
5. 读 [[06-TDOA定位/TDOA Geometry and Solvers]]，实现基础 WLS/约束解算。
6. 读 [[06-TDOA定位/TDOA Geometry Quality]] 与 [[06-TDOA定位/TDOA Robust Estimation]]，加入几何门和异常处理。
7. 按 [[06-TDOA定位/TDOA Validation Ledger]] 运行分层实验，再回写 EXPERIMENT 结果。

## 7. 证据与命名边界

- STANDARD + partial：TS 38.305/38.215 的标准定位方法、测量术语和参考点入口；精确 Release、条款和报告字段仍需外部核验。
- PERSONAL_NOTE：本目录的差分矩阵、几何模型、求解器接口和工程状态机。
- HYPOTHESIS + NEEDS_VERIFICATION：在无 LMF/gNB 协作时，以 PRACH/PUSCH/SRS 上行片段形成项目定制被动 UL-TDOA。
- EXPERIMENT + NEEDS_VERIFICATION：所有阈值、定位误差、覆盖率、实时性和现场鲁棒性结果。
- NEEDS_EXTERNAL_REFERENCE：标准 UL-RTOA 的精确测量参考点、第三方设备时间戳语义和未在本机运行核验的 MATLAB API。

项目字段建议使用 passive_ul_toa、passive_tdoa、project_position_solution；只有标准发射源、测量主体、参考信号、Release 和报告接口都闭合时，才升级为更窄的标准名称。

## 8. 目录验收清单

- [ ] TDOA 符号和距离差方向在所有页面一致。
- [ ] 站点坐标、单位、坐标系和天线参考面可回查。
- [ ] 差分矩阵与 ToA 协方差一同保存；共享参考站不被误当成独立差分。
- [ ] 2D/3D、已知/未知时钟和约束边界明确写出。
- [ ] 初值、权重、停止条件、异常站策略和重算记录可复现。
- [ ] 几何 rank/条件数/残差与位置协方差分开报告。
- [ ] 拒绝样本、替代候选和未运行实验未被删除或伪装成成功。
- [ ] 每个结果都能沿 solution_id → event_id → observation_id → capture_id 回到原始证据。

## Related Notes

- [[06-TDOA定位/TDOA]]
- [[06-TDOA定位/TDOA Measurement Model]]
- [[06-TDOA定位/TDOA Geometry and Solvers]]
- [[06-TDOA定位/TDOA Robust Estimation]]
- [[06-TDOA定位/TDOA Geometry Quality]]
- [[06-TDOA定位/TDOA Validation Ledger]]
- [[05-定位观测量/README]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[09-采数实验/Capture Experiment Checklist]]
