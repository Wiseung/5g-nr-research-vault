---
title: Observation Taxonomy
aliases:
  - 定位观测量分类
  - NR 观测量矩阵
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/measurement
  - topic/positioning
  - stage/observation
source:
  - "[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[02-标准与参考/3GPP/3GPP TR 38.901｜Channel model]]"
  - "[[01-专题知识/5G定位/单用户时频截取与定位观测量]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
related:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[01-专题知识/信道估计与均衡/DM-RS]]"
  - "[[01-专题知识/信道估计与均衡/SRS]]"
  - "[[01-专题知识/信道估计与均衡/CSI-RS]]"
  - "[[06-TDOA定位/TDOA]]"
---

# Observation Taxonomy

> [!abstract] 一句话结论
> 定位观测量不是一个单独的“时延数”，而是带有信号角色、时间/频率/空间坐标、参考点、估计器、校准状态、质量和证据来源的观测束。先区分原始特征、单站测量、跨站派生量和最终位置，再讨论某个字段能否用于定位。

## 1. 目的与边界

本页回答三个问题：

1. 一个字段究竟测量了什么物理对象？
2. 它依赖哪些配置、参考点和校准？
3. 它能否作为下一层算法的输入，还是只能作诊断特征？

本页不把标准定位方法、第三方被动监听和仿真设计混为一谈。精确的 3GPP 版本、表格、测量参考点和报告字段仍需按项目 Release 外部核验，当前相关主张保留 NEEDS_EXTERNAL_REFERENCE。

## 2. 五层观测模型

~~~text
L0 原始证据
    IQ、时间戳、丢样/溢出、天线通道、原始频域网格
        ↓
L1 算法特征
    相关轨迹、峰列表、FFT、相位差、功率和参考匹配残差
        ↓
L2 单站观测
    ToA/CFO/功率/角度/信道特征 + 参考点和估计器
        ↓
L3 校准观测
    校正 ToA/RToA、频率修正、阵列校正、协方差和质量等级
        ↓
L4 融合结果
    TDOA、几何残差、GDOP、位置和位置不确定度
~~~

相邻层之间必须是可追溯映射，而不是原地覆盖：

| 映射 | 必须保存 | 典型失败状态 |
| --- | --- | --- |
| L0 → L1 | 算法版本、窗口、模板、参数和原始轨迹引用 | feature_unreproducible |
| L1 → L2 | 参考点、索引基准、估计器和候选选择 | reference_unknown |
| L2 → L3 | 时钟/RF/滤波/阵列校准版本和有效范围 | calibration_missing |
| L3 → L4 | 事件关联、协方差、站点几何和参考站 | tdoa_rejected |

## 3. 总分类矩阵

| 类别 | 观测对象 | 代表字段 | 主要依赖 | 当前项目角色 |
| --- | --- | --- | --- | --- |
| 时间 | 波形到达或相对时间 | toa_raw_seconds、toa_corrected_seconds、rtoa_seconds | 参考序列、采样率、时钟/RF 校准 | 主线 |
| 时间差 | 站间或往返差分 | tdoa_seconds、rtt_seconds | 同一事件、共同参考、站点同步 | 主线/对照 |
| 频率 | 本振/采样/传播引起的频率变化 | cfo_hz、residual_cfo_hz、doppler_candidate_hz | 多时刻参考、相位展开、载频 | 辅助质量 |
| 功率 | 目标信号与噪声/干扰能量 | peak_power、noise_floor、snr_db、sinr_db | 窗口、归一化、校准 | 质量门 |
| 相位 | 复信道或阵列相位 | phase_slope、phase_diff | 频率轴、CFO、天线校准 | 辅助/后续 |
| 空间 | 到达方向、波束或空间响应 | aoa_candidate、beam_id、spatial_spectrum | 多天线、阵列几何、相位中心 | 后续 |
| 信道 | 多径、时延扩展、频率/时间选择性 | path_count_lower_bound、delay_spread | 参考信号、带宽、模型 | 诊断 |
| 身份/上下文 | 事件、用户、资源和方向 | event_id、c_rnti_state、resource_snapshot | PRACH/RA/PDCCH/RRC | 关联前提 |
| 几何 | 站点关系和解算残差 | gdop、residual_seconds、position_covariance | 坐标系、有效站、求解器 | L4 |

同一字段名不能跨类别复用。例如 timing_advance 是协议命令，不能填入 toa_raw_seconds；rsrp_dbm 也不能在没有测量口径时替代项目的相关峰功率。

## 4. 时间类观测

### 4.1 ToA、RToA、TDoA、RTT 和 TA

对第 i 个站点，单站观测可抽象为：

$$
t_i^{obs}
=t_{tx}
+\frac{\rho_i}{c}
+b_i+d_i+e_i
$$

其中 t_tx 是未知或部分已知的发射时刻，rho_i 是传播距离，b_i 是站点时钟项，d_i 是 RF/数字链延迟，e_i 汇总估计、噪声、多径和 NLOS 误差。

| 名称 | 数学/语义 | 是否能直接给 UE 距离 | 本项目字段建议 |
| --- | --- | --- | --- |
| ToA | 一个站相对某参考点的到达时间估计 | 通常不能，除非发射时刻和延迟已知 | toa_raw_seconds、toa_corrected_seconds |
| RToA | 相对规定参考点或参考信号的时间观测 | 取决于参考点和标准口径 | rtoa_seconds + reference_point |
| TDoA | 两个 ToA 的差 | 可形成距离差约束 | tdoa_seconds + 参考站 |
| RTT/Multi-RTT | 往返时延或多次交互组合 | 需要交互时序和协议上下文 | rtt_seconds，不用于被动链默认输入 |
| TA | 网络发送给 UE 的上行定时控制命令 | 不是接收站直接测得的传播时间 | ta_command，单独保存 |

以参考站 r 做差：

$$
\Delta t_{i,r}
=t_i^{obs}-t_r^{obs}
=\frac{\rho_i-\rho_r}{c}
+(b_i-b_r)+(d_i-d_r)+(e_i-e_r).
$$

只有校准项、事件关联和参考点都闭合时，tdoa_seconds 才能进入几何解算。PRACH 的循环移位、检测索引和 TA 命令各自属于不同语义，不应互相换算。

### 4.2 时间参考点

每个时间值必须带枚举式参考点，至少区分：

| reference_point | 含义 | 风险 |
| --- | --- | --- |
| capture_start | 相对原始文件起点 | 文件起点未跨站对齐时只能作单站值 |
| ro_start | 相对 PRACH occasion 起点 | RO 配置或 unwrap 错误会产生整周期偏差 |
| sequence_start | 相对已知序列理论起点 | 需要明确序列映射、CP 和窗口 |
| fft_window_start | 相对去 CP 的 FFT 窗 | 窗口平移和 CP 误差会进入偏置 |
| external_timebase | 相对 PPS/PTP/触发时间 | 必须保存时间源、锁定状态和不确定度 |
| unknown | 参考点无法恢复 | 只能保留 raw 特征，不能标 valid |

### 4.3 时间方法选择

| 方法 | 最小输入 | 优势 | 失效/降级条件 |
| --- | --- | --- | --- |
| 时域匹配相关 | 已知模板和接收片段 | 可解释、适合 PRACH/DM-RS | 模板错配、碰撞、多径 |
| 频域相关 | 有效子载波和参考相位 | 可分块、便于带宽诊断 | 频率轴错位、相位缠绕 |
| 峰值插值 | 整数峰及邻点 | 增加网格细度 | 峰平坦、边界或多峰 |
| 相位斜率 | 多个频点的复相关 | 可作独立对照 | 未校准 CFO、频率选择性 |
| 能量起始/包络 | 信号与噪声窗口 | 不依赖完整序列 | 阈值敏感，难分首径 |

方法名称、窗口、模板版本和残差必须写入事件；不同方法得到的差异应作为诊断量而不是静默平均。

## 5. 频率与相位类观测

接收片段可用一个简化模型表示：

$$
r[n]\approx\alpha\,s[n-n_0]
\exp\left(j2\pi f_{\mathrm{res}}\frac{n}{F_s}+j\phi_0\right)+w[n].
$$

这里的 f_res 可能包含 CFO、采样频率偏差在局部窗口内的表现、传播多普勒和残余补偿误差。仅凭单个短窗口通常无法把它们唯一分解。

| 字段 | 解释 | 需要的附加证据 |
| --- | --- | --- |
| cfo_hz | 本地估计的载波频率偏差候选 | 参考序列、估计区间、符号时间 |
| residual_cfo_hz | 补偿后的剩余旋转 | 补偿前后残差和方法 |
| sample_rate_offset_ppm | 采样时钟相对误差 | 跨块/外部时钟对照 |
| doppler_candidate_hz | 传播频移候选 | 载频、速度/角度假设和多时刻轨迹 |
| phase_slope | 跨频点或跨时刻的相位斜率 | 相位解缠、频率坐标和权重 |

对相邻参考观测，频率候选可写成：

$$
\widehat f
\approx\frac{\operatorname{unwrap}(\phi_2-\phi_1)}
{2\pi(t_2-t_1)}.
$$

该式受相位缠绕和参考点间隔约束；它不是“速度测量”本身。载频频偏、传播多普勒、相位噪声和采样率漂移应分字段、分状态记录。未完成分解时，状态应为 frequency_ambiguous 或 cfo_unresolved。

## 6. 功率与信噪质量类观测

对一个明确窗口 W，线性平均功率可写为：

$$
\widehat P_W=\frac{1}{|W|}\sum_{n\in W}|x[n]|^2.
$$

任何 dB/dBm 数值都必须同时说明：

- 采样域还是 RE 域；
- 目标窗口、噪声窗口和保护区；
- 是否做了 ADC/RF 增益校准；
- 是峰值、平均值、每 RE 值还是总带宽值；
- 噪声是否含邻用户干扰。

建议分列保存：

| 指标 | 用途 | 不可静默假设 |
| --- | --- | --- |
| peak_power | 候选峰排序 | 峰宽和归一化会改变数值 |
| noise_floor | CFAR/质量门 | 训练单元不能包含目标峰 |
| snr_db | 单站检测质量 | 信号/噪声窗口和带宽必须固定 |
| sinr_db | 含干扰的有效质量 | 干扰估计方法必须记录 |
| rsrp_dbm/rsrq_db | 标准名称候选 | 精确定义和参考带宽需按 38.215 核验 |
| evm/nmse | 参考/信道重构质量 | 参考域、归一化和真值来源必须明确 |

项目内部可以使用 snr_db 作为质量特征，但不能把未校准的相关峰 dB 直接命名为标准 RSRP。任何质量门都应带 quality_config_id，便于知道门限如何产生。

## 7. 空间、相位和角度类观测

多天线接收的简化阵列模型为：

$$
\mathbf y[k]
=\mathbf a(\theta)\,s[k]
+\mathbf n[k],
$$

或在多径情形下：

$$
\mathbf y[k]
=\sum_p\mathbf a(\theta_p)\,s_p[k]
+\mathbf n[k].
$$

阵元间相位差、波束扫描峰或空间谱可以形成 aoa_candidate，但必须先说明：

1. 阵元坐标、极化、端口到天线的映射；
2. 频率轴和中心频率；
3. 天线/线缆/RF 相位校准及参考面；
4. 单径、多径和 NLOS 假设；
5. 角度坐标系、正负方向和高度定义。

未校准阵列的相位差可以作相对诊断，不能直接作为地理方位。AoA/AoD 也不能自动替代多站 UL-TDOA；本项目当前把它们标为后续扩展。

## 8. 信道与多径观测

参考信号可生成离散信道响应候选：

$$
\widehat h[\ell]
=\mathcal F^{-1}\{\widehat H[k]\}.
$$

可记录的特征包括：

- 主峰、首个可检测峰和峰簇；
- 峰间距、峰宽、峰功率比和旁瓣；
- 可分离路径数下界；
- 有效时延扩展和频率选择性；
- 参考信号重构残差、跨天线一致性和跨重复一致性。

这些量描述“当前带宽和门限下可见的结构”，不等于真实路径数，也不等于用户数。TR 38.901 可用于 TDL/CDL 仿真分层，但仿真路径参数不应写成现场观测。

## 9. 身份与上下文观测

身份类字段不是物理测量，但没有它们就无法判断“多个站看到的是不是同一事件”：

| 上下文 | 例子 | 证据边界 |
| --- | --- | --- |
| 载波/小区 | carrier_id、cell_id | 小区同步/配置快照 |
| 时间坐标 | frame、slot、symbol、RO | config_id 和同步状态 |
| 资源 | BWP、PRB、RE、端口/层 | 38.211/38.214 资源映射 |
| 接入状态 | preamble、RO、RA-RNTI、RAR | 不能直接升级为 C-RNTI |
| 用户状态 | temporary C-RNTI、C-RNTI、关联置信度 | 需跨消息/时序证据 |
| 事件关联 | event_id、重传序号、碰撞标记 | 候选关联，不应只按时间最近 |

CRC pass、valid DCI、user_associated、toa_valid 和 tdoa_usable 是不同状态。身份字段应与观测字段并列，不能把一个高层 ID 当作时间质量证明。

## 10. 标准信号与项目用途矩阵

| 信号 | 主要观测 | 适合的阶段 | 必须保留的边界 |
| --- | --- | --- | --- |
| PRACH | 粗 ToA、事件触发、碰撞峰 | PRACH/RA | 前导不是 C-RNTI；TA 不是 ToA |
| PUSCH DM-RS | 当前 UL 传输的时间/频率/信道质量 | 单 UE、TDOA 候选 | DCI/RRC、端口/层和资源必须闭合 |
| SRS | UL 空间/频率/时间候选 | 标准对照或上行测量 | 配置和标准测量参考点待核验 |
| PDSCH DM-RS | DL 质量和发射源时间辅助 | 同步/质量 | 固定站对 DL 的差分不能直接定位 UE |
| PDCCH DM-RS | 控制候选质量 | 控制解析辅助 | 不是 UE UL 定位信号 |
| CSI-RS | 下行 CSI/波束测量 | 预编码/质量 | 测量时刻和数据时刻可能不同 |
| PRS | 标准定位参考候选 | 标准定位背景 | 测量主体和配置需按 38.211/38.305 核验 |

“标准信号存在”只说明有潜在观测源，不说明第三方设备已捕获、已正确解调或已满足标准流程。

## 11. 观测选择决策树

~~~text
目标是定位 UE 还是描述下行发射源？
  ├─ UE → 优先寻找多站可见的 UL 参考/已知 UL 片段
  └─ DL 源 → 保存 gNB/TRP 观测，不改名为 UE 观测
        ↓
是否有合法资源和可回放参考？
  ├─ 否 → 只输出 feature_only / partial_observation
  └─ 是
        ↓
是否能区分同一事件、碰撞和重传？
  ├─ 否 → observation_candidate，禁止唯一用户解释
  └─ 是
        ↓
是否有时间/频率/空间校准与质量指标？
  ├─ 否 → raw_observation 或 calibrated_pending
  └─ 是 → 交给对应融合器
~~~

## 12. 最小观测束示例

一次可进入跨站时间融合的观测，至少应携带：

~~~json
observation_id: obs-example
event_id: evt-example
station_id: station-a
signal:
  kind: PUSCH_DMRS
  direction: UL
  reference_available: true
coordinate:
  config_id: cfg-example
  frame: null
  slot: null
  symbol: null
  reference_point: sequence_start
  sample_rate_hz: null
time:
  toa_raw_seconds: null
  toa_corrected_seconds: null
  rtoa_seconds: null
frequency:
  cfo_hz: null
  sample_rate_offset_ppm: null
power:
  signal_db: null
  noise_db: null
quality:
  grade: unknown
  state: calibrated_pending
  reasons: []
provenance:
  source_kind: PERSONAL_NOTE
  status: NEEDS_VERIFICATION
~~~

示例中的 null 是有意的：没有现场配置或运行结果时，不填常见 SCS、采样率、门限或精度。

## 13. 证据与未决项

- STANDARD + partial：[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]] 的物理信道/参考信号/资源网格职责、[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]] 的数据和 CSI 接口。
- STANDARD + partial：[[02-标准与参考/3GPP/3GPP TR 38.901｜Channel model]] 的 TDL/CDL、时延、角度和多普勒建模边界。
- PERSONAL_NOTE：[[单用户时频截取与定位观测量]]、[[多站 UL-TDOA 定位与同步]] 对项目观测链的整理。
- HYPOTHESIS + NEEDS_VERIFICATION：把 PRACH/PUSCH/SRS 参考用于没有 LMF/gNB 协作的定制被动 UL-TDOA。
- NEEDS_EXTERNAL_REFERENCE：38.215/38.305 精确字段、参考点、误差要求、PRS/UL-RTOA 标准定义和 Release 差异。
- EXPERIMENT + NEEDS_VERIFICATION：所有现场可见性、检测概率、ToA/TDOA/位置误差和实时性能。

## 14. Related Notes

- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Standard Positioning Observables]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[02-PRACH/Timing Estimation]]
- [[04-PDSCH/UE Resource Extraction]]
- [[01-专题知识/信道估计与均衡/DM-RS]]
- [[01-专题知识/信道估计与均衡/SRS]]
- [[01-专题知识/信道估计与均衡/CSI-RS]]
- [[06-TDOA定位/TDOA]]
