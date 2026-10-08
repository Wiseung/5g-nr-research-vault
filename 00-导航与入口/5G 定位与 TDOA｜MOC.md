---
title: 5G 定位与 TDOA
aliases:
  - 5G 定位与 TDOA
  - 5G NR 被动监测定位
  - NR TDD 定位知识库
type: moc
status: seed
created: 2026-09-04
tags:
  - moc/5g-nr
  - domain/5g-nr
  - topic/定位
  - topic/tdoa
  - stage/解析
  - stage/仿真
---

# 5G 定位与 TDOA

> [!abstract] 项目主线
> 本专题面向第三方连续采集设备：在同一 5G TDD 载频上监测 DL/UL，先恢复时频与方向资源，再通过 PRACH/随机接入事件建立有限的用户关联，之后用 C-RNTI 驱动 PDCCH/PDSCH/PUSCH 解析和单用户截取，最后对多个站点观测到的 UE 上行信号做项目定制的 UL-TOA/RTOA/TDOA 协同定位（标准 UL-RTOA 的参考口径需另行核对）。

## 1. 先看这条链

```text
TDD 连续采集与小区/帧同步
    ↓
DL/UL/flexible/guard 资源标注
    ↓
PRACH 前导检测（不是直接读 C-RNTI）
    ↓
RA-RNTI → RAR（PDSCH 上的 MAC 内容）→ TEMPORARY-C-RNTI → Msg3/Msg4
    ↓
C-RNTI 关联与 PDCCH/DCI 盲搜
    ↓
PDSCH/PUSCH 时频资源、DM-RS 和编码参数解析
    ↓
目标用户滤波/截断与质量评估
    ↓
多站项目 UL-TOA/RTOA/TDOA、校准、几何解算
```

### 关键纠偏

1. NR TDD 的“上下行同时监测”是同一连续时间轴上的采集和并行处理；DL/UL 在具体符号上的方向由 D/U/F 配置决定。
2. PRACH 的前导索引和 occasion 是随机接入事件证据，不是唯一用户 ID，也不直接携带 C-RNTI。
3. 固定第三方站对下行做的时差首先描述下行发射源；项目要定位 UE，应优先使用多个站接收的上行 PRACH/PUSCH/SRS/定位参考。
4. `CRC pass`、`valid DCI`、`user_associated`、`toa_valid` 和 `tdoa_usable` 是不同状态。

## 2. 知识点索引

### 系统与资源

| 知识点 | 作用 | 证据/状态 |
|---|---|---|
| [[5G TDD 上下行监测与资源解析]] | 同频连续采集、D/U/F 标注、坐标契约 | `PERSONAL_NOTE + STANDARD partial` |
| [[单用户时频截取与定位观测量]] | 资源掩码、滤波/截断、群时延和质量 | `PERSONAL_NOTE + NEEDS_VERIFICATION` |
| [[01 5G 物理层与信道模型]] | OFDM、资源网格、TDL/CDL 前置 | `PERSONAL_NOTE` |
| [[06 OFDM 接收与频域均衡]] | 同步、CP、FFT、频域均衡 | `PERSONAL_NOTE` |

### 随机接入与用户关联

| 知识点 | 作用 | 证据/状态 |
|---|---|---|
| [[NR PRACH 检测与 RA-RNTI-C-RNTI 关联]] | Msg1-4、RA-RNTI、临时 C-RNTI、争用解决 | `STANDARD partial + NEEDS_VERIFICATION` |
| [[02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别]] | 相关检测与 PRACH/DM-RS 边界 | `PERSONAL_NOTE` |
| [[NR-DCI 编码链]] | RNTI CRC 掩码、候选级 Polar/CRC | `PERSONAL_NOTE + STANDARD partial` |

### 控制、数据与定位

| 知识点 | 作用 | 证据/状态 |
|---|---|---|
| [[NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]] | DCI 候选、资源快照、PDSCH/PUSCH 边界 | `STANDARD partial + NEEDS_VERIFICATION` |
| [[NR-DL-SCH 编码链]] | PDSCH/DL-SCH 逆率匹配、LDPC、TB-CRC | `PERSONAL_NOTE` |
| [[NR-UL-SCH 编码链]] | PUSCH/UL-SCH 与 UCI 复用边界 | `PERSONAL_NOTE` |
| [[多站 UL-TDOA 定位与同步]] | 项目 UL-TOA/RTOA/TDOA、时钟/RF 校准、几何和误差 | `STANDARD partial + HYPOTHESIS` |
| [[5G-NR-Positioning/06-TDOA定位/TDOA Measurement Model]] | ToA/TDOA 差分矩阵、钟差模型、协方差和物理可行性 | PERSONAL_NOTE + NEEDS_VERIFICATION |
| [[5G-NR-Positioning/06-TDOA定位/TDOA Geometry and Solvers]] | 双曲线几何、Jacobian、WLS、初值、约束和求解诊断 | PERSONAL_NOTE + NEEDS_VERIFICATION |
| [[5G-NR-Positioning/06-TDOA定位/TDOA Robust Estimation]] | 标准化残差、NLOS/坏站、留一站和替代候选 | HYPOTHESIS + NEEDS_VERIFICATION |
| [[5G-NR-Positioning/06-TDOA定位/TDOA Geometry Quality]] | rank、奇异值、条件数、GDOP-like 和布局退化 | PERSONAL_NOTE + NEEDS_VERIFICATION |
| [[5G-NR-Positioning/06-TDOA定位/TDOA Validation Ledger]] | T0-T9 分层实验、指标、故障分类和复现台账 | EXPERIMENT + NEEDS_VERIFICATION |

### 项目接手

- [[第三方 5G 定位项目接手与数据契约]]：嘉琪工程交接、采集字段、阶段门槛和问题清单。
- [[5G-NR-Positioning/08-MATLAB代码/NR_decode_test 代码学习与协议映射]]：从真实 MATLAB 入口理解 SSB/PDCCH/PDSCH 解码步骤和待核验假设。

## 3. 仿真索引

| 实验页 | 对应阶段 | 当前状态 |
|---|---|---|
| [[仿真：NR 被动监测从 PRACH 到 UL-TDOA 全流程]] | F0-F5 全流程编排 | `EXPERIMENT + NEEDS_VERIFICATION` |
| [[仿真：PRACH 检测与 RA 事件关联]] | F1/F2 | `EXPERIMENT + NEEDS_VERIFICATION` |
| [[仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜]] | F3 | `EXPERIMENT + NEEDS_VERIFICATION` |
| [[仿真：多站 UL-TDOA 协同定位]] | F4/F5 | `EXPERIMENT + NEEDS_VERIFICATION` |
| [[仿真-无噪声编解码闭环]] | DCI/数据编码接口基线 | `EXPERIMENT + NEEDS_VERIFICATION` |
| [[08 仿真实验：LS 与 MMSE]] | DM-RS/CSI 估计基线 | `EXPERIMENT + NEEDS_VERIFICATION` |
| [[09 仿真实验：MIMO 均衡]] | 端口/层/均衡基线 | `EXPERIMENT + NEEDS_VERIFICATION` |

## 4. 三层关系表

| 用户问题 | 知识节点 | 仿真/验证 | 主要标准入口 |
|---|---|---|---|
| 如何在同频 TDD 中区分上下行？ | [[5G TDD 上下行监测与资源解析]] | [[仿真：NR 被动监测从 PRACH 到 UL-TDOA 全流程]] F0 | [[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.213｜Physical layer procedures for control]] |
| PRACH 是否能直接给 C-RNTI？ | [[NR PRACH 检测与 RA-RNTI-C-RNTI 关联]] | [[仿真：PRACH 检测与 RA 事件关联]] P0-P4 | TS 38.211/38.213/38.321 |
| 如何用 C-RNTI 盲搜 PDCCH/PDSCH？ | [[NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]、[[NR-DCI 编码链]] | [[仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜]] C0-C5 | TS 38.211/38.212/38.213/38.214 |
| 如何取得单用户定位片段？ | [[单用户时频截取与定位观测量]] | 全流程 F4 | TS 38.211/38.214、[[DM-RS]] |
| 三台/四台设备如何做 TDOA？ | [[多站 UL-TDOA 定位与同步]] | [[仿真：多站 UL-TDOA 协同定位]] T0-T6 | TS 38.305/38.215 |

## 5. 项目阶段与验收

### 当前阶段：PRACH 单站接手

- [ ] 取得嘉琪工程版本、运行入口、样本和 MATLAB/5G Toolbox 版本。
- [ ] 核对 PRACH 格式、根序列、循环移位、occasion、SCS、采样率和窗口。
- [ ] 重现单前导相关峰，保存全轨迹、门限、整数/亚采样偏移。
- [ ] 明确当前输出是前导事件、RAR/临时 C-RNTI，还是已经完成 C-RNTI 争用解决。

### 下一阶段：C-RNTI 与控制/数据

- [ ] 用一个已知 C-RNTI 正例和两个错误候选完成 PDCCH C0/C1。
- [ ] 保存 CORESET、搜索空间、聚合等级、候选、DCI 格式和 RNTI 假设。
- [ ] 由有效 DCI 生成 resource/coding snapshot，验证 PDSCH/PUSCH 资源命中。
- [ ] 把定位支路（参考序列/ToA）与完整译码支路（LDPC/TB-CRC）分开统计。

### 最后阶段：多站实时化

- [ ] 固定三站二维坐标和参考站，完成公共时钟/RF/滤波延迟标定。
- [ ] 在单径、理想时钟下通过 T0/T1，再加入一个误差因素。
- [ ] 报告 ToA/TDOA/位置 RMSE、95% 分位数、GDOP、残差和尾延迟。
- [ ] 评估四站冗余、碰撞/NLOS/丢站和实时缓存等待。

## 6. 参数与版本待确认

| 项目 | 当前记录 | 处理 |
|---|---|---|
| `120.88 MHz` | 用户口述“120.88 兆” | `TODO`：确认是中心频率、带宽、采样率还是其他量 |
| NR Release | 未提供 | `NEEDS_EXTERNAL_REFERENCE`：锁定标准/工具箱版本 |
| RA 类型 | 未提供 | `TODO`：确认 2-step、4-step、CBRA/CFRA |
| TDD pattern | 未提供 | `TODO`：从 SIB1/RRC/设备元数据取得 D/U/F/guard |
| PDCCH 配置 | 未提供 | `TODO`：CORESET、搜索空间、DCI 格式和候选来源 |
| 多站时基 | 未提供 | `TODO`：GNSS/PPS、PTP、线缆触发或其他方案 |
| 定位主观测 | 候选为 PRACH/PUSCH/DM-RS/SRS | `HYPOTHESIS`：先以已知上行参考序列做对照 |

## 7. 证据规则

- `STANDARD`：只写已由标准入口支持的职责、接口和术语；版本/表格未核对时加 `partial`。
- `PERSONAL_NOTE`：用户项目流程和本库已有推导，不能升级为规范要求。
- `HYPOTHESIS`：定制被动 UL-TDOA、参考序列选择、实时候选策略等待实验验证的方案。
- `EXPERIMENT + NEEDS_VERIFICATION`：所有新仿真页在真实运行、保存参数和结果前都保持此状态。
- `TODO`：明确缺失的配置、版本、代码或实测数据，不用默认值隐藏。

## 8. 标准与外部资料

- [[3GPP TS 38.211｜Physical channels and modulation]]：物理信道、资源网格、调制和参考信号映射。
- [[3GPP TS 38.212｜Multiplexing and channel coding]]：DCI/数据的 Polar/LDPC、CRC 和率匹配。
- [[3GPP TS 38.213｜Physical layer procedures for control]]：PRACH occasion 上下文、PDCCH 监测、搜索空间和控制状态。
- [[3GPP TS 38.214｜Physical layer procedures for data]]：PDSCH/PUSCH 调度、MCS/TBS/RV 和数据参数。
- [ETSI TS 38.321 V16.21.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/16.21.00_60/ts_138321v162100p.pdf)：随机接入、RAR、争用解决和 RNTI 状态（版本待统一）。
- [ETSI TS 38.305 V18.5.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf)：DL-TDOA/UL-TDOA 标准定位架构（不等同本项目定制被动方案）。
- [ETSI TS 38.215 V17.2.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf)：UL-RTOA/参考点/首径测量边界，需与项目自定义 TOA 区分。
- [MathWorks nrPRACHDetect](https://www.mathworks.com/help/5g/ref/nrprachdetect.html)、[PDCCH 盲搜示例](https://www.mathworks.com/help/5g/ug/downlink-control-processing-and-procedures.html)：MATLAB API 线索，需本机版本核验。

## 当前状态

- 知识骨架：已建立，均明确标准/个人笔记/假设边界。
- 仿真骨架：已建立，尚无本项目真实运行结果。
- 工程事实：等待嘉琪代码、采集样本、网络配置和多站同步信息。

## 新项目目录入口

- [[5G-NR-Positioning/README]]
- [[5G-NR-Positioning/00-项目总览/5G NR Passive Positioning Pipeline]]
- [[5G-NR-Positioning/00-项目总览/Current Learning Path]]
- [[5G-NR-Positioning/00-项目总览/项目知识地图]]

## 定位观测量专题（补充）

本目录把“能测到什么”和“能否用于融合”拆开：

| 入口 | 负责的问题 | 状态 |
| --- | --- | --- |
| [[5G-NR-Positioning/05-定位观测量/README|05-定位观测量]] | 目录边界、阅读顺序和质量门 | partial |
| [[5G-NR-Positioning/05-定位观测量/Observation Taxonomy|定位观测量分类]] | 时间/频率/功率/空间/身份/几何观测的角色 | STANDARD partial + PERSONAL_NOTE |
| [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables|标准与被动观测对照]] | PRS、SRS、UL/DL-TDOA、Multi-RTT、AoA 的发射源和测量主体 | STANDARD partial + NEEDS_EXTERNAL_REFERENCE |
| [[5G-NR-Positioning/05-定位观测量/Timing Observation|Timing Observation]] | 参考点、ToA/RToA/TDoA、峰和校准 | STANDARD partial + NEEDS_VERIFICATION |
| [[5G-NR-Positioning/05-定位观测量/Observation Event Schema|观测事件 Schema]] | 事件键、单站字段、跨站关联和状态机 | PERSONAL_NOTE + NEEDS_VERIFICATION |
| [[5G-NR-Positioning/05-定位观测量/Quality and Uncertainty|质量与不确定度]] | 误差预算、协方差、质量等级和验证 | EXPERIMENT + NEEDS_VERIFICATION |

这些页面输出的是项目内部可回放接口，不替代 38.215/38.305 的标准测量报告或定位协议。

直接入口：

- [[5G-NR-Positioning/05-定位观测量/README]]
- [[5G-NR-Positioning/05-定位观测量/Observation Taxonomy]]
- [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]
- [[5G-NR-Positioning/05-定位观测量/Timing Observation]]
- [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]]
- [[5G-NR-Positioning/05-定位观测量/Quality and Uncertainty]]

## TDOA 解算层入口

在单用户时间观测和多站同步完成后，按以下顺序进入几何层：

1. [[5G-NR-Positioning/06-TDOA定位/TDOA Measurement Model]]：锁定差分方向、矩阵和协方差。
2. [[5G-NR-Positioning/06-TDOA定位/TDOA Geometry and Solvers]]：建立无鲁棒 WLS 基线和求解诊断。
3. [[5G-NR-Positioning/06-TDOA定位/TDOA Geometry Quality]]：检查空间可观测性、条件数和协方差。
4. [[5G-NR-Positioning/06-TDOA定位/TDOA Robust Estimation]]：按预注册规则处理异常站和 NLOS 候选。
5. [[5G-NR-Positioning/06-TDOA定位/TDOA Validation Ledger]]：用合成、回环、回放和现场层级验收。

只有通过 [[5G-NR-Positioning/05-定位观测量/Quality and Uncertainty]] 质量门的观测才进入这条链；所有页面仍保留 NEEDS_VERIFICATION 边界。
