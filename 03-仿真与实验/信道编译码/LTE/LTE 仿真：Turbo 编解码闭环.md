---
title: LTE 仿真：Turbo 编解码闭环
aliases:
  - LTE Turbo BLER 实验
type: experiment
status: NEEDS_VERIFICATION
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - stage/仿真
  - topic/channel-coding
  - code/turbo
  - status/待验证
source:
  - "[[LTE-Turbo 编码与译码]]"
  - "[[LTE-CRC 与码块分段]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
related:
  - "[[LTE 仿真：CRS-DMRS 信道估计与均衡]]"
---

# LTE 仿真：Turbo 编解码闭环

> [!warning] 状态
> 这是可执行实验设计，当前没有已记录的运行结果。任何 BLER、迭代增益或 HARQ 结论都必须在结果表和元数据写回后才可使用。

## 目标

逐层验证 LTE DL-SCH/UL-SCH Turbo 链：

```text
payload → CRC24A → 分段/CB-CRC/filler → Turbo/QPP
→ 速率匹配/RV → BPSK/QPSK AWGN 或 LTE 物理层
→ LLR → 逆率匹配/HARQ → Turbo 迭代 → CB/TB CRC
```

## 固定参数

| 类别 | 必填字段 |
|---|---|
| 标准 | TS 36.212 版本、承载（DL-SCH/UL-SCH/BCH/DCI） |
| 长度 | `A/B/C/K_r/D_r/E_r/G`、filler、CRC 类型 |
| 交织 | QPP `K/f1/f2` 表版本、子块交织方向 |
| 速率匹配 | `rv_idx`、`N_cb`、`k_0`、逆映射规则 |
| 译码 | Log-MAP/Max-Log-MAP、最大迭代、停止规则、量化 |
| 信道 | AWGN 或 LTE 波形、SNR/EbN0 定义 |
| 统计 | seed、帧数、错误数、停止条件、软件版本 |

## 分层用例

1. 非零 payload、无噪声、`E=K_w`，验证编码/逆率匹配。
2. `E<K_w`，验证打孔/选择和母码 LLR 位置。
3. `E>K_w`，验证重复位置 LLR 累加。
4. `B=6144` 与 `B=6145`，验证单/多码块和 CB-CRC。
5. `B<40`，验证 filler/NULL。
6. `rv_idx=0,1,2,3` 与两次 HARQ，验证统一软缓冲区。
7. 扫描 Turbo 最大迭代次数，分别报告 CB-BLER、TB-BLER 和实际迭代次数。
8. 将物理层实验产生的 LLR 接入，定位均衡/解调/译码边界故障。

## 结果表模板

| 承载 | A | C | K_r | E_r | RV | SNR | 译码器/迭代 | CB-BLER | TB-BLER | 帧/错误数 | 首次失败状态 |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| 待运行 | - | - | - | - | - | - | - | - | - | - | `NEEDS_VERIFICATION` |

## 通过条件

- [ ] 编码长度和每一路 `D_r=K_r+4` 闭合。
- [ ] QPP 和子块交织互为可逆映射。
- [ ] 逆率匹配对重复位置累加 LLR。
- [ ] CB-CRC、TB-CRC、译码失败和资源/LLR 无效分开统计。
- [ ] 迭代曲线有明确帧数、错误数和停止规则。

## 证据边界

- `EXPERIMENT + NEEDS_VERIFICATION`：本页结果和性能判断。
- `STANDARD`：36.212 的分支、CRC、分段和速率匹配规则。
- `PERSONAL_NOTE`：分层测试策略、LLR 接口和故障分类。
