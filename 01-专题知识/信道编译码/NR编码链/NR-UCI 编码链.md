---
title: NR-UCI 编码链
aliases:
  - 5G NR UCI 编码链
  - UCI 控制信息编码流程
type: atomic
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - channel/uci
  - code/polar
  - process/encoding
  - process/decoding
  - evidence/3gpp
source:
  - 3GPP TS 38.212
  - 3GPP TS 38.211
  - 3GPP TS 38.213
simulation:
  - 仿真-无噪声编解码闭环
  - 仿真-Polar-AWGN-BLER
---

# NR-UCI 编码链

> [!abstract] 一句话结论
> UCI 包含 HARQ-ACK、CSI 和 SR 等上行控制信息，编码方式取决于载荷长度、承载信道和复用场景，可能使用小块码、Polar 或其他标准规定的处理；不能把所有 UCI 都直接套用 DCI 的 Polar 链。

## UCI 的信息类型

| 信息 | 作用 | 典型特征 |
|---|---|---|
| HARQ-ACK | 反馈下行数据是否正确接收 | 载荷通常较短，可靠性和时延敏感 |
| CSI | 报告信道状态、测量和推荐参数 | 长度和字段随配置变化 |
| SR | 请求上行资源 | 可能是极短控制指示 |

UCI 可以映射到 PUCCH，也可能与 UL-SCH 一起复用到 PUSCH。编码方式和物理映射必须结合承载信道、载荷长度和资源配置确定。

## 典型处理分支

```text
UCI 载荷
    ├── 短载荷
    │     ↓
    │   小块码或标准规定的短控制编码
    │     ↓
    │   率匹配、调制和 PUCCH/PUSCH 映射
    │
    └── 较长载荷或规定场景
          ↓
        CRC（如适用）
          ↓
        Polar 编码
          ↓
        率匹配与交织
          ↓
        PUCCH/PUSCH 映射
```

上图是学习用的分支概览，不是替代 TS 38.212 的完整判定表。具体的载荷阈值、CRC、编码类型、交织和率匹配规则必须按 UCI 传输方式实现。

可以把分支选择抽象为：

$$
\Psi(A_{UCI},\,\mathrm{carrier},\,\mathrm{resource},\,\mathrm{config})
\longrightarrow
\{\mathrm{short\ block},\mathrm{Polar},\mathrm{other\ standard\ branch}\}
$$

这里 $\Psi$ 不是一个只由载荷长度决定的阈值函数；承载信道、资源配置、是否与 UL-SCH 复用以及标准版本都可能参与判定。实现日志应记录分支选择原因，而不是只记录最终编码器名称。

## 分支选择与长度账本

UCI 编码器至少应先确定以下边界，再选择算法：

1. UCI 字段类型、字段顺序和总载荷长度。
2. 承载在 PUCCH 还是 PUSCH，以及对应的资源和调制配置。
3. 是否与 UL-SCH 复用，是否需要 CRC 或标准规定的附加校验。
4. 编码分支和目标输出长度 $E_{UCI}$。
5. 编码输出到物理资源的复用索引。

建议把 $A_{UCI}$、CRC 后长度 $K_{UCI}$、Polar 母码长度 $N_{UCI}$、目标长度 $E_{UCI}$ 分开记录。$E_{UCI}$ 是物理资源预算，不等于 UCI 有效载荷长度，也不等于 Polar 母码长度。

对确实进入 Polar 分支的场景，长度账本可写成：

$$
A_{UCI}
\xrightarrow{\mathrm{CRC/附加字段}}
K_{UCI}
\xrightarrow{\mathrm{构造信息集合}}
N_{UCI}
\xrightarrow{\mathrm{率匹配}}
E_{UCI}
$$

必须同时保存 $A_{UCI}$、$K_{UCI}$、$N_{UCI}$ 和 $E_{UCI}$ 的数值及其单位。常见错误是把 CRC 后的 $K_{UCI}$ 当成物理发送比特数，或者把 PUSCH 资源中为 UCI 预留的符号数直接当成编码输入长度。

## PUCCH 与 PUSCH

### PUCCH

PUCCH 专门承载上行控制信息。不同 PUCCH format 支持不同长度、符号数和调制方式，编码和映射随格式变化。接收端需要先依据资源配置恢复 UCI 候选，再执行对应的软解调和译码。

### PUSCH

UCI 可以与 UL-SCH 共同复用到 PUSCH。此时需要分配物理资源并按标准顺序处理：

```text
UL-SCH 编码比特 + UCI 编码比特
    ↓
按优先级和资源规则复用
    ↓
扰码、调制和 PUSCH 映射
```

接收端必须先分离 UCI 与 UL-SCH 的软信息，再分别译码。不能把复用后的整个比特序列当作一个 Polar 码字。

复用接收可以抽象为：

```text
PUSCH 软信息
  ↓
按照 UCI/UL-SCH 资源索引分离
  ├── UCI LLR → 对应短块码或 Polar 逆率匹配
  └── UL-SCH LLR → LDPC 逆率匹配
```

分离后的两个缓冲区都应检查长度、索引覆盖和功率/噪声标定。只检查最终 UCI 比特而不检查分离索引，难以定位复用错误。

可为每个复用软比特定义标签 $\mu(j)$：

$$
\mu(j)\in\{\mathrm{UCI},\mathrm{UL\text{-}SCH}\},
\qquad
\mathbf{L}_{\mathrm{UCI}}
=\{L[j]:\mu(j)=\mathrm{UCI}\}
$$

其中 $j$ 是复用后物理软比特坐标。分离后还要使用 UCI 自身的逆交织和逆率匹配索引，不能因为标签正确就假设同一序列顺序可直接送入译码器。

## UCI Polar 分支

当 UCI 使用 Polar 时，处理可抽象为：

```text
UCI 有效载荷
    ↓
按照标准添加 CRC 或相关校验
    ↓
输入交织
    ↓
信息位和冻结位安排
    ↓
Polar 变换
    ↓
率匹配到目标 E
    ↓
输出交织和物理层复用
```

极化码长 $N$、信息位数 $K$ 和传输长度 $E$ 由输入长度和物理资源共同决定。UCI 的 Polar 参数不能直接继承 DCI，因为承载信道、目标长度和复用规则不同。

接收端的 Polar 子分支应返回至少以下状态：

$$
\mathrm{UCI\ result}
\in\{\mathrm{decoded},\mathrm{crc\_fail},\mathrm{dtx},\mathrm{invalid\_configuration}\}
$$

`dtx` 表示没有形成可用的 UCI 候选或检测到未发送状态，不能与已经形成候选但 CRC 失败的 `crc_fail` 混为一类。

## 短块码分支

对于很短的 UCI，直接使用通用长 Polar 链可能带来不必要的开销或不符合标准。小块码通常通过较短的线性映射或专门的控制编码结构增加约束，再进行调制和映射。

实现时应明确：

- 输入载荷长度和字段顺序。
- 是否包含 CRC。
- 校验矩阵或编码映射表。
- 目标物理资源和输出长度。
- 接收端硬判决或软判决接口。

## UCI 与 HARQ 反馈

HARQ-ACK 的错误会影响网络对下行数据的重传判断，因此 UCI 的 BLER 可能比普通业务比特更敏感。仿真应区分：

- UCI 译码错误。
- ACK/NACK 语义错误。
- DTX 或未检测到 UCI。
- UCI 与 UL-SCH 复用造成的相互干扰。

不能只统计“任意比特错误”而不区分 ACK、NACK 和 DTX 的协议含义。

对 HARQ 反馈，建议同时统计发送语义 $s$ 与接收语义 $\hat{s}$：

$$
P_{\mathrm{semantic\ error}}
=P(\hat{s}\ne s,\;s,\hat{s}\in\{\mathrm{ACK},\mathrm{NACK}\})
$$

并单独报告：

$$
P_{\mathrm{miss}}
=P(\hat{s}=\mathrm{DTX}\mid s\in\{\mathrm{ACK},\mathrm{NACK}\})
$$

ACK 被误判为 NACK 可能引起不必要重传，NACK 被误判为 ACK 则可能阻止必要重传；两者的系统代价不同。

## 实现检查表

- 是否根据 UCI 类型、长度和承载信道选择正确编码分支？
- PUCCH format 或 PUSCH 资源是否与编码输出长度匹配？
- UCI 和 UL-SCH 复用索引是否可逆？
- Polar 分支的 CRC、冻结位、可靠性序列和率匹配是否正确？
- 接收端是否区分 ACK/NACK、CSI 和 SR 字段？
- 是否记录 DTX、CRC 失败和译码失败的不同状态？

## 常见误区

1. UCI 不是一种固定长度、固定编码的单一数据类型。
2. UCI 在 PUCCH 和 PUSCH 上的处理不能直接互换。
3. 所有 UCI 都使用 Polar 的说法过于简化。
4. 与 UL-SCH 复用时不能把 UCI 直接插入 UL-SCH 的 LDPC 输入。
5. ACK/NACK 语义错误、DTX 和普通比特错误会产生不同系统后果。

## 最小验证

1. 分别构造短 HARQ-ACK、SR、较长 CSI 和 PUSCH 复用场景。
2. 记录载荷长度、编码分支、目标输出长度和物理资源。
3. 在无噪声条件下验证每个分支的编码和译码闭环。
4. 对 PUSCH 复用场景检查 UCI/UL-SCH 软信息分离后长度和顺序。
5. 在 AWGN 下分别统计 UCI BLER、DTX、ACK/NACK 语义错误和 UL-SCH BLER。
6. 对每个编码分支记录 `decoded`、`crc_fail`、`dtx` 和 `invalid_configuration` 等状态，避免把不同失败原因合并为一个 BLER。
7. 在改变 UCI 与 UL-SCH 资源比例时，检查两类软信息的长度账本和索引映射仍然闭合。

## 关联笔记

- Polar：[[Polar-信道极化]]、[[Polar-冻结位]]、[[Polar-SCL 译码]]、[[Polar-率匹配]]。
- LDPC 复用对象：[[NR-UL-SCH 编码链]]。
- 基础：[[CRC 校验]]、[[软判决与 LLR]]。
- 标准：[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.213｜Physical layer procedures for control]]。
