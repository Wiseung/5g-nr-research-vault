---
title: Multi-Station Observation Fusion
aliases:
  - 多站观测融合
  - TDOA 输入观测包
  - 站点观测束
type: implementation-contract
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/multi-station
  - topic/tdoa
  - topic/covariance
  - stage/measurement
source:
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[07-多站协同/Clock Offset and Drift]]"
  - "[[07-多站协同/RF and Digital Delay Calibration]]"
  - "[[07-多站协同/Cross-Station Event Association]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
related:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[06-TDOA定位/TDOA Robust Estimation]]"
  - "[[06-TDOA定位/TDOA Geometry Quality]]"
  - "[[07-多站协同/Synchronization Validation Ledger]]"
---

# Multi-Station Observation Fusion

> [!abstract] 接口边界
> 本页定义如何把多个已关联的单站观测组织成 TDOA 解算输入。它不重新估计单站峰、不选择最终位置，也不把站点数量多误写成观测质量高。

## 1. 一句话定义

多站观测融合是对同一 event_id 的站点观测进行兼容性检查、时基/链路校正、站序固定、差分变换和协方差传播，并输出可回放的 TDOA 输入包。

## 2. 输入和输出

| 类型 | 内容 |
| --- | --- |
| 输入 | station_observation、event association、clock_model、delay calibration、站点坐标、处理配置和质量状态 |
| 输出 | station bundle、reference_station_id、station_order、raw/corrected ToA、TDOA 向量、D 矩阵、协方差、有效站集合、拒绝原因 |

输出包必须能够在不读取最终位置的情况下重建。位置解、残差和几何质量由 06-TDOA 定位层追加生成。

## 3. 最小站点观测束

一个 bundle 至少要固定以下字段：

~~~json
bundle_id: null
event_id: null
config_id: null
signal_kind: null
direction: UL
coordinate_frame: null
reference_plane: null
reference_point: null
reference_station_id: null
station_order: []
observation_ids: []
clock_model_ids: []
calibration_ids: []
toa_raw_seconds: []
toa_corrected_seconds: []
tdoa_seconds: []
tdoa_matrix_ref: null
toa_covariance_ref: null
tdoa_covariance_ref: null
valid_station_ids: []
rejected_station_ids: []
state: unknown
quality_reasons: []
~~~

示例只定义结构，不代表任何字段已有真实数值；空值和状态必须由处理程序生成。

## 4. 合并前的兼容性检查

在构造向量前逐项检查：

| 检查 | 通过要求 | 失败动作 |
| --- | --- | --- |
| 事件 | association_state 至少为 cross_station_matched | 保留候选，不合并 |
| 配置 | cell/carrier/config 和 Release 语义兼容 | 标 config_conflict |
| 方向 | 都是同一 UL 事件或明确的可比较参考 | 标 direction_conflict |
| 参考点 | reference_point、reference_plane 一致 | 标 reference_mismatch |
| 采样 | 实际采样率和重采样版本可解释 | 标 sample_axis_conflict |
| 校准 | clock_model_id、calibration_id 在有效期 | 降级或拒绝 |
| 质量 | ToA、峰策略、协方差和失败原因齐全 | 降权或拒绝 |
| 几何 | 坐标系、单位和站点位置可用 | 标 geometry_input_missing |

兼容性检查结果和版本要进入 bundle；不能只保留一个布尔值。

## 5. raw、corrected 和 used 三种时间

对站点 $i$ 保存：

$$
\tau_i^{raw},\qquad
\tau_i^{clock},\qquad
\tau_i^{used}.
$$

其中：

- $\tau_i^{raw}$：从原始捕获样点和参考点得到的时间；
- $\tau_i^{clock}$：应用时钟偏置/漂移后的时间；
- $\tau_i^{used}$：再应用 RF/数字链路修正并通过质量门后送入差分的时间。

若采用 waveform 域重采样，必须另存新处理版本和群时延；不能把 used 覆盖 raw。若某项修正未知，保持 null 并写入 correction_status。

## 6. 参考站选择

参考站选择是坐标规范和数值条件的一部分：

| 策略 | 优点 | 风险 | 适用记录 |
| --- | --- | --- | --- |
| 固定站点 | 结果容易比较，日志简单 | 参考站失效会影响整包 | 长期回放基线 |
| 质量最佳 | 可避开低 SNR/坏站 | 每次 station_order 可能变化 | 在线动态融合 |
| 几何中心/条件最优 | 可能改善数值条件 | 需要先算几何，逻辑耦合 | 已有可靠坐标 |
| 多参考冗余 | 便于交叉检查 | 差分相关性更复杂 | 验证和诊断 |

无论选择哪种策略，都必须保存 reference_station_id 和完整 station_order。更换参考站时，应通过同一 ToA 向量变换，而不是重新独立估计一套 ToA。

## 7. 差分矩阵

将 $M$ 个 ToA 排成：

$$
\boldsymbol{\tau}
=[\tau_1,\ldots,\tau_M]^T.
$$

以参考站 $r$ 形成独立差分：

$$
\boldsymbol{\Delta\tau}
=\mathbf D_r\boldsymbol{\tau}.
$$

例如站序为 $[1,2,3]$、参考站为 1：

$$
\mathbf D_1=
\begin{bmatrix}
-1&1&0\\
-1&0&1
\end{bmatrix}.
$$

实现应保存矩阵或等价的 pair 列表，并显式记录差分方向。全 pair 可以作为诊断输出，但不能把其重复行当成独立测量。

## 8. 协方差传播

若单站 ToA 协方差为 $\mathbf\Sigma_\tau$，则：

$$
\mathbf\Sigma_\Delta
=\mathbf D_r\mathbf\Sigma_\tau\mathbf D_r^{T}.
$$

共享参考站、公共时钟、共同滤波链和同一参考源会引入非对角项。对角近似可以作为 baseline，但必须标注 covariance_model=diagonal_approximation，并在验证台账中与完整模型比较。

协方差中的每一项都应能追溯到：

- 单站峰/估计器散布；
- 时钟偏置和漂移不确定度；
- RF/数字延迟校准散布；
- 事件关联置信度或错配风险；
- 重采样和插值误差。

没有这些来源时，填写一个很小的标准差会制造虚假的高精度。

## 9. 站点缺失和降级

融合器不应为了满足最少站数而填入假观测。建议区分：

| 情况 | 处理 |
| --- | --- |
| 观测缺失但候选存在 | 保留 missing_station_ids，按现有站集评估 |
| 站点失锁/校准过期 | 从 valid_station_ids 移出，保留原因 |
| 关联歧义 | 不进入默认 TDOA；可作为替代候选包 |
| 协方差奇异 | 退回独立差分或显式广义逆，并标记 |
| 参考站缺失 | 重新选择参考站并生成新 bundle_version |
| 少于几何所需约束 | 输出 insufficient_geometry，不生成位置 |

“少一站仍能运行”是降级能力，不等于结果保持相同精度。

## 10. 时间和资源一致性

跨站融合只比较同一参考定义下的时间。以下情况不能直接合并：

- 一个站以 PRACH RO 起点为参考，另一个站以 FFT window 为参考；
- 一个站使用完整带宽，另一个站使用截断 PRB；
- 一个站使用 strongest peak，另一个站使用 first peak；
- 一个站已补偿群时延，另一个站仍是 raw；
- 不同站点的处理版本改变了采样率或窗口边界。

这些情况可以形成独立候选或做方法对照，但必须在 bundle 中显式列出，不得静默平均。

## 11. 质量门和状态

~~~text
assembled
    -> synchronized
    -> calibrated
    -> covariance_ready
    -> tdoa_ready
    -> handed_to_solver

任意状态 -> degraded
任意状态 -> rejected
~~~

状态说明：

| 状态 | 允许动作 |
| --- | --- |
| assembled | 仅保存观测束 |
| synchronized | 时基字段可比较 |
| calibrated | 校正后的 ToA 可生成 |
| covariance_ready | 可计算带协方差的 TDOA |
| tdoa_ready | 通过关联和物理门，可交解算器 |
| handed_to_solver | 已生成不可变输入快照 |
| degraded/rejected | 只用于诊断或替代分支 |

tdoa_ready 仍不代表位置正确；解算器必须再检查几何 rank、条件数和残差。

## 12. 示例：三站输入包

~~~json
bundle_id: bundle-001
event_id: evt-001
reference_station_id: station-a
station_order:
  - station-a
  - station-b
  - station-c
observation_ids:
  - obs-a
  - obs-b
  - obs-c
toa_raw_seconds:
  - null
  - null
  - null
toa_corrected_seconds:
  - null
  - null
  - null
tdoa_seconds:
  - null
  - null
tdoa_matrix_ref: D-reference-a-v1
toa_covariance_ref: cov-toa-001
tdoa_covariance_ref: cov-tdoa-001
valid_station_ids:
  - station-a
  - station-b
  - station-c
state: assembled
quality_reasons:
  - placeholder_until_run
provenance:
  source_kind: EXPERIMENT
  evidence_status: NEEDS_VERIFICATION
~~~

这个包故意保留空结果，防止模板被误读为运行结果。

## 13. 融合伪代码

~~~text
读取 event_id 候选和 station_observation
    -> 运行配置/参考点/校准兼容性检查
    -> 固定或选择 reference_station_id
    -> 形成 station_order 和 ToA 向量
    -> 保存 raw/corrected 值与 correction status
    -> 由 D 矩阵生成独立 TDOA
    -> 传播 ToA 协方差并检查秩/数值条件
    -> 生成不可变 bundle 快照
    -> 交给 TDOA model/solver，或输出明确降级状态
~~~

融合器不应读取最终位置来决定 event_id 或删站；否则会形成信息泄漏。

## 14. 与鲁棒解算的边界

融合层负责“输入是否兼容、误差如何传播”；[[06-TDOA定位/TDOA Robust Estimation]] 负责“已形成的观测中哪些站应降权或剔除”。若融合层提前根据位置残差删站，需单独记录这是预处理规则，并避免与鲁棒层重复计数。

## 15. 记录版本和不可变性

以下变更必须生成新的 bundle_version：

- 参考站或 station_order 变化；
- 时钟/延迟校准版本变化；
- 峰策略、模板、窗口或有效带宽变化；
- 协方差模型变化；
- 事件关联状态升级或回退；
- 站点加入、退出或坐标修正。

历史 bundle 只读保留；派生位置结果引用具体 bundle_version，而不是只引用 event_id。

## 16. 验证矩阵

| 编号 | 条件 | 重点检查 |
| --- | --- | --- |
| F0 | 三站、同一公共源 | 站序、D 矩阵和符号 |
| F1 | 注入固定偏置 | 校正前后 TDOA 方向 |
| F2 | 注入相关 ToA 误差 | 协方差非对角项传播 |
| F3 | 删除参考站 | 新 bundle_version 和结果可回放 |
| F4 | 多峰/关联歧义 | 替代候选不被静默丢弃 |
| F5 | 换峰策略/带宽 | 处理版本和 reference_point 分离 |
| F6 | 交给几何层 | solver 输入与 bundle 快照一致 |

具体运行结果和阈值写入 [[07-多站协同/Synchronization Validation Ledger]]。

## 17. 证据与状态

- PERSONAL_NOTE：站点束、站序、D 矩阵和协方差接口承接 Observation Event Schema、TDOA Measurement Model 和多站同步笔记。
- STANDARD + partial：标准定位测量角色仅作术语边界；本页是项目内部数据契约。
- HYPOTHESIS + NEEDS_VERIFICATION：动态参考站、缺站降级和关联置信度如何影响最终误差尚无本项目结果。
- EXPERIMENT + NEEDS_VERIFICATION：三站 bundle 和协方差传播尚未由真实代码运行。

## Related Notes

- [[07-多站协同/Multi-Station Synchronization]]
- [[07-多站协同/Clock Offset and Drift]]
- [[07-多站协同/RF and Digital Delay Calibration]]
- [[07-多站协同/Cross-Station Event Association]]
- [[07-多站协同/Synchronization Validation Ledger]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[06-TDOA定位/TDOA Measurement Model]]
- [[06-TDOA定位/TDOA Geometry and Solvers]]
- [[06-TDOA定位/TDOA Robust Estimation]]
