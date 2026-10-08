---
title: NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析
aliases:
  - 5G C-RNTI 盲搜盲解
  - NR 控制到数据资源解析
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - channel/pdsch
  - channel/pusch
  - topic/用户关联
  - topic/资源解析
  - process/blind-detection
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TS 38.214
  - 用户项目流程说明
simulation:
  - 仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜
related:
  - "[[NR-DCI 编码链]]"
  - "[[NR-DL-SCH 编码链]]"
  - "[[NR-UL-SCH 编码链]]"
  - "[[DM-RS]]"
  - "[[5G TDD 上下行监测与资源解析]]"
  - "[[单用户时频截取与定位观测量]]"
---

# NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析

> [!abstract] 一句话结论
> C-RNTI 是把候选 PDCCH/DCI 与用户关联起来的关键上下文；PDCCH 盲搜先在合法 CORESET/搜索空间候选上做资源解映射、DM-RS 信道估计、均衡、Polar/CRC 和 RNTI 掩码检查，再把通过的 DCI 转换为 PDSCH/PUSCH 的时频资源与编码参数。

> [!note] 与现有脚本的边界
> 本页主要描述项目目标中的 C-RNTI/UE-specific SearchSpace 与 PDSCH/PUSCH 路径。当前 `NR_decode_test.m` 走的是 CORESET-0 公共搜索空间、SI-RNTI 和 SIB1 PDSCH；它没有完成 C-RNTI 关联、UE-specific PDCCH 或 PUSCH 解码。DCI 提供调度资源也不等于物理上已分离出某个 UE 的信号。

## 1. C-RNTI 不是“全频段可直接搜索的字段”

DCI 的 C-RNTI 关联通常体现在 CRC 掩码判决，而不是明文数据字段。现有 [[NR-DCI 编码链]] 已将候选级链路写成：

```text
候选资源 → 软解调 → 逆率匹配 → Polar 译码 → CRC/RNTI 掩码 → 字段合法性
```

因此第三方接收机的搜索空间有三个层次：

| 层次 | 候选范围 | 适用情况 | 风险 |
|---|---|---|---|
| 已知 C-RNTI | 已知 RNTI + 合法搜索空间候选 | RA 链已经建立关联 | 依赖关联正确、配置未过期 |
| 候选 RNTI 池 | 由 RA 事件、历史窗口或测试 UE 生成的有限集合 | 现场被动监测 | 误检和计算量增加 |
| 全空间假设 | 理论上遍历所有 RNTI | 仅作复杂度上界 | 不适合作为实时实现默认方案 |

不要用“搜索到一个 CRC 通过值”替代 C-RNTI 的协议关联。接受条件还应包括候选坐标、DCI 格式、字段范围、时序连续性和后续数据链一致性。

### 1.1 RNTI 类型和用途

| RNTI 上下文 | 典型用途 | 在本项目中的处理 |
|---|---|---|
| RA-RNTI | 随机接入响应窗口中的 RAR 调度 | 由 PRACH occasion 推导，短时有效 |
| TEMPORARY-C-RNTI/TC-RNTI | RAR 后的临时接入和争用解决 | 绑定到 RA 事件，不能直接当最终用户键 |
| C-RNTI | 连接期间的 UE 专用控制/数据寻址 | 争用解决或 C-RNTI MAC CE 后进入候选池 |
| SI-RNTI/P-RNTI 等 | 系统信息或寻呼等公共用途 | 作为公共搜索分支单独记录，不混入 C-RNTI 统计 |

具体 RNTI 类型、有效窗口和 DCI 格式要按当前标准/配置核对；表格只给出解析分层，不替代标准表格。

## 2. PDCCH 候选级处理

对时隙 $t$ 的候选集合 $\mathcal{C}_t$，每个候选 $h$ 都应有独立日志：

```text
CORESET / search-space / monitoring occasion
    ↓
CCE/REG 到 RE 的资源解映射
    ↓
PDCCH DM-RS 提取与信道估计
    ↓
MMSE/ZF 均衡和软解调
    ↓
解扰、逆率匹配、Polar 译码
    ↓
按 RNTI 假设恢复 CRC
    ↓
DCI 格式与字段合法性检查
```

候选状态至少区分：`invalid_candidate`、`not_present`、`decode_fail`、`crc_fail`、`crc_pass`、`valid_dci`。沿用 [[3GPP TS 38.213｜Physical layer procedures for control]] 的约定，`CRC pass` 不能直接等同于 `valid DCI`。

### 候选账本

| 字段 | 说明 |
|---|---|
| `monitoring_slot` / `symbol` | 监测时机 |
| `coreset_id` / `search_space_id` | 候选所属配置 |
| `aggregation_level` | 候选占用的 CCE 数量类别 |
| `candidate_index` | 候选在当前聚合等级中的索引 |
| `dci_format` / `payload_size` | 外层盲搜假设和字段长度 |
| `rnti_hypothesis` | 本次 CRC 掩码假设 |
| `pdcch_re_indices` | 资源解映射索引 |
| `dmrs_quality` / `noise_var` | 估计质量和噪声方差 |
| `crc_state` / `field_valid` | 判决状态 |
| `compute_time` | 候选级延迟，用于实时预算 |

## 3. DCI 到数据资源的快照

一旦得到有效 DCI，不能只保存“C-RNTI + 有数据”。需要把 DCI 字段解析为可复现的 `resource_snapshot` 和 `coding_snapshot`：

```text
有效 DCI
  ├─ 方向：DL assignment / UL grant
  ├─ 时域：时隙偏移、起止 OFDM 符号
  ├─ 频域：BWP、PRB/RIV、频域跳变或资源集合
  ├─ 调制/编码：MCS、目标码率、TBS、层数
  ├─ HARQ：进程号、NDI、RV、重传状态
  └─ 参考信号：DM-RS/PTRS 配置和端口关联
```

现有 [[3GPP TS 38.214｜Physical layer procedures for data]] 要求资源、TBS、MCS、RV 和编码链联动；现有 [[NR-DL-SCH 编码链]] / [[NR-UL-SCH 编码链]] 负责 38.212 的 CRC、LDPC、率匹配和逆处理。任何字段缺失都应写入 `missing_fields`，不要用默认值静默填充。

## 4. PDSCH/PUSCH 的“盲解”边界

| 目标 | 最低可行输入 | 是否需要完整高层解码 |
|---|---|---:|
| 只判断某用户是否占用资源 | 有效 DCI、RNTI、资源掩码、能量/DM-RS | 否 |
| 提取定位用单用户波形 | DCI 资源 + 方向/时序 + 已知参考信号 | 通常否，但需关联证据 |
| 恢复 PDSCH 业务比特 | DCI、DM-RS、MCS/TBS/RV、LDPC 参数 | 是，直到 TB-CRC |
| 恢复 PUSCH/UL-SCH 比特 | UL grant、PUSCH/UCI 配置、DM-RS、LDPC | 是，直到 TB-CRC |
| 生成跨站一致的 ToA | 共同已知上行参考/可对齐数据片段 | 不一定，优先使用 PRACH/PUSCH/SRS 等上行序列 |

“定位观测量”与“完整业务解码”是两个输出通道。为了降低第三方监测复杂度，可先用 PRACH、PDSCH/PUSCH DM-RS 或已知上行导频得到 ToA/SNR。PDCCH DM-RS 属于下行控制参考，不是 UE 专用定位信号；它可辅助小区/时频同步和控制候选质量，但不应单独当作 UE 的 UL-TDOA 观测。完整译码结果再用于用户关联和质量校验。

## 5. 单用户资源掩码

给定 DCI 解析出的资源集合 $\mathcal{R}_u$，接收网格应显式区分：

$$
\mathcal{R}_{all}=\mathcal{R}_{u}\,\dot\cup\,\mathcal{R}_{other}\,\dot\cup\,\mathcal{R}_{ref}\,\dot\cup\,\mathcal{R}_{reserved}
$$

这里的 `user` 不是由 PRB 位置单独决定的；MU-MIMO、同频邻区、重叠控制资源、预编码端口和参考信号复用都会改变可分离性。至少保存：

- 局部 RE 索引和绝对子载波/符号索引。
- 数据、DM-RS、PTRS、控制和保留 RE 掩码。
- 端口/层/预编码域，以及是否为等效信道。
- 资源快照对应的 C-RNTI、时隙和 DCI 候选。

## 6. MATLAB 官方示例的可复用接口

MathWorks 的 [Downlink Control Processing and Procedures](https://www.mathworks.com/help/5g/ug/downlink-control-processing-and-procedures.html) 展示了候选级处理思路，文档示例中出现的接口包括：

- `nrPDCCHSpace`：生成搜索空间候选资源和 PDCCH DM-RS 索引。
- `nrChannelEstimate`、`nrExtractResources`、`nrEqualizeMMSE`：候选信道估计、资源提取和均衡。
- `nrPDCCHDecode`、`nrDCIDecode`：PDCCH 软解调/解扰和 DCI 率恢复、Polar/CRC 判决。

MathWorks 的 [DL-SCH and PDSCH Transmit and Receive Processing Chain](https://www.mathworks.com/help/5g/gs/dl-sch-and-pdsch-transmit-and-receive-processing-chain.html) 展示了 `nrPDSCHDMRSIndices`、`nrPDSCHDMRS`、`nrPDSCHDecode` 和 DL-SCH 译码链的连接。

这些是官方示例中的 API 线索，不是本项目已运行证明。必须在本机 MATLAB/5G Toolbox 版本中核对对象属性、输入维度、RNTI 类型、数据类型、采样率和 Release 行为，并把版本写入实验账本。

### 6.1 候选账本判决与 BWP 局部资源掩码

候选级解码仍由已核验的 5G Toolbox/项目解码器完成。下面接收其逐候选结果，要求 CRC、字段、资源和跨时隙连续性同时成立；随后把已经规范化为 BWP 局部坐标的 DCI grant 转为资源网格掩码。资源网格掩码函数需另存为 `makeBwpResourceMask.m`。

> [!note] 代码片段的运行前提
> 以下是接口示例，不是可独立运行的端到端程序。`candidateResults`、`grant`、DM-RS/PTRS/reserved masks 和 BWP 坐标必须由已验证的解码/配置阶段提供；当前 `NR_decode_test.m` 尚未产出这组输入。

```matlab
% candidateResults 是解码适配器的 struct 数组，每项至少包含：
% rntiHypothesis, crcPass, fieldValid, resourceValid, temporalConsistent
required = ["rntiHypothesis", "crcPass", "fieldValid", ...
    "resourceValid", "temporalConsistent"];
assert(~isempty(candidateResults), "没有 PDCCH 候选结果");
assert(all(isfield(candidateResults, cellstr(required))), ...
    "候选账本缺少必需字段");

accepted = false(numel(candidateResults), 1);
for k = 1:numel(candidateResults)
    q = candidateResults(k);
    accepted(k) = q.crcPass && q.fieldValid && ...
        q.resourceValid && q.temporalConsistent;
end
acceptedCandidates = candidateResults(accepted);
```

```matlab
% grant 是 DCI 解析器的规范化输出；PRB/symbol 坐标均为 BWP 内 0-based。
% masks 输入也必须与当前 BWP 网格同尺寸，且来自已确认的 DM-RS/PTRS 配置。
function [allocatedRE, dataRE] = makeBwpResourceMask( ...
        grant, nPRB, nSymbols, dmrsMask, ptrsMask, reservedMask)
    nSubcarriers = 12 * nPRB;
    expectedSize = [nSubcarriers, nSymbols];
    assert(isequal(size(dmrsMask), expectedSize));
    assert(isequal(size(ptrsMask), expectedSize));
    assert(isequal(size(reservedMask), expectedSize));

    grantValues = [grant.startPRB0, grant.nPRB, ...
        grant.startSymbol0, grant.nSymbols];
    assert(all(isfinite(grantValues) & grantValues == floor(grantValues)) && ...
        grant.startPRB0 >= 0 && grant.nPRB > 0 && ...
        grant.startSymbol0 >= 0 && grant.nSymbols > 0, ...
        "grant 坐标必须是非负整数且分配长度大于 0");
    sc = (12 * grant.startPRB0 + 1): ...
        (12 * (grant.startPRB0 + grant.nPRB));
    sym = (grant.startSymbol0 + 1): ...
        (grant.startSymbol0 + grant.nSymbols);
    assert(~isempty(sc) && ~isempty(sym) && ...
        sc(1) >= 1 && sc(end) <= nSubcarriers && ...
        sym(1) >= 1 && sym(end) <= nSymbols, ...
        "DCI grant 超出当前 BWP/时隙边界");

    allocatedRE = false(expectedSize);
    allocatedRE(sc, sym) = true;
    dataRE = allocatedRE & ~dmrsMask & ~ptrsMask & ~reservedMask;
end
```

此处的 `allocatedRE` 表示调度分配范围，不等同于已完成端口/层分离的“单用户 RE”。频域资源分配字段（例如 RIV）必须先按适用 DCI 格式和 BWP 大小解码，再传给掩码函数；DM-RS、PTRS、保留 RE 也必须使用同一配置快照。

## 7. 误检、漏检和连续性判据

建议将最终接受函数写成多证据判决：

$$
\mathrm{accept}(h)=
\mathbf{1}[\mathrm{CRC}_{RNTI}=0]
\mathbf{1}[\mathrm{field\_valid}=1]
\mathbf{1}[\mathrm{resource\_valid}=1]
\mathbf{1}[\mathrm{temporal\_consistent}=1]
$$

其中最后一项可检查：同一 RNTI 的 DCI 是否能解释后续 PDSCH/PUSCH、HARQ 进程和 DM-RS 资源；不能只依赖一个时隙的 CRC。错误候选通过概率的数量级分析可参考 [[NR-DCI 编码链#CRC 掩码和盲检测]]，但真实误检率必须实测。

## 8. 故障定位矩阵

| 现象 | 优先检查层 | 典型记录 |
|---|---|---|
| 所有候选均无能量 | TDD/CORESET/BWP/定时 | 方向、符号、绝对频点 |
| DM-RS 相关差 | 端口、序列、功率、频偏 | 参考序列和资源索引 |
| Polar 译码失败 | LLR 符号、逆率匹配、聚合等级 | $K,N,E$、LLR 范围 |
| CRC 只在错误 RNTI 通过 | RNTI 掩码、位序、误检控制 | 所有 RNTI 假设和候选数 |
| DCI 通过但 PDSCH 不通 | K0/资源/MCS/TBS/RV/DM-RS | 两份 snapshot 对比 |
| PDSCH 通但定位峰不稳 | 截取窗口、滤波、CFO、多径 | 原始 I/Q、群时延、峰轨迹 |

## 证据与出处

- `PERSONAL_NOTE`：[[NR-DCI 编码链]]、[[3GPP TS 38.213｜Physical layer procedures for control]]、[[3GPP TS 38.214｜Physical layer procedures for data]]。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.212｜Multiplexing and channel coding]]；本地页提供职责边界，具体 Release 表格仍需锁定。
- `NEEDS_EXTERNAL_REFERENCE`： [MathWorks PDCCH 盲搜示例](https://www.mathworks.com/help/5g/ug/downlink-control-processing-and-procedures.html)、[MathWorks PDSCH/DL-SCH 链路示例](https://www.mathworks.com/help/5g/gs/dl-sch-and-pdsch-transmit-and-receive-processing-chain.html)，访问日期 2026-09-04。
- `PERSONAL_NOTE`：用户项目说明中的“先拿到 C-RNTI，再盲搜/盲解所有相关 PDCCH/PDSCH”；本页补充了候选空间和协议状态约束。

## 当前状态

- `EXPERIMENT + NEEDS_VERIFICATION`：尚无现场 C-RNTI、PDCCH 候选或 PDSCH/PUSCH 解码结果。
- `TODO`：从现有 MATLAB 工程导出一帧 `carrier/BWP/CORESET/search-space/RNTI/DCI` 快照，并用已知测试 UE 验证一个正确候选和两个错误候选。

## 项目化入口

- PDCCH 原子笔记集：[[5G-NR-Positioning/03-PDCCH/PDCCH Overview]]、[[5G-NR-Positioning/03-PDCCH/PDCCH Blind Decoding]]、[[5G-NR-Positioning/03-PDCCH/DCI]]
- PDSCH 桥接：[[5G-NR-Positioning/04-PDSCH/PDSCH]]
- 项目主线：[[5G-NR-Positioning/00-项目总览/5G NR Passive Positioning Pipeline]]
