---
title: Search Space
aliases:
  - 搜索空间
  - PDCCH 搜索空间
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - topic/search-space
  - process/blind-detection
  - evidence/3gpp
source:
  - 3GPP TS 38.213
  - 3GPP TS 38.331
  - 用户项目流程说明
related:
  - "[[03-PDCCH/CORESET|CORESET]]"
  - "[[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]"
  - "[[03-PDCCH/RNTI|RNTI]]"
  - "[[01-NR基础/SSB PBCH MIB]]"
---

# Search Space

> [!abstract] 项目主线
> Search Space 定义何时监测某个 CORESET、哪些聚合等级和候选可被尝试，以及该搜索分支服务于公共还是 UE 专用控制上下文；它是把“控制资源集合”变成有限候选列表的规则层。

## 1. 一句话定义

Search Space 是 PDCCH 监测配置，描述关联 CORESET 的监测时机、候选数量/聚合等级和 RNTI/控制用途约束。

## 2. 为什么项目需要它

被动接收机不能只在 CORESET 内任意遍历所有 CCE。Search Space 提供候选枚举边界，直接决定 PDCCH 盲搜的漏检风险、误检数量和计算量。对于 C-RNTI 驱动的项目，它还把 UE 专用候选与 RA-RNTI、SI-RNTI 等公共候选分开，避免错误地把公共 DCI 归给目标 UE。

## 3. 它位于整个 5G 空口链路的什么位置

```text
RRC SearchSpace + CORESET
  -> 监测周期/偏移/符号
  -> 聚合等级与候选枚举
  -> CCE/REG/RE 解映射
  -> DCI Polar/CRC + RNTI 检查
  -> PDSCH/PUSCH resource_snapshot
```

Search Space 位于 CORESET 之后、PDCCH 候选解码之前；它不包含 DCI 字段，也不等于 RNTI。

## 4. 输入

| 输入 | 用途 |
|---|---|
| `SearchSpace` 配置和标识 | 关联 CORESET、公共/专用上下文 |
| 监测周期、偏移、持续符号/时隙 | 生成 monitoring occasion |
| 每个聚合等级的候选数量 | 枚举 candidate index |
| CORESET 的 CCE 数及映射 | 将候选转成 RE 索引 |
| RNTI 类型/候选池和 DCI 格式 | CRC 掩码及字段解释 |
| 帧/时隙/TDD 状态 | 过滤当前可监测时机 |

项目需要保留配置版本和生效窗口；RRC 更新后旧搜索空间不可静默沿用。

## 5. 输出

对每个监测时机输出候选清单：

```js
search_space_id: null
coreset_id: null
monitoring_occasion: ""
common_or_ue_specific: "common|ue_specific|unknown"
aggregation_levels: []
candidates:
  - aggregation_level: null
    candidate_index: null
    first_cce: null
    cce_indices: []
    rnti_contexts: []
candidate_generation_status: "ready|partial|NEEDS_VERIFICATION"
```

候选清单是 [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]] 的唯一物理输入边界之一；候选之外的 RE 不应被当作“未检测到的 PDCCH”。

## 6. 关键参数

| 参数 | 说明 |
|---|---|
| `searchSpaceId` / `controlResourceSetId` | 配置关联键 |
| `monitoringSlotPeriodicityAndOffset` | 监测周期/偏移 |
| `duration`/监测符号 | 时域监测窗口 |
| 聚合等级 `L` | 每候选使用的 CCE 数 |
| `nCandidates[L]` | 每个聚合等级的候选数量 |
| common/UE-specific | 公共或专用控制用途 |
| DCI format/RNTI context | 候选的语义与 CRC 假设 |
| BWP/时隙状态 | 坐标和 TDD 过滤 |

精确候选数、监测规则和 RNTI 适用范围依赖目标 Release 与 RRC 配置，均不得从本页默认补齐。

## 7. 时域位置

Search Space 将候选绑定到离散的 monitoring occasion。实现应先按周期/偏移生成候选时隙，再检查 CORESET 所在符号是否为可用下行或经配置允许的灵活符号。记录 `frame/slot/symbol_set/occasion_index`，并区分 `not_monitored`、`no_candidate` 与 `candidate_decode_fail`。

## 8. 频域位置

Search Space 本身通常不重新定义 PRB 位图，而是引用 CORESET 的频域资源；聚合等级和候选索引选择其中一段 CCE，再经 [[03-PDCCH/CCE REG|CCE REG]] 映射到 RE。不要把搜索空间 ID 当作频域起点，也不要跳过 BWP/Point A 坐标转换。

## 9. 数学原理

令时隙 $t$ 的监测时机指示为 $I_t$，聚合等级集合为 $\mathcal{L}$，每个等级的候选数为 $M_L$。候选集合可写成：

$$
\mathcal{C}_t
=\bigcup_{L\in\mathcal{L}}\bigcup_{m=0}^{M_L-1}
\{(t,L,m,\mathrm{CCE}_{t,L,m})\}\quad\text{if }I_t=1.
$$

每个候选的首 CCE 由规范规定的哈希/置换和 RNTI、时隙、Search Space 参数共同决定，可抽象为：

$$
\mathrm{firstCCE}=f(\mathrm{RNTI},t,L,m,\theta_{SS},\theta_{CORESET}).
$$

具体 $f$ 的公式、索引基准和候选上限必须按适用 TS 38.213 Release 核验，当前标为 `NEEDS_EXTERNAL_REFERENCE`。

候选接受仍需满足：

$$
h\in\mathcal{C}_{valid}
\Longleftrightarrow
h\in\mathcal{C}_t,\ q_h=1,\ \mathrm{field\_valid}=1.
$$

## 10. 3GPP 对应规范

| 规范 | 相关内容 | Clause/字段状态 |
|---|---|---|
| TS 38.213 | PDCCH 搜索空间、监测时机、候选与 UE 控制接收 | 控制信道接收相关 §10 范围；候选公式子条款 `NEEDS_EXTERNAL_REFERENCE` |
| TS 38.331 | `SearchSpace`、监测周期/偏移、候选数量等 RRC 字段 | ASN.1 字段和版本需外部核验 |
| TS 38.211 | 候选 CCE/REG 到 PDCCH RE 的物理映射 | PDCCH 相关 §7.3.2；`NEEDS_EXTERNAL_REFERENCE` |

本地 [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|TS 38.213]] 明确了“配置 -> 候选 -> CRC/RNTI 判决”的职责链，但没有提供项目锁定 Release 的全部候选表。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

| 函数 | 用途 | 状态 |
|---|---|---|
| `nrPDCCHSpace` | 现有项目笔记引用的候选空间/DM-RS 索引示例入口 | `NEEDS_EXTERNAL_REFERENCE` |
| `nrPDCCHDecode` | 对枚举候选执行 PDCCH 软处理 | `NEEDS_EXTERNAL_REFERENCE` |
| `nrDCIDecode` | 对候选 DCI 做率恢复和 CRC 判决 | `NEEDS_EXTERNAL_REFERENCE` |

本 Vault 没有已验证的 MATLAB Search Space 对象/API 版本。运行前应保存 `search_space_id`、候选数量、工具箱版本和函数输入输出维度。

## 12. 本项目中的用途

Search Space 是 C-RNTI 到 PDCCH 的候选路由：

1. 从 [[02-PRACH/Random Access Procedure|Random Access Procedure]] 得到 RA-RNTI/临时标识或 C-RNTI 候选。
2. 区分公共 Search Space 和 UE-specific Search Space，选择相应 RNTI 上下文。
3. 为每个 monitoring occasion 生成 `(L, candidate_index, first_CCE)`。
4. 交给 [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]，再由 [[03-PDCCH/DCI|DCI]] 驱动 [[04-PDSCH/PDSCH|PDSCH]]。
5. 将“未监测”与“监测但解码失败”分开，避免把配置缺失误判为无线链路差。

## 13. 常见误区

- 把 CORESET 内所有 CCE 都当成每个时隙的候选，忽略周期/偏移和 `nCandidates`。
- 把 UE-specific Search Space 的 RNTI 规则套到 RA-RNTI/SI-RNTI 公共候选。
- 将候选索引从 0/1 基准错误转换，导致正确 DCI 资源整体偏移。
- 只记录 CRC 通过，不记录 `not_monitored`、`no_candidate` 和 `decode_fail`。
- 在 RRC 配置更新或 BWP 切换后继续使用旧 Search Space。

## 14. 与相似概念的区别

| 概念 | 关注点 | 区别 |
|---|---|---|
| CORESET | 物理控制资源区域 | Search Space 引用它，不决定监测时机 |
| Candidate | 某一时机/聚合等级的一组 CCE | Search Space 产生候选集合 |
| RNTI | CRC 掩码/控制上下文 | 不是候选位置规则本身 |
| PDCCH Blind Decoding | 对候选执行信号处理和判决 | Search Space 只负责候选生成 |
| Monitoring Occasion | 某个实际监测时机 | 是 Search Space 的时间实例 |

## 15. 代码实现注意事项

- 先生成并缓存每个 `config_id + slot` 的候选清单，再执行信号处理，便于复现和复杂度统计。
- 候选生成函数输入应显式包含 RNTI 上下文、时隙和 CORESET；不要从全局变量隐式读取。
- 对每个聚合等级验证 `first_CCE + L <= N_CCE`，越界候选标为 `invalid_candidate`。
- 保留候选生成公式所需的哈希中间值，便于定位 RNTI/时隙位序错误。
- 候选数、监测周期和 RNTI 池大小变化时，单独记录计算预算和误检统计。

## 16. 待实验验证的问题

- [ ] 用已知 RRC 配置逐时隙生成候选，并与 MATLAB/参考实现的索引逐项比对。
- [ ] 分别测试 common 与 UE-specific Search Space，确认 RNTI 类型和 DCI 格式约束。
- [ ] 注入错误周期/偏移、错误聚合等级和错误 candidate index，验证失败分类。
- [ ] 在有限 C-RNTI 候选池下统计候选数、CRC 通过数、字段有效数和尾延迟。
- [ ] 验证 BWP 切换、TDD 灵活符号和 RRC 更新时 Search Space 缓存正确失效。

## 17. Common Search Space 与 UE-specific Search Space

Search Space 不是只有一个“候选数量”字段。至少要先判定它服务于公共控制还是 UE 专用控制，再决定 RNTI、DCI 格式和候选哈希的输入：

| 类型 | 典型用途 | RNTI/格式上下文 | 被动监测策略 |
|---|---|---|---|
| Common Search Space (CSS) | 初始接入、系统信息、寻呼、RAR、公共时隙格式等 | SI-RNTI、RA-RNTI、P-RNTI 等公共标识；具体格式依配置 | 先由 MIB/SIB/RA 事件缩小候选，按窗口保留公共事件 |
| UE-specific Search Space (USS) | 已建立上下文后的专用调度 | C-RNTI、CS-RNTI 等专用标识；格式与 BWP/过程相关 | 绑定 C-RNTI 生命周期和 `config_id`，做跨时隙连续性 |
| 特殊/恢复分支 | BFR、重配置或其他专用过程 | 由触发原因和 RRC/MAC 状态决定 | 不能把 CSS/USS 默认规则外推 |

CSS/USS 的名称只描述配置语境；它不保证候选上一定有信号，也不直接证明 RNTI 已确认。具体 SearchSpace 类型、允许的 DCI 格式和适用 RNTI 需回到目标 Release 的 TS 38.213/38.331。

初始接入的 SearchSpace0 属于公共控制支路；MIB 到 SearchSpace0、SI-RNTI 与 SIB1 的完整关系见 [[01-NR基础/SSB PBCH MIB]]。这条支路不能替代后续由 RA/C-RNTI 上下文进入 USS 的用户专属流程。

## 18. Monitoring Occasion 的生成

建议把“是否监测”和“监测哪些候选”拆成两个纯函数：

```python
occasion = is_monitoring_slot(frame, slot, periodicity_offset,
                               duration, monitoring_symbols)
if occasion:
    candidates = generate_candidates(coreset, search_space,
                                      aggregation_levels, rnti_context)
else:
    emit(not_monitored)
```

逐时隙记录以下字段，才能在现场区分配置问题和无线问题：

| 字段 | 说明 |
|---|---|
| `periodicity_offset` | 周期/偏移原值及解码版本 |
| `duration` | Search Space 生效的连续时隙范围（若配置提供） |
| `monitoring_symbols` | 时隙内允许监测的符号位图/解析结果 |
| `frame_slot` | 系统帧、slot、numerology |
| `tdd_direction` | `DL`、`flexible`、`UL` 或 `unknown` |
| `occasion_index` | 本次监测实例的稳定编号 |
| `configuration_age` | 相对 `config_id` 的生效年龄 |

监测符号与 CORESET duration 的交集为空时，状态是 `no_candidate` 或 `not_monitored`，而不是 `decode_fail`。对 `flexible` 符号应遵循已确认的 TDD 配置；未知时保守标记，不强行当作 DL。

## 19. 候选首 CCE 的哈希接口

候选首 CCE 不能用“从 0 连续递增”替代。对聚合等级 $L$、候选索引 $m$ 和 CORESET 的 $N_{CCE}$，可用一个版本化的抽象接口表示：

$$
Y_p=g(Y_{p-1},\mathrm{RNTI},t,\theta_{SS}),
$$

$$
\mathrm{firstCCE}(L,m,n_{CI})
=L\left[
\left(Y_p+\left\lfloor\frac{mN_{CCE}}{L M_{L,\max}}\right\rfloor+n_{CI}\right)
\bmod\left\lfloor\frac{N_{CCE}}{L}\right\rfloor
\right].
$$

这里 $M_{L,\max}$ 是该聚合等级跨适用 carrier-indicator 语境的最大候选数，$n_{CI}$ 是 carrier indicator（未配置时取 0）；$g$、初值、公共/专用分支和索引域必须由目标 TS 38.213 版本确定。常见规范实现会使用版本化的模乘常数与 RNTI 初值；这些常数只能作为核验线索，不能在未锁定 Release 时硬编码。`firstCCE + L <= N_CCE` 是实现层硬约束。

> [!note] USS 核验线索（非本项目已锁定参数）
> Rel-17 参考版本的 UE-specific 候选递推使用 `Y_{p-1}=n_RNTI`、`D=65537`，且乘数 `A_p` 会随 CORESET pool 语境变化（常见值包括 `39827`、`39829`、`39839`）；公共搜索空间常以 `Y_p=0` 处理。这里的常数、`p` 的时隙索引、carrier indicator 和适用 Search Space 类型必须逐项核对；在核对完成前，代码应保持 `verified=false` 并标记 `NEEDS_EXTERNAL_REFERENCE`。

候选生成器应把哈希中间量也放进调试记录：

```js
candidate_hash:
  seed: null
  recurrence_step: null
  modulus: null
  rnti_input: null
  slot_input: null
  release: "unknown"
  verified: false
```

## 20. 候选枚举与去重

候选枚举应先按配置生成，再交给信号处理；不要在 IQ 上盲目滑窗：

```python
for L in configured_aggregation_levels:
    M = n_candidates[L]
    for m in 0 .. M-1:
        first = first_cce(L, m, context)
        cces = [first + i for i in 0 .. L-1]
        if first < 0 or first + L > N_CCE:
            emit(invalid_candidate, reason=cce_boundary)
            continue
        regs = cce_to_reg(cces, coreset.mapping)
        res = reg_to_re(regs, coreset, slot_context)
        if not masks_disjoint(res) or overlaps_previous(res):
            emit(invalid_candidate, reason=resource_overlap)
            continue
        emit(candidate_generated, first, cces, regs, res)
```

同一 Search Space 中不同聚合等级的候选可能占用相同 CCE；这不是自动错误，但必须记录 `overlap_group`，并在统计中区分“规范允许的候选重叠”和“实现生成的重复候选”。跨 Search Space 或跨 `config_id` 的碰撞不能直接合并。

## 21. 候选预算与误检风险

每个 monitoring occasion 的计算预算至少由以下乘积决定：

$$
N_{attempt}
=\sum_{L\in\mathcal{L}}M_L
\times N_{RNTI}
\times N_{format}
$$

实际耗时还包括 RE 解映射、DM-RS 估计、均衡、LLR 整理和 Polar 译码。建议同时保存：

| 指标 | 口径 |
|---|---|
| `candidate_generated` | 配置生成的候选数 |
| `candidate_processed` | 实际执行物理处理的候选数 |
| `decode_attempts` | 候选 x DCI 格式 x RNTI 尝试数 |
| `crc_pass` / `valid_dci` | 分层通过数 |
| `compute_p50/p95/p99/max` | 每 occasion 和每候选延迟 |
| `false_alarm_estimate` | 有真值时按负例统计；无真值时不得伪造 |

候选数量增加会放大错误 CRC 通过的机会，但不能仅用独立随机公式替代现场误检测量。公共候选与 UE-specific 候选应分开统计，避免把系统信息误检算成 UE 误检。

## 22. RNTI 上下文绑定

同一个物理候选可能需要尝试多个 RNTI，但每次尝试都必须带来源和有效期：

```js
rnti_context:
  type: "C-RNTI|RA-RNTI|SI-RNTI|P-RNTI|other|unknown"
  value: null
  source_event: ""
  valid_from_slot: null
  valid_until_slot: null
  confidence: "unknown"
```

RA-RNTI 只在 RAR 响应窗口内作为公共候选；C-RNTI 只有在 [[03-PDCCH/RNTI|RNTI]]/[[02-PRACH/C-RNTI|C-RNTI]] 证据链允许的时间范围内才应进入 USS 候选池。旧 RNTI、错误小区或失效 BWP 的候选必须标 `expired`/`rejected`，而不是继续尝试以提高“召回率”。

## 23. Search Space 验证矩阵

| 场景 | 预期状态 | 验收重点 |
|---|---|---|
| 非监测 slot | `not_monitored` | 周期/偏移和 frame/slot 转换 |
| 监测但 `nCandidates=0` | `no_candidate` | 配置解析，不调用译码器 |
| 合法单候选 | `candidate_generated` | first CCE、CCE/REG/RE 正逆映射 |
| 候选越界 | `invalid_candidate` | 不读取 IQ，不静默裁剪 |
| CSS + RA-RNTI | `candidate_only`/`valid_dci` | RAR 窗口、RAPID 和公共统计分离 |
| USS + C-RNTI | `valid_dci`/`associated` | 生命周期、跨时隙连续性和资源解释 |
| BWP/RRC 更新 | 新 `config_id` | 旧候选缓存失效 |
| flexible 符号未知 | `NEEDS_VERIFICATION` | 不把未知方向当作 DL |

## 24. Rel-17 V17.8.0 搜索空间核验基线

以下内容已对照 [ETSI TS 138 213 V17.8.0 (Release 17)](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) §10.1（访问日期 2026-09-05）。它用于校准实现字段，不代表当前网络一定使用该版本：

| 项目 | 参考版本事实 | 接收端记录 |
|---|---|---|
| 搜索空间集合 | 可为 CSS 或 USS；CSS 还分 Type0/0A/0B/1/1A/2/2A/3 等过程语境 | `search_space_type`、具体 Type、来源配置 |
| 关联资源 | 每个 Search Space 关联一个 CORESET；一个 DL BWP 可配置多个 Search Space/CORESET | `search_space_id`、`coreset_id`、BWP、配置版本 |
| 监测输入 | 周期/偏移、时隙内 monitoring pattern、duration、每个聚合等级的候选数 | 保存原始字段和解析后的 occasion 列表 |
| 聚合等级 | USS 候选的基础集合为 `L ∈ {1,2,4,8,16}` | 不把未配置等级加入尝试 |
| CSS 哈希 | `Y_p=0` | 候选首 CCE 不使用 UE RNTI 哈希 |
| USS 哈希 | 由 RNTI、时隙和 CORESET pool 相关的递推值生成；参考版本 `A_p` 随 pool 取 `39827/39829/39839`，`D=65537` | 保存 `Y_{p-1}`、`A_p`、`D` 和 carrier indicator |
| 监测预算 | 终端按能力和配置限制每时隙/每 span 的候选与非重叠 CCE 数 | 统计 `candidate_generated` 与 `candidate_processed` |

V17.8.0 的 USS 递推核验线索为：`Y_{p-1}=n_RNTI`、`D=65537`，且 `A_p` 随 CORESET pool 语境可取 `39827`、`39829` 或 `39839`。完整的 first-CCE 公式还包括候选索引、`N_CCE`、聚合等级以及可能的 carrier indicator；实现应以目标条款逐项复核，不能只复制一个常数。

## 25. 监测规则的实现注意

对 V17.8.0 参考版本，Search Space 的配置字段不仅决定“某个 slot 是否监测”，还决定：

- monitoring pattern 是否跨连续 slot 组成一个 group；
- 同一 CORESET 内两个 Search Space 的 occasion 是否相隔至少一个 CORESET duration；
- `searchSpaceLinkingId` 是否让两个集合共享同一候选/同一 DCI 信息；
- `freqMonitorLocations` 是否把 CORESET 频域位图限制到某些 RB set；
- 同一 slot 内不同公共/专用候选的 DCI size、scrambling 和非重叠 CCE 计数。

这些条件会影响“候选总数”和“实际需要译码的候选数”，不能只从 `nCandidates[L]` 一列推断。缺少 capability、RB set 或 linking 配置时，输出 `monitoring_budget_unknown`。

## 26. 证据与当前状态

- `STANDARD + verified-reference`：本地 [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|TS 38.213]] 摘要，以及上面的 ETSI TS 138 213 V17.8.0 §10.1 参考版本。
- `PERSONAL_NOTE`：本页的 CSS/USS 分层、候选缓存和项目 RNTI 绑定约定。
- `NEEDS_EXTERNAL_REFERENCE`：当前项目 Release、完整 first-CCE 公式的 carrier/RB-set 分支、能力限制、RRC 字段版本和现场配置。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚无真实配置下的逐时隙候选对照、碰撞和尾延迟结果。

## 27. Related Notes

- [[03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[03-PDCCH/CORESET|CORESET]]
- [[03-PDCCH/CCE REG|CCE REG]]
- [[03-PDCCH/DCI|DCI]]
- [[03-PDCCH/RNTI|RNTI]]
- [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
- [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]
- [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]
- [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]
- [[04-PDSCH/PDSCH|PDSCH]]
