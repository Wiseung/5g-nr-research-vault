---
title: DCI
aliases:
  - Downlink Control Information
  - 下行控制信息
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - channel/dci
  - topic/调度
  - evidence/3gpp
source:
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TS 38.214
  - 用户项目流程说明
related:
  - "[[03-PDCCH/PDCCH Overview|PDCCH Overview]]"
  - "[[03-PDCCH/RNTI|RNTI]]"
  - "[[04-PDSCH/PDSCH|PDSCH]]"
---

# DCI

> [!abstract] 项目主线
> DCI（Downlink Control Information）是通过 PDCCH 发送的控制比特，描述下行分配或上行授权及其时序、资源、MCS、HARQ 等参数；被动接收机只有在候选资源、RNTI 掩码、格式和字段约束同时成立时，才能把译码结果作为后续 PDSCH/PUSCH 资源快照。

## 1. 一句话定义

DCI 是由网络在 PDCCH 上承载的格式化控制信息，用于指示 UE 如何接收 PDSCH、发送 PUSCH 或处理相关 HARQ/功控状态。

## 2. 为什么项目需要它

项目第二阶段的入口是 C-RNTI 驱动的 PDCCH 盲搜；DCI 是从“控制候选通过”走到“目标 UE 时频资源可提取”的桥梁。没有正确 DCI，就不能可靠确定 PDSCH/PUSCH 的 PRB、OFDM 符号、MCS、RV、层数和 DM-RS 关联，也不能把单用户信号送入后续 ToA/TDoA 支路。

## 3. 它位于整个 5G 空口链路的什么位置

~~~text
PDCCH 候选 RE
  -> 软解调/解扰
  -> Polar 逆率匹配与译码
  -> CRC + RNTI 掩码
  -> DCI 格式/字段解析
  -> resource_snapshot + coding_snapshot
  -> PDSCH/PUSCH
  -> UE Resource Extraction
~~~

DCI 是控制信息层；PDCCH 是物理承载层；PDSCH/PUSCH 是由 DCI 解释出的数据物理信道。

## 4. 输入

| 输入 | 用途 |
|---|---|
| 候选 PDCCH 的软比特/LLR | 进行逆率匹配和 Polar 译码 |
| DCI 格式与有效载荷长度假设 | 选择字段布局和 Polar 参数 |
| RNTI 候选/上下文 | 恢复 CRC 掩码并关联用户 |
| CORESET、Search Space、聚合等级 | 验证候选位置与编码长度 |
| 载波/BWP/TDD/时隙状态 | 解释时频字段和方向 |
| TS 38.214/配置字段 | 将比特转换为数据资源快照 |

若 DCI 格式、BWP 或 RNTI 来源不确定，应在输入中显式保留多个假设，而不是静默选择一个默认值。

## 5. 输出

DCI 解析器应输出比特级、协议级和资源级三类结果：

~~~js
dci_format: ""
payload_bits: ""
payload_length: null
rnti_type: "C-RNTI|RA-RNTI|SI-RNTI|unknown"
rnti_value: null
crc_state: "fail|pass"
field_valid: false
resource_snapshot: ""
coding_snapshot: ""
association_state: "candidate_only|associated|rejected"
~~~

resource_snapshot 至少包括方向、时隙偏移、BWP、PRB/符号分配、层数和 DM-RS/PTRS 相关配置；coding_snapshot 至少保留 MCS/TBS/RV、CRC/码块和 E 等待核对字段。CRC 通过但字段不合法时，状态不能升级为 valid_dci。

## 6. 关键参数

| 参数/字段 | 项目用途 | 状态 |
|---|---|---|
| DCI format（如 0_0、0_1、1_0、1_1） | 区分 UL grant/DL assignment 和字段布局 | 仅作示例，Release/适用性 NEEDS_EXTERNAL_REFERENCE |
| payload 长度 A | 进入 CRC/Polar 记账 | 由格式、带宽和配置决定 |
| CRC 长度/掩码 RNTI | 候选接受和用户上下文 | 按 38.212 核对 |
| K/N/E | Polar 输入、母码、率匹配长度 | 不能用固定常数 |
| 频域/时域分配 | 生成 PDSCH/PUSCH 资源 | 按 38.214 和 BWP 解释 |
| MCS、RV、NDI、HARQ process | 生成 coding_snapshot | 版本/配置相关 |
| K0/K1、PDSCH-to-HARQ 等时序字段 | 连接控制与数据时机 | 精确语义 NEEDS_EXTERNAL_REFERENCE |
| 天线端口/层/DM-RS 配置 | 目标 UE 资源和信道估计 | 与 [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]] 一致 |

不要把 DCI 字段名或位宽从某个 Release/工具箱示例直接复制到未知网络。

## 7. 时域位置

DCI 在 PDCCH 的监测时机发送，但其字段可能指向后续时隙或不同 OFDM 符号的数据资源。接收机需同时保存“DCI 所在 slot/symbol”和“被调度 PDSCH/PUSCH 的 slot/symbol”，并记录 K0/K1 或等效时序字段的解释状态。不能把 DCI 的控制时刻当成数据到达时刻。

## 8. 频域位置

DCI 自身的比特位没有独立频率含义；它通过频域资源分配字段指向 BWP 内 PRB/RIV 或其他资源集合，再转换为绝对载波子载波坐标。转换必须继承 [[03-PDCCH/CORESET|CORESET]]、Point A 和 BWP 偏移，保留局部与绝对坐标。

## 9. 数学原理

对候选 $h$，DCI 编码/映射链可抽象为：

$$
A_h
\xrightarrow{+\mathrm{CRC}(r_h)}K_h
\xrightarrow{\mathrm{Polar}}N_h
\xrightarrow{\mathrm{rate\ matching}}E_h
\xrightarrow{\mathrm{scramble/modulate/map}}\mathbf{y}_h.
$$

接收端对 $\mathbf{y}_h$ 做逆处理得到 $\hat{\mathbf a}_h$。RNTI 掩码判决可写为：

$$
q_h
=\mathbf{1}\left[
\mathrm{CRC}(\hat{\mathbf a}_h)
\oplus \mathrm{mask}(r_h)=\mathbf{0}
\right].
$$

只有同时满足格式和字段约束的候选才进入有效集合：

$$
\mathcal{D}_{valid}
=\{h:q_h=1,\ \mathrm{format\_valid}(h)=1,\ \mathrm{field\_valid}(h)=1\}.
$$

$A/K/N/E$、CRC 位序、掩码方向和 Polar 构造来自 [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]] 的接口；具体标准值不能由抽象式推断。

## 10. 3GPP 对应规范

| 规范 | 相关内容 | Clause/字段状态 |
|---|---|---|
| TS 38.212 | DCI CRC、Polar 编码、输入交织和率匹配/逆处理 | DCI/控制信息 §5.3 相关子条款；Release/子条款 NEEDS_EXTERNAL_REFERENCE |
| TS 38.213 | DCI 监测、Search Space、RNTI 上下文和控制时序 | 控制信道接收 §10 范围；精确子条款 NEEDS_EXTERNAL_REFERENCE |
| TS 38.214 | DCI 字段到 PDSCH/PUSCH 资源、MCS、HARQ 的解释 | 数据过程相关章节/表格需按 Release 核验 |
| TS 38.331 | RRC 提供的 BWP、CORESET、Search Space 和专用配置 | ASN.1 字段版本需外部核验 |

本地 [[02-标准与参考/3GPP/3GPP TS 38.212｜Multiplexing and channel coding|TS 38.212]] 和 [[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data|TS 38.214]] 只提供流程边界；不能据此声称当前设备已符合某个 Release。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

| 函数 | 用途 | 状态 |
|---|---|---|
| nrPDCCHDecode | 候选 PDCCH 的软处理/解扰线索 | NEEDS_EXTERNAL_REFERENCE |
| nrDCIDecode | DCI 率恢复、Polar/CRC 判决线索 | NEEDS_EXTERNAL_REFERENCE |
| nrPDCCHSpace | 候选资源/DM-RS 索引生成线索 | NEEDS_EXTERNAL_REFERENCE |
| nrExtractResources、nrChannelEstimate、nrEqualizeMMSE | 候选资源提取、DM-RS 估计、均衡 | NEEDS_EXTERNAL_REFERENCE |

函数名来自现有项目笔记和官方示例线索，并非本项目已运行结果。应在本机 MATLAB/5G Toolbox 版本中确认 DCI 格式、RNTI 参数、输入 LLR 形状、输出位序和错误状态。

## 12. 本项目中的用途

DCI 是 C-RNTI -> PDCCH -> DCI -> PDSCH/PUSCH 的协议解释器：

1. 用 [[03-PDCCH/RNTI|RNTI]] 提供的候选上下文检查 CRC 掩码。
2. 解析 DCI 格式和字段，区分 DL assignment 与 UL grant。
3. 生成可复现的 resource_snapshot/coding_snapshot。
4. 把 [[04-PDSCH/PDSCH|PDSCH]] 资源交给 DM-RS 信道估计、均衡、解调或单用户截取。
5. 将资源、时隙、方向和 C-RNTI 证据传递给 [[05-定位观测量/Timing Observation|Timing Observation]]，再进入 TDOA。

## 13. 常见误区

- 把 DCI 比特直接当作 PDSCH 业务数据，或把 PDCCH 资源当作 DCI 字段。
- 只依赖 CRC pass，不检查 DCI 格式、字段范围、时序和后续资源一致性。
- 把 RA-RNTI、TEMPORARY-C-RNTI 和 C-RNTI 的掩码上下文混用。
- 解析频域/时域字段时忽略 BWP、Point A、TDD 和时隙偏移。
- 使用固定 K/N/E 或固定字段位宽跨 Release 译码。
- DCI 解码成功后立即声称获得用户业务内容；上层加密和 MAC/RLC 解析仍是独立边界。

## 14. 与相似概念的区别

| 概念 | 主要内容 | 与 DCI 的区别 |
|---|---|---|
| PDCCH | 物理控制信道和 RE | DCI 的承载，不是比特字段 |
| RNTI | CRC 掩码/控制上下文 | 参与 DCI 判决，不是 DCI payload |
| MAC CE | MAC 层控制元素 | 可能出现在 PDSCH/UL-SCH，不等同 DCI |
| RRC 配置 | 半静态资源/过程配置 | 提供解释 DCI 所需上下文 |
| PDSCH/PUSCH | 数据物理信道 | 通常由 DCI 调度 |

## 15. 代码实现注意事项

- 为每个候选保留 $format、A、K、N、E、rnti_{hypothesis}、crc_{state}$ 和字段解析日志。
- 将比特位序、端序、CRC 掩码和字段偏移写成显式表，并为每种 DCI 格式单独测试。
- 把字段解析和资源生成分成两个函数，资源生成输入必须包含 BWP、载波和时序上下文。
- $crc_{pass}$ 只升级到 $valid_{dci}$ 的必要条件之一；记录拒绝原因。
- DCI 到 PDSCH/PUSCH 的快照应不可变，供译码支路和定位支路共享，避免后续默认值覆盖。
- 发生配置版本或 BWP 切换时使旧 DCI 解释缓存失效。

## 16. 待实验验证的问题

- [ ] 对每种目标 DCI 格式做无噪声编码-映射-译码闭环，逐项比对 payload 和 K/N/E。
- [ ] 使用正确/错误 RNTI、正确/错误候选和字段扰动，确认 CRC 与字段状态可分离。
- [ ] 从有效 DCI 生成 PDSCH/PUSCH resource_snapshot，核对 PRB、符号、MCS、RV、HARQ 和 DM-RS。
- [ ] 在 AWGN/CFO/多径下分别记录 DCI BLER、误检、字段错误和资源命中率。
- [ ] 将 DCI 资源快照接入 [[04-PDSCH/PDSCH|PDSCH]] 与定位支路，验证两条支路使用同一时间基准。

## 17. DCI 格式族与控制用途

被动接收端应先定义“要尝试的格式集合”，再开始 Polar/CRC 循环。以下是项目最常见的格式分层；表格只表达方向和配置语境，具体字段、长度和适用 RNTI 必须按目标 Release 与 RRC/MAC 状态核验：

| 格式 | 控制方向/用途 | 常见上下文 | 解析重点 | 状态 |
|---|---|---|---|---|
| `0_0` | 基础上行授权 | CSS 或回退/基础 USS | PUSCH 时频资源、MCS、HARQ、TPC 等 | `STANDARD + partial` |
| `0_1` | 配置化上行授权 | UE-specific、较丰富的 UL 配置 | BWP、资源分配、跳频/层和 UCI 相关字段 | `STANDARD + partial` |
| `1_0` | 基础下行分配 | CSS 或回退/基础 USS | PDSCH 时频资源、MCS、HARQ、PUCCH 反馈时序 | `STANDARD + partial` |
| `1_1` | 配置化下行分配 | UE-specific、较丰富的 DL 配置 | BWP、资源分配、层/端口、DM-RS、反馈时序 | `STANDARD + partial` |
| `2_0` 等 | 公共控制/组控制 | 由配置启用的特定过程 | 时隙格式、抢占/TPC 等过程字段 | `NEEDS_EXTERNAL_REFERENCE` |

`0_x`/`1_x` 的数字不是“上下行物理信道编号”，而是 DCI payload 的字段布局选择。不能只凭 payload 长度猜格式；同长度分支必须结合 Search Space、RNTI、方向和字段合法性共同消歧。

## 18. 字段分组：先解析语义，再生成资源

DCI 字段应按作用分组保存，字段解析函数不应直接修改全局资源网格：

| 字段组 | 典型内容 | 生成的中间结果 |
|---|---|---|
| 格式/上下文 | format identifier、RNTI、BWP 语境 | `format_context` |
| 频域分配 | 资源分配类型、RIV/位图/跳频相关字段 | `frequency_allocation` |
| 时域分配 | TDRA index、起止符号、K0 或等效偏移 | `time_allocation` |
| 传输参数 | MCS、NDI、RV、HARQ process | `coding_snapshot` |
| 空间/参考 | 层数、天线端口、DM-RS/PTRS 相关字段 | `reference_snapshot` |
| 反馈/功控 | PUCCH 资源、PDSCH-to-HARQ timing、TPC | `feedback_context` |
| 过程控制 | SRS、抢占、时隙格式等（若启用） | `procedure_context` |

字段是否存在、位宽和解释依赖 BWP、RRC 配置和 DCI format。解析器应输出 `missing_fields`，而不是把不存在的字段填成零。

## 19. 比特、CRC、Polar 与 PDCCH 的边界

完整发送链可以拆成四个可独立复核的边界：

```text
DCI payload A
  -> CRC append / RNTI mask (K)
  -> Polar construction (N)
  -> rate matching to PDCCH E
  -> scrambling + QPSK + CCE/REG/RE mapping
```

接收端必须沿逆序恢复，并在每个边界保存长度和坐标：

$$
A\rightarrow K\rightarrow N\rightarrow E\rightarrow
\mathrm{LLR}_{physical}\rightarrow\hat{A}.
$$

RNTI 掩码属于 CRC 判决上下文，不等同于 PDCCH 物理层的比特扰码；两者的作用位置、输入长度和位序都要在实现中分开命名。具体 CRC 长度、Polar 构造、输入交织和率匹配规则由 TS 38.212 目标版本确定。

在常见 NR DCI 基线中，控制 payload 会附加 24-bit CRC，因此常见长度记账可写成 `K=A+24`；这只是版本化实现的核验线索。CRC 长度、掩码覆盖范围、位序和是否存在额外输入处理必须从目标 TS 38.212 条款确认，不能把 `24` 当成所有未来分支的无条件常量。

## 20. 位序和字段偏移账本

为每一种 DCI format 维护一张不可变字段表：

```js
dci_layout:
  format: ""
  release: "unknown"
  payload_length: null
  fields:
    - name: ""
      start_bit: null
      width: null
      direction: "DL|UL|common"
      interpretation: ""
      source: "RRC|DCI|derived"
  bit_order: "unknown"
  crc_order: "unknown"
  verified: false
```

字段表同时服务于编码器、译码器和资源快照生成器。不要在多个函数中手写相同的偏移；否则一个字段增删会让 CRC 仍通过但资源整体错位。

## 21. 时域字段的双时刻记录

DCI 的控制时刻和被调度数据时刻必须分开：

```js
time_context:
  control_frame: null
  control_slot: null
  control_symbols: []
  data_frame: null
  data_slot: null
  data_symbols: []
  slot_offset: null
  feedback_slot: null
  timing_rule: "K0/K1/or_other/unknown"
  timing_verified: false
```

`K0`、`K1` 或其他等效时序字段不是“固定延迟样点数”。它们要结合 numerology、时隙格式、TDD 方向和配置解释。若无法将 DCI 映射到唯一数据 slot，保留 `timing_ambiguous`，不要把控制 slot 复制到数据 slot。

## 22. 频域字段到 PRB 的转换

频域解析应分成“位字段解码”和“坐标变换”两步：

```text
DCI frequency bits
  -> allocation_type / RIV / bitmap interpretation
  -> BWP-local PRB set
  -> carrier-relative PRB set
  -> absolute subcarrier/RE mask
```

统一输出：

| 字段 | 说明 |
|---|---|
| `allocation_type` | 目标 Release/RRC 允许的资源分配分支 |
| `bwp_prb_start/size` | 解释位字段的 BWP 上下文 |
| `prb_indices_local` | BWP 内 PRB 集合 |
| `prb_indices_absolute` | 载波坐标下的 PRB 集合 |
| `symbol_indices` | 数据符号和 DM-RS/PTRS 排除后的集合 |
| `coordinate_transform_version` | Point A、SCS、FFT 解释版本 |

RIV/位图的具体公式、资源分配类型和频域跳变规则属于 `NEEDS_EXTERNAL_REFERENCE`。资源生成器必须拒绝 BWP 尺寸缺失或超界的 DCI，而不是截断到可用 PRB。

## 23. 从 DCI 到两个快照

DCI 解析完成后分别构造资源和编码快照，便于定位“资源正确但译码失败”与“编码正确但资源错位”：

```js
resource_snapshot:
  event_id: ""
  direction: "DL|UL|unknown"
  control_slot: ""
  data_slot: ""
  bwp_id: null
  prb_local: []
  prb_absolute: []
  symbols: []
  dmrs: {}
  ptrs: {}
  layers: null
  ports: []
  state: "complete|partial|rejected"
coding_snapshot:
  dci_format: ""
  mcs: null
  modulation_order: null
  target_code_rate: null
  tbs: null
  ndi: null
  rv: null
  harq_process: null
  E: null
  state: "complete|partial|rejected"
```

两份快照共享 `event_id`、`config_id` 和 RNTI 上下文，但各自保留来源字段。PDSCH/PUSCH 译码器和定位提取器都应消费快照，不应重新从裸 payload 猜资源。

## 24. 格式歧义与多命中消解

同一候选可能在多个 DCI format/RNTI 假设下出现 CRC 通过。建议使用分层评分而不是“最后一次通过覆盖前一次”：

$$
S(h,f,r)=w_{crc}I_{crc}+w_{format}I_{format}
 +w_{field}I_{field}+w_{resource}I_{resource}
 +w_{temporal}I_{temporal}+w_{history}I_{history}.
$$

权重和阈值是项目策略，不是标准事实；未有真值时不应把分数解释为概率。记录全部命中：

| 情况 | 状态 | 处理 |
|---|---|---|
| 一个候选/一个格式/一个 RNTI 通过 | `valid_dci_candidate` | 进入快照生成，等待关联证据 |
| 同候选多格式通过 | `format_ambiguous` | 保留所有 payload/快照分支，等待后续资源或时序证据 |
| 多候选同 RNTI 通过 | `candidate_collision` | 按 Search Space 和资源冲突消歧，不覆盖原记录 |
| CRC 通过但字段越界 | `field_invalid` | 作为负例统计 |
| 只有错误 RNTI 通过 | `rnti_suspect` | 检查掩码位序、候选资源和 RNTI 生命周期 |

## 25. 解析器伪代码

```python
parse_dci(llr, candidate, config, rnti_contexts, format_set):
    results = []
    for fmt in format_set:
        layout = load_layout(fmt, config.release)
        if not layout.verified and config.require_verified_layout:
            results.append(rejected(fmt, reason=layout_unknown))
            continue
        decoded = polar_inverse(llr, layout, candidate.aggregation_level)
        for rnti in applicable_rntis(fmt, rnti_contexts, candidate.search_space):
            crc = check_crc_mask(decoded, rnti)
            if not crc.pass:
                results.append(crc_fail(fmt, rnti))
                continue
            fields = parse_fields(decoded.payload, layout)
            if not fields.in_range:
                results.append(field_invalid(fmt, rnti, fields.errors))
                continue
            snapshot = derive_resource_and_coding(fields, config)
            if not snapshot.resource_valid:
                results.append(resource_invalid(fmt, rnti, snapshot.missing_fields))
                continue
            results.append(valid_dci(fmt, rnti, snapshot))
    return retain_all_results(results)
```

伪代码只定义阶段顺序；`polar_inverse`、CRC 掩码、字段布局和资源公式必须由目标标准/工具箱实现验证。

## 26. 定位支路如何使用 DCI

定位支路只消费 DCI 提供的约束，不把 DCI 当作测距样本：

1. 用 DCI 的方向、数据 slot、PRB、符号和 DM-RS 配置限定目标 UE 资源窗口。
2. 用 [[04-PDSCH/PDSCH|PDSCH]]/PUSCH 资源快照建立单用户掩码；保留邻 UE、控制和保留 RE 的排除记录。
3. 对上行 PUSCH/DM-RS/SRS 或项目明确的参考片段计算 ToA/RToA；PDCCH DM-RS 只作为下行控制质量/同步辅助。
4. 将 `event_id`、RNTI 证据状态、采样起点和校准 ID 传给 [[05-定位观测量/Timing Observation|Timing Observation]]。

如果 DCI 只能解析出方向而不能解析出资源，定位支路状态应为 `resource_pending`，不能输出看似精确的 UE ToA。

## 27. DCI 核验矩阵

| 测试 | 正例/扰动 | 必须比较 |
|---|---|---|
| 编码闭环 | 已知 payload、RNTI、format | A/K/N/E、CRC、payload 位序 |
| 候选闭环 | 已知 CCE/REG/RE | LLR 顺序、候选位置和 format |
| 掩码测试 | 正确/错误 RNTI | CRC 状态和拒绝原因 |
| 字段测试 | 每字段边界/保留值 | `field_valid`、错误名和资源结果 |
| 时序测试 | 改 K0/K1/TDRA | control/data/feedback slot 变化 |
| 频域测试 | 改 BWP/位图/RIV | 局部/绝对 PRB 和越界状态 |
| 多命中测试 | 多格式/多候选 | 不覆盖、可回放的歧义记录 |
| 定位桥接 | 有效 DCI + 上行参考 | event_id、时间基准和资源掩码一致 |

## 28. Rel-17 V17.8.0 DCI 编码核验基线

以下条目已对照 [ETSI TS 138 212 V17.8.0 (Release 17)](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.08.00_60/ts_138212v170800p.pdf) §7.3-§7.3.4（访问日期 2026-09-05）。它是用于实现对照的参考版本，不等于项目现场 Release：

| 条目 | V17.8.0 事实 | 实现约束 |
|---|---|---|
| DCI 编码步骤 | 信息复用 -> CRC attachment -> channel coding -> rate matching | 四个边界分别记录中间向量 |
| DCI 格式 | `0_0/0_1/0_2` 调度 PUSCH，`1_0/1_1/1_2` 调度 PDSCH，`2_0`-`2_7` 为其他公共控制，另有 sidelink/MBS 分支 | 格式集合必须由 Search Space/配置筛选 |
| 字段映射 | 按格式描述出现顺序映射到 `a_0...a_{A-1}`；每字段的最高位先映射到该字段的最低序号 | `field_offset` 表必须集中维护 |
| 最小 payload | 信息位少于 12 bit 时补零到 12 bit | 不能用短 payload 直接构造 Polar |
| DCI 尺寸 | 由被调度小区的 active BWP 配置决定，并按 §7.3.1.0 做尺寸对齐 | 不能用一个带宽的长度跨 BWP 复用 |
| 尺寸上限 | 终端期望每小区最多 4 种 DCI size，其中含 C-RNTI 的最多 3 种 | 候选预算要按实际尺寸集合统计 |

### 28.1 CRC 与 RNTI 掩码的精确边界

V17.8.0 §7.3.2 对整个 DCI payload 计算 CRC，采用 24-bit `CRC24C`，因此：

$$
K=A+L,\qquad L=24.
$$

CRC parity 不是把 16-bit RNTI 整数直接 XOR 到整个向量。规范定义 RNTI 的 16 个比特（`x_{rnti,0}` 对应 RNTI 的 MSB）只参与 CRC parity 的后 16 个位置：

$$
c_k=b_k,\quad 0\le k\le A+7,
$$

$$
c_k=\left(b_k+x_{rnti,k-A-8}\right)\bmod 2,
\quad A+8\le k\le A+23.
$$

这一区别必须在实现中单独测试：`payload -> CRC24C -> RNTI parity mask`，不能与 PDCCH 物理比特扰码共用一个函数。目标 Release 或非 unicast 分支若改变 RNTI/CRC 语境，应新建布局记录。

### 28.2 Polar 与率匹配参数

在该参考版本的 DCI 分支中，38.212 指定使用 Polar channel coding，并给出 DCI 专用构造参数（包括 `n_max=9`、输入交织开关和 parity-check 相关参数）以及 `I_BIL=0` 的率匹配分支。实现应把这些参数随 `dci_format`/`release` 写入 `coding_snapshot`，而不是从 PDSCH Polar/LDPC 配置继承。

## 29. 尺寸对齐与格式消歧的工程含义

DCI size alignment 会通过补零或截断频域资源分配字段，使某些 format 在同一 Search Space 或不同 Search Space 中具有可比较的 payload size。因而：

1. 盲译码外层要先生成“对齐后的格式布局”，再计算 `A/K/N/E`。
2. 看到相同长度不能直接判定格式相同；还要结合 Search Space、RNTI、候选位置和字段语义。
3. 更换 active BWP、SUL/NUL、RB set 或 DCI 版本时，必须重新计算尺寸并使旧 layout 缓存失效。
4. 统计候选复杂度时按**不同 DCI size**和格式分支计数，不能只按四个名字计数。

## 30. 38.214 调度字段路由

对照 [ETSI TS 138 214 V17.8.0 (Release 17)](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/17.08.00_60/ts_138214v170800p.pdf)（访问日期 2026-09-05），DCI 字段到数据快照的主要路由如下：

| DCI 方向 | 38.214 入口 | 需要生成的快照字段 |
|---|---|---|
| DL assignment | §5.1.2.1 时域资源、§5.1.2.2 频域资源 | PDSCH slot、起止符号、PRB/RBG、资源分配类型 |
| DL 传输参数 | §5.1.3 调制阶数/目标码率/RV、§5.1.3.2 TBS | `mcs`、`Q_m`、目标码率、TBS、RV |
| DL 物理映射 | §5.1.4 PDSCH resource mapping、§5.1.6.2 DM-RS | 数据/DM-RS/PTRS 掩码、层/端口/QCL |
| UL grant | §6.1.2.1 时域资源、§6.1.2.2 频域资源 | PUSCH slot、起止符号、PRB/RBG、跳频/资源类型 |
| UL 传输参数 | §6.1.4.1 调制/目标码率、§6.1.4.2 TBS | `mcs`、`Q_m`、TBS、RV、HARQ/UL-SUL 语境 |
| UL 参考/定位 | §6.2.1 sounding、§6.2.2 DM-RS | SRS/PUSCH-DM-RS 资源、端口和时间参考 |

这些章节是“字段解释的责任入口”，不是把 `RIV`、TDRA 表或 TBS 公式从一个版本复制到所有网络。资源生成器应将 `spec_version`、配置快照和缺失字段一起写入 `resource_snapshot`；任何跨 BWP、SUL/NUL、RB set 或 Release 的差异都要重新计算。

## 31. 证据与当前状态

- `STANDARD + verified-reference`：本地 TS 38.212/38.213/38.214 摘要，以及上面的 ETSI TS 138 212/214 V17.8.0 §7.3/数据过程参考版本。
- `PERSONAL_NOTE`：本页的格式分层、字段账本、双时刻快照和多命中策略。
- `NEEDS_EXTERNAL_REFERENCE`：当前项目 Release 的完整字段位宽/顺序、RIV/TDRA/K0/K1 规则、非 unicast 分支和工具箱签名；参考版本之外的扩展仍需核验。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚无真实 DCI payload、资源真值或跨站定位结果。

## 32. Related Notes

- [[03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[03-PDCCH/CORESET|CORESET]]
- [[03-PDCCH/Search Space|Search Space]]
- [[03-PDCCH/CCE REG|CCE REG]]
- [[03-PDCCH/RNTI|RNTI]]
- [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
- [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]
- [[04-PDSCH/PDSCH|PDSCH]]
- [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]
- [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]
- [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]]
- [[05-定位观测量/Timing Observation|Timing Observation]]
