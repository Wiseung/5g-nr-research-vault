---
title: 仿真-LDPC-AWGN-BLER
aliases:
  - LDPC AWGN BLER 仿真
  - LDPC 链路性能基线
  - LDPC BLER Curve
type: experiment
status: seed
tags:
  - domain/5g-nr
  - code/ldpc
  - stage/simulation
  - metric/bler
  - metric/ber
  - metric/latency
  - stage/performance-analysis
source:
  - LDPC 编码理论
  - 3GPP TS 38.212
  - AWGN 通信系统仿真
simulation:
  - 仿真-LDPC-AWGN-BLER
---

# 仿真-LDPC-AWGN-BLER

> [!abstract] 一句话结论
> LDPC-AWGN-BLER 仿真用于建立固定码率、块长、调制和译码配置下的错误率基线；它应同时报告 CB-BLER、TB-BLER、BER、译码迭代和统计置信度，不能只画一条平滑曲线。

## 实验目标

在理想同步、理想信道估计和 AWGN 条件下，测量 NR LDPC 链路的单次传输性能。实验用于回答：

- 不同 SNR 下 LDPC 译码是否产生合理瀑布区。
- 率匹配比例、码率和块长如何影响 BLER。
- BP、Min-Sum、NMS/OMS 和 layered/flooding 的差异。
- 最大迭代次数、早停和 LLR 标定对性能与延迟的影响。
- 结果是否与未编码 BPSK/QPSK 基线方向一致。

## 固定与变化参数

### 建议固定

- 基图 BG、提升因子 $Z$ 和码块分段规则。
- 信息长度、CRC 类型、码块数和目标 $E$。
- 调制、层数、资源归一化和噪声定义。
- LLR 符号、缩放、量化和饱和范围。
- 译码算法、最大迭代次数、早停规则。
- 随机种子策略、每个 SNR 的停止规则。

### 一次只改变

- $E_b/N_0$、$E_s/N_0$ 或接收 SNR。
- 或率匹配目标长度 $E$。
- 或译码算法/最大迭代次数，但不能同时改变码率和译码器并归因于一个因素。

## AWGN 定义

以 BPSK 为基线：

$$
 b=0\mapsto +\sqrt{E_b},\qquad
 b=1\mapsto -\sqrt{E_b}
$$

$$
 y=x+n,\qquad n\sim\mathcal{N}(0,\sigma^2)
$$

若使用实 AWGN 每维方差 $N_0/2$：

$$
\sigma^2=\frac{N_0}{2},\qquad
\sigma^2=\frac{E_b}{2\cdot10^{E_b/N_0/10}}
$$

实际代码需要明确横轴是信息比特能量、编码比特能量、调制符号能量还是接收信号功率。包含 CRC 的 $K$ 与有效载荷长度会改变 $E_b/N_0$ 换算。

## 仿真流程

```text
生成信息比特
    ↓
TB-CRC、码块分段和 LDPC 编码
    ↓
率匹配、码块级联和扰码
    ↓
调制
    ↓
加入 AWGN
    ↓
软解调得到 LLR
    ↓
解扰、逆率匹配和 LLR 合并
    ↓
LDPC 译码与 CB/TB-CRC
    ↓
统计 BER、BLER 和迭代负载
```

初始基线可以跳过物理波形，直接对编码比特使用 BPSK AWGN；通过后再加入 38.211 资源网格和 OFDM，以区分译码器误差与物理层误差。

## 指标

| 指标 | 定义 |
|---|---|
| CB-BLER | 码块 CRC 或参考码字失败率 |
| TB-BLER | 传输块 CRC 失败率 |
| 信息 BER | 译码后有效载荷错误比特率 |
| 编码比特 BER | 率匹配/解调接口比特错误率 |
| 平均迭代数 | 每码块或每 TB 的平均实际迭代 |
| P95/P99 迭代数 | 译码尾部工作量 |
| 早停比例 | 提前满足停止条件的块比例 |
| 吞吐量 | 每时间单位成功的信息比特数 |

TB-BLER 不能由 CB-BLER 的独立假设替代，应直接统计。

## 统计停止规则

每个 SNR 点至少记录：

- `min_blocks`：最少码块或传输块数。
- `min_errors`：希望观测到的失败数。
- `max_blocks`：最大仿真预算。
- `stop_reason`：达到错误数、样本数或置信要求。
- 随机种子和独立信道/噪声实现数。

失败数为 0 时，记录样本数和置信上界；不能把观测值直接写成真实 BLER 为 0。零失败的数量级上界可用 $3/n$ 作初步参考，但正式结果应说明置信水平和区间方法。

## 对照实验

| 对照 | 固定内容 | 变化内容 | 目的 |
|---|---|---|---|
| 未编码基线 | 调制、SNR 定义 | 是否编码 | 检查总体方向 |
| 不同码率 | 调制、块长、译码器 | $E$ 或有效码率 | 比较冗余代价 |
| 不同译码器 | 码图、LLR、停止规则 | BP/MS/NMS/OMS | 比较实现损失 |
| 不同 CSI | 编码和资源 | 理想/估计 CSI | 分离接收机损失 |
| 不同 HARQ | 单次配置 | RV 和软合并 | 比较重传收益 |

## 结果表

| $E_b/N_0$ | 总 TB | TB 失败 | TB-BLER | CB-BLER | 信息 BER | 平均迭代 | P99 迭代 | 早停率 | 吞吐量 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  |  |  |  |  |  |

## 故障定位

- 全部 SNR 都接近 0.5 BLER 或 1：优先检查 LLR 符号、调制映射和解扰。
- 无噪声都失败：转到 [[仿真-无噪声编解码闭环]]，检查率匹配和码图。
- 高 SNR 仍有明显错误：检查 CRC、filler、基图、提升因子和索引。
- 只改变译码器但曲线完全相同：检查译码器是否真正接收了软 LLR。
- 平均迭代很低但 BLER 异常好：检查 syndrome/CRC 早停是否过早接受错误码字。
- BLER 曲线不单调：检查 SNR/噪声换算、随机种子、LLR 缩放和统计停止规则。

## 最小实验

1. BPSK-AWGN 未编码基线。
2. 一个单码块 LDPC 配置的 $E_b/N_0$ 扫描。
3. CB-BLER、TB-BLER 和信息 BER 同时统计。
4. 固定 SNR 比较 BP、Min-Sum 和 NMS/OMS。
5. 记录每个点样本数、失败数、平均迭代和置信上界。
6. 加入一个 RV 重传对照，分开报告初传和 HARQ 后失败率。

## 关联笔记

- 链路：[[NR-DL-SCH 编码链]]、[[NR-UL-SCH 编码链]]。
- LDPC：[[LDPC-率匹配]]、[[LDPC-置信传播译码]]、[[LDPC-Min-Sum 译码]]。
- 指标：[[BLER 与 BER]]、[[编码增益]]、[[软判决与 LLR]]。
- 标准：[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.211｜Physical channels and modulation]]。
- 相关实验：[[仿真-不同译码迭代次数]]、[[仿真-不同码率比较]]。
