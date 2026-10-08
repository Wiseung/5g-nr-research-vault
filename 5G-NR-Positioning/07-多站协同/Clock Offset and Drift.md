---
title: Clock Offset and Drift
aliases:
  - 站间时钟偏置与漂移
  - 采样时钟偏差
  - 多站时基模型
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/synchronization
  - topic/clock
  - topic/calibration
source:
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
related:
  - "[[07-多站协同/RF and Digital Delay Calibration]]"
  - "[[07-多站协同/Cross-Station Event Association]]"
  - "[[07-多站协同/Multi-Station Observation Fusion]]"
  - "[[07-多站协同/Synchronization Validation Ledger]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
---

# Clock Offset and Drift

> [!abstract] 模型边界
> 本页只描述接收站的时间基准、采样率偏差和重锁分段。它不把某种 GNSS/PPS/PTP 方案写成已验证的设备能力，也不替代 [[07-多站协同/RF and Digital Delay Calibration]] 的链路延迟校准。

## 1. 一句话定义

站间时钟模型把“每个站自己认为的时间”映射到一个显式参考时间轴，并分别记录固定偏置、频率偏差、随时间变化的漂移、重锁跳变和未建模残差。

## 2. 为什么要单独建模

TDOA 使用的是站间时间差。若两个站的时钟各自有未知偏置，单次差分会表现为固定距离差；若采样率不一致，误差会随捕获时长增长；若发生重锁，时间轴可能出现分段跳变。把这些效应都塞进一个 clock_bias 字段，会使校准、关联和几何诊断无法区分。

## 3. 三套时间坐标

| 坐标 | 例子 | 可回答的问题 | 不能自动推出 |
| --- | --- | --- | --- |
| 协议坐标 | frame/slot/symbol、PRACH RO | 事件在 NR 空口的哪个资源 | 站间绝对时间 |
| 采样坐标 | capture sample、window sample | 峰在文件中的哪个样点 | 物理参考面延迟 |
| 外部时基坐标 | PPS/PTP/触发时间戳 | 各站时间标签如何比较 | 信号是否为同一事件 |

一个 toa_raw_seconds 必须同时引用采样坐标和外部/协议参考点；只有文件中的样点索引而没有时间基准，不能称为跨站对齐。

## 4. 符号和单位

| 符号 | 含义 | 单位 | 备注 |
| --- | --- | --- | --- |
| $t$ | 理想参考时间 | s | 由项目选择的参考轴定义 |
| $u_i$ | 第 $i$ 站记录的时间 | s | 设备或软件输出 |
| $b_{i,0}$ | 相对参考站的固定偏置 | s | 符号必须在校准记录中固定 |
| $\alpha_i$ | 时间轴斜率/频率偏差 | 无量纲 | 常以 ppm 展示 |
| $q_i(t)$ | 未建模的慢变项 | s | 可与温度或锁定状态关联 |
| $\epsilon_i$ | 采样/估计随机误差 | s | 不能与固定偏置合并 |
| $F_{s,i}$ | 站点实际采样率 | samples/s | 必须区别标称值 |

如果工程日志使用 clock_offset、timestamp_bias 或 sample_rate_offset_ppm 等不同命名，应在适配层提供映射表，不要通过字段名猜正负号。

## 5. 基本时间模型

以一个公共参考时间 $t$ 表示站点 $i$ 的时间标签：

$$
u_i(t)
 =
t+b_{i,0}
+\alpha_i(t-t_{\mathrm{ref}})
+q_i(t)
+\epsilon_i(t).
$$

对同一事件的 ToA，可把传播和链路项另列：

$$
\widehat{\tau}^{raw}_{i,k}
 =
t_{0,k}
+\frac{\|\mathbf{x}_k-\mathbf{s}_i\|}{c}
+b_{i,0}
+\alpha_i(t_k-t_{\mathrm{ref}})
+d_i
+\epsilon_{i,k}.
$$

这里的 $\alpha_i$ 是工程上的局部斜率，不等同于设备内部全部振荡器噪声。若锁定状态变化，应用分段模型而不是把整段数据拟合成一条直线。

## 6. 采样率偏差如何积累

设实际采样率为：

$$
F_{s,i}=F_{s,\mathrm{nom}}(1+\delta_i),
\qquad
\delta_i\approx \mathrm{ppm}_i\times10^{-6}.
$$

若用标称采样率把长度为 $T$ 的样点换算成秒，时间轴误差的一阶量级为：

$$
\Delta t_i(T)\approx\delta_i T.
$$

该式只说明误差随观测时长累积的趋势；实际符号、重采样实现和时间戳定义必须用已知参考验证。短窗口看不出明显漂移，不代表长时间捕获可以忽略采样率偏差。

## 7. 时间同步、频率同步和相位同步的区别

| 名称 | 主要约束 | 在本项目中的可见症状 |
| --- | --- | --- |
| 时间同步 | 事件时间标签/秒边界 | 固定偏置、触发抖动、整段平移 |
| 频率同步 | 本振/采样时钟的速率 | TDOA 随时间漂移、CFO 或相关峰变化 |
| 相位同步 | 载波相位参考 | 相位差跳变、相干合并失败 |

某一层通过不等于其他层通过。TDOA 的时间闭合主要依赖时间轴和采样率，但参考序列相关质量还会受到 CFO、相位噪声和数字链路的影响。

## 8. 参考站与可辨识性

在差分系统中通常选择一个参考站 $r$，并设：

$$
b_{r,0}=0,\qquad \alpha_r=0.
$$

这只是坐标规范，不是说参考站没有真实误差。所有其他站的偏置都表示为相对参考站的量。若同时估计 UE 位置和未知站间钟差，单个事件通常不够提供全部约束；需要公共源、已知位置、多事件轨迹或外部时基锚点。

> [!warning] 不可辨识性
> 没有额外锚点时，位置偏移和站间固定钟差可能互相补偿。求解器给出一个坐标并不证明钟差已被正确估计。

## 9. 校准观测的来源

| 来源 | 估计对象 | 优点 | 限制 |
| --- | --- | --- | --- |
| 公共线缆/分配器参考源 | 站间固定差和短期漂移 | 路径可控、易重复 | 不包含真实空口多径 |
| 已知位置的空口源 | 时基与传播模型的联合残差 | 覆盖实际天线/环境 | 传播和 NLOS 会混入 |
| 外部 PPS/PTP/触发日志 | 时间戳和锁定状态 | 可直接审计时基事件 | 不一定描述 ADC 采样边界 |
| 长时重复事件 | 漂移趋势和重锁跳变 | 可观察运行状态 | 事件关联必须先可靠 |
| 盲自校准 | 统计上的相对偏置 | 不依赖专用参考 | 可辨识性和模型风险高 |

第一版应优先使用公共参考源建立基线，再用已知位置/长时数据验证；盲自校准只能作为明确标记的研究候选。

## 10. 固定偏置估计

对第 $k$ 个公共参考事件，令 $y_{i,k}$ 是站 $i$ 相对参考站的观测差：

$$
y_{i,k}=b_{i,0}+\eta_{i,k}.
$$

可用加权均值或稳健位置估计得到 $\widehat b_{i,0}$，但必须保存：

- 参考源和传播路径；
- 事件数、时间范围和每次观测；
- 异常值规则及被拒绝样本；
- 估计标准差或协方差；
- 估计所对应的频率、带宽和处理链。

固定偏置不能只保留一个四舍五入后的纳秒数字；原始样点差和浮点估计都应可回读。

## 11. 漂移估计

对多个时间点 $t_k$，可用局部线性模型：

$$
y_{i,k}
 =
b_{i,0}
+\alpha_i(t_k-t_{\mathrm{ref}})
+\eta_{i,k}.
$$

回归输出至少包括斜率、截距、残差、有效时间区间和状态。建议按以下条件切段：

- 锁定状态由 locked 变为 unlocked 或 holdover；
- PPS/PTP/触发丢失或恢复；
- 采样率、中心频率、带宽或滤波配置变化；
- 温度跨过已验证范围；
- 设备重启或时间戳计数器回绕。

分段边界应成为 clock_model_id 的一部分，而不是在后处理中被平滑掉。

## 12. 温度和环境变量

温度、供电、风扇状态和机箱热稳定过程可能与漂移相关，但当前 Vault 没有本项目硬件的响应曲线。可以把温度作为协变量候选：

$$
b_i(t,T)
 =
b_{i,0}
+\alpha_i(t-t_{\mathrm{ref}})
+\beta_i(T-T_{\mathrm{ref}})
+q_i(t).
$$

$\beta_i$ 只有在足够的温度覆盖、重复运行和独立验证后才能使用。没有这些证据时，保留温度字段并标 temperature_effect_unknown，不要套用其他设备的系数。

## 13. 重锁和时间轴分段

每一段时间轴至少记录：

~~~json
clock_segment_id: null
station_id: null
start_time: null
end_time: null
clock_source: null
lock_state: unknown
relock_count: null
offset_model: constant_or_linear
offset_seconds: null
drift_ppm: null
residual_std_seconds: null
validity: unknown
~~~

事件落在重锁边界附近时，默认降级为 clock_boundary_ambiguous，除非能证明边界前后时间计数连续且校准有效。跨段合并需要显式转换关系。

## 14. 校正和重采样的两种实现

### 14.1 时间戳域修正

保留原始样点，在时间标签上应用：

$$
t^{corr}=t^{raw}-\widehat b(t)-\widehat d.
$$

优点是原始 IQ 不变；缺点是下游算法必须支持非等间隔或带修正的时间轴。

### 14.2 波形域重采样

先用估计的 $\delta_i$ 把波形重采样到共同 $F_s$，再进行相关或峰估计。此时必须记录重采样滤波器、相位响应、边界补零和新增群时延。重采样后的样点索引不能直接冒充原始捕获索引。

两种实现可以并存做对照，但一个结果记录只能明确标识采用了哪一种，不能重复应用同一偏差修正。

## 15. 质量状态建议

| 状态 | 含义 | 允许用途 |
| --- | --- | --- |
| unknown | 没有足够时基证据 | 原始回放/故障统计 |
| observed | 有锁定日志和时间戳，但未校准 | 单站诊断、候选关联 |
| calibrated | 偏置/漂移模型和有效期齐全 | 形成 TDOA 候选 |
| degraded | 超出有效期、温度范围或残差门 | 降权或保留诊断 |
| invalid | 失锁、计数器回绕或模型冲突 | 禁止数值融合 |

状态应与数值字段分开。drift_ppm: 0 不能代表“已证明没有漂移”。

## 16. 与事件关联和 TDOA 的接口

进入 [[07-多站协同/Cross-Station Event Association]] 前，输出时基可比较窗口和最大不确定度；进入 [[07-多站协同/Multi-Station Observation Fusion]] 前，输出 clock_model_id、修正后的 ToA 和协方差。TDOA 模型仍由 [[06-TDOA定位/TDOA Measurement Model]] 负责，本站不重复定义差分矩阵。

## 17. 最小实现伪代码

~~~text
读取 station metadata 和原始 timestamp
    -> 按 lock/relock 事件切分 clock segment
    -> 用公共参考估计 offset/drift
    -> 计算模型残差和有效时间区间
    -> 对每个 observation 选择匹配的 clock_model_id
    -> 在 timestamp 域或 waveform 域应用一次修正
    -> 输出 raw/corrected 时间、残差、状态和协方差引用
~~~

## 18. 验证矩阵

| 场景 | 注入/条件 | 必须观察 |
| --- | --- | --- |
| C0 | 公共参考、短窗口、无重锁 | 固定偏置方向和重复性 |
| C1 | 延长捕获时长 | 漂移是否可从随机散布中分离 |
| C2 | 已知采样率偏差 | 时间误差随时长的趋势 |
| C3 | 人工重锁/断链 | 分段边界和状态降级 |
| C4 | 温度变化 | 相关性是否跨重复运行保持 |
| C5 | 时间戳域与波形域修正 | 两种实现的闭合差异 |
| C6 | 同一事件多站回放 | 进入融合前的残差和可用率 |

具体通过阈值由 [[07-多站协同/Synchronization Validation Ledger]] 预注册；本页不填未经运行的数值。

## 19. 常见误区

- 把 PPS 到达时间当作 ADC 第一个样点时间。
- 把标称采样率当作每站实际采样率。
- 用一条全局直线跨越重锁、换配置或温度跃迁。
- 把时钟偏置和 RF/滤波固定延迟混在同一个字段。
- 用未知漂移的站点参与 TDOA，再由位置残差倒推“自动校准成功”。

## 20. 证据与状态

- PERSONAL_NOTE：时间基准、采样偏差和分段字段承接既有多站同步与观测质量笔记。
- STANDARD + partial：NR 定位测量角色参考 TS 38.215/38.305；本页不是同步协议规范。
- HYPOTHESIS + NEEDS_VERIFICATION：温度模型、盲自校准和具体时基方案的可用性尚无本项目证据。
- EXPERIMENT + NEEDS_VERIFICATION：C0-C6 尚未运行，偏置、漂移和覆盖率字段保持空值。

## Related Notes

- [[07-多站协同/Multi-Station Synchronization]]
- [[07-多站协同/RF and Digital Delay Calibration]]
- [[07-多站协同/Cross-Station Event Association]]
- [[07-多站协同/Multi-Station Observation Fusion]]
- [[07-多站协同/Synchronization Validation Ledger]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[05-定位观测量/Timing Observation]]
- [[06-TDOA定位/TDOA Measurement Model]]
