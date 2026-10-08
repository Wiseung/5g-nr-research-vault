---
title: CCE REG
aliases:
  - CCE 与 REG
  - PDCCH CCE REG RE 映射
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - topic/cce
  - topic/reg
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 用户项目流程说明
related:
  - "[[03-PDCCH/CORESET|CORESET]]"
  - "[[03-PDCCH/Search Space|Search Space]]"
  - "[[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]"
---

# CCE REG

> [!abstract] 项目主线
> CCE、REG、RE 是 PDCCH 物理资源的三级坐标：候选以 CCE 为聚合单位，CCE 由 REG 组织，REG 再落到资源网格 RE。正确的层级和置换是从候选位置提取 PDCCH DM-RS/控制符号并完成 DCI 译码的前提。

## 1. 一句话定义

CCE（Control Channel Element）是 PDCCH 候选的聚合单位，REG（Resource Element Group）是 CORESET 内的控制资源组，RE（Resource Element）是具体的子载波-OFDM 符号资源元素。

## 2. 为什么项目需要它

被动监测设备拿到的是连续 IQ 或资源网格，而 Search Space 给出的是候选 CCE。只有正确完成 candidate CCE -> REG -> RE 解映射，才能把 PDCCH DM-RS 与控制调制符号分开，避免把错误的 RE 喂给 Polar/CRC 链。索引错误会表现为“所有 RNTI 都译码失败”，也会误导后续 C-RNTI 关联。

## 3. 它位于整个 5G 空口链路的什么位置

~~~text
CORESET 频域/时域资源
  -> REG 组织
  -> CCE-to-REG 映射
  -> Search Space 选择候选 CCE
  -> candidate CCE -> REG -> RE
  -> PDCCH DM-RS/控制符号提取
  -> PDCCH Blind Decoding -> DCI
~~~

CCE/REG/RE 只描述物理资源组织，不携带 C-RNTI 或 DCI 字段语义。

## 4. 输入

| 输入 | 作用 |
|---|---|
| CORESET 频域位图、持续符号和 BWP 坐标 | 构造可用 REG 集合 |
| CCE-to-REG 映射类型 | 决定 REG 顺序/置换 |
| REG bundle、interleaver、shift 等配置 | 生成交织映射 |
| Search Space 候选的首 CCE 与聚合等级 | 选择候选占用的 CCE |
| 资源网格/IQ 和同步坐标 | 读取实际复数样本 |
| PDCCH DM-RS 参数 | 分离参考符号和控制符号 |

精确字段名、位图解释和索引基准应从同一 Release 的 CORESET 配置快照取得。

## 5. 输出

每个候选至少输出以下显式索引和掩码：

~~~js
candidate_id: ""
aggregation_level: null
cce_indices: []
reg_indices: []
re_indices:
  dmrs: []
  data: []
  reserved: []
local_grid_coordinates: []
absolute_subcarrier_coordinates: []
mapping_status: "ready|out_of_range|overlap|NEEDS_EXTERNAL_REFERENCE"
~~~

data RE 的有序排列应直接供软解调使用；dmrs RE 供 [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]] 信道估计使用。不要只保存一个扁平样点数组而丢失逆映射关系。

## 6. 关键参数

| 参数                     | 含义                  | 记录要求                |
| ---------------------- | ------------------- | ------------------- |
| $N_{CCE}$              | 当前 CORESET 可用 CCE 数 | 由 REG 数和标准规则计算，版本化  |
| L                      | 候选聚合等级              | 与 Search Space 候选一致 |
| first_CCE              | 候选首 CCE             | 保存生成来源和索引基准         |
| REG bundle size        | REG 绑定粒度            | 不使用默认值              |
| interleaver size/shift | 交织置换参数              | 保存原始配置              |
| k/l                    | 子载波/OFDM 符号坐标       | 同时保存局部、BWP、绝对坐标     |
| DM-RS 位置               | 控制参考 RE             | 与数据掩码互斥             |
| 端口/层                   | 资源的空间上下文            | 不把端口号当作天线号          |

“一个 CCE 含多少 REG”“一个 REG 含多少 RE”虽有常见实现约定，仍应按适用 Release 的 38.211 条款核对，当前不写死为项目常量。

## 7. 时域位置

REG 的时域坐标来自 CORESET 的连续 OFDM 符号范围。候选聚合只改变 CCE 覆盖的资源数量/组合，不改变 CORESET 的时隙坐标。实现应在 frame、slot、symbol 三级记录每个 RE，并先应用 TDD 方向过滤；不能跨越 UL 或 guard 资源拼接一个候选。

## 8. 频域位置

REG 的频域坐标由 CORESET 位图选出的 PRB、BWP 起点和 Point A 偏移共同确定。CCE-to-REG 置换可能让逻辑相邻 CCE 映射到非相邻 REG，因此必须通过显式置换表生成 RE 顺序。局部 grid_index、BWP PRB 和载波绝对子载波号要分开保存。

## 9. 数学原理

资源网格中的一个 RE 可表示为：

$$
\mathrm{RE}=(k,l,p),
$$

其中 $k$ 为频域子载波、$l$ 为 OFDM 符号、$p$ 为端口/逻辑空间端口。令 CORESET 的可用 REG 集合为 $\mathcal{G}$，配置参数为 $\theta$，则 CCE 到 REG 的映射可抽象为：

$$
\mathrm{REG}_{c,r}=\pi(c,r;\theta),\qquad
\mathrm{CCE}_c=\{\mathrm{REG}_{c,r}\}_{r}.
$$

候选 $h$ 的资源集合为：

$$
\mathcal{R}_h
=\bigcup_{c\in\mathcal{C}_h}\bigcup_{r}
\mathrm{RE}\bigl(\mathrm{REG}_{c,r}\bigr),
$$

其中 $\mathcal{C}_h$ 是候选所占 CCE 集合。PDCCH DM-RS 与控制数据使用同一候选资源但不同 RE 子集：

$$
\mathcal{R}_h
=\mathcal{R}_{h,\mathrm{DMRS}}
\dot\cup
\mathcal{R}_{h,\mathrm{control}}
\dot\cup
\mathcal{R}_{h,\mathrm{reserved}}.
$$

具体置换 $\pi$、每个 CCE/REG 的固定数量和 DM-RS RE 位置属于标准映射细节，均标记 NEEDS_EXTERNAL_REFERENCE。

## 10. 3GPP 对应规范

| 规范 | 相关内容 | Clause/字段状态 |
|---|---|---|
| TS 38.211 | PDCCH 的 REG、CCE、RE 映射、调制和 DM-RS | PDCCH 相关 §7.3.2 子条款；版本/子条款 NEEDS_EXTERNAL_REFERENCE |
| TS 38.213 | CORESET/Search Space 对候选 CCE 的选择与监测 | 控制信道接收相关 §10 范围；候选规则 NEEDS_EXTERNAL_REFERENCE |
| TS 38.331 | CORESET 频域资源、持续长度和映射配置字段 | ASN.1 字段版本需外部核验 |

本地 [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]] 只确认资源坐标和物理映射职责；不应以本页抽象式替代规范表格。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

| 函数 | 用途 | 状态 |
|---|---|---|
| nrPDCCHSpace | 既有项目笔记中的候选/DM-RS 索引生成入口 | NEEDS_EXTERNAL_REFERENCE |
| nrExtractResources | 按索引提取候选 RE | NEEDS_EXTERNAL_REFERENCE |
| nrChannelEstimate | 用 DM-RS 估计候选信道 | NEEDS_EXTERNAL_REFERENCE |

当前 Vault 没有对 nrPDCCHSpace 返回数组的维度、索引基准或交织细节做本机验证。所有 MATLAB API 只作为外部文档线索，运行前需固定版本并保存 size、数据类型和坐标约定。

## 12. 本项目中的用途

CCE/REG/RE 是 PDCCH 盲搜的资源解码器：

1. 从 [[03-PDCCH/CORESET|CORESET]] 解出可用 REG。
2. 从 [[03-PDCCH/Search Space|Search Space]] 取得首 CCE、聚合等级和候选索引。
3. 用显式置换生成候选的 DM-RS/控制 RE 掩码。
4. 交给 [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]] 做信道估计、均衡和 Polar/CRC。
5. 通过 [[03-PDCCH/DCI|DCI]] 关联 C-RNTI 并驱动 [[04-PDSCH/PDSCH|PDSCH]] 资源提取。

## 13. 常见误区

- 把 CCE、REG、RE 当作同一个索引，或在不同层级重复乘/除一个固定因子。
- 忽略交织映射，直接按频率升序取 RE。
- 把 DM-RS RE 当成 DCI 数据 RE，导致 LLR 数量和顺序错误。
- 混用 0-based/1-based 索引，或把局部 BWP 下标当作绝对载波下标。
- 在候选越过 CORESET 边界时静默裁剪，而不是标记 invalid_candidate。
- 用一帧的映射缓存跨越 BWP/RRC/CORESET 配置变更。

## 14. 与相似概念的区别

| 概念 | 层次 | 主要作用 |
|---|---|---|
| RE | 资源网格最小坐标 | 具体子载波/符号/端口样本 |
| REG | 控制资源组 | 组织一个 PRB-符号范围内的控制 RE |
| CCE | 候选聚合单位 | 由多个 REG 组成，供 Search Space 选择 |
| Candidate | 监测候选 | 某时机、聚合等级和 CCE 组合 |
| CORESET | 配置资源集合 | 规定可用时频区域和映射上下文 |

## 15. 代码实现注意事项

- 用结构体保存 config_id、candidate_id、cce_indices、reg_indices 和 re_indices，不要依赖隐含排列。
- 建立 RE -> (k,l,p) 和逆映射单元测试，检查覆盖、互斥和顺序。
- 对 DM-RS、控制数据、保留资源分别维护布尔掩码，并检查交集为空。
- 在每个候选入口验证 first_CCE + L <= N_CCE；失败即返回状态，不进行越界读取。
- 保存原始和转换后的索引，便于与 MATLAB/参考实现逐项比较。
- 记录端口/层和 FFT/BWP 偏移，避免在后续 [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]] 估计时丢失域信息。

## 16. 待实验验证的问题

- [ ] 用已知 CORESET 和单候选做无噪声资源覆盖闭环，逐 RE 比较发送/接收索引。
- [ ] 分别验证非交织和交织 CCE-to-REG 映射，记录置换表和逆置换。
- [ ] 注入一个 RE 偏移、DM-RS 掩码错位和 BWP 偏移错误，确认故障可定位。
- [ ] 在不同聚合等级下核对 LLR 长度、DM-RS 数量和候选边界。
- [ ] 将生成的 re_indices 与 MATLAB 5G Toolbox 目标版本输出比对，补齐 clause/API 状态。

## 17. 三层坐标与有序资源

实现中应把三个层级建模为不同类型，而不是用一个整数数组表示全部索引：

| 层级 | 逻辑对象 | 必须保存的字段 | 可执行断言 |
|---|---|---|---|
| CCE | 候选聚合单位 | `cce_id`、`candidate_id`、`aggregation_level` | CCE 连续且位于 `0..N_CCE-1` |
| REG | CORESET 内控制资源组 | `reg_id`、PRB、OFDM symbol、bundle | 每个 REG 只属于一个逻辑映射位置 |
| RE | 资源网格最小坐标 | `k`、`l`、`p`、局部/绝对坐标 | 坐标在 BWP/slot/port 域内 |

候选的资源顺序不是“按频率升序重新排序”即可。发送端的调制符号顺序、PDCCH DM-RS 插入位置、CCE-to-REG 置换和接收端 LLR 顺序必须共享同一张显式索引表：

```js
resource_order:
  cce_order: []
  reg_order: []
  re_order_control: []
  re_order_dmrs: []
  inverse_control_order: []
  index_base: 0
  verified: false
```

## 18. 常见基线值与 Release 门

在 NR PDCCH 的常见基线中，通常需要核验以下关系：一个 CCE 由固定数量的 REG 组成，一个 REG 覆盖一个 PRB 的一个 OFDM 符号，一个 REG 包含一个 PRB 的 12 个子载波，PDCCH DM-RS 占用其中的固定 RE 子集，控制数据采用 QPSK。工程中经常见到“6 REG/CCE、12 RE/REG、3 个 DM-RS RE/REG、9 个控制 RE/REG”的组合，并由此得到每 CCE 的控制比特预算。

> [!warning] 版本化数值
> 上述数字是标准核验线索，不是本项目跨 Release 的常量。启用任何 `N_REG_PER_CCE`、`N_RE_PER_REG`、`N_DMRS_PER_REG` 或 `E_per_CCE` 常量前，必须记录目标 TS 38.211 版本、条款和逐 RE 对照结果；未核验时保持 `NEEDS_EXTERNAL_REFERENCE`。

若目标版本确认采用该基线，可在快照中显式记录推导：

$$
N_{RE,data/REG}=N_{RE/REG}-N_{RE,DMRS/REG},
$$

$$
E_{CCE}=N_{REG/CCE}\times N_{RE,data/REG}\times Q_m,
\qquad
E_{candidate}=L\times E_{CCE}.
$$

这里 $Q_m$、各项固定数量和是否存在其他保留 RE 都必须来自同一 Release；不能只凭 `L` 推断 LLR 长度。

## 19. CCE-to-REG 映射的实现分层

将映射拆成三个纯函数，便于分别测试：

```js
reg_domain = enumerate_coreset_regs(coreset_snapshot)
logical_cces = group_regs_into_cce(reg_domain, mapping_parameters)
physical_regs = apply_cce_to_reg_permutation(logical_cces, mapping_parameters)
candidate_regs = select_first_cce_and_aggregation(physical_regs, first_cce, L)
candidate_re = expand_reg_to_re(candidate_regs, dmrs_parameters)
```

### 19.1 非交织映射

非交织分支仍需明确“逻辑顺序”与“物理顺序”的定义。不能因为输出看起来连续就省略置换表；应保存 `logical_to_physical_reg`，并用逆表将接收 LLR 还原到编码比特顺序。

### 19.2 交织映射

交织分支至少涉及 REG bundle、interleaver size 和 shift。可抽象为：

$$
g_{physical}=\pi_{bundle,interleave,shift}(g_{logical};\theta),
$$

其中 $\pi$ 必须是可逆置换。实现应检查：

1. 每个逻辑 REG 恰好映射到一个物理 REG；
2. 置换后的 REG 仍落在 CORESET 的 PRB/符号集合；
3. 候选聚合取到的 CCE 不跨越无效 REG；
4. 逆置换恢复出的控制符号顺序与发送端一致。

具体 bundle/interleaver/shift 取值和排列公式属于 `NEEDS_EXTERNAL_REFERENCE`，不要用“常见配置”替代缺失字段。

## 20. DM-RS 与控制 RE 分离

PDCCH 候选资源应拆成互斥子集：

$$
\mathcal{R}_{candidate}
=\mathcal{R}_{DMRS}\dot\cup
\mathcal{R}_{control}\dot\cup
\mathcal{R}_{reserved}.
$$

对于每个 REG，至少保存以下掩码和顺序：

```js
reg_record:
  reg_id: null
  prb: null
  ofdm_symbol: null
  dmrs_re_offsets: []
  control_re_offsets: []
  reserved_re_offsets: []
  mask_intersections: []
  port: null
```

`mask_intersections` 非空时，候选必须停在 `invalid_candidate`；不能把 DM-RS 样点送进软解调器再期待 Polar 译码器“自行修复”。端口是逻辑空间端口，不等于物理天线编号。

PDCCH DM-RS 还需要独立的序列快照。序列初始化通常与小区/控制资源标识、时隙/符号和端口上下文有关；具体 `c_init`、序列长度、端口和映射位置属于 TS 38.211 的版本化细节，不能从普通 PDSCH DM-RS 配置直接复制：

```js
pdcch_dmrs_snapshot:
  candidate_id: ""
  scrambling_id: null
  frame: null
  slot: null
  symbols: []
  ports: []
  sequence_ref: ""
  re_offsets_per_reg: []
  power_assumption: "unknown"
  verified_against_release: false
```

接收端应分别记录“参考序列与观测的相关质量”和“参考 RE 是否从控制数据掩码排除”。前者低可能是信道/同步问题，后者错误则会直接改变 LLR 长度；两类故障不能合并成一个 `dmrs_fail`。

## 21. 从资源顺序到 LLR 顺序

发送端和接收端需要共享以下坐标链：

```text
control bit index
  -> scrambling bit index
  -> modulation symbol index
  -> control RE index
  -> REG/CCE/candidate index
  -> (k,l,p)
```

接收端逆向执行时，必须先按 `re_order_control` 提取，再按相同顺序恢复调制符号和 LLR。若把 RE 按二维网格默认列优先/行优先展开，可能出现“星座看似正常、DCI 全部 CRC 失败”的症状。日志应同时保存：

- 原始资源网格布局和数组 shape；
- `bit -> symbol -> RE` 索引表哈希；
- LLR 正负号、尺度、量化和噪声方差；
- 逆率匹配输入长度 `E` 与候选聚合等级。

## 22. 资源映射不变量

给定候选 $h$，至少检查以下关系：

$$
|\mathcal{C}_h|=L,
\qquad
\mathcal{R}_{DMRS}\cap\mathcal{R}_{control}=\varnothing,
$$

$$
\mathcal{R}_{candidate}\subseteq\mathcal{R}_{CORESET},
\qquad
|\mathrm{LLR}_{control}|=E_h.
$$

若目标 Release 的物理映射引入额外保留资源，需把它们加入第三个集合并更新长度账本。`E_h` 只在固定的编码、调制和资源配置下才可由索引计数得到。

## 23. 逐 RE 核验与故障注入

| 测试 | 扰动 | 应观察的结果 |
|---|---|---|
| 正逆映射 | 对 `reg_order` 做逆置换 | 原始 CCE/REG/RE 集合完全恢复 |
| DM-RS 错位 | 平移一个 RE | DM-RS 相关下降，控制掩码交集/LLR 长度异常 |
| BWP 偏移 | 只改变 BWP 起点 | 局部索引不变，绝对子载波整体平移 |
| 交织参数 | 改 bundle/shift | 置换表变化但集合覆盖不变 |
| 聚合等级 | L=1/2/4/8/16 等目标配置 | 候选 CCE 数、资源覆盖和 LLR 长度同步变化；具体集合需核验 |
| 越界 | `first_CCE+L>N_CCE` | 返回 `invalid_candidate`，不读取 IQ |
| 端口混用 | 交换端口标签 | 资源集合可相同但信道估计域不一致，必须报错/告警 |

逐 RE 对照应优先在无噪声、单端口、单候选条件下进行；通过后再加入交织、频偏、多径和多站采样差异。

## 24. Rel-17 V17.8.0 物理映射核验基线

以下内容已对照 [ETSI TS 138 211 V17.8.0 (Release 17)](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf)（访问日期 2026-09-05）中的 §7.3.2、§7.4.1.3；它是一个**参考版本快照**，不是当前项目网络的 Release 声明：

| 项目 | V17.8.0 核验结果 | 实现含义 |
|---|---|---|
| 聚合等级 | `1/2/4/8/16` 个 CCE | 候选 `L` 只能取配置/规范允许值 |
| CORESET 时域 | `N_symb^CORESET ∈ {1,2,3}` | duration 是连续 OFDM 符号数 |
| CCE 组成 | 1 CCE = 6 REG | 候选按 CCE 聚合 |
| REG 定义 | 一个 PRB 的一个 OFDM 符号 | REG 在 CORESET 内按 time-first 编号 |
| 非交织映射 | `L_bundle=6`、`R=1` | 逻辑/物理顺序仍需显式保存 |
| CORESET 0 基线 | 交织、`L_bundle=6`、`R=2`、`shift=N_ID^cell` | 不能套用普通专用 CORESET 默认值 |
| PDCCH 调制/端口 | QPSK、天线端口 `p=2000` | 控制 RE 按先 `k` 后 `l` 的升序映射 |

### 24.1 PDCCH 比特扰码

V17.8.0 的 PDCCH 物理比特扰码初始化可记为：

$$
c_{init}=\left(n_{RNTI}\,2^{16}+n_{ID}\right)\bmod 2^{31}.
$$

当 UE-specific Search Space 配置了 `pdcch-DMRS-ScramblingID` 时，`n_RNTI` 使用 C-RNTI；否则按规范分支取值（常见为 0），`n_ID` 使用配置的 PDCCH-DMRS scrambling ID 或小区 ID。这里的条件与 RNTI 的 CRC 掩码不同，必须分别记录。

### 24.2 PDCCH DM-RS

V17.8.0 §7.4.1.3 规定 PDCCH DM-RS 序列由伪随机序列生成。用 `n_s,f^mu` 表示帧内 slot 号、`l` 表示 slot 内 OFDM symbol 号时，初始化可写为：

$$
c_{init}=\left[2^{17}\left(14n_{s,f}^{\mu}+l+1\right)\left(2N_{ID}+1\right)+2N_{ID}\right]\bmod 2^{31}.
$$

映射到候选 REG 时使用固定的频域偏移集合（常见表达为 `k=n*N_sc^RB+4*k'+1`，`k'=0,1,2`），端口为 `p=2000`。参考点在 CORESET 0 与其他 CORESET 情形下不同，不能直接把 PDSCH DM-RS 的坐标公式复制过来。

因此 `pdcch_dmrs_snapshot` 至少要保存 `N_ID`、frame/slot/symbol、端口、参考点、REG/RE 偏移和序列版本；只保存相关峰值不能证明映射正确。

## 25. 证据与当前状态

- `STANDARD + verified-reference`：[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]] 的本地摘要，以及上面的 ETSI TS 138 211 V17.8.0 §7.3.2/§7.4.1.3 参考版本。
- `PERSONAL_NOTE`：本页的显式索引表、掩码不变量和实现分层。
- `NEEDS_EXTERNAL_REFERENCE`：当前项目 Release、频域位图/Point A 具体上下文、交织公式的现场配置适用性、MATLAB API 和任何跨版本差异。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚无工具箱/发送端逐 RE 对照和真实 IQ 结果。

## 26. Related Notes

- [[03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[03-PDCCH/CORESET|CORESET]]
- [[03-PDCCH/Search Space|Search Space]]
- [[03-PDCCH/DCI|DCI]]
- [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
- [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]
- [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析|NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]
- [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]
- [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]]
- [[04-PDSCH/PDSCH|PDSCH]]
