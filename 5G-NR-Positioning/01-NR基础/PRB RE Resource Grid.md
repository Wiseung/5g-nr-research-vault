---
title: PRB RE Resource Grid
aliases:
  - NR PRB/RE 资源网格
  - PRB RE Resource Grid
  - NR 资源网格
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/resource-grid
  - topic/prb
  - topic/re
  - topic/bwp
  - stage/基础
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.214
  - 01-专题知识/信道估计与均衡/01 5G 物理层与信道模型
related:
  - "[[5G-NR-Positioning/01-NR基础/SCS|SCS]]"
  - "[[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]"
  - "[[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]"
  - "[[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]"
  - "[[5G-NR-Positioning/03-PDCCH/CORESET|CORESET]]"
  - "[[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]"
  - "[[01-专题知识/信道估计与均衡/DM-RS|DM-RS]]"
---

# PRB RE Resource Grid

## 1. 一句话定义

NR 资源网格用 `(subcarrier, OFDM symbol, port)` 等坐标描述资源元素 RE；PRB 是频域上连续 12 个子载波的资源块，多个 PRB、符号和端口共同组成可映射的网格。

## 2. 为什么项目需要它

PRACH、PDCCH、PDSCH、PUSCH 和 DM-RS 都必须先映射到正确 RE 才能检测、解调或提取单用户信号。项目中的“资源命中”本质上是 DCI/配置到 RE/样点掩码的闭环。

## 3. 它位于整个 5G 空口链路的什么位置

```text
Carrier/BWP/SCS → PRB/RE grid → channel/reference mapping
                 → PRACH/PDCCH/DCI/PDSCH resource extraction
                 → filtering/truncation → timing observation
```

资源网格是协议字段和时域 IQ 之间的接口，不是单独的信道估计器。

## 4. 输入

- 载波、BWP、Point A、SCS、PRB 数及局部/绝对频率偏移。
- Frame/slot/symbol 时间坐标和 TDD 方向。
- 物理信道、参考信号、层/端口及资源分配字段。
- FFT、CP、采样率和 OFDM 解调约定。

## 5. 输出

- RE 坐标、PRB 坐标、端口/层坐标和资源掩码。
- 局部网格索引到绝对载波频率/样点的映射。
- 数据、控制、DM-RS、保留和 guard RE 的互斥分类。
- 可供 PDCCH/PDSCH 盲搜和 UE 信号截取使用的 `resource_snapshot`。

## 6. 关键参数

| 参数 | 含义 | 项目注意 |
|---|---|---|
| `N_SC_RB` | 每 PRB 的连续子载波数，常用为 12 | 按规范版本核对 |
| `N_RB` | 活动载波/BWP 的 PRB 数 | 不等于物理天线数 |
| `k,l,p` | 子载波、symbol、端口坐标 | 记录坐标原点 |
| `N_layer` | 数据层数 | 不可与 port 混同 |
| `PointA/BWPStart` | 绝对频率参考和 BWP 起点 | 影响所有 RE 映射 |
| `mask` | 数据/参考/控制/保留资源掩码 | 要保存版本和生成规则 |

## 7. 时域位置

RE 的 `l` 轴位于某个 frame/slot 内的 OFDM symbol；符号边界和中心时刻由 [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]] 与 CP 配置给出。PRB 只描述频域连续资源，不意味着整个 slot 的每个 symbol 都被同一信道占用。

## 8. 频域位置

一个 RE 可表示为：

$$
\mathrm{RE}=(k,l,p),
$$

其中 `k` 是子载波，`l` 是 OFDM symbol，`p` 是逻辑端口/空间端口。若 `k_PRB` 是 PRB 索引，则其子载波集合可抽象为：

$$
\mathcal K_{PRB}=\{12k_{PRB},\ldots,12k_{PRB}+11\}
$$

实际绝对索引还要加 Point A、BWP 和载波偏移。

## 8.1 CRB、PRB、BWP 与 RE 的坐标层级

频域索引至少要保留以下层级，避免把不同原点的整数混用：

| 层级 | 原点/含义 | 典型使用者 |
| --- | --- | --- |
| Point A | 载波公共参考频点 | 跨 BWP、跨信号建立绝对频率关系 |
| CRB | 相对 Point A 的公共资源块 | RRC/BWP 配置和公共网格 |
| BWP | 载波内的一段连续工作带宽 | UE/接收机当前活动范围 |
| PRB | 相对 BWP 的物理资源块 | PDSCH/PUSCH/参考信号资源分配 |
| RE | PRB 内一个子载波、symbol、端口位置 | 调制、估计和掩码 |

在一个明确的 SCS 和坐标约定下，可用抽象关系检查局部到绝对索引：

$$
k_{abs}=12\left(n_{start}^{BWP}+n_{PRB}\right)+n_{sc},
\qquad 0\le n_{sc}<12.
$$

这里的 $n_{start}^{BWP}$ 必须注明是相对 Point A 的 CRB 起点还是工具箱的局部起点；若两者单位/原点不同，不能直接代入。PRACH 可能使用独立的 SCS 和频域坐标，其索引不应复用普通 UL BWP 的 PRB 编号。

## 9. 数学原理

对一个有效网格，资源可用性应拆成互斥集合：

$$
\mathcal R_{all}=\mathcal R_{data}\,\dot\cup\,
\mathcal R_{reference}\,\dot\cup\,
\mathcal R_{control}\,\dot\cup\,
\mathcal R_{reserved}.
$$

局部子载波到物理频率的映射可写为：

$$
f_{abs}[k]=f_c+f_{offset}+(k-k_0)\Delta f.
$$

时域 OFDM 解调后，`(k,l)` 还需通过 FFT 窗口和 CP 规则映射回样点区间。

## 9.1 resource_snapshot 与掩码闭包

建议把一次资源解析的结果固化为可回放的快照，而不是只输出一个二维矩阵：

~~~json
resource_snapshot_id: ueA-slot000123
config_id: nr-cellA-2026-09-04-v03
carrier_id: cellA
bwp:
  start_crb: null
  size_prb: null
  mu: 2
  scs_hz: 60000
time:
  frame: 12
  slot: 3
  symbols: [2, 3, 4, 5, 6, 7]
frequency:
  prb_indices: [10, 11, 12, 13]
  point_a: null
ports_layers:
  ports: [0]
  layers: [0]
masks:
  data: <generated>
  dmrs: <generated>
  ptrs: <generated-or-null>
  control: <generated-or-null>
  reserved: <generated-or-null>
direction: U
coordinate_convention: "k,l,p; local k is BWP-relative"
~~~

掩码闭包至少满足：

$$
\mathcal R_{usable}
=\mathcal R_{allocated}\cap\mathcal R_{direction}
\setminus\left(\mathcal R_{control}\cup\mathcal R_{reserved}\right).
$$

数据、DM-RS、PTRS 和控制集合若按实现被定义为互斥分类，应检查并集覆盖数等于预期 RE 数；若某些信号允许复用，则必须记录优先级和覆盖规则，不能用“非零”判断资源类型。快照还应保存生成规则的版本，确保同一 DCI 在不同软件版本下可以复现同一索引表。

## 10. 3GPP 对应规范

- **TS 38.211 §§4.4.1–4.4.4**：RE、资源块、资源栅格和公共资源块等物理资源接口；条款编号请按项目 Release 核对。
- **TS 38.211** 各物理信道/参考信号章节：具体 PDCCH、PDSCH、PUSCH、DM-RS、PRACH 的 RE 映射。
- **TS 38.214**：PDSCH/PUSCH 资源分配、层数和调度参数到可用 RE 的过程。
- **TS 38.331**：BWP、Point A 和 RRC 资源配置字段（当前字段映射待核对）。
- 状态：`STANDARD + partial`；具体信道映射表和 Release 为 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- `nrResourceGrid(carrier, nPorts)`：创建按 carrier 配置的资源网格。
- `nrPDSCHIndices` / `nrPDCCHIndices`：获得相应物理信道 RE 索引（输入对象/参数依 Release 核对）。
- `nrPDSCHDMRSIndices`：生成 PDSCH DM-RS 索引，便于估计和掩码排除。
- `nrPRACHIndices`、`nrCarrierConfig`、`nrOFDMInfo`：连接 PRACH/载波配置与网格/波形坐标。
- 本项目尚无已运行 MATLAB 脚本；上述 API 均标为 `NEEDS_EXTERNAL_REFERENCE`，需锁定工具箱版本后验证。

## 12. 本项目中的用途

1. 将 [[5G-NR-Positioning/03-PDCCH/DCI|DCI]] 字段转换成 PDSCH/PUSCH 的 PRB、symbol、层和端口资源快照。
2. 用资源掩码隔离目标 UE 的数据/DM-RS，避免把邻 UE、控制或 guard RE 混入。
3. 将网格资源反变换到时域 IQ，执行滤波/时频截断并生成 ToA 候选。
4. 将同一 `resource_snapshot` 跨站复用，保证 TDOA 比较的是同一用户事件和参考片段。

## 12.1 定位掩码与单用户截取

定位支路不应把“数据 RE”和“参考 RE”简单合并或全部删除，而应按观测目的分层：

1. **事件检测层**：用 PRACH、SRS 或已知 DM-RS 的序列/资源位置形成候选峰。
2. **用户隔离层**：用 C-RNTI、DCI、BWP、PRB、symbol 和端口/层掩码排除邻 UE 与控制资源。
3. **时间观测层**：保留未滤波参考支路和滤波/截断后的数据支路，分别记录群时延和窗口。
4. **跨站复用层**：各站对同一 <code>resource_snapshot_id</code> 使用相同的逻辑掩码，再把样点时间交给 [[5G-NR-Positioning/05-定位观测量/Timing Observation|Timing Observation]]。

可将最终定位候选写成：

$$
\mathcal R_{position}
=\mathcal R_{target}
\cap\mathcal R_{UL}
\cap\mathcal R_{capture\_valid}.
$$

这个集合只定义“可以测量”的资源，不保证存在首径或足够 SNR。没有目标用户关联证据时，输出应降级为 <code>candidate_observation</code>，而不是标成已确认 UE。

## 12.2 端口、层与接收通道

<code>port</code>、<code>layer</code>、物理天线和采集接收通道是不同维度。建议在快照中分别记录：

- 参考信号端口及其序列/映射；
- 数据层数和层到端口的映射；
- 预编码矩阵（若可见）或“未知”；
- 采集通道编号、天线校准状态和极化；
- 均衡器实际使用的等效信道域。

对定位而言，跨站比较的是同一物理事件的时间，不是未经校准的端口索引；端口顺序错误仍可能造成峰值相位或幅度变化，因此应保留端口域中间结果。

## 13. 常见误区

- 把 PRB、RE、RB group、BWP 和载波带宽混为一谈。
- 忽略局部 BWP 索引与绝对载波索引的偏移。
- 把 port、layer、物理天线和接收通道当成同一维度。
- 重复扣除 DM-RS/PTRS/控制 RE，或把参考信号当数据解码。
- 只保存网格数组，不保存生成该数组的配置和坐标原点。

## 14. 与相似概念的区别

| 概念 | 区别 |
|---|---|
| RE | 一个子载波、symbol、端口位置的最小资源单元 |
| PRB | 频域连续 12 子载波的资源块 |
| BWP | 载波内一段连续、可配置的频域工作范围 |
| Resource grid | 按载波/BWP、symbol、端口组织的完整索引容器 |
| Resource allocation | DCI/RRC 对哪些 PRB/symbol 可用的规则 |

## 15. 代码实现注意事项

- 用结构体保存 `local_k`、`absolute_k`、`frequency_hz`、`symbol_l`、`port_p`，不要只传裸矩阵。
- 生成掩码时先确定配置和方向，再叠加控制、参考、数据和保留集合；对重叠资源报错。
- 明确数组维度顺序（`k,l,p` 或工具箱约定），在函数入口做维度断言。
- 逆 OFDM 变换用于时频截断时，记录 FFT 归一化、窗函数、CP 和边界零填充。

## 15.1 资源映射的最小单元测试

在接入完整 PDCCH/PDSCH 译码前，先对一个小网格做以下结构测试：

- PRB 到 12 个 RE 子载波的映射无越界、无重复；
- <code>k,l,p</code> 与工具/数组维度约定互相可逆；
- BWP 起点改变只平移绝对频率，不改变局部资源顺序；
- 数据与参考/保留掩码的重叠被显式报告；
- 方向为 D 时，UL 定位掩码为空；方向为 U 时，合法 UL 资源可被枚举；
- 由快照重建的频率轴相邻间隔等于当前 SCS。

这些测试只验证索引和掩码闭包，不能代替序列正确性、信道估计、同步或实测定位精度。

## 16. 待实验验证的问题

- 现场设备能否提供 Point A、BWP 起点、PRB 数和端口/层配置？
- DCI 驱动的资源快照与工具箱 `nrPDSCHIndices`/`nrPDCCHIndices` 是否逐 RE 一致？
- 资源命中后，保留 RE、DM-RS 和邻 UE 干扰的残余功率如何量化？
- 由网格反变换到 IQ 时，滤波器和截断窗口引入的群时延如何写入 ToA 账本？

## 17. Related Notes

- [[5G-NR-Positioning/01-NR基础/SCS|SCS]]
- [[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]
- [[5G-NR-Positioning/01-NR基础/NR Frame Slot|NR Frame Slot]]
- [[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]
- [[5G-NR-Positioning/03-PDCCH/CORESET|CORESET]]
- [[5G-NR-Positioning/03-PDCCH/Search Space|Search Space]]
- [[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]
- [[01-专题知识/信道估计与均衡/01 5G 物理层与信道模型|01 5G 物理层与信道模型]]
- [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]]
- [[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡|06 OFDM 接收与频域均衡]]
- [[01-专题知识/5G定位/单用户时频截取与定位观测量|单用户时频截取与定位观测量]]

## 证据与状态

- `STANDARD + partial`：TS 38.211 资源坐标与 TS 38.214 数据资源接口。
- `PERSONAL_NOTE`：继承现有物理层笔记的 `(k,l,p)`、BWP/绝对索引和互斥掩码约定。
- `NEEDS_VERIFICATION`：项目实际 BWP/Point A、端口/层维度、工具箱索引顺序和所有信道的 Release 映射。
