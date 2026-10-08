---
title: TDOA
aliases:
  - Time Difference of Arrival
  - 到达时间差定位
type: atomic
status: partial
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/tdoa
  - topic/geometric-solver
  - topic/measurement-model
  - stage/validation
  - stage/positioning
source:
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[05-定位观测量/Timing Observation]]"
related:
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
  - "[[5G NR Passive Positioning Pipeline]]"
  - "[[TDOA Measurement Model]]"
  - "[[TDOA Geometry and Solvers]]"
  - "[[TDOA Robust Estimation]]"
  - "[[TDOA Geometry Quality]]"
  - "[[TDOA Validation Ledger]]"
---

# TDOA

## 1. 一句话定义

TDOA 用多个站点对同一发射事件的到达时间差作为观测，消除共同发射时刻的一部分影响，再结合站点几何估计 UE 位置。

## 2. 为什么项目需要它

它是第三阶段从“单用户信号已提取”走向“多站位置估计”的核心接口，也是检验时间同步、RF 延迟校准和观测质量的综合环节。

## 3. 它位于整个 5G 空口链路的什么位置

`PRACH/C-RNTI/PDCCH/PDSCH` 负责识别和提取用户，[[05-定位观测量/Timing Observation]] 负责每站 ToA，TDOA 再把这些观测与站点坐标、同步校准组合为位置约束。

## 4. 输入

同一 `event_id` 的多站校准 ToA/RToA、站点坐标和坐标系、参考站、钟差/采样偏差校准、传播速度假设、质量和 NLOS 标志。

## 5. 输出

站间 TDOA 向量、加权残差、几何质量（如 GDOP 或等价诊断）、位置估计、置信区间/误差指标和拒绝原因。

## 6. 关键参数

站点数量、参考站、二维/三维几何、采样率、时钟偏置/漂移、RF/数字延迟、峰策略、权重、鲁棒损失、初值和约束区域。

## 7. 时域位置

所有 ToA 必须对应同一物理事件和统一时间基准；跨帧或跨重传的事件不能仅凭相近 slot 编号合并。事件关联键至少包含 cell、frame/slot、信号类型和捕获 ID。

## 8. 频域位置

不同观测带宽/PRB/参考信号会产生不同时间分辨率和群时延；TDOA 输入应记录频域掩码与滤波链，不能将未对齐带宽的 ToA 直接相减。

## 9. 数学原理

设 UE 位置为 $\mathbf{x}$，第 $i$ 个站点位置为 $\mathbf{s}_i$，传播速度为 $c$，以参考站 $r$ 构造：

$$
\Delta t_{i,r}(\mathbf{x})=
\frac{\|\mathbf{x}-\mathbf{s}_i\|-\|\mathbf{x}-\mathbf{s}_r\|}{c}.
$$

观测模型为 $\widehat{\Delta t}_{i,r}=\Delta t_{i,r}(\mathbf{x})+\epsilon_{i,r}$。可用加权非线性最小二乘或鲁棒估计求解，但算法选择和精度必须由实验数据支持。

## 10. 3GPP 对应规范

- TS 38.305：NR 定位架构、定位方法和功能边界；标准条款需按 Release 核对。
- TS 38.215：时间/测量定义和物理层测量边界。
- TS 38.455：定位协议接口（LMF/NG-RAN 相关）；不等同第三方被动设备接口。

精确 clause、测量参考点和误差要求当前标记 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

定位求解可用基础 MATLAB `lsqnonlin`、`fmincon` 或自定义加权最小二乘；这些是数值工具，不是 NR 定位协议实现。`nrPositioning` 类 API 是否存在及适用版本需外部核验，当前不作已运行声明。

## 12. 本项目中的用途

接收经 C-RNTI/资源掩码筛出的同一 UE 上行片段，按站点形成校准 ToA，计算 TDOA 并输出带残差和质量标志的位置；先做理想时钟/单径基线，再逐项加入误差因素。

## 13. 常见误区

- 把三站数量等同于任意场景都可稳定三维定位。
- 在站间时钟未校准时直接解释位置偏差为信道多径。
- 将不同 UE、不同重传或不同参考信号的峰错误配对。
- 只报告最终坐标而不报告 TDOA 残差、几何和拒绝样本。

## 14. 与相似概念的区别

- TDOA 是观测差分；ToA 是单站时间；AoA 使用角度而非时间差。
- UL-TDOA 使用上行发射观测；DL-TDOA 的发射源/参考信号角色不同。
- Multi-RTT 需要往返交互；被动 TDOA 不应假定存在下行响应控制。

## 15. 代码实现注意事项

先验证单位、坐标系、参考站和事件关联；把校准量从几何求解器中显式传入；保存每次迭代/残差和剔除原因；对站点缺失、NLOS 和多解场景设置可解释状态。

## 16. 待实验验证的问题

- 理想单径和已知坐标下的无偏性与数值稳定性。
- 时钟偏置、采样率偏差、RF 延迟和峰误差的单因素敏感性。
- 三站/四站几何、GDOP、丢站和 NLOS 的鲁棒性。
- 实时缓存等待、跨站事件匹配和位置尾延迟。

## 17. Related Notes

- [[05-定位观测量/Timing Observation]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]
- [[5G NR Passive Positioning Pipeline]]

## 证据与状态

- `PERSONAL_NOTE`：现有 UL-TDOA 笔记的项目化入口。
- `HYPOTHESIS + NEEDS_VERIFICATION`：解算器、峰策略和精度需真实多站数据验证。

## 18. 观测接口入口

TDOA 只消费通过时间参考、事件关联、校准和质量门的观测。字段和状态由以下页面统一：

- [[05-定位观测量/Observation Taxonomy]]：确认观测类别和信号角色。
- [[05-定位观测量/Timing Observation]]：确认 ToA/RToA、参考点、峰策略和协方差入口。
- [[05-定位观测量/Observation Event Schema]]：确认 event_id、站点顺序和差分矩阵。
- [[05-定位观测量/Quality and Uncertainty]]：确认质量等级、误差预算和拒绝原因。

没有 reference_station_id、站点坐标、校准版本或原始 ToA 协方差时，TDOA 结果应降级为诊断输出，不能宣称位置精度。

## 19. 本目录的解算分层

为避免把“测量问题”和“几何问题”混在同一个函数里，本目录按以下层次组织：

| 层次 | 负责内容 | 入口 |
| --- | --- | --- |
| 测量模型 | ToA、校准项、差分方向、矩阵和协方差 | [[TDOA Measurement Model]] |
| 数值解算 | 几何函数、Jacobian、WLS、初值、约束和停止 | [[TDOA Geometry and Solvers]] |
| 鲁棒处理 | 质量权重、标准化残差、NLOS/坏站和替代解 | [[TDOA Robust Estimation]] |
| 几何质量 | rank、奇异值、条件数、区域扫描和协方差诊断 | [[TDOA Geometry Quality]] |
| 验证台账 | T0-T9 场景、指标、结果表和故障定位 | [[TDOA Validation Ledger]] |

上游观测页负责“这个数是否可比较”，本目录负责“可比较的数对位置意味着什么”。解算器不应直接从原始 IQ 猜测资源、用户或校准状态。

## 20. 一次解算的审计顺序

~~~text
读取 event_id 和站点观测
    ↓
确认参考点、方向、站序、单位和 calibration_id
    ↓
构造独立 TDOA / 协方差
    ↓
检查物理上界、最小站数和 Jacobian rank
    ↓
执行无鲁棒 WLS baseline
    ↓
记录残差、条件数、约束和多起点结果
    ↓
按预注册规则执行鲁棒重加权/留一站诊断
    ↓
输出主候选、替代候选、位置协方差和状态
~~~

先跑无鲁棒 baseline 的目的，是区分“模型/输入本身不闭合”和“异常处理策略不足”。不能只保留最后的鲁棒结果而丢掉基线。

## 21. 结果命名和升级门

| 证据状态 | 允许名称 | 不允许名称 |
| --- | --- | --- |
| 只有相关峰或未校准 ToA | timing_feature / tdoa_candidate | 定位结果、标准 UL-TDOA |
| 事件和站点闭合、校准部分完成 | passive_tdoa_candidate | 已验证位置 |
| 校准、协方差、几何和质量门通过 | project_position_solution | 标准合规精度 |
| 标准参考信号、测量主体、Release 和报告接口均核验 | standard_measurement（需外部核验） | 无限定版本的通用结论 |

位置数值的存在不是升级证据；升级取决于输入契约、几何诊断和验证账本。

## 22. 当前未决项

- 目标网络 Release、标准 UL-RTOA 参考点和第三方设备时间戳语义尚未锁定。
- 真实站点坐标、天线参考面、公共时钟、RF/数字延迟和漂移记录尚未接入。
- 当前没有现场或合成运行结果可填写 ToA/TDOA/位置 RMSE、覆盖率和尾延迟。
- 2D/3D 服务区域、参考站策略、NLOS 标记和异常站阈值需要由项目实验预注册。

这些缺口不会阻止阅读和实现骨架，但必须保持 NEEDS_VERIFICATION 或 NEEDS_EXTERNAL_REFERENCE。

## 23. 证据与限制（补充）

- PERSONAL_NOTE：本页是现有多站 UL-TDOA 笔记的项目化入口和责任边界。
- STANDARD + partial：TS 38.305/38.215 的方法/测量入口；本目录的数值求解和质量门不是标准协议实现。
- EXPERIMENT + NEEDS_VERIFICATION：任何位置精度、收敛率、阈值、协方差覆盖率和实时性能。

## Related Notes（扩展）

- [[TDOA Measurement Model]]
- [[TDOA Geometry and Solvers]]
- [[TDOA Robust Estimation]]
- [[TDOA Geometry Quality]]
- [[TDOA Validation Ledger]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[07-多站协同/Multi-Station Synchronization]]
