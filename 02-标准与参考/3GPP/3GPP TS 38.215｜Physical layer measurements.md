---
title: 3GPP TS 38.215｜Physical layer measurements
aliases:
  - 3GPP 38.215
  - NR 物理层测量
  - TS 38.215 测量
type: reference
status: partial
tags:
  - domain/5g-nr
  - layer/physical-layer
  - evidence/3gpp
  - topic/measurement
  - topic/positioning
  - topic/timing
source:
  - 3GPP TS 38.215 V17.2.0 (Release 17)
  - "[[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]]"
  - "[[5G-NR-Positioning/05-定位观测量/Timing Observation]]"
related:
  - "[[3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[3GPP TS 38.213｜Physical layer procedures for control]]"
  - "[[3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[3GPP TS 38.321｜Medium Access Control protocol specification]]"
  - "[[3GPP TS 38.331｜Radio Resource Control protocol specification]]"
  - "[[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]"
  - "[[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]"
  - "[[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]"
---

# 3GPP TS 38.215｜Physical layer measurements

> [!abstract] 标准职责
> TS 38.215 规定 NR 物理层测量能力及其测量对象、参考点、适用状态和测量控制边界。它把 38.211/38.213/38.214 提供的参考信号和资源，转换成 UE 或 NG-RAN 可以报告的功率、质量、时间、角度和路径测量；它不是某个厂商接收机的相关器 API，也不是项目自定义 ToA/TDOA 数据格式。

## 1. 阅读定位

本页以 ETSI `3GPP TS 38.215 V17.2.0 (2022-09), Release 17` 为参考快照。当前项目没有锁定现场 Release，故采用“Release 无关的概念 + 版本化的标准事实”写法：

- `STANDARD`：可在该版本的章节中定位的测量定义、参考点和依赖关系。
- `PERSONAL_NOTE`：本项目将标准测量映射到内部观测事件的工程解释。
- `NEEDS_EXTERNAL_REFERENCE`：现场 Release、完整报告字段、误差要求、ASN.1 或设备实现仍需按目标版本复核。
- `NEEDS_VERIFICATION`：需要真实 RRC/NG-RAN 配置、校准或 IQ/测量结果才能确认的项目结论。

38.215 的核心问题是“谁在什么参考点、对什么资源、以什么窗口测量什么量”。它不单独决定：

1. 参考信号如何生成和映射（[[3GPP TS 38.211｜Physical channels and modulation]]）。
2. 搜索空间、HARQ、功率控制和测量触发如何运行（[[3GPP TS 38.213｜Physical layer procedures for control]]）。
3. 数据资源、MCS、TBS 和 CSI 过程如何配置（[[3GPP TS 38.214｜Physical layer procedures for data]]）。
4. 测量结果如何通过定位协议交换（[[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]、[[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]、[[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]）。

## 2. 范围和章节地图

ETSI V17.2.0 的范围声明为“physical layer measurements for NR”。本页只保留与当前 NR 定位、被动监测和链路质量分析直接相关的章节：

| 章节 | 主题 | 主要测量主体 | 本项目用途 |
| --- | --- | --- | --- |
| §4 | UE/NG-RAN 测量控制概念 | UE、NG-RAN | 说明 L1 测量由高层配置和控制 |
| §5.1.1--§5.1.6 | SS/CSI-RSRP、RSRQ、SINR | UE | 功率/质量指标和窗口边界 |
| §5.1.19、§5.1.21 | SRS-RSRP、RSSI | UE | 与上行参考和总功率区分 |
| §5.1.28--§5.1.30 | DL PRS-RSRP、DL RSTD、UE Rx--Tx | UE | 下行定位/时序对照 |
| §5.1.35 | DL PRS-RSRPP | UE | 首径和路径功率语义对照 |
| §5.2.1 | SSS transmit power | NG-RAN | 下行发射功率测量入口 |
| §5.2.2 | TUL-RTOA | NG-RAN | 以 SRS 为对象的上行相对到达时间 |
| §5.2.3--§5.2.4 | gNB Rx--Tx、UL AoA | NG-RAN | 上行时序和角度测量入口 |
| §5.2.5--§5.2.6 | UL SRS-RSRP、UL SRS-RSRPP | NG-RAN | 上行功率和路径功率 |
| §5.2.7 | TADV | NG-RAN | 以 PRACH 为对象的上行定时提前测量 |

表中“本项目用途”是 `PERSONAL_NOTE`，不表示项目已经实现或具备对应标准报告能力。

## 3. 测量控制链

38.215 §4 把 L1 测量放在高层控制之下，并区分 UE measurement capabilities 与 NG-RAN measurement abilities。实现或审计时应保存完整配置链：

```text
RRC/MAC/定位配置
    ↓
测量对象、参考信号、频域带宽和时间资源
    ↓
UE 或 NG-RAN L1 测量
    ↓
参考点、单位、适用 RRC 状态和质量约束
    ↓
38.331/38.455/其他高层报告或项目内部观测事件
```

一次测量至少要能回答以下问题：

- 测量主体是 UE、gNB、TRP 还是第三方接收站？
- 测量对象是 SS/PBCH、CSI-RS、SRS、PRS、PRACH 还是总载波功率？
- 使用哪组 RE、PRB、OFDM 符号、测量间隔和频率层？
- 参考点是 UE 天线连接器、gNB 接收天线、阵列边界，还是项目采集文件起点？
- 结果是标准测量量、协议命令，还是项目算法的中间特征？

缺少上述上下文时，数值只能标为 `feature_only` 或 `NEEDS_EXTERNAL_REFERENCE`，不能因为字段名相似就升级为标准测量。

## 4. UE 测量能力（§5.1）

### 4.1 功率、质量与总功率

以下定义均以线性功率平均为核心；具体适用 RRC 状态、SMTC/测量间隙和高层配置应回到目标版本核验。

| 测量量 | V17.2.0 定义要点 | 参考点/资源边界 |
| --- | --- | --- |
| SS-RSRP (§5.1.1) | 携带 SSS 的 RE 功率贡献的线性平均；在允许时可结合 PBCH DM-RS 或 CSI-RS | 同一 SS/PBCH block index 和物理小区 ID；FR1 为 UE 天线连接器，FR2 按接收分支组合 |
| CSI-RSRP (§5.1.2) | 配置 CSI-RS 测量带宽和 occasion 内 CSI-RS RE 功率贡献的线性平均 | 默认使用 CSI-RS 端口 3000；活动 DL BWP 和测量带宽约束需保留 |
| SS-RSRQ (§5.1.3) | `N × SS-RSRP / NR carrier RSSI`，分子分母使用同一 RB 集合 | RSSI 包括各来源、邻道干扰和热噪声；时间资源受配置/SMTC 约束 |
| CSI-RSRQ (§5.1.4) | `N × CSI-RSRP / CSI-RSSI`，同一资源集合 | CSI-RSSI 对应 CSI-RS occasion 的 OFDM 符号 |
| SS-SINR (§5.1.5) | SSS RE 平均功率除以噪声和干扰 RE 平均功率 | 干扰资源可由高层配置，不能默认为“空 RE” |
| CSI-SINR (§5.1.6) | CSI-RS RE 平均功率除以噪声和干扰功率 | 端口、测量带宽和专用干扰资源需与 CSI 配置一致 |
| RSSI (§5.1.21) | 配置 OFDM 符号和带宽内所有来源总接收功率的线性平均 | 不等于 RSRP；包含服务/非服务小区、邻道干扰和热噪声 |

功率 per RE 的标准说明以有用符号部分的能量为基础并排除 CP。项目把 ADC 样点平均、相关峰功率、RE 平均功率和 RF 校准 dBm 分开存储，不能互换命名。

### 4.2 下行定位相关测量

| 测量量 | 标准语义 | 项目边界 |
| --- | --- | --- |
| DL PRS-RSRP (§5.1.28) | 配置测量带宽内承载 DL PRS 的 RE 功率贡献线性平均 | 需要确认 PRS 资源、测量主体和 UE 参考点；不由一个未知峰自动证明 |
| DL RSTD (§5.1.29) | UE 从传输点 `j` 与参考传输点 `i` 接收的相应子帧起始时间之差 | 是下行参考信号时序量；固定第三方站监听 DL 不能直接改称 UE 定位结果 |
| UE Rx--Tx (§5.1.30) | UE 接收下行子帧时序与自身上行子帧发送时序之差 | 需要 UE 同时拥有 Rx/Tx 参考，第三方被动站不具备同一测量主体 |
| DL PRS-RSRPP (§5.1.35) | DL PRS 信道响应第 `i` 个路径时延的功率；第 1 路径对应 first detected path | 首径定义、路径编号和接收分支必须按目标版本/实现核验 |

因此，多个站收到相近的下行 PRS 峰只能形成发射点时间特征；它不自动成为 UE 的 DL-TDOA。这个边界与 [[5G-NR-Positioning/05-定位观测量/Timing Observation]] 的项目规则一致。

## 5. NG-RAN 测量能力（§5.2）

### 5.1 TUL-RTOA（§5.2.2）

V17.2.0 把 UL Relative Time of Arrival 定义为：在 Reception Point（RP）`j` 接收到包含 SRS 的子帧 `i` 的起始时间，相对于 RTOA Reference Time 的值。

RTOA reference time 为：

$$
T_{0}+t_{SRS},
\qquad
t_{SRS}=(10n_f+n_{sf})\times 10^{-3}\ \mathrm{s},
$$

其中 `T_0` 是由 SFN Initialization Time 提供的 SFN 0 名义起始时刻，`n_f` 和 `n_sf` 分别是 SRS 所在系统帧号和子帧号。`T_0` 的协议来源涉及 [[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]，不是采集文件的任意起点。

RP 参考点随 TS 38.104 基站类型区分：

| 基站类型 | TUL-RTOA 参考点（V17.2.0） |
| --- | --- |
| type 1-C | Rx antenna connector |
| type 1-O 或 2-O | Rx antenna（辐射区域中心位置） |
| type 1-H | Rx Transceiver Array Boundary connector |

该定义说明了三个不可混淆的层次：SRS 是标准测量对象；RP 是测量主体和参考面；RTOA reference time 是协议时间基准。项目从 IQ 相关得到的 `toa_raw_seconds` 只有在这些条件均闭合时，才可作为标准 TUL-RTOA 的候选对照。

### 5.2 gNB Rx--Tx time difference（§5.2.3）

该测量定义为：

$$
T_{gNB\text{-}RX}-T_{gNB\text{-}TX}.
$$

`T_gNB-RX` 是包含 UE 相关 SRS 的上行子帧接收时序，按时间上的 first detected path 定义；`T_gNB-TX` 是与该上行子帧最接近的下行子帧发送时序。Rx/Tx 两侧的参考点都随基站类型而定。它不是 UE 的单站 ToA，也不是网络下发的 TA 命令。

### 5.3 UL AoA（§5.2.4）

UL Angle of Arrival 是在 gNB 天线处对与 UE 对应的上行信道估计的方位角和俯仰/垂直角。V17.2.0 同时规定全局坐标系（GCS）和本地坐标系（LCS）的参考方向约定；LCS 的 bearing、downtilt、slant 与 [[3GPP TR 38.901｜Channel model]] 的定义相关。

项目若保存 `aoa_candidate`，至少还应保存：阵列几何、天线/端口映射、参考面、频率、校准版本、坐标系和角度正方向。未校准阵列的相位差只能作为 `PERSONAL_NOTE` 诊断特征，不能直接写成标准 UL AoA。

### 5.4 UL SRS-RSRP 与 UL SRS-RSRPP（§5.2.5--§5.2.6）

- **UL SRS-RSRP**：在配置的测量频带和时间 occasion 内，对承载 SRS 的 RE 功率贡献做线性平均。参考点仍按 type 1-C、type 1-O/2-O、type 1-H 区分；接收分支组合规则不能由项目自行简化。
- **UL SRS-RSRPP**：对接收 UL SRS 信道响应的第 `i` 个路径延迟取线性平均功率；第 1 路径的功率对应时间上的 first detected path。附加路径必须与同一接收分支/测量配置关联。

两者都不是“相关峰最大值”。前者是配置资源上的平均功率，后者是路径化的信道响应功率；项目的 `peak_power_linear`、`path_count_lower_bound` 和 `snr_db` 必须另列。

### 5.5 TADV（§5.2.7）

V17.2.0 将 Timing Advance 定义为：

$$
T_{ADV}=T_{gNB\text{-}RX}-T_{gNB\text{-}TX},
$$

其中 `T_gNB-RX` 是包含 UE PRACH 的上行子帧接收时序，并由时间上的 first detected path 定义；`T_gNB-TX` 是与之最接近的下行子帧发送时序。检测到的 PRACH 用于确定包含该 PRACH 的子帧起始。

TADV 的 Rx/Tx 参考点同样按基站类型区分。它是 NG-RAN 的物理层测量量；[[3GPP TS 38.321｜Medium Access Control protocol specification]] 中的 Timing Advance command 是 MAC 控制过程中的命令，两者不能在事件模式中共用一个字段。项目必须分别保存：

```yaml
timing:
  project_toa_raw_seconds: null
  project_toa_reference_point: null
  standard_tul_rtoa_seconds: null
  standard_tadv_seconds: null
  mac_ta_command: null
  status: NEEDS_EXTERNAL_REFERENCE
```

## 6. 参考点、单位和坐标不变量

38.215 的测量值只有在参考点和资源集合明确时才可比较。建议对每条记录保存：

| 字段 | 约束 |
| --- | --- |
| `measurement_kind` | `SS_RSRP`、`CSI_RSRP`、`TUL_RTOA`、`UL_SRS_RSRPP` 等标准名称或项目明确名称 |
| `measuring_entity` | `UE`、`gNB`、`TRP`、`RP` 或 `third_party_station` |
| `reference_point` | 天线连接器、天线/阵列边界、协议时间基准或项目采样起点；未知则不能标 valid |
| `reference_signal` | SS/PBCH、CSI-RS、SRS、PRS、PRACH 等 |
| `resource_snapshot_id` | PRB/RE、端口、层、符号、带宽和 occasion 的不可变快照 |
| `measurement_window` | 起止 slot/symbol/样点、SMTC/测量间隙和保护区 |
| `frequency_range` | FR1/FR2、ARFCN、中心频率和有效测量带宽 |
| `unit` | 线性 W、dBm、秒、弧度等；dB 值要保存换算口径 |
| `source_kind` | `STANDARD`、`PERSONAL_NOTE`、`EXPERIMENT` 或 `HYPOTHESIS` |
| `evidence_status` | `verified`、`partial`、`NEEDS_EXTERNAL_REFERENCE` 或 `NEEDS_VERIFICATION` |

时间观测还要拆开协议坐标和设备坐标：

```text
protocol_time = frame/slot/subframe/symbol + SRS/PRACH/PRS resource
sample_time   = capture_start + local_sample_index / Fs
reference_time = T0 + t_SRS 或明确的校准外部时基
```

`capture_start` 不能默认为 `T_0`；`TADV` 不能默认为 `toa_raw_seconds`；`RTOA` 不能只写一个没有 RP 的浮点数。

## 7. 与相邻规范的接口

| 接口问题 | 主要规范 | 38.215 在链中的位置 |
| --- | --- | --- |
| 信号/RE 如何生成 | 38.211 | 提供可测量的 SS、CSI-RS、SRS、PRS、PRACH 资源语义 |
| 测量时机、功控、RRC 状态下的控制 | 38.213 | 接收和发送过程的时序/资源约束 |
| CSI、数据带宽和测量相关资源 | 38.214 | 配置测量带宽、CSI 资源和报告前提 |
| MAC TA、随机接入、SRS 触发 | 38.321 | 过程命令与 L2 状态，不等于 L1 测量值 |
| RRC 测量配置、BWP、SMTC、SRS/PRS 资源 | 38.331 | 半静态配置的来源；ASN.1 版本需核验 |
| 定位方法、功能实体和测量角色 | 38.305 | 定义“什么定位流程使用什么测量”的系统层边界 |
| NG-RAN 定位协议、SFN 初始化和报告 | 38.455 | 承载/交换部分测量信息，不是 IQ 或相关峰接口 |

## 8. 项目观测事件映射（PERSONAL_NOTE）

项目内部的 `Observation Event Schema` 不是 38.215 的 ASN.1，也不是 LPP/NRPPa 消息。推荐把标准对照字段和项目算法字段并排保存：

| 38.215 对照字段 | 项目字段 | 升级条件 |
| --- | --- | --- |
| `TUL-RTOA` | `toa_raw_seconds`、`rtoa_seconds` | SRS、RP、T0、SFN/子帧和校准闭合 |
| `TADV` | `prach_tadv_candidate` | PRACH 首径、gNB Rx/Tx 参考点和版本闭合 |
| `UL SRS-RSRP` | `srs_re_power_linear` | SRS RE 集合、带宽、接收分支和功率参考闭合 |
| `UL SRS-RSRPP` | `path_power[]` | 信道响应路径索引、首径策略和分支闭合 |
| `UL AoA` | `aoa_candidate_rad` | 阵列几何、校准、坐标系和上行信道闭合 |
| `SS/CSI-RSRP` | `ss_rsrp_candidate`/`csi_rsrp_candidate` | UE 测量主体、RE 集合和测量窗口闭合 |
| `DL RSTD` | `dl_rstd_candidate` | 两个 TP、对应子帧和 UE 参考点闭合 |

项目自定义相关峰流程可以这样表示：

```text
已确认资源/参考信号
    ↓
原始 IQ/资源网格与完整相关轨迹
    ↓
峰列表、first/strongest/cluster 策略和残差
    ↓
reference_point + Fs + RF/filter/clock calibration
    ↓
project ToA/RToA candidate
    ↓ 仅在标准对象、主体、协议时间基准和报告路径闭合时
standard-measurement cross-check
```

任何未经过这条链的值都不应在标题或字段中直接使用 `TUL-RTOA`、`TADV`、`UL AoA` 或 `RSRP` 作为已确认标准量。

## 9. 质量、不确定度和失败状态

38.215 定义测量量，不替项目规定一个万能的峰值门限。项目应另外记录：

- `quality_config_id`：门限、窗口、噪声估计和分支组合策略。
- `measurement_uncertainty`：重复测量、参考真值或校准实验得到的标准差/协方差。
- `first_detected_path_method`：检测窗、门限、连续性和多径判决；这是实现策略，不要写成无条件的标准算法。
- `reference_point_status`：`known`、`partial`、`unknown`。
- `calibration_status`：时钟、RF、线缆、滤波和数字链延迟是否在有效期。
- `protocol_context_status`：是否有 RRC/NG-RAN 配置、SRS/PRACH 资源和 SFN 时间基准。

推荐状态：

```text
raw_feature
  -> resource_matched
  -> reference_known
  -> measurement_candidate
  -> calibrated_candidate
  -> standard_crosscheck_ready
```

缺少测量主体、标准参考点或目标 Release 时，降级到 `NEEDS_EXTERNAL_REFERENCE`；缺少实际校准/重复观测时，保持 `NEEDS_VERIFICATION`。不要用 `0` 填充未知延迟或功率。

## 10. 常见误区

1. 把相关峰样点直接命名为标准 UL-RTOA。
2. 把 MAC Timing Advance command 当作 38.215 §5.2.7 的 TADV 测量值。
3. 把 TUL-RTOA 的 `T0 + t_SRS` 协议参考时间替换成采集文件起点。
4. 把 SS-RSRP、CSI-RSRP、SRS-RSRP、RSSI 和相关峰功率放进同一列。
5. 把 first detected path 当成 strongest path，或把工程门限写成规范固定算法。
6. 把固定第三方站接收的下行 RSTD 当作 UE 的上行定位观测。
7. 只记录 dB 数值而不记录 RE 集合、带宽、符号、噪声/干扰窗口和参考点。
8. 看到一个 `UL AoA` 字段就忽略阵列坐标、极化、相位中心和校准版本。

## 11. 最小核验清单

- [ ] 锁定目标 Release、规范版本、发布日期和引用章节。
- [ ] 对每条测量记录标明 UE/NG-RAN/RP/gNB 测量主体。
- [ ] 记录参考信号、RE/PRB 集合、带宽、时间 occasion 和测量窗口。
- [ ] 记录 FR1/FR2 与天线连接器、天线或阵列边界参考点。
- [ ] 对 TUL-RTOA 保存 `T0`、SFN/子帧、SRS 资源和 `t_SRS` 计算输入。
- [ ] 对 TADV 保存 PRACH 资源、first detected path 策略和 gNB Rx/Tx 参考点。
- [ ] 将 MAC TA command、项目 ToA 和标准 TADV 分成独立字段。
- [ ] 对功率量保存线性域输入、平均方式、噪声/干扰定义和 dB 换算。
- [ ] 对 AoA 保存坐标系、阵列几何、相位校准和角度正方向。
- [ ] 将标准测量、项目推断、实验结果和外部待核验内容分层标记。
- [ ] 在真实 RRC/NG-RAN 配置、校准和重复测量可用前，不宣称标准合规或定位精度。

## 12. 标准核验记录

- 参考版本：`3GPP TS 38.215 V17.2.0 (Release 17)`。
- 已定位章节：§1 Scope、§4 Control of UE/NG-RAN measurements、§5.1 UE measurement capabilities、§5.2 NG-RAN measurement abilities。
- 已定位测量：§5.1.1--§5.1.6、§5.1.19、§5.1.21、§5.1.28--§5.1.30、§5.1.35、§5.2.1--§5.2.7。
- 版本状态：`STANDARD + partial`；现场 Release、后续修订和完整精度/报告要求仍需外部核验。
- 项目运行状态：`NEEDS_VERIFICATION`；本 Vault 没有真实 NG-RAN 测量、RRC 快照、校准数据或标准报告闭环。

## 13. 原始来源与证据账本

| 来源 | 证据类型 | 用途 | 当前状态 |
| --- | --- | --- | --- |
| [ETSI TS 38.215 V17.2.0 PDF](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf) | `STANDARD` | §4、§5.1、§5.2 测量定义、参考点和公式 | `verified snapshot` |
| [[5G-NR-Positioning/05-定位观测量/Standard Positioning Observables]] | `PERSONAL_NOTE` | 标准测量主体/参考信号/项目边界矩阵 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Timing Observation]] | `PERSONAL_NOTE` | ToA/RToA/TDoA/TA 的字段和校准分离 | `partial` |
| [[5G-NR-Positioning/05-定位观测量/Observation Event Schema]] | `PERSONAL_NOTE` | 项目内部事件封装；不是 38.215 消息 | `partial` |
| [[5G-NR-Positioning/02-PRACH/Timing Estimation]] | `PERSONAL_NOTE` | PRACH 峰、首径和项目相关时间候选 | `partial + NEEDS_EXTERNAL_REFERENCE` |

未锁定的现场规范版本、NG-RAN 测量报告字段、精度要求、设备参考面、SRS/PRS/PRACH 可见性和真实校准结果均保持 `NEEDS_EXTERNAL_REFERENCE` 或 `NEEDS_VERIFICATION`。

## 14. 关联标准和笔记

- 物理信号与资源网格：[[3GPP TS 38.211｜Physical channels and modulation]]。
- 控制时序和功率过程：[[3GPP TS 38.213｜Physical layer procedures for control]]。
- 数据/CSI 资源过程：[[3GPP TS 38.214｜Physical layer procedures for data]]。
- MAC 随机接入、TA command 和 SRS 触发：[[3GPP TS 38.321｜Medium Access Control protocol specification]]。
- RRC 测量与资源配置：[[3GPP TS 38.331｜Radio Resource Control protocol specification]]。
- 定位架构与方法：[[3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]。
- NG-RAN 定位协议和 RTOA reference time：[[3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]。
- 侧链定位协议：[[3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]]。
- 项目观测语义：[[5G-NR-Positioning/05-定位观测量/Observation Taxonomy]]、[[5G-NR-Positioning/05-定位观测量/Quality and Uncertainty]]。
- 多站时间与 TDOA：[[5G-NR-Positioning/05-定位观测量/Timing Observation]]、[[5G-NR-Positioning/06-TDOA定位/TDOA]]。
