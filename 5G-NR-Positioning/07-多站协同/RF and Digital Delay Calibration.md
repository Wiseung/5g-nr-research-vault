---
title: RF and Digital Delay Calibration
aliases:
  - 射频与数字链路延迟校准
  - 参考面延迟
  - 群时延校准
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/calibration
  - topic/rf-delay
  - topic/group-delay
source:
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
related:
  - "[[07-多站协同/Clock Offset and Drift]]"
  - "[[07-多站协同/Multi-Station Observation Fusion]]"
  - "[[07-多站协同/Synchronization Validation Ledger]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
---

# RF and Digital Delay Calibration

> [!abstract] 参考面边界
> 本页把“相关峰相对哪个物理端点”以及“接收链增加了多少时间”拆开记录。它是项目校准契约，不是某个采集设备的规格书；设备内部延迟、校准接口和绝对数值均需外部资料或实测确认。

## 1. 一句话定义

RF/数字延迟校准是在固定参考面、频率、带宽、采样率和处理链条件下，估计每个站从信号进入天线/射频端到输出数字样点之间的固定及频率相关时间偏移，并给出有效期和不确定度。

## 2. 为什么不能只校准时钟

即使各站共享同一个频率和 PPS，天线、馈线、连接器、滤波器、ADC、数字下变频、抽取和相关窗口仍可能产生不同延迟。此类差异在 TDOA 中看起来像传播距离差。反过来，只减去一个“硬件延迟”而不记录频率和滤波配置，也可能把群时延变化误当成随机噪声。

## 3. 延迟分解

对站点 $i$ 和通道 $m$，工程模型可写为：

$$
d_{i,m}(f,B,\mathcal F,T)
=d^{ant}_{i,m}
+d^{cable}_{i,m}
+d^{RF}_{i,m}(f)
+d^{ADC}_{i,m}
+d^{DDC}_{i,m}(f)
+d^{dec}_{i,m}
+d^{filter}_{i,m}(f,\mathcal F)
+d^{window}_{i,m}.
$$

各项未必能在设备层面单独辨识，因此记录时可以保存“总延迟”和可拆分的子项，但不能把估计总延迟重复加上每个子项。

## 4. 参考面

| reference_plane | 适用语义 | 常见遗漏 |
| --- | --- | --- |
| antenna_terminal | 天线连接器或阵列端口 | 天线相位中心、馈线和连接器 |
| cable_input | 校准线缆输入端 | 天线和现场馈线 |
| rf_input | 接收机 RF 输入 | 前端滤波、增益级和开关 |
| adc_sample | ADC 采样边界 | 模拟群时延和采样触发 |
| digital_output | 数字下变频/抽取输出 | DDC、抽取和滤波 |
| correlation_reference | 相关器定义的模板起点 | 模板生成和窗口约定 |

跨站 ToA 只有在 reference_plane 和 reference_point 一致时才可直接相减。把一个站的 antenna_terminal 值和另一个站的 digital_output 值放进同一 TDOA，是结构性错误而不是可由求解器修正的噪声。

## 5. 群时延和相位斜率

若链路频率响应为 $H(f)=|H(f)|e^{j\phi(f)}$，局部群时延可用相位斜率定义：

$$
\tau_g(f)=-\frac{1}{2\pi}\frac{\mathrm d\phi(f)}{\mathrm df}.
$$

离散测量应先做相位解缠并记录频率网格、拟合区间和权重。该定义描述线性系统的频率响应斜率；它不等同于任意相关峰位置，也不保证在宽带、多径或非线性设备中只有一个可用延迟。

对项目使用的有效子载波集合 $\mathcal K$，可把相位斜率拟合作为一个有效延迟候选：

$$
\phi_k \approx \phi_0-2\pi f_k d_{\mathrm{eff}}+\nu_k.
$$

$d_{\mathrm{eff}}$ 必须绑定 $\mathcal K$、带宽、滤波器和参考面；换用另一组 PRB 或另一采样率时应重新验证。

## 6. 校准方法对照

| 方法 | 连接方式 | 能覆盖 | 主要限制 |
| --- | --- | --- | --- |
| 线缆直连/回环 | 同一参考源分配到各站 | 固定链路和短期重复性 | 不包含天线与空口传播 |
| 功分器公共源 | 同源同刻度多路输出 | 站间相对差、幅相 | 分配网络自身要校准 |
| 天线端公共源 | OTA 同一已知发射 | 天线/馈线/现场路径 | 空间多径和遮挡 |
| 已知位置移动源 | 多位置、多时刻 | 端到端模型残差 | 依赖几何和事件关联 |
| 内部测试脉冲 | 设备自检路径 | 设备内重复性 | 未必代表外部输入到 ADC |

第一版建议先做线缆/公共源基线，再用天线端或已知位置样本验证是否存在参考面差异。校准结果不应跨方法直接平均。

## 7. 线缆与公共源校准流程

1. 固定站点通道、频率、带宽、采样率和数字滤波配置。
2. 等待时钟锁定和热状态稳定，记录锁定日志与环境变量。
3. 用同一参考源向各站输入已知序列或脉冲，保存原始 IQ。
4. 对每站用同一模板、同一窗口和同一峰策略估计峰位置。
5. 以选定参考站计算相对延迟，保留全峰轨迹而非只保留最大峰。
6. 更换线缆端口或交换站点顺序做对称性检查，识别线缆与设备项。
7. 重复多次并估计均值、散布、异常样本和校准不确定度。
8. 生成带 valid_from/valid_to 的 calibration_id，并记录处理版本。

步骤 6 是识别连接器/线缆错误的工程检查，不是自动消除误差；交换后若结果不闭合，应保留冲突记录。

## 8. 频率和带宽扫描

至少把以下条件作为独立维度记录：

- 中心频率和实际占用频带；
- 有效带宽、PRB/子载波掩码；
- 采样率、抽取倍率和数字下变频配置；
- FIR/IIR 配置、群时延补偿和边界处理；
- 天线/通道、增益和温度。

若延迟随频率变化，可用分段线性或查表表示，但只有在扫描数据支持时才建立模型。不能用单点校准外推到整段宽带并称为“已校准”。

## 9. 延迟符号和方向

本项目默认把信号经过链路增加的时间写成正延迟，并在校正时减去：

$$
t_i^{corr}=t_i^{raw}-\widehat d_i.
$$

校准装置若输出的是“参考到达减去被测到达”，符号相反；适配层需要保存：

~~~json
sign_convention: arrival_plus_or_minus
measurement_direction: reference_to_station
correction_operation: subtract_or_add
~~~

不要凭“位置更合理”反推符号。应使用已知延迟线或交换端口的方向性试验确定。

## 10. 与时钟偏置的分离

统一的单站观测可以写成：

$$
\widehat{\tau}^{raw}_i
=\tau^{prop}_i+b^{clock}_i(t)+d^{chain}_i(f,B,\mathcal F)+e_i.
$$

公共源回环主要观察 $b^{clock}_i+d^{chain}_i$ 的合成差；若要分别估计时钟和链路，必须引入外部时间标签、频率扫描、已知参考面或额外实验。将合成差直接命名为 clock_bias 会让后续换处理链时发生重复修正。

## 11. 校准记录模板

~~~json
calibration_id: null
station_id: null
channel_id: null
reference_plane: null
reference_point: null
method: cable_loopback_or_common_source_or_ota
source_id: null
frequency_hz: null
bandwidth_hz: null
active_resource_mask: null
sample_rate_hz: null
ddc_profile: null
filter_profile: null
temperature_c: null
delay_seconds: null
delay_std_seconds: null
phase_slope_delay_seconds: null
sign_convention: null
measured_at: null
valid_from: null
valid_to: null
processing_run_id: null
status: unknown
failure_reasons: []
~~~

delay_seconds 和 phase_slope_delay_seconds 不是同一个字段；前者可能来自时域峰，后者来自频域相位拟合。两者不一致时，保留差异并将原因标为待解释。

## 12. 校准质量和不确定度

建议至少记录：

| 指标 | 解释 |
| --- | --- |
| repeatability_std | 同条件重复测量散布 |
| fit_residual_std | 模型拟合残差 |
| port_swap_residual | 交换端口后的闭合误差 |
| frequency_slope | 延迟随频率的趋势候选 |
| valid_sample_count | 用于估计的有效重复次数 |
| outlier_count | 被拒绝的样本数及规则 |

这些指标描述校准实验的不确定度，不等同于空口 ToA 误差。空口多径、NLOS、CFO 和事件错配应在 [[05-定位观测量/Quality and Uncertainty]] 中另列。

## 13. 何时使校准失效

发生以下情况之一时，旧校准默认降级：

- 频率、带宽、采样率、资源掩码或滤波配置变化；
- 天线、线缆、连接器、衰减器或 RF 前端变化；
- 通道映射、增益路径或数字下变频变化；
- 设备重锁、重启、时间戳回绕或固件变化；
- 温度超出校准覆盖范围；
- 校准残差超出预注册门限；
- 参考面或峰策略改变。

门限由验证台账预注册；当前没有本项目实测阈值。

## 14. 处理链中的应用位置

推荐保留以下四种值：

~~~text
raw_peak_sample
    -> raw_toa_seconds
    -> clock_corrected_toa
    -> chain_corrected_toa
    -> tdoa_used
~~~

每一步都带处理版本和状态。若在 waveform 域做滤波/重采样，必须把新增群时延写入新版本；若在 timestamp 域修正，则保留原始样点索引。禁止把 correction 后的结果覆盖 raw 字段。

## 15. 多天线和多通道

阵列的每个通道都应有独立的 channel_id 和 reference_plane。通道间延迟差会影响波束、相位差和多站 ToA，不能只给一个 station-level 常数。若项目只使用单通道，也应记录未使用通道的状态，避免通道重排后静默改变含义。

## 16. 失败诊断矩阵

| 症状 | 候选原因 | 证据动作 |
| --- | --- | --- |
| 所有频点同一偏移 | 固定线缆/参考面差 | 回环、端口交换 |
| 只在带宽边缘变化 | 滤波器群时延/频响 | 频率扫描、相位拟合 |
| 换采样率后跳变 | DDC/抽取路径不同 | 保存处理链快照 |
| 时域峰和相位斜率不一致 | 多径、相位解缠或模板差异 | 保留双方法残差 |
| 设备重启后偏移变化 | 时间戳或锁定状态 | 分段并生成新 calibration_id |
| 单站校准正常、跨站异常 | event_id 错配或站间时基问题 | 转到事件关联/时钟页 |

## 17. 与观测融合的接口

进入 [[07-多站协同/Multi-Station Observation Fusion]] 时，应提供：

- calibration_id、reference_plane、frequency/bandwidth/filter 条件；
- raw_toa、校正后的 ToA 和 correction_status；
- delay_seconds、估计散布和协方差引用；
- 校准有效区间、温度和锁定状态；
- 失败原因以及是否允许降权。

融合层不能从一个无来源的 corrected_toa 数字反推出这些字段。

## 18. 验证矩阵

| 编号 | 条件 | 输出 |
| --- | --- | --- |
| D0 | 同一公共源、同一处理链 | 固定站间差和重复性 |
| D1 | 端口/线缆交换 | 设备项与线缆项的闭合残差 |
| D2 | 频率扫描 | 频变延迟候选和拟合残差 |
| D3 | 带宽/PRB 掩码扫描 | 有效观测带宽对 ToA 的影响 |
| D4 | 采样率/DDC/滤波切换 | 处理链版本差异 |
| D5 | 温度和长时运行 | 校准有效期和漂移边界 |
| D6 | 天线端或已知位置 | 端到端参考面残差 |

结果写入 [[07-多站协同/Synchronization Validation Ledger]]，不要把预期趋势写成实测结果。

## 19. 证据与状态

- PERSONAL_NOTE：延迟分解、参考面和校准字段承接现有多站 UL-TDOA、Timing Observation 和 Quality and Uncertainty 笔记。
- STANDARD + partial：TS 38.215/38.305 用于定位测量角色边界；本页的设备链路校准不由这些标准直接给出。
- NEEDS_EXTERNAL_REFERENCE：具体设备 RF group delay、ADC 时间戳、PPS/PTP 接口和硬件规格。
- EXPERIMENT + NEEDS_VERIFICATION：D0-D6 尚未运行，所有延迟和误差数字保持 null。

## Related Notes

- [[07-多站协同/Multi-Station Synchronization]]
- [[07-多站协同/Clock Offset and Drift]]
- [[07-多站协同/Cross-Station Event Association]]
- [[07-多站协同/Multi-Station Observation Fusion]]
- [[07-多站协同/Synchronization Validation Ledger]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[06-TDOA定位/TDOA Measurement Model]]
