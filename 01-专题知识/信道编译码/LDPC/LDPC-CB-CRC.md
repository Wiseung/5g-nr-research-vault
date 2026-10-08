---
title: LDPC-CB-CRC
aliases:
  - LDPC 码块 CRC
  - Code Block CRC
type: atomic
status: seed
tags:
  - domain/5g-nr
  - code/ldpc
  - code/crc
  - process/segmentation
  - process/error-detection
  - evidence/3gpp
source:
  - 3GPP TS 38.212
simulation:
  - 仿真-率匹配正确性验证
  - 仿真-无噪声编解码闭环
---

# LDPC-CB-CRC

> [!abstract] 一句话结论
> CB-CRC 是码块分段后附加到各个 LDPC 输入块上的错误检测信息，用于判断单个码块的译码结果；它与传输块 CRC 覆盖的比特范围、失败处理和重组位置不同。

## 为什么需要 CB-CRC

一个长传输块可能被拆成多个 LDPC 码块。每个码块独立进行译码，如果只在最后检查 TB-CRC，接收端难以知道具体哪个码块失败，也无法利用码块级状态进行调试和译码控制。

CB-CRC 提供码块级判据：

```text
传输块
    ↓
TB-CRC
    ↓
码块分段
    ↓
每个码块附加 CB-CRC
    ↓
独立 LDPC 编码与译码
    ↓
各码块 CB-CRC 检查
    ↓
码块重组与 TB-CRC 检查
```

## 与 TB-CRC 的区别

| 项目 | TB-CRC | CB-CRC |
|---|---|---|
| 覆盖范围 | 整个传输块 | 单个码块 |
| 附加时机 | 码块分段前 | 码块分段后、LDPC 编码前 |
| 主要用途 | 最终传输块接收判决 | 码块级错误定位和译码判决 |
| 检查时机 | 码块重组后 | 每个码块译码后 |
| 失败影响 | 整个传输块通常不可交付 | 对应码块失败，最终通常导致 TB-CRC 失败 |

CRC 通过只说明对应比特范围满足校验。必须结合码块索引和传输块状态解释结果。

若第 $r$ 个码块的待保护数据为 $\mathbf{d}_r$，CB-CRC 生成函数为 $g_{CB}$，则可以抽象写为：

$$
\mathbf{u}_r
=\operatorname{append}_{g_{CB}}(\mathbf{d}_r)
$$

接收端得到候选 $\hat{\mathbf{u}}_r$ 后，只检查同一覆盖集合上的余数：

$$
q_r
=\mathbf{1}\left[
\operatorname{CRC}_{CB}(\hat{\mathbf{u}}_r)=0
\right]
$$

这里的 $q_r$ 是检测判据，不是纠错输出；它不能把错误候选变回正确的 $\mathbf{d}_r$。

## CB-CRC 的覆盖范围

CB-CRC 的输入是分段后分配给某个码块的数据部分，而不是：

- 原始传输块的全部比特。
- 已经 LDPC 编码后的母码字。
- 率匹配后的物理发送比特。
- 包含 filler bits 的完整 LDPC 输入向量。

概念上，单个码块的顺序应记录为：

```text
分段数据
    ↓ CB-CRC 计算
数据 + CB-CRC
    ↓ filler/LDPC 输入布局
LDPC 编码
```

具体 CRC 多项式、比特顺序和附加位置必须以 38.212 适用版本为准；本笔记中的 `CB-CRC` 表示标准规定的码块校验，不应由通用 CRC 库的默认参数替代。

## 附加规则

在 NR LDPC 码块分段中，是否需要 CB-CRC 取决于传输块 CRC 后长度是否需要分成多个码块。多码块场景通常为每个码块附加 24 位 CB-CRC；单码块场景一般不增加 CB-CRC。

实际实现需要按 TS 38.212 的 `B`、`K_cb`、`C` 和 `L` 定义执行，不能仅以业务层的原始长度 `A` 判断。一个常见的抽象判定是：

```text
B = A + TB-CRC 长度
若 B <= K_cb：C = 1，通常不附加 CB-CRC
若 B > K_cb：C > 1，按标准附加 CB-CRC
```

这里的 `K_cb` 随基图变化，`B` 是 TB-CRC 后长度，不是未经 CRC 的业务长度。

从事件角度看，多码块 CB-CRC 可以把一个传输块错误定位到码块索引集合：

$$
\mathcal{F}_{CB}
=\{r\mid q_r=0\}
$$

若 $\mathcal{F}_{CB}=\varnothing$ 但 TB-CRC 失败，优先检查 TB 重组顺序、TB-CRC 覆盖范围或未检出错误；若 $\mathcal{F}_{CB}\ne\varnothing$，则应沿失败码块的 LLR、率匹配索引和译码状态继续定位。

## 单码块场景的边界

“单码块通常没有 CB-CRC”是流程概览，不应写成无条件的编码器规则。实现应根据标准中的分段分支决定：

1. 计算 TB-CRC 后长度。
2. 判断是否触发码块分段。
3. 根据分段结果决定是否生成 CB-CRC。
4. 在输出日志中记录 `C` 和实际 CRC 层级。

边界测试尤其要覆盖刚好不需要分段、刚好触发多码块，以及因基图或提升因子变化而改变输入布局的长度。

## CRC 比特与码块布局

每个码块的布局可抽象为：

```text
分段得到的码块数据
    +
CB-CRC
    +
必要的 filler bits
    ↓
LDPC 编码输入
```

具体比特排列、CB-CRC 计算顺序和 filler bits 位置必须与标准条款及编码器实现一致。不要把 CB-CRC 当作独立的 LDPC 校验位，也不要在 LDPC 编码后再追加 CB-CRC。

## 接收端检查

接收端对每个码块执行：

1. 逆率匹配，恢复该码块的 LLR。
2. LDPC 软输入译码。
3. 移除或忽略 filler bits。
4. 提取码块数据和 CB-CRC。
5. 重新计算 CB-CRC 并比较。
6. 记录码块索引、译码状态和校验结果。

之后再移除 CB-CRC、级联数据并执行 TB-CRC。若 CB-CRC 与 TB-CRC 的覆盖范围实现错误，可能出现码块看似通过但传输块始终失败的现象。

CB-CRC 的检查顺序可以写为：

$$
\hat{\mathbf{u}}_r
\xrightarrow{\operatorname{remove}(F)}
\hat{\mathbf{d}}_r\Vert\hat{\mathbf{p}}_r
\xrightarrow{\operatorname{CRC}_{CB}}
q_r
$$

其中 $F$ 表示 filler 坐标，$\hat{\mathbf{p}}_r$ 表示提取出的 CB-CRC 字段。先后顺序错误，例如把 filler 当作 CRC 输入，或在错误坐标上截取 CRC，都会使固定向量系统性失败。

## 码块判决状态

建议为每个码块保存结构化状态：

| 状态 | 含义 |
|---|---|
| `ldpc_not_converged` | 达到译码上限仍未满足停止条件 |
| `syndrome_fail` | 输出未满足 LDPC 校验约束 |
| `cb_crc_fail` | 译码输出未通过 CB-CRC |
| `cb_crc_pass` | 码块数据通过 CB-CRC |
| `invalid_layout` | filler、CRC 或码块边界不合法 |

`cb_crc_fail` 和 `invalid_layout` 都可能使传输块失败，但前者是信道/译码结果问题的候选，后者更可能是接口实现错误。把所有状态压缩成一个布尔值会降低调试效率。

## 与软信息和早停的关系

CB-CRC 通常在 LDPC 输出信息比特后执行，而不是直接替代校验节点更新。可以采用两种早停层次：

- **图级早停**：硬判决满足所有 LDPC 校验方程。
- **码块级确认**：提取数据和 CB-CRC 后通过校验。

图级早停更早、开销更低，但可能只说明输出是某个合法码字；CB-CRC 更贴近码块数据是否正确的判据，但需要完成信息提取和 CRC 计算。实验应记录停止原因。

从候选集合看：

$$
\{\hat{\mathbf{c}}:\mathbf{H}\hat{\mathbf{c}}^T=0\}
\supseteq
\{\hat{\mathbf{c}}:\mathrm{CB\text{-}CRC}=0\}
$$

前一个集合是所有合法 LDPC 码字，后一个集合还要求提取出的信息和 CRC 字段相互匹配；二者的交集才是更强的可接受候选。

## 与 HARQ 的关系

CB-CRC 是译码质量的码块级证据，但 HARQ 反馈通常围绕传输块或规定的传输过程形成。失败码块的软信息可在后续重传中继续合并；不能因为某次 CB-CRC 失败就把其他码块的软信息丢弃，除非具体接收机策略如此规定。

## 常见误区

1. TB-CRC 和 CB-CRC 使用位置不同，不能用同一个 CRC 结果替代另一个。
2. CB-CRC 不能纠正错误，只能检测译码结果是否可接受。
3. CB-CRC 长度和多码块条件不能凭经验固定到所有输入长度。
4. CB-CRC 的输入必须是分段后的指定比特，不是任意截取的码块数据。
5. 仅检查 LDPC 校验方程通过，不能替代 CB-CRC 检查。
6. CB-CRC 的失败状态不能单独定位物理层根因，仍需结合 LLR、码块布局和译码器状态。

## 最小验证

1. 构造一个需要多个码块的传输块，记录 $C$ 和各码块长度。
2. 逐个计算并验证 CB-CRC 附加后的长度。
3. 无噪声闭环中检查每个码块 CB-CRC 和最终 TB-CRC。
4. 只翻转一个码块的数据，确认对应 CB-CRC 失败并能定位码块索引。
5. 对单码块输入测试是否错误地附加了 CB-CRC。
6. 使用两个码块且只破坏其中一个，确认失败码块索引、其他码块状态和 TB-CRC 结果分别记录。
7. 将 CB-CRC 覆盖范围故意改为包含 filler，确认固定测试向量能够发现错误。

## 关联笔记

- CRC 基础：[[CRC 校验]]。
- 分段：[[LDPC-码块分段]]。
- 链路：[[NR-DL-SCH 编码链]]、[[NR-UL-SCH 编码链]]。
- 译码：[[LDPC-置信传播译码]]、[[LDPC-Min-Sum 译码]]。
