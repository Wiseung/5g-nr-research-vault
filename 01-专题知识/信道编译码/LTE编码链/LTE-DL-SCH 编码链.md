---
title: LTE-DL-SCH 编码链
aliases:
  - LTE 下行共享信道编码链
  - LTE PDSCH Turbo 链
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/4g-lte
  - domain/LTE
  - channel/dl-sch
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
  - "[[LTE-CRC 与码块分段]]"
  - "[[LTE-速率匹配与 HARQ 软合并]]"
  - "[[LTE OFDM 与 SC-FDMA 接收及频域均衡]]"
---

# LTE-DL-SCH 编码链

> [!abstract] 一句话结论
> LTE DL-SCH 的传输块经 CRC24A、码块分段/CRC24B、逐码块 Turbo 编码、Turbo 速率匹配和码块级联后形成 PDSCH 码字；接收端必须从 PDSCH 的软 LLR 反向恢复每个码块，再按 CB-CRC 和 TB-CRC 判定传输是否成功。

## 1. 适用范围

本页聚焦常规 LTE DL-SCH → PDSCH 数据链，不展开 MBMS、侧链路、增强型短 TTI 和 NB-IoT 特殊分支。具体传输块大小、调制、层数、RV 和资源由调度/物理层配置提供。

## 2. 从传输块到物理比特

```text
MAC 传输块 a[0:A-1]
  ↓ CRC24A
b[0:B-1], B=A+24
  ↓ §5.1.2 分段；必要时 CB-CRC24B/filler
c_r[0:K_r-1], r=0...C-1
  ↓ Turbo（每路 D_r=K_r+4）
d_r^(0), d_r^(1), d_r^(2)
  ↓ §5.1.4.1 速率匹配（rv_idx）
e_r[0:E_r-1]
  ↓ §5.1.5 码块级联
f[0:G-1], G=ΣE_r
  ↓ 36.211 扰码/调制/层映射/PDSCH
```

## 3. 参数账本

| 参数 | 说明 | 不变量 |
|---|---|---|
| `A` | TB 有效载荷 | 输入长度固定 |
| `B` | TB-CRC 后长度 | `B=A+24` |
| `C` | 码块数 | `C=1` 或按 6144 上限分段 |
| `K_r` | 码块输入长度 | 来自允许 Turbo `K` 集合 |
| `D_r` | 每路 Turbo 输出 | `D_r=K_r+4` |
| `E_r` | 每码块发送长度 | 由 `G、C、层数、Q_m、RV` 决定 |
| `G` | 码块级联长度 | `G=Σ_r E_r` |

## 4. 接收端逆链

```text
PDSCH RE 解映射
  ↓ 反扰码 + 软解调（带后均衡方差）
按 E_r 分割码块 LLR
  ↓ 逆 Turbo 速率匹配 + HARQ 合并
Turbo 迭代译码
  ↓
CB-CRC（适用时）→ 去 filler → 码块级联逆序
  ↓
TB-CRC24A → 交付/重传判定
```

`PDSCH` 的 CRS/UE-specific RS 信道估计和 MIMO 均衡属于 36.211/接收机层；译码器不应自行重建丢失的 RE 或错误的 LLR 尺度。

## 5. HARQ 状态

对同一 HARQ 进程，软缓冲区按码块母码坐标保存。新数据指示（NDI）改变时清空旧软信息；同一 TB 的重传则按 RV 逆映射后累加。状态至少区分：

| 状态 | 含义 |
|---|---|
| `resource_invalid` | PDSCH/DM-RS/层资源解析失败 |
| `llr_invalid` | LLR 符号、尺度或长度不合法 |
| `cb_crc_fail` | 至少一个码块 CRC 失败 |
| `tb_crc_fail` | 码块通过但 TB CRC 失败的异常/实现分支 |
| `decode_success` | TB-CRC 通过 |
| `harq_combined` | 使用了同一 TB 的多次软信息 |

## 6. 常见误区

- 把 `G` 当成 Turbo 母码长度；母码和物理发送长度不同。
- 将一个 TB 的 `E` 复用于所有码块而不检查余数分配。
- 对 `rv_idx` 只改变硬比特顺序，不改变逆率匹配的 LLR 坐标。
- 先做硬判决再合并 HARQ LLR。
- 把 PBCH/BCH 的 TBCC 链误接到 PDSCH。

## 7. 最小验证

先做非零 payload 的无噪声闭环，再加入 CRS/DM-RS 估计、MIMO 均衡、衰落和有限迭代。结果页需报告 `A/B/C/K_r/D_r/E_r/G`、RV、CRC、Turbo 迭代、帧数和错误数；没有实际运行数据时标记为 `EXPERIMENT + NEEDS_VERIFICATION`。

## 证据与待核验

- `STANDARD`：36.212 §5.3.2 的 DL-SCH 处理顺序和 36.211 的 PDSCH 物理映射边界。
- `PERSONAL_NOTE`：长度账本、HARQ 状态机和接收机诊断。
- `NEEDS_EXTERNAL_REFERENCE`：目标 Release 的 TBS/资源分配、UE 类别软缓冲区和完整调度字段。

## 关联笔记

- [[LTE-CRC 与码块分段]]
- [[LTE-Turbo 编码与译码]]
- [[LTE-速率匹配与 HARQ 软合并]]
- [[LTE-控制信道编码链]]
- [[LTE OFDM 与 SC-FDMA 接收及频域均衡]]
