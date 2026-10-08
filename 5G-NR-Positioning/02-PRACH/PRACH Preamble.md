---
title: PRACH Preamble
aliases:
  - NR PRACH 前导
  - 随机接入前导
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - topic/sequence
  - process/detection
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/02-PRACH/Zadoff Chu Sequence|Zadoff Chu Sequence]]"
  - "[[5G-NR-Positioning/02-PRACH/Cyclic Shift|Cyclic Shift]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]"
  - "[[01-专题知识/信道估计与均衡/02 参考信号与导频设计|现有参考信号笔记]]"
---

# PRACH Preamble

## 1. 一句话定义

PRACH Preamble 是 UE 在一个合法 RO 中发送的已知序列实例，由根序列、循环移位和前导索引共同确定。

## 2. 为什么项目需要它

前导是接收机做相关检测、粗 ToA 和事件触发的已知结构；检测结果可关联 RAPID，但它不携带明文 C-RNTI，也不能唯一标识 UE。

## 3. 它位于整个 5G 空口链路的什么位置

它是 Msg1 的序列层，位于 RO 资源映射之后、相关检测和 RA-RNTI/RAR 关联之前；后续 Msg3 使用 PUSCH，不应把两者当同一波形。

## 4. 输入

- 根序列索引、L_RA、循环移位集合和 restricted set。
- RO 的时频位置、前导索引和发射功率。
- 采样率、CFO、捕获窗口和信道传播条件。

## 5. 输出

- 时域前导样本或频域序列。
- 前导索引与根/循环移位的映射。
- 相关检测参考、可用的峰间隔和碰撞诊断。

## 6. 关键参数

L_RA、逻辑根序列索引、实际根序列、循环移位 C_v、zero-correlation zone、restricted set、前导索引和功率爬升。不同 PRACH format 和版本的序列长度/映射规则需按 TS 38.211 复核。

## 7. 时域位置

前导占用 RO 指定的连续时域区间，含循环前缀和保护部分；检测时应以序列有效区为相关主体，并记录相对捕获起点的偏移。

## 8. 频域位置

前导使用 PRACH 专用子载波间隔和频域 RO；频域映射后再经 IFFT 生成时域波形。其频域带宽不能简单等同于整个采集带宽或 PUSCH BWP。

## 9. 数学原理

给定根序列 x_u[n]，循环移位实例可抽象为

$$
x_{u,v}[n]=x_u[(n+C_v)\bmod L_{RA}].
$$

理想条件下不同 C_v 的相关峰分离；多径和频偏会引入峰展宽、旁瓣和偏移。精确序列生成中的奇偶长度、根索引置换和 restricted set 规则不可由此简式替代。

## 10. 3GPP 对应规范

- TS 38.211 §6.3.3.1/§6.3.3.2：PRACH 序列、前导生成和物理资源映射；§5.3.2 负责 PRACH OFDM 基带波形生成。准确子条款及表格按版本核对，状态 NEEDS_EXTERNAL_REFERENCE。
- TS 38.213 §8：前导发送功率、重传和 Occasion 上下文。
- 相关字段：rootSequenceIndex、zeroCorrelationZoneConfig、restrictedSetConfig、preamble index。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHConfig：设置 L_RA、根序列和循环移位相关配置。
- nrPRACH：生成 PRACH 前导符号。
- nrPRACHIndices：生成资源索引。
- nrPRACHDetect：按配置检测前导索引；多峰碰撞需自定义相关轨迹。

上述 API 的签名、归一化和 Release 行为为 `NEEDS_EXTERNAL_REFERENCE`，当前没有本项目实测结果。

## 12. 本项目中的用途

用前导索引和 RO 建立 preamble_event，并把相关峰/ToA 传给 [[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]；随后由 [[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]] 和 [[5G-NR-Positioning/02-PRACH/RAR|RAR]] 做协议级关联，而不是把前导直接命名为 C-RNTI。

## 13. 常见误区

- 把前导索引当作 UE 永久 ID。
- 把根序列索引和前导索引混用。
- 忽略同一 RO 内前导碰撞。
- 把 PRACH 前导当成可直接用于 PDSCH 均衡的 DM-RS。

## 14. 与相似概念的区别

前导是序列实例；Zadoff-Chu 是序列族的数学构造；循环移位是从根序列得到实例的参数；RAPID 是 RAR 中用于匹配前导的 MAC 子字段；C-RNTI 属于后续 UE 专用标识。

## 15. 代码实现注意事项

- 明确序列索引的 0/1 基和逻辑根到物理根的映射。
- 用复数双精度保存参考序列，避免量化导致相关损失。
- 保留每个候选的根、移位、RO 和峰值，不只返回 argmax。
- 对 CFO/采样率偏差先校正或在结果中显式标记。

## 16. 待实验验证的问题

- 当前采集设备是否保留足够带宽以覆盖完整 PRACH 前导。
- restricted set 和 beam-specific 前导是否启用。
- 多径下首峰与最大峰分别对应哪个循环移位。
- MATLAB 生成序列与现场设备序列的归一化是否一致。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/Zadoff Chu Sequence|Zadoff Chu Sequence]]、[[5G-NR-Positioning/02-PRACH/Cyclic Shift|Cyclic Shift]]、[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]、[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]。
- 旧笔记：[[01-专题知识/信道估计与均衡/02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别|PRACH 与信道估计边界]]、[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]。

## 18. 一个前导实例到底包含什么

“前导”不是一个孤立的复数向量，而是下面这组坐标和序列参数的联合对象：

$$
p=(\mathrm{RO}_t,\mathrm{RO}_f,\mathrm{format},L_{RA},i,u,v,C_v).
$$

其中 `RO_t`/`RO_f` 决定发送资源，`format` 和 `L_RA` 决定波形模板，`i` 是 logical root index，`u` 是表映射后的 physical root，`v` 是该根下的移位序号，`C_v` 才是实际循环移位量。`preamble_index` 是网络在当前时频 RO 内给这个元组分配的编号。

同一个 `preamble_index` 在不同 RO 中不是同一事件；同一 `physical_root_u` 在不同配置版本中也不一定拥有相同的候选移位集合。建议把前导 ID 写成 `(<config_id>, <RO_t>, <RO_f>, <preamble_index>)`，而不是只写一个整数。

## 19. 从配置到时域波形的完整链

序列层、资源网格层和时域波形层要分开记录。一个可实现的抽象是：

$$
\begin{aligned}
x_{u,v}[n]&=x_u[(n+C_v)\bmod L_{RA}],\\
y_{u,v}[k]&=\sum_{n=0}^{L_{RA}-1}x_{u,v}[n]e^{-j2\pi kn/L_{RA}},\\
a_{k}^{RA}&=\beta_{RA}y_{u,v}[k],\\
s_p&=\mathrm{CPGuard}_{format}\left(\mathrm{IFFT}_{N_u}(a_k^{RA}),N_{CP},N_{guard}\right).
\end{aligned}
$$

这里 `a_k^RA` 是映射到 PRACH 频域资源的符号，`beta_RA` 是功率/归一化因子，`N_u`、`N_CP` 和保护区由 format 表决定。最后一行不是把任意 ZC 向量直接零填充到 FFT：频域起点、PRACH SCS、IFFT 长度、CP 和保护部分必须来自同一份配置快照。
其中 `IFFT_{N_u}` 和 `CPGuard` 是项目侧的离散实现抽象；38.211 §5.3.2 的连续时间表达式、采样常数和起始时间仍是最终依据，不能仅凭这个简式推导出工具箱的 FFT/CP 参数。

发送端和接收端应分别保存：

| 层 | 必须能回放的对象 | 典型错误 |
|---|---|---|
| 序列层 | `u`、`C_v`、相位符号、`L_RA` | 根表错、移位方向反 |
| 频域资源层 | PRACH 子载波集合、`beta_RA`、频域起点 | 把局部 bin 当载波绝对 bin |
| OFDM 层 | `N_u`、CP、保护区、采样率 | 用 PUSCH FFT/CP 代替 PRACH |
| RO 层 | 帧/时隙/符号、`RO_t`/`RO_f` | 在非法 TDD 符号上搜索 |

## 20. 长前导/短前导：接收机必须显式分支

> [!warning] `STANDARD + NEEDS_EXTERNAL_REFERENCE`
> format 到 `L_RA`、`Δf_RA`、`N_u`、`N_CP`、重复段和 restricted-set 支持的绑定关系属于 TS 38.211 的版本化表格。本文只给边界和实现原则，不复制精确表值；要运行检测，必须加载锁定 Release 的表。

| 维度 | 长前导 | 短前导 |
|---|---|---|
| 主要用途 | 面向较大覆盖距离/较宽定时不确定度的设计点 | 面向较短时域占用和较高 PRACH SCS 的设计点 |
| 序列长度 | 长序列 family 的 `L_RA`，常见资料中的具体值不作默认 | 短序列 family 可能有多个 `L_RA`，按 format 查表 |
| PRACH SCS | 低 SCS 分支；与普通 UL SCS 不是同一字段 | 由 format 和 numerology 绑定，不能仅由 `L_RA` 推导 |
| 时域构成 | 序列、CP、重复段和 guard 可能跨较长窗口 | 序列更短，但 A/B/C 等 format 的 CP/重复段仍不同 |
| restricted set | 某些长 format 支持 type A/B | 支持与否由表行给出，不能按经验开启/关闭 |
| 定时处理 | 窗口较长，首径/最大峰和跨周期处理需留余量 | 窗口较短，采样率和 CP 错配更容易造成整段漏检 |

实现入口应是 `format -> waveform_profile` 的表查找，而不是 `if L_RA == 839` 这类常数分支。没有 format 或 Release 时，`family=unknown`、`preamble_decodable=false` 是诚实的输出。

## 21. 前导索引映射：root、shift、RAPID 的三层关系

一个 RO 的候选表可表示为：

| 列 | 含义 | 生成来源 |
|---|---|---|
| `preamble_index` | RO 内的编号 | 标准枚举顺序，从 0 基或实现约定转换时要记录 |
| `logical_root_index` | 根序列逻辑编号 | 从配置的起始 root 开始循环展开 |
| `physical_root_u` | ZC 公式中的根号 | 38.211 根索引置换表 |
| `shift_ordinal_v` | 根内移位序号 | unrestricted/restricted shift 生成器 |
| `cyclic_shift_C_v` | 模 `L_RA` 的实际移位 | `N_CS`、`d_u` 和 restricted 分支 |
| `RAPID` | RAR 中用于匹配的字段 | MAC 层字段，需在同一 RO 上下文验证 |

在 38.211 V17.8.0 基线中，每个时频 RO 定义 64 个前导候选；RRC 的 `totalNumberOfRA-Preambles`、MsgA 分区或 CFRA 配置可以进一步限制某次过程可用的子集。索引基准、分区和 2-step/专用接入分支仍必须按目标 Release 核对。前导索引的可复现构造应遵循：

```text
读取 format、L_RA、root start、restricted set 和 zero-correlation 配置
按 logical root 的循环顺序取得 root candidates
对每个 logical root 用 Release 对应表得到 physical u
对每个 u 生成该根允许的 (v, C_v)
按标准规定的 root/shift 枚举顺序逐项编号为 preamble_index
达到本 RO 的候选上限后停止，并检查 (u, C_v) 唯一
```

不要使用 `preamble_index // N_CS` 或 `preamble_index % N_CS` 代替上述过程：当 restricted set 使每根移位数量不同、或一个 RO 需要多个根时，这种算术映射会悄悄产生错误。RAPID 在 RAR 中通常用于与前导编号匹配，但“数值相等”必须同时满足相同 RO、RAR 窗口、PDCCH/PDSCH 解码和 MAC 字段合法性，不能单凭整数相等完成用户关联。

## 22. 碰撞、可分离性与受限集合

同一 RO 的信号叠加可写成

$$
r[n]=\sum_{q\in\mathcal{U}}\alpha_qx_{u_q,v_q}[(n-\tau_q)\bmod L_{RA}]+w[n].
$$

应按以下层次解释：

1. **同一根、同一 `C_v`**：两个 UE 发送相同前导时，理想单天线相关器只看到一个叠加峰；除非有额外空间、功率或后续消息证据，序列层不可分离。
2. **同一根、不同 `C_v`**：若相对移位大于信道时延扩展、采样误差和峰宽，可能出现多个峰；否则峰簇重叠，应标记 `ambiguous`。
3. **不同根**：根间相关不保证为零；低旁瓣不等于无干扰，尤其在低 SNR、CFO 或频域泄漏下不能强行拆分。
4. **不同 `RO_t` 或 `RO_f`**：资源坐标本身提供分离，但频域泄漏、捕获窗口错位或 TDD 标注错仍可造成伪碰撞。

`restrictedSetConfig`/`msgA-RestrictedSetConfig` 改变的是允许的 `C_v` 集合和根的利用方式，不是一个简单的“关闭某些前导”开关。其设计动机与高速移动下的相关峰/时延保护有关；具体 type A/B 公式、`d_u`、`n_shift^RA` 和可用候选数必须从 38.211 表和分支公式读取。检测器发现候选表为空或数量不足时，应输出 `config_inconsistent`，不能退回 unrestricted 公式猜测。

## 23. 接收数据结构：序列证据与协议证据分层

建议为每个前导候选保存不可变快照，为每次观测保存独立结果：

```js
preamble_candidate:
  config_id: <immutable-config-id>
  release_or_toolbox_version: null
  cell_id: null
  ro_time: {frame: null, slot: null, symbol: null}
  ro_frequency: {occasion: null, prach_subcarrier_start: null}
  format: <format-or-unknown>
  family: long|short|unknown
  L_RA: null
  delta_f_RA_hz: null
  logical_root_index: null
  physical_root_u: null
  shift_ordinal_v: null
  cyclic_shift_C_v: null
  preamble_index: null
  restricted_set: unrestricted|A|B|unknown
  N_CS: null
  reference_hash: null
  source_status: STANDARD|NEEDS_EXTERNAL_REFERENCE

preamble_observation:
  event_id: <ro-and-capture-key>
  candidate_ref: <candidate-id>
  capture_id: null
  correlation_trace_ref: null
  peak_indices: []
  peak_values: []
  residual_delay_samples: null
  toa_strategy: first|strongest|cluster|unknown
  cfo_state: estimated|compensated|unknown
  collision_status: none|possible|ambiguous|unresolvable
  quality_flags: []
  protocol_state: preamble_detected|rar_pending|associated|unknown
```

`protocol_state=associated` 必须由 [[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]] 的跨消息证据设置；序列相关器只能写 `preamble_detected` 或 `ambiguous`。不要把 `RAPID`、Temporary C-RNTI 或 C-RNTI 塞进 `preamble_candidate`，否则后续无法区分序列事实与协议推断。

## 24. 前导生成与接收伪代码

下面的伪代码刻意把标准表查找作为依赖注入，以便在 Release 切换时失败显式可见：

```python
def build_preamble_candidates(snapshot, tables):
    require(snapshot.format, snapshot.L_RA, snapshot.root_start)
    profile = tables.format_profile(snapshot.release, snapshot.format)
    assert profile.L_RA == snapshot.L_RA
    roots = tables.logical_root_order(snapshot.root_start, snapshot.L_RA)
    rows = []
    for logical_i in roots:
        u = tables.root_number(snapshot.L_RA, logical_i)
        shifts = tables.cyclic_shifts(snapshot, u)
        rows.append((logical_i, u, shifts))
    ordered = tables.preamble_order(rows)
    return assign_indices_until_limit(ordered, tables.preamble_limit(snapshot))

def detect_one_ro(iq, ro, snapshot, tables):
    candidates = build_preamble_candidates(snapshot, tables)
    segment = extract_prach_sequence_region(iq, ro, snapshot, tables)
    observations = []
    for c in candidates:
        ref = generate_reference(c, snapshot, tables)
        trace = circular_or_sliding_correlation(segment, ref)
        peaks = keep_all_local_peaks(trace)
        observations.append(score(c, peaks, trace))
    return classify_peaks(observations,
                          keep_trace=True,
                          collision_aware=True,
                          unknown_on_missing_profile=True)
```

实现约束：

- `extract_prach_sequence_region` 要同时处理 CP、guard、采样率和频域 RO，不能直接从任意 slot 截取固定长度。
- `generate_reference` 的相位符号、归一化和 DFT 方向必须与发射模型绑定，并写入 `reference_hash`。
- `classify_peaks` 输出所有通过候选，不只返回最大值；峰簇重叠时保留 `ambiguous`。
- 只有在同一 RO 的 `preamble_index` 与 RAR `RAPID`、时序和 MAC/PHY 校验全部一致时，才创建后续关联边。

## 25. 失败模式与最小诊断路径

| 症状 | 优先检查 | 可能的根因 | 正确状态 |
|---|---|---|---|
| 长前导有峰、短前导无峰 | family-specific profile、CP、FFT、SCS | 长/短模板混用 | `format_mismatch` |
| 峰值存在但索引始终错一组 | root-map、shift 方向、枚举顺序 | 把 logical `i` 当 physical `u` | `mapping_error` |
| 只有单个最大峰 | 全峰轨迹和峰筛选配置 | API 丢弃多实例/碰撞峰 | `multi_peak_unknown` |
| 同一 RO 多用户却只有一个稳定峰 | 同根同移位、功率比、时延差 | 序列碰撞本来不可分离 | `collision_unresolvable` |
| restricted set 配置下候选数异常 | type A/B、`N_CS` 表、`d_u` | 错用 unrestricted 公式 | `config_inconsistent` |
| RAPID 数值匹配但后续 Msg3 不对 | RO/响应窗口、RAR CRC、UL grant | 跨 RO 或伪 RAR 关联 | `rar_unconfirmed` |
| 峰跨 CP/周期边界 | 模索引、unwrap、捕获起点 | 把循环位置当绝对 ToA | `timing_ambiguous` |

任何一个序列层失败都不应直接写成“网络没有 UE”；任何一个 RAR 层失败也不应回写为“PRACH 前导不存在”。

## 26. 最小验证用例（设计稿）

| 用例 | 构造 | 通过条件 | 当前状态 |
|---|---|---|---|
| PRE-01 序列闭环 | 由同一 snapshot 生成/再生成一个候选 | `reference_hash` 稳定，幅度/相位和 DFT 关系一致 | `EXPERIMENT + NEEDS_VERIFICATION` |
| PRE-02 长短边界 | 各 family 各选一个 format fixture | profile、CP、FFT、采样率不串用；缺表时显式失败 | `EXPERIMENT + NEEDS_VERIFICATION` |
| PRE-03 前导索引 | root-map 和 shift-table fixture | 候选无重复，索引顺序与锁定 Release 向量一致 | `STANDARD + NEEDS_EXTERNAL_REFERENCE` |
| PRE-04 已知延迟 | 单用户、无噪声、整数/亚采样延迟 | `preamble_index` 正确，残余时延闭合到注入值 | `EXPERIMENT + NEEDS_VERIFICATION` |
| PRE-05 同前导碰撞 | 两个 UE 同一 RO/同一候选 | 输出 `collision_unresolvable` 或功率/空间附加证据，不伪造两个用户 | `EXPERIMENT + NEEDS_VERIFICATION` |
| PRE-06 可分离移位 | 同根两个允许 `C_v`，改变时延差 | 峰分离随峰距/多径变化可解释，保存全轨迹 | `EXPERIMENT + NEEDS_VERIFICATION` |
| PRE-07 restricted set | type A/B 与 unrestricted 对照 | 候选集合和失败原因来自对应公式，不能互换 | `STANDARD + NEEDS_EXTERNAL_REFERENCE` |
| PRE-08 协议边界 | 合成 RAR/Msg3/Msg4 事件 | 只有跨消息约束成立才从 `preamble_detected` 升级 | `EXPERIMENT + NEEDS_VERIFICATION` |

在 PRE-01 至 PRE-03 未通过前，不要把现场峰值送入跨站 ToA/TDoA；在 PRE-08 未通过前，不要把前导索引命名为用户或 C-RNTI。

## 27. 证据分层与来源账本

| 内容 | 证据标签 | 来源 | 当前缺口 |
|---|---|---|---|
| 序列、循环移位、频域 DFT 与 PRACH 物理映射 | `STANDARD` | TS 38.211 §6.3.3.1/§6.3.3.2；[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|本地 38.211 笔记]] | Release/条款版本尚未在项目锁定 |
| format→`L_RA`/SCS/CP/重复段 | `STANDARD` | TS 38.211 Tables 6.3.3.1-1/2 | `NEEDS_EXTERNAL_REFERENCE`，不填精确表值 |
| root/shift→`preamble_index` | `STANDARD` | TS 38.211 §6.3.3.1、Tables 6.3.3.1-3 至 7 | `NEEDS_EXTERNAL_REFERENCE`，需版本化 fixture |
| RAR `RAPID` 与前导的关联边界 | `STANDARD` + `PERSONAL_NOTE` | TS 38.321 Random Access、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|RA 流程]] | 需真实 RAR/Msg3/Msg4 捕获 |
| 碰撞峰可分离条件与首径/最强峰选择 | `HYPOTHESIS` | 本项目检测设计 | 由仿真和现场样本验证，不升级为标准结论 |
| 接收 schema、峰保留和失败状态 | `PERSONAL_NOTE` | 项目主线 [[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]] | 需与实际代码字段对齐 |
| MATLAB `nrPRACH`/`nrPRACHDetect` 的签名、返回和多峰行为 | `EXPERIMENT` | [[5G-NR-Positioning/08-MATLAB代码/MATLAB 5G Toolbox API Map|MATLAB API Map]]、MathWorks 文档 | `NEEDS_EXTERNAL_REFERENCE`，须本机 `ver/help` 和最小调用 |

本页只把规范稳定的层次关系写成 `STANDARD`；所有精确数值、表格行、工具箱返回字段和现场性能均保留为 `NEEDS_EXTERNAL_REFERENCE` 或 `NEEDS_VERIFICATION`。
