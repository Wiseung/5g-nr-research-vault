---
title: Standard Positioning Observables
aliases:
  - 标准定位观测量对照
  - 标准与被动观测边界
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/positioning
  - topic/measurement
  - topic/3gpp-boundary
source:
  - "[[5G-NR-Positioning/10-3GPP规范/3GPP Specification Map]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[05-定位观测量/Observation Taxonomy]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
related:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[01-专题知识/信道估计与均衡/DM-RS]]"
  - "[[01-专题知识/信道估计与均衡/SRS]]"
  - "[[01-专题知识/信道估计与均衡/CSI-RS]]"
  - "[[06-TDOA定位/TDOA]]"
---

# Standard Positioning Observables

> [!warning] 名称边界
> PRS、UL-TDOA、DL-TDOA、Multi-RTT、UL-RTOA、AoA 等名称描述的是标准方法、测量角色或观测语义，不是“看到一个峰”就自动获得的能力。本页先固定发射源、测量主体、参考信号、时间参考和报告路径；精确条款、表格、Release 差异和设备支持仍标记为 NEEDS_EXTERNAL_REFERENCE。

## 1. 先回答五个问题

对任何“定位观测量”声明，先写清楚：

1. **谁发射**：UE、gNB/TRP，还是校准参考源？
2. **谁测量**：UE、gNB/定位测量点、LMF，还是第三方接收站？
3. **测量什么**：到达时间、时间差、往返时间、功率、角度、频率还是身份？
4. **参考是什么**：哪个序列、资源、天线端口、时间基准和坐标系？
5. **结果如何使用**：标准报告、项目内部事件、TDOA 几何，还是仅作诊断？

缺少其中任何一项时，名称只能作为候选标签，不能写成标准符合性结论。

## 2. 标准定位与项目被动链的角色表

| 方法/观测 | 主要发射源 | 典型测量主体 | 需要的协议/配置上下文 | 本项目的关系 |
| --- | --- | --- | --- | --- |
| DL-TDOA | 多个 gNB/TRP 下行参考 | UE 或指定测量端 | 传输点、参考信号、测量时序和报告 | 固定第三方站测到的是下行源差异，不等于 UE 位置 |
| UL-TDOA | UE 上行定位参考 | 多个网络测量点 | 上行参考配置、测量点、时基和报告 | 可作为标准对照；无 LMF/gNB 协作时是定制被动路线 |
| Multi-RTT | UE 与多个传输点的双向交互 | UE/网络协同实体 | 往返消息、发射/接收时序和协议状态 | 被动监听不能默认具备往返交互 |
| PRS 相关观测 | gNB/TRP 下行 PRS | UE 或测量端 | PRS 资源、端口、时频配置 | 可作下行同步/标准定位参考候选 |
| SRS/定位 SRS | UE 上行 SRS | gNB/测量点 | SRS 资源、序列、周期/触发和测量参考 | 上行多站观测候选，标准口径需核验 |
| DM-RS 相关观测 | 当前物理信道的发射源 | 接收端 | PDSCH/PUSCH 资源、端口/层和调度 | 适合当前传输时间/质量；不是自动的专用定位信号 |
| PRACH 相关峰 | UE 随机接入前导 | 接收站 | RO、根序列、循环移位和检测窗 | 事件触发和粗 ToA；不直接给 C-RNTI |
| RSRP/RSRQ 等功率量 | 规定参考信号/资源 | 规定测量实体 | 测量带宽、资源和标准定义 | 可作质量/粗定位特征，精确定义待核验 |
| AoA/AoD | 单点或多点信号空间响应 | 阵列接收端/测量实体 | 阵列几何、相位校准和角度参考 | 后续扩展；未校准相位只能作相对特征 |

标准方法的名称不能跨角色移植。例如，第三方站被动接收多个 gNB 的下行峰，不能因为计算了时间差就称为 UE 的 DL-TDOA；多个站接收 UE 上行峰，也不能在没有标准参考配置和报告接口时直接宣称标准 UL-RTOA。

## 3. 参考信号的观测角色

### 3.1 PRS

PRS 是下行定位参考的候选来源。使用它时至少要保存：

- 传输点/小区和载波上下文；
- PRS 资源的时频位置、周期/重复和端口信息；
- 接收端参考点、采样率、FFT/CP 和校准状态；
- 采用的相关、相位或功率估计器；
- 这是标准定位链、同步辅助，还是项目内部下行源观测。

PRS 的存在不自动提供 UE 身份，也不自动解决多站时钟、NLOS 或发射点几何。

### 3.2 SRS

SRS 是上行探测参考的候选来源。对多站被动观测，应保存：

- SRS 资源和序列配置来源；
- UE/小区/载波及方向标签；
- 天线端口、梳状结构、带宽和跳频解释；
- 每站 raw ToA、RToA、CFO、功率和相位质量；
- 标准 UL-RTOA 口径是否已由目标 Release 核验。

如果只知道“某个上行峰像 SRS”而没有配置证据，应使用 SRS_candidate 或 reference_unknown，而不是强制命名为定位 SRS。

### 3.3 DM-RS

DM-RS 与当前 PDSCH/PUSCH 等物理传输关联。它可以提供当前传输的已知参考、信道估计、相位和时间特征，但必须区分：

- 参考序列是否已由资源/调度闭合；
- 估计的是传播信道、端口信道还是层域等效信道；
- 该片段用于解调质量、用户关联，还是时间观测；
- 下行 DM-RS 的时间差是否只是下行发射源观测。

相关信号的角色和端口边界见 [[01-专题知识/信道估计与均衡/DM-RS]]。

### 3.4 PRACH

PRACH 适合做随机接入事件检测和粗时间候选。它的观测链应保持：

~~~text
合法 RO
  ↓
根序列/循环移位参考
  ↓
相关轨迹与峰簇
  ↓
前导/事件候选和粗 ToA
  ↓
RA-RNTI/RAR/临时标识/争用解决
~~~

前导索引、RA-RNTI、RAR 中的 TA 和 C-RNTI 状态属于不同证据层。PRACH 峰通过不能单独证明唯一 UE 或最终定位资格。

## 4. 方法级观测方程

### 4.1 单站到达时间

对发射源 u 和测量站 i：

$$
\widehat{\tau}_{i,u}
=t_{tx,u}
+\frac{\|\mathbf x_u-\mathbf s_i\|}{c}
+b_i+d_i+e_i.
$$

其中 t_tx,u 在被动监听中通常未知；b_i、d_i 和 e_i 必须进入校准/质量账本。

### 4.2 UL/DL TDOA

以参考站 r：

$$
\widehat{\Delta\tau}_{i,r}
=\widehat{\tau}_{i,u}-\widehat{\tau}_{r,u}.
$$

公式本身只描述差分关系，不能决定 u 是 UE 还是 gNB/TRP。发射源和测量主体必须在事件上下文中显式保存。

### 4.3 Multi-RTT

往返观测需要至少两个方向的时间事件以及发射/接收时序。可抽象为：

$$
\widehat{T}_{RTT}
=t_{rx,2}-t_{tx,1}.
$$

并进一步扣除协议定义的处理或响应时延。没有双向交互和对应时序时，不应把单向 ToA 差值命名为 RTT。

### 4.4 角度

阵列相位差可抽象为：

$$
\Delta\phi_{mn}
=\phi_m-\phi_n
=\psi_{mn}(\theta)+\delta_{mn}^{cal}+\eta_{mn}.
$$

阵列校准项、频率、天线间距、相位中心和多径必须可回放。没有这些信息时，只输出 phase_difference 或 aoa_candidate，不输出绝对方位。

## 5. 标准名称的升级条件

项目内部名称按以下阶梯升级：

| 当前证据 | 推荐名称 | 不能写成 |
| --- | --- | --- |
| 只有能量或未知峰 | feature_candidate | ToA/RTOA/定位测量 |
| 已知模板和合法窗口 | raw_toa_candidate | 已校准 ToA |
| 单站参考点和估计器闭合 | project_toa_observation | 标准 UL-RTOA |
| 站间校准、参考信号和事件闭合 | passive_ul_tdoa_observation | 标准 UL-TDOA 合规结果 |
| 标准配置、测量主体和报告接口均核验 | standard_measurement | 未限定 Release 的通用结论 |

这是命名治理，不是降低算法目标。清楚命名可以让后续实验回答“算法失败”还是“标准接口尚未具备”。

## 6. 可观测性检查表

| 检查项 | 通过证据 | 失败时输出 |
| --- | --- | --- |
| 发射源方向 | UL/DL/unknown 和 TDD 快照 | direction_unknown |
| 参考信号 | 序列、资源和版本可回放 | reference_unknown |
| 事件身份 | event_id、RO/slot、重传/碰撞状态 | association_candidate |
| 时间基准 | 样点、参考点、采样率和时间戳 | raw_only |
| 站间校准 | clock/RF/filter/digital calibration_id | calibrated_pending |
| 标准流程 | 测量主体、配置和报告路径 | project_observation_only |
| 几何条件 | 站点坐标、坐标系、GDOP/残差 | geometry_poor |
| 质量 | 峰、SNR/SINR、协方差和失败原因 | quality_degraded |

## 7. 与本项目三阶段的映射

### 阶段一：PRACH/随机接入

- 目标：形成前导事件、粗 ToA 和有限用户关联候选。
- 主观测：PRACH 相关峰；辅助观测为功率、CFO、峰簇和碰撞标记。
- 禁止：把前导、TA 或 RA-RNTI 直接写成 C-RNTI 或绝对距离。

### 阶段二：控制/数据

- 目标：由 C-RNTI/有限候选得到 PDSCH/PUSCH 资源和参考信号。
- 主观测：PUSCH DM-RS/SRS 或已知上行片段的时间、频率和质量。
- 禁止：用 PDCCH DM-RS 的下行峰直接替代 UE 上行观测。

### 阶段三：多站融合

- 目标：对同一 event_id 的多站 UL 观测形成校准 ToA/RToA/TDOA。
- 主观测：跨站上行参考或可复现的上行模板。
- 禁止：缺少校准、协方差或几何约束时输出标准定位精度。

## 8. 观测记录的标准/项目双标签

每条记录建议同时保存：

~~~json
measurement_label:
  standard_name: null
  project_name: passive_ul_toa_candidate
  source_role: null # UE_UL, gNB_DL or unknown
  measuring_entity: null # station_a, UE, gNB, LMF or unknown
  standard_release: null
  standard_clause: null
  standard_status: NEEDS_EXTERNAL_REFERENCE
project_status:
  evidence_status: NEEDS_VERIFICATION
  calibration_status: unknown
  quality_state: feature_only
  allowed_use: null # trigger, diagnostic, tdoa_candidate or none
~~~

standard_name 只有在发射源、测量主体、参考信号、配置和目标 Release 均明确时才填写。项目字段和标准字段不共用一个字符串。

## 9. 规范阅读入口

| 主题 | 首选入口 | 当前状态 |
| --- | --- | --- |
| 物理资源和参考信号 | [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]] | STANDARD + partial |
| 数据/CSI 资源 | [[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]] | STANDARD + partial |
| 物理层测量 | [[02-标准与参考/3GPP/3GPP TS 38.215｜Physical layer measurements]] | STANDARD + partial；精确版本/报告字段仍需核验 |
| 定位方法和功能实体 | [[02-标准与参考/3GPP/3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]] | STANDARD + partial；方法能力和现场支持仍需核验 |
| 定位协议接口 | [[02-标准与参考/3GPP/3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]]、[[02-标准与参考/3GPP/3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]] | STANDARD + partial；ASN.1/现场互操作仍需核验 |
| 项目事件和质量 | [[05-定位观测量/Observation Event Schema]]、[[05-定位观测量/Quality and Uncertainty]] | PERSONAL_NOTE + NEEDS_VERIFICATION |

## 10. 常见术语误用

1. 将“下行接收时间差”写成 UE 的 DL-TDOA。
2. 将 PRACH timing peak 写成标准 UL-RTOA，而没有 SRS/定位参考和报告上下文。
3. 将网络下发的 TA 当作接收机 ToA。
4. 将单站 RSRP 或相关峰功率当作绝对距离。
5. 将多个站的相近峰按最近邻合并为同一 UE，不保存替代候选。
6. 将具有低残差的项目坐标写成标准定位精度。
7. 将仿真中的真值参考信号能力假定为现场设备已经具备。

## 11. 最小升级验证

- [ ] 每种标准名称都有发射源、测量主体、参考信号和 Release 字段。
- [ ] 项目定制被动观测使用独立字段和 project_status。
- [ ] 下行和上行事件不能仅靠同一载频或相近时间合并。
- [ ] PRS/SRS/DM-RS/PRACH 的资源、端口和方向可回查。
- [ ] 观察值、校准值、协方差和标准报告语义没有共用列。
- [ ] 标准条款未核验时保持 NEEDS_EXTERNAL_REFERENCE。
- [ ] 现场精度和实时性未运行时保持 NEEDS_VERIFICATION。

## 12. 证据与限制

- STANDARD + partial：TS 38.211/38.214 的物理信号、资源网格和数据接口。
- STANDARD + partial：[[02-标准与参考/3GPP/3GPP TS 38.215｜Physical layer measurements]]、[[02-标准与参考/3GPP/3GPP TS 38.305｜Stage 2 functional specification of UE positioning in NG-RAN]]、[[02-标准与参考/3GPP/3GPP TS 38.455｜NR Positioning Protocol A (NRPPa)]] 和 [[02-标准与参考/3GPP/3GPP TS 38.355｜Sidelink Positioning Protocol (SLPP)]] 已提供职责入口；精确测量参考点、完整报告字段和 ASN.1 条件仍需按目标 Release 复核。
- 外部核验入口（2026-09-05 检查）：[ETSI TS 38.215 V17.2.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf)、[ETSI TS 38.305 V18.5.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf)、[ETSI TS 38.455 V18.8.0](https://www.etsi.org/deliver/etsi_ts/138400_138499/138455/18.08.00_60/ts_138455v180800p.pdf)、[ETSI TS 38.355 V18.8.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138355/18.08.00_60/ts_138355v180800p.pdf)；版本仍需与项目 Release 对齐。
- PERSONAL_NOTE：本项目对标准名称、被动观测和事件字段的分离规则。
- HYPOTHESIS + NEEDS_VERIFICATION：在无 LMF/gNB 协作时使用上行参考形成定制被动 UL-TDOA。
- EXPERIMENT + NEEDS_VERIFICATION：现场信号可见性、标准流程互操作、ToA/TDOA/位置精度和实时延迟。

## 13. Related Notes

- [[05-定位观测量/Observation Taxonomy]]
- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[02-PRACH/Timing Estimation]]
- [[01-专题知识/信道估计与均衡/DM-RS]]
- [[01-专题知识/信道估计与均衡/SRS]]
- [[06-TDOA定位/TDOA]]
