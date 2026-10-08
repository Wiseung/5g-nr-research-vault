---
title: TDOA Measurement Model
aliases:
  - TDOA 测量模型
  - 到达时间差观测方程
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/tdoa
  - topic/toa
  - topic/measurement-model
  - stage/positioning
source:
  - "[[5G-NR-Positioning/05-定位观测量/Timing Observation]]"
  - "[[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
related:
  - "[[06-TDOA定位/TDOA]]"
  - "[[06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[06-TDOA定位/TDOA Geometry Quality]]"
  - "[[06-TDOA定位/TDOA Robust Estimation]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
---

# TDOA Measurement Model

> [!abstract] 模型边界
> 本页把“每站测到的时间”整理成可进入几何解算的观测向量。方程是项目的工程模型与推导，不是 3GPP ASN.1 或定位协议消息定义。标准 UL-RTOA 的参考点、测量主体和报告接口仍须按目标 Release 外部核验。

## 1. 先固定符号和对象

| 符号                 | 含义                                   | 维度/单位        | 必须绑定                             |
| ------------------ | ------------------------------------ | ------------ | -------------------------------- |
| $M$            | 参与该事件的接收站数量                          | 无量纲          | station_ids_used                 |
| $\mathbf{s}_i$ | 第 $i$ 站天线参考点坐标                   | $d$ 维、坐标单位 | coordinate_frame、reference_plane |
| $\mathbf{x}$     | 发射源/UE 位置                            | $d$ 维、坐标单位 | coordinate_frame                 |
| $r_i$            | 几何距离 $\|\mathbf{x}-\mathbf{s}_i\|$ | 坐标单位         | 同一坐标系                            |
| $c$              | 传播速度参数                               | 坐标单位/秒       | propagation_model_id             |
| $t_0$            | 该物理事件的未知发射时刻                         | 秒            | event_id                         |
| $b_i(t)$         | 站点时间基准偏置/漂移                          | 秒            | calibration_id、时间                |
| $d_i$            | RF、天线、线缆和数字链固定延迟                     | 秒            | reference_plane、频率/带宽            |
| $\epsilon_i$     | 估计、噪声、多径和关联残差                        | 秒            | quality/evidence                 |

这里的“站点”是接收观测的时间实体，不自动等同于 gNB、TRP 或 3GPP 测量点。项目第三方设备的角色必须在事件字段中单独记录。

## 2. 单站观测方程

对同一 event_id 的站 $i$，未经校正的时间可写成：

$$
\widehat{\tau}^{raw}_i
 = t_0 + \frac{\|\mathbf{x}-\mathbf{s}_i\|}{c}
 + b_i(t_e) + d_i(f,B,\mathcal{F})
 + \epsilon_i .
$$

其中 $t_e$ 是事件所在的时间，$f$ 是中心频率，$B$ 是有效观测带宽，$\mathcal{F}$ 是数字滤波/抽取配置。把这些条件写入方程，是为了防止把一次窄带校准表静默复用于另一条处理链。

若已应用版本化校准，工程上保存：

$$
\widehat{\tau}^{corr}_i
 = \widehat{\tau}^{raw}_i
 - \widehat b_i(t_e)
 - \widehat d_i(f,B,\mathcal{F}).
$$

减号只是本项目的显式符号约定；校准装置若定义了相反方向，必须在 calibration record 中记录转换，不得靠字段名猜符号。

### 2.1 绝对 ToA 的限制

没有已知发射时刻 $t_0$、天线参考面、站点时钟偏置和链路延迟时，$\widehat{\tau}_i$ 主要是相对观测。它可以支持事件触发或站间差分候选，但不能直接声明为 UE 到该站的绝对距离。

Timing Advance 是网络向 UE 发送的上行定时控制信息；它和接收机由 PRACH/PUSCH 相关峰得到的时间不是同一字段。TA 可以作为协议上下文或一致性检查，不能未经事件对齐就代替 $\widehat{\tau}_i$。

## 3. 差分模型

选定参考站 $r$，定义本项目统一的差分方向：

$$
\Delta\tau_{i,r}
 = \widehat{\tau}_i-\widehat{\tau}_r,
\qquad i\ne r.
$$

理想几何项为：

$$
h_{i,r}(\mathbf{x})
 = \frac{\|\mathbf{x}-\mathbf{s}_i\|
       -\|\mathbf{x}-\mathbf{s}_r\|}{c}.
$$

因此：

$$
\Delta\tau_{i,r}
 = h_{i,r}(\mathbf{x})
 + \bigl(b_i-b_r\bigr)
 + \bigl(d_i-d_r\bigr)
 + \bigl(\epsilon_i-\epsilon_r\bigr).
$$

对应的距离差是 $c\Delta\tau_{i,r}$，但只有在时钟、链路延迟和传播速度模型已被明确后才可将其用于双曲线约束。若实现采用 $\widehat{\tau}_r-\widehat{\tau}_i$，必须同时反转几何方程和输出字段，不能只改显示符号。

## 4. 差分矩阵表示

把 $M$ 个单站时间组成：

$$
\boldsymbol{\tau}
 = [\widehat{\tau}_1,\ldots,\widehat{\tau}_M]^T.
$$

以参考站 $r$ 的独立差分为例，构造矩阵 $\mathbf D_r$。若站点顺序是 $[1,2,\ldots,M]$，且 $r=1$，则：

$$
\mathbf D_1 =
\begin{bmatrix}
-1&1&0&\cdots&0\\
-1&0&1&\cdots&0\\
\vdots&\vdots&\vdots&\ddots&\vdots\\
-1&0&0&\cdots&1
\end{bmatrix},
\qquad
\boldsymbol{\Delta\tau}=\mathbf D_1\boldsymbol{\tau}.
$$

一般参考站 $r$ 只需把每一行的 $+1$ 放在被比较站、$-1$ 放在参考站。实现必须把矩阵或等价的 station order 一起保存，避免“同名 pair”在不同脚本中代表相反方向。

### 4.1 全 pair 与独立基

所有站两两相减可产生 $M(M-1)/2$ 个 pair，但这些差分不是全都独立；它们来自同一个 $\boldsymbol{\tau}$，矩阵秩最多为 $M-1$。因此：

- 训练和展示可以保存全 pair；
- 求解应优先使用一组独立差分，或显式使用奇异协方差的广义逆；
- 不能把全 pair 的重复信息当作独立样本来缩小不确定度。

这也是为什么参考站表示、独立基表示和全 pair 表示可能给出不同的数值协方差，但在模型闭合时应给出一致的物理解。

## 5. 协方差传播

设单站 ToA 协方差为 $\mathbf{\Sigma}_{\tau}$，则：

$$
\mathbf{\Sigma}_{\Delta}
 = \mathbf D_r \mathbf{\Sigma}_{\tau}\mathbf D_r^T.
$$

若站点误差独立，$\mathbf{\Sigma}_{\tau}$ 可以是对角近似；共享参考时钟、公共触发、同一参考站或共同滤波链会引入非对角项，必须保留其来源。对角近似只能作为明确标记的 baseline，不能写成“真实协方差”。

对两个差分的示意：

$$
\operatorname{cov}(\tau_i-\tau_r,\tau_j-\tau_r)
 = \operatorname{cov}(\tau_i,\tau_j)
 -\operatorname{cov}(\tau_i,\tau_r)
 -\operatorname{cov}(\tau_j,\tau_r)
 +\operatorname{var}(\tau_r).
$$

参考站时间不确定度会同时进入多个方程，这正是忽略协方差会低估位置不确定度的直接原因。

## 6. 钟差与漂移模型

固定偏置和随时间变化的项分开记录：

$$
b_i(t)=b_{i,0}+\alpha_i(t-t_{ref})+\nu_i(t),
$$

其中 $b_{i,0}$ 是固定偏置，$\alpha_i$ 是工程上的时钟/采样漂移斜率，$\nu_i(t)$ 是未建模残差。对事件 $k$：

$$
\Delta\tau_{i,r,k}
 = h_{i,r}(\mathbf{x}_k)
 + (b_{i,0}-b_{r,0})
 + (\alpha_i-\alpha_r)(t_k-t_{ref})
 + \eta_{i,r,k}.
$$

单个事件通常不能同时从未知位置和未知站间偏置中辨识全部参数。可行路线包括：

1. 先用公共源/线缆回环估计校准项，再固定到事件解算；
2. 用已知位置的多事件估计站间偏置和漂移；
3. 在联合优化中加入先验和锚定站，但显式报告可辨识性假设。

没有这些额外约束时，把钟差当成位置坐标会产生不可解释的自由度。

## 7. 事件关联门

组成 $\boldsymbol{\tau}$ 之前，至少检查：

| 检查 | 证据 | 失败动作 |
| --- | --- | --- |
| 事件身份 | 同一 event_id、信号类型、方向和资源快照 | 不合并，保留候选 |
| 时间窗口 | capture/sample 区间和协议时间兼容 | 标记 event_window_conflict |
| 参考点 | RO/序列起点/FFT 窗等定义一致 | 标记 reference_mismatch |
| 频域条件 | 中心频率、有效带宽、PRB/滤波配置 | 标记 bandwidth_mismatch |
| 校准有效期 | calibration_id、valid_from/to、温度/重锁状态 | 降级 calibrated_pending |
| 参考序列 | 模板、端口/层和估计器版本一致 | 标记 template_mismatch |

“样点相近”只能产生关联候选，不能替代上述证据。PRACH 前导相同也不能消除同一 occasion 的碰撞不确定性。

## 8. 物理可行性检查

在无误差理想模型下，任一时间差必须满足：

$$
|c\Delta\tau_{i,r}|
\le \|\mathbf{s}_i-\mathbf{s}_r\|.
$$

真实观测允许估计误差和校准不确定度，因此工程门应使用带不确定度的松弛区间，而不是硬编码等号。若明显超出站间距离上界，优先检查：

- TDOA 符号或站点顺序反了；
- 事件跨站错配；
- 采样率/时间单位错；
- 周期相关索引没有 unwrap；
- RF/数字延迟重复或漏减；
- 观测并非同一发射源。

这项检查能在进入非线性优化前拦截大量结构性错误。

## 9. 观测记录示例

下面是项目内部字段示例，数值留空表示模板，不是实验结果：

~~~json
event_id: null
signal_kind: passive_ul_reference
station_order: []
reference_station_id: null
coordinate_frame: null
propagation_speed:
  value: null
  unit: distance_per_second
  model_id: null
toa:
  raw_seconds: {}
  corrected_seconds: {}
  reference_point: null
  estimator_id: null
tdoa:
  sign: station_minus_reference
  values_seconds: {}
  difference_matrix: []
  covariance_seconds2: []
calibration:
  calibration_ids: []
  valid: null
quality:
  state: unknown
  reasons: []
evidence_status: NEEDS_VERIFICATION
~~~

这里的空对象比填入 0 更诚实：零可能是合法测量，也可能代表“未估计”。

## 10. 与标准和项目名称的分离

- standard_ul_rtoa：只有标准参考信号、测量主体、参考点、Release 和报告接口都核验后才可使用。
- passive_ul_toa：固定第三方站从上行片段得到的项目单站时间候选。
- passive_tdoa：经过项目校准、事件关联和质量门后的站间差分。
- project_position_solution：几何求解器输出的项目结果，不等于标准定位服务响应。

TS 38.305/38.215 的方法和测量边界是外部核验入口；本页的矩阵、字段和状态是 PERSONAL_NOTE + NEEDS_VERIFICATION。

## 11. 实现检查表

- [ ] 所有时间字段同时保留样点、采样率和秒值。
- [ ] 站点顺序、参考站和差分方向写入结果，而不是依赖数组顺序。
- [ ] raw、corrected、tdoa_used 三层数值不互相覆盖。
- [ ] 采样率偏差用时间模型表达，不把长时间漂移塞入一次方差。
- [ ] 全 pair 展示和独立差分求解的关系有明确标记。
- [ ] 协方差与差分矩阵一起传播，奇异性/秩被记录。
- [ ] 物理可行性和事件关联在优化前执行。
- [ ] 未闭合字段返回降级状态，不静默补零。

## 12. 证据与限制

- PERSONAL_NOTE：由 [[05-定位观测量/Timing Observation]]、[[05-定位观测量/Observation Event Schema]] 和现有多站笔记整理出的项目测量方程。
- STANDARD + partial：TS 38.215/38.305 的测量与定位术语入口；精确参考点、Release 差异和报告字段仍为 NEEDS_EXTERNAL_REFERENCE。
- HYPOTHESIS + NEEDS_VERIFICATION：联合估计钟差/漂移和以被动上行片段形成项目 TDOA 的可用性。
- EXPERIMENT + NEEDS_VERIFICATION：任何偏置、协方差、定位误差、覆盖率和实时性数值。

## Related Notes

- [[06-TDOA定位/TDOA]]
- [[06-TDOA定位/TDOA Geometry and Solvers]]
- [[06-TDOA定位/TDOA Geometry Quality]]
- [[06-TDOA定位/TDOA Robust Estimation]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[07-多站协同/Multi-Station Synchronization]]
