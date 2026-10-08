---
title: CORESET
aliases:
  - Control Resource Set
  - 控制资源集
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - topic/coreset
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.331
  - 用户项目流程说明
related:
  - "[[03-PDCCH/PDCCH Overview|PDCCH Overview]]"
  - "[[03-PDCCH/Search Space|Search Space]]"
  - "[[03-PDCCH/CCE REG|CCE REG]]"
  - "[[01-NR基础/SSB PBCH MIB]]"
---

# CORESET

> [!abstract] 项目主线
> CORESET（Control Resource Set）定义 PDCCH 可使用的一块时间-频率控制资源及其 CCE/REG 组织方式；它缩小盲搜的物理资源范围，但本身不决定每个监测时机实际出现哪个候选。

## 1. 一句话定义

CORESET 是由 RRC/系统配置描述的控制资源集合，提供 PDCCH 的频域资源、OFDM 符号持续范围以及 CCE 到 REG 的映射上下文。

## 2. 为什么项目需要它

第三方接收机若把整个 BWP 当作 PDCCH 搜索区，会产生大量无效候选并放大误检。CORESET 提供第一层物理约束，使接收机能在正确的符号和 PRB 集合中提取 PDCCH DM-RS、建立信道估计并进入 [[03-PDCCH/Search Space|Search Space]] 候选生成。

## 3. 它位于整个 5G 空口链路的什么位置

```text
RRC/MIB/SIB1 配置
  -> CORESET 频域/时域资源
  -> REG/CCE 组织
  -> Search Space 监测时机和候选
  -> PDCCH 解映射
  -> DCI/RNTI 判决
```

CORESET 属于配置与物理资源层，位于 RNTI/盲译码之前；它不替代 DCI 内容，也不直接产生 C-RNTI。

## 4. 输入

| 输入 | 说明 |
|---|---|
| 载波、SCS、BWP、Point A/频域参考 | 把 CORESET 局部资源转换为绝对频率 |
| `ControlResourceSet` 配置 | CORESET 标识、频域位图、时域长度等 |
| CCE-to-REG 映射类型及交织参数 | 生成候选的物理索引顺序 |
| 监测时隙/符号 | 由 Search Space 和 TDD 状态筛出实际时机 |
| IQ/资源网格和同步结果 | 提取控制资源观测 |

配置版本、来源和生效时间要与 [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|TDD 监测笔记]] 的 `config_snapshot` 一致。

## 5. 输出

CORESET 解析器应输出一个可审计的资源描述：

```js
coreset_id: null
bwp_id: null
frequency_domain_resources: ""
duration_symbols: null
mapping_type: "nonInterleaved|interleaved|unknown"
reg_bundle_size: null
interleaver_size: null
shift_index: null
local_reg_indices: []
absolute_subcarriers: []
candidate_domain_status: "ready|partial|NEEDS_VERIFICATION"
```

输出交给 [[03-PDCCH/CCE REG|CCE REG]] 和 [[03-PDCCH/Search Space|Search Space]]；若位图或坐标缺失，不应生成“默认 CORESET”。

## 6. 关键参数

| 参数 | 作用 | 当前处理 |
|---|---|---|
| `controlResourceSetId` | 区分多个 CORESET | 记录原值和版本 |
| 频域资源位图 | 指定 PRB/REG 覆盖范围 | 按配置解码，禁止猜测 |
| `duration` | 指定连续 OFDM 符号范围 | 记录相对时隙坐标 |
| `cce-REG-MappingType` | 决定 CCE/REG 顺序 | `NEEDS_EXTERNAL_REFERENCE` 具体枚举 |
| REG bundle/interleaver/shift | 交织映射参数 | 随 Release/配置核对 |
| BWP/Point A 偏移 | 转换绝对频域坐标 | 与载波快照绑定 |
| PDCCH DM-RS 参数 | 对每候选做信道估计 | 由物理信道配置推导 |

不要把 CORESET 的 PRB 数、符号数、交织大小或候选数量写成跨 Release 常量。

## 7. 时域位置

CORESET 的时域范围通常是一个时隙内从配置起点开始的连续 OFDM 符号集合；实际是否在某一时隙监测由 Search Space 的周期/偏移和 TDD 下行可用性共同决定。项目日志应保存 `frame/slot/start_symbol/duration`，并标记 `DL`、`flexible` 或 `unknown`，不要把灵活符号强行当作 PDCCH。

## 8. 频域位置

频域资源由 CORESET 位图相对于 BWP/Point A 表示。先解码位图得到局部 PRB，再映射为 REG，最后按 CCE-to-REG 规则产生候选物理 RE。局部数组下标、BWP 内下标和载波绝对子载波下标必须分别保存。具体位图编码和偏移语义尚未在当前 Vault 锁定 Release，标为 `NEEDS_EXTERNAL_REFERENCE`。

## 9. 数学原理

令可用控制资源集合为：

$$
\mathcal{R}_{CORESET}
=\{(k,l): k\in\mathcal{K}_{freq},\ l\in\mathcal{L}_{time}\}.
$$

CCE-to-REG 映射可抽象为一个配置相关的置换 $\pi$：

$$
\mathrm{REG}_{c,r}=\pi(c,r;\theta_{CORESET}),
$$

其中 $c$ 是 CCE 索引，$r$ 是 CCE 内 REG 位置，$\theta_{CORESET}$ 包含映射类型、bundle、interleaver 和 shift。常见 NR 抽象把一个 CCE 组织为若干 REG（常见实现以 6 个 REG 为一组），但数量和具体映射必须以目标 Release 核对，故此处为 `NEEDS_EXTERNAL_REFERENCE`。

合法候选必须满足：

$$
\mathcal{R}_{candidate}\subseteq\mathcal{R}_{CORESET},
$$

并且其候选 CCE 不越过 CORESET 边界。

## 10. 3GPP 对应规范

| 规范 | 相关内容 | Clause/字段状态 |
|---|---|---|
| TS 38.211 | PDCCH 的 REG/CCE 到 RE 映射、调制和 DM-RS | PDCCH 相关 §7.3.2 子条款；Release/子条款 `NEEDS_EXTERNAL_REFERENCE` |
| TS 38.213 | CORESET 与 Search Space 的监测和候选规则 | 控制信道接收相关 §10 范围；`NEEDS_EXTERNAL_REFERENCE` |
| TS 38.331 | `ControlResourceSet` ASN.1 配置字段 | 字段版本和取值需外部核验 |

本地 [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]] 与 [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|TS 38.213]] 仅提供职责边界，不足以证明项目当前网络配置。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

| 函数/接口 | 用途 | 状态 |
|---|---|---|
| `nrPDCCHSpace` | 结合 CORESET/Search Space 生成候选资源或 PDCCH DM-RS 索引的示例入口 | `NEEDS_EXTERNAL_REFERENCE`；核对输入结构和版本 |
| `nrExtractResources` | 依据 CORESET 产生的索引提取资源网格 | `NEEDS_EXTERNAL_REFERENCE` |

当前 Vault 没有独立 MATLAB CORESET 脚本。对象名称、属性和位图编码不得凭记忆补写；先在本机 5G Toolbox 版本中运行 `help`/示例并保存配置快照。

## 12. 本项目中的用途

CORESET 是从“已知小区/配置”进入 PDCCH 盲搜的物理门：

1. 从 RRC/设备元数据取得 CORESET 配置。
2. 结合 [[03-PDCCH/CCE REG|CCE REG]] 生成控制 RE 掩码。
3. 交给 [[03-PDCCH/Search Space|Search Space]] 产生实际候选。
4. 供 [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]] 逐候选提取 DM-RS、软解调和 CRC/RNTI 判决。
5. 将通过的 [[03-PDCCH/DCI|DCI]] 转换为 [[04-PDSCH/PDSCH|PDSCH]] 资源，避免全带宽盲搜。

## 13. 常见误区

- 把 CORESET 当成一个必然承载 PDCCH 的固定波形；它只是可用资源集合。
- 把 CORESET 的频域位图直接当作 CCE 顺序，忽略 REG bundle/interleaver/shift。
- 把 BWP 局部 PRB 号直接当作载波绝对子载波号。
- 不检查 TDD 符号方向，在 UL 或 guard 符号上强行解 PDCCH。
- 配置切换后继续复用旧 CORESET 掩码，导致所有候选看似译码失败。

## 14. 与相似概念的区别

| 概念 | 定义 | 与 CORESET 的区别 |
|---|---|---|
| Search Space | 监测时机和候选规则 | 依附/引用 CORESET，但还定义何时、多少候选 |
| CCE | PDCCH 聚合和候选的逻辑单位 | CORESET 内由 REG 组织出来 |
| REG | 一个控制资源组的物理组织单位 | 由 CORESET 映射到 RE |
| BWP | 更大的带宽部分上下文 | CORESET 是 BWP 内的控制子区域 |
| PDCCH | 实际发送的控制信道 | 在 CORESET 允许的资源中承载 |

## 15. 代码实现注意事项

- 为每个 CORESET 保存 `config_id`、Release/版本、来源和生效时间。
- 解码频域位图后先做边界/重叠检查，再生成 REG/CCE 索引。
- 保留 `local_prb`、`bwp_prb`、`absolute_subcarrier` 三套坐标。
- 把非交织和交织映射实现为显式、可测试的置换函数，禁止在候选循环中隐式重排。
- 用单个已知 CORESET 做无噪声资源覆盖测试，验证每个 RE 只被预期候选引用。
- 配置不完整时返回 `candidate_domain_status=NEEDS_VERIFICATION`，而不是使用常见配置默认值。

## 16. 待实验验证的问题

- [ ] 从一份真实 RRC/设备配置重建 CORESET 位图，并核对绝对频域坐标。
- [ ] 在非交织/交织映射下逐项比较 REG、CCE 和 RE 索引。
- [ ] 改变 BWP/Point A 偏移，确认局部和绝对坐标同步变化。
- [ ] 在 TDD 灵活符号和配置切换边界测试 CORESET 可用性。
- [ ] 统计错误 CORESET 配置导致的候选数、DM-RS 质量和盲搜尾延迟。

## 17. CORESET 0 与专用 CORESET

被动接收机不能把所有 CORESET 当成同一种配置来源。项目至少要区分“用于初始接入/公共控制的 CORESET 0”和 RRC 专用配置的 CORESET；两者的发现路径、关联 Search Space 和生效时机可能不同。

| 分支 | 常见配置来源 | 主要服务对象 | 接收端策略 | 证据状态 |
|---|---|---|---|---|
| CORESET 0 | MIB/PDCCH-ConfigSIB1 等初始接入相关信息 | 公共 Search Space、SI、RAR 等 | 先从同步/广播配置恢复坐标，再生成公共候选 | `STANDARD + partial`；精确字段需 Release 核验 |
| 专用 CORESET | RRC dedicated 配置 | UE-specific Search Space 和专用 DCI | 绑定 `bwp_id`、RRC 配置版本和 UE 上下文 | `STANDARD + partial`；字段版本需外部核验 |
| 恢复/特殊分支 | MAC/RRC 触发的恢复或专用过程 | 特定控制过程 | 不套用普通 C-RNTI 假设，保留触发原因 | `NEEDS_VERIFICATION` |

“CORESET 0”是配置语境，不是“第 0 个候选”，也不意味着该区域每个时隙都有 PDCCH。若只有 IQ 而没有 MIB/SIB/RRC 或可靠设备元数据，输出应是 `coreset_candidate`，不能伪造完整配置。

初始接收中由 MIB 的 `pdcch-ConfigSIB1` 进入 CORESET-0/SearchSpace0 的学习流程见 [[01-NR基础/SSB PBCH MIB]]；本页负责展开 CORESET 的配置、坐标与资源映射契约。

## 18. 频域资源的逐级解析

建议把 CORESET 频域解析拆成四步，并为每一步保存中间数组：

```text
原始 frequencyDomainResources
    -> 位图/资源组解码
    -> BWP 内局部 PRB 集合
    -> CORESET REG 集合（跨 duration 个符号）
    -> BWP/载波绝对子载波坐标
```

在常见 NR 表示中，频域位图按固定 PRB 资源组展开；可用的结构化表示为：

$$
\mathcal{K}_{local}
=\bigcup_{g:\,b_g=1}\{6g,6g+1,\ldots,6g+5\},
$$

其中 $b_g$ 是资源组位图，`6` 和位图长度属于目标 Release 的规范参数，当前只作为解析线索，标记 `NEEDS_EXTERNAL_REFERENCE`。不要把这段抽象式当成任意带宽下都可直接套用的常量。

随后使用显式坐标转换：

$$
k_{abs}=k_{base}(\mathrm{PointA},\mathrm{BWP},\mu)
      +12\,n_{PRB,abs}+k_{in\,PRB},
$$

并同时保留：

| 坐标 | 示例字段 | 用途 |
|---|---|---|
| 位图组坐标 | `bitmap_group` | 复原原始配置 |
| CORESET 局部 PRB | `coreset_prb` | 生成 REG/CCE |
| BWP PRB | `bwp_prb` | 与 DCI/PDSCH 资源对齐 |
| 载波绝对子载波 | `absolute_subcarrier` | IQ/FFT 提取和跨站记录 |

`k_base`、Point A 与 numerology 的具体转换必须绑定配置快照；任何一个偏移未知都应让 `candidate_domain_status=NEEDS_VERIFICATION`。

## 19. 时域范围与 CCE 容量

CORESET 的时域范围是同一时隙内的连续符号集合；Search Space 决定某个时隙是否实际监测。对配置快照，可以先做结构性计数：

$$
N_{REG}^{raw}=N_{PRB}^{CORESET}\times N_{sym}^{CORESET},
$$

在常见 PDCCH 基线中，一个 CCE 由固定数量的 REG 组织，故：

$$
N_{CCE}=\left\lfloor\frac{N_{REG}^{raw}}{N_{REG/CCE}}\right\rfloor.
$$

`N_{REG/CCE}` 的常见实现值为 6，但此处不把它硬编码为跨 Release 常量；应在目标 TS 38.211 版本中核对。若原始 REG 不能整除一个 CCE，余下资源不能静默拼接到下一个候选，必须记录 `unused_reg_count`。

时域检查至少包括：

- `start_symbol + duration_symbols` 不越过 slot 边界；
- 每个符号的 TDD 方向允许控制接收；
- Search Space 的 monitoring symbol 与 CORESET 范围有交集；
- 配置切换前后的 `config_id` 不被同一缓存条目混用。

## 20. 映射类型对资源顺序的影响

非交织与交织不是“同一组 RE 的两种排序显示”，它们会改变逻辑 CCE 到物理 REG 的对应关系。CORESET 解析器应输出完整置换，而不是只输出 `mapping_type` 字符串：

```js
mapping:
  type: "nonInterleaved|interleaved|unknown"
  reg_bundle_size: null
  interleaver_size: null
  shift_index: null
  logical_to_physical_reg: []
  physical_to_logical_reg: []
  verified_against_release: false
```

若字段缺失，后续候选可以停在 `candidate_generated`，但不能进入声称有效的 `valid_dci`。置换表应独立于 IQ 处理生成和缓存，便于在无噪声资源测试中逐项比对。

## 21. 配置生效与缓存失效

CORESET 不是静态全局常量。以下事件都应结束旧 `config_id` 的适用范围：

| 事件 | 必须失效的缓存 | 需要保留的关联 |
|---|---|---|
| BWP 切换 | 频域坐标、REG/CCE、候选索引 | 原 DCI 与旧 BWP 的快照 |
| RRC 重配置 | CORESET 位图、duration、映射参数 | 配置版本和生效 slot |
| TDD pattern 更新 | 可监测符号和方向过滤 | 更新前后的时间轴 |
| 小区/载波切换 | Point A、NCellID、同步坐标 | `cell_id + capture_id` |
| 设备采样率/FFT 改变 | IQ 到 grid 的索引缓存 | 原始采样参数 |

缓存键建议至少为 `(cell_id, bwp_id, coreset_id, config_id, numerology)`；不能只用 `coreset_id`。当快照缺少生效时刻时，候选状态应带 `configuration_age_unknown`。

## 22. CORESET 核验矩阵

| 测试 | 操作 | 预期不变量 | 失败定位 |
|---|---|---|---|
| 位图回放 | 同一快照编码后再解码 | 位图和局部 PRB 完全相同 | 位图/端序 |
| 坐标平移 | 只改变 BWP/Point A | 局部索引不变，绝对坐标按偏移平移 | 坐标转换 |
| duration 扰动 | 增减一个符号 | REG 数和合法符号集合同步变化 | 时域范围 |
| 映射切换 | non-interleaved/interleaved | 置换表改变，候选 RE 顺序可回放 | CCE-to-REG |
| 方向过滤 | 将符号标为 UL/guard | 候选变为 invalid，不读取该 RE | TDD 状态 |
| 配置切换 | 在相邻 slot 更新 `config_id` | 旧缓存不影响新候选 | 生命周期 |

无噪声资源测试只能证明索引闭环；它不能证明现场 IQ 的同步、信道估计或 PDCCH 译码已经通过。

## 23. Rel-17 V17.8.0 CORESET 核验基线

以下条目已对照 [ETSI TS 138 211 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf) §7.3.2 和 [ETSI TS 138 213 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) §10.1（访问日期 2026-09-05）：

| 项目 | 参考版本事实 | 对项目的约束 |
|---|---|---|
| CORESET 尺寸 | 频域为 `N_RB^CORESET` 个资源块，时域为 `N_symb^CORESET ∈ {1,2,3}` 个连续符号 | duration 越界必须拒绝 |
| REG 编号 | CORESET 内 REG 按“先符号、后最低 PRB”的 time-first 顺序从 0 编号 | 不可按二维数组默认顺序替代 |
| CCE 组成 | 一个 CCE 包含 6 个 REG | 与 [[03-PDCCH/CCE REG|CCE REG]] 的长度账本一致 |
| `frequencyDomainResources` | 常规配置按 DL BWP 中不重叠的 6-PRB 组表示；若启用 RB set/频域监测位置，解释基准随配置变化 | 保存位图组、RB set 和 `rb-Offset` 语境 |
| 映射参数 | `cce-REG-MappingType`、`reg-BundleSize`、`interleaverSize`、`shiftIndex` 共同决定置换 | 缺任一必需字段不得静默默认 |
| CORESET 0 | 参考版本基线采用交织映射、bundle size 6、interleaver size 2，shift 由小区 ID 派生 | 初始接入分支独立缓存 |

这份表只证明 **Rel-17 V17.8.0 参考版本** 的标准接口；现场设备可能使用其他 Release、专用扩展或不完整元数据，仍需用 `config_id` 和 `verified_against_release` 标注。

## 24. TCI、预编码粒度与 DM-RS 解释

CORESET 配置还可能通过 TCI/`precoderGranularity` 影响 PDCCH DM-RS 的等效信道解释：

- `sameAsREG-bundle` 语境下，可在同一 REG bundle 内使用相同的 DM-RS 预编码假设；
- `allContiguousRBs` 语境下，假设作用范围扩展到 CORESET 内连续资源块集合，并受 SSB/LTE CRS 不重叠约束；
- CORESET 0 与其他 CORESET 的 QCL/参考点规则不同，不能只用 `N_ID^cell` 和一个全带宽信道矩阵替代。

项目快照应保存 `tci_state_id`、`precoder_granularity`、QCL 参考和生效时刻。没有这些字段时，PDCCH DM-RS 质量可以作为候选证据，但不能声称完成端口/波束级信道估计。

## 25. 证据与当前状态

- `STANDARD + verified-reference`：本地 [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]]/[[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|TS 38.213]] 摘要，以及上面的 Rel-17 V17.8.0 参考版本条目。
- `PERSONAL_NOTE`：本页的坐标分层、配置快照和项目缓存约定。
- `NEEDS_EXTERNAL_REFERENCE`：当前项目 Release/现场 RRC 字段、RB set/`freqMonitorLocations` 分支、TCI/QCL 状态和 MATLAB 对象属性。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚无真实 RRC 快照与逐 RE 发送/接收对照结果。

## 26. Related Notes

- [[03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[03-PDCCH/Search Space|Search Space]]
- [[03-PDCCH/CCE REG|CCE REG]]
- [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
- [[03-PDCCH/DCI|DCI]]
- [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]
- [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|5G TDD 上下行监测与资源解析]]
- [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]]
- [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|3GPP TS 38.211]]
- [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|3GPP TS 38.213]]
