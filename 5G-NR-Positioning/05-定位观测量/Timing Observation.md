---
title: Timing Observation
aliases:
  - 时间观测量
  - ToA RToA TDoA 观测
type: atomic
status: partial
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/toa
  - topic/tdoa
  - stage/measurement
source:
  - "[[01-专题知识/5G定位/单用户时频截取与定位观测量]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[02-标准与参考/3GPP/3GPP TR 38.901｜Channel model]]"
related:
  - "[[04-PDSCH/PDSCH]]"
  - "[[05-定位观测量/Observation Taxonomy]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[06-TDOA定位/TDOA]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
---

# Timing Observation

## 1. 一句话定义

时间观测量是从已识别且可复现的 UE 参考/数据片段中提取的到达时间估计及其校准、质量和不确定度，而不是未经标定的相关峰样点。

## 2. 为什么项目需要它

第三阶段需要把每站同一 UE 事件转成可比较的 ToA/RToA，再形成 TDOA；没有峰策略、时钟偏置和数字链路延迟，最终坐标没有可解释性。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 `UE resource extraction` 和 `multi-station synchronization` 之间：[[04-PDSCH/PDSCH]]/上行参考 -> 滤波/截断 -> 时间峰 -> 校准 -> [[06-TDOA定位/TDOA]]。

## 4. 输入

单用户资源掩码、参考序列或可重复波形、采样率/时间戳、站点 ID、RF/滤波群时延、公共时钟状态、峰搜索窗口和质量门限。

## 5. 输出

`toa_raw_seconds`、`toa_corrected_seconds`、`clock_bias_seconds`、`rf_delay_seconds`、`filter_group_delay_seconds`、峰策略、峰值/旁瓣指标、置信度和 `tdoa_usable`。

## 6. 关键参数

采样率、整数/亚采样偏移、相关模板、带宽、窗口、`first|strongest|cluster` 峰策略、CFO/采样率偏差、噪声估计、参考站和质量门限。

## 7. 时域位置

时间坐标必须绑定 frame/slot/symbol 和捕获起点；PRACH occasion、PUSCH DM-RS、SRS 或其他参考的可用符号不同，不能用一个固定 slot 偏移覆盖所有信号。

## 8. 频域位置

观测带宽由被提取的 PRB/参考信号决定。频域截断、带通滤波和子载波选择改变等效脉冲响应与群时延，必须在校准字段中保留。

## 9. 数学原理

对模板 $s[n]$ 和接收片段 $r[n]$，离散相关为：

$$
z[\ell]=\sum_n r[n]s^*[n-\ell],\qquad
\hat n=\arg\max_\ell |z[\ell]|.
$$

粗略原始 ToA 为 $\hat t_{raw}=\hat n/F_s$；校准值可写成

$$
t_{cal}=t_{raw}-b_{clock}-d_{RF}-d_{filter}-d_{digital},
$$

其中各项的定义和符号约定必须在实验账本中固定。

## 10. 3GPP 对应规范

- TS 38.215：物理层测量和时间参考边界，UL-RTOA/参考点的精确条款需按 Release 核对（`NEEDS_EXTERNAL_REFERENCE`）。
- TS 38.211/38.214：参考信号、物理信道和资源位置；具体序列/映射条款依信号类型核对。
- TS 38.305：定位架构和观测量语义；标准 UL-TDOA 与项目定制被动测量需分开。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

可用基础 MATLAB `xcorr`、`findpeaks`、插值/拟合工具构造原型；`nrTimingEstimate` 等 NR API 是否适合当前信号与 Release 需本机核验，状态为 `NEEDS_EXTERNAL_REFERENCE`。API 输出不能替代校准账本。

## 12. 本项目中的用途

由 PRACH/PDSCH/PUSCH 资源识别支路产生稳定模板或参考 RE，提取每站原始峰和校准时间；只将满足 SNR、旁瓣、校准和跨站一致性的观测送入 TDOA。

## 13. 常见误区

- 把相关峰样点直接解释为绝对传播时间。
- 用 strongest peak 代替首径而不记录多径/NLOS 风险。
- 忽略滤波、抽 decimation、数字下变频和 FFT 窗口的群时延。
- 混用不同站点的捕获起点、采样率或符号边界。

## 14. 与相似概念的区别

- ToA 是单站到达时间估计；RToA 是相对参考的时间；TDOA 是站间差分。
- 相关峰位置是算法中间量；校准后的时间观测才是定位接口。
- 同步误差是观测误差来源，不是 UE 几何距离本身。

## 15. 代码实现注意事项

统一 SI 单位（秒、Hz、samples/s）；日志同时保留样点和秒；峰检测输出全相关轨迹、门限、峰宽和多峰；校准参数版本化；禁止用缺失值 0 伪装已校准。

## 16. 待实验验证的问题

- 单径已知延迟下整数/亚采样估计偏差。
- 带宽、滤波器和截断窗口对群时延与 ToA 方差的影响。
- 多径、CFO、采样率偏差和碰撞场景下的首径/最强峰选择。
- 三站同一事件的跨站时间残差和质量门限。

## 17. Related Notes

- [[04-PDSCH/PDSCH]]
- [[01-专题知识/5G定位/单用户时频截取与定位观测量]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[06-TDOA定位/TDOA]]
- [[09-采数实验/Capture Experiment Checklist]]

## 证据与状态

- `PERSONAL_NOTE`：现有单用户截取和 UL-TDOA 笔记的接口整理。
- `HYPOTHESIS + NEEDS_VERIFICATION`：峰策略、模板和项目观测信号仍待实测选择。

## 18. 观测对象和层级

Timing Observation 不是一个函数名，而是一份带上下文的测量记录。建议按以下层级保存：

| 层级 | 内容 | 是否可直接进入 TDOA |
| --- | --- | --- |
| 原始采样 | IQ、时间戳、通道、丢样/溢出计数 | 否，作为回放证据 |
| 相关特征 | 全相关轨迹、门限、峰列表、峰簇 | 否，作为候选和诊断 |
| 单站时间 | raw ToA、参考点、峰策略、频偏 | 仅在质量门通过后 |
| 校准时间 | 时钟/RF/滤波/数字链修正后的 ToA/RToA | 是，需带协方差 |
| 跨站派生 | TDOA、残差、有效站集合 | 交给 [[06-TDOA定位/TDOA]] |

不同层级使用不同状态。校准失败不能删除单站 raw 值；峰策略变化不能覆盖旧估计；最终位置也不能反写成“真实 ToA”。

## 19. 统一时间坐标

一条观测至少有三套坐标：

1. **协议坐标**：cell、carrier、frame、subframe、slot、symbol、RO 和资源快照。
2. **采样坐标**：捕获文件起点、窗口起点、相关轨迹局部索引和采样率。
3. **物理/校准坐标**：参考面、站点时钟、RF/滤波/数字链延迟和外部时间基准。

推荐的样点闭合关系是：

$$
n_{\mathrm{peak,capture}}
=n_{\mathrm{capture0}}
+n_{\mathrm{window,start}}
+n_{\mathrm{peak,local}}
+\delta_{\mathrm{frac}}.
$$

以参考样点 $n_{ref}$ 计算原始相对时间：

$$
\tau_{\mathrm{raw}}
=\frac{n_{\mathrm{peak,capture}}-n_{\mathrm{ref}}}{F_s}.
$$

同时保存：

| 字段 | 约定 |
| --- | --- |
| capture_sample_start/end | 明确左闭右开边界，记录窗口是否补零 |
| index_base | zero_based 或 one_based，不允许隐含 |
| local_or_absolute | 相关轨迹局部索引和捕获绝对索引分列 |
| reference_point | capture_start、RO 起点、序列起点、FFT 窗或 external timebase |
| sample_rate_hz | 当前处理链的实际采样率，重采样后生成新版本 |
| frame/slot/symbol | 与同一 config_id 绑定 |

如果周期相关返回模序列索引，先保存 peak_index_modulo，再由 RO 窗口和传播范围做 unwrap。不能由峰值大小猜 q。

## 20. ToA、RToA、TDoA 和 TA 的接口边界

### 20.1 ToA

ToA 是某个站相对明确参考点的到达时间估计：

$$
\widehat{\tau}_i
=\tau_{i}^{prop}
+b_i^{clock}
+d_i^{chain}
+e_i.
$$

没有已知发射时刻、站点偏置和链路延迟时，ToA 主要是相对观测，不是绝对距离。

### 20.2 RToA

RToA 必须携带 reference_point、reference_signal 和 measurement_domain。标准测量定义与项目用相关峰得到的相对时间不能只靠名称判断相同；TS 38.215 的具体参考点和适用信号需按目标 Release 外部核验。

### 20.3 TDoA

以站 $r$ 为参考：

$$
\widehat{\Delta\tau}_{i,r}
=\widehat{\tau}_i-\widehat{\tau}_r.
$$

该差值只有在 event_id、参考点、带宽/滤波配置和校准版本兼容时才有几何意义。共享参考站会产生协方差，不能把各 pair 当成独立噪声。

### 20.4 Timing Advance

TA 是网络向 UE 发送的上行定时控制命令；它和接收机从 PRACH/PUSCH 相关峰得到的 ToA 属于不同事件。TA 可作为协议上下文或一致性检查，但不能替代接收 ToA，也不能在没有时序证据时与 ToA 相加。

## 21. 信号特定的时间观测入口

| 输入信号 | 推荐参考 | 观测用途 | 先决条件 | 默认降级 |
| --- | --- | --- | --- | --- |
| PRACH 前导 | RO/序列起点 | 事件触发、粗 ToA | PRACH 配置、根序列、循环移位、检测窗 | collision_suspected 或 coarse_only |
| PUSCH DM-RS | 参考序列起点/FFT 窗 | UE 上行传输 ToA、跨站比较 | DCI/RRC 资源、端口/层、用户关联 | resource_partial |
| SRS | SRS 资源/参考点 | UL-RTOA 或项目时间候选 | SRS 配置和标准测量口径 | standard_measurement_pending |
| PDSCH DM-RS | 下行参考点 | 小区/发射源同步与质量 | PDSCH 资源和端口 | downlink_source_only |
| PDCCH DM-RS | CORESET/候选位置 | 控制候选质量 | CORESET、搜索空间、候选索引 | control_only |
| 未知业务 | 捕获/能量窗 | 低级事件候选 | 无法确认序列时只留特征 | feature_only |

固定第三方站接收到的下行时间差直接描述下行发射源；它不能仅凭差分推导 UE 位置。UE 定位支路应优先使用多站可见的 PRACH、PUSCH DM-RS、SRS 或其他已知上行片段。

## 22. 时间估计器选择

### 22.1 时域匹配相关

给定模板 $s[n]$ 和接收片段 $r[n]$：

$$
z[\ell]=\sum_n r[n]s^{*}[n-\ell].
$$

优点是参考明确、能保存完整峰轨迹；风险是模板错配、CFO、多径和碰撞。PRACH 专用实现见 [[02-PRACH/Timing Estimation]]。

### 22.2 频域相关

对有效子载波集合 $\mathcal K$，可保存：

$$
C[k]=Y[k]S^{*}[k],\qquad k\in\mathcal K.
$$

它便于比较带宽和频率掩码，但频率轴、FFT 定义、相位参考和零填充必须闭合。

### 22.3 峰值插值

整数峰附近可用局部抛物线或模板拟合估计 fractional_samples。插值增加的是估计网格细度，不自动增加有效带宽或真实物理分辨率。峰在边界、平台峰、邻峰未分离或拟合残差过大时应降级。

### 22.4 相位斜率

若多个频点的复相关相位可解缠，可拟合：

$$
\angle C[k]\approx\phi_0-2\pi f_k\tau+\eta_k.
$$

phase_slope 可作为独立交叉检查，但未知信道相位、频率选择性、多径和残余 CFO 会使它偏离时延模型。必须记录拟合权重、残差和频点集合。

## 23. 带宽、分辨率和混叠边界

三个容易混淆的量应分开记录：

| 量       | 由什么决定           | 解释          |
| ------- | --------------- | ----------- |
| 样点间隔    | $1/F_s$         | 离散时间轴的网格    |
| 相关插值网格  | 插值/零填充/模板       | 数值表示的细化     |
| 可辨识时延尺度 | 有效占用带宽、SNR、窗和信道 | 物理上可分离的路径尺度 |

工程上常用的数量级关系是：

$$
\Delta\tau_{\mathrm{scale}}\sim\frac{1}{B_{\mathrm{use}}},
$$

但它不是标准精度保证。零填充不会凭空提高物理带宽；窄带滤波可能降低可辨识度并引入群时延。每次观测必须保存有效 PRB/子载波集合、滤波通带和 FFT/窗配置。

周期相关还存在模索引歧义。unwrap 必须由 occasion 窗口、CP/保护区和允许传播范围约束；如果约束不足，状态为 modulo_ambiguous。

## 24. 多径、碰撞和峰策略

### 24.1 三种策略

| 策略 | 规则 | 适用输出 | 风险 |
| --- | --- | --- | --- |
| strongest | 功率最大峰 | 检测基线、粗 ToA | NLOS/反射导致晚到 |
| first_detected | 最早通过门限并满足连续性检查的峰 | 首径候选 | 低 SNR 漏检弱首径 |
| cluster | 对同一峰簇做联合拟合/加权中心 | 研究性时间和质量 | 簇边界/权重依赖 |

### 24.2 必须保留的峰信息

- 全部局部峰、峰功率、峰宽、prominence/PSLR；
- 峰簇 ID、邻峰间距和门限轨迹；
- first/strongest/cluster 的并行结果；
- 首径和最强峰的差值；
- 碰撞、多径、NLOS 和边界截断标志。

PRACH 同一 RO 内多个前导峰不能自动当作多个用户；同一前导的多径峰也不能自动当作多个 UE。峰数只是在当前带宽、门限和模型下可见的峰数下界。

## 25. CFO、采样频偏和多普勒

### 25.1 CFO

时域补偿可写为：

$$
r_{\mathrm{corr}}[n]
=r[n]\exp\left(-j2\pi\widehat f_{\mathrm{CFO}}n/F_s\right).
$$

补偿前后都保存相关峰、峰宽和残余频率误差。不同 CFO 假设产生的 ToA 差异应进入不确定度或状态，而不是静默选择一个最好看的峰。

### 25.2 采样频率偏差

跨块观测的漂移可用：

$$
\widehat\tau_k
\approx\tau_0+kT_{\mathrm{obs}}\epsilon_{\mathrm{sr}}+e_k
$$

描述。$\epsilon_{sr}$ 是相对采样率误差；它应由跨块轨迹或外部时钟估计。一次观测的标准差不能代替长期漂移模型。

### 25.3 多普勒和相位噪声

传播多普勒、载波频偏和相位噪声都会造成相位变化，但物理来源和补偿方式不同。没有载频、时间间隔、速度/角度或外部参考时，只能记录 frequency_candidate，不能把相位斜率直接命名为速度。

## 26. RF、滤波和数字链校准

推荐将每站观测写成：

$$
\tau_i^{corr}
=\tau_i^{raw}
-d_{i,RF}
-d_{i,cable}
-d_{i,filter}
-d_{i,digital}
-b_i^{clock}(t).
$$

正负号必须和校准装置的传播方向固定一致。校准表至少包含：

| 字段 | 要求 |
| --- | --- |
| station_id/channel_id | 指定接收链和天线 |
| frequency_hz/bandwidth_hz | 频率相关条件 |
| sample_rate_hz/filter_profile | 数字链条件 |
| reference_plane | 天线、线缆、RF、ADC 或数字输出端 |
| delay_seconds/std_seconds | 延迟和不确定度 |
| calibration_id | 不可变版本 |
| valid_from/valid_to | 有效时间范围 |
| temperature/method | 温度和回环/线缆/参考源方法 |

不同站若使用不同滤波器或带宽，TDOA 还包含群时延差：

$$
\widehat{\Delta\tau}_{ij}
=\Delta\tau_{ij}^{prop}
+(\tau_{g,i}-\tau_{g,j})
+(d_i-d_j)+e_{ij}.
$$

缺失校准时保留 raw 值，corrected 值为 null，状态至少为 calibration_missing 或 calibrated_pending。

## 27. 不确定度和协方差

### 27.1 单站误差预算

建议分列：

$$
\sigma_{\tau}^2
=\sigma_{\mathrm{sample}}^2
+\sigma_{\mathrm{frac}}^2
+\sigma_{\mathrm{CFO}}^2
+\sigma_{\mathrm{clock}}^2
+\sigma_{\mathrm{RF}}^2
+\sigma_{\mathrm{filter}}^2
+\sigma_{\mathrm{multipath}}^2
+\sigma_{\mathrm{association}}^2.
$$

这是工程近似；相关误差项需要协方差和交叉项。未测量项保持 unknown，不要填经验常数。

### 27.2 估计器不确定度

有真值的合成波形可计算 bias、RMSE、MAE、95/99 分位数和覆盖率；回环/重复采集可估计重复散布和固定偏置。两者必须分别标记 synthetic、calibration 或 field，不能混成一个精度数字。

### 27.3 TDOA 协方差

若 ToA 向量为 $\boldsymbol{\tau}$，差分矩阵为 $\mathbf{D}$：

$$
\boldsymbol{\Delta\tau}=\mathbf D\boldsymbol{\tau},
\qquad
\mathbf\Sigma_{\Delta}
=\mathbf D\mathbf\Sigma_{\tau}\mathbf D^{T}.
$$

下游应接收站点顺序、参考站、原始 ToA 协方差、剔除站和校准版本，而不是只接收一个差值数组。

## 28. 观测输出契约

最小字段集合如下；完整可扩展版本见 [[05-定位观测量/Observation Event Schema]]：

~~~json
observation_id: null
event_id: null
capture_id: null
station_id: null
config_id: null
signal_kind: null # PRACH, PUSCH_DMRS, SRS, PDSCH_DMRS, PDCCH_DMRS or UNKNOWN
reference_point: null # capture_start, ro_start, sequence_start, fft_window_start, external_timebase or unknown
sample_rate_hz: null
capture_sample_start: null
capture_sample_end: null
peak_index_integer: null
fractional_samples: null
fractional_method: null # none, parabolic, template_fit, phase_slope or unknown
peak_policy: null # strongest, first_detected, cluster or unknown
toa_raw_seconds: null
toa_corrected_seconds: null
rtoa_seconds: null
tdoa_seconds: null
reference_station_id: null
clock_bias_seconds: null
rf_delay_seconds: null
filter_group_delay_seconds: null
cfo_hz: null
sample_rate_offset_ppm: null
snr_db: null
uncertainty_std_seconds: null
quality_grade: null # A, B, C, invalid or unknown
quality_state: null # feature_only, toa_pending, toa_valid, calibrated_pending, tdoa_usable, rejected or unknown
diagnostic_reasons: []
calibration_id: null
source_kind: null # STANDARD, PERSONAL_NOTE, EXPERIMENT or HYPOTHESIS
evidence_status: null # verified, partial, NEEDS_VERIFICATION, NEEDS_EXTERNAL_REFERENCE or TODO
~~~

字段存在不代表可用：例如 toa_raw_seconds 有值但 reference_point=unknown 时，quality_state 不能是 toa_valid；tdoa_seconds 有值但没有 reference_station_id 时，记录不合格。

## 29. 质量门和状态转移

~~~text
candidate
  ↓ 资源、方向、参考和窗口通过
toa_pending
  ↓ 峰/拟合通过
toa_valid_candidate
  ↓ 时钟、RF、滤波和数字链校准在有效期
calibrated_pending
  ↓ event_id、协方差和站点几何通过
tdoa_usable
~~~

任一阶段失败都要保留原始证据并附原因：

| 原因 | 允许的降级 |
| --- | --- |
| resource_unknown / direction_unknown | partial_observation |
| reference_unknown / modulo_ambiguous | feature_only 或 coarse_only |
| window_truncated / template_mismatch | rejected |
| peak_ambiguous / collision_suspected | candidate，不进唯一 UE 解 |
| multipath_suspected / cfo_unresolved | toa_unreliable 或低权重 |
| calibration_missing / clock_unreliable | calibrated_pending |
| event_link_ambiguous / geometry_poor | tdoa_rejected |

quality_grade 是项目用途门，不是标准符合性等级；同一观测在事件触发和最终位置两个用途上可以有不同等级。

## 30. 验证矩阵

| 阶段 | 控制变量 | 必须记录 | 最小验收 |
| --- | --- | --- | --- |
| T0 坐标 | 已知样点/参考点 | 索引、边界、单位 | 样点和 raw 时间闭合 |
| T1 分数延迟 | fractional delay、SNR | 方法、残差、bias/RMSE | 边界失败可识别 |
| T2 相关质量 | SNR、门限、训练窗 | 全轨迹、PSLR、峰宽 | 低质量样本降级 |
| T3 CFO | CFO 网格、补偿状态 | 峰前后、残余频偏 | 不把 CFO 偏差隐藏 |
| T4 采样漂移 | ppm、采集时长 | 跨块轨迹 | 固定偏置和漂移分离 |
| T5 多径 | 路径延迟/功率 | 三种峰策略、峰簇 | 保留首径/最强峰差异 |
| T6 碰撞 | 前导/用户数、功率差 | 峰簇和关联候选 | 不强制唯一用户 |
| T7 滤波 | 带宽、FIR/IIR、抽取 | 群时延和校准版本 | raw/corrected 可解释 |
| T8 多站 | 时钟/RF/几何 | ToA 协方差、TDOA 残差 | 坏站显式剔除 |
| T9 现场 | 丢样、重锁、温度 | 失败计数、尾延迟 | 结果可回放 |

这些是验证设计，不是已经完成的实验。没有真实运行、配置和结果时，保持 EXPERIMENT + NEEDS_VERIFICATION。

## 31. 与相邻笔记的责任边界

| 问题 | 责任笔记 |
| --- | --- |
| PRACH 序列、RO 和相关器 | [[02-PRACH/PRACH Detection]]、[[02-PRACH/Timing Estimation]] |
| frame/slot/symbol 和 FFT/CP | [[01-NR基础/NR Frame Slot]]、[[01-NR基础/PRB RE Resource Grid]] |
| TDD 方向和资源合法性 | [[01-NR基础/NR TDD]] |
| 单用户资源掩码和截取 | [[04-PDSCH/UE Resource Extraction]]、[[单用户时频截取与定位观测量]] |
| 多站时钟/RF/数字校准 | [[07-多站协同/Multi-Station Synchronization]] |
| TDOA 几何和位置解算 | [[06-TDOA定位/TDOA]] |
| 统一字段、状态和证据 | [[05-定位观测量/Observation Event Schema]]、[[05-定位观测量/Quality and Uncertainty]] |

## 32. 证据分层和未决项

- STANDARD + partial：TS 38.211 的物理资源/参考信号接口；TS 38.214 的数据和 CSI 上下文。
- STANDARD + partial：TS 38.215/38.305 的测量和定位术语入口；精确参考点、误差要求和版本差异仍需外部核验。
- PERSONAL_NOTE：本项目对 ToA/RToA/TDoA、峰策略、校准字段和状态机的组织。
- HYPOTHESIS + NEEDS_VERIFICATION：用 PRACH/PUSCH/SRS 参考形成定制被动 UL-TDOA 的主观测。
- EXPERIMENT + NEEDS_VERIFICATION：任何检测概率、ToA/TDOA/位置误差、协方差覆盖率和实时延迟。
- NEEDS_EXTERNAL_REFERENCE：MATLAB/5G Toolbox 函数签名、标准 UL-RTOA/PRS 细节和项目 Release。

## 33. Related Notes

- [[05-定位观测量/Observation Taxonomy]]
- [[05-定位观测量/Standard Positioning Observables]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[02-PRACH/Timing Estimation]]
- [[04-PDSCH/UE Resource Extraction]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[06-TDOA定位/TDOA]]
- [[09-采数实验/Capture Experiment Checklist]]
