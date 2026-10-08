---
title: NR-UL-SCH 编码链
aliases:
  - 5G NR 上行共享信道编码链
  - UL-SCH LDPC 编码流程
type: atomic
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - channel/ul-sch
  - code/ldpc
  - process/encoding
  - process/decoding
  - evidence/3gpp
source:
  - 3GPP TS 38.212
  - 3GPP TS 38.211
  - 3GPP TS 38.214
simulation:
  - 仿真-无噪声编解码闭环
  - 仿真-LDPC-AWGN-BLER
---

# NR-UL-SCH 编码链

> [!abstract] 一句话结论
> UL-SCH 承载上行数据信息，主要采用与 DL-SCH 同族的 LDPC 数据编码流程，但最终通常通过 PUSCH 发送，并可能与 UCI 共同复用资源；因此需要同时关注 LDPC 编码、率匹配、HARQ 和 UCI 复用接口。

## 适用范围

UL-SCH 是上行共享传输信道，经过物理层处理后通常映射到 PUSCH。它承载终端发送给网络的数据，也可能与 HARQ-ACK、CSI 等 UCI 共同占用 PUSCH 资源。

本笔记先描述 UL-SCH 自身的 LDPC 链路。PUSCH 上 UCI 的具体复用、优先级和资源映射应结合 [[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.211｜Physical channels and modulation]] 与 [[3GPP TS 38.213｜Physical layer procedures for control]] 阅读。

## 从 PUSCH 资源到 UL-SCH 发送长度

在只发送 UL-SCH 且忽略具体标准分配边界的理想记账下，可用编码比特数近似为：

$$
E_{\mathrm{PUSCH,ideal}}
=Q_m\,\nu\,N_{\mathrm{RE,data}}
$$

其中 $Q_m$ 是调制阶数对应的每符号比特数，$\nu$ 是层数，$N_{\mathrm{RE,data}}$ 是扣除 DM-RS、PTRS 和其他开销后的数据 RE 数量。存在 UCI 时，UL-SCH 不能简单写成“总资源减去原始 UCI 比特数”；实际分配还受 UCI 类型、优先级、编码方式和资源不足处理约束。

因此应记录两套数量：

$$
E_{\mathrm{PUSCH}}
\longrightarrow
\left(E_{\mathrm{UL}},E_{\mathrm{ACK}},E_{\mathrm{CSI}},E_{\mathrm{SR}}\right)
$$

右侧表示各类信息实际占用的编码或复用位置，而不是把所有字段拼成一个 UL-SCH 输入向量。

## 发送端流程

```text
MAC 传输块 A
    ↓
传输块 CRC 附加
    ↓
码块分段与必要的 CB-CRC 附加
    ↓
LDPC 基图选择
    ↓
选择提升因子 Z 并插入 filler bits
    ↓
LDPC 编码
    ↓
每个码块率匹配到 E_r
    ↓
码块级联
    ↓
与 UCI 按标准规则复用（若存在）
    ↓
PUSCH 扰码、调制与资源映射
```

当 PUSCH 同时承载 UL-SCH 和 UCI 时，不能把 UCI 当作普通业务比特直接拼接到 UL-SCH 的 LDPC 输入中。二者有独立的编码或处理规则，之后再按照标准规定的资源和优先级进行复用。

## 接收端流程

```text
PUSCH 解映射
    ↓
信道估计、均衡和软解调
    ↓
PUSCH 解扰
    ↓
分离 UL-SCH 与 UCI 软信息
    ↓
UL-SCH 逆率匹配与 HARQ 软合并
    ↓
LDPC 译码
    ↓
码块 CRC 与传输块 CRC 检查
    ↓
输出数据并形成 HARQ 反馈
```

分离 UCI 和 UL-SCH 是接收端的重要边界。如果复用位置、比特数或可靠性排序错误，可能表现为 LDPC 译码器输入异常，即使 LDPC 本身实现正确也无法恢复数据。

## 上行参数依赖关系

UL-SCH 的编码参数由上行调度和 PUSCH 配置共同决定：

```text
上行授权、PUSCH 资源和 MCS
    ↓
可用 RE、层数、调制阶数和 UCI 开销
    ↓
UL-SCH 目标传输长度与 TBS
    ↓
TB-CRC、码块分段、BG、Z 和 LDPC 编码
    ↓
UL-SCH 率匹配与 UCI 复用
    ↓
PUSCH 调制、功率控制和发送
```

如果 UCI 占用了部分 PUSCH 资源，UL-SCH 可使用的比特数会随之变化。不能先独立确定 UL-SCH 的 $E$，再把 UCI 当作超出资源预算的附加字段。

## UCI 复用前后的长度账本

建议分别记录：

| 对象 | 变量或字段 | 说明 |
|---|---|---|
| UL-SCH 输入 | $A_{UL}$ | TB-CRC 前的有效数据长度 |
| UL-SCH 编码输出 | $E_{UL}$ | 率匹配后的 UL-SCH 比特数 |
| HARQ-ACK | $O_{ACK}$ | ACK/NACK/DTX 相关控制字段长度 |
| CSI/SR | $O_{CSI},O_{SR}$ | 其他 UCI 字段长度 |
| PUSCH 总资源 | $E_{PUSCH}$ | 当前资源可承载的总编码比特数 |
| 复用结果 | 索引表 | 每个输出位置属于哪一类信息 |

必须验证复用索引是双射或按标准规则可逆：接收端按照索引分离后，UL-SCH 和各 UCI 字段的长度、顺序和软信息数量都应恢复。

可以把复用器表示为一个带标签的坐标映射：

$$
\mu(j)\in\{\mathrm{UL\text{-}SCH},\mathrm{ACK},\mathrm{CSI},\mathrm{SR},\mathrm{unused}\}
$$

接收端先根据 $\mu(j)$ 分离软信息，再分别执行逆率匹配或对应的 UCI 译码。若只保存每类字段的长度而不保存坐标映射，遇到交织、优先级变化或资源不足时仍可能出现顺序错误。

## UCI 优先级与资源竞争

当多个 UCI 字段与 UL-SCH 同时存在时，资源不足可能触发字段丢弃、缩短、优先级调整或其他标准规定的处理。实验应记录：

- 每类 UCI 的优先级和原始长度。
- PUSCH 可用资源和 DM-RS/控制开销。
- 资源不足时实际保留的字段。
- 发送端复用顺序和接收端分离顺序。
- 被丢弃字段是否计入业务错误还是未发送状态。

不能把 UCI 资源不足导致的字段缺失归咎于 LDPC 译码器。

## 与 DL-SCH 的共同点和差异

| 项目 | DL-SCH | UL-SCH |
|---|---|---|
| 典型物理承载 | PDSCH | PUSCH |
| 数据主编码 | LDPC | LDPC |
| 传输块 CRC | 有 | 有 |
| 码块分段 | 按长度需要执行 | 按长度需要执行 |
| 率匹配与 RV | 有 | 有 |
| 重点复用问题 | 与下行控制和数据资源协调 | 可能与 UCI 共同复用 |
| HARQ 方向 | 网络向终端下发 | 终端向网络上行 |

两条链路共享 LDPC 结构知识，但资源分配、物理映射、UCI 共存和功率控制等过程不能直接照搬。

## UL-SCH 与 HARQ

UL-SCH 的重传通常使用冗余版本和软信息合并。接收端应将不同次传输映射到同一个母码字位置，再合并 LLR：

$$
L_{\mathrm{combined}}(i)=\sum_{t=1}^{T}L_t(i)
$$

其中只有来自同一母码字位置的软信息才能直接相加；不同 RV 的率匹配索引必须先恢复到统一位置。实际系统还要考虑功率、信道变化和软缓冲区大小。

不同传输的 LLR 还受到上行功率控制和瞬时信道增益影响。更一般地，可写为：

$$
L_{\mathrm{combined}}(i)
=\sum_{t=1}^{T}w_t(i)L_t(i)
$$

其中 $w_t(i)$ 用于补偿不同传输的噪声方差或 LLR 缩放。若第 2 次传输信道更差却仍使用相同权重，软合并可能过度放大低可信观测。

若 UL-SCH 传输块包含 $C$ 个码块，并以任一码块失败导致 TB 失败为判据，则独立性近似下：

$$
P_{\mathrm{TB\text{-}BLER}}
\approx1-\prod_{r=0}^{C-1}
\left(1-P_{\mathrm{CB\text{-}BLER},r}\right)
$$

不同码块实际共享同一时频资源和信道实现，独立性通常只是近似；实验中应同时报告 CB-BLER 和 TB-BLER，而不是用上式替代直接统计。

## UCI 复用接收机状态

```text
PUSCH 资源解映射
    ↓
联合信道估计和均衡
    ↓
软解调/解扰
    ↓
按复用索引分离 UCI 与 UL-SCH
    ├── UCI 译码与语义判决
    └── UL-SCH 逆率匹配、HARQ 合并和 LDPC 译码
    ↓
生成数据交付和 HARQ 反馈状态
```

UCI 和 UL-SCH 可能共享信道估计，但不应共享同一个译码状态。记录时要区分 `uci_decode_fail`、`ulsch_tb_crc_fail`、`uci_dtx` 和 `mux_index_error`。

## 上行链路的功率因素

上行数据和控制的相对功率会影响软解调输出的幅度和两类信息之间的干扰。对比 UCI 复用前后性能时应固定或记录：

- PUSCH 发射功率和功率控制闭环。
- UCI 与 UL-SCH 的功率分配。
- 信道估计使用的参考信号和估计误差。
- 是否存在邻小区或多用户干扰。

只改变 UCI 载荷长度而不记录功率和可用 RE，无法解释 BLER 变化。

对单个等效符号 $y=h x+n$，若接收机使用已知 $h$ 生成 LLR，则 LLR 幅度通常与 $|h|^2P_{\mathrm{tx}}/N_0$ 同向变化。上行功率控制改变的不是 LDPC 校验图，而是软解调输入的可靠性：

$$
L_{\mathrm{UL}}(i)
\propto\frac{|h_i|^2P_{\mathrm{tx}}}{N_0}
	imes\text{符号观测}
$$

该式是标量模型下的直观关系，实际 MIMO、干扰和均衡器输出还需要使用等效信道与等效噪声方差。

## UCI 复用的边界

与 UL-SCH 同时发送时，UCI 可能包括 HARQ-ACK、CSI 或其他控制信息。实现中至少要记录：

- UL-SCH 有效比特数和编码后长度。
- UCI 各字段的类型、长度和优先级。
- PUSCH 可用资源和每类信息分配到的比特数。
- 软解调后分离 UCI/UL-SCH 的索引。
- UL-SCH 与 UCI 各自的 CRC 或译码判决。

不要仅观察 UL-SCH 的 BLER 来判断整个 PUSCH 链路是否正确；UCI 错误可能影响 HARQ 状态和后续业务行为。

## 接口参数表

| 接口 | 关键参数 |
|---|---|
| MAC 到 UL-SCH 编码器 | $A$、TB-CRC、HARQ 进程和新数据指示 |
| 分段到 LDPC | $C$、$K'$、CB-CRC、BG 和 $Z$ |
| LDPC 到率匹配 | 母码字长度、RV、$E_r$ |
| UL-SCH 到 PUSCH | 调制阶数、目标资源、与 UCI 的复用参数 |
| PUSCH 到译码器 | 信道估计、均衡、LLR 符号和噪声标定 |
| 译码到 HARQ | TB-CRC、译码状态、软缓冲区和反馈结果 |

## 常见误区

1. UL-SCH 与 PUSCH 分别是传输信道和物理信道，不能混称。
2. UCI 不是简单附加在 UL-SCH CRC 后面的数据字段。
3. HARQ 软合并必须按母码字索引进行，不能直接按本次发送顺序拼接 LLR。
4. 仅做 UL-SCH 的无噪声闭环，不能验证 PUSCH 上的 UCI 复用。
5. 上行和下行的 LDPC 结构相似，不代表所有资源、扰码和反馈流程相同。
6. UCI/UL-SCH 复用索引错误通常会同时损害两类信息，但不应先假设 LDPC 算法有问题。
7. 上行 HARQ 合并必须同时记录 RV、功率、信道实现和 LLR 标定，不能只记录重传次数。

## 最小验证

1. 先构建不含 UCI 的 UL-SCH LDPC 无噪声闭环。
2. 记录 $A$、$C$、$Z$、RV、$E_r$ 和译码输出长度。
3. 在固定 RV 下验证单次传输的 TB-CRC 和 BER/BLER。
4. 使用两个不同 RV 生成受损传输，按母码字索引合并 LLR 并对比单次传输。
5. 再加入 UCI，独立检查 UCI 和 UL-SCH 的分离、译码和反馈结果。
6. 构造资源不足场景，确认 UCI 优先级、字段保留和状态记录符合预设规则。
7. 使用错误的复用索引或错误的功率标定，确认测试能区分 `mux_index_error` 与普通信道失败。

## 关联笔记

- 上位概念：[[信道编码基础]]、[[5G 信道编译码]]。
- 对比链路：[[NR-DL-SCH 编码链]]。
- 结构：[[LDPC-基图选择]]、[[LDPC-码块分段]]、[[LDPC-CB-CRC]]、[[LDPC-提升因子 Z]]。
- 处理：[[LDPC-率匹配]]、[[LDPC-置信传播译码]]。
- 软信息和指标：[[软判决与 LLR]]、[[BLER 与 BER]]。
