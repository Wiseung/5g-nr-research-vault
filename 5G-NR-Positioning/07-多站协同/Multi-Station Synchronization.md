---
title: Multi-Station Synchronization
aliases:
  - 多站同步与校准
  - 站间时间基准
type: atomic
status: partial
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/synchronization
  - topic/calibration
source:
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - 用户项目第三阶段要求
related:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[06-TDOA定位/TDOA]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
  - "[[07-多站协同/Clock Offset and Drift]]"
  - "[[07-多站协同/RF and Digital Delay Calibration]]"
  - "[[07-多站协同/Cross-Station Event Association]]"
  - "[[07-多站协同/Multi-Station Observation Fusion]]"
  - "[[07-多站协同/Synchronization Validation Ledger]]"
---

# Multi-Station Synchronization

## 1. 一句话定义

多站同步是让各接收站的采样时间、频率、RF/数字链路延迟和事件时间戳进入同一可校准坐标系，而不只是让设备“同时启动”。

## 2. 为什么项目需要它

TDOA 对纳秒/样点级偏差敏感；站间公共时钟、PPS/PTP、触发、线缆、滤波和采样率误差会直接表现为系统性位置偏差或漂移。

## 3. 它位于整个 5G 空口链路的什么位置

它位于各站独立的 [[05-定位观测量/Timing Observation]] 与 [[06-TDOA定位/TDOA]] 之间，并贯穿采数、预处理和事件关联。

## 4. 输入

站点硬件信息、时钟源和锁定状态、PPS/PTP/触发时间戳、采样率、中心频率、线缆/RF/滤波/数字下变频链路、校准样本和站点坐标。

## 5. 输出

每站时钟偏置/漂移模型、RF/数字固定延迟、采样率偏差 ppm、校准版本、有效时间范围和 `sync_quality`。

## 6. 关键参数

参考时钟类型、PPS/PTP 状态、触发延迟、ADC 时间戳定义、采样率误差、温度、滤波器群时延、天线/线缆长度、重采样策略和参考站。

## 7. 时域位置

校准必须覆盖真实捕获窗口和目标事件时间尺度；固定偏置与随时间变化的漂移分开建模，不能用一次启动时间差代替长时间采集的时基。

## 8. 频域位置

不同站点的数字下变频、抽 decimation、滤波带宽和频率偏移会改变群时延及相关峰；校准记录必须绑定中心频率、采样率和滤波配置。

## 9. 数学原理

可将站点时间写成：

$$
t_i^{obs}=t_i^{true}+b_i+\alpha_i(t-t_0)+d_i+\epsilon_i,
$$

其中 $b_i$ 是固定钟差，$\alpha_i$ 是采样率/时钟漂移项，$d_i$ 是 RF/数字固定延迟。TDOA 前需估计或约束这些项，并保留残差。

## 10. 3GPP 对应规范

- TS 38.215：物理层测量参考和时间精度边界（精确 clause 待核对）。
- TS 38.305：定位架构对同步/测量的功能边界。
- TS 38.455：定位接口携带的测量/协同信息边界；第三方采集链路不等同标准接口。

当前没有项目硬件校准标准文本，具体误差预算标记 `NEEDS_EXTERNAL_REFERENCE` 或 `NEEDS_VERIFICATION`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

基础 MATLAB 可用 `resample`、`interp1`、`xcorr` 和线性回归估计采样率偏差/固定延迟；硬件时钟/PPS/PTP 控制不由 5G Toolbox API 完成，需设备 SDK 或采集系统接口，当前为 `NEEDS_EXTERNAL_REFERENCE`。

## 12. 本项目中的用途

在每站输出 ToA 之前先应用版本化校准，给 TDOA 求解器提供站点级偏置、漂移和质量；任何未锁定时钟或缺失 RF 延迟的事件都保留为不可用，而不是静默参与定位。

## 13. 常见误区

- 把启动时间相同当作样点同步。
- 只校准时钟而忽略天线、线缆、滤波器和抽 decimation 延迟。
- 用一个 ppm 常数覆盖温漂和长时间漂移。
- 校准样本的带宽/中心频率与实际观测不一致。

## 14. 与相似概念的区别

- 频率同步控制载波/采样速率；时间同步控制时间基准；二者误差表现不同。
- 设备内部 frame/slot 对齐不等于站间绝对时间对齐。
- 事件关联是软件配对问题；同步校准是测量坐标问题。

## 15. 代码实现注意事项

所有校准参数带 `calibration_id` 和有效时间；用已知公共源/线缆回环做重复测量；把固定偏置、漂移、随机误差分列；禁止覆盖原始时间戳和原始 IQ。

## 16. 待实验验证的问题

- 公共时钟/PPS/PTP/独立时钟方案的固定偏置与漂移。
- 频率、带宽、滤波器和抽取倍率变化对群时延的影响。
- 温度和采集时长对 ppm 漂移模型的影响。
- 校准前后同一事件的 TDOA 残差与位置误差。

## 17. Related Notes

- [[05-定位观测量/Timing Observation]]
- [[06-TDOA定位/TDOA]]
- [[09-采数实验/Capture Experiment Checklist]]
- [[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]

## 证据与状态

- `PERSONAL_NOTE`：现有多站 UL-TDOA 校准清单。
- `EXPERIMENT + NEEDS_VERIFICATION`：硬件同步方案和数值误差尚无本项目实测。

## 18. 多站协同的四个独立层

“同步”不是一个开关，而是四个需要分别验收的层：

| 层 | 解决的问题 | 最小证据 | 失败时的下游状态 |
| --- | --- | --- | --- |
| 时间基准 | 各站时间戳是否可比较 | 时钟源、锁定日志、偏置/漂移模型 | `clock_unreliable` |
| 采样坐标 | 样点和秒是否保持一致 | 实际采样率、ppm、重采样版本 | `sample_rate_unresolved` |
| 链路延迟 | 参考面到数字输出的固定/频变延迟 | 回环或公共源校准表 | `calibration_missing` |
| 事件关联 | 各站是否看到同一个物理事件 | event_id 证据和候选日志 | `event_link_ambiguous` |

只有四层都通过，才允许把单站观测组成 TDOA 向量。`sync_quality=good` 不能替代四层字段，也不能由设备启动成功自动生成。

## 19. 站点协同数据流

~~~text
站点元数据与配置快照
    ↓
时钟源/锁定状态与原始时间戳
    ↓
样点坐标闭合、丢样检测、必要的重采样
    ↓
RF/天线/线缆/数字滤波延迟修正
    ↓
单站 raw_toa、校正 toa、峰轨迹和质量
    ↓
跨站事件候选与关联证据
    ↓
站点顺序、参考站、TDOA 向量和协方差
    ↓
[[06-TDOA定位/TDOA Geometry and Solvers]]
~~~

每一步都应追加新记录，不覆盖前一步的 raw 值。若校准或关联失败，仍保留失败记录和原始特征，供 [[06-TDOA定位/TDOA Validation Ledger]] 回放。

## 20. 时基方案的选择框架

| 方案 | 能直接约束 | 主要残余风险 | 适合的第一版证据 |
| --- | --- | --- | --- |
| 共享参考时钟 + 外部触发 | 频率和触发相位 | 线缆/输入延迟、重锁 | 公共源/线缆回环 |
| 共享 PPS + 各站本地时钟 | 秒边界和粗时间 | PPS 到 ADC 的固定差、短期漂移 | PPS 日志 + 回环 |
| PTP 或同类网络授时 | 软件/网络时间 | 网络抖动、硬件时间戳能力 | 时间戳对照 + 稳态/断链 |
| 独立时钟 + 后处理 | 统计意义上的相对时间 | 长期漂移和不可辨识偏置 | 已知位置多事件 |
| 仅按启动时刻对齐 | 进程启动顺序 | 几乎所有采样和链路误差 | 不可作为定位证据 |

该表是项目工程决策框架，不是对某一同步协议性能的标准结论。PPS/PTP 的精确能力、硬件时间戳语义和设备接口标记 `NEEDS_EXTERNAL_REFERENCE`。

## 21. 校准版本与有效期

一个校准快照至少绑定：

~~~json
calibration_id: null
station_id: null
channel_id: null
reference_plane: null
frequency_hz: null
bandwidth_hz: null
sample_rate_hz: null
filter_profile: null
temperature_c: null
clock_source: null
measured_at: null
valid_from: null
valid_to: null
status: unknown
~~~

`valid_to` 不能留空后被解释为永久有效。发生重锁、换线、修改数字滤波、采样率变化或温度超出验证范围时，应关闭旧快照并生成新版本。`calibration_id` 的版本变化不应改变历史记录的含义。

## 22. 站点时间戳的最小闭合关系

跨站比较前，至少能从日志复原捕获起点、窗口起点、局部峰索引和分数样点，并明确它们如何闭合为捕获坐标：

$$
n_{\mathrm{peak,capture}}
 =
n_{\mathrm{capture,start}}
 + n_{\mathrm{window,start}}
 + n_{\mathrm{peak,local}}
 + \delta_{\mathrm{frac}}.
$$

再用实际处理链采样率换算：

$$
t_{\mathrm{raw}}
 = \frac{n_{\mathrm{peak,capture}}-n_{\mathrm{reference}}}{F_{s,\mathrm{effective}}}.
$$

若发生重采样，$F_{s,\mathrm{effective}}$、重采样滤波器版本和附加群时延必须写入处理快照；不能只把采样率字段改成目标值而丢失原始坐标。

## 23. 校准应用顺序与符号

本项目采用“观测值减去已估计偏置”的显式约定：

$$
t_i^{corr}
 =
t_i^{raw}
 - \widehat b_i(t_e)
 - \widehat d_i(f,B,\mathcal F).
$$

实施时分为两个可审计阶段：

1. **样点/时基阶段**：完成索引 unwrap、采样率偏差处理和时钟偏置修正。
2. **参考面阶段**：减去天线、线缆、RF、ADC、数字下变频、抽取和滤波延迟。

若设备 SDK 或校准装置使用“信号到达时间增加为正”的相反定义，必须在适配层转换并记录 `sign_convention`。禁止以“校准后看起来更接近”来反推符号。

## 24. 进入 TDOA 的组合门

建议把组合门写成可解释的逻辑，而不是单个总分：

~~~c
resource_compatible
  AND reference_point_equal
  AND sample_rate_known
  AND calibration_valid
  AND clock_state_acceptable
  AND event_association >= cross_station_matched
  AND covariance_available
  AND geometry_precheck_pass
~~~

任一条件不满足时，输出可以是 `cross_station_candidate` 或 `calibrated_pending`，但不能标 `tdoa_usable`。门限数值由实验台账预注册；当前没有本项目实测门限。

## 25. 失效分类

| 现象 | 优先检查 | 不应做的解释 |
| --- | --- | --- |
| 所有站固定同向偏移 | 参考面、线缆和滤波延迟 | 直接归因于 UE 移动 |
| TDOA 随时间线性变化 | 采样率 ppm、时钟漂移、重采样 | 用单次固定偏置掩盖 |
| 只在某带宽/频点变化 | 频率相关群时延、滤波配置 | 认为是随机噪声 |
| 单站峰正常、跨站不闭合 | event_id 错配、RO/资源不同 | 只按最近时间强行合并 |
| 重锁后跳变 | 锁定状态和分段边界 | 把跳变平滑掉不留记录 |
| 位置解边界发散 | 站点几何或协方差 | 把求解器收敛当作准确 |

## 26. 与各层笔记的分工

| 本页 | 专门页 |
| --- | --- |
| 总体架构、层级和进入门 | [[07-多站协同/README]] |
| 时钟偏置、漂移和重锁分段 | [[07-多站协同/Clock Offset and Drift]] |
| RF/数字链路和参考面延迟 | [[07-多站协同/RF and Digital Delay Calibration]] |
| 同一事件的跨站候选与状态机 | [[07-多站协同/Cross-Station Event Association]] |
| TDOA 输入包和协方差接口 | [[07-多站协同/Multi-Station Observation Fusion]] |
| 回环、漂移和端到端验收 | [[07-多站协同/Synchronization Validation Ledger]] |

## 27. 当前可执行的最小闭环

在真实网络配置尚未锁定时，先用一个已知公共源、三站二维坐标和固定处理链完成：

1. 同时记录三站原始 IQ、采样率、时间戳和锁定状态。
2. 生成一条 `calibration_id`，明确参考面、频率、带宽和滤波器。
3. 对同一已知事件输出全峰轨迹、raw ToA、校正 ToA 和协方差。
4. 用事件关联页确认站点顺序，再生成独立 TDOA。
5. 将残差与校准台账绑定；任何空值保持 `null`，不补零。

这只是验证链路闭合的最小实验，不代表现场定位精度或标准 UL-TDOA 合规。

## 28. 证据与状态（扩展）

- `PERSONAL_NOTE`：四层协同结构、字段和状态门是本项目工程契约，承接既有 UL-TDOA、观测 Schema 和采数清单。
- `STANDARD + partial`：TS 38.215/38.305 仅用于标准测量和定位角色边界；精确参考点、报告字段和 Release 差异仍需核对。
- `HYPOTHESIS + NEEDS_VERIFICATION`：不同时基方案的相对适用性、漂移模型和门限尚无本项目实测。
- `EXPERIMENT + NEEDS_VERIFICATION`：第 27 节闭环尚未运行，不得填写偏置、RMSE 或位置结果。
