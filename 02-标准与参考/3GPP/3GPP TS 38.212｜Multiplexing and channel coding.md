---
title: 3GPP TS 38.212｜Multiplexing and channel coding
aliases:
  - 3GPP 38.212
  - NR 复用与信道编码
  - TS 38.212 编码标准
type: reference
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - evidence/3gpp
  - topic/channel-coding
  - process/encoding
  - process/decoding
  - process/rate-matching
source:
  - 3GPP TS 38.212
related:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.214
---

# 3GPP TS 38.212｜Multiplexing and channel coding

> [!abstract] 标准职责
> TS 38.212 规定 NR 的复用与信道编码过程，是 DL-SCH、UL-SCH、BCH、DCI、UCI 等传输或控制信息经过 CRC、信道编码、码块分段、率匹配和译码处理时的主要标准入口。

## 阅读定位

这份笔记用于记录标准条款和实现映射，不替代具体版本的标准原文。引用结论时必须补充：

- 3GPP 版本和发布日期。
- 具体章节、表格或图号。
- 使用的输入参数和承载类型。
- 与 38.211、38.213、38.214 的交叉引用。

标准条款可能随版本修订。未填写版本和条款的内容只能作为学习导航，不应标记为已核验结论。

## 版本与条款管理

建议为每个实现参数建立版本化记录：

| 字段 | 内容 |
|---|---|
| `release` | 适用 3GPP Release |
| `spec_version` | 文档版本号和发布日期 |
| `clause` | 章节、小节、表格或图号 |
| `carrier` | DL-SCH、UL-SCH、BCH、DCI 或 UCI |
| `parameter_snapshot` | 输入长度、$N$、$K$、$E$、RV 等 |
| `reference_result` | 参考实现或标准向量输出 |

版本升级时先比较条款和参数快照，再决定代码是否需要更新。不要只修改文件名或 Release 标签而保留旧的参数表。

## 主要覆盖范围

| 主题 | 在编码链中的位置 | 关联笔记 |
|---|---|---|
| CRC 附加与校验 | 传输块、码块或控制信息保护 | [[CRC 校验]] |
| LDPC 编码 | DL-SCH、UL-SCH 数据链 | [[NR-DL-SCH 编码链]]、[[NR-UL-SCH 编码链]] |
| LDPC 基图与提升 | 确定实际 QC-LDPC 结构 | [[LDPC-基图选择]]、[[LDPC-提升因子 Z]] |
| 码块分段 | 将长传输块拆成 LDPC 码块 | [[LDPC-码块分段]]、[[LDPC-CB-CRC]] |
| LDPC 率匹配 | 适配目标传输长度和 RV | [[LDPC-率匹配]] |
| Polar 编码 | BCH、DCI、部分 UCI 链 | [[NR-BCH 编码链]]、[[NR-DCI 编码链]]、[[NR-UCI 编码链]] |
| Polar 可靠性与冻结位 | 构造 Polar 母码 | [[Polar-可靠性序列]]、[[Polar-冻结位]] |
| Polar 率匹配 | 适配控制信道输出长度 | [[Polar-率匹配]] |
| UCI 复用 | UCI 与 UL-SCH 的编码或复用关系 | [[NR-UCI 编码链]]、[[NR-UL-SCH 编码链]] |

## 编码链总览

### DL-SCH/UL-SCH

```text
传输块
    ↓
TB-CRC
    ↓
码块分段与 CB-CRC
    ↓
LDPC 基图选择与提升
    ↓
LDPC 编码
    ↓
率匹配与 RV
    ↓
码块级联
    ↓
交给物理信道映射和调制过程
```

### BCH/DCI/Polar UCI

```text
控制或广播信息
    ↓
CRC（按承载类型）
    ↓
Polar 信息位与冻结位安排
    ↓
Polar 变换
    ↓
率匹配、交织和承载相关处理
    ↓
交给物理信道映射和调制过程
```

38.212 负责上述比特级处理；具体 RE、REG、CCE、PDSCH、PUSCH、PBCH 或 PDCCH 的物理资源映射应继续阅读 38.211。

## 承载分支的统一记账

不同承载虽然都可以抽象为“输入比特到发送比特”，但中间对象并不相同。数据链通常进入 LDPC，BCH、DCI 和部分 UCI 场景进入 Polar，UCI 还可能进入短块码或复用分支。实现首先要保存 `carrier`，再选择对应流程；不能先固定一个编码器，再用载荷长度去猜测标准分支。

### DL-SCH/UL-SCH 的 LDPC 记账

设传输块有效载荷长度为 $A$，传输块 CRC 长度为 $L_{TB}$，则传输块保护后的长度为：

$$
B=A+L_{TB}
$$

若需要码块分段，码块数记为 $C$。在适用码块 CRC 的场景，附加后的总长度可抽象为：

$$
B'=B+C L_{CB}
$$

若只有一个码块且标准流程不添加码块 CRC，则应使用 $B'=B$，不能机械地增加 $L_{CB}$。平均码块输入长度和 filler 数量可记为：

$$
K'=\left\lceil\frac{B'}{C}\right\rceil,
\qquad
F=C K'-B'
$$

其中 $F$ 是为了使各码块满足结构长度而引入的 filler 数量。实际码块长度、码块 CRC 条件、基图选择和提升因子仍应按目标 Release 的条款和表格确定。

选择基图和提升因子 $Z$ 后，QC-LDPC 校验矩阵可抽象为：

$$
\mathbf{H}_{BG,Z}\mathbf{x}^{\mathsf T}=\mathbf{0}\pmod 2
$$

这里 $\mathbf{H}_{BG,Z}$ 由基图中的移位块扩展得到。编码、译码和率匹配必须使用同一个基图、$Z$、filler 位置和母码坐标；只要其中一项不一致，长度仍可能正确但校验方程不会闭合。

若总目标发送长度为 $E$，各码块分配长度为 $E_r$，至少应满足：

$$
\sum_{r=0}^{C-1}E_r=E,
\qquad
E_r\in\left\{\left\lfloor\frac{E}{C}\right\rfloor,
\left\lceil\frac{E}{C}\right\rceil\right\}
$$

上式只表达总长度守恒；哪些码块获得较大的余数、RV 如何改变母码起点和哪些 filler 不参与发送，必须依据标准率匹配规则实现。

### BCH/DCI/Polar UCI 的记账

对进入 Polar 的控制或广播信息，设有效载荷为 $A$，CRC 或标准附加字段长度为 $L_C$，则：

$$
K=A+L_C,
\qquad
N=2^n,
\qquad
\mathbf{x}=\mathbf{u}\mathbf{G}_N\pmod 2,
\qquad
\lvert\mathbf{e}\rvert=E
$$

其中 $K$ 个比特进入信息集合，$N$ 是母码长度，$E$ 是率匹配后的目标长度。CRC 是否掩码、输入交织是否存在、冻结集合如何选择以及 $E$ 如何确定，都由承载类型和适用条款决定。

发送端和接收端应共享显式坐标映射：

$$
j\xrightarrow{\pi_{\mathrm{RM}}}i,
\qquad
L_{mother}(i)
=\sum_{j:\,\pi_{\mathrm{RM}}(j)=i}L_{physical}(j)
$$

该式说明重复发送位置必须在软信息域累加，未观测位置需要按照打孔或缩短规则初始化。对于 BCH/PBCH、DCI/PDCCH 和 UCI，不能因为 $N$ 或 $E$ 相同就复用未经验证的映射表。

## 标准过程的可逆边界

建议将 38.212 的输出分成三个可独立核验的边界：

1. **编码边界**：输入字段、CRC、码块或 Polar 信息集合到母码坐标。
2. **率匹配边界**：母码坐标到长度为 $E$ 的发送坐标，包含 RV、交织、打孔、缩短或重复。
3. **软信息边界**：物理层返回按发送坐标排列的 LLR，再逆率匹配回母码坐标。

边界上的长度不变量为：

$$
\lvert\mathbf{a}\rvert=A,
\quad
\lvert\mathbf{u}_{info}\rvert=K,
\quad
\lvert\mathbf{x}_{mother}\rvert=N,
\quad
\lvert\mathbf{e}\rvert=E
$$

边界上的坐标不变量则要求同一个索引函数在发送端和接收端互相解释。无噪声测试应逐项比较 CRC 后输入、母码字、率匹配输出和逆率匹配 LLR，不能只比较最终译码比特。

## 标准核验与实现约定

以下内容必须分开记录：

| 类别 | 示例 | 证据方式 |
|---|---|---|
| 规范事实 | 承载使用的编码分支、率匹配规则和参数限制 | Release、章节、表格或图号 |
| 理论关系 | $\sum E_r=E$、$\mathbf{H}\mathbf{x}^{\mathsf T}=0$ | 推导、单元测试和边界向量 |
| 实现约定 | 0-based 索引、LLR 正负号、数组布局 | 接口文档、参考代码和对照测试 |

测试日志至少保存版本、承载类型、$A/K/N/E$、$C$、基图、$Z$、RV、CRC 类型、交织版本、LLR 定义和随机种子。版本升级后，应重新核验受影响的表格和流程，而不是仅修改配置字符串。

## 长度账本与可逆接口

接收端能否闭环，取决于每个阶段的长度和坐标都可追踪。建议对一条链路保存：

$$
A\rightarrow K\rightarrow N\rightarrow E
$$

其中 $A$ 是有效载荷长度，$K$ 是加入 CRC 或标准附加字段后的编码输入长度，$N$ 是母码长度，$E$ 是实际发送长度。LDPC 多码块场景还要展开为 $C$ 个码块和 $E_r$ 分配；Polar 场景还要保存信息集合、冻结集合和交织索引。

长度一致不代表坐标一致，因此还应记录：

- CRC 覆盖范围和比特顺序。
- 码块分段、filler 和重组位置。
- 基图、提升因子或 Polar 可靠性集合。
- 率匹配发送位置到母码位置的映射。
- 接收端 LLR 符号、量化和未观测位置初始化。

## 标准阅读顺序

1. 先确定信息类型和承载信道：DL-SCH、UL-SCH、BCH、DCI 或 UCI。
2. 确定输入比特长度、CRC 类型和编码分支。
3. 计算码块数、基图、提升因子、母码长度和率匹配目标长度。
4. 记录所有交织、扰码前后的比特顺序。
5. 对照物理信道标准确认输出比特如何进入资源网格。
6. 接收端按逆顺序记录 LLR、逆率匹配和 CRC 判决。

## 发送端与接收端边界

标准过程可以按三个边界交接：

1. **编码边界**：输入字段到母码字，输出是长度和坐标已定义的编码比特。
2. **物理映射边界**：母码率匹配输出到 38.211 的扰码、调制和资源映射。
3. **软信息边界**：接收端从物理符号恢复按同一坐标排列的 LLR，再进入逆率匹配和译码。

每个边界都应有独立向量测试。把整个链路一次性运行后只比较最终 CRC，无法准确定位边界错误。

## 实现参数清单

| 参数 | 记录要求 |
|---|---|
| 承载类型 | DL-SCH、UL-SCH、BCH、DCI 或 UCI |
| 输入长度 | 明确是否包含 CRC |
| CRC | 类型、长度、附加位置和掩码 |
| 码块 | $C$、$K'$、CB-CRC 和 filler bits |
| LDPC | BG、$Z$、母码长度和译码算法 |
| Polar | $N$、$K$、可靠性序列和冻结集合 |
| 率匹配 | $E$、$E_r$、RV、交织和索引 |
| 译码 | LLR 约定、最大迭代次数或列表大小 |
| 版本 | 3GPP 版本、章节和表格定位 |

## 证据记录模板

```markdown
## 标准核验记录

- 版本：
- 发布日期：
- 承载类型：
- 条款/表格：
- 输入参数：
- 标准结论：
- 实现位置：
- 仿真验证：
- 当前状态：待核验
```

## 常见误区

1. 38.212 不是所有 NR 物理映射规则的唯一来源。
2. “标准采用 LDPC/Polar”不等于已经实现了完整编码链；长度、索引和率匹配仍需落实。
3. 不同承载类型不能只凭编码类型共享全部参数。
4. 没有版本、章节和表格定位的标准摘录难以复核。
5. 标准规定的过程与某个软件库的 API 名称不是同一层级的证据。

## 最小核验

1. 选一个 DL-SCH 码块和一个 DCI Polar 配置。
2. 记录版本、条款、输入长度、编码参数和目标输出长度。
3. 用独立参考实现完成无噪声编解码闭环。
4. 逐项比较 CRC、分段、码字、率匹配索引和译码输出。
5. 将差异归因到标准版本、比特顺序、LLR 约定或实现错误。
6. 对每个边界保存中间向量：CRC 后输入、母码字、率匹配输出、逆率匹配 LLR 和译码结果。
7. 使用一个错误注入矩阵分别扰动长度、CRC 位序、码图/可靠性集合、率匹配索引和 LLR 符号，确认诊断能定位到对应阶段。

## 关联标准和笔记

- 物理信道与调制：[[3GPP TS 38.211｜Physical channels and modulation]]。
- 控制过程：[[3GPP TS 38.213｜Physical layer procedures for control]]。
- 数据过程：[[3GPP TS 38.214｜Physical layer procedures for data]]。
- 信道模型：[[3GPP TR 38.901｜Channel model]]。
- 总入口：[[5G 信道编译码]]。
