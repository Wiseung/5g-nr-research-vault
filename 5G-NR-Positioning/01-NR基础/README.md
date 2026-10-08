---
title: 01-NR基础
type: directory-index
status: seed
---

# 01-NR基础

从时间轴、numerology、SCS 和 PRB/RE 网格开始，再用 TDD 方向标注连接到 PRACH/PDCCH。

- [[NR Frame Slot]]
- [[Numerology]]
- [[SCS]]
- [[PRB RE Resource Grid]]
- [[SSB PBCH MIB]]
- [[NR TDD]]

> [!abstract] 本目录的任务边界
> 本目录主责 NR 空口坐标，并补充初始同步到 MIB 的下行入口：时间（frame/slot/symbol）、频率（SCS/CRB/PRB/RE）、方向（D/U/F）和小区公共上下文。它不替代 PRACH 检测、PDCCH 盲搜或 TDOA 算法；相关信道的细节继续由 02/03/04 专题页负责，下游算法消费这里建立的坐标和状态。

## 学习目标与依赖

| 学完后应能回答的问题 | 依赖 | 下游产物 |
| --- | --- | --- |
| 一个样点属于哪个 frame/slot/symbol？ | OFDM、采样率、CP、同步起点 | `time_coordinate` |
| 一个频域 bin 属于哪个 SCS、BWP、PRB 和 RE？ | FFT、Point A、BWP、载波配置 | `frequency_coordinate` |
| 如何由下行同步进入 SIB1 的公共控制资源？ | PSS/SSS、SSB/PBCH、MIB、CORESET-0/SearchSpace0 | `cell_and_si_context` |
| 当前 symbol 是 D、U、F 还是未知？ | SIB1/RRC、TDD pattern、动态状态 | `direction_mask` |
| 哪些 RE 可以交给某个信号/用户？ | 资源分配、端口/层、参考信号 | `resource_snapshot` |
| 哪些时间片可以作为定位观测？ | 上述三类坐标、校准状态 | `timing_candidate` |

推荐顺序是：先建立时间轴、频率轴和资源网格，再学习 [[SSB PBCH MIB]] 的初始下行接收链，随后叠加 TDD 方向并进入 PDCCH/PDSCH。任何一个配置缺失时，输出应保留 `unknown` 或 `NEEDS_VERIFICATION`，不能用“常见参数”静默填充。

## 统一配置快照

五篇原子笔记共享一个 `config_snapshot` 概念。字段名可以按实现调整，但每次解析都应能回放出同一套坐标：

```json
config_id: <immutable-id>
release_or_toolbox_version: <explicit-or-null>
carrier_id: <id>
center_frequency_hz: <value-or-null>
mu: <value-or-null>
scs_hz: <value-or-null>
cp: <normal|extended|unknown>
n_fft: <value-or-null>
sample_rate_hz: <value-or-null>
point_a: <value-or-null>
bwp_start_crb: <value-or-null>
bwp_size_prb: <value-or-null>
tdd_config_id: <id-or-null>
frame_start_sample: <value-or-null>
coordinate_convention: <documented-string>
valid_from_capture_sample: <value-or-null>
valid_to_capture_sample: <value-or-null>
```

`config_id` 必须是不可变版本键；配置切换、重采样、FFT/CP 改变或时钟重锁都应生成新版本。`release_or_toolbox_version`、Point A、BWP 起点和 TDD 字段尚未在本项目锁定时，状态保持 `NEEDS_EXTERNAL_REFERENCE`，而不是把 null 改成默认值。

## 坐标闭环

```text
采集元数据/同步
    ↓
μ、SCS、FFT、CP、采样率
    ↓
frame → subframe → slot → OFDM symbol
    ↓
Point A/BWP → CRB → PRB → RE(k,l,p)
    ↓
TDD D/U/F + 物理信道/参考信号掩码
    ↓
PRACH/PDCCH/PDSCH/PUSCH 资源快照
    ↓
单用户片段 → ToA/RToA → 多站 TDOA
```

这条链有三个必须保持的交叉约束：

1. 时间和频率坐标必须引用同一个 `config_id`，不能让 PRACH 使用一套 SCS、PDCCH 使用另一套 FFT。
2. 方向掩码与资源掩码取交集后才是可检测集合：`usable = resource ∩ direction ∩ capture_valid`。
3. 定位时间戳必须同时保留样点、空口坐标和校准字段；一个未经校准的峰值不能直接写成传播时间。

## 从 IQ 到定位的最小闭环

| 阶段 | 输入 | 最小验收输出 | 失败时的降级 |
| --- | --- | --- | --- |
| 1. 同步与 numerology | IQ、采样率、同步候选 | `config_id`、μ/SCS、帧起点和置信度 | `unknown_time_base` |
| 2. Frame/slot 切分 | 时间配置、CP/FFT | 不重叠的 symbol 样点区间 | `boundary_uncertain` |
| 3. TDD 标注 | SIB1/RRC 或外部配置 | symbol 级 D/U/F/unknown | `direction_unknown` |
| 4. 资源网格 | Point A、BWP、资源分配 | 坐标原点、RE 掩码、端口/层维度 | `resource_partial` |
| 5. 单用户观测 | 合法 UL 资源、参考序列 | 原始峰、峰策略、质量和校准字段 | `toa_unreliable` |
| 6. 多站对齐 | 各站 `event_id`、时钟/RF 校准 | 可用站集合、TDOA 和残差 | `partial_observation` |

第 1--4 阶段通过后才进入 [[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]] 或 [[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]。这不是“先做完整译码再定位”的要求：定位支路可以使用已知参考序列，但仍必须保留用户/资源/时序关联证据。

## 关键不变量

在普通 CP、单一 numerology 的常见近似下，可先用以下关系做数量级检查：

$$
\Delta f=15\times2^\mu\ \mathrm{kHz},\qquad
N_{slot}^{frame}=10\times2^\mu,qquad
N_{SC}^{PRB}=12.
$$

若 `F_s=N_FFT·Δf`，则样点网格间隔为 `1/F_s`；它与由有效占用带宽决定的时延分辨率不是同一个量。所有公式只用于结构和数量级检查，精确 CP、资源表、TBS 和定位测量定义仍需对应 Release 的外部核验。

## 验收清单

- [ ] 每个捕获片段有唯一 `capture_id` 和不可变 `config_id`。
- [ ] `mu`、SCS、FFT、CP、采样率和 BWP/Point A 的单位与来源已记录。
- [ ] symbol 样点区间采用左闭右开约定，区间不重叠且能处理跨帧/丢样。
- [ ] D/U/F/unknown 在 symbol 级保存，flexible 和 guard 不被静默改写。
- [ ] RE 掩码保存局部索引、绝对频率、端口/层维度和生成规则。
- [ ] 定位支路保留原始 I/Q、原始峰、校准项、峰策略和质量标志。
- [ ] 标准定位（PRS、UL-TDOA、Multi-RTT 等）与项目定制被动观测分别标注。
- [ ] 未锁定的 Release、RRC 字段和 MATLAB API 仍显示 `NEEDS_EXTERNAL_REFERENCE`。

## 证据入口

| 主题                   | Vault 来源                                                               | 外部核验入口                                                      |
| -------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| 物理网格、numerology、OFDM | [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]      | [3GPP TS 38.211](https://www.3gpp.org/DynaReport/38211.htm) |
| TDD/控制时机             | [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control]] | [3GPP TS 38.213](https://www.3gpp.org/DynaReport/38213.htm) |
| 数据资源和层/MCS 接口        | [[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]]    | [3GPP TS 38.214](https://www.3gpp.org/DynaReport/38214.htm) |
| 定位测量/架构              | [[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]]                 | TS 38.215/38.305，当前为 `NEEDS_EXTERNAL_REFERENCE`<br>         |

本目录的 `STANDARD + partial` 只表示对应 Vault 参考笔记覆盖了该主题；它不表示当前项目已经完成现场配置恢复、工具箱运行或标准符合性测试。
