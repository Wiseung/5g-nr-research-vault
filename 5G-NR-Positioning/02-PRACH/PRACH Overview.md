---
title: PRACH Overview
aliases:
  - NR PRACH 概览
  - 物理随机接入信道概览
type: atomic
status: partial
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - channel/random-access
  - stage/detection
  - topic/定位
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.321
  - 用户项目流程说明
related:
  - "[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]"
  - "[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]"
  - "[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]"
---

# PRACH Overview

## 1. 一句话定义

PRACH（Physical Random Access Channel）是 UE 发起随机接入时发送前导的上行物理信道，用于让网络发现接入事件、估计到达时延并启动后续随机接入流程。

## 2. 为什么项目需要它

本项目把 PRACH 作为被动监测的第一事件入口：先检测前导和 RA Occasion，再在 RAR 窗口寻找 RA-RNTI、RAR、临时 C-RNTI 及后续 Msg3/Msg4。PRACH 不能单独给出最终 C-RNTI；该边界已在 [[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]] 明确说明。

## 3. 它位于整个 5G 空口链路的什么位置

它位于“原始 IQ → 同步/小区识别 → TDD 资源标注”之后、“RAR/Msg3/争用解决 → C-RNTI → PDCCH”之前。PRACH 是 Msg1 的物理承载，不是完整 Random Access 的同义词。

## 4. 输入

- 小区和载波同步结果、SCS、采样率、帧/时隙边界。
- RACH-ConfigCommon 或等价设备配置。
- PRACH 格式、根序列、循环移位、时域/频域 Occasion。
- 连续 IQ 及捕获起点、频偏和噪声估计。

## 5. 输出

- 前导索引、时域/频域 Occasion、相关峰和样点时延。
- 检测门限、峰轨迹、频偏/多径诊断、碰撞标记。
- 供 RA-RNTI 候选和 RAR 窗口使用的事件键。
- 状态应区分 preamble_detected、ambiguous、toa_valid，不能直接输出 C-RNTI。

## 6. 关键参数

prach-ConfigurationIndex、PRACH format、L_RA、根序列索引、zeroCorrelationZoneConfig、restrictedSetConfig、msg1-FDM、频域起点、SSB-to-RO 映射、功率门限和检测窗口。具体字段属于版本化 RRC/MAC 配置，未锁定 Release 时标记 NEEDS_EXTERNAL_REFERENCE。

## 7. 时域位置

PRACH 只出现在配置允许的 PRACH Occasion；一个 Occasion 的起始符号、持续符号数和保护区由格式与 numerology 决定。检测窗口必须覆盖前导有效序列和循环前缀，不能用任意 PUSCH 符号窗口代替。

## 8. 频域位置

PRACH 可能使用与普通 UL BWP 不同的频域资源和子载波间隔。应保存绝对频点、PRACH 频域 Occasion、局部 PRACH 资源索引和 Point A/BWP 关系，不能把 FFT 数组列号直接当 PRB 号。

## 9. 数学原理

已知前导序列 $u[n]$ 的接收模型可写为

$$
r[n]=\alpha u[n-n_0]+w[n],\qquad
z[\ell]=\sum_n r[n]u^*[n-\ell].
$$

峰值位置给出粗时延 $n_[hat]$，幅度给出检测统计量；循环移位使同一根序列的不同前导在理想条件下保持低互相关。多径、CFO、采样偏差和碰撞会改变峰形，需保留全相关轨迹。

## 10. 3GPP 对应规范

- TS 38.211：重点核对 §5.3.2（PRACH OFDM 基带波形生成）以及 §6.3.3.1/§6.3.3.2（序列生成和物理资源映射）；具体版本/子条款需按项目 Release 复核，状态 NEEDS_EXTERNAL_REFERENCE。
- TS 38.213：重点核对 §8.1 的 PRACH Occasion/资源与 §8.2、§8.2A 的随机接入响应上下文，版本化表格待核。
- TS 38.321：§5.1 Random Access Procedure 规定 Msg1 之后的 MAC 过程。
- 相关字段：RACH-ConfigCommon、prach-ConfigurationIndex、msg1-FDM、msg1-FrequencyStart、zeroCorrelationZoneConfig。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- nrPRACHConfig：构造 PRACH 配置对象，属性和版本行为需在本机核对。
- nrPRACH、nrPRACHIndices：生成前导符号或资源索引，适合建立已知真值。
- nrPRACHDetect：时域相关检测入口；现有实验页指出多实例输出和 strongest peak 限制，不能替代全峰检测器。
- nrOFDMModulate、nrOFDMDemodulate 或 nrWaveformGenerator：波形/网格转换，参数签名标记 NEEDS_EXTERNAL_REFERENCE。

本节函数名均为外部 API 线索，需在项目 MATLAB/5G Toolbox Release 中核对后才能作为实现依赖。

## 12. 本项目中的用途

先用 PRACH 检测产出 event_id=(cell,frame,slot,RO,preamble)，再由 [[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]] 生成 RAR 候选；只有 RAR、Msg3/Msg4 和争用解决证据一致，才把候选升级为 [[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]，然后交给 PDCCH 盲搜。

## 13. 常见误区

- 把 PRACH 前导、RA Occasion、RA-RNTI、RAR、Msg3、临时 C-RNTI 和最终 C-RNTI 当成一个字段。
- 看到相关峰就宣称识别了 UE。
- 只保留 strongest peak，忽略碰撞和多径。
- 用普通 UL BWP/PUSCH 参数替代 PRACH 专用配置。

## 14. 与相似概念的区别

PRACH 是物理信道；Random Access Procedure 是跨 PHY/MAC 的过程；RA-RNTI 是响应窗口寻址上下文；RAR 是 Msg2 的 MAC PDU；Msg3 是按 RAR grant 发送的 PUSCH；C-RNTI 是后续专用寻址标识。与 DM-RS 相比，PRACH 前导重点是接入检测和时延，不是数据解调 CSI。

## 15. 代码实现注意事项

- 所有索引同时保存 0-based/1-based 约定、局部/绝对频域坐标。
- 对每个 Occasion 保留相关数组、门限、峰筛选和失败原因。
- 配置快照与 IQ 的 capture_id、Release、采样率绑定。
- 2-step、4-step、CBRA、CFRA 分支不能静默复用同一状态机。

## 16. 待实验验证的问题

- 本项目网络使用 2-step 还是 4-step RA，是否有 CFRA。
- nrPRACHDetect 与自定义全峰检测在碰撞、多径、CFO 下的差异。
- PRACH 时延估计的首径/最大峰策略及亚采样误差。
- 从一个真实 Occasion 能否完整观测 RAR、Msg3、Msg4。

## 17. Related Notes

- 新项目链：[[5G-NR-Positioning/02-PRACH/PRACH Configuration|PRACH Configuration]]、[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]、[[5G-NR-Positioning/02-PRACH/PRACH Detection|PRACH Detection]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure|Random Access Procedure]]。
- RA 对象：[[5G-NR-Positioning/02-PRACH/RA-RNTI|RA-RNTI]]、[[5G-NR-Positioning/02-PRACH/RAR|RAR]]、[[5G-NR-Positioning/02-PRACH/Msg3|Msg3]]、[[5G-NR-Positioning/02-PRACH/C-RNTI|C-RNTI]]。
- 旧笔记：[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]、[[01-专题知识/信道估计与均衡/02 参考信号与导频设计|参考信号与导频设计]]。

## 18. 从 IQ 到可审计事件

本项目的“检测到 PRACH”不是一个布尔值，而是一串可以回放的中间产物。建议把每个阶段的停止条件也写入日志：

| 阶段 | 输入 | 产物 | 可以停止的原因 |
|---|---|---|---|
| 同步 | SSB/PSS/SSS、采样时钟 | `sync_snapshot` | 小区或帧边界不确定 |
| 配置 | SIB1/RRC/设备元数据 | `config_snapshot` | Release/字段缺失 |
| RO 展开 | 配置、帧号、TDD | `ro_snapshot` | Occasion 无效或频域越界 |
| 模板 | 根序列、移位、`L_RA` | `preamble_template` | 根索引/格式不一致 |
| 检测 | IQ、RO、模板 | `peak_list` | 无峰、低质量或碰撞未消歧 |
| 时延 | 峰轨迹、采样率、校准 | `toa_observation` | 峰簇不可分或校准缺失 |
| 响应 | RA-RNTI 候选、PDCCH/PDSCH | `rar_event` | CRC 失败、RAPID 不匹配 |
| 关联 | RAR、Msg3、Msg4 | `ra_state_event` | 超时、争用失败或消息不可见 |

任何阶段失败都应保留上一阶段的证据。比如 RAR 不可见时，仍可保留 `preamble_detected` 和 `toa_observation`，不能把整条链改写成“没有 UE”。

## 19. Type-1/Type-2 与 CBRA/CFRA

在 Release 17 基线中，38.213 把物理随机接入分为 Type-1 和 Type-2；工程资料中常把它们分别称为 4-step RA 和 2-step RA。两组术语应在事件日志中同时保存，避免仅凭 `MsgA/MsgB` 或 `Msg1/Msg2` 猜测流程。

| 维度 | Type-1（常称 4-step） | Type-2（常称 2-step） |
|---|---|---|
| 首次上行 | PRACH 前导（Msg1） | PRACH 前导 + 关联 PUSCH（MsgA） |
| 响应寻址 | `RA-RNTI` | `MSGB-RNTI`（由 RO 上下文派生） |
| 下行响应 | RAR/Msg2 | MsgB，可含 successRAR 或 fallbackRAR |
| 后续上行 | RAR UL grant 调度 Msg3 | successRAR 直接结束，fallbackRAR 可转入 Msg3 |
| 争用解决 | Msg4 或 C-RNTI 调度 | successRAR/后续 C-RNTI 调度 |
| 项目最小证据 | RO + RAPID + TA/UL grant + Msg3/Msg4 | RO + MsgA PUSCH + MsgB 类型/内容 |

`CBRA`（contention-based）允许多个 UE 选择共享前导，必须保留碰撞和争用状态；`CFRA`（contention-free）使用专用前导/资源，仍不能因为前导唯一就跳过 RAR 或后续协议证据。Beam failure recovery、SI request、PDCCH order 等触发原因还应作为独立字段记录。

## 20. 物理观测与协议证据的分层

| 观察到的现象 | 可以支持的结论 | 不能单独支持的结论 |
|---|---|---|
| RO 内有相关峰 | 某个配置假设下存在前导候选 | UE 唯一身份、RAR 已发送 |
| 峰位置稳定 | 相对到达样点候选 | 绝对距离或标准 TADV 已测得 |
| RA-RNTI CRC 通过 | RAR PDCCH 候选值得解析 | RAPID 一定匹配、MAC RAR 正确 |
| RAPID 匹配 | 某个 Msg1 与 RAR 子 PDU 关联 | 争用已解决、C-RNTI 已确认 |
| Temporary C-RNTI 出现 | 随机接入阶段临时标识候选 | 最终 C-RNTI 生命周期已建立 |
| Msg3 PUSCH 命中 | RAR grant 与一段 UL 资源相容 | MAC 内容或 UE 身份必然可见 |
| Msg4/后续 C-RNTI DCI 成功 | 争用解决/后续调度证据增强 | 跨时间无限期追踪同一 UE |

该分层是项目的 `evidence_kind` 约束：`STANDARD` 描述规范定义，`PERSONAL_NOTE` 描述本地解释，`EXPERIMENT` 只描述已记录运行结果。

## 21. 推荐的事件状态机

```text
UNKNOWN_CONFIG
  -> CONFIG_READY
  -> RO_READY
  -> PREAMBLE_CANDIDATE
       ├─无有效峰──────────────> RO_EMPTY
       ├─单峰/可解释───────────> PREAMBLE_DETECTED
       └─多峰/碰撞未消歧───────> PREAMBLE_AMBIGUOUS
  -> TOA_VALID | TOA_UNRELIABLE
  -> RA_RNTI_COMPUTED
       ├─RAR 未找到/CRC失败────> RAR_UNMATCHED
       └─RAPID 匹配────────────> RAR_MATCHED
  -> TEMP_C_RNTI_CANDIDATE
       ├─Msg3/Msg4 不可见──────> ASSOCIATION_PENDING
       ├─争用失败/超时─────────> RA_FAILED
       └─争用解决证据──────────> C_RNTI_CONFIRMED
```

状态转换应带 `reason`、`source_ref` 和时间戳；禁止用后续“确认”状态覆盖前面原始观测。候选老化时进入 `EXPIRED`，而不是删除历史事件。

## 22. 与定位支路的接口

PRACH ToA 是“接入事件的上行到达候选”，不是标准定位协议消息本身。写入 [[5G-NR-Positioning/05-定位观测量/Timing Observation|Timing Observation]] 前至少携带：

- `event_id`、站点和天线/接收链路；
- RO 起点、捕获起点、帧/时隙/符号坐标；
- `first_path`、`strongest_path` 或 `cluster` 峰策略；
- 采样率、CFO/采样率校正、滤波群时延和 RF 延迟状态；
- 是否有 TA 命令，以及 TA 与接收 ToA 的分开字段。

多站差分可写成项目观测模型：

$$
\widehat{\tau}_{i}=\tau_{i}^{prop}+b_i+d_i+e_i,
\qquad
\widehat{\Delta\tau}_{ij}=\widehat{\tau}_i-\widehat{\tau}_j.
$$

其中 $b_i$ 是站间时钟项，$d_i$ 是 RF/数字链路固定延迟；在未校准时，不得把 $\widehat{\Delta\tau}_{ij}$ 直接解释成几何距离差。

## 23. Release 17 证据账本

| 主张 | 证据级别 | 核验位置 | 当前限制 |
|---|---|---|---|
| PRACH 序列、端口和时频映射 | `STANDARD` | [38.211 V17.8.0 §5.3.2、§6.3.3.1/§6.3.3.2](https://etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf) | 现场格式和频域参数未锁定 |
| Type-1/Type-2、RO 有效性和响应窗口 | `STANDARD` | [38.213 V17.8.0 §8、§8.1、§8.2、§8.2A](https://etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) | 设备是否支持全部分支未知 |
| RAR、Msg3、争用解决和 C-RNTI 转换 | `STANDARD` | [38.321 V17.8.0 §5.1、§6.1.5、§6.2.3](https://etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf) | 尚无现场 MAC 解码正例 |
| RACH 配置字段 | `STANDARD` | [38.331 V17.0.0 RACH-ConfigCommon/Generic](https://etsi.org/deliver/etsi_ts/138300_138399/138331/17.00.00_60/ts_138331v170000p.pdf) | 当前网络 Release 待确认 |
| PRACH TADV/首径参考点 | `STANDARD` | [38.215 V17.5.0 §5.2.7](https://etsi.org/deliver/etsi_ts/138200_138299/138215/17.05.00_60/ts_138215v170500p.pdf) | 被动接收机校准不等价于 gNB 测量 |
| 事件键、状态机和峰保留策略 | `PERSONAL_NOTE` | 本项目流程说明与本目录数据契约 | 尚未用真实 IQ 验证 |

## 24. 最小可验收闭环

1. 用固定 Release 和人工构造配置生成一个 RO、一个根序列和一个已知前导。
2. 在无噪声、单径条件下验证模板相关峰位置、前导索引和资源坐标可逆。
3. 加入已知整数/亚采样延迟，检查 `sample_offset`、`toa_reference` 和误差是否闭合。
4. 构造两个不同循环移位或两个同 RO 用户，确认检测器保留多峰而非静默择一。
5. 构造 RAR 中匹配与不匹配 RAPID，分别记录 `RAR_MATCHED` 和 `RAR_UNMATCHED`。
6. 对 4-step 和 2-step 各走一条失败分支，确认超时/回退不被写成 C-RNTI 成功。
7. 用 Obsidian 链接检查和结构化事件回读确认所有引用、状态和证据字段可追踪。

## 25. 当前待补实测项

- 网络实际 Release、PRACH 格式、`L_RA`、RO 周期和 TDD 有效性；
- `RACH-ConfigCommon` 与 `RACH-ConfigDedicated` 的完整快照；
- 2-step/4-step、CBRA/CFRA、SUL、beam-specific 触发比例；
- `nrPRACHDetect` 的本机输入维度、返回字段和多峰行为；
- RAR/Msg3/Msg4 的可见性、抓包窗口和 MAC 解码成功率；
- 各接收站 RF、滤波器、时钟和采样率校准记录。
