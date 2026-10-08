---
title: PRACH Configuration
aliases:
  - NR PRACH 配置
  - RACH-ConfigCommon
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - topic/configuration
  - stage/receiver
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.331
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Overview|PRACH Overview]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]"
  - "[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]"
  - "[[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|现有 TDD 监测主线]]"
---
# PRACH Configuration

## 1. 一句话定义

PRACH Configuration 是把 RRC/MAC 配置字段转换为可生成 Occasion、前导集合和检测窗口的参数快照。

## 2. 为什么项目需要它

被动接收机没有网络侧调度权限，必须先知道“何时、何频、哪种格式、哪些前导”才可能把相关峰解释为 PRACH。配置错误会伪装成检测器或后续 RAR 解码错误。

## 3. 它位于整个 5G 空口链路的什么位置

它位于小区同步、MIB/SIB1/RRC 恢复之后，为 PRACH Occasion、Preamble、检测、RA-RNTI 计算提供输入；它也连接 TDD 方向标注和后续 RAR 监测。

## 4. 输入

- RACH-ConfigCommon、ServingCellConfigCommon 和 BWP/载波配置。
- 小区 ID、SSB/beam 配置、SCS、频域起点和 TDD pattern。
- 网络 Release、设备元数据及捕获采样率。

## 5. 输出

结构化 prach_snapshot，至少包括格式、L_RA、根序列、循环移位/零相关区、msg1-FDM、频域起点、时域 Occasion、SSB 映射、功率参数、响应窗口和版本。

## 6. 关键参数

prach-ConfigurationIndex、msg1-FDM、msg1-FrequencyStart、zeroCorrelationZoneConfig、restrictedSetConfig、preambleReceivedTargetPower、powerRampingStep、preambleTransMax、ra-ResponseWindow、ssb-perRACH-OccasionAndCB-PreamblesPerSSB、msg1-SubcarrierSpacing。字段是否存在及枚举含义需按 TS 38.331 版本核验。

## 7. 时域位置

配置索引映射到无线帧/时隙/符号中的合法 Occasion；应保存周期、起始符号、持续长度和响应窗口起止。TDD 下只在允许的 UL 或可用 flexible 区间检查，guard 符号不可当作前导数据。

## 8. 频域位置

配置同时决定 PRACH 使用的频域 Occasion 数量、起始 PRB/子载波和可能的独立 PRACH SCS。保存 Point A、BWP、绝对载频与本地 FFT bin 的映射，避免局部索引错位。

## 9. 数学原理

配置函数可抽象为

$$
\mathcal{C}_{RA}=F(\mathrm{SCS},\mathrm{configIndex},\mathrm{msg1\text{-}FDM},
\mathrm{freqStart},\mathrm{zeroCorrZone},\mathrm{SSB\ mapping}).
$$

接收机只在 $\mathcal{C}_{RA}$ 允许的时间频率集合做匹配滤波，从而降低虚警和计算量；任何默认参数都会扩大不可解释的候选空间。

## 10. 3GPP 对应规范

- TS 38.331：RACH-ConfigCommon、RACH-ConfigGeneric、SSB-to-RACH-occasion mapping 等字段；具体 clause/ASN.1 版本待核，标记 NEEDS_EXTERNAL_REFERENCE。
- TS 38.213 §8.1：PRACH Occasion、前导发送时机和相关资源过程，版本化表格待核。
- TS 38.211 §5.3.2、§6.3.3.2：配置到 PRACH OFDM 波形和物理资源映射。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHConfig：承载格式、频域、时域和根序列等属性。
- nrPRACHIndices、nrPRACH：从配置生成资源索引和前导。
- nrWaveformGenerator：若版本支持 PRACH 配置，可生成参考波形；对象字段和 SampleRate 计算需本机 help/ver 核验。

上述 API 仅作实现入口，函数签名、属性和版本行为为 `NEEDS_EXTERNAL_REFERENCE`，尚无本项目运行证明。

## 12. 本项目中的用途

把设备元数据或 SIB1/RRC 解码结果固化为 config_id，驱动 [[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]] 和 [[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]；配置版本随后写入 RA 事件、RAR 候选和 C-RNTI 关联日志。

## 13. 常见误区

- 把中心频率、采样率、带宽和用户口述的“120.88 兆”混成一个字段。
- 假定所有网络使用同一个 PRACH format 或 15 kHz SCS。
- 只记录配置索引，不记录其解析后的 Occasion/频域结果。
- 在配置未知时用“常见小区参数”静默填充。

## 14. 与相似概念的区别

PRACH Configuration 是配置快照，不是 Occasion 实例；RACH-ConfigCommon 是高层信令结构，TS 38.211 的物理映射是其下游解释；TDD pattern 决定方向可用性，但不替代 PRACH 专用参数。

## 15. 代码实现注意事项

- 用不可变 config_id 关联每次解析，配置切换时递增版本。
- 对枚举和单位做显式校验，所有缺失字段写 null/unknown。
- 生成检测窗口前检查采样率、FFT、CP 和 PRACH SCS 是否一致。
- 缓存时键中包含小区、BWP、载波和 Release，不能只用 config index。

## 16. 待实验验证的问题

- 能否从当前设备输出取得完整 RACH-ConfigCommon，而非手工参数。
- 网络是否启用 2-step、CFRA、restricted set 或 beam-specific 映射。
- 配置切换时旧快照多久失效，接收机如何检测并重置。
- 不同 MATLAB 版本对 nrPRACHConfig 属性的差异。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Overview|PRACH Overview]]、[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]、[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]、[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]。
- 旧笔记：[[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|现有 TDD 监测主线]]、[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]]。

## 18. 配置来源与优先级

配置解析器应先区分“来源”与“解释结果”，再合并为一个不可变快照。推荐的来源优先级如下：

1. SIB1/系统信息中的小区公共配置；
2. RRC_CONNECTED 下的 `RACH-ConfigDedicated`、BWP 和 beam-specific 配置；
3. PDCCH order 或其他动态触发携带的专用索引；
4. 设备导出的解码元数据；
5. 人工输入的实验参数（只能标为 `EXPERIMENT` 或 `HYPOTHESIS`）。

同名字段来自不同来源时，不应直接覆盖。快照保留 `source_ref`、解析时间、Release 和原始字节/文本摘要，冲突记录在 `conflicts` 数组中。

## 19. 字段字典（Release 17 基线）

下表按照 38.331 V17.0.0 的 `RACH-ConfigCommon`、`RACH-ConfigGeneric` 和 `RACH-ConfigGenericTwoStepRA` 组织。范围和枚举是核验基线，不是当前网络实测值。

| 字段                                          | 语义                                             | 解析结果/校验                                       |
| --------------------------------------------- | ------------------------------------------------ | --------------------------------------------------- |
| `prach-ConfigurationIndex`                  | 由 38.211 表格索引时间资源、格式和相关参数       | 保存原值与查表版本；不可自行推导表行                |
| `msg1-FDM`                                  | 一个时间实例中频分复用的 PRACH occasion 数       | 枚举`one/two/four/eight`；展开为 `f_id` 集合    |
| `msg1-FrequencyStart`                       | 最低 PRACH occasion 相对 UL BWP PRB 0 的频域偏移 | 检查整个 PRACH 资源位于 BWP 内                      |
| `zeroCorrelationZoneConfig`                 | `N_CS` 查表索引                                | 与`L_RA`、restricted set 联合解析                 |
| `preambleReceivedTargetPower`               | 网络接收端目标前导功率                           | V17 基线为 2 dB 步进；单位与功率参考点分开保存      |
| `preambleTransMax`                          | 失败前允许的前导发送次数                         | 保存枚举和展开整数，不把重传次数当检测次数          |
| `powerRampingStep`                          | 失败重传的功率爬升步长                           | 与`PREAMBLE_POWER_RAMPING_COUNTER` 一起记录       |
| `ra-ResponseWindow`                         | Msg2/RAR 监测窗口长度                            | 单位是基于 Type1-PDCCH CSS 的 slot；用同一 SCS 换算 |
| `prach-RootSequenceIndex`                   | PRACH 根序列逻辑索引                             | 结合`L_RA` 选择对应逻辑到物理根表                 |
| `msg1-SubcarrierSpacing`                    | PRACH 子载波间隔（可选）                         | 缺省时从配置索引查表；不得默认为普通 UL SCS         |
| `restrictedSetConfig`                       | unrestricted、restricted type A/B                | 传递给循环移位映射和检测器                          |
| `totalNumberOfRA-Preambles`                 | 该 RACH 资源中的前导总数                         | 与 SSB/RO 映射和 group A/B 一致性校验               |
| `ssb-perRACH-OccasionAndCB-PreamblesPerSSB` | SSB/RO 比例与每 SSB 的 CB 前导数                 | 展开为 SSB、RO、preamble 三元映射                   |
| `groupBconfigured`                          | Msg3 大小阈值、功率偏移、Group A 数量            | 只影响 CBRA 前导组选择                              |
| `msgA-PRACH-ConfigurationIndex`             | Type-2/2-step 的 PRACH 配置索引                  | 与 Type-1 配置分开存储                              |
| `msgA-RO-FDM` / `msgA-RO-FrequencyStart`  | MsgA 的频域 occasion 数和起点                    | 仅在相应 Type-2 配置存在时生效                      |
| `msgA-ZeroCorrelationZoneConfig`            | MsgA 的`N_CS` 索引                             | 不自动继承 Type-1 值，须按 RRC 条件解析             |
| `msgB-ResponseWindow`                       | Type-2 响应窗口                                  | 与`ra-ResponseWindow` 分字段保存                  |

在 V17.0.0 中，`RACH-ConfigGeneric` 还定义 `preambleReceivedTargetPower` 的允许范围、`preambleTransMax`/`powerRampingStep`/窗口的枚举；若采用其他 Release，应重新生成该表并保留旧版本。

## 20. 标准字段到接收机字段的映射

```Markdown
RRC/SIB ASN.1
    -> raw_config（原始字段和值）
    -> normalized_config（单位、枚举、缺省和来源）
    -> derived_config（L_RA、N_CS、SCS、格式、BWP 坐标）
    -> ro_snapshot + preamble_map
```

建议至少保留以下字段：

```JSON
config_id: "sha-or-database-id"
standard_release: "Rel-17 / version-17.x.y"
cell_id: null
carrier:
  absolute_frequency_hz: null
  point_a: null
  ul_carrier_id: 0
  bwp_id: null
  bwp_start_prb: null
  bwp_size_prb: null
prach:
  configuration_index: null
  format: null
  l_ra: null
  prach_scs_hz: null
  msg1_fdm: null
  msg1_frequency_start: null
  root_sequence_index: null
  zero_correlation_zone_config: null
  restricted_set_config: null
  total_number_of_ra_preambles: null
  two_step: null
timing:
  frame_offset: null
  slot_offset: null
  tdd_pattern_ref: null
ssb_mapping:
  ssb_positions: []
  ssb_per_ro: null
  cb_preambles_per_ssb: null
provenance:
  source_kind: "STANDARD|EXPERIMENT|PERSONAL_NOTE"
  source_ref: []
  raw_digest: null
  conflicts: []
```

`raw_digest` 只用于确认快照未被意外修改，不替代对原始 RRC 内容的保存；不要把用户身份、密钥或机器路径放入快照。

## 21. 配置展开伪代码

```python
parse_common(raw, release):
    validate_schema(raw, release)
    cfg = normalize_units_and_enums(raw)
    cfg.l_ra, cfg.format, cfg.prach_scs = lookup_211_format(cfg.configuration_index,
                                                               cfg.msg1_subcarrier_spacing)
    cfg.n_cs = lookup_n_cs(cfg.zero_correlation_zone_config, cfg.l_ra, cfg.format)
    cfg.ro_table = enumerate_time_frequency_ro(cfg, release)
    cfg.ssb_map = map_ssb_to_ro(cfg, release)
    cfg.preamble_map = enumerate_root_and_shifts(cfg, release)
    validate_invariants(cfg)
    return freeze(cfg)
```

任何查表失败、字段缺失或版本不匹配都返回 `NEEDS_EXTERNAL_REFERENCE`，而不是使用默认行。`freeze` 后若收到新的 RRC 配置，应产生新的 `config_id`，旧事件仍引用旧快照。

## 22. 配置一致性不变量

- `L_RA` 必须属于当前 Release/频段/格式允许的集合；根序列长度与之相容。
- `msg1-FrequencyStart + PRACH 占用 RB 数` 不能越过 UL BWP；频域多路 RO 之间不得重叠。
- `msg1-SubcarrierSpacing` 缺省时只能由规范表推导，不能从采样率猜测。
- `zeroCorrelationZoneConfig`、`restrictedSetConfig`、根序列和前导总数必须共同生成完整（或明确不完整）的 `preamble_map`。
- SSB-to-RO 映射中的前导分区总数不能超过 `totalNumberOfRA-Preambles`；不满足时标记冲突。
- TDD 方向、guard gap、测量间隔和 RO 时间表必须在同一 frame/slot 坐标系中检查。
- Type-1 与 Type-2 的字段不能互相覆盖；共享 RO 仅在 RRC 明确允许时合并。

## 23. 参数缺失时的处理矩阵

| 缺失/冲突                        | 允许的输出                          | 禁止的推断               |
| -------------------------------- | ----------------------------------- | ------------------------ |
| 只有`prach-ConfigurationIndex` | 记录索引候选，等待版本/频段         | 默认为 15 kHz 或某个格式 |
| 有格式但无根序列                 | 可检查 RO，不能生成完整前导模板     | 使用固定根`u=1`        |
| 有 RO 但无 SSB 映射              | 可检测物理峰，SSB 字段置`unknown` | 把所有峰绑定到一个 beam  |
| 有 PRACH 峰但无 TDD 配置         | 标为`preamble_candidate`          | 宣称该峰一定是合法 UL    |
| Type-2 字段缺失                  | 只运行 Type-1 分支候选              | 自动把 MsgA 当 Msg1      |
| 设备值与 RRC 值冲突              | 双份保留并标`NEEDS_VERIFICATION`  | 静默选较“常见”的值     |

## 24. 最小单元测试

1. 对一个已知 Release 的配置索引，验证查表得到的格式、`L_RA`、SCS 和时间资源可以被序列生成器消费。
2. 改变 `msg1-FDM`，确认只改变 `f_id` 数量和频域起点，不改变根序列本身。
3. 改变 `msg1-FrequencyStart`，确认局部 FFT bin 与绝对 PRB 映射同步改变且不越界。
4. 删除 `msg1-SubcarrierSpacing`，确认解析器走查表路径并写出来源，而不是填常量。
5. 在 Type-1/Type-2 共存配置下，确认两套 `config_id`、RO 和窗口可以分别回放。
6. 对同一原始配置重复解析，确认 `config_id` 稳定；对任一字段变更，确认生成新 ID。

## 25. 来源与证据账本

| 来源                                                                                                        | 证据级别               | 本笔记使用范围                           | 状态                           |
| ----------------------------------------------------------------------------------------------------------- | ---------------------- | ---------------------------------------- | ------------------------------ |
| [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation本地 38.211 笔记]]                                                                                                            | `STANDARD + partial` | PRACH 波形、格式和物理映射入口           | 具体表格以 Release 17 PDF 复核 |
| [TS 38.211 V17.8.0](https://etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf) | `STANDARD`           | §5.3.2、§6.3.3.1/2 查表与坐标          | 现场 Release 未锁定            |
| [TS 38.213 V17.8.0](https://etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) | `STANDARD`           | §8.1 RO 有效性、SSB 映射和窗口接口      | 设备动态配置待核               |
| [TS 38.331 V17.0.0](https://etsi.org/deliver/etsi_ts/138300_138399/138331/17.00.00_60/ts_138331v170000p.pdf) | `STANDARD`           | RACH-ConfigCommon/Generic 字段与条件存在 | 当前网络值未知                 |
| [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析现有 TDD 监测主线]]                                                                                                            | `PERSONAL_NOTE`      | 采集坐标、TDD 方向和设备输入边界         | 需项目代码核对                 |

## 26. 待核验项

- 项目使用的 3GPP Release、FR1/FR2 频段和是否存在 SUL；
- RRC/SIB1 是否能导出完整 `RACH-ConfigCommon` 与 `RACH-ConfigDedicated`；
- 配置切换的生效时刻、旧 `config_id` 的事件寿命和跨帧处理；
- MATLAB/其他工具对 `L_RA`、PRACH SCS、Point A/BWP 的索引原点；
- `msgA-*`、IAB、shared-spectrum 和 beam-failure-recovery 扩展是否在现场出现。
