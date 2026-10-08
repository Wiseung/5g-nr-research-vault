---
title: 仿真-Polar-AWGN-BLER
aliases:
  - Polar AWGN BLER 仿真
  - Polar 控制信道性能基线
  - Polar BLER Curve
type: experiment
status: seed
tags:
  - domain/5g-nr
  - code/polar
  - stage/simulation
  - metric/bler
  - metric/ber
  - metric/latency
  - stage/performance-analysis
source:
  - Polar Codes 编码理论
  - 3GPP TS 38.212
  - AWGN 通信系统仿真
simulation:
  - 仿真-Polar-AWGN-BLER
---

# 仿真-Polar-AWGN-BLER

> [!abstract] 一句话结论
> Polar-AWGN-BLER 仿真用于固定母码长度、信息长度、CRC、率匹配和译码列表大小下评估 SC/SCL/CRC-Aided SCL 的有限块长性能；必须把译码性能和候选路径、CRC 状态、LLR 质量及统计置信度一起记录。

## 实验目标

- 建立 Polar 控制链的 AWGN BLER 基线。
- 比较 SC、普通 SCL 和 CRC-Aided SCL。
- 观察列表大小 $L$、CRC 长度、母码率和率匹配比例的影响。
- 区分正确路径被剪枝、CRC 失败和错误路径误通过。
- 验证 Polar 率匹配输出长度 $E$ 改变时，译码树仍使用母码长度 $N$。

## 参数账本

| 类别 | 参数 |
|---|---|
| 输入 | 有效载荷 $A$、CRC 长度、信息集合输入顺序 |
| Polar | $N=2^n$、$K$、可靠性序列、冻结集合 |
| 率匹配 | $E$、打孔/缩短/重复、交织索引 |
| 译码 | SC/SCL/CA-SCL、列表大小 $L$、路径度量 |
| 信道 | BPSK/QPSK、$E_b/N_0$ 定义、AWGN 方差 |
| 统计 | 每点块数、错误数、随机种子、停止规则 |

母码率、有效载荷码率和物理发送码率要分别记录：

$$
R_{mother}=\frac{K}{N},\qquad
R_{payload}=\frac{A}{E},\qquad
R_{coded}=\frac{K}{E}
$$

具体口径应标注是否包含 CRC。

## 仿真流程

```text
生成有效载荷
    ↓
附加 CRC
    ↓
按照可靠性序列选择信息集合
    ↓
填充冻结位并执行 Polar 变换
    ↓
子块交织和率匹配到 E
    ↓
调制并加入 AWGN
    ↓
软解调、解扰和逆率匹配到 N 个 LLR
    ↓
SC/SCL/CRC-Aided SCL 译码
    ↓
提取有效载荷并检查 CRC
```

先采用直接 BPSK LLR 输入验证 Polar 树，再加入 38.211 调制和资源网格。这样可将可靠性集合、冻结位和率匹配问题与物理层问题分离。

## 关键指标

| 指标 | 说明 |
|---|---|
| Polar-BLER | 有效载荷错误或 CRC 失败的块比例 |
| 信息 BER | 译码后有效载荷错误比特比例 |
| CRC 失败率 | 最终没有候选通过 CRC 的比例 |
| 平均活动路径数 | SCL 实际路径负载 |
| 正确路径剪枝率 | 仿真可知的内部诊断指标 |
| 平均/ P99 延迟 | 路径搜索和率匹配总负载 |
| 误检率 | 错误候选通过 CRC 的比例，若有候选集 |

CRC 通过不是正确性的充分证明；错误候选可能以很低概率通过 CRC。仿真中如果保存发送信息，可以直接统计未检出错误。

## 列表大小对照

固定 $N$、$K$、CRC、可靠性序列、$E$、信道和随机输入，只改变：

$$
L\in\{1,2,4,8,16,32\}
$$

$L=1$ 作为 SC 近似基线。每个 $L$ 都要记录配置上限和实际峰值路径数，不能只记录 `L`。

| $L$ | BLER | BER | CRC 通过率 | 平均路径数 | 正确路径剪枝率 | 平均延迟 | P99 延迟 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |
| 8 |  |  |  |  |  |  |  |
| 16 |  |  |  |  |  |  |  |

## AWGN 与统计规则

固定每个 SNR 点的样本规则：

- `min_blocks`：至少完成的 Polar 块数。
- `min_errors`：至少观测的错误块数。
- `max_blocks`：最大仿真预算。
- `stop_reason`：停止原因。
- 置信区间方法和随机种子。

低 BLER 区域不能只用平滑曲线判断性能。若错误数为 0，应报告块数和统计上界，而不是写成真实 BLER 为 0。

## 故障定位矩阵

| 现象 | 优先检查 |
|---|---|
| 所有 $L$ 都失败 | LLR 符号、冻结位、可靠性序列、率匹配 |
| 增大 $L$ 完全无收益 | 正确路径是否被接口错误提前破坏、CRC 位序 |
| SCL 比 SC 更差 | 路径度量方向、候选复制和剪枝排序 |
| CRC 全部失败 | CRC 覆盖范围、信息位装载顺序、提取顺序 |
| $E>N$ 性能异常 | 重复位置 LLR 是否累加 |
| $E<N$ 性能异常 | 打孔/缩短初始化和逆交织 |
| 高 SNR 仍有错误 | Polar 变换排列、冻结集合、LLR 符号 |

先运行 [[仿真-无噪声编解码闭环]]，再解释 AWGN 曲线。

## 最小实验

1. 小型 $N=2^n$ 无噪声矩阵/递归闭环。
2. 固定 $L=1$ 的 SC-AWGN 基线。
3. 固定 CRC 的 SCL 列表大小扫描。
4. 分别测试 $E<N$、$E=N$、$E>N$。
5. 同时统计 BLER、BER、CRC 状态和路径负载。
6. 与未编码 BPSK 基线和 LDPC-AWGN 结果分开比较。

## 关联笔记

- 链路：[[NR-BCH 编码链]]、[[NR-DCI 编码链]]、[[NR-UCI 编码链]]。
- Polar：[[Polar-信道极化]]、[[Polar-可靠性序列]]、[[Polar-冻结位]]、[[Polar-SC 译码]]、[[Polar-SCL 译码]]。
- 率匹配：[[Polar-率匹配]]。
- 指标：[[BLER 与 BER]]、[[编码增益]]、[[软判决与 LLR]]。
- 相关实验：[[仿真-不同列表大小]]、[[仿真-率匹配正确性验证]]、[[仿真-LLR 符号验证]]。
