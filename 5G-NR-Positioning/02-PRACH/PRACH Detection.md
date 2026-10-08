---
title: PRACH Detection
aliases:
  - NR PRACH 检测
  - PRACH 相关检测
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - process/detection
  - process/correlation
  - topic/定位
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 用户项目流程说明
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Overview|PRACH Overview]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]"
  - "[[5G-NR-Positioning/02-PRACH/Timing Estimation|Timing Estimation]]"
  - "[[03-仿真与实验/5G定位/仿真：PRACH 检测与 RA 事件关联|现有 PRACH 检测实验]]"
---
# PRACH Detection

## 1. 一句话定义

PRACH Detection 是在合法 RO 内对候选前导做相关、门限和峰筛选，以输出前导是否存在、位置和质量，而不是解码 C-RNTI 的步骤。

## 2. 为什么项目需要它

它是第一阶段可运行的核心单元：检测输出触发 RA-RNTI 候选和 RAR 监测，并提供粗 ToA/功率。可靠检测必须能区分无能量、单峰、多峰、碰撞和多径，不应只返回一个布尔值。

## 3. 它位于整个 5G 空口链路的什么位置

它接收同步/配置/本地前导，位于 PRACH Preamble 之后、Timing Estimation 与 Random Access Procedure 之前；检测通过后才进入 RA-RNTI→RAR→Msg3/Msg4。

## 4. 输入

- 连续 IQ、捕获时间戳、采样率、CFO/噪声估计。
- 由 PRACH Configuration 展开的 RO 和前导候选。
- ZC 根序列、循环移位和检测窗口。

## 5. 输出

每个峰至少保存 preamble_index、RO 时频坐标、相关峰值/归一化方式、整数/亚采样偏移、阈值、CFO、多径峰、碰撞标记和状态（energy_seen、preamble_detected、ambiguous、rejected）。

## 6. 关键参数

相关器长度、匹配滤波实现、门限/CFAR 规则、峰间距、旁瓣抑制、最大保留峰数、CFO 搜索范围、窗口边界和质量门限。门限应与噪声估计和带宽绑定，不能照搬一个绝对幅度。

## 7. 时域位置

只在 RO 合法窗口内处理，窗口起点应由帧/时隙/符号同步和 PRACH CP 决定。输出时延是相对捕获起点或 RO 参考点的样点偏移，绝对到达时间还需硬件/时钟校准。

## 8. 频域位置

检测可以在时域相关，也可先在 PRACH 频域资源提取后处理；两者都必须保留 RO 的频域起点、PRACH SCS 和有效带宽。不能在整段 IQ 上不加资源约束地搜索所有 ZC 序列。

## 9. 数学原理

对候选参考 $u_p[n]$，归一化相关可写为

$$
z_p[\ell]=\frac{\left|\sum_n r[n]u_p^*[n-\ell]\right|^2}
{\left(\sum_n|r[n]|^2\right)\left(\sum_n|u_p[n]|^2\right)}.
$$

当 $z_p[\ell]$ 超过门限且峰形、峰距和资源约束通过时，输出候选事件。多径会产生峰簇，碰撞会产生多个移位峰；门限通过不等于用户唯一识别。

## 10. 3GPP 对应规范

- TS 38.211 §5.3.2、§6.3.3.1/§6.3.3.2：PRACH OFDM 波形、序列和资源映射。
- TS 38.213 §8.1：RO/检测时机及前导传输上下文。
- TS 38.321 §5.1.3：随机接入前导发送过程；检测器本身的门限和峰策略属于实现，不是规范固定算法。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHDetect：官方时域 PRACH 检测入口，返回检测到的前导和样点偏移；现有实验页提醒多实例 strongest peak 限制。
- nrPRACHConfig、nrPRACH、nrPRACHIndices：构造配置、生成参考序列和资源索引。
- nrTimingEstimate：可作为通用参考信号时延估计接口，但是否适合 PRACH 及输入维度需本机核验。

函数名和返回字段均为 `NEEDS_EXTERNAL_REFERENCE` 的 API 线索；实际 Release、输入维度和多峰行为需在本机测试。

## 12. 本项目中的用途

检测通过后生成事件键 (cell,frame,slot,RO,preamble)，交给 [[5G-NR-Positioning/02-PRACH/Timing Estimation|Timing Estimation]] 和 [[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]；只有后续 RAR/Msg3/Msg4 证据成立，才进入 C-RNTI 候选池。现有实现思路见 [[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]。

## 13. 常见误区

- 把 strongest peak 输出当作多用户检测结果。
- 只看相关峰，不记录门限、旁瓣、CFO 和全轨迹。
- 把检测成功当作 RAR、临时 C-RNTI 或最终 C-RNTI 已获得。
- 把无峰直接解释为现场没有 UE。

## 14. 与相似概念的区别

检测回答“某个 RO/前导是否存在”；Timing Estimation 回答“峰对应的相对到达位置”；RA-RNTI 由 RO 上下文计算；RAR/Msg3/Msg4 是协议消息；C-RNTI 是后续用户关联键。检测不是解码器。

## 15. 代码实现注意事项

- 先按 RO 分桶，再按前导和移位做相关，减少无约束搜索。
- 统一相关峰索引、样点起点、采样率和单位。
- 同时输出全峰轨迹和筛选后峰列表，支持碰撞回放。
- 将检测状态与协议关联状态分开存储，失败原因可枚举。

## 16. 待实验验证的问题

- 单径/AWGN/CFO/多径/碰撞下的检测率、虚警率和 ToA RMSE。
- 自定义全峰检测与 nrPRACHDetect 的输出差异。
- 门限随 PRACH 带宽、噪声和接收增益变化的稳定性。
- 现场采样窗口是否覆盖完整 RO、CP 和可能的 TA 范围。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Overview|PRACH Overview]]、[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]、[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]、[[5G-NR-Positioning/02-PRACH/Timing Estimation|Timing Estimation]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]。
- 实验与旧笔记：[[03-仿真与实验/5G定位/仿真：PRACH 检测与 RA 事件关联|PRACH 检测实验]]、[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]、[[01-专题知识/信道估计与均衡/02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别|PRACH 相关检测边界]]。

## 18. 接收机分层流程

检测器的责任是把“连续 IQ”变成带证据的 `prach_detection_event`。每层都应保留输入、输出和失败原因，不能在最后一步才猜测前面的资源坐标。

```text
连续 IQ/时间戳
    ↓
小区、帧、时隙、采样率与 CFO/噪声状态
    ↓
RACH 配置展开 → 合法 RO 列表与窗口
    ↓
按 RO 分桶（时域窗口、频域窗口、载波/波束上下文）
    ↓
生成根序列/循环移位参考并做长度、相位、能量自检
    ↓
预处理（DC/邻带抑制、增益记录、可选 CFO 搜索或补偿）
    ↓
时域匹配滤波或频域相关
    ↓
归一化统计量 → 噪声估计 → CFAR/门限
    ↓
局部峰、旁瓣、峰簇和候选前导筛选
    ↓
整数/亚采样偏移与质量字段
    ↓
preamble 事件 → [[5G-NR-Positioning/02-PRACH/Timing Estimation|Timing Estimation]] / RA-RNTI
```

建议把每层的状态拆开：`config_status`、`window_status`、`reference_status`、`correlation_status`、`decision_status` 和 `association_status`。例如 `preamble_detected` 只表示相关判决通过，不表示 `rar_matched` 或 `c_rnti_confirmed`。

## 19. RO 分桶与窗口契约

### 19.1 RO 桶键

一个检测任务的最小桶键应能唯一确定“在哪个资源、用哪套参考、相对哪个时间点解释峰”：

```yaml
ro_key:
  cell_id: null
  carrier_id: null
  ul_carrier_id: null
  frame: null
  slot: null
  start_symbol: null
  freq_occasion: null
  ssb_or_beam: null
  prach_format: null
  prach_scs: null
  config_id: null
  release_or_toolbox_version: NEEDS_EXTERNAL_REFERENCE
```

`frame/slot/start_symbol` 是协议坐标，`sample_start/sample_stop` 是设备坐标，两者必须同时保存。`freq_occasion`、Point A/BWP 偏移和局部 FFT bin 也要分开记录；数组列号不能直接当作绝对频点。

### 19.2 窗口生成

对每个 RO 生成如下窗口契约：

| 字段                    | 含义                                              | 缺失时处理               |
| ----------------------- | ------------------------------------------------- | ------------------------ |
| `sample_start`        | 相对捕获起点的候选起点                            | `window_unresolved`    |
| `sample_stop`         | 可处理的末端（含必要保护）                        | `window_truncated`     |
| `sequence_start/stop` | 去除 CP/保护后的序列主体                          | 不执行相关               |
| `guard_left/right`    | 防止同步边界和邻接资源污染的保护区                | 标`NEEDS_VERIFICATION` |
| `freq_bins`           | PRACH 有效频域资源                                | 不在全带宽盲搜           |
| `reference_time`      | `capture_start`/`ro_start`/`sequence_start` | 交给 ToA 页处理          |

窗口长度不能用固定“一个 slot 或 14 个符号”代替。长、短前导、不同 PRACH SCS、采样率和实现滤波器都可能改变样点数；准确映射依赖锁定的 38.211/38.213 Release，当前为 `NEEDS_EXTERNAL_REFERENCE`。

### 19.3 桶级预检

在相关前先做结构检查，失败就不要产生“无用户”结论：

1. `sample_start < sample_stop` 且窗口完全落在捕获数据内。
2. 采样率、中心频率、PRACH SCS、FFT 约定与 `config_id` 一致。
3. TDD 方向允许该 RO；flexible/guard 区不被默认为 UL。
4. 频域资源没有越过采集带宽或数字滤波通带。
5. 前导候选集合非空，根/循环移位映射可追溯。

## 20. 参考生成与一致性检查

### 20.1 生成链

参考生成器的输入、输出和版本边界建议固定为：

```text
config_id + preamble_index
    ↓
逻辑根索引 → 物理根索引（标准映射）
    ↓
L_RA、zero-correlation zone、restricted set
    ↓
循环移位 C_v 与前导索引映射
    ↓
序列域参考
    ↓
PRACH 频域资源/FFT/CP/相位约定
    ↓
与接收窗口同采样率的时域模板
```

逻辑到物理根索引、奇偶长度公式、`C_v` 表和 restricted set 的精确规则须回到 TS 38.211 对应版本核验；本页不重复硬编码标准表。

### 20.2 参考自检

每次加载参考后至少记录：

- `reference_length`、复数精度、平均/峰值能量和归一化因子。
- 相位符号、共轭方向、循环移位方向和 0/1 基索引约定。
- 参考的时域起点、CP 是否包含在模板中、FFT 长度和频域起点。
- 同根序列不同循环移位的相关轨迹；异常高旁瓣标为 `reference_mismatch`。
- 多天线模板是否共用相位基准；未校准时只做非相干合并。

参考序列逐点相等只能证明序列层一致，不能证明 RO 资源映射、采样率或接收机时间参考一致。

## 21. 相关器实现

### 21.1 时域匹配滤波

对长度为 $L$ 的模板 $u_p[n]$，窗口内线性相关可以写为：

$$
c_p[\ell]=\sum_{n=0}^{L-1}r[\ell+n]u_p^*[n],
\qquad
P_p[\ell]=|c_p[\ell]|^2.
$$

`\ell` 是窗口内局部索引。实现必须明确是 `valid`、`same` 还是带零填充的边界模式；边界样本不足时不能把补零造成的低能量峰当作真实路径。

### 21.2 频域相关与分块处理

对接收块 $r$ 和模板 $u_p$，取 $N\ge L_r+L_u-1$ 的零填充 FFT，可用：

$$
c_p=\operatorname{IFFT}\left\{\operatorname{FFT}(r,N)
\,\operatorname{conj}\left[\operatorname{FFT}(u_p,N)\right]\right\}.
$$

连续流应使用 overlap-save/overlap-add，并丢弃受块边界污染的样本。PRACH 序列的周期相关可在序列周期内取模，但周期索引与捕获绝对时间不是同一坐标；需要先保留周期索引，再依据 RO 窗口和 CP 约束做 unwrap。

### 21.3 多天线合并

第 $a$ 根天线的相关功率为 $P_{p,a}[\ell]$。未做相位校准时，优先采用非相干统计量：

$$
P_p^{\mathrm{NC}}[\ell]=\sum_a w_aP_{p,a}[\ell],
$$

其中 $w_a$ 与增益或噪声估计有关。只有在天线相位、群时延和采样起点已校准时，才考虑

$$
P_p^{\mathrm{C}}[\ell]=\left|\sum_a w_a c_{p,a}[\ell]\right|^2.
$$

两种统计量不能混用同一阈值；日志必须记录 `combining_mode`。

### 21.4 相关伪代码

```python
for ro in valid_ro_list:
    bucket = slice_iq(capture, ro.sample_start, ro.sample_stop)
    if bucket.status != "ok":
        emit(ro, state="window_truncated", reason=bucket.reason)
        continue

    refs = generate_references(ro.config_id, ro.preamble_candidates)
    for preamble in refs:
        traces = []
        for cfo_hz in cfo_grid_or_zero:
            block = derotate(bucket.iq, cfo_hz, bucket.sample_origin)
            trace = correlate(block, preamble.template, mode="td_or_fft")
            traces.append(score(trace, cfo_hz))
        trace = select_cfo_hypothesis(traces)
        statistic = normalize(trace, bucket.noise_and_energy)
        threshold = estimate_threshold(statistic, bucket.training_cells)
        peaks = find_local_peaks(statistic, threshold, ro.peak_policy)
        peaks = suppress_sidelobes_and_cluster(peaks, ro.peak_policy)
        emit_candidates(ro, preamble, peaks, trace, threshold)

finalize_ro_events()  # 只更新检测状态，不直接写入 C-RNTI
```

`cfo_grid_or_zero`、峰距、保留峰数和聚类半径都是实现参数，不是本页提供的标准固定值。

## 22. 归一化、噪声估计与 CFAR

### 22.1 统计量选择

若 $E_r[\ell]$ 是与模板重叠的接收能量、$E_u$ 是模板能量，可用归一化匹配统计量：

$$
\rho_p[\ell]=
\frac{|c_p[\ell]|^2}
{(E_r[\ell]+\epsilon)(E_u+\epsilon)}.
$$

固定模板能量而不计算滑动 $E_r[\ell]$ 会使 AGC、窗口边界和突发干扰改变统计量。epsilon 只防止数值除零，不能用来掩盖低能量窗口。

也可保存未归一化 $P_p[\ell]$、噪声归一化 $P_p[\ell]/\hat\sigma^2$ 和 $\rho_p[\ell]$ 三条轨迹，便于追查增益与带宽变化。

### 22.2 训练单元与保护单元

CFAR 应在候选峰周围排除 guard cells，再从 training cells 估计背景。训练单元必须避开：

- 同一 RO 的其他候选峰和已知旁瓣区。
- 相邻 UL 资源泄漏、同步信号和捕获边界。
- CFO 搜索产生的重复峰。

训练单元不足、背景非平稳或整桶被占用时，应输出 `threshold_unstable`，而不是强行用全局均值。

### 22.3 可记录的门限模型

CA-CFAR 的工程抽象为：

$$
\hat P_N[\ell]=\frac{1}{K}\sum_{k\in\mathcal{T}(\ell)}P[k],
\qquad
T[\ell]=\alpha\hat P_N[\ell].
$$

`\mathcal{T}` 是训练单元集合，`\alpha` 由目标虚警率、样本数和噪声分布假设决定。OS-CFAR、GO-CFAR 等可在非均匀背景使用，但排序规则、`\alpha` 和目标 `P_FA` 必须在实验中核验；不写死一个跨设备通用常数。建议日志至少包含 `threshold_method`、`training_count`、`guard_count`、`noise_estimate`、`target_pfa`（若有）和 `threshold_source`。

## 23. 峰值、旁瓣与多峰处理

### 23.1 峰候选与抑制

局部峰候选应同时满足：门限通过、落在有效序列窗口、不是边界伪峰，并且与模板自相关的旁瓣解释一致。对候选按峰值从高到低做非极大值抑制时，抑制距离应来自模板主瓣/零相关区和当前采样率，不能任意使用一个样点常数。

建议每个峰保存：

| 字段                          | 说明                                   |
| ----------------------------- | -------------------------------------- |
| `peak_index_local`          | 相对相关轨迹起点的整数索引             |
| `peak_power_raw/normalized` | 原始和归一化峰值                       |
| `threshold_at_peak`         | 峰所在位置实际门限                     |
| `prominence`                | 相对邻域背景的峰突出度                 |
| `pslr_db`                   | 主峰相对最大旁瓣的比值，主瓣定义须记录 |
| `width_samples`             | 峰宽估计及算法                         |
| `cluster_id`                | 多径/碰撞候选簇                        |
| `peak_rank`                 | 在同一前导/RO 内的排序                 |

### 23.2 多径与碰撞的区分

- 同一前导、相近时间的多个峰更像多径，但高反射路径也可能比首径强。
- 不同循环移位或不同前导参考均有独立峰，可能是碰撞，也可能是旁瓣、参考错配或邻接干扰。
- 只有在配置、参考、CFO 和峰距均通过检查后，才把 `collision_suspected` 作为候选诊断；不能从峰数直接推导 UE 数。

输出应保留 `multipath_suspected`、`collision_suspected`、`ambiguous` 三个可并存标志，并附 `diagnostic_reasons[]`。

### 23.3 CFO 搜索与残差

粗频偏可用假设网格 $f_q$ 搜索：

$$
r_q[n]=r[n]e^{-j2\pi f_q n/F_s},
\qquad
q^*=\arg\max_q\max_\ell P_{p,q}[\ell].
$$

该方法的网格间隔、搜索范围和最大值判据是实现选择。可把 `cfo_hypothesis_hz`、`cfo_metric_loss`、`residual_cfo_estimate` 和补偿前后峰值分别写入事件。残余 CFO 仍可能造成峰展宽、相位旋转和多天线不一致，不能只记录“已补偿”。

### 23.4 峰簇策略

检测器保留全峰后，由下游 Timing Estimation 选择：`strongest`、`first_detected` 或 `cluster`。检测页只负责报告候选和诊断，不把某一种策略强制当成真值。

## 24. 检测事件 schema

以下 schema 是项目日志契约，不是 3GPP 标准数据结构；未知项保持 `null` 或 `unknown`。

```js
event_type: prach_detection
event_schema_version: "0.1"
event_id: null
capture_id: null
station_id: null
config_id: null
release_or_toolbox_version: NEEDS_EXTERNAL_REFERENCE
ro:
  cell_id: null
  carrier_id: null
  ul_carrier_id: null
  frame: null
  slot: null
  start_symbol: null
  freq_occasion: null
  ssb_or_beam: null
  sample_start: null
  sample_stop: null
  reference_time: ro_start
candidate:
  preamble_index: null
  logical_root_index: null
  physical_root_index: null
  cyclic_shift: null
  l_ra: null
correlation:
  method: td|fft|unknown
  combining_mode: noncoherent|coherent|single_antenna|unknown
  template_length: null
  normalization: sliding_energy|fixed_energy|noise_normalized|unknown
  cfo_hypothesis_hz: null
  trace_path: null
peaks:
  - peak_index_local: null
    peak_power_raw: null
    peak_power_normalized: null
    threshold_at_peak: null
    pslr_db: null
    width_samples: null
    cluster_id: null
    peak_rank: null
decision:
  state: config_unresolved|window_truncated|reference_mismatch|energy_seen|preamble_detected|ambiguous|cfo_unresolved|threshold_unstable|rejected
  collision_suspected: false
  multipath_suspected: false
  diagnostic_reasons: []
quality:
  snr_or_metric: null
  noise_estimate: null
  threshold_method: null
  resource_check: pass|fail|unknown
  toa_status: pending|valid|unreliable|unknown
evidence:
  standard: STANDARD+partial
  implementation: PERSONAL_NOTE
  experiment: NEEDS_VERIFICATION
```

`event_id` 需包含 RO 上下文和候选前导，但不应把 preamble index 当作用户 ID。若多个峰暂不能判定是否同一用户，使用同一 `ro_event_id` 加不同 `candidate_id/cluster_id`，不要覆盖原始峰。

## 25. 状态与失败原因

| 状态                    | 进入条件                      | 可否交给 Timing Estimation | 说明                     |
| ----------------------- | ----------------------------- | -------------------------- | ------------------------ |
| `config_unresolved`   | 配置/Release 不完整           | 否                         | 等待外部配置或人工核验   |
| `window_truncated`    | RO 窗口越界或 CP/序列主体不足 | 否                         | 不能解释为无前导         |
| `reference_mismatch`  | 序列长度、相位或映射自检失败  | 否                         | 先修参考生成             |
| `energy_seen`         | 桶内有超背景能量但相关未通过  | 可作诊断                   | 可能是邻带、截断或错配置 |
| `preamble_detected`   | 相关、资源和门限均通过        | 是                         | 仍可能多径/碰撞          |
| `ambiguous`           | 多个解释均满足门限            | 是但降级                   | 必须保留候选集合         |
| `collision_suspected` | 多前导/峰组合符合碰撞特征     | 是但禁止唯一化             | 不是用户数结论           |
| `cfo_unresolved`      | CFO 假设间差异过大或峰不稳定  | 可作诊断                   | ToA 质量降级             |
| `threshold_unstable`  | 训练单元不足/背景非平稳       | 否或降级                   | 不输出硬判决             |
| `rejected`            | 峰未满足资源/旁瓣/质量规则    | 否                         | 保存拒绝原因和轨迹       |

一个事件可以同时有 `decision.state=preamble_detected` 和 `collision_suspected=true`；状态字段与诊断标志不要互相覆盖。

## 26. 指标与场景矩阵

### 26.1 指标定义

按真实前导事件统计检测概率：

$$
P_D=\frac{N_{\mathrm{true\ events\ detected}}}
{N_{\mathrm{true\ events}}},
\qquad
P_{FA}=\frac{N_{\mathrm{false\ events}}}
{N_{\mathrm{empty\ RO\ trials}}}.
$$

必须在实验记录中声明“事件”是前导、候选峰还是 RO。碰撞时分别报告：真实前导召回率、误拆分率、漏拆分率和错误增加用户数；不要把同一 RO 的多个峰重复计入普通虚警。建议同时记录资源坐标准确率、峰索引误差、门限越界率、`ambiguous` 比例、`threshold_unstable` 比例和每 RO 计算耗时。

### 26.2 场景矩阵

| 场景             | 控制变量                     | 必须观察                      | 预期失败标签/边界                      |
| ---------------- | ---------------------------- | ----------------------------- | -------------------------------------- |
| D0 单径无噪声    | 已知根、移位、整数延迟       | RO、前导、峰索引闭合          | 任何偏差先查参考/窗口                  |
| D1 AWGN 空 RO    | SNR、噪声种子、目标`P_FA`  | $P_D$、$P_{FA}$、门限分布 | 不填虚构阈值                           |
| D2 CFO           | CFO 大小、补偿状态           | 峰损失、展宽、残余频偏        | `cfo_unresolved`                     |
| D3 多径/NLOS     | 路径延迟/功率、随机种子      | 峰簇、首径/最大峰差异         | `multipath_suspected`                |
| D4 同 RO 碰撞    | 前导组合、功率差、时延差     | 多峰召回与错误拆分            | `collision_suspected`/`ambiguous`  |
| D5 旁瓣/邻接干扰 | 参考错配、带外能量、窗口邻接 | PSLR、误峰位置                | `reference_mismatch` 或 `rejected` |
| D6 截断/采样漂移 | 窗口边界、采样率偏差         | 边界峰和资源标签              | `window_truncated`                   |
| D7 多天线        | 相位/增益校准状态            | 相干与非相干合并差异          | 未校准不得声称增益                     |

## 27. 最小验证步骤

1. **配置闭合**：导出 `config_id`，枚举至少一个 RO，检查协议坐标到样点窗口、频域 bin 和方向标签的映射；保存检查报告。
2. **参考闭合**：在无噪声单径合成波形中注入已知前导和整数延迟，验证模板长度、共轭方向、移位索引和峰位置；只做结构闭合，不称为标准一致性证明。
3. **空桶虚警**：对没有前导的捕获或合成空 RO 运行同一 CFAR，保存训练/保护单元和每个拒绝峰；报告实际样本数后再估计 ($P_{FA}$)。
4. **扰动回放**：逐一加入 CFO、分数延迟、多径和窗口截断，确认状态从 `preamble_detected` 降级到可解释失败，而不是静默输出一个峰。
5. **碰撞回放**：用至少两个已知循环移位构造同 RO，比较全峰轨迹与单峰 API；若 API 只给 strongest，明确记录该能力缺口。
6. **跨实现对照**：只有在本机具备对应 MATLAB/5G Toolbox Release 时，才运行 `nrPRACHDetect` 等 API，并保存 `ver`、输入维度、返回字段和原始波形；否则维持 `NEEDS_EXTERNAL_REFERENCE`。
7. **回读审计**：从事件 schema 反查原始 IQ、配置快照、相关轨迹、门限和失败原因，确保没有只剩最终布尔值的不可回放记录。

## 28. 证据分层与未决项

| 层级                             | 本页允许的内容                                          | 当前状态                                          |
| -------------------------------- | ------------------------------------------------------- | ------------------------------------------------- |
| `STANDARD`                     | 38.211/38.213 对 PRACH 波形、资源和 Occasion 的职责边界 | `STANDARD + partial`；精确表值需按 Release 核验 |
| `PERSONAL_NOTE`                | 项目中的事件键、RA-RNTI/RAR 关联边界和接收流程          | 作为项目约定，不升级为规范要求                    |
| `PERSONAL_NOTE`/`HYPOTHESIS` | 匹配滤波、归一化、CFAR、峰聚类和事件 schema 建议        | 算法选择待实验比较，不是规范固定算法              |
| `EXPERIMENT`                   | 真实检测率、虚警率、ToA 误差、碰撞召回和耗时            | 尚未运行，`NEEDS_VERIFICATION`                  |
| `NEEDS_EXTERNAL_REFERENCE`     | `nrPRACHDetect`、`nrPRACHConfig` 等函数名线索       | 签名、返回字段、多峰行为需本机版本核验            |

未决项包括：项目锁定 Release、真实 RACH 配置、设备采样率/滤波群时延、CFO 与时钟校准、碰撞判决准则、首径定义以及是否存在 2-step/CFRA 分支。在这些信息补齐前，不能把本页的实现建议写成 conformance、现场覆盖率或用户识别结论。
