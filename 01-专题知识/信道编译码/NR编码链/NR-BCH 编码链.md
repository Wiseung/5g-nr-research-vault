---
title: NR-BCH 编码链
aliases:
  - 5G NR BCH 编码链
  - PBCH Polar 编码流程
type: atomic
status: seed
tags:
  - domain/5g-nr
  - layer/physical-layer
  - channel/bch
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

# NR-BCH 编码链

> [!abstract] 一句话结论
> NR-BCH 承载广播相关信息，经过 CRC、Polar 编码、率匹配和物理映射后形成 PBCH 传输；PBCH 的极化码参数、盲检测相关比特和物理映射必须与系统帧号、同步信号块和标准版本一致。

## BCH、PBCH 与 MIB

BCH 是广播传输信道，PBCH 是承载 BCH 的物理信道，MIB 是其主要承载的系统信息内容。三者处于不同抽象层：

| 名称 | 层次 | 作用 |
|---|---|---|
| BCH | 传输信道 | 承载广播信息 |
| PBCH | 物理信道 | 在同步信号块中传输 BCH |
| MIB | 信息内容 | 提供终端初始接入所需的基础系统参数 |

不要把 MIB 比特直接当作最终 PBCH 调制输入。中间还包括 CRC、Polar 编码、率匹配、扰码和物理资源映射。

## 四层长度与候选账本

PBCH 调试时建议把以下四层长度分开：

$$
A_{MIB}
\longrightarrow
K_{BCH}=A_{BCH}+L_{CRC}
\longrightarrow
N_{PBCH}
\longrightarrow
E_{PBCH}
$$

其中 $A_{MIB}$ 是 MIB 字段长度，$A_{BCH}$ 是按标准加入相关广播比特后的 BCH 输入长度，$K_{BCH}$ 是放入 Polar 信息集合的长度，$N_{PBCH}$ 是母码长度，$E_{PBCH}$ 是物理发送长度。具体值和字段组成必须以适用版本 TS 38.212 为准；这个公式用于防止把 MIB 长度直接当成 Polar $K$ 或 PBCH 的发送长度。

每个物理候选还应绑定：

| 候选参数 | 对 Polar 链的影响 |
|---|---|
| 系统帧号/半帧相关比特 | 影响 BCH 输入或物理组合假设 |
| SS/PBCH block 候选 | 影响物理映射和解扰假设 |
| $K_{BCH},N_{PBCH},E_{PBCH}$ | 决定信息集合、译码树和率匹配 |
| CRC 结果 | 筛选候选并判断是否可交付 |

## 发送端抽象流程

```text
MIB 与相关广播比特
    ↓
构造 BCH 传输块
    ↓
附加 BCH CRC
    ↓
输入比特交织与 Polar 信息位安排
    ↓
Polar 变换
    ↓
率匹配到 PBCH 目标长度
    ↓
与物理层相关参数进行扰码或比特处理
    ↓
调制
    ↓
PBCH 映射到 SS/PBCH block
```

具体输入长度、CRC 长度、Polar 码长度和率匹配长度由 TS 38.212 的 BCH 条款规定。PBCH 的部分比特还与系统帧号、半帧指示或同步信号块相关参数组合，不能只用一组固定随机输入替代完整链路。

## 长度与假设账本

实现时应把 BCH 链路拆成两个相互关联但不能混用的账本：

| 阶段 | 需要记录的对象 | 主要风险 |
|---|---|---|
| BCH 载荷 | MIB 字段、附加广播比特、字段顺序 | 把 MIB 长度误当成最终 Polar 信息长度 |
| CRC 后 | 有效载荷与 CRC 的总长度 $K$ | CRC 位序或覆盖范围错误 |
| Polar 母码 | $K$、$N$、信息集合和冻结集合 | 使用了 DCI/UCI 的参数或索引 |
| 率匹配后 | 目标长度 $E$ 和逆映射规则 | 把 $E$ 当作译码树长度 |
| PBCH 映射 | 物理扰码、候选参数和资源位置 | 编码参数与物理层假设混在一起 |

其中 $K$、$N$、$E$ 的具体值以适用版本 TS 38.212 和 PBCH 配置为准；测试日志应同时保存系统帧号、半帧、同步信号块候选和解扰假设。

## 接收端抽象流程

```text
PBCH 资源解映射
    ↓
信道估计、均衡和软解调
    ↓
物理层相关解扰与参数假设
    ↓
Polar 逆率匹配
    ↓
SC/SCL 或标准规定的 Polar 译码
    ↓
BCH CRC 检查
    ↓
恢复 MIB 与系统参数
```

PBCH 接收端通常需要在部分未知物理参数下尝试候选假设。CRC 不仅检查 Polar 译码结果，也帮助接收端筛选正确的候选配置。

可以把接收端写成候选状态机：

```text
生成一个 PBCH 参数候选
    ↓
解扰并执行逆率匹配
    ↓
Polar 译码
    ↓
BCH CRC 失败：丢弃候选
    ↓
BCH CRC 通过：检查字段与物理假设
    ↓
接受唯一合法候选或继续消除歧义
```

“译码成功”“CRC 通过”和“恢复出可用 MIB”应作为不同状态记录。这样可以区分 Polar 算法错误、CRC 误检和物理参数候选错误。

若候选集合为 $\mathcal{H}$，对每个候选 $h$ 得到 CRC 判决 $q_h$，则最终接受条件可以抽象为：

$$
\mathcal{H}_{\mathrm{pass}}
=\{h\in\mathcal{H}:q_h=1\text{ 且字段与物理约束一致}\}
$$

只有在 $|\mathcal{H}_{\mathrm{pass}}|=1$ 或标准规定的消歧条件成立时，才能输出 MIB。单个 Polar 路径完成并不等于物理候选已经唯一确定。

## 与普通 Polar 教学链的区别

教学链可以抽象为：

```text
K 个信息比特 + CRC
    ↓
Polar 编码
    ↓
率匹配到 E
```

PBCH 还要考虑：

- 固定广播载荷和标准规定的 CRC。
- 物理层相关比特的组合、扰码和交织。
- SS/PBCH block 的资源位置。
- 系统帧号、半帧和同步信号块候选。
- 接收端的盲假设与 CRC 筛选。

## 关键接口

| 接口 | 必须保持一致的内容 |
|---|---|
| MIB 到 BCH | 载荷字段顺序和系统参数编码 |
| BCH 到 Polar | CRC 后长度、信息位位置和冻结位位置 |
| Polar 到率匹配 | $N$、$K$、目标 $E$ 和索引 |
| 率匹配到 PBCH | 输出长度、比特顺序和物理扰码 |
| 接收端译码 | LLR 符号、候选假设和 CRC 判决 |

## 常见误区

1. BCH、PBCH 和 MIB 不是同一个对象。
2. PBCH 的 Polar 参数不能直接照搬 DCI 或 UCI。
3. CRC 通过不代表所有物理参数假设都唯一正确，需结合候选和协议规则判断。
4. 只验证固定已知参数下的无噪声译码，不能覆盖 PBCH 的盲检测流程。
5. 未区分物理层扰码和信道编码，会导致接收端逆处理顺序错误。

PBCH 中的物理候选处理可以理解为对同一软观测执行多个假设变换：

$$
\mathbf{L}_{h}
=\operatorname{descramble}_{h}
\left(\operatorname{demap}_{h}(\mathbf{y})\right)
$$

不同候选的 $\mathbf{L}_{h}$ 不能混合后再统一 Polar 译码；每个 $h$ 都应独立完成物理解扰、逆率匹配、Polar 译码和 CRC 判决。

## 最小验证

1. 固定 MIB、系统帧号、半帧和同步信号块参数。
2. 记录 BCH CRC、Polar $K/N$、率匹配目标长度和所有物理层假设。
3. 在无噪声条件下完成 PBCH 编解码，确认 MIB 字段逐比特恢复。
4. 故意改变一个候选物理参数，确认 CRC 或候选判决能够拒绝错误假设。
5. 在 AWGN 下统计 PBCH BLER，并区分译码失败和候选假设错误。
6. 分别破坏 CRC 位序、Polar 信息集合、率匹配索引和物理扰码，确认每类错误在对应接口被捕获。
7. 对多个同步信号块候选记录候选数量、CRC 通过数量和最终接受条件。

## 关联笔记

- Polar 原理：[[Polar-信道极化]]、[[Polar-可靠性序列]]、[[Polar-冻结位]]。
- 译码：[[Polar-SC 译码]]、[[Polar-SCL 译码]]、[[Polar-CRC 辅助 SCL 译码]]。
- 率匹配：[[Polar-率匹配]]。
- 标准链路：[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.211｜Physical channels and modulation]]。
