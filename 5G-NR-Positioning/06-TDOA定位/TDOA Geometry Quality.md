---
title: TDOA Geometry Quality
aliases:
  - TDOA 几何质量
  - GDOP 与可观测性
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/tdoa
  - topic/geometry
  - topic/gdop
  - topic/observability
  - stage/validation
source:
  - "[[06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[03-仿真与实验/5G定位/仿真：多站 UL-TDOA 协同定位]]"
related:
  - "[[06-TDOA定位/TDOA]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[06-TDOA定位/TDOA Robust Estimation]]"
  - "[[06-TDOA定位/TDOA Validation Ledger]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
---

# TDOA Geometry Quality

> [!abstract] 几何边界
> 低残差不等于几何良好。本站点布局、坐标误差、参考站选择和高度约束决定了 TDOA 对位置扰动的可观测方向；本页定义项目诊断量和布局验收，不把 GDOP-like 指标当作标准合规阈值。

## 1. 局部可观测性

对 $K$ 条独立 TDOA 方程，位置维度为 $d$，Jacobian 为 $\mathbf J\in\mathbb R^{K\times d}$：

$$
\mathbf J_{k,:}
=\frac{1}{c}
\left(
\frac{(\mathbf{x}-\mathbf{s}_{i_k})^T}
     {\|\mathbf{x}-\mathbf{s}_{i_k}\|}
-\frac{(\mathbf{x}-\mathbf{s}_{r_k})^T}
     {\|\mathbf{x}-\mathbf{s}_{r_k}\|}
\right).
$$

局部位置可观测性的第一道检查是：

- $K\ge d$ 只是方程数量条件；
- $\operatorname{rank}(\mathbf J)=d$ 才表示局部方向没有完全缺失；
- rank 满足时仍可能有很小的奇异值，导致误差巨大；
- 非线性多解和远离线性化点的问题不能由 rank 单独排除。

因此报告必须同时保存方程数、rank、奇异值和条件数。

## 2. 奇异值与条件数

对加权设计矩阵：

$$
\widetilde{\mathbf J}
=\mathbf{\Sigma}_z^{-1/2}\mathbf J
=\mathbf U\mathbf S\mathbf V^T.
$$

设奇异值为 $s_1\ge\cdots\ge s_d$：

- $s_d$ 接近零说明至少一个位置方向弱可观测；
- $s_1/s_d$ 可作为条件数诊断；
- 不同坐标缩放、时间/距离残差单位会改变数值，必须记录尺度；
- 协方差近似不可靠时，奇异值只能作诊断，不能直接解释为置信度。

如果观测使用全 pair 差分，$\mathbf{\Sigma}_z$ 可能包含结构性零特征值。白化时应先使用独立差分基，或按记录的有效秩进行特征分解/广义逆；不能把一个数值上加小的对角线项伪装成测量信息。正则化参数若确有必要，必须写入 solver 和 geometry report。

建议把原始奇异值向量保存，而不是只保存一个布尔值 geometry_ok。

## 3. GDOP-like 与位置协方差

在线性化模型成立且协方差可逆时：

$$
\mathbf{\Sigma}_x
\approx
(\mathbf J^T\mathbf W\mathbf J)^{-1},
\qquad
\mathbf W=\mathbf{\Sigma}_z^{-1}.
$$

项目可以报告以下透明的派生量：

| 字段 | 定义/用途 | 边界 |
| --- | --- | --- |
| position_covariance | 位置坐标的局部协方差 | 依赖模型、线性化和权重 |
| axis_std | 协方差对角线平方根 | 不是任意方向最大误差 |
| condition_number | 加权 Jacobian 或正规矩阵条件数 | 需记录计算对象和尺度 |
| gdop_like | 协方差迹或几何矩阵迹的项目代理量 | 不是未限定 Release 的标准 GDOP |
| error_ellipse | 二维协方差特征分解后的轴/方向 | 需说明覆盖约定 |

不要把 gdop_like 的数值阈值写成 3GPP 要求；阈值只能来自项目实验或明确外部定义。

## 4. 站点布局

### 4.1 二维

三站可以提供两个独立差分方程的候选，但若站点近共线，双曲线交点在横向方向非常敏感。布局评估应在预期服务区域内扫描，而不是只在一个方便的真值点计算。

建议保存：

- 站点多边形面积/基线长度等布局描述；
- 服务区域网格上的 rank、最小奇异值和条件数；
- 每个候选 UE 位置的可行差分范围；
- 参考站变更前后的协方差和数值稳定性。

这些几何描述是项目设计指标，不自动等同标准覆盖保证。

### 4.2 三维

如果站点高度近似相同，垂直方向可能弱可观测；增加一个高度差明显且视线条件良好的站，可能比单纯增加共面站更有帮助，但效果必须用实际坐标和传播模型验证。未知高度、地面约束和 NLOS 不能被一个二维结果替代。

### 4.3 服务区域外推

站点布局在训练区域表现好，不代表区域外仍然好。验证应把坐标域划分为：

1. 设计/调参区域；
2. 未见位置的验证区域；
3. 边界和站点外侧的压力区域。

报告中分开统计，避免以同一位置反复调参后宣称泛化。

## 5. 参考站选择

理想无误差模型下，改变参考站只是改变差分表示；有协方差、丢站和数值退化时，参考站会影响条件数和稳定性。项目可把参考站作为可配置策略：

| 策略 | 依据 | 必须报告 |
| --- | --- | --- |
| 固定站 | 长期硬件稳定、校准完整 | 固定 ID 和失效替代 |
| 质量优先 | 当前峰/校准质量最高 | 质量配置版本 |
| 几何优先 | 使设计矩阵条件更好 | 评估位置/区域和目标函数 |
| 自适应 | 质量与几何联合 | 防止使用未来真值或泄漏 |

参考站选择不应改变物理观测的原始值；只改变差分矩阵和求解表示。

## 6. 坐标、单位和参考面

几何质量计算前必须闭合：

- 坐标轴方向、原点、单位和维度；
- 站点坐标对应天线相位中心、阵列中心还是设备外壳；
- 地面高度、楼层和移动目标的高度假设；
- 传播速度参数与环境模型；
- 站点坐标测量误差是否进入协方差或仅作为固定误差。

坐标参考面不一致会表现为系统性残差；调大噪声权重不能替代坐标修正。

## 7. 物理可行域和双曲线交集

每个 TDOA 给出一条等距差约束：

$$
\|\mathbf{x}-\mathbf{s}_i\|
-\|\mathbf{x}-\mathbf{s}_r\|
=c\Delta\tau_{i,r}.
$$

在存在误差时，更合理的是带宽度的条带：

$$
\left|
\|\mathbf{x}-\mathbf{s}_i\|
-\|\mathbf{x}-\mathbf{s}_r\|
-c\Delta\tau_{i,r}
\right|
\le \gamma_k\sigma_{k,d},
$$

其中 $\sigma_{k,d}=c\sigma_k$，$\gamma_k$ 来自版本化质量门。条带交集为空时，应优先报告模型/关联冲突，而不是无条件寻找一个高残差坐标。

## 8. 站点与坐标误差

若站点坐标也有不确定度，可把它们作为单独误差源：

$$
\delta z
\approx
\mathbf J_x\delta\mathbf x
+\mathbf J_s\delta\mathbf s
+\epsilon.
$$

当前项目先把站点坐标视为配置输入，坐标测量误差列为 NEEDS_VERIFICATION。不得把未量化的地图误差塞进 ToA 协方差而不标记来源。

## 9. 几何质量报告模板

~~~json
geometry_report_id: null
event_id: null
coordinate_frame: null
dimension: null
station_order: []
reference_station_id: null
station_count_total: null
station_count_used: null
equation_count: null
jacobian_rank: null
singular_values: []
condition_number: null
gdop_like:
  definition: null
  value: null
position_covariance: null
active_constraints: []
feasible_region:
  bounds: null
  method: null
states: []
evidence_status: NEEDS_VERIFICATION
~~~

gdop_like.definition 必须和数值同时保存；只保存一个名字会让不同脚本的量无法比较。

## 10. 几何门建议

几何门应分成硬门和软诊断：

| 门 | 示例条件 | 失败动作 |
| --- | --- | --- |
| 硬门 | 坐标/维度/单位缺失 | geometry_unknown |
| 硬门 | rank 小于位置维度 | tdoa_rejected |
| 硬门 | TDOA 超物理上界 | model_inconsistent |
| 软门 | 条件数偏大 | geometry_poor 或降权 |
| 软门 | 协方差迹偏大 | position_uncertain |
| 软门 | 多起点解分散 | multiple_solution_candidate |
| 软门 | 结果贴边 | boundary_active |

具体阈值应在验证账本中预注册。硬门和软门不能合并成一个 opaque score。

## 11. 验证矩阵

| 场景 | 变量 | 指标 | 目标 |
| --- | --- | --- | --- |
| G0 | 已知坐标、单径、无噪声 | rank、残差、位置闭合 | 验证方程实现 |
| G1 | 服务区域网格 | 最小奇异值、条件数 | 找到弱几何区域 |
| G2 | 参考站轮换 | 解、协方差、数值稳定 | 检查表示不变性 |
| G3 | 站点坐标扰动 | 偏差和残差 | 分离地图/测量误差 |
| G4 | 2D/3D 高度变化 | 垂直轴不确定度 | 验证高度可观测性 |
| G5 | 一站丢失 | rank、替代解 | 明确失效边界 |
| G6 | 多径/NLOS | 几何指标与残差 | 不用几何分数掩盖信号问题 |

这些行是实验设计，不是已经完成的结果。

## 12. 证据与限制

- PERSONAL_NOTE：本页的 rank、奇异值、条件数、协方差和布局检查来自项目几何推导。
- STANDARD + partial：标准定位方法和测量角色见 TS 38.305/38.215；本页的几何门和 gdop_like 定义不是标准合规判定。
- HYPOTHESIS + NEEDS_VERIFICATION：布局自适应、参考站策略和坐标误差传播在现场的收益。
- EXPERIMENT + NEEDS_VERIFICATION：所有几何阈值、位置误差、覆盖率和服务区域结论。

## Related Notes

- [[06-TDOA定位/TDOA]]
- [[06-TDOA定位/TDOA Measurement Model]]
- [[06-TDOA定位/TDOA Geometry and Solvers]]
- [[06-TDOA定位/TDOA Robust Estimation]]
- [[06-TDOA定位/TDOA Validation Ledger]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[07-多站协同/Multi-Station Synchronization]]
