---
title: Numerology
aliases:
  - NR Numerology
  - NR 数字学
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/numerology
  - topic/timing
  - topic/scs
  - stage/基础
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 01-专题知识/信道估计与均衡/01 5G 物理层与信道模型
related:
  - "[[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]"
  - "[[5G-NR-Positioning/01-NR基础/SCS|SCS]]"
  - "[[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]"
  - "[[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]"
---

# Numerology

## 1. 一句话定义

NR numerology 用整数参数 `mu` 规定一组相互耦合的子载波间隔、OFDM 时间尺度、slot 周期和采样/资源映射约定。

## 2. 为什么项目需要它

项目要从 IQ 样点恢复 PRACH occasion、PDCCH 候选和 PDSCH/PUSCH 资源；`mu` 错一档会同时造成频率栅格、符号边界、TDD 方向和 ToA 解释错误。

## 3. 它位于整个 5G 空口链路的什么位置

Numerology 是同步与资源网格之间的全局配置层：

```text
SCS/μ → Frame/Slot → PRB/RE grid → TDD/PRACH/PDCCH/PDSCH → timing observation
```

它不直接产生 C-RNTI，但决定后续每个协议对象的时频坐标。

## 4. 输入

- 网络/小区配置中的 SCS 或 numerology 索引。
- 载波带宽、BWP、FFT、采样率和 CP 选择。
- 设备采集的中心频率、采样率及同步状态。

## 5. 输出

- `mu` 与 `Delta_f` 的一致配置。
- 有效 OFDM symbol、slot、frame 的时间尺度。
- 资源网格频率轴、采样率和 CP 相关参数。
- 提供给 PRACH、PDCCH、PDSCH 解析器的配置快照。

## 6. 关键参数

| 参数 | 关系/含义 | 注意 |
|---|---|---|
| `mu` | numerology 索引 | 支持范围由 Release/信号类型约束 |
| `Delta_f` | SCS | 与 `mu` 同一快照保存 |
| `N_FFT` | 采样域变换长度 | 不等于有效子载波数 |
| `F_s` | 采样率 | 需满足当前 FFT/SCS 约定 |
| `T_u` | 无 CP 的 OFDM symbol 时长 | `1/Delta_f` |
| `T_slot` | slot 周期 | 普通 CP 下常用 `1 ms/2^mu` |

## 7. 时域位置

常用关系为：

$$
\Delta f=15\times2^\mu\ \mathrm{kHz},\qquad
T_u=\frac{1}{\Delta f},\qquad
T_{slot}\approx\frac{1\ \mathrm{ms}}{2^\mu}.
$$

CP 会改变完整 symbol 的持续时间；因此 `T_u` 不能直接替代带 CP 的 symbol 周期。Frame/slot 的编号和边界见 [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]。

## 7.1 基础时间单位

为了避免把“有用符号时间”和“采样时钟”混在一起，建议在配置账本中同时保存三层时间：

| 层 | 记号 | 用途 | 备注 |
| --- | --- | --- | --- |
| 子载波/有用符号 | $\Delta f,\ T_u$ | 频率轴和去 CP 后的 FFT 窗口 | $T_u=1/\Delta f$ |
| 空口组织 | $T_{slot},\ T_{subframe},\ T_{frame}$ | 调度、TDD 和事件索引 | slot 还要叠加 CP |
| 设备采样 | $F_s,\ T_s^{(sample)}$ | IQ 样点和跨站时间戳 | 不等于规范的 $T_u$ |

在 TS 38.211 的常用基本时间单位表示中，还会出现参考采样周期 $T_c$ 和 NR 参考时间单位 $T_s$。其形式可写为：

$$
T_c=\frac{1}{\Delta f_{\max}N_f},\qquad
T_s=\frac{1}{\Delta f_{\mathrm{ref}}N_{f,\mathrm{ref}}},
\qquad T_s=64T_c.
$$

上式用于解释规范整数计数与实现样点之间的关系；$\Delta f_{\max}$、$N_f$ 及参考常数的精确取值和适用 Release 应以项目锁定的 TS 38.211 原文复核，当前状态为 <code>NEEDS_EXTERNAL_REFERENCE</code>。工程代码应把规范计数先转换为秒，再转换为设备样点，不能直接把两套整数下标相加。

## 7.2 数值例子

下面是一个**说明性**配置，不代表现场网络参数：

| $\mu$ | SCS | $T_u$ | 普通 CP 下的 slot 近似 | 每 1 ms 的 slot 数 |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 15 kHz | 66.667 μs | 1 ms | 1 |
| 1 | 30 kHz | 33.333 μs | 500 μs | 2 |
| 2 | 60 kHz | 16.667 μs | 250 μs | 4 |
| 3 | 120 kHz | 8.333 μs | 125 μs | 8 |
| 4 | 240 kHz | 4.167 μs | 62.5 μs | 16 |

例如 $\mu=2$、$N_{FFT}=1024$、$F_s=61.44$ MHz 时，满足 $F_s=N_{FFT}\Delta f$，去 CP 的一个 symbol 含 1024 个样点；一个 1 ms subframe 含 4 个 slot。若只用 $1/F_s$ 计算，样点网格约为 16.28 ns，但这不是由有效带宽决定的时延分辨率，也不能直接换算成已验证的定位精度。CP 样点应从设备或 <code>nrOFDMInfo</code> 的实际配置读取。

## 8. 频域位置

SCS 是相邻子载波间距，频域资源网格还需结合 PRB 数、BWP 起点、Point A、保护带和 DC 位置。`mu` 不等于带宽，也不等于 FFT 点数；这些量共同决定采集带宽和可见资源。

## 9. 数学原理

设 `N_FFT` 与 SCS 采用一致的基带约定：

$$
F_s=N_{FFT}\Delta f,
\qquad
\Delta\tau_{grid}=\frac{1}{N_{FFT}\Delta f}=\frac{1}{F_s}.
$$

FFT 网格可以细化时延采样，但实际时延分辨能力主要由有效占用带宽 `B_use` 决定：

$$
\Delta\tau_{resolution}\approx\frac{1}{B_{use}}.
$$

这一区分对 PRACH/定位测量尤其重要。

## 10. 3GPP 对应规范

- **TS 38.211 §4.2**：numerology、子载波间隔及相关波形参数入口；精确表格和适用范围按项目 Release 核对。
- **TS 38.211 §4.3**：frame、slot 和 OFDM symbol 的时间组织。
- **TS 38.213/38.331**：将 numerology 与 TDD、BWP、RRC 配置关联的过程/字段。
- 相关字段/参数：`mu`、`subcarrierSpacing`、CP、BWP、载波栅格、采样率。
- 状态：`STANDARD + partial`，具体 Release 与设备配置为 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- `nrCarrierConfig` 的 `SubcarrierSpacing` 属性：保存 SCS；`mu` 可由 SCS 映射，但应在配置中显式记录。
- `nrOFDMInfo(carrier)`：查询与 numerology 一致的 FFT、采样率、CP 和 symbol 信息。
- `nrOFDMModulate` / `nrOFDMDemodulate`：验证 numerology 改变后时域长度和资源网格映射。
- 具体 `mu` 支持范围、对象属性和 Release 行为尚未在本机核验，标为 `NEEDS_EXTERNAL_REFERENCE`。

## 12. 本项目中的用途

1. 从同步/配置快照锁定 `mu`，并生成 Frame/Slot 和 SCS 记录。
2. 用同一 numerology 构造 [[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]、occasion 和相关器参考。
3. 给 [[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]、DCI、PDSCH 资源解析提供符号与频率坐标。
4. 在 ToA/TDOA 中区分采样网格精度与有效带宽分辨能力，不把增大 FFT 当作真实定位精度提升。

## 12.1 多 numerology 共存与跨 BWP 边界

同一载波可能存在不同 BWP 或不同信号参数；即使它们共享 10 ms 的宏观帧参考，symbol 边界、CP 长度、FFT 配置和资源索引也可能不同。解析器应按下列顺序处理：

1. 先按载波/BWP 和配置版本分流，分别建立 $\mu$、SCS、CP、FFT、采样率和 Point A 映射。
2. 在各自的局部网格内解析 PRACH、PDCCH、PDSCH/PUSCH 或参考信号。
3. 只有在转换到同一个绝对时间基准后，才允许跨 BWP 比较事件时间；频域数组不能直接拼接。
4. 若一个捕获片段跨越配置切换，切换前后的样点区间必须分别引用不同 config_id，并在切换附近保留不确定窗口。

定位上，跨 numerology 的比较应使用秒或公共时钟计数作为中间表示。把不同 SCS 的子载波索引、symbol 索引或 FFT bin 当成同一坐标，会制造看似稳定但实际错误的 ToA 偏差。

## 13. 常见误区

- 把 SCS、numerology、带宽、采样率或 FFT 点数互相替代。
- 只改变 FFT 点数却声称改变了 NR numerology。
- 忽略 CP 和不同 symbol 的边界，把 `1/Delta_f` 当作完整 symbol 周期。
- 用“常见 SCS”填补缺失的网络配置。
- 在同一项目中让 PRACH 与 PDCCH 解析器使用不同 `mu` 快照。

## 14. 与相似概念的区别

| 概念 | 区别 |
|---|---|
| Numerology (`mu`) | 一组时频参数的配置索引 |
| SCS | numerology 导出的相邻子载波间隔 |
| Bandwidth | 占用频域范围，通常由 PRB 数和 SCS 共同决定 |
| Sampling rate | 设备/波形样点速率，可由 FFT 与 SCS 约定关联但不是同义词 |
| BWP | 载波内给 UE/解析器使用的频域资源范围 |

## 15. 代码实现注意事项

- 用不可变配置对象传递 `mu`、SCS、FFT、CP、采样率和 BWP；避免各模块自行推断。
- 配置哈希或 `config_id` 必须覆盖 numerology 相关字段，防止跨配置复用缓存。
- 计算样点偏移时保留有理数/浮点结果和取整策略，避免累计误差污染跨站 ToA。
- 对不支持的 `mu` 或不一致的 `F_s/N_FFT/Delta_f` 组合显式报错。

## 15.1 配置快照 schema

可用以下最小结构作为模块间接口（值为示意，占位字段不能直接用于现场解析）：

~~~json
config_id: nr-cellA-2026-09-04-v03
release_or_toolbox_version: null
carrier_id: cellA
mu: 2
scs_hz: 60000
cp: unknown
n_fft: 1024
sample_rate_hz: 61440000
point_a: null
bwp_start_crb: null
tdd_config_id: null
frame_start_sample: null
coordinate_convention: "sample interval is left-closed, right-open"
~~~

接受快照前至少检查：

- <code>scs_hz = 15000 × 2^mu</code> 是否成立，或是否明确记录了信号专用例外；
- <code>sample_rate_hz / (n_fft × scs_hz)</code> 是否等于 1，若不等于 1 则写明过采样/重采样约定；
- CP、Point A、BWP 和 TDD 配置是否有来源或显式 null；
- 快照是否覆盖捕获起止样点，且不会在跨配置时段继续复用。

## 16. 待实验验证的问题

- 设备 IQ 的采样率和中心频率能否唯一确定 `mu`/SCS，还是必须读取 RRC/元数据？
- 不同 `mu` 下 PRACH 检测峰的位置、窗口长度和门限如何变化？
- 采样率偏差、重采样和 CFO 是否会被错误吸收到 numerology 配置中？
- 现场是否存在同一载波多 BWP/多 numerology，需要按 BWP 分流？

## 17. Related Notes

- [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]
- [[5G-NR-Positioning/01-NR基础/SCS|SCS]]
- [[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]
- [[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]
- [[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]
- [[01-专题知识/信道估计与均衡/01 5G 物理层与信道模型|01 5G 物理层与信道模型]]
- [[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡|06 OFDM 接收与频域均衡]]
- [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|5G TDD 上下行监测与资源解析]]

## 证据与状态

- `STANDARD + partial`：TS 38.211 §4.2/§4.3 的 numerology 与时间尺度入口。
- `PERSONAL_NOTE`：沿用现有物理层笔记中的 `Delta_f`、`T_u`、`T_slot` 与时延分辨率区分。
- `NEEDS_VERIFICATION`：项目 Release、CP 类型、实际 `F_s/N_FFT` 组合和多 BWP 配置。
