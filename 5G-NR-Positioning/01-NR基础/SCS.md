---
title: SCS
aliases:
  - Subcarrier Spacing
  - 子载波间隔
  - NR SCS
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/scs
  - topic/frequency-grid
  - topic/timing
  - stage/基础
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 01-专题知识/信道估计与均衡/01 5G 物理层与信道模型
related:
  - "[[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]"
  - "[[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]"
  - "[[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]"
  - "[[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]"
---

# SCS

## 1. 一句话定义

SCS（Subcarrier Spacing）是 NR 频域相邻子载波之间的间隔；它与 numerology `mu` 共同规定 OFDM 的频率和时间尺度。

## 2. 为什么项目需要它

SCS 决定 FFT 频率轴、OFDM 有效符号时长、PRB 的实际带宽和采样到资源的映射。SCS 配错会让 PRACH 相关器、PDCCH 候选和 PDSCH 资源整体落在错误位置。

## 3. 它位于整个 5G 空口链路的什么位置

SCS 位于 numerology 与资源网格之间，并贯穿整个被动解析链：

```text
SCS/μ → Frame/Slot timing + PRB frequency axis
      → PRACH/PDCCH/PDSCH resource mapping
      → UE signal extraction → ToA/TDOA
```

## 4. 输入

- `subcarrierSpacing` 或 `mu` 配置。
- 载波/BWP 的 PRB 数、Point A、保护带和 DC 约定。
- FFT 点数、采样率、CP 和捕获同步结果。

## 5. 输出

- 子载波中心频率序列与相邻间隔。
- 有效 OFDM symbol 时长、slot 周期和采样坐标关系。
- 每个 PRB 的带宽及资源网格频域索引。
- 提供给 PRACH 检测和 PDCCH/PDSCH 解析的频域配置。

## 6. 关键参数

| 参数 | 含义 | 风险 |
|---|---|---|
| `Delta_f` | SCS，Hz 或 kHz | 单位混用会造成数量级错误 |
| `mu` | 与 SCS 的离散映射 | 不要从经验值覆盖配置 |
| `N_FFT` | FFT 长度 | 不等于占用子载波数 |
| `F_s` | 采样率 | 需与 FFT/SCS 约定一致 |
| `N_RB` | 频域 PRB 数 | 决定有效带宽而非仅由 SCS 决定 |
| `B_use` | 有效占用带宽 | 与时延分辨率直接相关 |

## 7. 时域位置

在不含 CP 的近似下：

$$
T_u=\frac{1}{\Delta f},\qquad
T_{slot}\approx\frac{1\ \mathrm{ms}}{2^\mu}.
$$

较大的 SCS 缩短 symbol/slot 时间，但完整 symbol 仍需加 CP；采样边界由 [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]] 管理。

## 7.1 PRB 带宽与资源预算

一个 PRB 在频域通常包含 12 个连续子载波，因此在同一 numerology 下，其名义频域宽度为：

$$
B_{PRB}=12\Delta f.
$$

这只是网格宽度，不等于有效发射带宽；保护带、未占用 PRB、BWP 边界和滤波滚降都可能使实际可用带宽更小。

| SCS | 单个 PRB 名义宽度 | 说明性用途 |
| ---: | ---: | --- |
| 15 kHz | 180 kHz | 窄 SCS、较长 symbol |
| 30 kHz | 360 kHz | 常见 FR1 配置之一 |
| 60 kHz | 720 kHz | 更短 symbol，需核对 CP/频段 |
| 120 kHz | 1.44 MHz | 高频段/高 SCS 场景 |
| 240 kHz | 2.88 MHz | 只在适用信号和频段下使用 |

若活动网格有 $N_{RB}$ 个连续 PRB，可用 $12N_{RB}\Delta f$ 做频宽数量级检查；不要据此反推出网络的 channel bandwidth 或把保护带算进定位有效带宽。

## 8. 频域位置

第 `k` 个子载波的基带频率可写成：

$$
f_k=(k-k_c)\Delta f,
$$

若计入载波和 BWP 偏移，则：

$$
f_{abs}[k]=f_c+f_{offset}+(k-k_0)\Delta f.
$$

`k_c/k_0` 的定义必须写入配置快照，不能把数组列号默认当作绝对频率。

## 9. 数学原理

常用 numerology 关系为：

$$
\Delta f=15\times2^\mu\ \mathrm{kHz}.
$$

若 `F_s=N_FFT Delta_f`，则频率 bin 与时延网格满足：

$$
\Delta f_{bin}=\Delta f,
\qquad
\Delta\tau_{grid}=\frac{1}{F_s}.
$$

但利用有限有效子载波估计到达时间时，物理分辨率数量级更接近 `1/B_use`；增大 FFT 点数不等于增加有效带宽。

## 9.1 时延分辨率、网格间隔与无歧义范围

频域采样到时延的三个量必须分开记录：

$$
\Delta\tau_{grid}=\frac{1}{F_s},\qquad
\Delta\tau_{resolution}\approx\frac{1}{B_{use}},\qquad
T_{\tau,amb}\sim\frac{1}{\Delta f}.
$$

- $\Delta\tau_{grid}$ 是设备/FFT 产生的离散网格间隔，受采样率和插值影响。
- $\Delta\tau_{resolution}$ 是由有效频率跨度 $B_{use}$ 决定的可分辨时延数量级，受窗函数、SNR、多径和估计器影响。
- $T_{\tau,amb}$ 是均匀子载波采样导致的周期性无歧义范围数量级；非连续频点、同步误差和实际波形会改变可用范围。

若把传播时延换算为距离，单向距离数量级为 $c\Delta\tau$；这不是误差上界，也不代表已经完成硬件、时钟和多径校准。定位报告应同时给出频率覆盖、采样率和估计不确定度。

## 9.2 频域相位斜率与时延拟合

当多个有效子载波上的参考信号能够保持相干时，单径近似下的信道相位可写为：

$$
H(f_k)\approx A_k\,e^{-j2\pi f_k\tau}.
$$

对相位展开后的线性部分拟合，可得到时延候选：

$$
\widehat{\tau}_{phase}
\approx-\frac{1}{2\pi}
\frac{\partial\,\mathrm{unwrap}(\angle H(f))}{\partial f}.
$$

这是一种工程估计关系，不是把 SCS 直接变成定位距离的规范公式。拟合前必须处理公共相位、残余 CFO/采样频偏、频率参考误差和多径；子载波不连续、相位跳变或低 SNR 时，线性斜率可能只反映某个路径簇。建议同时保留相关峰、相位拟合残差和有效子载波集合，只有多个估计器一致时才把结果送入 [[5G-NR-Positioning/05-定位观测量/Timing Observation|Timing Observation]]。

## 10. 3GPP 对应规范

- **TS 38.211 §4.2**：numerology 和 SCS 定义入口；具体支持值/表格按 Release 核对。
- **TS 38.211 §4.4**：资源网格、资源块和子载波索引的接口。
- **TS 38.331**：RRC 中 `subcarrierSpacing`、BWP 和载波配置字段；当前项目字段尚未核验。
- 相关字段/参数：`subcarrierSpacing`、`mu`、BWP、载波栅格、FFT/采样率。
- 状态：`STANDARD + partial`；网络 Release 与设备配置为 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- `nrCarrierConfig.SubcarrierSpacing`：设置或读取载波 SCS。
- `nrOFDMInfo(carrier)`：查询与 SCS 配套的 FFT、采样率、CP 和 symbol 长度。
- `nrResourceGrid(carrier)`：生成按 SCS/载波配置的资源网格容器。
- API 属性和支持的 SCS 范围需在本机工具箱 Release 中核对，当前仅作接口线索。

## 12. 本项目中的用途

1. 用 SCS 校验 IQ 的频率轴和 `mu`，再生成 [[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]。
2. 确定 PRACH 参考序列采样率、检测窗口和 occasion 的频域位置。
3. 为 PDCCH/PDSCH 的 CORESET、PRB、DM-RS 和调制符号提供绝对/局部频率映射。
4. 在定位支路中报告有效带宽和时延分辨率，避免把 SCS 本身当作 ToA 精度。

## 12.1 定位视角：SCS 不等于定位精度

SCS 改变子载波间隔和 symbol 时间尺度，而定位时延信息主要来自**有效频率跨度、相位一致性和观测 SNR**。因此：

1. 在固定 PRB 数下增大 SCS 会扩大名义占用带宽，但也会改变 symbol/CP 和采样配置，不能只比较 SCS。
2. 在固定 channel bandwidth 下改变 SCS 往往会改变可容纳的 PRB 数；应明确固定的是 PRB、$B_{use}$ 还是总带宽。
3. 增大 FFT 或零填充只会细化 $\Delta\tau_{grid}$，不会自动增加 $B_{use}$。
4. 多站比较时，各站必须使用相同的频率参考、采样率标定和频域掩码；不同 BWP 的局部 bin 不能直接做相位/时延差。

说明性例子：106 PRB、30 kHz SCS 的名义网格宽度是 $106\times12\times30$ kHz $=38.16$ MHz。若再选择 $N_{FFT}=2048$、$F_s=61.44$ MHz，样点网格约 16.28 ns；但有效带宽、滤波器和未占用边缘决定的时延分辨率仍需单独估计和实测。

## 13. 常见误区

- 把 SCS 当作采样率、信号带宽或 PRB 数。
- 只在频域改 SCS，未同步更新 OFDM symbol、CP、采样率和时隙边界。
- 忽略 BWP/Point A 偏移，造成资源与实际载频错位。
- 用 `1/F_s` 直接宣称 ToA 的物理分辨率。
- 将不同 numerology 的资源放入同一网格而未记录 numerology 边界。

## 14. 与相似概念的区别

| 概念 | 主要区别 |
|---|---|
| SCS | 相邻子载波间的频率间隔 |
| Numerology | 由 `mu` 表示的一组时频参数 |
| Channel bandwidth | 整个载波频域范围 |
| PRB | 12 个连续子载波组成的资源块 |
| Sampling rate | 设备/波形时间采样速率 |

## 15. 代码实现注意事项

- 统一内部单位（建议 Hz、seconds、samples），在展示层再转换为 kHz/ms。
- 以 `config_id` 绑定 SCS、`mu`、FFT、采样率、BWP 和 CP；任何一个变化都使旧网格缓存失效。
- 生成频率轴时同时保存 local bin、BWP-relative bin、absolute bin 和物理频率。
- 对 `F_s/(N_FFT Delta_f)` 偏离 1 的情况显式记录重采样或过采样约定。

## 15.1 频率轴与采样一致性检查

生成频率轴时建议同时保存四个坐标：BWP-relative bin、Point-A-relative CRB/PRB、设备 FFT bin 和物理频率（Hz）。对任一相邻有效子载波，检查：

$$
f[k+1]-f[k]=\Delta f,
\qquad
F_s=N_{FFT}\Delta f
$$

或明确记录过采样/重采样因子。频率轴的起点、FFT <code>fftshift</code> 约定、DC 位置和负频率排序都应进入 <code>config_id</code>。若只保存一个数组列号，后续无法判断资源错位来自 BWP 偏移还是 FFT 排序。

## 16. 待实验验证的问题

- 当前设备报告的“120.88 兆”究竟是中心频率、带宽还是采样率？
- SCS 是否能从同步/广播信息恢复，还是必须由设备配置提供？
- 不同 SCS 下 PRACH 相关峰宽、检测门限和 ToA 误差的实测变化是什么？
- 采样率偏差和重采样会如何影响跨站频率/时间坐标一致性？

## 17. Related Notes

- [[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]
- [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]
- [[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]
- [[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]
- [[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]
- [[01-专题知识/信道估计与均衡/01 5G 物理层与信道模型|01 5G 物理层与信道模型]]
- [[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡|06 OFDM 接收与频域均衡]]
- [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|5G TDD 上下行监测与资源解析]]

## 证据与状态

- `STANDARD + partial`：TS 38.211 §4.2/§4.4 的 SCS、频率轴和资源网格接口。
- `PERSONAL_NOTE`：沿用现有物理层笔记对 `B_use`、FFT 网格和时延分辨率的区分。
- `NEEDS_VERIFICATION`：项目实际 SCS、采样率、BWP 偏移和多 numerology 情况。
