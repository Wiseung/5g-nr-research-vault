---
title: PDCCH Overview
aliases:
  - NR PDCCH 总览
  - 物理下行控制信道总览
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - topic/用户关联
  - process/blind-detection
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TS 38.214
  - 用户项目流程说明
related:
  - "[[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]"
  - "[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|既有 PDCCH 盲搜笔记]]"
  - "[[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]"
  - "[[04-PDSCH/PDSCH|PDSCH]]"
---

# PDCCH Overview

> [!abstract] 项目主线
> PDCCH 是承载 DCI 的物理下行控制信道。被动接收机在合法的 CORESET、搜索空间和候选位置上解映射并译码，通过 RNTI 掩码和字段约束确认 DCI，再由 DCI 驱动 [[04-PDSCH/PDSCH|PDSCH]] 或上行资源解析。

## 1. 一句话定义

PDCCH（Physical Downlink Control Channel）是在 NR 下行资源网格中传输 DCI 的控制信道；它由 CCE/REG/RE 资源、PDCCH DM-RS、加扰调制和候选监测规则共同构成。

## 2. 为什么项目需要它

PRACH 只提供随机接入入口，不能直接给出连接期间的 C-RNTI。项目需要在 RA 事件建立有限 RNTI 候选后，监测 C-RNTI 相关的 PDCCH，取得 DCI 的时频、MCS、HARQ 和参考信号参数，才能定位目标 UE 的后续数据资源。核心既有说明见 [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]。

## 3. 它位于整个 5G 空口链路的什么位置

在本项目中，PDCCH 位于以下控制到数据链的中间：

```text
Raw IQ
  -> NR 同步与小区识别
  -> TDD DL/UL 标注
  -> CORESET/搜索空间配置
  -> PDCCH 候选解映射与盲译码
  -> DCI + RNTI 关联
  -> PDSCH/PUSCH 资源快照
  -> UE 信号提取与时序观测
  -> 多站 TDOA
```

PDCCH 是下行控制承载，不等同于 DCI 比特本身，也不等同于后续的 PDSCH 数据。

## 4. 输入

接收端至少需要以下输入；缺失项应显式记为 `unknown` 或 `NEEDS_VERIFICATION`：

| 输入 | 作用 |
|---|---|
| 复基带 IQ/资源网格 | 提供候选控制资源的观测 |
| 小区、载波、SCS、BWP 和时隙坐标 | 把局部 RE 映射到绝对时间/频率 |
| CORESET 配置 | 限定控制资源的频域、时域和 CCE-to-REG 关系 |
| Search Space 配置 | 生成监测时机、聚合等级和候选 |
| DCI 格式/长度假设 | 决定 Polar/字段解释分支 |
| RNTI 候选及来源 | 执行 CRC 掩码检查和用户关联 |
| PDCCH DM-RS、噪声/信道估计输入 | 产生均衡后的软比特 |

项目配置层、观测层和协议层的分层约定沿用 [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|5G TDD 上下行监测与资源解析]]。

## 5. 输出

每个候选应输出可回放的 `candidate_record`，而不是只返回一个布尔值：

```js
monitoring_slot: ""
coreset_id: null
search_space_id: null
aggregation_level: null
candidate_index: null
rnti_hypothesis: null
dci_format: ""
llr_shape: ""
crc_state: "invalid|fail|pass"
field_valid: false
candidate_state: "invalid_candidate|not_present|decode_fail|crc_fail|crc_pass|valid_dci"
resource_snapshot: ""
```

只有 `valid_dci` 才能进入 [[04-PDSCH/PDSCH|PDSCH]]/PUSCH 资源解析；`crc_pass` 仍需字段、资源和跨时隙连续性检查。

## 6. 关键参数

| 参数 | 项目中要保存的内容 |
|---|---|
| `NCellID`/载波/BWP | 小区和频域坐标上下文 |
| `coreset_id`、时域持续长度、频域资源 | 控制区域掩码 |
| `search_space_id`、周期/偏移/监测符号 | 候选出现的时机 |
| 聚合等级 `L`、候选索引 | 候选占用的 CCE 范围 |
| PDCCH DM-RS 参数 | 序列、端口、资源索引和估计质量 |
| DCI 格式、有效载荷长度 | 字段和 Polar 长度假设 |
| RNTI 类型/值/来源/有效期 | CRC 掩码和关联证据 |
| `K/N/E`、LLR 约定 | 38.212 解码账本 |
| 监测时隙、符号、绝对子载波 | 跨站和后续资源定位坐标 |

精确的候选数量、聚合等级集合、序列初始化和字段长度随 Release/配置变化，不能从本页默认补齐。

## 7. 时域位置

PDCCH 只在配置的 CORESET OFDM 符号和 Search Space 监测时机出现。接收机要同时记录帧号、时隙号、起始符号和监测周期/偏移；不能把每个时隙的整个资源网格都假设为 PDCCH。TDD 的 `DL/UL/flexible` 标注来自网络配置，见 [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|TDD 监测笔记]]。

## 8. 频域位置

PDCCH 的频域资源由 CORESET 的频域资源集合和 BWP/Point A 坐标确定，再经 REG/CCE 组织和可能的交织映射落到 RE。数组局部子载波下标不一定等于载波绝对下标；要同时保存 `grid_index` 和 `absolute_subcarrier`。具体频域资源位图和交织参数必须按适用 Release 外部核验。

## 9. 数学原理

对候选 $h$ 的 PDCCH 资源，接收模型可抽象为：

$$
\mathbf{y}_h=\mathbf{H}_h\mathbf{x}_h+\mathbf{n}_h,
$$

其中 $\mathbf{x}_h$ 包含控制调制符号和 DM-RS，$\mathbf{H}_h$ 是候选资源上的等效信道。经信道估计、均衡和软解调后，DCI 编码链可记为：

$$
A_h \xrightarrow{+CRC} K_h
\xrightarrow{\mathrm{Polar}} N_h
\xrightarrow{\mathrm{rate\ matching}} E_h
\xrightarrow{\mathrm{PDCCH\ mapping}} \mathbf{y}_h.
$$

接收端用 RNTI 假设 $r_h$ 检查译码结果 $\hat{\mathbf a}_h$：

$$
q_h=\mathbf{1}\left[\mathrm{CRC}_{r_h}(\hat{\mathbf a}_h)=0\right].
$$

`q_h=1` 只是候选证据，最终接受还要满足资源和字段语义约束。长度、位序和掩码方向以 [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]] 为接口，具体标准参数仍需核验。

## 10. 3GPP 对应规范

| 规范 | 本笔记使用的边界 | Clause/字段状态 |
|---|---|---|
| TS 38.211 | PDCCH 加扰、调制、PDCCH DM-RS 和 RE 映射；与 CORESET/CCE/REG 的物理资源接口 | PDCCH 相关 §7.3.2 子条款建议核对目标 Release；`NEEDS_EXTERNAL_REFERENCE` |
| TS 38.212 | DCI 的 CRC、Polar 编码、率匹配和逆处理 | DCI/控制信息相关 §5.3 子条款需按 Release 核对；`NEEDS_EXTERNAL_REFERENCE` |
| TS 38.213 | PDCCH 监测、Search Space、候选和 RNTI 上下文 | 控制信道接收相关 §10 范围需按 Release 核对；`NEEDS_EXTERNAL_REFERENCE` |
| TS 38.214 | DCI 字段驱动的 PDSCH/PUSCH 调度、MCS、HARQ 和资源解释 | 具体字段/表格需按 Release 核对；`NEEDS_EXTERNAL_REFERENCE` |
| TS 38.331 | RRC 中 `ControlResourceSet`、`SearchSpace` 等配置字段 | ASN.1 字段版本需外部核验；`NEEDS_EXTERNAL_REFERENCE` |

本地标准笔记确认了上述职责分工，但没有锁定项目 Release 的完整表格；不得把本表当作合规实现证明。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

既有项目笔记记录了以下 MathWorks API 线索：

| 函数 | 用途 | 状态 |
|---|---|---|
| `nrPDCCHSpace` | 生成/查询搜索空间候选资源和 PDCCH DM-RS 索引的示例入口 | `NEEDS_EXTERNAL_REFERENCE`；需核对版本和输入维度 |
| `nrPDCCHDecode` | 对候选 PDCCH 做软解调/解扰或控制比特恢复的示例入口 | `NEEDS_EXTERNAL_REFERENCE` |
| `nrDCIDecode` | 按 DCI 假设进行率恢复、Polar/CRC 判决的示例入口 | `NEEDS_EXTERNAL_REFERENCE` |
| `nrExtractResources` | 从资源网格提取候选资源 | `NEEDS_EXTERNAL_REFERENCE` |
| `nrChannelEstimate`、`nrEqualizeMMSE` | 候选 DM-RS 信道估计和均衡 | `NEEDS_EXTERNAL_REFERENCE` |

这些函数名来自 [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|既有项目笔记]] 的官方示例线索，不代表本项目已运行。MATLAB 版本、5G Toolbox 版本、对象属性、RNTI 参数和数组维度必须在本机记录。

## 12. 本项目中的用途

PDCCH 是 `C-RNTI -> DCI -> PDSCH/PUSCH -> UE signal extraction` 的控制枢纽：

1. 从 [[02-PRACH/Random Access Procedure|Random Access Procedure]] 的证据链得到 C-RNTI 候选，而不是从 PRACH 峰直接命名 C-RNTI。
2. 用 [[03-PDCCH/CORESET|CORESET]] 和 [[03-PDCCH/Search Space|Search Space]] 限定候选。
3. 在 [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]] 中完成候选级资源解映射、Polar、CRC/RNTI 和字段检查。
4. 读取 [[03-PDCCH/DCI|DCI]]，生成 `resource_snapshot`，交给 [[04-PDSCH/PDSCH|PDSCH]] 和后续单用户时频截取。
5. 为 [[05-定位观测量/Timing Observation|Timing Observation]] 保存方向、符号、RE 和 C-RNTI 关联证据。

## 13. 常见误区

- 把 PDCCH 当成 DCI 的同义词；PDCCH 是物理承载，DCI 是控制信息。
- 把 PRACH 前导或 RA-RNTI 当成最终 C-RNTI；二者需要 RAR、Msg3/Msg4 和争用解决证据连接。
- 看到一个 CRC 通过就判为有效 DCI；还要检查候选位置、格式、字段范围和跨时隙连续性。
- 把 CORESET 的频域区域当成 Search Space 的全部候选；前者是资源集合，后者定义何时和哪些候选被监测。
- 忽略 PDCCH DM-RS、BWP 偏移、TDD 方向或绝对频率坐标，导致后续 PDSCH 资源整体错位。

## 14. 与相似概念的区别

| 概念 | 主要回答的问题 | 与 PDCCH 的关系 |
|---|---|---|
| DCI | 网络要调度什么、何时调度、用什么 MCS/HARQ | 由 PDCCH 承载的比特信息 |
| CORESET | 哪片时频资源可以承载控制 | PDCCH 物理资源边界 |
| Search Space | 何时监测、哪些聚合等级/候选 | PDCCH 候选生成规则 |
| PDSCH | 下行数据位于哪些资源 | 通常由 DCI 调度，不是 PDCCH |
| RA-RNTI/C-RNTI | 当前控制上下文属于哪个过程/UE | 用于 CRC 掩码和关联，不是物理信号 |

## 15. 代码实现注意事项

- 为每个 `(slot, coreset, search_space, L, candidate, rnti)` 保存不可变候选记录。
- 显式管理 `RE -> REG -> CCE -> candidate` 索引，保留局部和绝对坐标；不要依赖隐式转置。
- 把 `invalid_candidate`、`decode_fail`、`crc_fail`、`crc_pass`、`valid_dci` 分开计数。
- 为 PDCCH DM-RS、数据 RE 和保留 RE 建立互斥掩码，并记录端口/层域。
- 保留 `K/N/E`、LLR 符号/尺度、Polar 版本和 RNTI 掩码假设；不以默认值静默填补未知参数。
- DCI 通过后生成独立的 `resource_snapshot` 与 `coding_snapshot`，供 [[04-PDSCH/PDSCH|PDSCH]] 解析和定位支路复用。
- 对候选级计算量记录 P95/P99 或最大尾延迟，不能只记录平均耗时。

## 16. 待实验验证的问题

- [ ] 在已知 C-RNTI、单 CORESET、单候选、无噪声条件下闭合 PDCCH -> DCI。
- [ ] 构造错误 RNTI、错误候选位置和错误聚合等级，验证失败状态可区分。
- [ ] 在 AWGN、CFO、定时偏移和多径下分别记录 DM-RS 质量、DCI BLER、误检率和尾延迟。
- [ ] 用有效 DCI 驱动 [[04-PDSCH/PDSCH|PDSCH]]，核对 PRB/符号/MCS/TBS/RV/DM-RS 资源快照。
- [ ] 用 RA 驱动的有限 C-RNTI 候选池做跨时隙连续性和误关联测试。
- [ ] 验证 PDCCH DM-RS 只作为控制候选质量/同步辅助，不被误用为 UE 上行 TDOA 主观测。

## 17. 控制域的四层边界

PDCCH 相关问题经常因为把不同层的对象写进同一个字段而失去可复现性。项目实现应按以下边界传递数据：

| 层 | 对象 | 负责的问题 | 典型输入 | 典型输出 |
|---|---|---|---|---|
| 配置层 | BWP、CORESET、Search Space、TDD | 哪些资源、何时允许监测 | SIB/RRC/MAC、设备元数据 | `config_snapshot` |
| 物理层 | CCE、REG、RE、DM-RS、LLR | 候选落在哪些样点、软信息是否可靠 | IQ/资源网格、同步、映射规则 | `candidate_record` |
| 控制信息层 | DCI format、字段、K0/K1 等 | 网络调度什么资源和过程 | Polar/CRC 输出、RNTI 假设 | `dci_record` |
| 协议/观测层 | RNTI 状态、事件、ToA/TDoA | 候选属于谁、能否进入定位链 | RA 证据、跨时隙快照、时钟 | `association_record`/定位观测 |

CORESET 不等于 Search Space，PDCCH 不等于 DCI，RNTI 不等于用户永久身份；这三个区分是本目录所有笔记的前置不变量。

## 18. 一次监测时机的生命周期

对一个 `monitoring_occasion`，建议按以下顺序生成并保存中间结果：

1. **锁定配置版本**：读取 `config_id`，确认 BWP、TDD 方向、CORESET 和 Search Space 未过期。
2. **判断是否应监测**：根据周期/偏移和监测符号生成 occasion；不命中时记录 `not_monitored`，不要生成空候选。
3. **枚举候选**：按聚合等级和候选索引生成 `first_CCE`，做边界、重叠和方向检查。
4. **建立物理索引**：使用 [[03-PDCCH/CCE REG|CCE REG]] 产生有序 CCE/REG/RE 索引，保留局部和绝对坐标。
5. **检查参考信号**：提取候选 DM-RS，记录相关质量、端口/序列假设和噪声方差。
6. **恢复软信息**：均衡、软解调、解扰和逆率匹配，保存 LLR 约定及 `A/K/N/E`。
7. **执行控制判决**：对每个 DCI 格式/RNTI 假设做 Polar、CRC 和字段检查，分别记录失败原因。
8. **生成快照**：只有 `valid_dci` 才生成 `resource_snapshot`/`coding_snapshot`；用户关联还需跨事件证据。

```text
not_monitored
    -> occasion_open
    -> candidate_generated
    -> dmrs_checked
    -> decoded
    -> crc_checked
    -> crc_pass
    -> valid_dci
    -> associated (可选，需额外协议证据)
```

## 19. 接受判据：从 CRC 到关联

把控制候选接受写成分层谓词，比返回一个 `true/false` 更容易定位问题：

$$
I_{crc}(h,r)=\mathbf{1}\left[\mathrm{CRC}_{r}(\hat{a}_h)=0\right]
$$

$$
I_{valid}(h,r)=I_{crc}(h,r)
\cdot I_{format}(h)
\cdot I_{field}(h)
\cdot I_{resource}(h)
$$

$$
I_{associated}(h,r)=I_{valid}(h,r)
\cdot I_{temporal}(h,r)
\cdot I_{protocol}(h,r)
$$

其中：

- `CRC pass` 对应 $I_{crc}=1$，只说明当前 RNTI 假设与译码结果相容。
- `valid_dci` 对应 $I_{valid}=1$，还要满足格式、字段范围和资源可解释性。
- `associated` 对应 $I_{associated}=1$，需要 RA/临时标识、后续 DCI 连续性或其他明确协议证据。

错误候选、错误 RNTI 和错误字段都应保留为负例；不能为了提高“检测率”而删除它们。

## 20. 统一事件和快照接口

```js
event_id: ""
config_id: ""
candidate_id: ""
control:
  frame: null
  slot: null
  coreset_id: null
  search_space_id: null
  aggregation_level: null
  candidate_index: null
  first_cce: null
  rnti_type: "unknown"
  rnti_value: null
  dci_format: ""
  crc_state: "not_run|fail|pass"
  field_valid: false
data:
  direction: "DL|UL|unknown"
  frame: null
  slot: null
  bwp_id: null
  prb_indices_local: []
  prb_indices_absolute: []
  symbol_indices: []
  mcs_index: null
  rv: null
  harq_process: null
positioning:
  source_signal: "unknown"
  sample_origin: ""
  toa_state: "not_run|valid|unreliable"
  calibration_id: ""
quality_flags: []
```

控制时刻和数据时刻必须分列保存。若 DCI 字段尚未能解释到数据资源，`data` 保持缺失并写入 `missing_fields`，不能以控制 slot 或零 PRB 代替。

## 21. PDCCH 与定位观测的边界

PDCCH 的下行 DM-RS 可以用于候选质量、下行同步或配置诊断，但它不携带 UE 上行传播时延的充分身份信息。对本项目的 UL-TDOA 支路，优先级应是：

1. 用 PDCCH/DCI 建立“哪个时隙、哪个 UE 上下文、哪组上行资源”的约束。
2. 用 DCI 解析出的 PUSCH/DM-RS、SRS 或其他已确认上行参考形成单用户观测。
3. 在跨站融合前校正采样起点、RF 延迟、滤波群时延和站间时钟偏差。
4. 同时保存 raw/corrected ToA、峰策略、质量和不确定度；不能用 PDCCH CRC 通过替代时间测量证据。

## 22. 目录级核验门

| 门 | 最小正例 | 必须通过的断言 | 当前状态 |
|---|---|---|---|
| P0 配置 | 一份已知 BWP/CORESET/SS | 坐标和版本可回放 | `TODO` |
| P1 映射 | 一个已知候选 | CCE/REG/RE 正逆映射、掩码互斥 | `TODO` |
| P2 控制 | 无噪声单 DCI | 正确 RNTI 通过、错误 RNTI 失败 | `TODO` |
| P3 语义 | 一个已知 DCI format | 字段范围和方向判定正确 | `TODO` |
| P4 数据 | DCI 驱动的 PDSCH/PUSCH | 资源/编码快照与真值一致 | `TODO` |
| P5 关联 | RA 驱动有限 RNTI 池 | 跨时隙状态和老化可解释 | `TODO` |
| P6 定位 | 三站上行参考 | 时间基准和校准证据完整 | `TODO` |

这些是验收门和实验设计，不是已经完成的实验结果。

## 23. Rel-17 V17.8.0 参考版本索引

为了让目录中的“标准事实”和“项目约定”可区分，下面记录已核对的 Release 17 入口（访问日期 2026-09-05）：

| 标准 | 已核验的 PDCCH 边界 | 对应目录笔记 |
|---|---|---|
| [TS 38.211 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf) §7.3.2/§7.4.1.3 | CCE/REG/CORESET、PDCCH 扰码/QPSK/端口、DM-RS 和物理映射 | [[03-PDCCH/CORESET|CORESET]]、[[03-PDCCH/CCE REG|CCE REG]] |
| [TS 38.212 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.08.00_60/ts_138212v170800p.pdf) §7.3 | DCI 格式、尺寸对齐、CRC attachment、Polar 和率匹配 | [[03-PDCCH/DCI|DCI]] |
| [TS 38.213 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) §10.1 | CSS/USS、monitoring occasion、候选 CCE 和监测预算 | [[03-PDCCH/Search Space|Search Space]]、[[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]] |
| [TS 38.214 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/17.08.00_60/ts_138214v170800p.pdf) 数据过程章节 | DCI 到 PDSCH/PUSCH 资源、MCS/HARQ/层和反馈上下文的解释边界 | [[03-PDCCH/DCI|DCI]]、[[04-PDSCH/PDSCH|PDSCH]] |

这些链接证明的是参考文本已读取，不证明当前第三方设备使用同一 Release，也不证明本项目代码已经通过 conformance test。现场配置、工具箱版本和实验结果仍需单独记录。

## 24. 证据与当前状态

- `STANDARD + verified-reference`：上面的 Rel-17 V17.8.0 参考版本和本地 TS 38.211/212/213/214 摘要。
- `PERSONAL_NOTE`：项目主线是 `C-RNTI -> PDCCH -> DCI -> PDSCH/PUSCH -> UE resource extraction -> Timing Observation`。
- `EXPERIMENT + NEEDS_VERIFICATION`：当前没有真实设备候选、LLR、CRC、DCI 或定位结果。
- `NEEDS_EXTERNAL_REFERENCE`：当前项目 Release/现场配置、38.331 RRC 字段、工具箱 API、版本差异和一致性向量。

## 25. Related Notes

- [[03-PDCCH/CORESET|CORESET]]
- [[03-PDCCH/Search Space|Search Space]]
- [[03-PDCCH/CCE REG|CCE REG]]
- [[03-PDCCH/DCI|DCI]]
- [[03-PDCCH/RNTI|RNTI]]
- [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]
- [[02-PRACH/C-RNTI|C-RNTI]]
- [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
- [[04-PDSCH/PDSCH|PDSCH]]
- [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]
- [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]
- [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]]
- [[05-定位观测量/Timing Observation|Timing Observation]]
