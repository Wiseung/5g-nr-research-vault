---
title: LDPC-Min-Sum 译码
aliases:
  - LDPC Min-Sum Decoding
  - LDPC 最小和译码
type: atomic
status: seed
tags:
  - domain/5g-nr
  - code/ldpc
  - process/decoding
  - algorithm/min-sum
  - theory/graph-code
  - metric/bler
source:
  - LDPC 编码理论
  - 迭代译码相关文献
  - 3GPP TS 38.212
simulation:
  - 仿真-LDPC-AWGN-BLER
  - 仿真-不同译码迭代次数
---

# LDPC-Min-Sum 译码

> [!abstract] 一句话结论
> Min-Sum 用输入消息绝对值的最小值近似 BP 的校验节点更新，避免昂贵的双曲函数计算，适合硬件和低延迟实现；未经修正的 Min-Sum 往往高估消息可靠性，通常需要归一化或偏移修正。

## 从 BP 到 Min-Sum

和积 BP 的校验节点更新是：

$$
L_{c\to v}
=2\operatorname{atanh}\left(
\prod_{v'\in\mathcal{N}(c)\setminus v}
\tanh\frac{L_{v'\to c}}{2}
\right)
$$

Min-Sum 用符号乘积和幅度最小值近似它：

$$
L_{c\to v}^{MS}
=\left(
\prod_{v'\in\mathcal{N}(c)\setminus v}
\operatorname{sign}(L_{v'\to c})
\right)
\min_{v'\in\mathcal{N}(c)\setminus v}
|L_{v'\to c}|
$$

变量节点更新仍然累加信道 LLR 和其他校验节点消息：

$$
L_{v\to c}
=L_v^{ch}+
\sum_{c'\in\mathcal{N}(v)\setminus c}
L_{c'\to v}
$$

后验 LLR 为：

$$
L_v^{post}=L_v^{ch}+
\sum_{c\in\mathcal{N}(v)}L_{c\to v}
$$

### Min-Sum 为什么会高估幅度

设校验节点输入的绝对值为 $a_1,\ldots,a_d$，并暂时忽略符号。对和积更新，令 $x_i=\tanh(a_i/2)$，由于 $0\le x_i\le1$，有：

$$
\prod_i x_i\le\min_i x_i
$$

而 $\operatorname{atanh}(\cdot)$ 在 $[0,1)$ 上单调递增，因此：

$$
2\operatorname{atanh}\left(\prod_i\tanh\frac{a_i}{2}\right)
\le\min_i a_i
$$

右侧正是未经修正的 Min-Sum 幅度。于是通常有：

$$
|L_{c\to v}^{SP}|
\le
|L_{c\to v}^{MS}|
$$

这说明 Min-Sum 的误差方向通常是过度自信，而不是简单的随机扰动；NMS 和 OMS 的目的就是补偿这部分系统性偏差。

对两个输入的 box-plus 运算，和积结果还可以写成：

$$
a\boxplus b
=\operatorname{sign}(a)\operatorname{sign}(b)
\left[
\min(|a|,|b|)-\Delta(a,b)
\right]
$$

其中 $\Delta(a,b)\ge0$ 是依赖两个幅度差异的校正项。Min-Sum 忽略或近似该校正项，因此在输入幅度接近时误差更明显。

## 为什么需要修正

Min-Sum 的最小值近似通常会让校验节点输出的幅度偏大，译码器会对消息过度自信。过大的置信度可能降低迭代译码在短环和低 SNR 条件下的纠错能力。

### Normalized Min-Sum

引入归一化系数 $\alpha$：

$$
L_{c\to v}^{NMS}
=\alpha\,L_{c\to v}^{MS},
\qquad 0<\alpha\le 1
$$

$\alpha$ 可以是固定参数，也可以按层、码率或量化配置设定。它通常需要通过仿真或硬件定点分析选择。

### Offset Min-Sum

从最小幅度中减去偏移量 $\beta$，再截断为非负：

$$
L_{c\to v}^{OMS}
=\operatorname{sign}(L_{c\to v}^{MS})
\max\left(\min|L|-\beta,0\right)
$$

归一化和偏移修正不能同时凭经验叠加；若组合使用，应明确公式和调参过程。

两种修正的作用可以分别理解为：

$$
	ext{NMS：缩放整体幅度},
\qquad
	ext{OMS：削减小幅度消息}
$$

当输入消息已经经过定点缩放或前级均衡，$\alpha$、$\beta$ 的最优值会随 LLR 尺度改变。调参时必须把 LLR 标度作为实验参数记录，否则不同实现之间的参数数值不可直接比较。

## 最小值与次小值算法

对一个校验节点 $c$，设除目标边 $v$ 外输入绝对值的最小值和次小值为 $m_1$、$m_2$，最小值所在边为 $v_{min}$。则：

$$
m_{c\setminus v}=\begin{cases}
m_2,&v=v_{min}\\
m_1,&v\ne v_{min}
\end{cases}
$$

输出符号为除目标边外所有输入符号的乘积。一次扫描即可得到 $m_1$、$m_2$、最小值索引和总符号，避免对每条输出边重复排序。

对度数为 $d_c$ 的校验节点，朴素实现每条边都重新求最小值，计算量可能达到 $\mathcal{O}(d_c^2)$；保存最小值和次小值后可降为近似 $\mathcal{O}(d_c)$。

设输入符号乘积为 $s_{all}=\prod_{u\in\mathcal{N}(c)}\operatorname{sign}(L_{u\to c})$，则目标边 $v$ 的输出符号可写成：

$$
s_{c\to v}=s_{all}\operatorname{sign}(L_{v\to c})
$$

在只使用符号比特 XOR 的实现中，可以用全局奇偶校验值减去目标边符号的方式完成排除自身；但零值符号必须单独定义，不能直接把 `sign(0)` 当作普通正负号参与 XOR。

## 最小值查找实现

对一个校验节点，需要找出输入消息绝对值中的最小值和次小值：

- 对输出到最小值所在边的消息使用次小值。
- 对其他边使用最小值。
- 输出符号为除目标边外所有输入符号的乘积。

这避免了对每条边重复排序。QC-LDPC 的层结构还可以把最小值、次小值和符号统计按向量方式处理。

对一次校验节点扫描，建议同时输出三个调试量：

| 量 | 作用 |
|---|---|
| 全部输入符号的奇偶结果 | 检查输出符号排除目标边是否正确 |
| 最小值和次小值及其索引 | 检查目标边是否选择正确幅度 |
| 修正后的输出幅度 | 检查 NMS/OMS 和截幅顺序 |

这三个量比只比较最终译码比特更容易定位 Min-Sum 的局部实现错误。

## 零值和符号约定

实现必须规定 `sign(0)` 和零消息的处理。一个常见做法是把零值视为幅度为零、符号不改变乘积，但具体实现应保持变量节点、校验节点和量化逻辑一致。

采用的 LLR 约定应与 [[软判决与 LLR]] 一致：如果正值表示比特 0 更可信，则后验 LLR 的判决符号也必须使用同一规则。

## 分层 Min-Sum

在 QC-LDPC 中，分层 Min-Sum 常按基图的校验层更新：

```text
读取当前层相关变量节点 LLR
    ↓
计算校验节点输入消息
    ↓
更新最小值、次小值和符号
    ↓
得到新的校验节点消息
    ↓
将消息增量立即写回变量节点
    ↓
处理下一层
```

分层调度需要保存旧的校验消息，以便计算变量节点更新的增量。若把 flooding 版本的消息更新直接套到 layered 数据结构，常见结果是重复累加或遗漏旧消息。

分层 Min-Sum 的核心更新可抽象为：

```text
读取层内旧校验消息
  ↓
从变量节点后验 LLR 中减去旧消息，得到外部输入
  ↓
计算符号、最小值和次小值
  ↓
应用 MS/NMS/OMS 修正
  ↓
写入新校验消息
  ↓
把新旧差值加入变量节点后验 LLR
```

“先减旧、后加新”是 layered 实现与 flooding 实现最容易混淆的地方。

## 性能与复杂度

相对于 Sum-Product，Min-Sum 通常具有：

- 更低的函数计算复杂度。
- 更适合定点量化和并行硬件。
- 通过归一化或偏移参数换取接近 BP 的性能。
- 对参数、码图、LLR 缩放和量化位宽更敏感。

比较算法时要固定最大迭代次数、早停规则和 LLR 定点格式。否则“Min-Sum 比 BP 差多少”的结论无法归因。

## 归一化和偏移参数的选择

$\alpha$ 或 $\beta$ 不是只由码率决定的通用常数，还可能依赖：

- 基图和提升因子。
- 校验节点度数分布。
- SNR 区间和目标 BLER。
- flooding/layered 调度。
- LLR 量化位宽和饱和范围。

建议在固定代码、固定信道和固定停止规则下扫描参数，并同时记录 BLER、平均迭代次数、LLR 饱和比例和吞吐量。只选取让单个 SNR 点最好看的参数，容易过拟合仿真条件。

## 定点实现

定点 Min-Sum 通常需要：

1. 对输入 LLR 和边消息统一缩放。
2. 对绝对值求最小值前处理最小可表示值。
3. 对符号和幅度分开存储或使用带符号格式。
4. 在变量节点累加处执行饱和，而不是溢出回绕。
5. 记录每轮或每层的饱和次数。

溢出回绕可能把大正 LLR 变成负值，造成比简单截幅更严重的译码错误。

## 常见误区

1. Min-Sum 不是把所有输入消息取平均，而是保留符号乘积和最小幅度。
2. 对目标边排除自身输入时，不能直接对所有邻居取同一个最小值。
3. 忽略次小值会使最小输入边的校验消息错误。
4. 未修正的 Min-Sum 幅度偏大，不能保证与 Sum-Product 相同。
5. 只比较 BLER 不记录译码延迟、平均迭代次数和量化位宽，会遗漏工程代价。
6. Min-Sum 的最小值必须排除目标边；否则校验消息会错误地使用自身输入。
7. NMS/OMS 参数变化和 LLR 缩放变化可能互相抵消，比较时要分别记录。

## 最小验证

1. 用一个校验节点的少量消息手工验证符号、最小值和次小值规则。
2. 对照 Sum-Product 计算校验节点输出，检查 Min-Sum 的近似方向。
3. 在相同 LLR、码图和停止规则下比较 MS、NMS、OMS 和 BP。
4. 扫描归一化系数或偏移量，记录 BLER、平均迭代次数和吞吐量。
5. 使用极大、极小和零 LLR 测试定点饱和与符号处理。
6. 对一个度数为 3 或 4 的校验节点手工验证最小值边使用次小值。
7. 扫描 $\alpha$ 或 $\beta$ 后在多个 SNR 点验证，而不是只在一个点选参。
8. 比较浮点和定点实现的 BLER、平均迭代次数、饱和比例和吞吐量。

## 关联笔记

- 上位算法：[[LDPC-置信传播译码]]。
- 结构：[[QC-LDPC 结构]]、[[LDPC-提升因子 Z]]。
- 软信息：[[软判决与 LLR]]。
- 参数：[[LDPC-译码迭代次数]]。
- 性能：[[BLER 与 BER]]、[[编码增益]]。
