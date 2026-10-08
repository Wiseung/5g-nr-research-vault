---
title: Quality and Uncertainty
aliases:
  - 定位观测量质量与不确定度
  - ToA 误差预算与质量门
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/measurement-quality
  - topic/uncertainty
  - topic/calibration
  - stage/validation
source:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[5G-NR-Positioning/02-PRACH/Timing Estimation]]"
  - "[[02-标准与参考/3GPP/3GPP TR 38.901｜Channel model]]"
related:
  - "[[05-定位观测量/Observation Taxonomy]]"
  - "[[06-TDOA定位/TDOA]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
  - "[[01-专题知识/5G定位/单用户时频截取与定位观测量]]"
---

# Quality and Uncertainty

> [!abstract] 一句话结论
> 质量不是一个分数，不确定度也不是把所有误差相加后的经验常数。定位观测必须把随机噪声、固定偏置、时间漂移、结构性错配和事件关联风险分开记录，并在每个下游门控处说明“为什么可用”或“为什么拒绝”。

## 1. 质量层和不确定度层

质量回答“这条观测是否满足某个用途的输入条件”；不确定度回答“在明确模型和假设下，数值可能偏离多少”。两者不能互相替代：

| 情况 | 可能的质量/不确定度关系 |
| --- | --- |
| 峰很高但参考点未知 | 质量只能为 C 或 pending；绝对时间不确定 |
| 峰很低但单径和校准完备 | 可能可用，但方差较大 |
| 误差很小但有未发现碰撞 | 数值不确定度低估，结构性风险高 |
| 多站 TDOA 残差小但站点共线 | 测量可能一致，几何可观测性仍差 |

每个 quality.state 都应绑定用途：事件触发、单站诊断、TDOA 候选或最终位置，而不是只有一个全局 valid/invalid。

## 2. 误差分类

### 2.1 随机误差

典型来源是热噪声、ADC 量化、随机干扰、有限相关积累和估计器随机性。它们通常可以通过重复试验估计方差或分位数，但估计方法、样本数和噪声口径必须写入日志。

### 2.2 系统偏置

典型来源是：

- 捕获起点、FFT 窗或 RO 参考点定义；
- 天线、线缆、RF、ADC 和数字下变频固定延迟；
- 滤波器群时延和不同带宽；
- 本地时钟相对公共时间基准的固定偏置；
- 阵列相位中心和端口映射。

系统偏置不能用增加样本数消除；应通过校准、差分或显式参数建模。

### 2.3 漂移误差

采样时钟 ppm、载频温漂、PPS/PTP 重锁、设备温度和长时间缓存会造成随时间变化的误差。对观测时刻 t，可用工程模型表示：

$$
b_i(t)=b_{i,0}+\alpha_i(t-t_0)+\eta_i(t),
$$

其中 b_i,0 是固定偏置，alpha_i 是漂移项，eta_i 是未建模残差。alpha_i 不应被塞进一次测量的随机标准差。

### 2.4 结构性错误

资源掩码错位、方向判定错误、参考序列错配、端口/层错配、碰撞、NLOS、重传误合并和错误跨站关联都属于结构性风险。它们可能产生看似平滑、但物理意义错误的观测，必须用状态和负例显式暴露。

## 3. 统一误差模型

对站 i 的时间观测，可写成：

$$
\widehat{\tau}_i
=\tau_i^{prop}
+b_i^{clock}
+d_i^{RF}
+d_i^{filter}
+d_i^{digital}
+e_i^{est}
+e_i^{multipath}
+e_i^{association}.
$$

其中各项的单位均为秒。对频率、功率和角度观测也应使用类似的“物理量 + 校准项 + 估计误差 + 结构风险”分解。若某项尚未测量，保存 null 并降低状态，不要默认为 0。

独立误差项的平方和只可作近似：

$$
\sigma_\tau^2\approx
\sum_q\sigma_q^2.
$$

如果多个站共享参考时钟、滤波器或参考站，误差项会相关，应使用协方差矩阵而不是简单逐项相加。

## 4. 时间观测质量指标

### 4.1 峰和相关质量

| 指标 | 计算对象 | 解释 | 需要警惕 |
| --- | --- | --- | --- |
| peak_power | 选中峰或峰簇 | 候选强度 | 强峰不一定是首径 |
| noise_floor | 保护区外训练窗 | 噪声/干扰基线 | 训练窗污染会虚高质量 |
| peak_to_floor_db | 峰与基线 | 检测可分性 | 归一化和带宽需固定 |
| peak_width_samples | 主峰宽度 | 模板/多径/滤波诊断 | 不能直接等于标准差 |
| pslr_db | 主峰与旁瓣 | 峰可辨识度 | 碰撞和多径会改变旁瓣 |
| neighbor_gap_samples | 与邻峰间距 | 峰分离程度 | 周期相关要先 unwrap |
| first_strongest_delta | 首径和最强峰差 | 多径/NLOS 风险 | 首径定义需固定 |

### 4.2 参考和一致性质量

- 参考序列匹配残差和模板版本；
- 资源掩码覆盖率、非法 RE 比例和方向一致率；
- 多天线峰位置/相位一致性；
- 同一事件重复观测的时间差；
- 多站校准后 TDOA 残差和被剔除站比例；
- 相关器、相位斜率和模板拟合等独立方法之间的差异。

这些指标应保存原始值和聚合值。只保留一个 confidence 分数无法知道失败来自信号、资源、同步还是关联。

## 5. 频率、功率和空间质量

### 5.1 频率质量

| 指标 | 记录方式 | 失效提示 |
| --- | --- | --- |
| cfo_hz | 估计值、搜索网格、残差 | CFO 假设不稳定 |
| residual_cfo_hz | 补偿后估计 | 仍有明显相位旋转 |
| sample_rate_offset_ppm | 跨块拟合斜率 | ToA 随时间漂移 |
| phase_fit_residual | 相位斜率拟合残差 | 频率选择性/多径/缠绕 |
| coherence_across_reference | 参考间相位/相关一致性 | 不能把频偏解释成 Doppler |

### 5.2 功率质量

功率指标必须绑定域和窗口：ADC 样点、RF 校准功率、RE 平均功率、参考峰功率不是同一个量。SNR 与 SINR 的分母也必须区分噪声和邻用户干扰。标准名称 RSRP/RSRQ 的精确口径需按 38.215 和目标 Release 外部核验。

### 5.3 空间质量

对阵列观测，应记录：

- 天线通道是否齐全、是否有饱和/掉线；
- 阵元幅相校准版本；
- 空间谱峰、峰宽和旁峰；
- 多径下的角度候选数和稳定性；
- 阵列坐标系、波束索引和相位参考。

未校准阵列可以输出相对相位或诊断特征，但不得把它标为绝对 AoA。

## 6. 校准账本

校准记录至少包含：

| 项目 | 字段 |
| --- | --- |
| 对象 | station_id、channel_id、antenna_id |
| 条件 | frequency_hz、bandwidth_hz、sample_rate_hz、filter_profile、temperature |
| 参考面 | 天线端、线缆端、RF 输入端、ADC 或数字输出端 |
| 方法 | 回环、线缆直连、公共参考源、PPS/PTP 或其他 |
| 结果 | delay_seconds、phase_offset_rad、sample_rate_offset_ppm、std/协方差 |
| 版本 | calibration_id、measured_at、valid_from、valid_to |
| 失效 | 重锁、温度超限、频段/带宽不匹配、设备链变化 |

校准方程可以写成：

$$
\tau_i^{corr}
=\tau_i^{raw}
-d_i^{RF}
-d_i^{filter}
-d_i^{digital}
-b_i^{clock}(t).
$$

正负号是项目约定，必须和校准装置的传播方向一致。校准表不能只写一个“已校准”布尔值。

## 7. 质量等级与用途门

以下等级是项目工程门，不是 3GPP 合规等级：

| 等级 | 最低条件 | 允许用途 | 禁止用途 |
| --- | --- | --- | --- |
| A | 资源/方向/参考闭合；校准在有效期；峰策略和协方差可回放 | TDOA 候选、位置解算 | 无 |
| B | 单站时间闭合，部分校准或不确定度上界可追溯 | 单站诊断、加权候选 | 无校准的绝对距离结论 |
| C | 只有峰/能量或参考点不完整 | 事件触发、负例统计 | 最终 TDOA/位置 |
| invalid | 窗口截断、参考错配、通道失效或关联冲突 | 证据留存、故障统计 | 任何数值融合 |

等级判定必须依赖质量配置版本和用途；同一观测对事件触发可以是 A，对绝对 ToA 可能只有 B。

## 8. 状态和拒绝原因

推荐把质量状态拆成可组合标签：

~~~text
resource_unknown
reference_unknown
window_truncated
template_mismatch
peak_ambiguous
collision_suspected
multipath_suspected
cfo_unresolved
sample_rate_unresolved
calibration_missing
clock_unreliable
array_uncalibrated
event_link_ambiguous
geometry_poor
tdoa_usable
~~~

一个记录可以同时拥有多个原因，例如 toa_valid + multipath_suspected；不要用单一枚举覆盖所有信息。详细字段见 [[05-定位观测量/Observation Event Schema]]。

## 9. 不确定度估计方法

### 9.1 合成真值

在已知整数/分数延迟、CFO、SNR 和多径参数的合成波形上，计算：

$$
e_q=\widehat{\tau}_q-\tau_{true,q},
\qquad
\widehat{\sigma}^2
=\frac{1}{N-1}\sum_q(e_q-\bar e)^2.
$$

必须报告偏差、RMSE、分位数、样本数和随机种子；这只验证算法在指定模型下的表现。

### 9.2 重复采集或回环

对同一已知参考进行重复采集，区分：

- 重复测量的随机散布；
- 估计器固定偏差；
- 站点/链路之间的固定差；
- 温度、频率和时间变化造成的漂移。

回环结果不能自动代表空口多径；空口和校准数据应分开标识。

### 9.3 拟合残差和 bootstrap

模板拟合、相位斜率或重复峰轨迹可以给出内部不确定度，但必须记录模型、权重、残差和有效样本。峰宽只能作诊断，不能未经验证直接当作标准差。

## 10. 协方差传播

把 m 个站的 ToA 组成 tau，以参考站差分矩阵 D 构造：

$$
\boldsymbol{\Delta\tau}=\mathbf D\boldsymbol{\tau},
\qquad
\mathbf\Sigma_\Delta
=\mathbf D\mathbf\Sigma_\tau\mathbf D^{T}.
$$

若位置约束函数为 g(x)，在估计点 x_hat 附近线性化：

$$
\delta\mathbf z\approx\mathbf J\,\delta\mathbf x+\boldsymbol\epsilon,
\qquad
\mathbf\Sigma_x
\approx(\mathbf J^{T}\mathbf W\mathbf J)^{-1},
\quad
\mathbf W=\mathbf\Sigma_\Delta^{-1}.
$$

这只是局部线性近似；非线性、多解、NLOS 和错误关联需要另外报告。GDOP 或位置协方差不能掩盖错误的事件配对。

## 11. 验证矩阵

| 编号 | 固定/注入因素 | 观察指标 | 通过条件 |
| --- | --- | --- | --- |
| Q0 | 无噪声、单径、已知整数延迟 | 索引和符号闭合 | 无未解释的常数偏差 |
| Q1 | 分数延迟扫描 | bias、RMSE、插值失败率 | 方法和边界状态可复现 |
| Q2 | AWGN/SNR 扫描 | 峰质量、置信区间覆盖 | 低质量样本能降级 |
| Q3 | CFO 扫描 | 峰漂移、残余相位 | 补偿状态和残差一致 |
| Q4 | 采样率 ppm/长窗口 | ToA 漂移 | 可识别 drift，不混入随机误差 |
| Q5 | 多径/NLOS | first/strongest/cluster 差异 | 保留多峰和风险标签 |
| Q6 | PRACH 碰撞/MU-MIMO | 峰簇和关联错误率 | 不强制生成唯一 UE |
| Q7 | 滤波/带宽改变 | raw/corrected 偏差 | 群时延账本闭合 |
| Q8 | 站间公共源/回环 | 固定延迟和协方差 | calibration_id 可回放 |
| Q9 | 三站/四站几何 | TDOA 残差、GDOP、有效站率 | 坏站被显式剔除 |
| Q10 | 现场连续采集 | 失锁、丢样、尾延迟 | 失败原因可统计 |

所有 Q0-Q10 在运行前都只是实验设计；不要把预期通过条件写成实测结果。

## 12. 报告模板

一次质量报告至少包含：

~~~json
run_id: null
quality_config_id: null
capture_ids: []
config_ids: []
calibration_ids: []
event_count: null
observation_count: null
grade_counts:
  A: null
  B: null
  C: null
  invalid: null
state_counts: {}
metrics:
  toa_bias_seconds: null
  toa_rmse_seconds: null
  tdoa_rmse_seconds: null
  confidence_coverage: null
  valid_station_ratio: null
  p95_processing_latency_ms: null
failure_reasons: []
evidence_status: NEEDS_VERIFICATION
~~~

没有真值时，toa_bias、RMSE 和 coverage 应保持 null，只报告内部一致性、峰统计和失败分布。

## 13. 常见错误

1. 用峰值功率替代时间质量。
2. 把校准缺失写成零延迟。
3. 用单次回环结果覆盖不同频率、带宽或温度。
4. 以同一参考站形成多个差分，却把协方差设成对角矩阵。
5. 用低残差证明事件一定属于目标 UE。
6. 把仿真真值、标准测量和现场估计放在同一结果列。
7. 只保留通过样本，删除被拒绝样本和拒绝原因。

## 14. 证据与限制

- PERSONAL_NOTE：本项目的质量等级、拒绝状态、校准账本和报告字段。
- STANDARD + partial：TS 38.211/38.214 的资源、参考信号和数据接口；TR 38.901 的传播/多径仿真边界。
- STANDARD + partial：TS 38.215/38.305 的测量和定位术语入口，精确参考点、误差要求和 Release 差异仍需外部核验。
- EXPERIMENT + NEEDS_VERIFICATION：Q0-Q10、任何阈值、置信区间、现场精度和实时尾延迟。
- HYPOTHESIS + NEEDS_VERIFICATION：以 PRACH/PUSCH/SRS 参考形成定制被动 UL-TDOA 的质量门和峰策略。

## 15. Related Notes

- [[05-定位观测量/Observation Taxonomy]]
- [[05-定位观测量/Standard Positioning Observables]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Observation Event Schema]]
- [[02-PRACH/Timing Estimation]]
- [[06-TDOA定位/TDOA]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[09-采数实验/Capture Experiment Checklist]]
