---
title: PRACH Occasion
aliases:
  - NR PRACH Occasion
  - 随机接入时机
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - topic/resource
  - topic/timing
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.331
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]"
  - "[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]"
  - "[[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|现有 TDD 监测主线]]"
---
# PRACH Occasion

## 1. 一句话定义

PRACH Occasion（RO）是配置定义的一个可发送随机接入前导的时频资源实例，通常由帧/时隙/符号和频域位置共同描述。

## 2. 为什么项目需要它

RO 把相关峰限制到合法资源，并提供生成 RA-RNTI 所需的时域、频域和载波索引。没有 RO，前导索引无法可靠关联到响应窗口或用户事件。

## 3. 它位于整个 5G 空口链路的什么位置

RO 是配置解析到 PRACH 检测之间的资源坐标层；其输出进入 RA-RNTI 计算和 RAR PDCCH 监测，随后才可能关联临时 C-RNTI。

## 4. 输入

- PRACH Configuration、载波/BWP、SCS 和帧号。
- TDD D/U/F pattern、SSB/beam 到 RO 映射。
- msg1-FDM、频域起点和 PRACH format。

## 5. 输出

每个 RO 的 frame、slot、起始符号、持续长度、频域 Occasion、PRACH SCS、载波 ID、SSB/beam 关联和检测窗口；同时输出供 RA-RNTI 使用的 $s_{id}$/$t_{id}$/$f_{id}$/$ul^{carrier}_{id}$ 候选。

## 6. 关键参数

prach-ConfigurationIndex、msg1-FDM、msg1-FrequencyStart、msg1-SubcarrierSpacing、zeroCorrelationZoneConfig、restrictedSetConfig、SSB-per-RO 和 TDD slot format。具体索引映射属于标准表格，未核对 Release 时标记 NEEDS_EXTERNAL_REFERENCE。

## 7. 时域位置

RO 的时间位置由配置索引映射到帧、时隙和 OFDM 符号；长前导和短前导的符号长度、CP 和保护时间不同。检测器必须用实际采样率生成窗口，不可按固定 14 符号模板硬切。

## 8. 频域位置

RO 的频域位置可用 PRACH 资源块/子载波索引和绝对频率表示，可能与普通 UL BWP 的 PRB 编号不同。保存局部 PRACH bin、Point A 偏移和载波 ID，避免将同一 $f_{id}$ 误当绝对频点。

## 9. 数学原理

把合法 Occasion 集合记为

$$
\mathcal{O}=\{(s,t,f,c):\text{满足配置和 TDD 约束}\}.
$$

检测器只在 $(s,t,f,c)\in\mathcal{O}$ 上计算序列相关；RO 坐标还映射到 RA-RNTI 的索引项。一个 RO 可包含多个前导，不能假设一 RO 对应一个 UE。

## 10. 3GPP 对应规范

- TS 38.211 §5.3.2、§6.3.3.2：PRACH 波形与时频资源映射，具体长/短前导子条款需按版本复核。
- TS 38.213 §8.1：PRACH Occasion 和资源关系，表格/Release 待核。
- TS 38.331：RACH-ConfigCommon 及 SSB-to-RO 配置字段，clause/ASN.1 版本待核。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHConfig：配置 RO 相关属性。
- nrPRACHIndices：返回 PRACH 资源网格索引，可用于检查时频坐标。
- nrPRACHDetect：输入时域波形和配置后做候选检测，但 RO 枚举/多峰保留仍需外围代码。
- nrOFDMInfo：查询采样率、FFT 和符号长度；字段签名需本机核验。

上述 API 的对象属性、索引基准和 Release 行为均为 `NEEDS_EXTERNAL_REFERENCE`，不代表已在项目代码中运行。

## 12. 本项目中的用途

将每个 RO 建成可查询索引，检测到峰后生成 event_id 和 RA-RNTI 候选；只有在相同 RO 的 RAPID 匹配成功时，才把 RAR 与前导事件绑定，降低跨窗误关联。

## 13. 常见误区

- 把 Occasion 当成前导序列本身。
- 忽略频域 Occasion，导致同一时刻的多个 RO 混在一起。
- 忽略 SSB/beam 关联或把所有前导都绑定到一个 beam。
- 在 flexible/guard 符号上强行标记 UL PRACH。

## 14. 与相似概念的区别

RO 是资源实例；preamble index 是 RO 内的序列编号；RA-RNTI 是由 RO 上下文推导的响应寻址标识；RAR window 是 RO 后监测响应的时间区间。它们都不是最终 C-RNTI。

## 15. 代码实现注意事项

- 生成 RO 时保留标准表查找输入和输出，便于版本审计。
- 将时间坐标同时保存为帧/时隙/符号和绝对样点。
- 多载波/UL carrier 场景显式保留 ul_carrier_id。
- 做边界测试：周期起点、跨帧 RO、频域起点和不同 SCS。

## 16. 待实验验证的问题

- 当前网络的 RO 周期、频域数量和 SSB 映射是否能从采集数据确认。
- 长/短前导在设备采样率下的窗口长度与 CP 是否正确。
- 同一 RO 多前导碰撞时，如何定义 event_id 和峰簇。
- RA-RNTI 计算所需的各索引是否全部可由设备元数据恢复。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]、[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]、[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]、[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]。
- 旧笔记：[[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|现有 TDD 监测主线]]、[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]。

## 18. RO 的坐标模型

项目中把一个 RO 表示为六元组：

$$
\mathrm{RO}=(n_f,n_{slot},l_{start},n_{RA},\Delta f_{RA},c),
$$

其中 $n_f$ 是系统帧，$n_{slot}$ 是用于窗口定位的 slot，$l_{start}$ 是起始 OFDM 符号，$n_{RA}$ 是同一时间实例内的频域 occasion 序号，$\Delta f_{RA}$ 是 PRACH SCS，$c$ 是 UL carrier。`ssb_index`、`preamble_index` 和 `ra_rnti` 是 RO 的关联字段，但不属于 RO 的物理坐标本身。

这样做能避免三个常见混淆：

- `slot` 不是任意采集块编号；RA-RNTI 所需的 `t_id` 要按规范规定的 SCS/120 kHz 基准换算。
- `n_RA`/`f_id` 不是绝对频率；还要经过 `msg1-FrequencyStart`、BWP、Point A 和 PRACH 占用 RB 的映射。
- `l_start` 只是前导起点；有效序列、CP、保护区和检测窗口长度还由格式与 SCS 决定。

## 19. 从配置索引展开 RO

38.211 V17.8.0 将格式、时间位置和部分采样参数分散在表 6.3.3.1-1/2、6.3.3.2-1/2/3/4。接收机应使用“查表 + 约束过滤”，不要把 `prach-ConfigurationIndex` 当作可线性计算的周期。

```python
expand_ro(config, frame_range):
    row = lookup_format_and_timing_table(config.release,
                                         config.frequency_range,
                                         config.spectrum_type,
                                         config.prach_configuration_index)
    derive L_RA, Δf_RA, N_u, N_CP, starting_symbol, period
    for each frame in frame_range:
        enumerate time occasions from row and frame modulo period
        enumerate f_id = 0 .. msg1_FDM-1
        calculate local PRACH frequency bins and absolute frequency
        apply TDD/SSB/guard-gap validity rules
        emit ro_snapshot with source row and rejection reason
```

查表结果至少保存 `table_id`、Release、频段/频谱类型和原始索引。若同一索引在不同表中出现，必须先用频段和 spectrum type 消歧，再生成 RO。

## 20. 时间有效性：配对、非配对与 TDD

在 Release 17 的 38.213 §8.1 中，配对频谱或 SUL 的 RO 有效性规则与非配对频谱不同。非配对频谱下，RO 还要满足下列检查：

1. RO 不得在同一 PRACH slot 的 SS/PBCH block 之前非法开始；
2. 若配置了 `tdd-UL-DL-ConfigurationCommon`，RO 必须落在 UL 符号，或满足与最后一个 DL/SSB 符号之间的 `N_gap`；
3. shared-spectrum 场景还要检查 channel occupancy time 和 LBT 约束；
4. 不允许把 guard/flexible 中被标为 DL 的符号当作可发 PRACH 的 UL 符号。

V17.8.0 的 `N_gap` 基线为：1.25/5 kHz 为 0，15/30/60/120 kHz 为 2，480 kHz 为 8，960 kHz 为 16。该表只对本轮 Release 基线成立；现场采用其他版本时重新核验。

有效性过滤应同时输出 `valid=false` 的原因，例如 `overlaps_dl`、`before_ssb`、`guard_gap`、`lbt_window` 或 `outside_capture`，否则“未检测到”无法区分资源不存在和采集遗漏。

## 21. SSB-to-RO 映射

`ssb-perRACH-OccasionAndCB-PreamblesPerSSB` 同时表达 SSB/RO 比例和每个 SSB 的竞争前导数量。38.213 §8.1 的映射顺序是：

1. 单个 RO 内按前导索引递增；
2. 同一时间实例内按频域 RO 索引递增；
3. 一个 PRACH slot 内按时间 RO 索引递增；
4. 再按 PRACH slot 索引递增。

从 frame 0 开始，选择能让配置的 SS/PBCH block indexes 至少映射一次的最小 association period；V17 表 8.1-1 给出 10/20/40/80/160 ms 配置周期对应的候选周期集合，pattern period 还需满足重复上限。未映射到 SSB 的 RO/前导不能被接收机擅自绑定到某个 beam。

项目侧建议显式保存映射表：

| 字段                      | 说明                                      |
| ------------------------- | ----------------------------------------- |
| `association_period_id` | 映射周期编号和起始 frame                  |
| `ro_id`                 | 时间/频率 RO 唯一键                       |
| `ssb_index`             | 关联 SS/PBCH block，可为`null`          |
| `preamble_range`        | 该 SSB 可用的连续或分区前导索引           |
| `mapping_source`        | common、dedicated、PDCCH order 或 unknown |
| `validity_reason`       | 有效/无效及过滤原因                       |

## 22. 频域坐标与采样坐标

38.211 §6.3.3.2 的物理映射可抽象为：

$$
a_k^{(p,RA)}=\beta_{PRACH}y_{u,v}(k),
\qquad k=0,\ldots,L_{RA}-1,
$$

其中 PRACH antenna port 在 V17 基线为 4000；`k` 是 PRACH 序列内部索引，不是载波 FFT 的绝对 bin。载波 FFT 中的起点还受 `k_1`、BWP 起点、`msg1-FrequencyStart`、`n_RA` 和表 6.3.3.2-1 的 RB 分配影响。

应同时记录：

- `prb_local`：PRACH 资源相对 UL BWP 的局部 RB；
- `crb_absolute`/`absolute_frequency_hz`：经过 Point A 后的坐标；
- `fft_bin`：当前采样率和 FFT 约定下的数组位置；
- `prach_scs_hz` 与普通 UL BWP SCS；
- `frequency_index` 与 `f_id` 的来源和 0-based 约定。

同一 `f_id` 在不同 BWP/载波下不保证指向相同的绝对频率。任何“频域峰没找到”的结论，先检查坐标变换和采集带宽覆盖，再检查相关器。

## 23. RO 快照 schema

```js
ro_id: "cell=<id>|frame=<nf>|slot=<slot>|time=<t>|freq=<f>|carrier=<c>"
config_id: "<immutable-config-id>"
standard_release: "Rel-17 / version-17.x.y"
frame: null
slot:
  index: null
  scs_reference_hz: null
time:
  first_symbol: null
  n_symbols: null
  start_sample: null
  end_sample: null
frequency:
  f_id: null
  msg1_fdm: null
  msg1_frequency_start: null
  local_prb_start: null
  absolute_frequency_hz: null
  fft_bin_start: null
prach:
  format: null
  l_ra: null
  prach_scs_hz: null
  n_u_samples: null
  n_cp_samples: null
carrier:
  ul_carrier_id: 0
ssb:
  index: null
  association_period_id: null
validity:
  valid: false
  reason: "unknown"
provenance:
  table_id: null
  source_ref: []
```

`start_sample`/`end_sample` 必须注明是捕获起点、同步参考点还是绝对硬件时间换算；这两个字段不能与 ToA 峰位置混用。

## 24. RO 与 RA-RNTI 的接口

RO 展开完成后才具备计算 RA-RNTI 所需的 `s_id`、`t_id`、`f_id` 和 `ul_carrier_id`。前导索引不参与 RA-RNTI 的计算，但参与后续 RAR RAPID 匹配。建议在 `ro_snapshot` 生成时同时输出：

```js
ra_rnti_inputs:
  s_id: null
  t_id: null
  f_id: null
  ul_carrier_id: null
  index_origin: "0-based"
  formula_release: "Rel-17 / TS 38.321 V17.8.0"
```

若 `t_id` 的 SCS 基准或 `f_id` 的频域顺序不确定，RA-RNTI 只能写成候选集合，不得用一个猜测值盲搜整个 RAR 窗口。

## 25. 边界与故障矩阵

| 场景                     | 预期处理                                 | 日志状态                           |
| ------------------------ | ---------------------------------------- | ---------------------------------- |
| 配置周期跨 frame 0       | 按表中模运算展开，并保留周期起点         | `valid` 或 `needs_table_check` |
| RO 跨 slot/frame         | 保留实际起止样点，不截成单 slot          | `cross_boundary`                 |
| 多个频域 RO              | 每个`f_id` 单独相关和单独 RA-RNTI 输入 | `valid`                          |
| RO 与 DL/SSB 重叠        | 按 38.213 规则过滤                       | `invalid:overlap`                |
| shared-spectrum/LBT 禁止 | 不运行 PRACH 相关器                      | `invalid:lbt_window`             |
| SSB 未映射               | 物理检测可继续，beam 字段为`unknown`   | `unassociated`                   |
| 采集带宽覆盖不全         | 不把缺失频域当无前导                     | `outside_capture`                |
| Type-1/Type-2 共享 RO    | 按配置拆分流程和窗口                     | `shared_ro`                      |

## 26. 最小验收用例

1. 选一个 Release 17 表行，逐字段回放格式、SCS、`L_RA`、起始符号和持续样点。
2. 在 `msg1-FDM=one` 与多频分复用配置之间切换，检查 `f_id` 数量、频域起点和 RA-RNTI 输入变化。
3. 对 paired、unpaired、TDD DL overlap 和 guard-gap 场景分别验证 `validity_reason`。
4. 用已知 `ssb-PositionsInBurst` 与 association period 重建映射顺序，检查未映射 RO 不被绑定。
5. 让 RO 跨 frame/slot 边界，比较符号坐标、样点坐标和窗口起止的一致性。
6. 用两个载波或 SUL 配置确认 `ul_carrier_id` 进入事件键和 RA-RNTI 输入，而不改变前导模板。

## 27. 来源与证据账本

| 来源                                                                                                        | 证据级别              | 本笔记使用范围                                                | 状态                          |                    |
| ----------------------------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------- | ----------------------------- | ------------------ |
| [TS 38.211 V17.8.0](https://etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf) | `STANDARD`          | §6.3.3.1/2 的格式、序列和物理坐标                            | 现场 Release 未锁定           |                    |
| [TS 38.213 V17.8.0](https://etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) | `STANDARD`          | §8.1 的 RO 有效性、SSB 映射、association period 和`N_gap`  | 设备动态配置待核              |                    |
| [TS 38.331 V17.0.0](https://etsi.org/deliver/etsi_ts/138300_138399/138331/17.00.00_60/ts_138331v170000p.pdf) | `STANDARD`          | `RACH-ConfigGeneric`、`msg1-FDM`、频域起点和 SSB/前导字段 | 当前 RRC 快照缺失             |                    |
| [[5G-NR-Positioning/01-NR基础/NR TDD]]                                                                                                            | NR TDD]]              | `PERSONAL_NOTE`                                             | 项目 D/U/F 过滤和采集窗口边界 | 需真实配置验证     |
| [[5G-NR-Positioning/02-PRACH/PRACH Configuration                                                            | PRACH Configuration]] | `PERSONAL_NOTE`                                             | 配置快照与`config_id` 契约  | 与现场字段尚未闭合 |

## 28. 待核验项

- 当前网络适用的 38.211/38.213/38.331 Release 和 spectrum type；
- `prach-ConfigurationIndex` 对应的具体表行、格式、周期和 `N_u/N_CP`；
- SSB-to-RO association period、beam 映射及 `ra-ssb-OccasionMaskIndex`；
- 采样率、FFT、Point A/BWP 和 PRACH 独立 SCS 的坐标变换；
- shared-spectrum、SUL、IAB、Type-2/MsgA 等扩展是否出现在现场数据中。
