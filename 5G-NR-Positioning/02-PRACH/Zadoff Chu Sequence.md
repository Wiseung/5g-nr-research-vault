---
title: Zadoff Chu Sequence
aliases:
  - Zadoff-Chu 序列
  - ZC 序列
  - NR PRACH 根序列
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - topic/sequence
  - process/correlation
source:
  - 3GPP TS 38.211
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]"
  - "[[5G-NR-Positioning/02-PRACH/Cyclic Shift|Cyclic Shift]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]"
  - "[[01-专题知识/信道估计与均衡/02 参考信号与导频设计|现有参考信号笔记]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]]"
---

# Zadoff Chu Sequence

## 1. 一句话定义

Zadoff–Chu（ZC）序列是恒包络、具有良好周期相关性质的复序列族，NR PRACH 用它构造根序列和不同循环移位的前导。

## 2. 为什么项目需要它

接收机可按根序列生成本地参考并进行相关检测，在低信噪比下发现前导、估计时延和诊断碰撞。根序列只说明序列族，不能直接说明 UE 或 C-RNTI。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 PRACH Configuration/Occasion 之后、Preamble 实例和 PRACH Detection 之前；检测结果再进入 RA-RNTI、RAR 和随机接入状态机。

## 4. 输入

- 序列长度 $L_{RA}$、逻辑 rootSequenceIndex 和实际根索引映射。
- 序列样点 $n$、循环移位/限制集合和实现精度。
- PRACH format 与版本化标准表。

## 5. 输出

- 根序列 $x_u[n]$ 及其归一化版本。
- 周期自相关/互相关参考值。
- 供循环移位、波形生成和匹配滤波使用的本地模板。

## 6. 关键参数

L_RA、根序列 u、根索引置换、序列奇偶长度公式、restricted set 和零相关区参数。L_RA=839 与短前导长度等选择不能凭经验硬编码，必须从配置和 TS 38.211 表格读取。

## 7. 时域位置

ZC 序列本身填入 PRACH 有效序列区，前后还有 CP/保护区；其样点时长由 L_RA、PRACH SCS 和采样率决定。相关时需先去除或正确建模 CP/保护区。

## 8. 频域位置

根序列通常先在 PRACH 频域资源上形成，再通过 IFFT/波形映射到时域；频域起点和 PRACH SCS 由 RO 配置决定，不等于普通 PUSCH 的 BWP 频点。

## 9. 数学原理

常见奇数长度形式可写为

$$
x_u[n]=\exp\left(-j\pi u n(n+1)/L_{RA}\right),\quad 0\le n<L_{RA}.
$$

偶数长度及根索引映射可能采用不同二次项；准确公式以 TS 38.211 为准。理想周期相关的主峰和低旁瓣是循环移位可分离的基础，但频偏、多径和非整数时延会破坏理想性质。

## 10. 3GPP 对应规范

- TS 38.211 §6.3.3.1：PRACH 序列生成、根序列和循环移位定义；§5.3.2 负责 PRACH OFDM 基带波形生成。奇偶长度、逻辑到物理根映射及表格需按 Release 核对，状态 NEEDS_EXTERNAL_REFERENCE。
- TS 38.211 §6.3.3.2：PRACH 序列到物理资源的映射；§5.3.2 负责 OFDM 基带波形生成。
- 相关字段：rootSequenceIndex、L_RA、zeroCorrelationZoneConfig、restrictedSetConfig。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHConfig：保存根序列和 L_RA 相关配置。
- nrPRACH：按配置生成 PRACH 序列。
- nrPRACHIndices：检查序列对应的资源网格位置。
- nrPRACHDetect：以生成的参考序列进行检测；函数内部的序列生成细节和版本差异需本机核验。

上述 API 均为 `NEEDS_EXTERNAL_REFERENCE` 的实现线索，不能替代对标准序列和本机输出的逐项核对。

## 12. 本项目中的用途

为每个候选 RO 生成与网络配置一致的本地模板，交给 [[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]；相关峰只能生成前导事件和 ToA 候选，必须继续通过 [[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]] 关联 C-RNTI。

## 13. 常见误区

- 把 ZC 根序列索引当成前导索引或 UE 标识。
- 忽略序列长度奇偶、根索引置换和 restricted set。
- 用非周期线性相关的结果直接套用理想零相关结论。
- 将恒包络误解为经过信道后仍无幅度变化。

## 14. 与相似概念的区别

ZC 是数学序列族；根序列是族中的一个基准；循环移位从根序列生成多个前导；PRACH Preamble 是映射到具体 RO 的实例；DM-RS/SRS 是不同物理过程的参考信号。

## 15. 代码实现注意事项

- 固定复数精度、相位符号和归一化方式，并在日志中记录。
- 对逻辑根索引到实际根序列的映射写单元测试。
- 用循环相关和已知移位真值测试整数/亚采样时延。
- 不要把本地生成器的默认采样率或 FFT 当作现场配置。

## 16. 待实验验证的问题

- MATLAB 生成的根序列与第三方设备参考序列是否同相位、同归一化。
- 不同 L_RA、restricted set 和根索引下的互相关旁瓣。
- CFO、采样偏差和多径对根序列判决的误差。
- 现场是否存在未记录的序列预旋转或硬件相位约定。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]、[[5G-NR-Positioning/02-PRACH/Cyclic Shift|Cyclic Shift]]、[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]。
- 旧笔记：[[01-专题知识/信道估计与均衡/02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别|PRACH 相关检测边界]]、[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]。

## 18. 变量字典：不要把索引压成一个字段

| 符号/字段 | 语义 | 作用域 | 可否互换 |
|---|---|---|---|
| `L_RA` | PRACH 序列长度 | 一个 format/序列族 | 否；不能由普通 UL SCS 推断 |
| `i` | logical root sequence index | 当前 RO 的根序列枚举 | 否；不是物理根序列号 |
| `u` | sequence number/physical root | ZC 公式和本地模板 | 否；须经过标准表映射 |
| `v` | 某个根下的 cyclic-shift ordinal | 当前根序列 | 否；不是传播时延 |
| `C_v` | 实际循环移位量，模 `L_RA` | 当前根序列 | 否；不是 `v` 或 TA |
| `preamble_index` | RO 内按标准顺序分配的编号 | 当前时频 RO | 否；跨 RO 不具全局身份 |
| `RO_t`, `RO_f` | Occasion 的时域/频域坐标 | 小区配置 | 否；决定资源和 RA-RNTI 上下文 |

最小可审计键应至少是

```js
(cell_id, config_id, RO_t, RO_f, preamble_index,
 logical_root_index, physical_root_u, shift_ordinal_v, C_v)
```

这里的 `logical_root_index` 和 `physical_root_u` 必须同时保存。长序列的根索引置换通常不是恒等映射；把 RRC 的 `prach-RootSequenceIndex` 直接写入 ZC 公式，是一种常见且难以从最终峰值反推的错误。

## 19. 长前导与短前导的边界

> [!warning] `STANDARD + NEEDS_EXTERNAL_REFERENCE`
> “长/短”由 PRACH format 对应的规范表决定，不是由文件名、普通 UL SCS 或波形持续时间的经验阈值决定。TS 38.211 的 format 表同时绑定 `L_RA`、`Δf_RA`、有效序列重复数、CP/保护长度和 restricted-set 支持。本文不复制任何 Release 的精确表值；锁定项目 Release 后，才把表行写入 `prach_snapshot`。

| 判断维度 | 长前导家族 | 短前导家族 |
|---|---|---|
| 设计目标 | 较大的覆盖/定时不确定度容忍，允许较长的序列和保护区 | 较短的时域占用，适配较高 PRACH SCS 和更密集的 Occasion |
| `L_RA` | 由长前导 format 表给出，常见资料中的数值仅可作导航 | 可能包含多个短序列长度，必须随 format 和 Release 读取 |
| `Δf_RA` | 通常低于短前导；不能用普通 PUSCH SCS 代替 | 由 format/`μ` 表绑定，不能仅凭 `L_RA` 猜测 |
| 波形窗口 | `N_u`、`N_CP`、重复段和保护区较长，窗口跨符号时要按表展开 | `N_u`、`N_CP` 和重复段较短，但不同 A/B/C format 仍有差异 |
| 受限集合 | 某些长 format 支持 restricted type A/B | 支持情况由表格决定，不能假设可用或不可用 |
| 检测实现 | 长/短必须使用不同的 FFT、CP、采样坐标和搜索窗口 | 不能把长前导参考重采样后当作短前导模板 |

工程上可将边界写成判别函数，而不是散落的 `if L_RA == ...`：

```js
family = lookup_format_family(format, release_tables)
assert family in {long, short}
waveform_profile = lookup(format, L_RA, delta_f_RA, N_u, N_CP,
                           guard_profile, restricted_set_support)
```

若只拿到 IQ 而没有 format，`family=unknown` 是正确状态。用“序列长度看起来像长前导”反推配置属于 `HYPOTHESIS`，不能直接进入标准合规或定位结果。

## 20. ZC 根序列的数学关系

令 `L = L_RA`，且 `u` 满足

$$
\gcd(u,L)=1.
$$

对 NR 中常见的奇数长度形式，根序列可写成

$$
x_u[i]=\exp\left(-j\pi u i(i+1)/L\right),
\qquad i=0,1,\ldots,L-1.
$$

若某一通用实现允许偶数长度，则二次项约定可能写成 $i^2$；这不是在 NR PRACH 中自行切换公式的许可，必须以对应 format 的 38.211 定义为准。数学实现应把相位公式作为配置字段记录：

```js
phase_law: "exp(-j*pi*u*i*(i+1)/L_RA)"
phase_sign: -1
index_origin: 0
normalization: unit_modulus_before_waveform_scaling
```

由指数形式可直接得到

$$
|x_u[i]|=1,
$$

所以“恒包络”是发送模板的序列性质，不表示经过多径、频偏、AGC、量化或 OFDM 窗口后的接收 IQ 仍然恒包络。对同一合法根的理想周期自相关，可用下式作为单元测试目标：

$$
R_{u,u}[m]=\sum_{i=0}^{L-1}x_u[i]x_u^*[(i-m)\bmod L]
\approx
\begin{cases}
L,&m\equiv0\pmod L,\\
0,&\text{otherwise}.
\end{cases}
$$

这里的“约等于”只允许来自浮点误差；若在无噪声、完整周期条件下出现明显旁瓣，应优先检查根合法性、相位符号、索引起点和相关方向。

## 21. 循环移位、频域相位与相关峰

根序列经过 `C_v` 得到候选序列：

$$
x_{u,v}[n]=x_u[(n+C_v)\bmod L].
$$

采用未归一化 DFT

$$
y_{u,v}[k]=\sum_{n=0}^{L-1}x_{u,v}[n]e^{-j2\pi kn/L},
$$

可得到时域循环移位对应的频域相位斜坡：

$$
y_{u,v}[k]=y_u[k]e^{+j2\pi kC_v/L}.
$$

若代码定义为 $x_u[(n-C_v)\bmod L]$，相位符号会反向；发送端和接收端必须共享同一约定。这个关系是很便宜的实现核验：同时比较时域循环移位结果和频域相位斜坡，能把“序列生成错”与“OFDM 映射错”分开。

对同一根的两个候选 `v_1`、`v_2`，理想周期相关峰的相对位置只与

$$
\Delta C=(C_{v_1}-C_{v_2})\bmod L
$$

有关。接收模型可抽象为

$$
r[n]=\sum_a \alpha_a x_{u,v}[(n-\tau_a)\bmod L]+w[n],
$$

因此相关峰观测位置是“循环移位 + 信道时延”的混合量。接收机若已经用候选 $x_{u,v}$ 做匹配，应记录候选模板下的残余时延；不能把原始峰索引直接当作 `C_v`，也不能把 `C_v/F_s` 直接当作传播时间。跨周期边界时必须先做模运算和 unwrap，再进入 [[5G-NR-Positioning/02-PRACH/Timing Estimation|Timing Estimation]]。

## 22. 根索引与前导索引的表驱动映射

标准定义的是“从配置起始 logical root 开始，按规定顺序取根和循环移位，直到得到一个 RO 所需的前导集合”。可复现实现应遵循以下层次：

1. 读取当前分支适用的 root 字段（普通 PRACH、BFR 或 MsgA 分支不能静默混用）。
2. 以该值作为 logical root index 的起点，按标准规定的循环顺序展开后续 logical index。
3. 用当前 `L_RA` 对应的 38.211 表把 logical index 映射成 physical root `u`。
4. 对每个 `u` 调用 unrestricted 或 restricted-set 的 `C_v` 生成器。
5. 使用标准规定的枚举顺序分配 `preamble_index`，达到本 RO 的候选上限后停止。

根索引置换表、每根可提供的移位数量和 RO 候选上限都是 `NEEDS_EXTERNAL_REFERENCE`。即使两个 Release 的字段名称相同，也不能假设表行相同。

建议把“规范顺序”封装成不可变函数，避免在业务代码里用整数除法猜测：

```python
def enumerate_preambles(snapshot, root_map, shift_table, standard_order):
    validate(snapshot.format, snapshot.L_RA, snapshot.restricted_set)
    logical_roots = cyclic_logical_roots(
        start=snapshot.logical_root_start,
        count=standard_order.max_root_scan,
    )
    per_root = []
    for i in logical_roots:
        u = root_map(snapshot.L_RA, i)       # table lookup, never identity by default
        shifts = shift_table(snapshot, u)     # C_v plus shift ordinal v
        per_root.append((i, u, shifts))

    candidates = []
    for i, u, v, C_v in standard_order(per_root):
        candidates.append({
            "preamble_index": len(candidates),
            "logical_root_index": i,
            "physical_root_u": u,
            "shift_ordinal_v": v,
            "cyclic_shift": C_v,
        })
        if len(candidates) == snapshot.max_preambles_per_ro:
            break
    assert_unique(candidates, keys=("physical_root_u", "cyclic_shift"))
    return candidates
```

`standard_order` 的测试向量必须来自锁定 Release；在没有向量时，代码可以输出候选表，但状态只能是 `NEEDS_EXTERNAL_REFERENCE`，不能宣称前导索引映射已验证。

## 23. 接收机数据结构与处理伪代码

序列层建议保存一个与波形层解耦的快照：

```js
sequence_snapshot:
  config_id: <immutable-config-id>
  release_or_toolbox_version: null
  format: <format-or-unknown>
  family: long|short|unknown
  L_RA: null
  delta_f_RA_hz: null
  logical_root_start: null
  logical_root_index: null
  physical_root_u: null
  shift_ordinal_v: null
  cyclic_shift_C_v: null
  restricted_set: unrestricted|A|B|unknown
  N_CS: null
  phase_convention: <explicit-formula-and-sign>
  sequence_normalization: <unit-or-waveform-scale>
  source_status: STANDARD|NEEDS_EXTERNAL_REFERENCE
```

每次相关检测的中间对象至少包含：`reference_hash`、`RO_t`、`RO_f`、`preamble_index`、`correlation_trace`、`peak_indices`、`residual_delay_samples`、`cfo_state`、`collision_status` 和 `failure_reason`。`reference_hash` 只用于发现配置或代码改变，不替代源文件和参数快照。

```text
读取 prach_snapshot 和 IQ 捕获
若 format/L_RA/根映射/N_CS 任一未知：输出 unknown_config，停止标准判决
展开合法 RO 和候选 (`u`, `C_v`, `preamble_index`)
对每个 RO:
    提取有效序列区，按同一相位和归一化生成本地模板
    对每个候选计算循环/滑动相关，保存完整 correlation_trace
    在峰筛选前保留峰值、旁瓣、峰宽和跨周期位置
    以候选模板解释残余时延，区分首径、最强峰和峰簇
    若多个候选峰不可分离，collision_status=ambiguous
    输出 sequence_event，不将其升级为 C-RNTI
```

## 24. 失败模式与诊断优先级

| 现象 | 更可能的序列层原因 | 建议先查什么 | 不应直接结论 |
|---|---|---|---|
| 全部无峰 | `L_RA`/format/根表错、频域资源错、窗口错 | 配置快照和参考哈希 | “没有 UE” |
| 峰在所有前导间错位 | 循环移位方向或 `preamble_index` 顺序错 | shift 表和标准向量 | “传播时延异常” |
| 同一根旁瓣很高 | 相位公式、长度或相关边界错 | 无噪声周期自相关 | “信道严重多径” |
| 仅 restricted set 失败 | 把 A/B 当 unrestricted，或 `d_u` 分支错 | restricted 类型、`N_CS` 来源 | “高速 UE 不可检测” |
| 长前导能检、短前导全失 | 误用 `N_u`/CP/采样率或 format 表 | family-specific waveform profile | “短前导功率低” |
| 峰跨窗口边界 | 模运算/CP 去除/unwrap 错 | 原始索引和 RO 起点 | “TA 已改变” |

## 25. 最小验证用例（仅设计，不是已运行结果）

| 用例 | 输入 | 通过条件 | 证据状态 |
|---|---|---|---|
| ZC-01 根序列不变量 | 每种待支持 `L_RA`、多个合法 `u` | 所有样点幅度接近 1；无噪声周期自相关主峰/旁瓣符合理论 | `EXPERIMENT + NEEDS_VERIFICATION` |
| ZC-02 移位等价 | 随机 `C_v`、正负移位实现 | 时域模移位与频域相位斜坡在浮点容差内一致 | `EXPERIMENT + NEEDS_VERIFICATION` |
| ZC-03 根表闭合 | 锁定 Release 的 root-map fixture | logical→physical 映射、候选顺序和参考哈希与 fixture 一致 | `STANDARD + NEEDS_EXTERNAL_REFERENCE` |
| ZC-04 长/短分支 | 每个 format family 的最小配置 | family 不混用；`N_u`/CP/窗口来自同一表行 | `EXPERIMENT + NEEDS_VERIFICATION` |
| ZC-05 已知时延 | 单根单移位、无噪声、整数/亚采样延迟 | 正确 `preamble_index`，残余时延与注入值闭合 | `EXPERIMENT + NEEDS_VERIFICATION` |
| ZC-06 碰撞 | 同一 RO 两个相同前导及两个可分离移位 | 相同前导标记不可分离；可分离移位保留多峰而非只留 argmax | `EXPERIMENT + NEEDS_VERIFICATION` |

用例通过前，不应把序列相关峰写入跨站 `toa_valid` 或用户关联表。通过后仍需分别验证 CFO、多径、设备群时延和 RAR 关联。

## 26. 证据分层与来源账本

| 断言/对象 | 证据类型 | 当前来源 | 状态与后续动作 |
|---|---|---|---|
| ZC 公式、循环移位和频域 DFT 接口 | `STANDARD` | TS 38.211 §6.3.3.1；本地 [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|38.211 笔记]] | `STANDARD + partial`；锁定 Release 后回填精确条款/表号 |
| format→`L_RA`/SCS/CP/重复段 | `STANDARD` | TS 38.211 Tables 6.3.3.1-1/2 | `NEEDS_EXTERNAL_REFERENCE`；不在本页硬编码表值 |
| logical root→physical `u` | `STANDARD` | TS 38.211 Tables 6.3.3.1-3 至 4B | `NEEDS_EXTERNAL_REFERENCE`；使用版本化 fixture |
| `N_CS` 与 restricted A/B 分支 | `STANDARD` | TS 38.211 §6.3.3.1、Tables 6.3.3.1-5 至 7 | `NEEDS_EXTERNAL_REFERENCE`；按 `L_RA`/format 读取 |
| “峰只能证明序列事件，不能给 C-RNTI” | `PERSONAL_NOTE` + `STANDARD` | [[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]] | 已作为项目边界；仍需 RAR/Msg3/Msg4 证据 |
| 某峰策略在碰撞/多径下最优 | `HYPOTHESIS` | 当前工程假设 | 不得写成标准事实；用 ZC-05/06 及检测实验验证 |
| MATLAB `nrPRACH*` 的实际输出和归一化 | `EXPERIMENT` | [[5G-NR-Positioning/08-MATLAB代码/MATLAB 5G Toolbox API Map|MATLAB API Map]] | `NEEDS_EXTERNAL_REFERENCE`；记录本机版本、输入维度和输出 |

本页的精确数值、表格行和 API 返回字段均遵守“先锁定 Release，再写入”的门槛。未完成核验时，`null`/`unknown` 比一个看似合理的默认值更有信息量。
