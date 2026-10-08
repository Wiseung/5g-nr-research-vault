---
title: TDOA Validation Ledger
aliases:
  - TDOA 验证台账
  - 多站定位验收矩阵
type: experiment-protocol
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/tdoa
  - topic/validation
  - topic/reproducibility
  - stage/experiment
source:
  - "[[06-TDOA定位/TDOA]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[06-TDOA定位/TDOA Robust Estimation]]"
  - "[[03-仿真与实验/5G定位/仿真：多站 UL-TDOA 协同定位]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
related:
  - "[[06-TDOA定位/README]]"
  - "[[06-TDOA定位/TDOA Geometry Quality]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
---

# TDOA Validation Ledger

> [!warning] 实验状态
> 本页是可执行的验证设计和结果契约，不是已经完成的实验报告。没有真实运行、配置快照、原始输出和结果表时，所有数值保持 null，状态保持 EXPERIMENT + NEEDS_VERIFICATION。

## 1. 验证目标

验证顺序应从“方程是否闭合”逐步推进到“设备和现场是否可用”：

1. 检查索引、符号、单位和差分矩阵；
2. 检查已知真值下的 ToA/TDOA/位置闭合；
3. 单独注入噪声、分数延迟、CFO、采样漂移和固定链路延迟；
4. 比较多径/NLOS、碰撞、坏站和几何退化；
5. 回放真实多站 IQ，统计失败原因和实时尾延迟。

每一步只改变预先登记的因素；否则不能知道误差来自哪一层。

## 2. 证据层级

| 层级 | 数据 | 能证明 | 不能证明 |
| --- | --- | --- | --- |
| V0 代数 | 手工/单元级向量和矩阵 | 差分方向、协方差传播和单位闭合 | 空口检测能力 |
| V1 合成 | 已知位置、延迟、噪声和信道 | 指定模型下的偏差/方差/收敛 | 真实硬件和标准互操作 |
| V2 回环 | 公共源、线缆或已知同步装置 | 站间固定延迟/漂移诊断 | 空口 NLOS 和用户关联 |
| V3 设备回放 | 真实 IQ、配置和多站事件 | 端到端处理和失败分类 | 未覆盖场景的泛化 |
| V4 现场 | 已知参考轨迹/真值与完整日志 | 指定部署范围内的性能 | 其他 Release/布局/环境 |

V1/V2 的通过不能替代 V3/V4；标准术语通过也不能替代项目算法验证。

## 3. 场景矩阵

| ID | 场景 | 固定项 | 注入/扫描项 | 核心输出 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T0 | 无噪声单径 | 坐标、站序、c、参考站 | 整数延迟 | 索引、符号、零/近零残差 | TODO |
| T1 | 分数延迟 | T0 全部 | 亚采样延迟、插值方法 | bias、RMSE、边界失败 | TODO |
| T2 | AWGN | T1 方法 | SNR/噪声种子 | ToA/TDOA 误差、质量门 | TODO |
| T3 | 固定链路延迟 | T2 | RF/滤波/数字偏置 | 校准前后偏差 | TODO |
| T4 | 时钟/采样漂移 | T3 | ppm、时长、重锁 | 时间漂移、残差趋势 | TODO |
| T5 | 多径 | T2 基线 | 路径延迟/功率、峰策略 | first/strongest/cluster 对照 | TODO |
| T6 | NLOS/异常站 | T5 | 单站结构偏差 | 降权、剔除、替代解 | TODO |
| T7 | 几何退化 | T2 基线 | 共线/共面/边界位置 | rank、条件数、协方差 | TODO |
| T8 | 丢站/错配 | T7 | 缺失站、错误 event_id | 拒绝率、误关联保护 | TODO |
| T9 | 真实回放/现场 | 锁定设备配置 | 温度、时长、移动轨迹 | 端到端指标、尾延迟 | TODO |

“TODO”表示尚未执行，不表示预期会通过。

## 4. 每次运行的配置快照

~~~json
run_id: null
parent_run_id: null
software:
  language: null
  version: null
  commit: null
  dependencies: []
signal:
  signal_kind: null
  event_source: null
  center_frequency_hz: null
  effective_bandwidth_hz: null
  sample_rate_hz: null
  reference_point: null
stations:
  coordinate_frame: null
  station_order: []
  coordinates: {}
  reference_station_id: null
  antenna_reference_plane: null
difference:
  representation: null
  matrix_rank: null
  covariance_handling: null
timing:
  propagation_speed: null
  clock_model: null
  rf_delay_model: null
  filter_profile: null
  calibration_ids: []
solver:
  name: null
  version: null
  initialization: null
  weight_model: null
  robust_policy: null
  constraints: null
  stopping: null
randomness:
  seed: null
  repetitions: null
artifacts:
  input_uri: null
  raw_observation_uri: null
  solution_uri: null
evidence_status: NEEDS_VERIFICATION
~~~

中心频率、带宽和采样率必须分别填写；用户口述的“120.88 兆”在语义未确认前不能自动放入其中任一字段。

## 5. 指标定义

### 5.1 时间差指标

对第 $n$ 个事件：

$$
e^{tdoa}_{n,k}
=\widehat{\Delta\tau}_{n,k}
-\Delta\tau^{true}_{n,k}.
$$

报告 bias、RMSE、标准差、分位数、有效样本数和拒绝样本数，并说明单位是秒还是距离。没有真值时这些字段保持 null。

### 5.2 位置指标

若有参考位置 $\mathbf{x}^{true}_n$：

$$
e^{pos}_n
=\|\widehat{\mathbf{x}}_n-\mathbf{x}^{true}_n\|.
$$

二维和三维误差分开统计；移动目标还应报告时间对齐、轨迹切片和速度/插值方式。不能把单次坐标或平均坐标替代分布指标。

### 5.3 质量和决策指标

| 指标 | 定义要求 |
| --- | --- |
| event recall | 分母是已知事件数，明确是否含碰撞/不可见事件 |
| association error | 错配事件数和候选总数，保留替代候选 |
| station retention | 每事件使用站数分布和剔除原因 |
| gate acceptance | 通过质量/几何门的比例及版本 |
| covariance coverage | 置信区域定义、覆盖率和样本数 |
| convergence rate | 成功终止的定义、初值策略和迭代上限 |
| p95/p99 latency | 从输入到输出的时间边界，不只报平均值 |

任何指标都必须绑定 run_id、场景、配置和停止规则。

## 6. 通过条件的写法

通过条件应是可观察的，而不是“结果看起来合理”。示例：

| 层 | 可接受的记录形式 |
| --- | --- |
| V0 | 差分矩阵与手算结果逐项相等，单位转换可回放 |
| V1 | 真值、估计、bias/RMSE、样本数和种子齐全 |
| V2 | 校准重复测量的偏置/漂移和不确定度有原始轨迹 |
| V3 | 每个 event_id 可回到 capture/config/observation |
| V4 | 参考轨迹、坐标系、遮挡/环境和失败样本完整 |

阈值若尚未由项目确定，写 threshold_pending，不用模型记忆填数。

## 7. 故障定位矩阵

| 现象 | 首先检查 | 不应直接下的结论 |
| --- | --- | --- |
| 所有站 TDOA 反号 | 站序、差分方向、坐标轴 | 不是先改传播速度 |
| TDOA 超站间基线 | 单位、unwrap、事件匹配、重复校准 | 不是先强行裁剪 |
| 固定方向位置偏移 | RF/滤波/坐标参考面 | 不是随机噪声增大 |
| 误差随时间线性增长 | sample-rate ppm、时钟漂移 | 不是多径唯一解释 |
| 低残差但位置跳变 | 几何 rank、多解、初值 | 不是“算法稳定” |
| 某站总被剔除 | 通道健康、校准和站点布局 | 不是自动删除该站 |
| 真实回放无事件 | TDD/资源/模板/捕获范围 | 不是定位器失败 |
| 位置解在边界 | 约束、模型冲突、区域外事件 | 不是精度良好 |

每个失败都要保留 raw feature、状态和原始日志引用。

## 8. 结果表模板

| run_id | 场景 | 站数/站集 | 几何状态 | SNR/信道 | 校准 | 峰策略 | ToA bias/RMSE | TDOA bias/RMSE | 位置 RMSE/p95 | 覆盖率 | 收敛率 | p95 延迟 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| null | T0 | null | null | 单径 | ideal | first | null | null | null | null | null | null | TODO |
| null | T1 | null | null | 分数延迟 | ideal | first | null | null | null | null | null | null | TODO |
| null | T2 | null | null | AWGN | ideal | first | null | null | null | null | null | null | TODO |
| null | T3-T6 | null | null | 多径/异常 | calibrated | first/strongest/cluster | null | null | null | null | null | null | TODO |
| null | T7-T9 | null | null | 退化/现场 | calibrated | configured | null | null | null | null | null | null | TODO |

空表是有意保留的证据边界，不应为了“完成”而填入预期数字。

## 9. 复现和审计清单

- [ ] 输入 IQ、配置、站点坐标和校准表的引用可访问。
- [ ] 原始观测和校正观测均保存，校准没有覆盖 raw。
- [ ] 站点顺序、参考站、坐标系、传播速度和单位明确。
- [ ] event_id 关联规则和碰撞/重传处理可回放。
- [ ] 求解器初值、权重、鲁棒策略、约束和停止条件锁定。
- [ ] 真值生成或参考轨迹方法独立记录。
- [ ] 失败样本、异常站和替代候选没有被过滤掉。
- [ ] 结果指标按场景和 run_id 分层，不跨设置混合汇总。
- [ ] 未验证的标准/API/现场结论仍标记 NEEDS_EXTERNAL_REFERENCE 或 NEEDS_VERIFICATION。

## 10. 与项目其他层的接口

| 本页需要 | 来源 |
| --- | --- |
| 单站 ToA、参考点、峰和协方差 | [[05-定位观测量/Timing Observation]] |
| event_id、资源和状态 | [[05-定位观测量/Observation Event Schema]] |
| 质量等级和拒绝原因 | [[05-定位观测量/Quality and Uncertainty]] |
| 站间时基和校准 | [[07-多站协同/Multi-Station Synchronization]] |
| 真实捕获格式和设备元数据 | [[09-采数实验/Capture Experiment Checklist]] |
| 几何方程和求解器 | [[06-TDOA定位/TDOA Geometry and Solvers]] |

## 11. 证据与限制

- EXPERIMENT + NEEDS_VERIFICATION：T0-T9、指标、阈值和结果表均未在本轮运行。
- PERSONAL_NOTE：验证层级、故障矩阵和报告字段是项目工程契约。
- STANDARD + partial：TS 38.215/38.305 仅作为标准测量/定位边界入口，不提供本项目算法的通过条件。
- NEEDS_EXTERNAL_REFERENCE：设备 API、目标 Release、标准参考点和现场真值获取方法。

## Related Notes

- [[06-TDOA定位/README]]
- [[06-TDOA定位/TDOA]]
- [[06-TDOA定位/TDOA Measurement Model]]
- [[06-TDOA定位/TDOA Geometry and Solvers]]
- [[06-TDOA定位/TDOA Robust Estimation]]
- [[06-TDOA定位/TDOA Geometry Quality]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[09-采数实验/Capture Experiment Checklist]]
