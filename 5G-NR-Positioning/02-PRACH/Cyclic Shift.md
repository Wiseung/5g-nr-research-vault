---
title: Cyclic Shift
aliases:
  - PRACH 循环移位
  - 循环移位前导
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - topic/sequence
  - topic/timing
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
related:
  - "[[5G-NR-Positioning/02-PRACH/Zadoff Chu Sequence|Zadoff Chu Sequence]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]"
---
# Cyclic Shift

## 1. 一句话定义

Cyclic Shift 是对 PRACH 根序列做模 $L_{RA}$ 循环位移的参数，用来构造多个可区分的前导并提供一定的时延容忍间隔。

## 2. 为什么项目需要它

它决定前导索引到本地参考序列的映射、相关峰的理想相对位置和零相关区保护。循环移位错一位会造成前导误判、RAPID 不匹配及后续 RA-RNTI 关联失败。

## 3. 它位于整个 5G 空口链路的什么位置

它位于 ZC 根序列生成与 Preamble 实例化之间；接收端根据配置枚举移位并检测，之后把前导索引送入 RAR/RAPID 关联。

## 4. 输入

- 根序列 $x_u[n]$、$L_{RA}$ 和逻辑前导索引。
- zeroCorrelationZoneConfig、$N_{CS}$、restrictedSetConfig。
- 小区/载波配置和 PRACH format。

## 5. 输出

- 循环移位值 $C_v$ 与前导索引的映射表。
- 每个候选前导的本地序列。
- 预期相关峰间隔和碰撞/不可分离标记。

## 6. 关键参数

$N_{CS}$（零相关区相关循环移位间隔）、$C_v$、$L_{RA}$、highSpeedFlag/restricted set、根序列可用数量和前导总数。$N_{CS}$ 的标准表和高速场景修正规则需按 TS 38.211/38.213 版本核对。

## 7. 时域位置

循环移位在周期序列域表现为相关峰的循环位置；传播时延可能使峰跨越周期边界。检测窗口必须覆盖有效循环相关区，不能把循环位移对应的相对位置误当绝对 ToA。

## 8. 频域位置

循环移位参数不改变 RO 的频域起点，但会改变映射到时域的相位/循环位置。根序列、移位和频域 Occasion 要作为独立字段保存。

## 9. 数学原理

对根序列 $x_u[n]$，循环移位实例可写为

$$
x_{u,v}[n]=x_u[(n+C_v)\bmod L_{RA}].
$$

在理想同步和无多径条件下，移位间隔至少为 $N_{CS}$ 时相关峰可分离；实际可用移位数还受根序列长度、restricted set 和传播时延范围限制。该简式不替代标准的 $C_v$ 生成表。

## 10. 3GPP 对应规范

- TS 38.211 §6.3.3.1：循环移位、$N_{CS}$ 和前导生成；§5.3.2 负责 PRACH OFDM 基带波形生成。精确公式/表格按 Release 核对，状态 NEEDS_EXTERNAL_REFERENCE。
- TS 38.213 §8：前导发送和 Occasion 约束。
- 相关字段：zeroCorrelationZoneConfig、restrictedSetConfig、preamble index。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHConfig：设置零相关区和 restricted set 相关属性。
- nrPRACH：生成给定前导的参考序列。
- nrPRACHIndices：验证前导在 RO 的资源位置。
- nrPRACHDetect：返回前导索引，但移位表和多峰解释需用配置对象及自定义日志复核。

以上函数名是 API 线索，签名、属性和 Release 行为均标记为 `NEEDS_EXTERNAL_REFERENCE`，需在本机核验。

## 12. 本项目中的用途

将检测峰映射到唯一的候选前导索引和 preamble_event，供 [[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]] 计算和 [[5G-NR-Positioning/02-PRACH/RAR|RAR]] RAPID 匹配；它只提供序列层证据，不直接产生 C-RNTI。

## 13. 常见误区

- 把循环移位值当传播时延或 TA 命令。
- 假定所有根序列都能提供相同数量的移位。
- 在高速/受限集合场景仍使用普通 N_CS 表。
- 忽略周期边界、峰折返和多径峰的混淆。

## 14. 与相似概念的区别

循环移位是序列构造参数；传播时延是信道观测量；TA 是 RAR 下发的 MAC 命令；前导索引是网络层用于 RAPID 匹配的编号；它们数值上可能相关，但语义不能互换。

## 15. 代码实现注意事项

- 生成表时同时保存 root、$C_v$、$N_{CS}$、前导索引和 restricted set。
- 对模运算、正负移位方向和 0/1 基索引写双向测试。
- 对峰跨周期边界做 unwrap，再估计传播时延。
- 将不可分离移位标为 ambiguous，不强行选择最近序列。

## 16. 待实验验证的问题

- 当前网络 zeroCorrelationZoneConfig 和 restrictedSetConfig 的真实值。
- 设备相关器采用的移位方向、起始相位和峰索引约定。
- 多径/大时延下不同 $C_v$ 的可分离门限。
- 循环移位候选数与现场前导碰撞率的关系。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/Zadoff Chu Sequence|Zadoff Chu Sequence]]、[[5G-NR-Positioning/02-PRACH/PRACH Preamble|PRACH Preamble]]、[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]、[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]。
- 旧笔记：[[01-专题知识/信道估计与均衡/02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别|PRACH 相关检测边界]]、[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]。

## 18. 先区分四个“移位”量

| 名称       | 符号/字段 | 语义                                | 不能替代的量                       |
| ---------- | --------- | ----------------------------------- | ---------------------------------- |
| 根序列     | `u`     | ZC 相位二次项中的物理根号           | logical root index、preamble index |
| 移位序号   | `v`     | 某个根的候选序列 ordinal            | `C_v`、传播时延                  |
| 循环移位量 | `C_v`   | 在长度`L_RA` 的序列域内取模的偏移 | TA、ToA、采样点                    |
| 传播时延   | `tau`   | 信道造成的到达延迟                  | `C_v`、RAR TA                    |

发送模板采用哪一个正负方向必须写入配置。若定义为

$$
x_{u,v}[n]=x_u[(n+C_v)\bmod L_{RA}],
$$

则采用未归一化 DFT 时有

$$
y_{u,v}[k]=y_u[k]e^{+j2\pi kC_v/L_{RA}}.
$$

若代码使用 `(n-C_v) mod L_RA`，频域相位斜坡符号随之反向。接收机不能只比较幅度峰值来掩盖这个约定差异；应在序列单元测试中同时比较复数向量、相关相位和频域相位斜坡。

## 19. unrestricted set：等间隔只是一个分支

在 unrestricted set 且 `N_CS != 0` 时，标准公式可抽象为

$$
C_v=vN_{CS},\qquad
v=0,1,\ldots,\left\lfloor\frac{L_{RA}}{N_{CS}}\right\rfloor-1.
$$

当 `N_CS = 0` 时，该分支只产生零循环移位。上式描述的是移位集合，不等于“每个根都能提供同样多的前导”：候选数量仍受 `L_RA`、根索引、每 RO 前导上限和其他配置约束。

`zeroCorrelationZoneConfig`（以及 type-2/MsgA 对应字段）只是高层索引，必须先按 `L_RA`、PRACH SCS 和 set 类型查到 `N_CS`。不要把字段值本身当成样点间隔，也不要把一个 format 的 `N_CS` 表复制到另一个 format。

## 20. restricted type A/B：根相关的受限集合

受限集合的目的不是减少“随机性”，而是在特定移动性/时延条件下控制可用循环移位，避免不同候选的相关峰落入彼此保护区。与 unrestricted set 相比：

- `C_v` 不一定是 `v*N_CS` 的等差序列。
- 可用移位数量可能随 physical root `u` 改变。
- 需要先由 `u` 求模逆和距离参数，再进入 type A/B 的分段公式。
- 某些 format 不支持 restricted set；是否支持必须读 format 表。

标准中常用的中间量可写成：

$$
q=\min\{q\ge0:(qu)\bmod L_{RA}=1\},
$$

$$
d_u=
\begin{cases}
q,&0\le q<L_{RA}/2,\\
L_{RA}-q,&\text{otherwise}.
\end{cases}
$$

随后由 `d_u`、`N_CS` 和 set type 计算 `n_shift^RA`、`d_start`、`n_group^RA` 等量，再生成 `C_v`。type A/B 的分段边界和整除/取整细节属于 TS 38.211 的规范公式；本页不复制整段 Release 表达式，避免在版本变化时留下半正确实现。

推荐的实现接口是：

```text
restricted_parameters(L_RA, u, N_CS, set_type, release_tables)
    -> {d_u, n_shift_RA, d_start, n_group_RA, valid_ranges}
restricted_shifts(parameters)
    -> [(v, C_v), ...]
```

若 `set_type`、`N_CS` 或对应表缺失，应返回 `unknown_config`，而不是悄悄调用 unrestricted 公式。`d_u` 的计算也要检查 `gcd(u,L_RA)=1`；没有模逆时，根索引本身已不满足序列生成前提。

## 21. 长前导与短前导对移位的影响

> [!warning] ⚠️ `STANDARD + NEEDS_EXTERNAL_REFERENCE`
> 长/短前导的 `L_RA`、`Δf_RA`、CP/保护时长和 restricted-set 支持由 TS 38.211 format 表绑定。下表只说明工程边界，不提供任何 Release 的精确 `N_CS` 或长度值。

| 维度            | 长前导                                                   | 短前导                                         |
| --------------- | -------------------------------------------------------- | ---------------------------------------------- |
| 序列域          | 长序列 family，循环位置对应的物理时间尺度更长            | 短序列 family，可能有多种长度和 format         |
| `N_CS` 查表键 | 至少包含长 format、SCS、zero-correlation 配置和 set type | 还要包含短 format/numerology；不能沿用长前导表 |
| 受限集合        | 部分 format 可用 type A/B                                | 支持情况必须逐行核对，不能凭“短”字样判断     |
| 检测窗口        | CP、重复段和 guard 可能跨较长采样窗口                    | 窗口更短，错一个符号/采样率就可能整体错位      |
| 定时保护        | 通常需要更大的传播时延/覆盖容忍                          | 需要在较短窗口内满足时延和多径保护             |

因此 `C_v` 的数值只能在“同一 `format`、同一 `L_RA`、同一 `N_CS` 表和同一 set type”内比较。跨长/短前导直接比较 `C_v` 大小没有物理意义。

## 22. 循环移位与相关峰/时延的关系

以候选模板做循环相关：

$$
z_{u,v}[\ell]=\sum_{n=0}^{L_{RA}-1}r[n]x_{u,v}^*[(n-\ell)\bmod L_{RA}].
$$

若接收信号只有一个路径，峰的位置是候选模板定义下的残余时延；若用公共根模板而未扣除 `C_v`，观测位置会把循环移位和传播时延叠加起来。

> [!note] ✏️ `HYPOTHESIS`（工程坐标模型）
> 下式只用于把循环序列坐标与物理时间坐标分开记账，不是 3GPP 的 ToA 定义；`T_seq` 必须由具体 format、SCS、IFFT 和采样率核验。

抽象地写：

$$
\tau_{obs}=\left(C_vT_{seq}+\tau_{channel}\right)\bmod(L_{RA}T_{seq}),
$$

其中 `T_seq` 是序列域索引映射到物理时域的单位，须由 PRACH SCS、IFFT 和采样率共同确定。它不等于任意采集设备的 `1/F_s`，所以 `C_v/F_s` 不是合法的 ToA 换算。

工程上的可分离性判据可以先写成假设：

$$
|\Delta C|T_{seq}
>\tau_{spread}+\tau_{uncertainty}
$$

但这不是 3GPP 的检测门限。`tau_spread`、CFO、采样时钟偏差、滤波器群时延和峰估计方法都要通过实验估计。跨周期边界时先计算模差，再按已知 RO 起点 unwrap；否则一个真实晚到峰可能被标成负时延。

## 23. 碰撞和不可分离情形

| 场景                         | 序列层现象                            | 应输出的状态                   | 后续可用证据                 |
| ---------------------------- | ------------------------------------- | ------------------------------ | ---------------------------- |
| 同一 RO、同一根、同一`C_v` | 一个叠加峰，功率为多用户叠加          | `collision_unresolvable`     | 空间阵列、功率轨迹、RAR/Msg3 |
| 同一 RO、同一根、不同`C_v` | 可能多峰，也可能因时延/多径重叠成峰簇 | `separable` 或 `ambiguous` | 全相关轨迹、峰间距、信道模型 |
| 同一 RO、不同根              | 根间互相关旁瓣干扰                    | `cross_root_interference`    | 根候选重算、CFO/频域泄漏分析 |
| 不同`RO_t`/`RO_f`        | 资源上可分离                          | 分别建事件                     | RO 坐标、RA-RNTI 上下文      |
| restricted set 下缺少某移位  | 候选表不含该`C_v`                   | `invalid_candidate`          | 配置/Release 表核对          |

同一前导的碰撞不是“相关器不够聪明”就能解决的问题。若没有额外天线、功率差、重复观测或后续协议消息，接收机必须保留不可分离结论，不能为了填满用户列表而复制峰。

## 24. 前导索引映射与移位表的接口

循环移位模块只负责返回每个根的合法 `(v,C_v)`，不负责决定最终 `preamble_index`。两者的接口应明确：

```text
shift_table(snapshot, physical_root_u)
    -> [{shift_ordinal_v, cyclic_shift_C_v}, ...]

preamble_order(logical_root_rows, standard_rule)
    -> ordered tuples (logical_i, u, v, C_v)

assign_preamble_index(ordered_tuples)
    -> preamble_index + immutable candidate row
```

这能防止三个常见错误：

1. 把 `zeroCorrelationZoneConfig` 直接当 `C_v`。
2. 对 restricted set 仍假定每根有固定的 `N_CS` 个移位。
3. 用 `preamble_index % N_CS` 反推 `v`，却没有保存真实的移位表。

候选表至少要通过 `(physical_root_u, cyclic_shift_C_v)` 唯一性检查，并记录“使用了哪一版 root-map/N_CS 表”。标准规定的每 RO 候选上限、根遍历顺序和 0/1 基索引都是 `NEEDS_EXTERNAL_REFERENCE`。

## 25. 接收机数据结构

```js
cyclic_shift_candidate:
  config_id: <immutable-config-id>
  release_or_toolbox_version: null
  format: <format-or-unknown>
  family: long|short|unknown
  L_RA: null
  delta_f_RA_hz: null
  logical_root_index: null
  physical_root_u: null
  restricted_set: unrestricted|A|B|unknown
  zero_correlation_zone_config: null
  N_CS: null
  shift_ordinal_v: null
  cyclic_shift_C_v: null
  root_map_revision: null
  shift_table_revision: null
  phase_sign: -1
  source_status: STANDARD|NEEDS_EXTERNAL_REFERENCE

cyclic_shift_observation:
  event_id: <capture-and-ro-key>
  candidate_ref: <cyclic-shift-candidate-id>
  raw_peak_index: null
  residual_peak_index: null
  unwrapped_delay_samples: null
  correlation_peak: null
  peak_width: null
  neighboring_peaks: []
  collision_status: none|possible|ambiguous|unresolvable
  timing_status: raw|relative|calibrated|unknown
  failure_reason: null
```

`raw_peak_index` 是相关数组坐标，`residual_peak_index` 是扣除候选 `C_v` 后的坐标；两者不能覆盖写入同一字段。`timing_status=calibrated` 需要 [[5G-NR-Positioning/02-PRACH/Timing Estimation|Timing Estimation]] 的硬件/滤波/时钟证据，循环移位模块本身只能提供相对位置。

## 26. 生成和检测伪代码

```python
def generate_shifts(snapshot, u, tables):
    validate_gcd(u, snapshot.L_RA)
    N_CS = tables.n_cs(snapshot.release, snapshot.format,
                       snapshot.L_RA, snapshot.zero_corr,
                       snapshot.restricted_set)
    if snapshot.restricted_set == "unrestricted":
        if N_CS == 0:
            return [(0, 0)]
        return [(v, v*N_CS)
                for v in range(floor(snapshot.L_RA/N_CS))]

    if snapshot.restricted_set not in {"A", "B"}:
        return unknown_config("unsupported restricted set")
    q = smallest_nonnegative_mod_inverse(u, snapshot.L_RA)
    d_u = q if q < snapshot.L_RA/2 else snapshot.L_RA-q
    params = tables.restricted_parameters(
        snapshot.release, snapshot.L_RA, u, d_u, N_CS,
        snapshot.restricted_set)
    return tables.restricted_shifts(params)

def explain_peak(raw_peak, candidate, seq_time_unit):
    expected = candidate.cyclic_shift_C_v
    residual = modulo_difference(raw_peak, expected, candidate.L_RA)
    return {
        "raw_peak_index": raw_peak,
        "residual_peak_index": residual,
        "relative_delay": residual * seq_time_unit,
    }
```

`tables.restricted_parameters` 和 `tables.preamble_order` 必须由锁定 Release 的标准实现或经过核验的 fixture 提供。若它们返回 `unknown_config`，上层检测器应保留 IQ 和相关轨迹并停止索引判决，而不是用“最近的合法移位”强行修正。

## 27. 失败模式与排查顺序

| 症状                                   | 首先检查                              | 典型根因                           | 不应下的结论     |
| -------------------------------------- | ------------------------------------- | ---------------------------------- | ---------------- |
| 所有候选都偏同一方向                   | `+C_v`/`-C_v`、DFT 符号、索引原点 | 移位方向不一致                     | UE 时延都相同    |
| `N_CS=0` 仍生成多组移位              | zero-correlation 表查找               | 把字段值当数量                     | 网络配置非法     |
| unrestricted 正常、A/B 全失败          | `d_u`、分段参数和 set type          | 用错 restricted 公式               | 高速场景无前导   |
| 每个根候选数都一样                     | 候选表统计                            | 忽略 root-dependent restricted set | 相关器漏峰       |
| 峰落在周期另一端                       | modulo/unwrap 和 RO 起点              | 循环坐标被当线性坐标               | TA 突然跳变      |
| 不同根峰互相污染                       | 根间旁瓣、CFO、频域泄漏               | 把低旁瓣当正交                     | 必然是多用户碰撞 |
| `preamble_index` 与 `C_v` 无法互查 | 保存字段/版本                         | 只存编号未存表                     | 标准没有映射     |

## 28. 最小验证用例（设计稿）

| 用例                    | 构造                                                         | 通过条件                                        | 当前状态                                |
| ----------------------- | ------------------------------------------------------------ | ----------------------------------------------- | --------------------------------------- |
| CS-01 模移位组合        | 先移`C_1` 再移 `C_2`，与一次 `(C_1+C_2) mod L_RA` 对照 | 复数序列逐点一致，正负方向均有明确约定          | `EXPERIMENT + NEEDS_VERIFICATION`     |
| CS-02 DFT 相位斜坡      | 同一根的时域移位和频域相位实现                               | 误差在浮点容差内，符号反向时测试应失败          | `EXPERIMENT + NEEDS_VERIFICATION`     |
| CS-03 unrestricted 边界 | `N_CS=0`、非零 `N_CS`、整除/非整除的 `L_RA`            | 候选数量和`C_v` 集合符合公式，零分支不多生成  | `STANDARD + NEEDS_EXTERNAL_REFERENCE` |
| CS-04 restricted 根依赖 | 固定`N_CS`，改变合法 `u`，分别跑 A/B                     | 输出可重复、根相关数量/范围来自标准公式         | `STANDARD + NEEDS_EXTERNAL_REFERENCE` |
| CS-05 索引闭环          | shift-table + root-map fixture                               | `preamble_index -> (u,C_v) -> index` 双向闭合 | `STANDARD + NEEDS_EXTERNAL_REFERENCE` |
| CS-06 周期边界          | 注入接近 0 和接近`L_RA` 的峰                               | unwrap 后相对时延连续，不出现符号翻转           | `EXPERIMENT + NEEDS_VERIFICATION`     |
| CS-07 碰撞              | 同一/不同`C_v` 的双用户叠加                                | 同移位标不可分离，不同移位保留多峰/歧义         | `EXPERIMENT + NEEDS_VERIFICATION`     |
| CS-08 长短隔离          | 各 family 的 format fixture                                  | 不跨 family 复用`N_CS`、CP 或采样时间单位     | `EXPERIMENT + NEEDS_VERIFICATION`     |

这些用例只验证序列和索引层。即使全部通过，也不能替代真实 CFO、多径、采集群时延和 RAR/Msg3 协议关联验证。

## 29. 证据分层与来源账本

| 断言/实现                                      | 证据标签          | 来源                                                                       | 当前状态/后续动作                                   |
| ---------------------------------------------- | ----------------- | -------------------------------------------------------------------------- | --------------------------------------------------- |
| `x_{u,v}` 的循环移位关系与 unrestricted 公式 | `STANDARD`      | TS 38.211 §6.3.3.1                                                        | `STANDARD + partial`；锁定 Release 后回填精确版本 |
| `zeroCorrelationZoneConfig -> N_CS`          | `STANDARD`      | TS 38.211 Tables 6.3.3.1-5 至 7                                            | `NEEDS_EXTERNAL_REFERENCE`；本页不写表值          |
| restricted type A/B 的`d_u`/分段公式         | `STANDARD`      | TS 38.211 §6.3.3.1                                                        | `NEEDS_EXTERNAL_REFERENCE`；实现需版本化 fixture  |
| format、`L_RA`、SCS、CP 和 set 支持          | `STANDARD`      | TS 38.211 Tables 6.3.3.1-1/2                                               | `NEEDS_EXTERNAL_REFERENCE`；长短边界仅写原则      |
| 峰可分离判据和首径/最强峰策略                  | `HYPOTHESIS`    | 本项目检测设计必须由 [[03-仿真与实验/5G定位/仿真：PRACH 检测与 RA 事件关联 |                                                     |
| 字段 schema、状态和失败分类                    | `PERSONAL_NOTE` | [[5G-NR-Positioning/02-PRACH/PRACH DetectionPRACH Detection]]、[[5G-NR-Positioning/02-PRACH/Timing Estimation                           |                                                     |
| MATLAB API 的`N_CS`/移位输出行为             | `EXPERIMENT`    | [[5G-NR-Positioning/08-MATLAB代码/MATLAB 5G Toolbox API MapMATLAB API Map]]                                                                           |                                                     |
| 循环移位峰与跨站 ToA/TDoA 的可用性             | `EXPERIMENT`    | [[5G-NR-Positioning/05-定位观测量/Timing ObservationTiming Observation]]                                                                           |                                                     |

本页的 `N_CS`、根表、restricted-set 候选数量和 API 字段均保持未决状态，直到项目明确 Release、设备配置和验证向量。这样可以避免把一个数值相同但语义不同的移位、时延或 TA 混在一起。
