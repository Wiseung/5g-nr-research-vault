---
title: PDSCH
aliases:
  - Physical Downlink Shared Channel
  - NR 下行共享信道
type: atomic
status: partial
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - channel/pdsch
  - stage/ue-extraction
source:
  - "[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]"
  - "[[01-专题知识/信道估计与均衡/DM-RS]]"
  - "[[01-专题知识/信道估计与均衡/PTRS]]"
  - 3GPP TS 38.211
  - 3GPP TS 38.214
  - "[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.212｜Multiplexing and channel coding]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[5G-NR-Positioning/03-PDCCH/PDCCH Implementation Contract]]"
  - "[[01-专题知识/信道编译码/NR编码链/NR-DL-SCH 编码链]]"
related:
  - "[[03-PDCCH/DCI]]"
  - "[[03-PDCCH/PDCCH Blind Decoding]]"
  - "[[01-专题知识/信道估计与均衡/DM-RS]]"
  - "[[01-专题知识/信道估计与均衡/LS 信道估计]]"
  - "[[01-专题知识/信道估计与均衡/MMSE 均衡]]"
  - "[[01-专题知识/信道估计与均衡/PTRS]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[04-PDSCH/UE Resource Extraction|UE Resource Extraction]]"
---

# PDSCH

> [!abstract] 本页结论与证据边界
> PDSCH 的“可见位置”来自已接受的 DCI 与配置快照，PDSCH 的“可译码性”还取决于 DM-RS、层/端口、调制、LDPC/率匹配和 LLR 约定。下文把这些依赖拆成可回放的中间状态；没有项目 Release、RRC 配置或真实 IQ 时，精确表值、API 行为和性能数字仍保持 `NEEDS_EXTERNAL_REFERENCE` 或 `NEEDS_VERIFICATION`。

## 1. 一句话定义

PDSCH 是承载下行共享数据（通常对应 DL-SCH）的物理信道；在被动接收机中，必须由合法 DCI、BWP 和参考信号配置共同确定其资源，不能只凭能量峰值命名为目标 UE。

## 2. 为什么项目需要它

第二阶段需要从 DCI 得到目标 UE 的下行资源与编码上下文，用于验证调度关联、提取单用户资源，并为后续上行/下行时间观测建立可重复的时频坐标。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 `PDCCH/DCI 调度` 之后、`DM-RS 信道估计/均衡/译码` 之前；项目链路为 [[03-PDCCH/DCI]] -> PDSCH -> UE 资源提取 -> [[05-定位观测量/Timing Observation]]。

## 4. 输入

- 已接受的 DCI（格式、RNTI、频域/时域资源、MCS、RV、层数等）。
- carrier/BWP/point A、numerology、TDD 方向和时隙上下文。
- PDSCH DM-RS/PTRS 配置、接收 IQ 和采样时间轴。

## 5. 输出

- PDSCH 数据 RE、DM-RS RE、层/端口和符号映射。
- `resource_snapshot` 与 `coding_snapshot`。
- 可选的解调 LLR、DL-SCH/TB-CRC 状态和单用户资源掩码。

## 6. 关键参数

PRB 集合、起止 OFDM 符号、BWP、调制阶数、MCS/TBS、RV、层数、DM-RS 类型/位置、PTRS、RNTI、HARQ 进程、采样率和 FFT 归一化。任何缺失字段都记录 `unknown`，不用 0 代替。

## 7. 时域位置

由 DCI 时域分配和当前 slot/symbol 上下文确定；需与 [[01-NR基础/NR Frame Slot]]、[[01-NR基础/NR TDD]] 的坐标一致。具体表格/映射随 Release 和配置变化，标记 `NEEDS_EXTERNAL_REFERENCE`。

## 8. 频域位置

由 BWP、PRB/VRB 映射、Point A 和载波栅格确定。保存 BWP 内局部索引与载波绝对子载波索引，避免把局部数组下标误当成射频频点。

## 9. 数学原理

在已知 DM-RS 资源 $(k_p,l_p)$ 上，接收模型可写为：

$$
Y[k_p,l_p]=H_{\mathrm{eff}}[k_p,l_p]X_{\mathrm{DMRS}}[k_p,l_p]+N[k_p,l_p].
$$

逐 RE LS 基线为 $\hat H=Y/X_{\mathrm{DMRS}}$；再将估计插值到数据 RE，均衡后软解调、逆率匹配和 LDPC 译码。实际端口/层/预编码维度必须由配置确定。

## 10. 3GPP 对应规范

- TS 38.211：PDSCH 调制、层映射、资源元素映射和 DM-RS/PTRS 接口；精确子条款按项目 Release 核对（`NEEDS_EXTERNAL_REFERENCE`）。
- TS 38.214：PDSCH 资源分配、MCS/TBS、时域/频域调度和 HARQ；精确表格按 Release 核对（`NEEDS_EXTERNAL_REFERENCE`）。
- TS 38.212：DL-SCH CRC、码块分段、LDPC 和率匹配；详见 [[01-专题知识/信道编译码/NR编码链/NR-DL-SCH 编码链]]。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

官方 API 线索包括 `nrPDSCHIndices`、`nrPDSCHDMRSIndices`、`nrPDSCHDMRS`、`nrPDSCHDecode`、`nrExtractResources`、`nrChannelEstimate`、`nrEqualizeMMSE` 和 `nrDLSCHDecoder`。函数签名、Release、输入维度和对象属性必须在本机核验，当前状态为 `NEEDS_EXTERNAL_REFERENCE`。

## 12. 本项目中的用途

PDCCH 通过后，将 DCI 转成 PDSCH/PUSCH 资源快照；PDSCH 侧用于验证 C-RNTI 关联、构造时频掩码和分离控制/数据能量。定位支路可只使用可靠参考序列/资源，不必把上层加密数据当作可读明文。

## 13. 常见误区

- 把任意下行能量或 PBCH/PDCCH 误标为 PDSCH。
- 只用 DCI 的一个字段而忽略 BWP、DM-RS、层数和 TDD 时序。
- 把 PDSCH 解码失败归因于 PRACH；控制、资源、信道估计和 LDPC 应分层记录。
- 认为 PDSCH 明文可见就等于高层业务内容可见。

## 14. 与相似概念的区别

- PDSCH 是物理信道；DL-SCH 是其主要传输信道承载。
- PDCCH 承载 DCI，告诉接收机如何找 PDSCH；二者不能互换。
- DM-RS 是解调参考信号，不是 PDSCH 数据 RE。
- PUSCH 是上行共享信道，方向和调度来源不同。

## 15. 代码实现注意事项

先冻结并记录配置快照，再生成索引；保持 BWP/载波/端口/层维度显式；对资源掩码做覆盖、互斥和顺序单元测试；滤波或时域截断后的群时延必须写入定位测量账本。

## 16. 待实验验证的问题

- 无噪声单位信道下，发送/接收 DM-RS 索引和 LS 输出是否逐 RE 一致。
- 正确/错误 DCI、RNTI、DM-RS 配置下的资源命中率和 TB-CRC 状态。
- 单用户掩码在邻近用户、频偏、多径和 TDD 灵活符号下的残余泄漏。
- `nrPDSCHDecode` 等 API 在项目 MATLAB Release 的实际输入维度。

## 17. Related Notes

- [[03-PDCCH/DCI]]
- [[03-PDCCH/PDCCH Blind Decoding]]
- [[01-专题知识/信道估计与均衡/DM-RS]]
- [[01-专题知识/信道估计与均衡/03 信道估计基础|Channel Estimation]]
- [[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡|Equalization]]
- [[04-PDSCH/UE Resource Extraction|UE Signal Extraction]]
- [[01-专题知识/信道估计与均衡/二维时频插值]]
- [[01-专题知识/信道估计与均衡/MMSE 均衡]]
- [[05-定位观测量/Timing Observation]]
- [[01-专题知识/5G定位/单用户时频截取与定位观测量]]

## 证据与状态

- `PERSONAL_NOTE`：与现有 PDCCH/PDSCH 和 DM-RS 笔记的接口整理。
- `STANDARD + partial`：规范职责和术语；精确版本/表格待核对。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚未接入本项目真实 IQ/代码。

## 18. 端到端所有权图

PDSCH 不应被实现成一个“从 IQ 直接输出明文”的黑盒。每一段输入由不同层负责，接收机要保留中间结果和失败原因：

```text
RRC/SIB/MAC 配置 + DCI
          |
          v
  data-slot / BWP / PRB / symbol
          |
          v
  RE 分类：data / DM-RS / PTRS / reserved / control
          |
          v
  DM-RS 信道估计 -> 层/端口域均衡 -> 软解调 LLR
          |
          v
  解扰 -> 逆率匹配 -> LDPC -> CB-CRC/TB-CRC
          |
          +--> resource_snapshot / coding_snapshot
          |
          +--> UE 资源掩码 -> 单用户观测 -> ToA/TDoA（需另行校准）
```

这里的箭头是接口而不是结论。任何一个阶段缺少配置时，后续输出都应降级为 `partial`，不能用最终 CRC 或相关峰反推缺失的资源字段。

## 19. 输入、输出与证据分层

### 19.1 输入契约

| 输入组 | 最少字段 | 缺失时的处理 |
|---|---|---|
| 控制上下文 | `event_id`、`candidate_id`、RNTI 类型/值、DCI 格式、CRC/字段状态 | 不生成 `valid_dci` |
| 载波与时序 | Release/版本、SCS、frame/slot、BWP、Point A、TDD 方向 | 保留 `unknown`，不采用默认值 |
| 资源分配 | 局部/绝对 PRB、起止 symbol、映射版本 | `resource_snapshot.state=partial` |
| 参考信号 | DM-RS/PTRS 配置、端口/层、序列引用 | 不能宣称可均衡 |
| 波形接收 | IQ、采样率、FFT/CP、捕获起点、噪声估计 | 只能输出索引，不能输出可靠 ToA |

### 19.2 输出契约

输出至少分成四类：

1. **资源事实**：有序 RE/样点索引、数据和非数据掩码。
2. **编码状态**：`A/B/C/K'/F/N/E/E_r`、MCS、RV、HARQ 与 CRC 状态。
3. **观测质量**：DM-RS 相关/估计质量、噪声方差、均衡后 SINR、LLR 摘要。
4. **关联结论**：`candidate_only`、`associated`、`rejected`，以及支持该结论的事件列表。

`decoded_payload` 只有在 TB-CRC 通过且载荷权限/安全边界允许时才可交付上层；物理层恢复出的比特不等于可读的高层业务明文。

## 20. `resource_snapshot`：回答“在哪里”

下面的结构是项目实现契约，不是某个 Release 的完整 ASN.1 或 DCI 定义。数组保持有序，单位和坐标域必须与快照一起保存。

```js
resource_snapshot:
  snapshot_id: ""
  event_id: ""
  candidate_id: ""
  config_id: ""
  release_or_spec_version: "unknown"
  direction: "DL|unknown"
  control_time:
    frame: null
    slot: null
    symbol: null
  data_time:
    frame: null
    slot: null
    symbols: []
    scheduling_offset: null
  carrier:
    ncellid: null
    scs_hz: null
    point_a: null
    absolute_subcarrier_origin: null
  bwp:
    id: null
    start_prb: null
    size_prb: null
    numerology: null
  frequency:
    prb_indices_local: []
    prb_indices_absolute: []
    vrb_to_prb_mapping: "unknown"
  re_sets:
    data: []
    dmrs: []
    ptrs: []
    reserved: []
    control_or_other: []
  spatial:
    antenna_count: null
    port_count: null
    layer_count: null
    port_to_layer_map_ref: ""
    precoder_ref: ""
  mapping_version: ""
  state: "complete|partial|rejected"
  missing_fields: []
  source_refs: []
```

`prb_indices_local` 只在 BWP 内解释，`prb_indices_absolute` 才能与载波级频率轴或跨站记录对齐。两者不一致时应报 `coordinate_mismatch`，不能通过加一个经验偏移修复。

## 21. `coding_snapshot`：回答“用什么方式发送”

```js
coding_snapshot:
  snapshot_id: ""
  event_id: ""
  config_id: ""
  transport_channel: "DL-SCH|unknown"
  physical_channel: "PDSCH"
  mcs:
    index: null
    modulation_order_Qm: null
    target_code_rate: null
  transport_block:
    payload_bits_A: null
    tb_crc_length: null
    tbs_bits: null
  ldpc:
    codeblock_count_C: null
    codeblock_input_K_prime: null
    filler_bits_F: null
    base_graph: "unknown"
    lifting_size_Z: null
    mother_length_N: null
  rate_matching:
    total_E: null
    per_codeblock_Er: []
    rv: null
    interleaver_ref: ""
  harq:
    process_id: null
    ndi: null
    retransmission_index: null
    soft_buffer_ref: ""
  llr:
    sign_convention: "unknown"
    scale_or_noise_variance: null
    coordinate_ref: ""
  state: "not_attempted|llr_ready|decoded|tb_crc_pass|tb_crc_fail|invalid"
  missing_fields: []
```

资源快照与编码快照必须共享 `event_id`、`config_id` 和版本引用。只填 `mcs_index` 而不填 `Q_m`、TBS、`E` 或层数，不能称为完整 `coding_snapshot`。

## 22. DCI 到 PDSCH 的解释顺序

为了避免把控制时刻、资源时刻和译码时刻混在一起，按下面顺序消费 DCI：

| 步骤 | 解释对象 | 产物 | 失败状态 |
|---:|---|---|---|
| 1 | PDCCH 候选的 `crc_state`、RNTI、格式 | `dci_record` | `crc_fail` / `field_invalid` |
| 2 | 控制所在 frame/slot 与调度偏移 | `data_time` | `timing_unknown` |
| 3 | BWP、Point A、频域分配与映射语义 | 局部/绝对 PRB | `coordinate_mismatch` |
| 4 | 起止 symbol、TDD 方向、保护/控制区域 | symbol 集合 | `direction_invalid` |
| 5 | DM-RS/PTRS、层/端口、预编码引用 | 参考/空间掩码 | `reference_config_missing` |
| 6 | MCS、RV、NDI、HARQ 进程与 TBS 输入 | `coding_snapshot` | `coding_config_missing` |
| 7 | 资源和编码闭合检查 | `snapshot_state` | `snapshot_rejected` |

具体字段名称、位宽、表格和调度偏移依赖适用 Release 与 RRC 配置。它们在本页只作为接口槽位，状态为 `NEEDS_EXTERNAL_REFERENCE`，不能从字段名推断规范数值。

## 23. 坐标闭包：从 RE 到采样点

PDSCH 的坐标至少有五个域：

1. **协议域**：`event_id`、RNTI、DCI、HARQ。
2. **载波域**：Point A、绝对子载波、SCS、BWP。
3. **资源网格域**：`(k,l,p)`，其中 `k` 为频率坐标、`l` 为 OFDM 符号、`p` 为端口/逻辑空间端口。
4. **波形域**：FFT bin、CP、OFDM 符号起点和有效采样区间。
5. **设备域**：捕获起点、IQ 样点、数字下变频/抽取与时钟校准。

推荐显式保存以下映射，而不是把它们压成一个整数：

$$
k_{abs}=f_{BWP}(k_{local},\,\mathrm{PointA},\,\Delta f,\,\mathrm{mapping\_version}),
$$

$$
n_{sample}=\mathcal{W}(frame,slot,l,N_{FFT},N_{CP},F_s,\,t_{capture}),
$$

其中 `f_BWP` 和 `W` 是带版本的映射函数。第一式只表达坐标依赖，第二式只表达“由波形配置产生样点窗口”；它们不授权在未知配置时套用固定 FFT 或 CP 数值。

每次映射应检查：

- 局部索引在 BWP/载波范围内；
- symbol 属于被调度的 DL 方向；
- 样点窗口不越过捕获边界；
- 发送/接收两端采用同一 0-based/1-based 约定；
- 时频映射版本与 `config_id` 一致。

## 24. RE 分类与数据预算

在同一物理资源域内，先建立互斥集合，再做数量计算：

$$
\mathcal{R}_{occupied}
=\mathcal{R}_{data}\dot\cup
\mathcal{R}_{DMRS}\dot\cup
\mathcal{R}_{PTRS}\dot\cup
\mathcal{R}_{reserved}\dot\cup
\mathcal{R}_{control/other}.
$$

若两个集合交集非空，优先报告 `resource_overlap`；不要让后写入的符号静默覆盖前一类资源。用于数量级审计的近似关系为：

$$
N_{RE,data}
=N_{RE,total}-N_{RE,DMRS}-N_{RE,PTRS}-N_{RE,reserved}-N_{RE,control/other},
$$

$$
E_{ideal}\approx N_{RE,data}Q_mN_{layers}.
$$

这两个式子是个人实现的记账检查，不是 TBS 或率匹配规则的替代。实际 `E` 还受层映射、码块分配、资源粒度、UCI/其他复用和适用 Release 规则影响；因此日志同时保存“审计近似值”和“标准/实现计算值”。两者偏差应有解释字段，而不是直接取较小者。

## 25. DM-RS、PTRS 与 CSI-RS 的边界

| 信号/资源 | 在 PDSCH 接收中的角色 | 可推出的结论 | 不可推出的结论 |
|---|---|---|---|
| DM-RS | 当前传输的解调信道观测 | 估计与当前数据时频/空间域相容的 `H_eff` | 不能单独确认高层 UE 身份 |
| PTRS | 相位噪声/公共相位误差跟踪接口 | 修正相位相关残差（若配置和算法可用） | 不能替代完整 DM-RS 信道估计 |
| CSI-RS | CSI 测量、反馈或波束管理 | 可形成带时间戳的测量输入 | 不能默认当作当前 PDSCH DM-RS |
| PDSCH 数据 RE | 软解调/译码输入 | 形成 LLR 和 TB-CRC 候选 | 能量峰不等于目标 UE 关联 |

DM-RS 估计的最小模型为：

$$
Y[k_p,l_p,p]
=H_{eff}[k_p,l_p,p]X_{DMRS}[k_p,l_p,p]+N[k_p,l_p,p],
$$

$$
\widehat H_{LS}[k_p,l_p,p]
=\frac{Y[k_p,l_p,p]}{X_{DMRS}[k_p,l_p,p]},
\qquad X_{DMRS}\ne0.
$$

随后才可把参考 RE 的估计按明确的时间/频率假设插值到数据 RE。插值不能修复错误的端口、序列初始化、预编码或资源掩码；这些错误应在 `reference_config_missing` 或 `channel_domain_mismatch` 中暴露。

## 26. 层、端口、天线与等效信道

PDSCH 解调时至少要区分四种空间对象：

| 对象 | 解释 | 典型错误 |
|---|---|---|
| 物理天线 | 射频接收/发送链路 | 与端口数量直接相等 |
| 端口 | 参考信号和物理映射使用的逻辑端口 | 当成用户或层 |
| 层（layer） | 传输块被映射到的空间流 | 当成天线或 PRB 数 |
| 等效层信道 | 叠加预编码后的数据域信道 | 用传播信道直接均衡 |

一个便于核对的抽象模型是：

$$
\mathbf y[k,l]
=\mathbf H_{prop}[k,l]\mathbf W[k,l]\mathbf s[k,l]+\mathbf n[k,l],
\qquad
\mathbf H_{eff}=\mathbf H_{prop}\mathbf W.
$$

DM-RS 估计究竟落在物理天线域、端口域还是层域，取决于参考信号、预编码和实现接口。发送端与接收端必须记录同一个 `channel_domain`，不能只用最终 BLER 判断空间映射是否正确。

若使用线性均衡器，建议记录矩阵维度和条件数，而不是在代码中隐式转置：

$$
\widehat{\mathbf s}=\mathbf G\mathbf y,
\qquad
\mathbf G\mathbf H_{eff}\approx\mathbf I.
$$

MMSE 形式可作为实现参考：

$$
\mathbf G_{MMSE}
=\left(\mathbf H_{eff}^{H}\mathbf R_n^{-1}\mathbf H_{eff}+\mathbf I\right)^{-1}
\mathbf H_{eff}^{H}\mathbf R_n^{-1}.
$$

这里的矩阵式是条件化的理论接口；`R_n`、端口顺序、层顺序和归一化必须在实际配置中核验。工程实现优先使用线性方程求解或分解，避免不必要的显式求逆。

## 27. DL-SCH 到 PDSCH 的长度闭包

PDSCH 的数据比特通常来自 DL-SCH。接收端应保存以下长度边界：

```text
TB payload A
    -> TB-CRC B
    -> code-block segmentation C, K', F
    -> LDPC base graph / lifting Z / mother code N
    -> rate matching per-codeblock E_r with RV
    -> concatenated E bits
    -> scrambling / modulation / PDSCH RE mapping
```

个人记账可写为：

$$
B=A+L_{TB},
$$

$$
B'=\begin{cases}
B+C L_{CB}, & \text{适用且附加 CB-CRC 时},\\
B, & C=1\text{ 且该流程不附加 CB-CRC 时},
\end{cases}
$$

$$
F=C K'-B',
\qquad
E=\sum_{r=0}^{C-1}E_r.
$$

这些关系用于检查长度守恒；具体分段阈值、基图、提升因子、filler 位置和 `E_r` 分配必须按适用版本的 TS 38.212/38.214 核对，状态为 `NEEDS_EXTERNAL_REFERENCE`。特别要避免把 `E` 当成 LDPC 母码长度 `N`，也不要把 `A`、TBS 和 `B` 在代码中复用为同一字段。

接收端的可逆边界应分别输出：

| 边界 | 输入 | 输出 | 必查项 |
|---|---|---|---|
| 物理到 LLR | 均衡符号、噪声估计 | 按数据 RE/层排列的 LLR | 符号、尺度、顺序 |
| LLR 到码块 | PDSCH LLR、`E` | 每个 `E_r` 的 LLR | 层联接、码块边界 |
| 逆率匹配 | `E_r`、RV | 母码坐标 LLR | 重复累加、打孔初始化 |
| LDPC/CRC | 母码 LLR | CB/TB 状态和载荷 | filler、CB-CRC、TB-CRC |

只比较最终 TB-CRC 无法定位资源、LLR、率匹配或译码哪一层出错。

## 28. HARQ、NDI 与软合并

PDSCH 的一次传输应绑定 `harq_process_id`、`ndi`、`rv` 和快照版本。建议用如下状态机记录每次尝试：

```text
new_data (NDI toggled or new process)
    |
    v
resource_checked -> llr_ready -> inverse_rate_matched
    |                                      |
    |                                      v
    |                              soft_buffer_updated
    |                                      |
    +------------------------------> LDPC_decode
                                           |
                         +-----------------+-----------------+
                         |                                   |
                    tb_crc_pass                         tb_crc_fail
                         |                                   |
                       ACK                         NACK -> next RV/retry
```

不同 RV 的观测必须先按各自率匹配索引还原到相同母码坐标，再合并软信息：

$$
\mathbf L_{mother}^{(t)}
=R_t^{-1}\left(\mathbf L_{physical}^{(t)}\right),
\qquad
\mathbf L_{HARQ}=\sum_t w_t\mathbf L_{mother}^{(t)}.
$$

当均衡增益、噪声方差或量化尺度不同，`w_t` 不能默认相同。不同 TBS、基图、`Z` 或码块划分不能直接共用旧软缓冲区；发生 `harq_context_mismatch` 时应丢弃或隔离该缓冲区，而不是继续累加。

记录至少包括：

- 初传/重传的 `rv`、`ndi`、资源和 MCS；
- 每次逆率匹配后的母码坐标摘要；
- 软合并前后的 LLR 范围、噪声标定和饱和值；
- CB-CRC、TB-CRC、ACK/NACK/DTX 以及失败原因。

## 29. PDSCH 与定位链路的关系

PDSCH 在本项目中首先是**资源和协议关联证据**，其次才是可选的下行观测源：

1. 由 PDCCH/DCI 确认目标 UE 的数据时频资源，生成可回放掩码。
2. 用 DM-RS/数据 RE 检查资源命中、信道质量和 C-RNTI 关联的一致性。
3. 将同一 `event_id` 的资源快照交给 [[04-PDSCH/UE Resource Extraction|UE Resource Extraction]]。
4. 只有在时间参考、滤波群时延和站间校准已知时，才把下行峰值作为辅助时间观测。
5. UE 几何定位优先使用多站接收的上行 PRACH、PUSCH DM-RS、SRS 或其他已知上行参考；固定站观测到的 PDSCH 下行时差本身描述的是下行发射源，不自动等于 UE 位置。

建议把定位输出与译码输出分开：

```js
pdsch_observation:
  event_id: ""
  resource_snapshot_id: ""
  reference_kind: "dmrs|ptrs|data|unknown"
  toa_raw_samples: null
  toa_raw_seconds: null
  calibration_state: "uncalibrated|partial|calibrated"
  peak_strategy: "first|strongest|cluster|unknown"
  snr_db: null
  residual_cfo_hz: null
  collision_flag: false
  mu_mimo_possible: false
  tdoa_usable: false
  state: "candidate|partial_observation|toa_unreliable|usable"
  failure_reason: ""
```

`tb_crc_pass` 不能自动把 `tdoa_usable` 置为 `true`；反之，可靠的参考峰也不能自动证明 PDSCH 载荷译码成功。

## 30. 接收机实现骨架

下面的伪代码只定义所有权和状态，不绑定某个工具箱 API：

```python
decode_pdsch(dci_record, config_snapshot, iq):
    require dci_record.crc_state == pass
    require dci_record.field_valid == true

    resource = build_resource_snapshot(dci_record, config_snapshot)
    if not resource.complete:
        return state=snapshot_rejected, reason=resource.missing_fields

    masks = classify_re(resource)
    if masks.overlap or masks.out_of_range:
        return state=resource_invalid, reason=masks.reason

    dmrs = extract_ordered(iq, masks.dmrs)
    h_eff, quality = estimate_channel(dmrs, resource.spatial)
    if not quality.usable:
        return state=dmrs_fail, quality=quality

    data = extract_ordered(iq, masks.data)
    equalized = equalize(data, h_eff, resource.spatial)
    llr = soft_demod(equalized, noise_variance=quality.noise_variance)
    coding = build_coding_snapshot(dci_record, resource)
    if not coding.complete:
        return state=coding_invalid, reason=coding.missing_fields

    tb_state = decode_dl_sch(llr, coding)
    observation = build_positioning_observation(iq, masks, quality)
    return resource, coding, tb_state, observation
```

实现时保留每一步的输入哈希/引用、维度、坐标域和版本。`estimate_channel`、`equalize`、`soft_demod` 和 `decode_dl_sch` 的具体 API/对象属性仍需在项目 MATLAB 或其他实现环境中实测，当前标记 `NEEDS_EXTERNAL_REFERENCE`。

## 31. 失败分类与排查顺序

| 阶段 | 典型症状 | 首要证据 | 建议状态 |
|---|---|---|---|
| DCI/关联 | PDSCH 资源漂移或用户串线 | candidate、RNTI、字段合法性、跨时隙一致性 | `dci_invalid` |
| 时序 | 数据窗口整体前后错位 | control/data slot、调度偏移、frame anchor | `timing_unknown` |
| 频域 | 资源命中但频率轴偏移 | BWP/Point A、局部/绝对 PRB 映射 | `coordinate_mismatch` |
| 方向 | 在 U/F/guard 符号提取到伪数据 | TDD symbol mask、捕获边界 | `direction_invalid` |
| 参考 | DM-RS 相关弱、估计发散 | 序列/端口/位置/功率快照 | `reference_config_missing` |
| 空间 | 单层正常、多层失败 | 天线/端口/层/预编码维度、条件数 | `channel_domain_mismatch` |
| 软信息 | 星座正常但 LDPC 不收敛 | LLR 符号、尺度、噪声方差、顺序 | `llr_invalid` |
| 率匹配 | 长度正确但 TB-CRC 始终失败 | `A/B/C/K'/F/N/E/E_r`、RV、索引 | `rate_matching_invalid` |
| HARQ | 重传后性能不升反降 | 软缓冲区键、母码坐标、LLR 标定 | `harq_context_mismatch` |
| 定位 | 峰稳定但跨站差异漂移 | 原始 I/Q、群时延、RF delay、时钟状态 | `toa_unreliable` |

排查顺序应从上游到下游：`config -> candidate/DCI -> coordinate -> mask -> DM-RS -> LLR -> coding -> HARQ -> timing`。不能先调峰值阈值来掩盖资源或译码错误。

## 32. 最小验证矩阵

| 编号 | 场景 | 固定项 | 单变量扰动 | 通过条件 | 当前状态 |
|---|---|---|---|---|---|
| PDSCH-01 | 无噪声、单位单径、单层 | 配置、资源、随机种子 | 无 | DM-RS/数据索引与端到端比特逐项闭合 | `NEEDS_VERIFICATION` |
| PDSCH-02 | 资源坐标 | 同一 IQ/快照 | BWP/Point A/PRB 偏移 | 只出现预期的坐标差异，越界被拒绝 | `NEEDS_VERIFICATION` |
| PDSCH-03 | 参考信号 | 同一数据和信道 | DM-RS 位置/序列/端口 | 错配进入 `dmrs_fail`，不静默译码 | `NEEDS_VERIFICATION` |
| PDSCH-04 | 调制与 LLR | 同一资源和编码 | `Q_m`、噪声方差、LLR 符号 | 长度、星座和译码状态同步变化 | `NEEDS_VERIFICATION` |
| PDSCH-05 | 多层/预编码 | 同一 TB、SNR | 层数、端口、预编码 | 端口/层维度和 `H_eff` 记录闭合 | `NEEDS_VERIFICATION` |
| PDSCH-06 | LDPC 长度 | 固定资源和 MCS | 单/多码块、TBS | `A/B/C/K'/F/N/E/E_r` 守恒 | `NEEDS_VERIFICATION` |
| PDSCH-07 | HARQ | 同一母码参数 | RV/重传次数 | 逆率匹配后软合并，TB-CRC 状态可解释 | `NEEDS_VERIFICATION` |
| PDSCH-08 | 邻 UE/MU-MIMO | 同一目标快照 | 干扰层/频偏/多径 | 掩码泄漏和 `collision_flag` 可量化 | `NEEDS_VERIFICATION` |
| PDSCH-09 | 定位接口 | 同一参考和站点 | 滤波器/窗口/时钟偏差 | 原始峰、校准字段和可用性门限闭合 | `NEEDS_VERIFICATION` |

在实际运行前，表中的“通过条件”是验收标准，不是已经获得的实验结果。任何 BLER、NMSE、ToA RMSE 或泄漏数值都必须附带配置、原始数据和运行记录。

## 33. 来源账本与外部核验队列

| 主张/接口 | 来源 | 证据类型 | 当前状态 |
|---|---|---|---|
| RE 坐标、层/端口、物理映射、DM-RS/PTRS 边界 | [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]] | `STANDARD` | `partial`；精确版本/表格 `NEEDS_EXTERNAL_REFERENCE` |
| MCS、资源预算、TBS、HARQ/CSI 数据过程 | [[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]] | `STANDARD` | `partial`；精确版本/表格 `NEEDS_EXTERNAL_REFERENCE` |
| CRC、LDPC 分段、率匹配、LLR 逆处理 | [[02-标准与参考/3GPP/3GPP TS 38.212｜Multiplexing and channel coding]]、[[01-专题知识/信道编译码/NR编码链/NR-DL-SCH 编码链]] | `STANDARD` + `PERSONAL_NOTE` | `partial`；参数表 `NEEDS_EXTERNAL_REFERENCE` |
| DCI 监测、调度时序和 HARQ 控制边界 | [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control]]、[[03-PDCCH/DCI]] | `STANDARD` + `PERSONAL_NOTE` | `partial`；精确时序 `NEEDS_EXTERNAL_REFERENCE` |
| DM-RS LS/插值和等效信道 | [[01-专题知识/信道估计与均衡/DM-RS]]、[[01-专题知识/信道估计与均衡/03 信道估计基础]] | `PERSONAL_NOTE` | `partial`；多端口闭环 `NEEDS_VERIFICATION` |
| 单 UE 掩码、ToA/TDoA 分离 | [[01-专题知识/5G定位/单用户时频截取与定位观测量]]、[[05-定位观测量/Timing Observation]] | `PERSONAL_NOTE` | `partial`；硬件/滤波校准 `NEEDS_VERIFICATION` |
| MATLAB/5G Toolbox API 名称和签名 | [[08-MATLAB代码/MATLAB 5G Toolbox API Map]] | `NEEDS_EXTERNAL_REFERENCE` | 尚未在本机运行闭环 |

本页没有锁定项目网络 Release、RRC 专用配置、实际 PDSCH IQ、MATLAB 版本或真实定位结果。具体字段、表值、序列初始化、API 输入维度和性能结论不得从本页抽象式推断。

## 34. 验收清单

- [ ] `config_id`、`event_id`、`candidate_id` 在控制、资源、编码和观测记录中一致。
- [ ] 控制 slot 与数据 slot 分开保存，调度偏移有来源和版本。
- [ ] BWP 局部 PRB、载波绝对 PRB、RE、FFT bin 和样点窗口可互相追溯。
- [ ] data/DM-RS/PTRS/reserved/control 掩码互斥，越界和重叠有明确失败状态。
- [ ] 端口、层、天线和等效信道域显式记录，未用数组形状猜测。
- [ ] `A/B/C/K'/F/N/E/E_r`、MCS、RV、NDI、HARQ 和 TB/CB-CRC 状态可回读。
- [ ] LLR 符号、尺度、噪声方差和率匹配坐标已定义，重传在母码坐标软合并。
- [ ] PDSCH 译码状态与定位观测状态独立，不用一个成功标志覆盖另一个。
- [ ] 所有未锁定 Release/API/现场实验项仍标为 `NEEDS_EXTERNAL_REFERENCE` 或 `NEEDS_VERIFICATION`。

## 35. 比特到 PDSCH RE 的逐层记账

将物理处理拆成四个可逆边界，可以更快定位“长度对了但内容错了”的问题：

```text
DL-SCH rate-matched bits e[0:E)
          |
          v  scrambling (cell/RNTI/config dependent)
scrambled bits c[0:E)
          |
          v  modulation Q_m
complex symbols d[0:E/Q_m)
          |
          v  layer mapping (N_layers)
layer symbols x^(v)[q]
          |
          v  precoding / port mapping
port symbols y^(p)[q]
          |
          v  data-RE mapping
grid symbols a[k,l,p]
```

可用下列抽象式检查维度：

$$
\mathbf c=\mathbf e\oplus\mathbf q_{scramble},
\qquad
|\mathbf c|=|\mathbf e|=E,
$$

$$
\mathbf d=\operatorname{Mod}_{Q_m}(\mathbf c),
\qquad
|\mathbf d|=E/Q_m,
$$

$$
\mathbf y[k,l]=\mathbf W[k,l]\mathbf x[k,l],
\qquad
\mathbf a[k,l,p]=\operatorname{Map}_{data}(\mathbf y[k,l]).
$$

`q_scramble` 的初始化、扰码作用域、比特排列和 `Map_data` 的顺序必须绑定 PDSCH 配置与适用 Release；上式只表达接口关系。接收端应保存每个边界的长度、索引引用和域：

至少应检查 `E mod Q_m = 0`，并记录层映射是否按配置均衡分配。若实现通过截断或补零强行满足整除，必须把该行为标为 `mapping_invalid`，不能把它当作标准率匹配结果。

| 边界 | 记录内容 | 常见故障 |
|---|---|---|
| 率匹配→扰码 | `E`、RNTI/小区上下文、比特顺序 | 解扰上下文错 |
| 扰码→调制 | `E`、`Q_m`、星座归一化 | LLR 符号/长度错 |
| 调制→层 | 每层符号数、层顺序 | 层间交错错 |
| 层→端口 | `W`、端口顺序、功率缩放 | 端口/预编码域错 |
| 端口→RE | `(k,l,p)` 有序映射和数据掩码 | RE 覆盖/顺序错 |

任何阶段发生截断、补零或隐式重排，都应记录为显式事件；不能靠最终 TB-CRC 通过来掩盖。

## 36. PDSCH DM-RS 配置维度

PDSCH DM-RS 不是一个只由“频域导频间隔”决定的二维图案。实现快照至少预留以下维度：

| 维度 | 作用 | 当前证据边界 |
|---|---|---|
| `mapping_type` | 参考符号相对 PDSCH 起始符号的解释 | 具体允许值/字段 `NEEDS_EXTERNAL_REFERENCE` |
| `dmrs_type` | 频域 RE 图案和端口复用关系 | 具体图案 `NEEDS_EXTERNAL_REFERENCE` |
| `additional_position` | 时域参考符号数量/位置 | 依配置和 Release，待核验 |
| `max_length` | 单/双符号参考结构 | 依配置和 Release，待核验 |
| `cdm_groups_without_data` | 码域复用与数据 RE 排除 | 依端口集合，待核验 |
| `port_set` | 参考端口到层/等效信道的关系 | 必须与预编码快照一致 |
| `scrambling_id`/初始化 | 生成参考序列的上下文 | 不能从小区 ID 单独猜测 |
| `power_scaling` | 参考与数据的相对功率 | 需记录实现/配置来源 |

接收端应先把这些维度解析成版本化的 `dmrs_config_ref`，再生成 `dmrs` 掩码和序列。只比较序列数值而不比较端口、位置和数据排除集合，不能证明 PDSCH 参考映射正确。

工程字段常见的语义例子包括 `mapping_type`（例如 A/B）、`dmrs_type`（例如 1/2）、additional position、max length 和 CDM group；这里仅说明接口维度，不固化允许值、表行或位宽。它们必须随 RRC/DCI 版本一起核验，当前均为 `NEEDS_EXTERNAL_REFERENCE`。

## 37. PTRS 与相位跟踪接口

当 PDSCH 配置了 PTRS 时，接收机要把它作为独立的参考层处理：

```text
PDSCH grid
  ├─ DM-RS -> channel estimate H_eff
  ├─ PTRS  -> common phase / phase-noise estimate
  └─ data  -> equalize + phase correction -> LLR
```

建议记录：

- PTRS 频域/时域密度和资源集合引用；
- PTRS 与 DM-RS 的端口/层关联；
- 相位估计的时间插值、频率插值或平滑假设；
- 相位校正前后的 EVM、残余公共相位和噪声估计；
- PTRS 不存在、不可用或与数据掩码冲突时的降级状态。

PTRS 的具体序列、密度、端口和启用条件属于版本化标准/配置内容，当前标为 `NEEDS_EXTERNAL_REFERENCE`。未配置 PTRS 时，不应在代码中凭经验生成“虚拟 PTRS”并写入标准快照。

## 38. MCS/TBS 计算边界

PDSCH 调度的数量级闭包可按以下顺序保存：

```text
PRB × data symbols
    -> total RE
    -> subtract DM-RS/PTRS/reserved/control
    -> N_RE,data
    -> Q_m × N_layers × target code rate
    -> N_info / TBS (standard rounding/table)
    -> DL-SCH A/B/C/K'/F/N/E
```

可用一个带条件的估算量检查方向是否合理：

$$
N_{info,approx}
\approx N_{RE,data}Q_mN_{layers}R,
$$

其中 `R` 是目标编码率近似值。该式不能替代 TBS 表格、取整规则、资源粒度、UCI/其他复用或特定调度限制；只要 `N_info,approx` 与实现得到的 TBS 相差明显，就应回到资源和版本快照排查。

建议把以下三个量分开：

| 量 | 含义 | 是否可由近似式替代 |
|---|---|---|
| `N_RE,data` | 可用于 PDSCH 数据的 RE 数 | 可做数量级审计，不替代映射 |
| `E` | 率匹配后实际送入调制的比特数 | 不可替代，必须由编码/资源闭合得到 |
| `TBS/A` | 传输块有效载荷长度 | 不可替代，需按标准过程计算 |

固定资源比较 MCS 时，记录 TBS、`E`、调制、目标码率和层数的联合变化；固定 TBS 比较资源时，记录能量、占用和有限块长效应。否则“同一 MCS 的 BLER 曲线”可能同时改变了多个因素。

## 39. DCI 字段族到 PDSCH 参数

PDSCH 解析器不需要把 DCI 位串直接传给后续模块，而应先生成带来源的字段对象：

| DCI 字段族 | 对 PDSCH 的影响 | 还需要的上下文 | 字段缺失时 |
|---|---|---|---|
| 频域资源分配 | 生成 BWP 内 VRB/PRB 集合 | BWP 大小、Point A、VRB-to-PRB 解释 | `coordinate_mismatch` |
| 时域资源分配 | 生成数据 slot、起始/长度 symbol | RRC 时域表、PDSCH mapping type、TDD | `timing_unknown` |
| MCS | 得到 `Q_m`/目标码率输入 | Release 对应 MCS 表和 TBS 过程 | `coding_config_missing` |
| RV/NDI/HARQ | 判定新数据、重传和软缓冲区键 | HARQ 进程、历史传输快照 | `harq_context_mismatch` |
| 天线端口/层相关字段 | 约束 DM-RS、层和预编码域 | RRC 端口配置、接收阵列 | `channel_domain_mismatch` |
| PTRS/相位相关字段 | 生成 PTRS 资源和校正输入 | PTRS 配置、功率和密度 | `reference_config_missing` |
| PDSCH-to-HARQ 时序 | 连接 ACK/NACK 反馈时机 | 38.213 控制过程和 PUCCH/PUSCH | `timing_unknown` |

字段解释顺序应固定为“先坐标、后资源、再编码、最后反馈时序”。同一个 DCI 候选如果只能解释出部分字段，仍可保存为 `candidate_only`，但不能生成 `snapshot_state=complete`。

## 40. 资源映射的边界条件

以下边界经常在实验中被遗漏，应作为独立断言：

- PDSCH 起止 symbol 不得覆盖已确定的控制、保护或非 DL 符号；flexible 符号需按配置单独标记。
- BWP 内局部 PRB 必须能映射到载波绝对子载波；跨 BWP 切换不能复用旧 `mapping_version`。
- DM-RS/PTRS/保留 RE 从数据集合扣除后，剩余集合必须与调制符号顺序一一对应。
- 多层映射时，端口/层的符号数量、顺序和功率缩放必须在 `spatial` 快照中闭合。
- 频域截取、FFT bin 选择和时域重构要记录是否包含 guard/保护带；不能把零填充当成真实观测。
- 任何“资源存在但 IQ 没有覆盖”的情况都应区分 `not_present`、`capture_truncated` 和 `decode_fail`。

这些边界是实现与实验的验收规则，不是对未知网络配置的推断；具体合法范围仍由锁定 Release 和 RRC 快照决定。

## 41. 物理处理闭环的中间断言

在实现或仿真中，每个 PDSCH 事件至少应能输出以下断言结果：

```js
pdsch_assertions:
  event_id: ""
  coordinate:
    local_absolute_prb_consistent: false
    symbol_direction_valid: false
    sample_window_in_bounds: false
  mask:
    data_reference_disjoint: false
    duplicate_count: 0
    overlap_count: 0
    ordered_index_reversible: false
  spatial:
    port_layer_dimensions_consistent: false
    dmrs_data_domain_consistent: false
  coding:
    modulation_length_consistent: false
    codeblock_length_conserved: false
    rate_matching_length_conserved: false
    harq_context_consistent: false
  outcome:
    resource_state: "unknown"
    decode_state: "unknown"
    observation_state: "unknown"
```

断言失败时保留失败阶段和最小复现引用。`false` 表示已检查且失败，`null`/`unknown` 表示尚未检查，不能把两者都编码为 0。

## 42. 版本化阅读与更新规则

当项目锁定一个新的 3GPP Release 或工具箱版本时，按以下顺序更新本页：

1. 先复制旧的 `config_snapshot`、`resource_snapshot` 和 `coding_snapshot`，生成新的版本键。
2. 对照 TS 38.211 核查物理映射、DM-RS/PTRS、调制和端口相关条款。
3. 对照 TS 38.214 核查 DCI 字段解释、资源分配、MCS/TBS、HARQ 和 CSI 过程。
4. 对照 TS 38.212 核查 DL-SCH 分段、LDPC、率匹配和 RV 坐标。
5. 对照 TS 38.213 核查控制时序、TDD/反馈和相关状态边界。
6. 用无噪声、单径和已知参考向量做逐边界回归，再更新 `verification_state`。

旧版本事件继续引用旧快照；不能只改 frontmatter 中的 Release 字符串来“升级”历史结果。当前 Vault 尚未锁定项目 Release，因此本页的精确字段/表值和 API 仍保持 `NEEDS_EXTERNAL_REFERENCE`。
