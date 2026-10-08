---
title: Timing Estimation
aliases:
  - PRACH 时延估计
  - PRACH 到达时间估计
  - PRACH ToA
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - topic/timing
  - topic/toa
  - stage/measurement
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.215
  - 用户项目流程说明
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]"
  - "[[01-专题知识/5G定位/单用户时频截取与定位观测量|现有单用户观测量笔记]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步|现有多站 TDOA 笔记]]"
  - "[[5G-NR-Positioning/05-定位观测量/Timing Observation|项目 Timing Observation]]"
---

# Timing Estimation

## 1. 一句话定义

Timing Estimation 是从 PRACH 相关峰或其他已知参考中估计相对到达样点/时间，并给出峰选择、插值和不确定度的过程。

## 2. 为什么项目需要它

第一阶段需要用时延验证 PRACH 检测和触发跨站事件；后续 TDOA 需要各站在同一时间定义下输出 ToA。估计值必须保留参考点、硬件延迟和峰策略，不能直接当绝对传播距离。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 PRACH Detection 之后，可并行服务 RA 事件关联和定位观测；在 C-RNTI/PDSCH 解析后还可对 PUSCH/DM-RS 重新估计更稳定的用户 ToA。

## 4. 输入

- 相关轨迹、候选前导和 RO 时间参考。
- 采样率、FFT/CP、捕获起点、CFO/采样率校正状态。
- 峰选择策略（first、strongest、cluster）和硬件校准表。

## 5. 输出

整数峰 n_hat、亚采样修正、峰宽/峰簇、质量指标、首径/最大峰标记、参考时间戳和 toa_valid/toa_unreliable 状态。

## 6. 关键参数

采样率 F_s、有效 PRACH 带宽 B_RA、相关峰插值方法、门限、峰间距、CFO、采样频率偏差、CP/窗口偏移、RF/滤波群时延和时钟偏置。没有校准值时应保留 unknown。

## 7. 时域位置

输出通常相对于捕获起点、RO 起点或同步参考点。PRACH 物理前导的传播峰、RAR 下发的 Timing Advance 命令和后续 PUSCH 的发射时刻属于不同时间事件，不可混为一个“时延”。

## 8. 频域位置

作为信号处理近似，时延分辨率主要受有效占用带宽影响，约为 $\Delta\tau\sim1/B_{RA}$；FFT 点数只改变采样网格细度，不会凭空增加物理带宽。这不是 38.215 的精度保证，实际误差还受 SNR、窗函数、CFO、滤波和多径影响。应记录 PRACH 频域 Occasion 和有效带宽。

## 9. 数学原理

整数峰和亚采样修正可写为

$$
\hat n=\arg\max_\ell |z[\ell]|,\qquad
\hat\tau=\frac{\hat n+\delta_{\mathrm{frac}}}{F_s}.
$$

若采用三点抛物线、相位斜率或插值滤波，必须记录 $\delta_{\mathrm{frac}}$ 的方法和适用条件。多站差分观测还包含时钟、RF、群时延和多径项：

$$
\widehat{\Delta\tau}_{ij}
=\Delta\tau_{ij}^{prop}+(b_i-b_j)+(d_i-d_j)+e_{ij}.
$$

## 10. 3GPP 对应规范

- TS 38.215：§5.2.2 是 UL-RTOA（以 SRS 为观测对象）的术语/参考点对照；PRACH 的 TADV、首径和参考点重点核对 §5.2.7。版本和术语需锁定，状态 NEEDS_EXTERNAL_REFERENCE。
- TS 38.211 §6.3.3：PRACH 波形和有效时间资源。
- TS 38.321 §5.1.4：RAR 中 Timing Advance 命令的协议位置；TA 不等于接收端直接测得的 ToA。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHDetect：返回样点偏移，可作为粗 ToA 单元测试入口。
- nrTimingEstimate：通用参考信号时延估计接口；PRACH 专用适配和版本签名需本机核验。
- nrOFDMDemodulate、nrOFDMInfo：核对符号/采样坐标和采样率。

函数名与返回字段均只作 API 线索，实际使用状态为 `NEEDS_EXTERNAL_REFERENCE`，需锁定本机 Release 后验证。

## 12. 本项目中的用途

把单站峰转换为带质量的 toa_observation，与 event_id、站点和配置绑定；随后由 [[01-专题知识/5G定位/多站 UL-TDOA 定位与同步|现有多站 TDOA 笔记]] 形成 TDOA。它既不能替代 [[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]，也不能从单次峰值直接推出 C-RNTI。

## 13. 常见误区

- 把相关峰样点偏移直接换算为 UE 到站距离。
- 把 TA 命令当作接收机 ToA 或把两者相加两次。
- 只取最大峰，忽略首径、多径和碰撞。
- 忽略滤波器群时延、RF 延迟和站间时钟偏置。

## 14. 与相似概念的区别

ToA 是相对/绝对到达时间估计；RTOA 是相对参考点的时间观测；TDOA 是多个站 ToA 的差分；TA 是网络对 UE 发出的上行定时控制命令；循环移位是序列参数，不是传播时延。

## 15. 代码实现注意事项

- 保存原始相关轨迹、峰候选、参考起点和插值参数。
- 统一秒、样点、采样率和帧/时隙时间坐标。
- 校准表按站点、频率、温度、滤波配置和采集 ID 版本化。
- 输出协方差或质量等级，坏峰不得静默进入 TDOA 解算。

## 16. 待实验验证的问题

- 单径、AWGN、CFO、多径和碰撞下的 ToA bias/RMSE/分位数。
- first/strongest/cluster 峰策略对后续 TDOA 的影响。
- 亚采样估计与设备实际采样时钟误差的耦合。
- PRACH 带宽、滤波器群时延和站间校准对可定位性的影响。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]、[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]。
- 定位接口：[[5G-NR-Positioning/05-定位观测量/Timing Observation|项目 Timing Observation]]、[[01-专题知识/5G定位/单用户时频截取与定位观测量|现有单用户观测量笔记]]、[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步|现有多站 TDOA 笔记]]。

## 18. 时间坐标契约

ToA 不是一个没有参考点的单一数字。每条观测都应同时保存协议坐标、设备样点坐标和选用的参考点，才能在跨站或跨采集比较时解释偏差。

### 18.1 三套坐标

定义：

- n_capture0：捕获文件第一个样点在设备时间轴上的索引，通常取 0，但不能假定所有文件都从 0 开始。
- n_window_start：相对于捕获文件起点的窗口起点。
- n_peak_local：相关轨迹中的整数峰索引。
- delta_frac：亚采样修正，约定单位为样点。
- n_ref_capture：当前输出所选参考点在统一捕获坐标中的索引。

样点到达位置和原始相对时间写为：

$$
n_{\mathrm{peak,capture}}
=n_{\mathrm{capture0}}+n_{\mathrm{window,start}}+n_{\mathrm{peak,local}}+\delta_{\mathrm{frac}},
$$

$$
\tau_{\mathrm{raw}}
=\frac{n_{\mathrm{peak,capture}}-n_{\mathrm{ref,capture}}}{F_s}.
$$

reference_time 必须是枚举而不是隐含约定，例如 capture_start、ro_start 或 sequence_start。如果参考点未知，toa_raw_seconds 仍可保存，但 toa_status 必须降级为 unreliable 或 unknown。

### 18.2 周期索引与绝对索引

PRACH 的周期相关或循环移位可能返回模序列长度的索引。先保存 peak_index_modulo，再依据 RO 窗口、CP/保护区和允许的传播时延范围做 unwrap：

$$
n_{\mathrm{unwrap}}
=n_{\mathrm{mod}}+qL_{\mathrm{period}},
\qquad q\in\mathbb{Z}.
$$

q 不能凭峰值大小猜测；应由窗口边界和配置约束决定。循环移位 $C_v$、Timing Advance 命令和传播 ToA 是不同语义，绝不能用同一个字段互相替代。

### 18.3 观测字段最小集合

| 字段 | 说明 |
| --- | --- |
| capture_id | 原始 IQ 与时间戳文件的不可变标识 |
| ro_key | cell、carrier、frame、slot、symbol、freq occasion 等上下文 |
| sample_rate_hz | 实际采集/重采样后的 $F_s$ |
| reference_time | 捕获起点、RO 起点或序列起点 |
| n_capture0 | 捕获文件起点在统一设备时间轴的索引 |
| n_window_start | Detection 窗口在捕获轴的起点 |
| n_integer | 相关峰整数索引 |
| fractional_samples | 亚采样修正和估计方法 |
| toa_raw_seconds | 未做硬件/群时延校正的相对时间 |
| corrections | RF、线缆、滤波、数字链和时钟校正项 |
| toa_corrected_seconds | 校正后时间；无校正时保持 null |
| uncertainty_std_seconds | 估计标准不确定度或未知 |
| peak_policy | strongest、first_detected 或 cluster |
| toa_status | valid、unreliable、pending 或 unknown |

## 19. 估计前的输入检查

Timing Estimation 只能消费 Detection 页产生的候选峰，不能绕过 RO 和参考检查在整段 IQ 上重新猜测时间。进入估计前逐项检查：

1. decision.state 至少为 preamble_detected 或明确允许降级的 ambiguous；reference_mismatch、window_truncated 不得直接输出有效 ToA。
2. 峰索引的局部起点、相关模式（线性/周期）和采样率已记录。
3. CFO 假设、采样率偏差和数字滤波状态已记录；未知项不能默认为零。
4. 峰是否属于同一前导、同一峰簇或可能碰撞已有诊断。
5. 原始相关轨迹、噪声/门限轨迹和候选峰仍可回读。

预处理可能改变时间位置：去直流、带通、抽 decimation、匹配滤波和窗口平移都要留下实现版本和群时延信息。若滤波器频响或群时延没有测量，输出可保留 raw 值，但不能标记为硬件校正后的 valid。

## 20. 整数样点 ToA

### 20.1 最大峰基线

对 Detection 页给出的相关功率 $P[\ell]$，在有效索引集合 $\mathcal{W}$ 内：

$$
\hat n_{\mathrm{strongest}}
=\arg\max_{\ell\in\mathcal{W}} P[\ell].
$$

若存在相同最大值或平台峰，保存全部等价索引并标记 peak_tie，不要依赖数组遍历顺序。valid 窗口应排除零填充边界、CP 不确定区和已知旁瓣保护区。

### 20.2 首个可检测路径

首径候选可定义为从预期最早位置向后扫描，第一个同时满足自适应门限、最小连续性和跨天线/重复观测一致性的局部峰。该定义是工程策略；TS 38.215 中 first detected path 的参考点、测量窗口和术语边界必须按目标 Release 外部核验，当前标为 NEEDS_EXTERNAL_REFERENCE。

### 20.3 整数索引的边界

整数峰只说明相关网格上的最佳样点，不能等同于物理传播路径的精确起点。采样率提高会细化网格，但不一定改善由有效带宽、SNR、滤波和多径决定的可辨识度。报告时至少区分：

- 样点量化误差；
- 相关主瓣宽度或峰宽；
- 峰选择造成的多径/NLOS 偏差；
- 参考点与硬件延迟造成的固定偏差。

## 21. 亚采样 ToA

### 21.1 三点抛物线插值

在整数峰 $\hat n$ 附近取 $A_{-1}=P[\hat n-1]$、$A_0=P[\hat n]$、$A_{+1}=P[\hat n+1]$，可用局部抛物线给出：

$$
\delta_{\mathrm{par}}
=\frac{1}{2}
\frac{A_{-1}-A_{+1}}
{A_{-1}-2A_0+A_{+1}},
\qquad
\hat\tau
=\frac{\hat n+\delta_{\mathrm{par}}}{F_s}.
$$

分母接近零、峰在边界、峰不具备局部单峰形状或相邻峰未分离时，应拒绝该修正或标记 fractional_unreliable。也可在功率对数域拟合，但必须把 fit_domain=power 或 log_power 写入事件；两者不能混称为同一个估计器。

### 21.2 模板插值/最小二乘

在已知模板 $u[n]$ 且信道在窗口内近似单径时，可对分数延迟模板 $u_\delta[n]$ 做拟合：

$$
(\hat\delta,\hat\alpha)
=\arg\min_{\delta,\alpha}
\left\|r[n]-\alpha u_\delta[n-\hat n]\right\|_2^2.
$$

插值核、搜索范围、复增益模型和噪声权重都属于实现参数；需要用已知分数延迟的合成波形和真实设备回放分别验证。模板拟合不应覆盖原始相关峰，拟合失败要保留残差和失败原因。

### 21.3 频域相位斜率

若已完成 CFO 校正并能获得多个有效频域相关 bin，可把相位近似写成：

$$
\angle C[k]\approx \phi_0-2\pi f_k\tau+\eta_k,
$$

再对解缠相位做加权线性拟合。未知信道相位、频率选择性、多径和残余 CFO 会破坏该近似；因此 phase_slope 只能作为独立对照方法，不能在没有残差检查时替代时域峰。

### 21.4 亚采样结果的记录

必须同时保存 fractional_samples、方法、拟合残差、邻峰间距、峰宽和是否触发边界裁剪。亚采样输出的单位是样点，不是纳秒；换算到时间后仍要使用同一 sample_rate_hz 和参考点。

## 22. 首径、最大峰与峰簇选择

| 策略 | 选择规则 | 优点 | 主要风险 | 适合输出 |
| --- | --- | --- | --- | --- |
| strongest | 取功率最大峰 | 简单、可复现 | NLOS/反射使峰晚到；碰撞时丢用户 | 检测基线、粗 ToA |
| first_detected | 最早通过门限且满足连续性检查的峰 | 更接近传播首径 | 低 SNR 时漏掉弱首径；门限敏感 | 首径候选、标准边界对照 |
| cluster | 对同一峰簇做加权中心、模板拟合或联合估计 | 利用多径能量、可给簇宽 | 需要明确权重和簇边界，可能偏向强路径 | 研究性观测、质量诊断 |

峰策略必须和场景绑定。碰撞时同一 RO 的多个前导峰应先分别保存；同一前导的多径峰则由 cluster_id 组织。若首径和最大峰差异超过预设一致性规则，输出 peak_policy_disagreement，不要静默覆盖。

### 22.1 峰选择伪代码

~~~python
input: correlation_trace, threshold_trace, ro_window, peak_policy
peaks = local_peaks(correlation_trace within ro_window)
peaks = keep(peaks where power >= threshold_trace)
peaks = annotate_width_prominence_pslr(peaks)
clusters = group_by_time_and_reference(peaks)

if policy == "strongest":
    selected = argmax_power(clusters or peaks)
elif policy == "first_detected":
    selected = earliest_peak_with_continuity_check(clusters or peaks)
elif policy == "cluster":
    selected = fit_or_weighted_centroid(clusters)
else:
    state = "peak_policy_unknown"

emit(selected, all_peaks=peaks, clusters=clusters,
     policy=policy, disagreement=check_policy_disagreement())
~~~

该伪代码描述处理边界，不规定具体门限、峰距或拟合核；这些值应和 Detection 页的配置快照一起版本化。

## 23. CFO、采样频率偏差与时间漂移

### 23.1 CFO 补偿

对频偏假设 $\hat f_{\mathrm{CFO}}$ 做时域去旋转：

$$
r_{\mathrm{corr}}[n]
=r[n]\exp\left(-j2\pi\hat f_{\mathrm{CFO}}n/F_s\right).
$$

补偿前后都应保存峰值、峰宽和残余频偏指标。CFO 未知时可沿用 Detection 页的假设网格，但不同假设得到的 ToA 差异必须进入不确定度或状态降级。

### 23.2 采样率偏差

采样频率偏差会使跨时间块的 ToA 产生漂移，可用工程模型表示：

$$
\hat\tau_k\approx\tau_0+kT_{\mathrm{obs}}\epsilon_{\mathrm{sr}}+e_k,
$$

其中 $\epsilon_{\mathrm{sr}}$ 是相对采样率误差，$T_{\mathrm{obs}}$ 是观测间隔。该模型的估计和重采样实现需通过外部仪器或已知参考验证；不要把长期漂移塞进单次峰的随机误差。

### 23.3 不同时间事件的边界

PRACH 接收峰、RAR 中的 Timing Advance、后续 PUSCH 发射时刻和本地采集时间戳属于不同事件。TA 是网络下发的控制命令，不是接收机直接测得的 ToA；两者不能相加两次，也不能在缺少协议时序时互换。

## 24. 硬件/滤波校准

### 24.1 校正方程与符号

可将校正后的观测抽象为：

$$
\tau_{\mathrm{corr}}
=\tau_{\mathrm{raw}}
-d_{\mathrm{RF}}
-d_{\mathrm{cable}}
-d_{\mathrm{filter}}
-d_{\mathrm{digital}}
-b_{\mathrm{clock}}(t).
$$

上式的正负号只是项目约定；每一项的测量方向、参考面和单位必须写进校准记录。未知项保持 null，不能用零替代后再宣称 corrected。

### 24.2 校准表

| 字段 | 要求 |
| --- | --- |
| station_id | 站点/接收链标识 |
| frequency_hz、bandwidth_hz | 频率相关校准条件 |
| sample_rate_hz、filter_profile | 数字链配置 |
| antenna_cable_chain | 天线、线缆、RF 路径参考面 |
| delay_seconds、std_seconds | 延迟及不确定度 |
| temperature_range | 适用温度或测量条件 |
| measured_at、calibration_id | 测量时间与不可变版本 |
| method | 回环、线缆直连、参考源或其他方法 |
| validity | 适用范围和失效原因 |

线缆直连、回环或外部参考源都可能作为校准方法，但具体装置、连接器和参考面尚未在项目中核验，标记 NEEDS_VERIFICATION。跨频率或温度插值必须有测量支撑，不能线性外推而不报告误差。

### 24.3 多站差分

若站 $i$ 和站 $j$ 输出同一 event_id 的校正 ToA：

$$
\widehat{\Delta\tau}_{ij}
=\tau_{\mathrm{corr},i}-\tau_{\mathrm{corr},j}.
$$

站间共享参考、共同触发或同一事件会产生相关误差；下游 TDOA 应接收原始 ToA 协方差，而不是只接收一个差值。

## 25. 不确定度与质量等级

### 25.1 误差预算

工程上可先拆分为：

$$
\sigma_{\tau}^2
=\sigma_{\mathrm{sample}}^2
+\sigma_{\mathrm{frac}}^2
+\sigma_{\mathrm{CFO}}^2
+\sigma_{\mathrm{clock}}^2
+\sigma_{\mathrm{RF}}^2
+\sigma_{\mathrm{filter}}^2
+\sigma_{\mathrm{multipath}}^2
+2\sum_{a<b}\operatorname{cov}(e_a,e_b).
$$

独立误差的平方和只是近似；同一参考站、同一滤波器或同一时钟源会产生协方差。若某项尚未测量，应写成未知并降低质量等级，而不是填入经验常数。

### 25.2 估计器不确定度

亚采样拟合可通过重复噪声试验、bootstrap 或模型拟合残差估计方差；这些是实现/实验方法，不是规范要求。必须记录样本数、SNR/噪声定义、随机种子和置信区间算法。单个峰的峰宽可作为诊断特征，但不能未经验证直接等价为标准差。

### 25.3 TDOA 协方差

将 $m$ 个站的 ToA 组成 $\boldsymbol{\tau}$，以站 $r$ 为参考的差分矩阵为 $\mathbf{D}$，则：

$$
\boldsymbol{\Delta\tau}=\mathbf{D}\boldsymbol{\tau},
\qquad
\mathbf{\Sigma}_{\Delta}
=\mathbf{D}\mathbf{\Sigma}_{\tau}\mathbf{D}^{T}.
$$

这提醒下游 [[01-专题知识/5G定位/多站 UL-TDOA 定位与同步|现有多站 TDOA 笔记]]：共享参考站会让差分项相关，不能默认使用对角权重矩阵。

### 25.4 质量等级建议

| 等级 | 必须具备 | 可用于 |
| --- | --- | --- |
| A | 参考、窗口、CFO、采样率和硬件校准均可追溯，峰策略稳定 | 进入 TDOA 候选 |
| B | 参考和窗口闭合，校准部分缺失但有不确定度上界 | 诊断/谨慎加权 |
| C | 只有相关峰或参考点未知 | 单站事件触发，不进最终解算 |
| invalid | 窗口截断、参考错配或估计失败 | 只保存原始证据 |

等级只是项目质量门，不是 3GPP 合规等级；阈值和上界需要实验校准。

## 26. ToA 观测事件 schema

以下是和 Detection 页衔接的项目日志契约，不是标准 ASN.1 或 3GPP 测量报告结构。

~~~js
event_type: prach_toa_observation
event_schema_version: "0.1"
event_id: null
capture_id: null
station_id: null
config_id: null
release_or_toolbox_version: NEEDS_EXTERNAL_REFERENCE
ro_key:
  cell_id: null
  carrier_id: null
  frame: null
  slot: null
  start_symbol: null
  freq_occasion: null
  preamble_index: null
  cluster_id: null
coordinate:
  sample_rate_hz: null
  reference_time: capture_start|ro_start|sequence_start|unknown
  n_capture0: null
  n_window_start: null
  peak_index_modulo: null
  n_integer: null
  fractional_samples: null
  fractional_method: none|parabolic|template_fit|phase_slope|unknown
  unwrap_period_samples: null
  n_peak_capture: null
toa:
  toa_raw_seconds: null
  corrections:
    rf_seconds: null
    cable_seconds: null
    filter_seconds: null
    digital_seconds: null
    clock_seconds: null
  toa_corrected_seconds: null
  correction_status: none|partial|complete|unknown
peak:
  policy: strongest|first_detected|cluster|unknown
  peak_power: null
  peak_width_samples: null
  pslr_db: null
  path_count_lower_bound: null
  collision_suspected: false
quality:
  uncertainty_std_seconds: null
  covariance_ref: null
  cfo_hz: null
  sample_rate_offset_ppm: null
  grade: A|B|C|invalid|unknown
  state: toa_pending|reference_unknown|integer_valid|toa_valid|toa_unreliable|fractional_unreliable|peak_policy_disagreement|multipath_suspected|collision_suspected|cfo_unresolved|calibration_missing|clock_unreliable|invalid
  diagnostic_reasons: []
evidence:
  standard: STANDARD+partial
  implementation: PERSONAL_NOTE
  experiment: NEEDS_VERIFICATION
~~~

path_count_lower_bound 只表示在当前参考和门限下可分离的峰数下界，不是用户数。toa_corrected_seconds 为空时，TDOA 接口必须消费 raw 值并显式带上校准缺口。

## 27. 指标与场景矩阵

### 27.1 指标

对有真值的合成或标定数据，分别报告偏差、RMSE、MAE、标准差和 95/99 分位数：

$$
e_{\tau,q}=\hat\tau_q-\tau_{\mathrm{true},q},
\qquad
\mathrm{RMSE}_{\tau}
=\sqrt{\frac{1}{N}\sum_{q=1}^{N}e_{\tau,q}^{2}}.
$$

还应记录：整数峰命中率、亚采样成功率、峰簇正确关联率、首径/最大峰切换率、toa_unreliable 比例、校准残差、跨站 TDOA RMSE、协方差覆盖率和处理延迟。没有真值时只能报告内部一致性，不能伪造绝对误差。

### 27.2 场景矩阵

| 场景 | 扰动/控制变量 | 重点指标 | 失败或降级观察 |
| --- | --- | --- | --- |
| T0 单径整数延迟 | 已知样点、无噪声 | 整数峰偏差、参考点闭合 | 非零偏差先查窗口/相关索引 |
| T1 单径分数延迟 | 注入 $\delta$、SNR | 插值 bias/RMSE、失败率 | fractional_unreliable |
| T2 AWGN | SNR、噪声种子 | ToA RMSE、置信区间覆盖 | 低 SNR 首径漏检 |
| T3 CFO | CFO 大小、补偿状态 | 峰偏移、峰宽、残余 CFO | cfo_unresolved |
| T4 多径/NLOS | 路径延迟/功率 | first/strongest/cluster 偏差 | multipath_suspected |
| T5 碰撞 | 前导组合、功率差 | 峰簇分离、错误关联率 | collision_suspected |
| T6 滤波/群时延 | filter profile、带宽 | raw/corrected bias | correction_partial |
| T7 多站时钟 | 触发偏置、漂移 | TDOA bias、协方差 | clock_unreliable |
| T8 采样率漂移 | ppm、观测时长 | 随时间的 ToA 漂移 | sample_rate_unresolved |

所有结果表的场景参数、Release、配置、随机种子和原始相关轨迹都必须可回放；当前不填写任何数值结果。

## 28. 状态与失败原因

| 状态 | 进入条件 | 处理 |
| --- | --- | --- |
| toa_pending | 检测峰已产生，尚未选择峰策略 | 保留所有候选峰 |
| reference_unknown | 时间参考点或序列起点未知 | 可保存 raw，不标 valid |
| integer_valid | 整数峰在有效窗口且门限通过 | 进入亚采样/校准 |
| fractional_unreliable | 插值分母、拟合残差或边界不合格 | 使用整数值并降级 |
| peak_policy_disagreement | first/strongest/cluster 结果分歧过大 | 输出多策略结果，不覆盖 |
| multipath_suspected | 峰簇或首径/最大峰差异明显 | 标记 NLOS 风险 |
| collision_suspected | 不同前导峰可能共用一个 RO | 禁止唯一 UE 解释 |
| cfo_unresolved | 补偿假设不稳定或残余过大 | ToA 不进高质量集合 |
| calibration_missing | RF/滤波/时钟校准项缺失 | raw 保留，corrected 为空 |
| clock_unreliable | 跨站时间基准不可追溯 | 禁止形成高质量 TDOA |
| invalid | 窗口截断、参考错配或估计失败 | 只保存证据和失败原因 |

状态应与 quality.grade、diagnostic_reasons[] 分离；例如 integer_valid + multipath_suspected 是合法组合。

## 29. 最小验证步骤

1. **坐标单元测试**：构造已知 n_window_start、整数延迟和参考点，确认 n_peak_capture 与 toa_raw_seconds 的单位、符号和 0/1 基约定闭合。
2. **分数延迟测试**：用已知 $\delta$ 的合成模板比较整数、抛物线、模板拟合三种方法，保存偏差和拟合残差；不把插值输出当作设备精度。
3. **峰策略测试**：构造首径弱于反射径的多径波形，以及两个不同前导的碰撞波形，分别检查 first/strongest/cluster 和诊断标志。
4. **CFO/采样率测试**：注入已知 CFO 和采样率偏差，比较补偿前后峰、跨块漂移和状态降级。
5. **校准回放**：使用带已知延迟的回环或线缆参考，验证校正方程的符号和校准表绑定；没有实测装置时保持 NEEDS_VERIFICATION。
6. **多站闭合**：在公共时钟、单径、已知几何下生成同一 event_id，验证 TDOA 差分、协方差变换和站点缺失时的降级。
7. **API 对照**：仅在本机锁定 MATLAB/5G Toolbox Release 后核验 nrPRACHDetect、nrTimingEstimate 等输入/输出；保存 ver、返回字段和波形，不能以函数名推断行为。
8. **回读审计**：从 ToA 事件反查 Detection 轨迹、配置、校准版本和原始 IQ；任何无法反查的数值标为 unreproducible。

## 30. 证据分层与限制

| 层级 | 允许的主张 | 当前状态 |
| --- | --- | --- |
| STANDARD | 38.211 的 PRACH 波形/资源接口、38.215 的测量术语边界 | STANDARD + partial；精确参考点、表值和 Release NEEDS_EXTERNAL_REFERENCE |
| PERSONAL_NOTE | 项目把 PRACH 峰作为粗 ToA 并接入多站 TDOA 的流程 | 项目约定，不等同标准流程 |
| PERSONAL_NOTE/HYPOTHESIS | 整数/亚采样估计、峰策略、校准和 schema | 建议方案，需单元测试和对照，不是规范要求 |
| EXPERIMENT | bias、RMSE、覆盖率、实时性和现场稳定性 | 尚未运行，NEEDS_VERIFICATION |
| NEEDS_EXTERNAL_REFERENCE | MATLAB 函数名和可能的入口 | 签名、维度、峰策略和版本行为需本机核验 |

当前未决项：项目采用的 3GPP Release、真实 PRACH 配置与时间参考、设备滤波/群时延、站间时钟方案、CFO/采样率估计器、first detected path 的具体实现、碰撞和 NLOS 判定规则。除非这些项有配置快照或实验记录，否则只能把本页输出称为“相对、带质量的工程观测”，不能宣称绝对距离、标准合规或现场定位精度。
