---
title: PDCCH Blind Decoding
aliases:
  - PDCCH 盲搜与盲译码
  - NR PDCCH Blind Detection
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - process/blind-detection
  - process/blind-decoding
  - topic/用户关联
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 用户项目流程说明
related:
  - "[[03-PDCCH/PDCCH Overview|PDCCH Overview]]"
  - "[[03-PDCCH/CORESET|CORESET]]"
  - "[[03-PDCCH/Search Space|Search Space]]"
  - "[[03-PDCCH/DCI|DCI]]"
  - "[[03-PDCCH/RNTI|RNTI]]"
---

# PDCCH Blind Decoding

> [!abstract] 项目主线
> PDCCH 盲译码不是在全频带猜一个 DCI，而是在已知或候选的 CORESET/Search Space 中枚举合法候选，逐候选完成 CCE/REG/RE 解映射、DM-RS 信道估计、均衡、软解调、Polar/CRC、RNTI 和字段语义检查，再把可信 DCI 交给 [[04-PDSCH/PDSCH|PDSCH]]/PUSCH 资源解析。

## 1. 一句话定义

PDCCH 盲译码是接收端在不知道承载位置、聚合等级或目标 RNTI 的情况下，对规范允许的多个 PDCCH 候选执行检测、译码和消歧的过程。

## 2. 为什么项目需要它

第三方被动设备通常没有 gNB 调度内部状态，必须从空口恢复目标 UE 的 PDCCH。项目第一阶段形成的 C-RNTI 或有限候选池只提供关联上下文，不会告诉接收机每个时隙的候选位置；盲译码负责把这些候选转成 DCI，从而进入 [[04-PDSCH/PDSCH|PDSCH]]、单用户截取和定位观测。它也是区分“无 PDCCH”“候选译码失败”“错误 RNTI 误检”的主要诊断层。

## 3. 它位于整个 5G 空口链路的什么位置

~~~text
同步/小区/BWP/TDD
  -> CORESET + Search Space
  -> 候选 CCE/REG/RE 枚举
  -> DM-RS 信道估计与均衡
  -> 软解调、解扰、逆率匹配、Polar
  -> CRC/RNTI 掩码
  -> DCI 字段语义和资源检查
  -> PDSCH/PUSCH -> UE Resource Extraction -> Timing Observation
~~~

盲译码只负责控制候选的判决，不等于完整 PDSCH 业务解码，也不等于 C-RNTI 获取本身。

## 4. 输入

| 输入 | 作用 |
|---|---|
| 原始 IQ/资源网格、采样率、FFT/CP 和同步状态 | 生成可用接收网格 |
| CORESET、Search Space、BWP、TDD 快照 | 枚举合法候选 |
| CCE/REG/RE 映射和 PDCCH DM-RS 配置 | 提取候选并估计信道 |
| DCI 格式/长度候选 | 选择 Polar/字段解析分支 |
| RNTI 候选池及来源 | 执行 CRC 掩码和用户关联 |
| 噪声方差、均衡和 LLR 约定 | 产生可译码软信息 |

输入必须带配置版本和生效时间；未知项保持 NEEDS_VERIFICATION，不要用默认网络参数替代。

## 5. 输出

盲译码器应为每个候选输出完整状态账本，并为最终接受的 DCI 输出资源快照：

~~~js
candidate_id: ""
monitoring_occasion: ""
coreset_id: null
search_space_id: null
aggregation_level: null
candidate_index: null
rnti_hypothesis: null
dci_format: ""
dmrs_quality: null
llr_quality: null
polar_state: "not_run|fail|pass"
crc_state: "not_run|fail|pass"
field_valid: false
candidate_state: "invalid_candidate|not_present|decode_fail|crc_fail|crc_pass|valid_dci"
resource_snapshot: ""
association_state: "candidate_only|associated|rejected"
failure_reason: ""
~~~

最终输出还应统计每个 monitoring occasion 的候选总数、译码次数、CRC 通过数、语义有效数、漏检和误检估计。

## 6. 关键参数

| 参数 | 作用 | 记录要求 |
|---|---|---|
| CORESET/Search Space | 限定资源和候选 | 保存原始配置和版本 |
| 聚合等级 L、候选索引 m | 决定候选 CCE 组合和编码长度 | 保留索引基准 |
| RNTI 类型/值 | CRC 掩码和上下文 | 标注来源、有效期、置信度 |
| DCI 格式/长度 A | 字段和 Polar 分支 | 不跨 Release 硬编码 |
| K/N/E、LLR 符号/尺度 | 控制译码参数 | 与 NR-DCI 编码链对齐 |
| PDCCH DM-RS/噪声方差 | 信道估计和软信息质量 | 保存估计窗口和质量指标 |
| 字段合法性/资源连续性 | 减少 CRC 误检 | 保存拒绝原因 |
| 候选数、RNTI 池大小 | 计算量和误检概率 | 统计 P95/P99/最大延迟 |

## 7. 时域位置

盲译码只在 Search Space 指定的 monitoring occasion 和 CORESET 符号内运行。对每个候选同时记录控制所在 slot/symbol、可能被 DCI 调度的数据 slot/symbol、TDD 方向和配置版本。not_monitored、no_candidate、decode_fail 和 crc_fail 必须分开，否则无法判断是时序配置问题还是信号质量问题。

## 8. 频域位置

候选频域位置由 CORESET 位图、BWP/Point A、CCE-to-REG 映射和候选首 CCE 共同决定。盲译码器应先生成有序 RE 索引，再提取 DM-RS 和控制符号；不能在整个 BWP 上滑动一个未知长度的窗口冒充规范候选。局部网格、BWP PRB 和绝对载波坐标都要保留。

## 9. 数学原理

设时隙 $t$ 的合法候选集合为 $\mathcal{C}_t$，RNTI 假设集合为 $\mathcal{R}$。每个候选经过解映射和译码得到 $\hat{\mathbf a}_{h,r}$，接受函数可写为：

$$
\mathrm{accept}(h,r)
=\mathbf{1}\left[
h\in\mathcal{C}_t
\right]
\mathbf{1}\left[
\mathrm{CRC}_{r}(\hat{\mathbf a}_{h,r})=0
\right]
\mathbf{1}\left[
\mathrm{field\_valid}(h,r)=1
\right]
\mathbf{1}\left[
\mathrm{resource\_valid}(h,r)=1
\right].
$$

控制候选的处理链为：

$$
A
\xrightarrow{+\mathrm{CRC}}
K
\xrightarrow{\mathrm{Polar}}
N
\xrightarrow{\mathrm{rate\ matching}}
E
\xrightarrow{\mathrm{map}}
\mathbf{y}_{h}
\xrightarrow{\mathrm{equalize/demod}}
\mathrm{LLR}_{h}
\xrightarrow{\mathrm{decode}}
\hat{\mathbf a}_{h}.
$$

若单个错误候选的 CRC 通过概率近似为 $2^{-m}$，候选数为 $M$，独立近似下至少一次误检的数量级可写为：

$$
P_{\mathrm{FA}}\approx 1-(1-2^{-m})^{M}.
$$

该式只用于复杂度/误检的数量级检查；实际候选相关性、字段约束、RNTI 池和信道错误必须实测。

盲译码工作量可粗略表示为：

$$
W_{\mathrm{blind}}
\asymp\sum_{h\in\mathcal{C}_t}\sum_{r\in\mathcal{R}}
W_{\mathrm{map+est+Polar}}(h,r).
$$

## 10. 3GPP 对应规范

| 规范 | 相关内容 | Clause/字段状态 |
|---|---|---|
| TS 38.211 | PDCCH 加扰、调制、DM-RS、CCE/REG/RE 物理映射 | PDCCH 相关 §7.3.2 子条款；版本/具体映射 NEEDS_EXTERNAL_REFERENCE |
| TS 38.212 | DCI CRC、Polar、率匹配和逆处理 | DCI/控制信息 §5.3 相关子条款；版本/位序 NEEDS_EXTERNAL_REFERENCE |
| TS 38.213 | Search Space 监测、候选、RNTI 和控制接收过程 | 控制信道接收 §10 范围；候选公式 NEEDS_EXTERNAL_REFERENCE |
| TS 38.331 | CORESET/Search Space 的 RRC 配置 | ASN.1 字段和 Release 需外部核验 |

本地 [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|TS 38.213]] 明确要求区分 CRC pass、valid DCI 和 no detection；现有 [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|PDCCH 盲搜笔记]] 提供候选账本。两者均不能替代项目锁定 Release 的规范核对。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

| 函数 | 盲译码阶段 | 状态 |
|---|---|---|
| nrPDCCHSpace | 生成候选空间/资源和 PDCCH DM-RS 索引线索 | NEEDS_EXTERNAL_REFERENCE |
| nrExtractResources | 提取候选 RE/DM-RS | NEEDS_EXTERNAL_REFERENCE |
| nrChannelEstimate | 候选信道估计 | NEEDS_EXTERNAL_REFERENCE |
| nrEqualizeMMSE | 候选均衡 | NEEDS_EXTERNAL_REFERENCE |
| nrPDCCHDecode | PDCCH 软处理/解扰线索 | NEEDS_EXTERNAL_REFERENCE |
| nrDCIDecode | DCI 率恢复、Polar/CRC 判决线索 | NEEDS_EXTERNAL_REFERENCE |

这些函数名取自既有项目笔记中的官方示例线索，没有在当前项目运行证明。必须先核对 MATLAB/5G Toolbox Release、函数签名、RNTI 输入、LLR 形状、索引基准和错误状态。

## 12. 本项目中的用途

盲译码是第二阶段的执行核心：

1. 读取 [[02-PRACH/C-RNTI|C-RNTI]] 或有限候选池，并区分 RA-RNTI/临时标识。
2. 用 [[03-PDCCH/CORESET|CORESET]] 和 [[03-PDCCH/Search Space|Search Space]] 生成合法候选。
3. 经 [[03-PDCCH/CCE REG|CCE REG]] 取出候选 RE，使用 [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]] 做信道估计和均衡。
4. 对每个 DCI 格式/候选执行 Polar、CRC/RNTI 和字段检查。
5. 把有效 [[03-PDCCH/DCI|DCI]] 转换为 [[04-PDSCH/PDSCH|PDSCH]]/PUSCH 资源快照。
6. 将 C-RNTI、资源、时序和质量证据传给 [[05-定位观测量/Timing Observation|Timing Observation]]，再进入多站 TDOA。

## 13. 常见误区

- 把盲搜理解为在全带宽、全时隙任意滑窗；规范候选必须由 CORESET/Search Space 约束。
- 将 PDCCH 软比特直接送入 DCI 字段解析，跳过候选级 Polar/率匹配/CRC。
- 把错误 RNTI 的 CRC pass 当成 C-RNTI 确认。
- 把 not_monitored、资源越界、解码失败和 CRC 失败合并成一个“无信号”状态。
- 忽略 PDCCH DM-RS、LLR 符号、端口、BWP 偏移或 TDD 方向。
- 只优化 Polar 树计算而忽略候选资源解映射、信道估计和尾延迟。
- DCI 通过后不保存原始候选和快照，导致后续 PDSCH/定位问题无法回溯。

## 14. 与相似概念的区别

| 概念 | 主要问题 | 与盲译码的区别 |
|---|---|---|
| PDCCH detection | 候选上是否存在可靠控制能量/码字 | 盲译码还需 Polar、CRC、RNTI 和语义判决 |
| DCI decoding | 恢复某个已选候选的控制字段 | 盲译码包含候选枚举和消歧 |
| Blind search | 枚举未知候选/RNTI | 是盲译码的搜索阶段，不包含完整输出 |
| PDSCH decoding | 恢复下行数据 TB | 依赖有效 DCI，属于后续数据链 |
| C-RNTI acquisition | 建立 UE 控制上下文 | 可能由 RA 链提供，盲译码只验证/使用它 |

## 15. 代码实现注意事项

- 采用两层循环：monitoring occasion/candidate 与 RNTI/格式假设；每次循环生成不可变 candidate_record。
- 先做资源边界、TDD 方向和 DM-RS 索引检查，再调用昂贵的 Polar 译码。
- 保留中间 artifact：RE 索引、DM-RS 估计、LLR、K/N/E、CRC 状态、字段错误和耗时。
- 维护候选状态机：invalid_candidate、not_present、decode_fail、crc_fail、crc_pass、valid_dci。
- 对 RNTI 候选池设来源、有效期和淘汰策略，避免旧 C-RNTI 造成误检。
- 把 PDCCH 控制结果和 PDSCH/PUSCH 资源快照用 event_id 关联，但不覆盖原始候选记录。
- 统计候选数量、平均/P95/P99/最大处理延迟和每种失败原因；不要只输出最终 DCI 数。

## 16. 待实验验证的问题

- [ ] C0：已知 CORESET、Search Space、C-RNTI、单候选、无噪声，验证 DCI 闭环。
- [ ] C1：正确资源+错误 RNTI、错误资源+正确 RNTI、随机候选三类负例可区分。
- [ ] C2：多聚合等级、多候选和多 DCI 格式下核对候选索引、漏检和误检。
- [ ] C3：加入 AWGN、CFO、定时偏移、多径，记录 DM-RS/LLR/Polar/CRC 分层指标。
- [ ] C4：有效 DCI 驱动 [[04-PDSCH/PDSCH|PDSCH]]，核对资源命中和 DM-RS/LDPC/TB-CRC。
- [ ] C5：RA 驱动的有限 C-RNTI 池做跨时隙连续性、RNTI 重用和候选老化测试。
- [ ] C6：把通过的控制候选接到定位支路，确认时间基准、资源掩码和质量标志一致。

## 17. 两阶段候选处理架构

把所有候选都直接送入 Polar 译码会浪费计算，也会让故障难以定位。建议将盲译码拆成“廉价结构筛选”和“昂贵控制译码”两阶段：

```text
阶段 A：结构/参考筛选
  配置合法性 -> CCE/REG/RE 边界 -> TDD 方向
  -> DM-RS 是否存在/相关质量/噪声估计
  -> 保留候选或记录早期失败

阶段 B：控制信息译码
  LLR 整理 -> 解扰 -> 逆率匹配 -> Polar
  -> CRC/RNTI -> DCI format/字段/资源
  -> valid_dci -> 跨时隙关联
```

阶段 A 的筛选只能减少无效计算，不能用一个能量门限替代 CRC/字段判决。每个阶段都要输出计数和失败原因，避免把 `dmrs_fail` 误报成 `crc_fail`。

## 18. 候选处理顺序与伪代码

推荐的外层循环顺序是 monitoring occasion -> candidate -> DCI format -> RNTI。若 RNTI 池很大，可在同一个候选上复用一次解调/Polar 结果，再逐 RNTI 检查 CRC，但必须保留每个假设的记录：

```python
for occasion in valid_monitoring_occasions:
    candidates = candidate_generator(occasion, config_snapshot)
    for c in candidates:
        rec = create_record(c)
        if not bounds_ok(c) or not tdd_ok(c):
            emit(rec.with_state(invalid_candidate))
            continue

        re_obs = extract_ordered_re(grid, c.re_indices)
        dmrs_result = estimate_dmrs(re_obs, c.dmrs_indices)
        if not dmrs_result.usable:
            emit(rec.with_state(dmrs_fail,
                                quality=dmrs_result.quality))
            continue

        llr = soft_demod(equalize(re_obs, dmrs_result),
                         noise_variance=dmrs_result.noise_variance)
        for fmt in configured_dci_formats(c.search_space_id):
            decoded = polar_decode_inverse_rm(llr, fmt, c)
            if not decoded.ok:
                emit(rec.with_state(decode_fail, format=fmt))
                continue
            for rnti in applicable_rnti_contexts(c, fmt):
                verdict = check_crc_mask_and_fields(decoded, rnti,
                                                    c, config_snapshot)
                emit(verdict)
                if verdict.state == valid_dci:
                    emit(build_resource_snapshot(verdict))
                    emit(build_coding_snapshot(verdict))
```

`configured_dci_formats` 和 `applicable_rnti_contexts` 必须来自 Search Space/RNTI 快照；不能为了提高召回率把所有格式和所有历史 RNTI 无条件相乘。

## 19. DM-RS 质量门与早期失败

PDCCH DM-RS 的作用是为候选控制资源提供参考观测。建议对每候选保存以下质量字段，而不是只留一个相关峰：

```js
dmrs_quality:
  correlation_peak: null
  normalized_correlation: null
  estimated_noise_variance: null
  channel_condition: null
  phase_rotation: null
  missing_re_count: null
  port_hypothesis: null
  threshold_id: ""
  state: "not_run|usable|weak|inconsistent"
```

阈值应与采样率、调制功率、估计窗口和 SNR 定义绑定；没有经过正负例校准时，不能把某个经验阈值写成标准要求。`weak` 候选可作为低优先级重试或待验证样本，但不应直接升级为有效 DCI。

## 20. LLR、Polar 和 CRC 的边界日志

控制译码失败至少要能定位到以下边界之一：

| 边界 | 记录字段 | 典型症状 |
|---|---|---|
| RE/符号顺序 | `re_order_hash`、shape、端口 | 所有聚合等级都失败 |
| 均衡/噪声 | `H_est` 摘要、噪声方差、LLR 范围 | DM-RS 好但 LLR 饱和/反号 |
| 物理解扰 | 扰码初始化/版本 | 星座正常、Polar 全失败 |
| 率匹配 | `A/K/N/E`、逆索引 | 特定聚合等级失败 |
| Polar | 可靠性集合、列表/路径状态 | CRC 前 payload 不稳定 |
| RNTI 掩码 | 类型、值、位序 | 只有错误 RNTI 通过 |
| 字段解析 | format、offset、BWP | CRC 通过但资源越界 |

建议保留受控长度的 LLR 摘要或 artifact 引用，不要只存最终比特。完整原始 IQ/LLR 可放在实验目录，笔记中保存路径、哈希和配置版本。

## 21. 多命中与候选消歧

一个 monitoring occasion 可能出现多个合法 DCI，也可能因为低 SNR/错误假设产生多个 CRC pass。盲译码器应先保留全集，再根据协议约束消歧：

```text
all crc_pass records
    -> 同 candidate 多 format/RNTI 分组
    -> 检查字段范围和资源是否越界
    -> 检查候选是否属于当前 Search Space
    -> 检查同一 RNTI 的时序/HARQ/资源连续性
    -> 输出 valid_dci、ambiguous 或 rejected
```

| 情况 | 处理 |
|---|---|
| 不同候选、不同 RNTI 都通过 | 允许多个 `valid_dci`，分别生成快照 |
| 同候选多个 RNTI 通过 | 标 `rnti_ambiguous`，不覆盖任何结果 |
| 同候选多个 format 通过 | 标 `format_ambiguous`，保留 payload 和字段错误 |
| 资源互相重叠且协议不允许 | 标 `candidate_collision`，列出冲突 RE/slot |
| CRC 通过但后续资源无法解释 | 降级为 `field_invalid`/`resource_invalid` |

“每时隙只允许一个 DCI”不能作为通用假设；是否允许多个传输、多个 Search Space 或公共/专用控制并存，必须由配置和过程决定。

## 22. 计算预算与并行边界

候选处理的工作量可展开为：

$$
W_t=\sum_{c\in\mathcal{C}_t}
\left(W_{map}(c)+W_{dmrs}(c)+W_{eq}(c)
 +N_{format}(c)\,W_{polar}(c)
 +N_{rnti}(c)\,W_{crc}\right).
$$

适合并行的边界是“候选记录”或“候选的 format 分支”；配置快照、索引表和 RNTI 生命周期应是只读输入。并行实现仍须保证：

- 每个 `candidate_id` 的日志顺序可重建；
- 相同物理候选的多 RNTI 结果不互相覆盖；
- 内存/缓存预算和 P95/P99/最大尾延迟可测；
- 早期失败不会被异步任务静默丢弃。

平均吞吐量不能替代实时监测的尾延迟；应按 monitoring occasion 输出候选数、译码次数、最大并发和丢弃原因。

## 23. 盲译码事件记录

```js
blind_decode_event:
  event_id: ""
  config_id: ""
  frame: null
  slot: null
  occasion_state: "not_monitored|open|closed"
  candidate_totals:
    generated: 0
    processed: 0
    invalid: 0
    dmrs_fail: 0
    decode_fail: 0
    crc_fail: 0
    crc_pass: 0
    valid_dci: 0
    ambiguous: 0
  latency_us:
    p50: null
    p95: null
    p99: null
    max: null
  accepted_candidate_ids: []
  rejected_candidate_ids: []
  artifact_refs: []
```

候选级记录与 occasion 汇总都要保留。只保存汇总数字会失去“哪个候选、哪个 RNTI、哪种格式失败”的回放能力。

## 24. 定位支路的使用边界

盲译码输出的首要价值是恢复控制上下文和数据资源，而不是直接给出距离：

1. `valid_dci` 提供控制 slot、数据 slot、方向、BWP、PRB、符号和参考信号配置。
2. `associated` 或明确的候选状态决定是否允许把这些资源归给目标 UE。
3. 定位支路从上行 PUSCH/DM-RS、SRS、PRACH 或项目定义的参考片段提取 ToA/RToA；PDCCH DM-RS 只作下行控制质量/同步辅助。
4. 跨站融合前检查 `event_id`、采样起点、站间时钟、RF/滤波延迟和峰策略一致性。

若只有 CRC pass 而没有资源或用户证据，定位状态应为 `positioning_pending`，不能生成确定的 UE TDOA。

## 25. C0-C6 验证矩阵

| 门 | 输入 | 通过条件 | 失败时保留 |
|---|---|---|---|
| C0 | 单候选、已知 RNTI、无噪声 | payload、CRC、A/K/N/E 全部闭合 | 每阶段向量 |
| C1 | 正确资源 + 错误 RNTI | CRC fail 且状态可解释 | RNTI/掩码日志 |
| C2 | 错误资源 + 正确 RNTI | 不接受为 valid_dci | RE/DM-RS/字段日志 |
| C3 | 多 L/多候选/多格式 | 候选边界、去重和多命中可回放 | occasion 汇总 |
| C4 | AWGN/CFO/多径 | 分层统计 DM-RS、LLR、Polar、CRC | 参数/种子/指标 |
| C5 | 有效 DCI -> PDSCH/PUSCH | 资源/编码快照与真值一致 | 两份 snapshot |
| C6 | RA 驱动 RNTI 池 + 上行参考 | 关联、老化和定位时间基准可解释 | event_id/校准证据 |

通过 C0-C2 只证明控制译码边界，不能声称现场被动定位已经完成。

## 26. Rel-17 V17.8.0 盲译码参考边界

把三份标准的已核验边界串起来（访问日期 2026-09-05）：

| 阶段 | 参考文本 | 已确认的输入/输出边界 |
|---|---|---|
| 候选物理资源 | [TS 38.211 V17.8.0 §7.3.2/§7.4.1.3](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf) | CCE/REG/CORESET、PDCCH QPSK/端口、DM-RS、物理扰码和 RE 顺序 |
| 候选监测 | [TS 38.213 V17.8.0 §10.1](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) | CSS/USS、monitoring occasion、候选首 CCE、RNTI/格式语境和监测预算 |
| DCI 逆编码 | [TS 38.212 V17.8.0 §7.3](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.08.00_60/ts_138212v170800p.pdf) | 字段位序、尺寸对齐、CRC24C、RNTI parity mask、Polar 和率匹配 |

参考版本下的候选循环仍不是现场结果：目标网络的 Release、RRC 配置、采样同步、RNTI 生命周期和工具箱实现必须在 `config_snapshot`/实验账本中另行确认。

## 27. 证据与当前状态

- `STANDARD + verified-reference`：本地 TS 38.211/38.212/38.213 笔记及上面的 Rel-17 V17.8.0 参考边界。
- `PERSONAL_NOTE`：本页的两阶段架构、状态机、候选预算和定位接口。
- `NEEDS_EXTERNAL_REFERENCE`：当前项目 Release/现场配置、阈值校准、工具箱 API、端口/QCL 状态和非 Rel-17 扩展。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚无现场 PDCCH 候选、LLR、CRC、DCI 或定位结果。

## 28. Related Notes

- [[03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[03-PDCCH/CORESET|CORESET]]
- [[03-PDCCH/Search Space|Search Space]]
- [[03-PDCCH/CCE REG|CCE REG]]
- [[03-PDCCH/DCI|DCI]]
- [[03-PDCCH/RNTI|RNTI]]
- [[02-PRACH/C-RNTI|C-RNTI]]
- [[04-PDSCH/PDSCH|PDSCH]]
- [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]
- [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]
- [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]]
- [[05-定位观测量/Timing Observation|Timing Observation]]
- [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]
