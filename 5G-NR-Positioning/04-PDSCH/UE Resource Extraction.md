---
title: UE Resource Extraction
aliases:
  - UE 信号资源提取
  - 单用户资源掩码
type: atomic
status: partial
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/ue-extraction
  - topic/resource-mask
source:
  - "[[01-专题知识/5G定位/单用户时频截取与定位观测量]]"
  - "[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]"
  - "[[04-PDSCH/PDSCH]]"
  - "[[01-NR基础/PRB RE Resource Grid]]"
  - "[[01-NR基础/NR Frame Slot]]"
related:
  - "[[03-PDCCH/DCI]]"
  - "[[04-PDSCH/PDSCH]]"
  - "[[01-专题知识/信道估计与均衡/03 信道估计基础]]"
  - "[[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
---

# UE Resource Extraction

## 1. 一句话定义

UE Resource Extraction 是依据已接受的 DCI、RNTI、物理信道配置和参考信号，把目标 UE 的时频 RE/样点从混合 IQ 中标出并生成可追溯掩码的过程。

> [!note] 与当前代码的边界
> 本页描述项目后续的 UE 资源提取接口，不是 `NR_decode_test.m` 已实现的能力。该脚本尝试解 SI-RNTI 调度的 SIB1；DCI 给出授权资源不自动等于已从混合 IQ 中分离出目标 UE 波形，仍需参考信号、空间/复用上下文和验证证据。

## 2. 为什么项目需要它

它把“控制信道解出来了”转成“知道目标 UE 在哪里发/收”，是单用户滤波、时频截断和定位观测的直接输入。

## 3. 它位于整个 5G 空口链路的什么位置

`C-RNTI -> PDCCH -> DCI -> PDSCH/PUSCH` 之后，`Timing Observation` 之前；它不负责重新猜测 RNTI，也不替代 PDCCH/数据译码。

## 4. 输入

接受的 DCI、carrier/BWP/PRB/symbol 配置、TDD 方向、DM-RS/PTRS 资源、端口/层、采样率/FFT/CP 和原始 IQ。

## 5. 输出

目标 UE 的 RE 索引、样点窗口、数据/参考/控制掩码、邻近用户残余指标、截取波形和 `resource_snapshot`。

## 6. 关键参数

`event_id`、RNTI、物理信道、BWP、PRB 集合、symbol 集合、层/端口、DM-RS 位置、FFT/CP、滤波器、窗口扩展量和群时延校准 ID。

## 7. 时域位置

按 frame/slot/symbol 生成合法窗口，并把 DCI 指示的时域资源与实际捕获样点对齐；跨 slot 的调度偏移要保留原始索引和解释版本。

## 8. 频域位置

按 BWP/Point A/PRB 生成子载波掩码；同时记录 BWP 局部下标和载波绝对下标，避免频移或带宽截断后无法复现。

## 9. 数学原理

设完整网格为 $Y[k,l]$，目标 UE 掩码为 $M_u[k,l]\in\{0,1\}$，则提取网格为：

$$
Y_u[k,l]=M_u[k,l]Y[k,l].
$$

掩码由配置和 DCI 决定，不由单纯能量阈值决定；时域波形重构还需明确窗函数、带宽和 FFT 归一化。

## 10. 3GPP 对应规范

- TS 38.211：RE、物理信道/参考信号映射。
- TS 38.214：DCI 驱动的数据资源和调度参数。
- TS 38.213/38.331：时序、TDD、BWP/CORESET/搜索空间配置来源。

精确 clause、版本和私有设备资源语义需核对，状态为 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

可参考 `nrExtractResources`、`nrPDSCHIndices`、`nrPDSCHDMRSIndices`、`nrOFDMInfo` 和基础逻辑索引/FFT 函数；输入维度与对象属性必须在项目 Release 中实际核验。

## 12. 本项目中的用途

将有效 DCI 转成目标 UE 的资源掩码，再分别输出完整译码支路和定位支路：前者用于 PDSCH/PUSCH/CRC，后者用于滤波、截断和 ToA。两支路共享 `event_id` 和配置快照，但不互相伪造成功状态。

## 13. 常见误区

- 把 DCI 的 PRB 字段直接当成绝对频率或样点范围。
- 忽略 DM-RS/PTRS/控制/保护 RE，导致“单用户”仍含结构化干扰。
- 只截取 strongest energy，不验证 RNTI、时序和资源合法性。
- 截取后不记录滤波器群时延和窗口扩展。

## 14. 与相似概念的区别

- 资源提取是索引/掩码操作；信道估计是从参考信号求 CSI；均衡是补偿信道。
- 单用户波形不是“解密后的业务明文”，而是经过资源选择的物理层观测。
- PDSCH/PUSCH 是物理信道，UE 是协议实体，掩码是接收机实现对象。

## 15. 代码实现注意事项

用显式结构体保存 `resource_snapshot`、`mask_version` 和坐标轴；对掩码做覆盖/互斥/边界测试；保留原始网格和截取前后波形；将群时延、抽取和重采样记录到校准账本。

## 16. 待实验验证的问题

- 已知单 UE 正例下 DCI 资源到 RE/样点的逐项命中率。
- 邻近用户、频偏、多径和 TDD flexible symbol 下的残余泄漏。
- 资源掩码对 ToA 方差、峰偏差和带宽变化的影响。
- MATLAB `nrExtractResources` 等 API 的实际维度和边界行为。

## 17. Related Notes

- [[03-PDCCH/DCI]]
- [[04-PDSCH/PDSCH]]
- [[01-专题知识/信道估计与均衡/03 信道估计基础|Channel Estimation]]
- [[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡|Equalization]]
- [[01-专题知识/5G定位/单用户时频截取与定位观测量|Filtering and Truncation]]
- [[05-定位观测量/Timing Observation]]

## 证据与状态

- `PERSONAL_NOTE`：现有单用户截取与 PDCCH/PDSCH 笔记的接口整理。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚无本项目真实 C-RNTI/资源正例。

## 18. 资源提取的所有权边界

资源提取器消费的是已经通过候选、RNTI、DCI 字段和配置检查的结果；它不应重新猜测用户身份，也不应把能量最大的 PRB 直接命名为目标 UE。

```text
配置/RRC + C-RNTI 证据
          |
          v
PDCCH/DCI record（控制时刻）
          |
          v
resource_snapshot（数据时刻、BWP、PRB、symbol、空间配置）
          |
          +--> RE mask / ordered extraction
          |          |
          |          +--> DM-RS -> CSI -> equalization -> PDSCH/DL-SCH
          |          |
          |          +--> reference/data segment -> timing observation
          |
          +--> failure/quality ledger
```

四种结果必须分开：

| 结果 | 含义 | 不能替代 |
|---|---|---|
| `resource_found` | 依配置生成了合法索引 | DCI 或 TB-CRC 通过 |
| `signal_extracted` | 从 IQ 取出了对应 RE/样点 | 信道估计成功 |
| `decoded` | 软解调和 DL-SCH 状态可回读 | 用户身份最终确认 |
| `timing_candidate` | 有可追溯峰和校准字段 | 可靠 TDOA/绝对距离 |

## 19. 坐标域与不可变字段

提取器至少同时维护以下坐标域：

| 坐标域 | 关键字段 | 典型用途 |
|---|---|---|
| 事件/协议域 | `event_id`、RNTI、DCI、HARQ | 关联控制和重传 |
| 载波/BWP 域 | Point A、BWP ID/起点/大小、SCS | 解释绝对频率 |
| 网格域 | `k`、`l`、`p`、数据/参考集合 | 生成 RE 掩码 |
| 波形域 | FFT bin、CP、symbol start/end | OFDM 解调与重构 |
| 设备域 | capture offset、IQ sample、抽取/滤波版本 | 回放与时间校准 |

`resource_snapshot` 一旦被观测或译码消费就视为不可变。配置变化、重采样、FFT/CP 变化或时钟重锁必须产生新的 `config_id`/`mask_version`，不能原地修改旧掩码，否则跨站记录会引用不同含义的“同一”资源。

## 20. 提取输入契约

```js
extraction_input:
  event_id: ""
  candidate_id: ""
  config_id: ""
  mask_version: ""
  rnti:
    type: "C-RNTI|TC-RNTI|RA-RNTI|unknown"
    value: null
    evidence_ref: ""
  dci_ref: ""
  resource_snapshot_ref: ""
  iq:
    capture_id: ""
    channel_id: ""
    start_sample: null
    sample_count: null
    sample_rate_hz: null
    center_frequency_hz: null
    complex_layout: "unknown"
  ofdm:
    fft_size: null
    cp_lengths: []
    windowing: "unknown"
    demod_version: ""
  calibration:
    sample_time_origin: "unknown"
    rf_delay_id: ""
    filter_delay_id: ""
    clock_state: "unknown"
  state: "ready|partial|rejected"
  missing_fields: []
```

`null` 表示字段未知，`0` 才表示已知的零值；二者不能互换。对多个站点复用同一逻辑掩码时，站点特有的采样起点、RF 延迟和滤波器版本仍必须分别记录。

## 21. 掩码分层与优先级

不要只保存一个布尔矩阵。建议按层保存并保留有序索引：

```js
mask_layers:
  control_or_other: []
  pdsch_data: []
  pdsch_dmrs: []
  pdsch_ptrs: []
  reserved_or_guard: []
  unknown: []
  overlap_pairs: []
  out_of_range: []
```

在同一个 `(k,l,p)` 上，任何两个互斥层发生交集都应进入 `overlap_pairs`。推荐的判定顺序是：

1. 先验证网格/端口范围和 TDD 方向。
2. 再写入控制、保护和已知参考信号集合。
3. 最后将剩余且合法的资源标为数据。
4. 对重复索引、未知资源和跨 BWP 坐标单独计数。

这样可以避免“数据层最后写入，所以覆盖了 DM-RS”的静默错误。掩码覆盖率可定义为：

$$
\rho_{mask}
=\frac{|\mathcal R_{target}\cap\mathcal R_{extracted}|}
{|\mathcal R_{target}|},
$$

但 `\rho_mask=1` 只说明索引覆盖，不说明信号来自目标 UE 或已完成均衡。

## 22. 网格到样点的提取流程

提取过程应把“有序索引”作为一等数据，避免依赖二维数组当前布局：

```text
读取 resource_snapshot/config_snapshot
        |
        v
检查 BWP、PRB、symbol、端口、TDD 和边界
        |
        v
生成有序 (k,l,p) 集合与 data/dmrs/ptrs/reserved 掩码
        |
        v
按 OFDM 配置把 (frame,slot,l) 映射为样点窗口
        |
        v
对每个样点窗口做 FFT/资源解调并保留原始坐标
        |
        v
分别输出 RE 网格、参考片段、数据片段和质量摘要
```

实现骨架：

```python
extract_resources(iq, snapshot):
    validate_axes(snapshot)
    masks = build_disjoint_masks(snapshot)
    if masks.out_of_range or masks.overlap:
        return rejected(masks.reason)

    windows = symbol_windows(snapshot.data_time, snapshot.ofdm)
    grid = ofdm_demodulate(iq, windows, snapshot.ofdm)
    refs = ordered_take(grid, masks.dmrs + masks.ptrs)
    data = ordered_take(grid, masks.data)

    return {
        "grid": grid,
        "reference_re": refs,
        "data_re": data,
        "mask_layers": masks,
        "coordinate_map": snapshot.coordinate_map,
        "state": "signal_extracted"
    }
```

`symbol_windows`、FFT 归一化、CP 去除和频率搬移必须由同一 `demod_version` 定义。提取后的网格不能脱离原始 IQ、捕获起点和配置快照单独交付。

## 23. 两条输出支路

### 23.1 完整译码支路

```text
DM-RS -> 信道估计/插值 -> 数据均衡
      -> 软解调/解扰 -> 逆率匹配
      -> LDPC -> CB-CRC/TB-CRC -> HARQ 状态
```

该支路关注 `resource_valid`、LLR 长度/符号、`A/B/C/K'/F/N/E/E_r` 和 TB-CRC。解码失败要保留中间 LLR 和失败阶段。

### 23.2 定位观测支路

```text
已验证参考/数据片段
      -> 频域选择或时域重构
      -> 滤波/窗口/相关
      -> 原始峰 -> 群时延/RF/时钟校准
      -> timing_candidate / tdoa_usable
```

两条支路共享 `event_id`、`resource_snapshot_id` 和原始样点引用，但状态独立：

| 译码状态 | 定位状态 | 合法解释 |
|---|---|---|
| `tb_crc_pass` | `uncalibrated` | 可确认资源/载荷，不能用于可靠 TDOA |
| `tb_crc_fail` | `reference_usable` | 可保留参考峰，不能声称数据译码成功 |
| `resource_invalid` | `none` | 不应生成目标 UE 观测 |
| `decoded` | `calibrated` | 仍需检查跨站一致性和峰策略 |

## 24. 质量、泄漏与碰撞指标

建议每次提取保存以下指标，而不是只保存一张波形图：

```js
extraction_quality:
  event_id: ""
  resource_snapshot_id: ""
  mask_coverage: null
  duplicate_re_count: 0
  overlap_re_count: 0
  out_of_range_count: 0
  dmrs_snr_db: null
  channel_nmse: null
  equalized_sinr_db: null
  llr_abs_percentiles: []
  adjacent_user_power_ratio_db: null
  residual_cfo_hz: null
  collision_flag: false
  mu_mimo_possible: false
  confidence: "low|medium|high|unknown"
  state: "pass|partial|fail"
```

`adjacent_user_power_ratio_db`、`channel_nmse` 和 ToA 方差只有在有明确参考真值、噪声定义和运行记录时才可填数值；否则使用 `null` 并标 `NEEDS_VERIFICATION`。同一 PRB 多用户、码域复用或未知预编码时，`single_user_confidence` 应主动降级。

## 25. 窗口、滤波与时间偏差

资源掩码到样点窗口的转换会引入实现层偏差。每个站点至少记录：

- 捕获起点、frame/slot/symbol 对齐方法；
- FFT 窗口、CP 去除、窗函数和零填充；
- 数字下变频、抽取/重采样及其版本；
- 滤波器通带、相位响应和群时延校准 ID；
- RF/采样链固定延迟、时钟偏置和采样率偏差；
- `first`、`strongest` 或 `cluster` 峰选择策略。

线性滤波器的群时延可用频响相位表达：

$$
\tau_g(f)=-\frac{1}{2\pi}\frac{d\arg G(f)}{df}.
$$

未经校准的滤波或窗口偏差不得被隐藏在 `toa_raw_seconds` 中，更不能把它直接送入 [[05-定位观测量/Timing Observation|Timing Observation]] 作为几何距离。

## 26. 失败状态机

```text
not_ready
  -> snapshot_checked
  -> mask_built
  -> grid_extracted
  -> reference_checked
  -> data_extracted
  -> decoded_or_observed

任一阶段可转入：
  rejected / partial / collision / coordinate_mismatch / calibration_missing
```

推荐保留以下细粒度状态：

| 状态 | 触发条件 | 是否可继续 |
|---|---|---|
| `snapshot_missing` | 无完整 DCI/配置引用 | 只可等待补配置 |
| `coordinate_mismatch` | 局部/绝对坐标或 BWP 不一致 | 不可生成数据掩码 |
| `direction_invalid` | symbol 不属于 DL/合法方向 | 丢弃该资源 |
| `mask_overlap` | data 与参考/保留集合交叠 | 修复映射后重试 |
| `ofdm_boundary_error` | 窗口越界或 CP/FFT 不一致 | 不能交付 ToA |
| `reference_fail` | DM-RS 不可用或域不匹配 | 可保留原始片段，不能均衡 |
| `extraction_partial` | 只有部分资源可回放 | 只能标记部分观测 |
| `collision_suspected` | 多 UE/层无法分离 | 降低置信度并隔离 |
| `calibration_missing` | 群时延/RF/时钟未知 | 禁止 `tdoa_usable` |

“没有监测到该候选”和“候选监测到但提取失败”必须用不同状态，否则召回率和资源错误率无法解释。

## 27. 最小验证矩阵

| 编号 | 输入 | 扰动 | 观测 | 通过条件 | 状态 |
|---|---|---|---|---|---|
| EXT-01 | 已知单层、无噪声网格 | 无 | RE/样点逐项索引 | 掩码覆盖、顺序和逆映射闭合 | `NEEDS_VERIFICATION` |
| EXT-02 | 同一 IQ | BWP/Point A 偏移 | 局部/绝对坐标 | 偏移可解释，越界拒绝 | `NEEDS_VERIFICATION` |
| EXT-03 | data+DM-RS+PTRS | 注入重复/交叠索引 | overlap 计数 | 不静默覆盖，状态为 `mask_overlap` | `NEEDS_VERIFICATION` |
| EXT-04 | 正确 DM-RS | 序列/端口/位置错配 | DM-RS 质量、域 | 进入 `reference_fail` | `NEEDS_VERIFICATION` |
| EXT-05 | 双支路 | 译码失败但参考存在 | 两类状态 | 观测支路不伪造 TB-CRC | `NEEDS_VERIFICATION` |
| EXT-06 | 邻 UE/MU-MIMO | 频偏、多径、同 PRB | 泄漏/碰撞指标 | 置信度和残余功率可追溯 | `NEEDS_VERIFICATION` |
| EXT-07 | 多站片段 | 滤波/RF/时钟偏差 | raw/calibrated ToA | 未校准时 `tdoa_usable=false` | `NEEDS_VERIFICATION` |

每项都应保存原始 IQ 或引用、快照、掩码版本、运行参数和失败日志。通过静态结构检查不等于已通过这些动态实验。

## 28. 来源与缺口

- `PERSONAL_NOTE`：[[01-专题知识/5G定位/单用户时频截取与定位观测量]]、[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]] 提供单用户截取和定位接口语义。
- `STANDARD + partial`：[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]、[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]] 提供资源、参考信号和数据过程边界；精确 Release/表格为 `NEEDS_EXTERNAL_REFERENCE`。
- `PERSONAL_NOTE`：[[01-NR基础/PRB RE Resource Grid]]、[[01-NR基础/NR Frame Slot]] 提供坐标快照和 frame/slot/symbol 约定。
- `PERSONAL_NOTE`：[[05-定位观测量/Timing Observation]]、[[07-多站协同/Multi-Station Synchronization]] 提供校准字段和跨站接口；真实硬件延迟为 `NEEDS_VERIFICATION`。
- `NEEDS_EXTERNAL_REFERENCE`：`nrExtractResources`、`nrPDSCHIndices`、`nrPDSCHDMRSIndices`、`nrOFDMInfo` 等 API 的签名、数组布局和 Release 行为尚未在本机闭环核验。

## 29. 验收清单

- [ ] 资源提取只消费 `valid_dci`/完整配置，不从能量阈值猜测 UE。
- [ ] 所有索引携带坐标域、基准、顺序和 `mask_version`。
- [ ] data/DM-RS/PTRS/reserved/control 掩码互斥，重复和越界可计数。
- [ ] BWP 局部、载波绝对、网格、FFT 和样点坐标可回放。
- [ ] 原始 IQ、滤波/抽取参数、窗口和校准 ID 与片段绑定。
- [ ] 完整译码与定位观测两条支路状态独立。
- [ ] `tdoa_usable` 只有在校准、质量和跨站一致性门通过时才可置真。
- [ ] 动态实验尚未运行时，所有性能字段保持 `null` 并标 `NEEDS_VERIFICATION`。
