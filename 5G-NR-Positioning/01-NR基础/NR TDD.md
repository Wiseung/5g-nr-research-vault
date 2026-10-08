---
title: NR TDD
aliases:
  - NR TDD 上下行
  - NR TDD UL DL
  - TDD Slot Format
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - domain/tdd
  - topic/uplink-downlink
  - topic/slot-format
  - stage/基础
  - evidence/3gpp
source:
  - 3GPP TS 38.213
  - 3GPP TS 38.331
  - 01-专题知识/5G定位/5G TDD 上下行监测与资源解析
related:
  - "[[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]"
  - "[[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]"
  - "[[5G-NR-Positioning/01-NR基础/SCS|SCS]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]"
  - "[[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]"
---

# NR TDD

## 1. 一句话定义

NR TDD 在同一载波的连续时间轴上按 slot/symbol 将资源标为下行 `D`、上行 `U` 或灵活 `F`；具体方向由网络配置和当前协议状态决定。

## 2. 为什么项目需要它

被动设备要在同频连续 IQ 中区分 PRACH/PUSCH 等上行与 SSB/PDCCH/PDSCH 等下行，避免在错误方向或切换保护区做检测。TDD 标注也是把 UE 上行观测送入 ToA/TDOA 的前置条件。

## 3. 它位于整个 5G 空口链路的什么位置

```text
Frame/Slot + SCS → TDD slot/symbol direction
                 ├─ D: SSB/PDCCH/PDSCH
                 ├─ U: PRACH/PUSCH/SRS
                 └─ F/unknown: wait or classify
                 → C-RNTI/PDSCH → UE signal → TDOA
```

本项目“上下行同时监测”指连续采集后并行解析 D/U 分支，不表示同一 RE 同时属于上下行。

## 4. 输入

- `mu`/SCS、frame/slot/symbol 坐标。
- SIB1/RRC 或设备元数据中的 TDD UL-DL 配置。
- slot format 周期、下行/上行 slot 数及特殊 symbol 数。
- 同步状态、采样时间轴和必要的 guard/不确定区定义。

## 5. 输出

- 每个 slot/symbol 的 `DL|UL|F|unknown` 标签。
- 可供 PRACH、PDCCH、PDSCH、PUSCH 解析器使用的合法时隙集合。
- TDD 配置快照、版本和变化时间。
- 方向判定置信度及 flexible/guard 的排除窗口。

## 6. 关键参数

| 参数 | 含义 | 项目注意 |
|---|---|---|
| `pattern1/2` | TDD UL-DL pattern 配置 | 可能存在双 pattern |
| `nrofDownlinkSlots` | 完整下行 slot 数 | 与 symbol 数同时解释 |
| `nrofDownlinkSymbols` | 特殊 slot 的下行 symbol 数 | 不等于整 slot |
| `nrofUplinkSlots` | 完整上行 slot 数 | 影响 PRACH/PUSCH 窗口 |
| `nrofUplinkSymbols` | 特殊 slot 的上行 symbol 数 | 需留出切换保护 |
| `F`/guard | 灵活或工程保护标记 | 不能默认当 UL 或 DL |
| `periodicity` | pattern 重复周期 | 以 RRC/规范字段为准 |

## 7. 时域位置

TDD 标签附着在 frame/slot/symbol 时间坐标上。一个特殊 slot 可能包含连续的 D、F、U symbol；切换附近的 guard 是工程接收标记，不应悄悄改写为规范方向。方向周期需与 [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]] 的 `mu` 和实际 CP 边界一致。

## 7.1 pattern 展开与周期索引

TDD 配置不是一个“整 slot 标签”，而是一个可展开到 symbol 的周期序列。设 pattern 周期覆盖 $N_{slot}^{period}$ 个 slot、每 slot 有 $N_{sym}$ 个 symbol，可定义：

$$
r=(n_{slot}^{abs}N_{sym}+l)\bmod
\left(N_{slot}^{period}N_{sym}\right),
\qquad d(r)\in\{D,U,F\}.
$$

工程实现应保留：

- pattern 的原始配置字段和版本；
- 周期起点相对于 frame/slot 的定义；
- 完整 DL/UL slot 数、特殊 slot 的 DL/UL symbol 数；
- 两个 pattern（若存在）之间的选择条件；
- 配置生效和失效的捕获样点。

不能用固定的“前几 slot 下行、后几 slot 上行”模板替代展开结果。配置缺失时可以用能量或已知序列做观测校验，但观测校验不能反向把未经核验的启发式结果写成规范 TDD 配置。

## 8. 频域位置

TDD 主要是时域方向属性，但同一 slot 内不同 BWP/载波和资源仍可能有不同占用。方向标签应附着到 `(carrier/BWP, slot, symbol)`，再与 [[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]] 的 PRB/RE 掩码求交，而不是给整段 IQ 一个单一方向。

## 9. 数学原理

设一个 pattern 周期含 `N_slot^period` 个 slot，每个 slot 有 `N_sym` 个 symbol，定义方向函数：

$$
d(s,l)=\begin{cases}
DL,&(s,l)\in\mathcal D\\
UL,&(s,l)\in\mathcal U\\
F,&(s,l)\in\mathcal F\\
unknown,&\text{配置或同步缺失}.
\end{cases}
$$

工程上的有效检测集合可写为 `R_signal ∩ R_direction`。对 flexible/guard，保守做法是先排除并保留原始能量，再通过实验决定是否细分。

## 9.1 方向状态机

把“配置方向”“观测方向”和“可用于某个检测器”分开记录，可减少 flexible/guard 误判：

| 状态 | 含义 | 可否进入定位支路 |
| --- | --- | --- |
| <code>unknown</code> | 没有可信配置或同步丢失 | 否，保留原始 IQ |
| <code>configured</code> | RRC/外部快照给出 D/U/F | 仅在资源和质量条件满足时 |
| <code>observed</code> | 能量/序列观测与配置一致或存在冲突 | 冲突需标记，不自动覆盖配置 |
| <code>usable</code> | 方向、资源、捕获质量和时间基准均通过 | 是 |

一个保守的判定函数可以写成：

$$
\mathrm{usable}(s,l)=
\mathbf 1\{d_{\mathrm{cfg}}(s,l)\in\{D,U\}\}
\mathbf 1\{q_{\mathrm{sync}}\ge q_{\min}\}
\mathbf 1\{(s,l)\notin\mathcal G_{\mathrm{guard}}\}.
$$

<code>F</code> 不是“默认 U”，也不是“默认 D”；只有在动态状态或外部规则明确后，才可细分为可用方向。切换附近的 guard/泄漏窗口属于工程质量掩码，应与规范 D/U/F 字段分别保存。

## 10. 3GPP 对应规范

- **TS 38.213 §11.1**：slot format、D/U/F 符号方向和 TDD 相关过程入口；精确字段/表格按 Release 核对。
- **TS 38.331**：`TDD-UL-DL-ConfigCommon`、`TDD-UL-DL-ConfigDedicated` 及 `subcarrierSpacing`/pattern 配置字段。
- **TS 38.211 §4.3**：frame、slot、symbol 的物理时间组织。
- 相关字段/参数：`dl-UL-TransmissionPeriodicity`、`nrofDownlinkSlots`、`nrofDownlinkSymbols`、`nrofUplinkSlots`、`nrofUplinkSymbols`（字段命名需按 ASN.1/Release 核对）。
- 状态：`STANDARD + partial`；当前网络 RRC 配置和设备 guard 定义为 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- `nrCarrierConfig`：提供 SCS、载波网格和时间基准；本身不代表完整现场 TDD 配置。
- NR waveform generator 相关的 `nrDLCarrierConfig` / `nrULCarrierConfig`（若当前 Release 提供）：可用于构造仿真 D/U 波形，但对象属性和组合方式需本机核对。
- `nrOFDMInfo`、`nrOFDMDemodulate`：按 carrier 时间轴切分 symbol，供方向标签测试。
- 当前未发现一个已验证的通用 `nrTDDDetect` API；实际 TDD 标签通常来自 MIB/SIB1/RRC 或外部配置，状态为 `NEEDS_EXTERNAL_REFERENCE`。

## 12. 本项目中的用途

1. 从 SIB1/RRC/设备元数据建立 `config_snapshot`，映射每个 symbol 的 D/U/F。
2. 只在合法 UL occasion 运行 [[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]、PUSCH/DM-RS 相关器。
3. 只在合法 DL 控制资源运行 [[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]、DCI 和 PDSCH 解析。
4. 将方向、时间和资源坐标写入 event 记录，避免把下行发射源 ToA 当成 UE 上行 ToA。

## 12.1 定位观测筛选

对项目的 UE 上行定位支路，可把方向筛选写成：

$$
\mathcal R_{position}
=\mathcal R_{signal}
\cap\mathcal R_{U}
\cap\mathcal R_{capture\_valid}
\cap\mathcal R_{sync\_quality}.
$$

其中 $\mathcal R_{signal}$ 可以来自 PRACH、PUSCH DM-RS、SRS 或已确认的单用户片段。下行 SSB/PDCCH/PDSCH/PRS 的观测可以用于小区、帧或下行发射源分析，但不能仅凭固定站下行到达差直接命名为 UE 的 UL-TDOA。

每个候选至少记录 <code>direction_source</code>（RRC、动态指示、能量校验或人工配置）、<code>direction_conflict</code>、排除的 symbol 数和原始 IQ 位置。若方向为 F/unknown、跨 guard 或时钟未锁定，输出应为 <code>partial_observation</code> 或 <code>toa_unreliable</code>，而不是生成一个看似完整的坐标。

## 12.2 切换边界的质量窗口

D/U 切换附近常见的问题包括发射泄漏、接收机恢复时间、滤波器群时延和采样时钟相位跳变。建议为每次切换保存：

- 规范 symbol 边界；
- 工程排除窗口的起止样点；
- 排除原因和校准版本；
- 排除前后的能量、相关峰和噪声估计。

排除窗口的宽度不能在没有设备测量的情况下写成固定常数。应先保守排除，再通过已知 UL 参考和回放实验收窄，并把结果标为 <code>NEEDS_VERIFICATION</code>。

## 13. 常见误区

- 将“同频上下行同时监测”理解为同一 symbol 同时有 UL 和 DL。
- 把 flexible symbol 自动归为 UL 或 DL，忽略调度和配置状态。
- 把 guard 当作规范 D/U 类别，或用固定模板替代当前 RRC 配置。
- 只按 slot 标方向，忽略特殊 slot 内的 symbol 级切换。
- 用下行同步峰代替 UE 上行定位观测。

## 14. 与相似概念的区别

| 概念 | 区别 |
|---|---|
| TDD slot format | 规范定义的 D/U/F 方向组合 |
| Flexible symbol | 可由配置/调度决定方向的 symbol，不是自动的 UL |
| Guard interval | 工程或物理切换保护区标记，需与规范方向分开 |
| FDD | UL/DL 可在不同频段并行，不使用同一载波的 TDD 方向切换 |
| DL/UL energy detector | 观测启发式，不等价于规范 TDD 配置 |

## 15. 代码实现注意事项

- 方向函数输入必须包含 carrier/BWP、frame、slot、symbol 和配置版本；不要使用全局固定 pattern。
- 设立 `unknown`/`ambiguous` 状态，保留 flexible/guard 原始 IQ，不静默丢弃。
- 在方向判定后再调用 PRACH/PDCCH/PDSCH 检测器，并在日志中记录被排除的资源。
- 配置切换时使旧方向掩码失效；跨站处理使用同一 config_id 和时间版本。

## 15.1 TDD 配置快照 schema

方向标签应与 numerology、资源和捕获范围绑定：

~~~json
tdd_config_id: cellA-tdd-v02
config_id: nr-cellA-2026-09-04-v03
source: sib1_rrc_or_external
periodicity: null
pattern1:
  nrofDownlinkSlots: null
  nrofDownlinkSymbols: null
  nrofUplinkSlots: null
  nrofUplinkSymbols: null
pattern2: null
dynamic_indicator: unknown
guard_mask:
  start_sample: null
  end_sample: null
symbol_labels: <expanded-per-config>
valid_from_capture_sample: null
valid_to_capture_sample: null
~~~

接受快照前检查：pattern 周期能否整除展开区间、symbol 标签是否覆盖每个 slot、配置切换处是否切断旧版本，以及 <code>direction_mask</code> 是否引用同一 <code>config_id</code>。字段缺失时保留 null 和来源，不要由能量峰猜出完整 pattern。

## 16. 待实验验证的问题

- 当前网络的 pattern 周期、特殊 slot 和 flexible symbol 能否从 SIB1/RRC 可靠恢复？
- 设备在 D/U 切换附近是否有固定空窗、泄漏或额外群时延？
- 仅依靠能量/同步能否校验方向标签，还是必须保存规范配置？
- 多站在同一 UL event 上的方向和 symbol 标签是否一致？

## 17. Related Notes

- [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]
- [[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]
- [[5G-NR-Positioning/01-NR基础/SCS|SCS]]
- [[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]
- [[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]
- [[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]
- [[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]
- [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|5G TDD 上下行监测与资源解析]]
- [[01-专题知识/信道估计与均衡/01 5G 物理层与信道模型|01 5G 物理层与信道模型]]
- [[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡|06 OFDM 接收与频域均衡]]
- [[00-导航与入口/5G 定位与 TDOA｜MOC|5G 定位与 TDOA｜MOC]]

## 证据与状态

- `STANDARD + partial`：TS 38.213 §11.1、TS 38.331 TDD UL-DL 配置字段和 TS 38.211 时间组织。
- `PERSONAL_NOTE`：继承现有 [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|5G TDD 上下行监测与资源解析]] 对连续采集、D/U/F 和 guard 分层的约定。
- `NEEDS_VERIFICATION`：项目实际 RRC pattern、设备切换空窗、flexible/guard 解释和多站方向一致性。
