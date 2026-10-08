---
title: LTE-UL-SCH 编码链
aliases:
  - LTE 上行共享信道编码链
  - LTE PUSCH Turbo 链
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - channel/ul-sch
  - code/turbo
  - process/encoding
  - process/decoding
  - evidence/3gpp
source:
  - "[[3GPP TS 36.212｜Multiplexing and channel coding]]"
  - "[[3GPP TS 36.211｜Physical channels and modulation]]"
simulation:
  - "[[LTE 仿真：Turbo 编解码闭环]]"
related:
  - "[[LTE-DL-SCH 编码链]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
  - "[[LTE OFDM 与 SC-FDMA 接收及频域均衡]]"
---

# LTE-UL-SCH 编码链

> [!abstract] 一句话结论
> LTE UL-SCH 的数据部分与 DL-SCH 共享 TB-CRC、码块分段、Turbo 和 Turbo 速率匹配主干，但 PUSCH 还可能携带独立编码的 CQI/PMI、HARQ-ACK、RI 等 UCI；这些控制 LLR 需要按 36.212 的复用和 channel interleaver 坐标与 UL-SCH 分离。

## 1. 发送链

```text
UL-SCH TB a[0:A-1]
  ↓ CRC24A → 分段/CB-CRC/filler
Turbo 编码每个 c_r
  ↓ Turbo 速率匹配 → e_r
码块级联 → f[0:G-1]
  ↓
UCI 独立 CRC/编码/速率匹配 → q
  ↓ 36.212 §5.2.2.7 数据/控制复用
  ↓ §5.2.2.8 channel interleaver
  ↓ 36.211 PUSCH 调制、transform precoding、SC-FDMA
```

UL-SCH 数据本身仍是 Turbo 分支；UCI 的编码方案和分配长度不能从 UL-SCH 的 `K_r` 推断。

## 2. 接收链

```text
PUSCH FFT 域 DM-RS 估计 + 频域均衡 + IDFT
  ↓ 软解调/解扰
按 channel interleaver / 复用索引分离
  ├─ UCI LLR → 对应控制译码器
  └─ UL-SCH LLR → 逆 Turbo 率匹配/HARQ → Turbo
                                      ↓ CB/TB CRC
```

PUSCH 的 SC-FDMA 变换不改变 36.212 的比特级编码，但会改变物理符号到 LLR 的索引；接收端必须先完成正确资源解映射和 IDFT/符号排序。

## 3. 长度和资源账本

除 DL-SCH 的 `A/B/C/K_r/D_r/E_r/G` 外，UL-SCH 至少记录：

| 字段 | 含义 |
|---|---|
| `Q_m` | PUSCH 调制阶数 |
| `N_L` | UL-SCH 层数 |
| `E_UL`/`G` | UL-SCH 可用编码比特数 |
| `O_ACK`、`O_CQI`、`O_RI` | 各类 UCI 原始长度 |
| `Q'_ACK`、`Q'_CQI`、`Q'_RI` | 复用前各控制编码长度 |
| `H/H'` | 复用和层/调制分组长度 |
| `mux_index` | 每个输出位置的 data/UCI 归属 |

资源不足时，UCI 的截短、优先级和字段保留由目标 Release 条款决定；不能把被丢弃的 UCI 记为 Turbo 译码失败。

## 4. HARQ 与软合并

UL-SCH Turbo 码块的 RV 逆映射和软合并与 DL-SCH 类似：

$$
L_{UL,combined}(i)=\sum_t w_t(i)L_{UL,t}(i).
$$

但 UCI 通常有独立的编码/复用状态，不能把整个 PUSCH LLR 数组无条件合并到 UL-SCH 软缓冲区。每个 HARQ 进程要保存 `mux_index`、RV、层数、调制阶数和 NDI。

## 5. 诊断状态

- `dmrs_missing`：PUSCH DM-RS 无法提取。
- `scfdma_index_error`：FFT/子载波/IDFT 顺序错误。
- `mux_index_error`：UCI 与 UL-SCH 坐标分离错误。
- `uci_decode_fail`：UCI 分支 CRC/译码失败。
- `ulsch_cb_crc_fail` / `ulsch_tb_crc_fail`：数据分支失败。
- `harq_softbuffer_mismatch`：RV/传输未映射到同一母码坐标。

## 6. 常见误区

- 把 PUSCH DM-RS 当作数据比特，或把 UCI 直接接到 Turbo 译码器。
- 在 IDFT 前后交换均衡位置，导致 LLR 维度看似正确但符号顺序错误。
- 只保存 UCI 长度、不保存复用坐标。
- 用 DL-SCH 的 `E_r` 分配和软缓冲区公式处理 UL-SCH。

## 7. 最小验证

先做无 UCI 的 UL-SCH 闭环，再加入一类 UCI，最后加入多类 UCI、有限资源和 HARQ。每次固定 PUSCH PRB、DM-RS、FFT/IDFT、`Q_m`、层数、LLR 约定和随机种子。

## 证据与待核验

- `STANDARD`：36.212 §5.2.2 的 UL-SCH、UCI 复用和 channel interleaver；36.211 §5.3/§5.5 的 PUSCH/DM-RS/SC-FDMA。
- `PERSONAL_NOTE`：分层长度账本、复用索引和故障分类。
- `NEEDS_EXTERNAL_REFERENCE`：全部 UCI 格式、beta offset、资源不足处理和目标 Release 的短 TTI 分支。

## 关联笔记

- [[LTE-DL-SCH 编码链]]
- [[LTE-控制信道编码链]]
- [[LTE-CRC 与码块分段]]
- [[LTE-Turbo 编码与译码]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE OFDM 与 SC-FDMA 接收及频域均衡]]
