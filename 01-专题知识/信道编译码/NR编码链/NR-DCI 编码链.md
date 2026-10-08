---
title: NR-DCI 编码链
aliases:
  - 5G NR DCI 编码链
  - DCI Polar 编码流程
type: atomic
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - channel/dci
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

# NR-DCI 编码链

> [!abstract] 一句话结论
> DCI 是下行控制信息，通常在 PDCCH 上承载，采用 CRC、Polar 编码、率匹配、扰码和控制资源映射形成控制信道；接收端需要在候选 PDCCH 位置盲检测，并用 CRC 掩码和译码结果确定 DCI 是否有效。

## DCI、PDCCH 与控制资源

| 名称 | 层次 | 作用 |
|---|---|---|
| DCI | 控制信息 | 告知调度、HARQ、资源和其他物理层控制参数 |
| PDCCH | 物理信道 | 承载 DCI 的下行控制信道 |
| CCE/REG | 物理资源结构 | 提供 PDCCH 的控制资源映射单位 |

DCI 的具体字段由格式和上下行过程决定。编码链只负责把给定 DCI 比特可靠地映射为控制信道比特；搜索空间、聚合等级、RNTI 和候选位置还需要结合 TS 38.213、38.211 阅读。

## 候选级长度和资源账本

对搜索空间中的候选 $h$，应把逻辑字段、Polar 参数和物理资源分开记录：

$$
A_{DCI,h}
\xrightarrow{+L_{CRC}}
K_h
\xrightarrow{\mathrm{Polar\ construction}}
N_h
\xrightarrow{\mathrm{rate\ matching}}
E_h
\xrightarrow{\mathrm{PDCCH\ mapping}}
\mathbf{y}_h
$$

同一 DCI 格式下，$A_{DCI,h}$ 可能相同，但候选的资源位置和聚合等级不同；若聚合等级改变，$E_h$ 和物理资源映射也可能随之改变。候选级日志应至少包含格式、聚合等级、搜索空间索引、RNTI 假设、$K_h$、$N_h$ 和 $E_h$。

## 发送端流程

```text
DCI 有效载荷
	↓
按照 DCI 格式确定字段和长度
	↓
附加 CRC
	↓
用 RNTI 对 CRC 执行相关掩码
	↓
Polar 输入比特交织
	↓
信息位与冻结位分配
	↓
Polar 变换
	↓
率匹配到 PDCCH 目标长度 E
	↓
加扰、调制与 PDCCH 资源映射
```

RNTI 相关的 CRC 掩码用于把控制信息与特定终端或控制用途关联起来。接收端必须使用相同的 RNTI 假设进行 CRC 恢复检查。

## 接收端流程

```text
PDCCH 候选资源解映射
	↓
信道估计、均衡和软解调
	↓
解扰与候选级 LLR 整理
	↓
Polar 逆率匹配
	↓
SC/SCL Polar 译码
	↓
恢复 CRC 并尝试 RNTI 掩码
	↓
CRC 通过：接受 DCI
	↓
CRC 失败：丢弃候选并继续盲检测
```

接收端通常不知道哪个候选承载目标 DCI，需要在搜索空间中的多个候选上重复执行解映射和译码。候选越多，计算量越大，也越需要可靠的 CRC 判决避免误检。

若搜索空间包含 $M$ 个候选，单个错误候选通过长度为 $m$ 的 CRC 的概率近似为 $2^{-m}$，则在独立近似下至少一个错误候选通过的概率为：

$$
P_{\mathrm{FA}}
\approx1-(1-2^{-m})^{M}
$$

当 $M2^{-m}$ 很小时，进一步有 $P_{\mathrm{FA}}\approx M2^{-m}$。该式只用于数量级分析；实际候选受字段合法性、RNTI 约束和译码相关性影响。

## Polar 参数与率匹配

DCI 的有效载荷长度、CRC 后长度、Polar 母码长度 $N$ 和目标编码长度 $E$ 由标准规则确定。率匹配后的 $E$ 还受到 PDCCH 聚合等级和资源配置影响。

抽象链路为：

$$
K=A+L_{CRC}
\longrightarrow
N=2^n
\longrightarrow
E
$$

这里的 $K$、$N$、$E$ 不是任意调参值。实现必须按照适用 DCI 格式、资源配置和 TS 38.212 的 Polar 规则计算。

## 候选级长度账本

DCI 译码不是只对一个固定码字运行，而是对搜索空间中的每个候选分别维护参数：

| 候选阶段 | 记录内容 |
|---|---|
| DCI 解析 | 格式、有效载荷长度、字段顺序 |
| CRC 处理 | CRC 长度、RNTI 掩码和位序 |
| Polar 构造 | $K$、母码长度 $N$、信息集合和冻结集合 |
| 率匹配 | 聚合等级、目标长度 $E$、候选资源索引 |
| 译码判决 | 路径度量、CRC 状态、字段合法性 |

同一搜索空间内的候选可能具有不同的资源位置，但不能因此随意改变编码参数。候选级日志可以定位资源解映射错误和 Polar 参数错误这两类不同问题。

## CRC 掩码和盲检测

设译码得到的 CRC 结果为 $q$，RNTI 掩码为 $r$。接收端需要按标准约定执行逆掩码并检查：

$$
q\oplus r=\text{期望的 CRC 结果}
$$

具体比特顺序、掩码长度和 RNTI 类型必须按标准实现。盲检测中的一个候选 CRC 通过，不等于该候选绝对正确；错误通过概率、搜索空间约束和字段合法性也会影响误检风险。

CRC 掩码可以写成候选相关的判决函数：

$$
q_h
=\mathbf{1}\left[
\operatorname{CRC}(\hat{\mathbf{a}}_h)
\oplus\operatorname{mask}(RNTI_h)=\mathbf{0}
\right]
$$

这里 $q_h$ 只是候选接受证据。最终是否接受 DCI，还应结合候选资源、格式字段合法性和同一时隙内的协议约束。

在理想的随机独立近似下，长度为 $m$ 的 CRC 对随机错误候选的通过概率量级约为 $2^{-m}$，但实际误检率还受到候选数量、字段约束、相关错误和 RNTI 假设影响。因此应同时报告单候选和整组搜索空间的误检统计。

## 与 PDSCH/PUSCH 的关系

DCI 通常为后续数据传输提供调度信息，例如资源分配、MCS、HARQ 进程和新数据指示。它自身的 Polar 译码成功不等于后续 PDSCH 或 PUSCH 一定成功；控制和数据信道应分别统计 BLER 与失败原因。

## 实现检查表

- DCI 格式和有效载荷字段顺序是否正确？
- CRC 附加前后的长度是否明确？
- RNTI 掩码是在 CRC 的正确位置和顺序上执行的吗？
- 搜索空间候选和聚合等级是否与 PDCCH 资源一致？
- 每个候选的 LLR 是否正确分离、解扰和逆率匹配？
- CRC 失败候选是否被丢弃，是否记录候选索引和失败原因？

盲检测的总计算量可以粗略表示为：

$$
W_{\mathrm{blind}}
\asymp\sum_{h=1}^{M}W_{\mathrm{Polar}}(N_h,L_h)
$$

其中 $W_{\mathrm{Polar}}$ 还包含候选资源解映射、LLR 整理、逆率匹配和 CRC 判决。优化候选搜索时不能只减少 Polar 树计算而忽略物理候选解映射和失败候选的尾延迟。

## 常见误区

1. DCI 是控制信息，PDCCH 是物理承载，二者不能互换。
2. RNTI CRC 掩码不是普通的信道扰码，处理位置和用途不同。
3. DCI 译码器不能只输入固定长度的“裸 DCI”而忽略 Polar 率匹配。
4. 只测试正确候选不能证明盲检测实现正确，必须加入错误候选和搜索空间测试。
5. CRC 通过不应脱离 DCI 格式、RNTI 和搜索空间约束单独解释。

## 最小验证

1. 固定 DCI 格式、字段、RNTI、搜索空间和聚合等级。
2. 记录 CRC 后长度、Polar $N$、目标 $E$ 和候选资源位置。
3. 在无噪声条件下验证正确候选能恢复 DCI，错误 RNTI 不能通过 CRC。
4. 在候选集中加入多个错误候选，统计误检和漏检。
5. 在 AWGN 下分别记录候选级译码失败、CRC 失败、DCI BLER 和盲检测复杂度。
6. 构造一个候选资源正确但 RNTI 错误、一个 RNTI 正确但资源错误的测试，确认失败原因可区分。
7. 统计每个时隙的候选数、Polar 译码次数、CRC 通过数和最终接受数，评估盲检测尾延迟。

## 关联笔记

- Polar 原理：[[Polar-信道极化]]、[[Polar-可靠性序列]]、[[Polar-冻结位]]。
- 译码：[[Polar-SC 译码]]、[[Polar-SCL 译码]]、[[Polar-CRC 辅助 SCL 译码]]。
- 率匹配：[[Polar-率匹配]]。
- 软信息和 CRC：[[软判决与 LLR]]、[[CRC 校验]]。
- 物理控制：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.213｜Physical layer procedures for control]]。
