---
title: Current Learning Path
aliases:
  - 当前学习路径
  - 5G NR 被动定位学习路线
type: learning-path
status: seed
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/learning
source:
  - 用户项目阶段要求
  - "[[5G NR Passive Positioning Pipeline]]"
related:
  - "[[项目知识地图]]"
  - "[[01-专题知识/5G定位/第三方 5G 定位项目接手与数据契约]]"
---

# Current Learning Path

> [!abstract] 使用方式
> 现有 `NR_decode_test.m` 的最短学习路线是“PSS/SSS -> SSB/PBCH -> MIB -> CORESET-0 CSS/SI-RNTI -> SIB1”；它与项目目标中的“PRACH -> C-RNTI -> UE-specific PDCCH -> PUSCH/TDOA”是不同支路。先按 P0a 理解已有脚本，再按 P0/P1 推进用户关联和定位主链。`直接相关`只表示代码或实验入口，不表示已经验证通过。

## P0a：先读懂现有下行入口

| 顺序 | 学习目标 | 代码/规范入口 | 可观察验收点 |
|---|---|---|---|
| 1 | 建立样点、FFT bin、资源网格三套坐标 | [[08-MATLAB代码/NR_decode_test 代码学习与协议映射]]、TS 38.211 | 记录 IQ 形状、采样率、FFT、SCS、CP；能解释 `length_frame` 是 10 ms |
| 2 | 用 PSS/SSS 得到同步候选与 PCI | [[01-NR基础/SSB PBCH MIB]]、`PSS_generate`、`SSS_generate`；TS 38.211 | 保存相关峰、`NID1/NID2/PCI` 和峰值置信信息 |
| 3 | 从 SSB/PBCH 到 MIB | [[01-NR基础/SSB PBCH MIB]]、`nrPBCHDecode`、`nrBCHDecode`、`decode_mib`；TS 38.211/38.212/38.331 | 分开检查 BCH CRC、SFN、MIB 位段和 SSB index |
| 4 | 用 MIB 建立 CORESET-0/SearchSpace0 | [[01-NR基础/SSB PBCH MIB]]、`table_seach`；TS 38.213 §13、38.331 | 核对表项、RB/符号、频偏、monitoring occasion 与数组范围 |
| 5 | 解 SI-RNTI DCI 并定位 SIB1 PDSCH | `pdcch_decode*.m`、`decode_dci`、`pdsch_decodehbv1`；TS 38.211/38.212/38.213/38.214 | 记录候选、CRC、DCI 字段、PDSCH RE mask、TB-CRC；不把 SIB1 当 UE 数据 |

当前代码支路的主要静态风险：`decode_mib`/`table_seach` 参数个数不匹配、PDSCH 的 `S/L` 使用方式、固定 Case/采样配置和 `res` 未赋值。以上项目需要验证，不能在路线图中标为“已跑通”。

## P0：当前必须掌握

> [!note] 与 P0a 的关系
> 本表按整个项目目标安排学习顺序；“直接相关”表示项目知识或已有某类代码/实验入口，不表示 `NR_decode_test.m` 直接实现或调用了该步骤，也不代表已通过协议验证。现有脚本覆盖范围以 P0a 和代码导读为准。

| 知识点 | 学习目标 | 前置知识 | 建议阅读顺序 | 与当前项目代码直接相关 |
|---|---|---|---|---|
| [[01-NR基础/NR Frame Slot]] | 能把样点定位到 frame/slot/symbol | OFDM、采样率 | Frame/slot -> symbol -> 时间戳 | 是：所有窗口与事件日志 |
| [[01-NR基础/Numerology]] | 理解 μ、slot 时长、FFT/CP 的联动 | OFDM、离散时间 | Numerology -> SCS -> grid | 是：同步和资源映射 |
| [[01-NR基础/NR TDD]] | 用 D/U/F 配置标注上下行 | Frame/slot、RRC 配置 | slot -> symbol direction -> capture mask | 是：同频上下行监测 |
| [[02-PRACH/PRACH Overview]] | 识别 PRACH 入口和观测边界 | SCS、资源网格 | overview -> configuration -> occasion | 是：第一阶段入口 |
| [[02-PRACH/PRACH Configuration]] | 从配置得到格式、根序列、occasion | Numerology、RRC/SIB | config -> occasion -> preamble | 是：检测参数 |
| [[02-PRACH/PRACH Occasion]] | 把配置展开为合法时频 RO 和响应窗口 | PRACH Configuration、TDD | RO -> detection window -> RA-RNTI | 是：检测窗口 |
| [[02-PRACH/PRACH Preamble]] | 由根序列和循环移位解释前导索引 | ZC、Cyclic Shift | root -> shift -> preamble index | 是：相关模板 |
| [[02-PRACH/Zadoff Chu Sequence]] | 理解恒包络序列与相关性质 | 复数序列、相关 | ZC root -> local reference | 是：本地参考生成 |
| [[02-PRACH/Cyclic Shift]] | 将前导索引映射到循环移位和零相关区 | ZC、RO | shift table -> candidate preamble | 是：前导枚举 |
| [[02-PRACH/PRACH Detection]] | 在合法 RO 中检测峰、碰撞和粗 ToA | 前导、采样率、CFO | correlation -> peak list -> event | 是：第一阶段核心 |
| [[02-PRACH/Timing Estimation]] | 估计整数/亚采样时延并记录不确定度 | PRACH Detection、采样时钟 | peak -> fractional delay -> timing field | 是：定位前置 |
| [[02-PRACH/RA-RNTI]] | 由 occasion 形成响应上下文候选 | PRACH occasion | occasion -> RA-RNTI -> RAR | 是：RAR 监测 |
| [[02-PRACH/RAR]] | 解析 RAPID、TA、UL grant、临时标识 | RA-RNTI、PDSCH | RAR -> Msg3 | 是：C-RNTI 关联前置 |
| [[02-PRACH/Msg3]] | 理解 UL grant 指向的 Msg3 和 C-RNTI MAC CE | RAR、PUSCH | RAR -> Msg3 -> contention | 是：关联证据 |
| [[02-PRACH/Random Access Procedure]] | 用状态机区分 2-step/4-step、CBRA/CFRA | 全部 PRACH 子节点 | Msg1 -> Msg2 -> Msg3 -> Msg4 | 是：端到端第一阶段 |
| [[02-PRACH/C-RNTI]] | 只在足够证据下确认 UE 标识 | RAR、Msg3、争用解决 | candidate -> confirmed -> track | 是：PDCCH 输入 |

## P1：控制和数据

| 知识点 | 学习目标 | 前置知识 | 建议阅读顺序 | 与当前项目代码直接相关 |
|---|---|---|---|---|
| [[03-PDCCH/PDCCH Implementation Contract]] | 统一候选记录、状态机和资源/编码快照 | C-RNTI、资源网格 | config -> candidate -> DCI -> positioning | 是：实现总契约 |
| [[03-PDCCH/PDCCH Overview]] | 了解控制信道在 CORESET/搜索空间中的位置 | C-RNTI、资源网格 | CORESET -> search space -> candidates | 是：第二阶段入口 |
| [[03-PDCCH/CORESET]] | 生成 PDCCH 频域/时域候选资源 | NR grid、RRC | CORESET -> CCE/REG | 是：资源解映射 |
| [[03-PDCCH/Search Space]] | 枚举公共/UE 专用监测候选 | CORESET、RNTI | search space -> aggregation -> candidates | 是：盲搜边界 |
| [[03-PDCCH/CCE REG]] | 理解 CCE/REG 交织和聚合等级 | CORESET | REG -> CCE -> candidate | 是：候选索引 |
| [[03-PDCCH/DCI]] | 从 DCI 字段得到 PDSCH/PUSCH 调度 | PDCCH、38.212 | DCI format -> CRC/RNTI -> grant | 是：资源快照 |
| [[03-PDCCH/RNTI]] | 区分 RA-RNTI、TC-RNTI、C-RNTI 等用途 | Random Access | RNTI 类型 -> CRC 掩码 | 是：候选判决 |
| [[03-PDCCH/PDCCH Blind Decoding]] | 记录 CRC、字段合法性和误检/漏检 | 全部 PDCCH 节点 | candidate loop -> DCI -> data | 是：核心算法 |
| [[04-PDSCH/PDSCH]] | 由 DCI 驱动数据 RE、DM-RS、译码和 HARQ | DCI、DM-RS、DL-SCH | resource snapshot -> coding snapshot -> extraction | 是：目标 UE 资源提取 |
| [[04-PDSCH/UE Resource Extraction]] | 将合法快照转换为单 UE RE/样点掩码并分离定位支路 | PDSCH、OFDM、采样校准 | mask -> waveform window -> observation | 是：单用户截取接口 |
| [[01-专题知识/信道估计与均衡/DM-RS|DM-RS]] | 用解调参考信号估计目标传输的等效信道 | PDSCH/PUSCH 资源、资源网格 | DM-RS mapping -> LS/LMMSE -> equalization | 是：PDSCH/PUSCH 解调与单用户提取 |

## P2：时间观测基础

| 知识点 | 学习目标 | 前置知识 | 建议阅读顺序 | 与当前项目代码直接相关 |
|---|---|---|---|---|
| [[05-定位观测量/Timing Observation]] | 定义 ToA/RToA、峰策略和校准字段 | PRACH/PUSCH、采样时钟 | event -> peak -> calibrated time | 是：定位支路 |
| ToA | 区分原始到达样点与校准后的时间 | Timing Observation | first/strongest/cluster 对照 | 是：日志字段 |
| TDOA | 用站间时间差消除共同发射时刻 | ToA、站间同步 | pairwise difference -> residual | 是：第三阶段输入 |
| TDOA Measurement Model | 固定差分矩阵、符号、协方差和钟差项 | Timing Observation、Event Schema | ToA vector -> D matrix -> covariance | 是：解算输入契约 |
| TDOA Geometry and Solvers | 用 Jacobian/WLS/约束得到位置候选 | TDOA Measurement Model | model -> initialization -> solver -> diagnostics | 是：几何解算核心 |
| TDOA Robust Estimation | 处理坏站、多径/NLOS 和替代站集 | Geometry and Solvers、Quality | residual -> reweight -> leave-one-out | 是：质量与异常支路 |
| TDOA Geometry Quality | 判断 rank、条件数、GDOP-like 和空间退化 | Geometry and Solvers | Jacobian -> singular values -> geometry gate | 是：位置可信度诊断 |
| TDOA Validation Ledger | 以 T0-T9 分层验证并记录结果 | 全部 TDOA 页面、采数清单 | synthetic -> loopback -> replay -> field | 是：验收与复现 |
| [[07-多站协同/Multi-Station Synchronization]] | 组织时基、链路、关联和融合四层 | 采数实验、Timing Observation | clock -> delay -> association -> fusion | 是：多站前置 |
| [[07-多站协同/Clock Offset and Drift]] | 估计站间固定偏置、采样率偏差和漂移 | 时间戳、PPS/PTP | offset -> drift -> correction | 是：误差预算 |
| [[07-多站协同/RF and Digital Delay Calibration]] | 分离参考面、RF/数字链路和群时延 | 处理链、公共源 | reference plane -> delay model | 是：链路校准 |
| [[07-多站协同/Cross-Station Event Association]] | 证明不同站观测属于同一物理事件 | Event Schema、PRACH/PUSCH | candidate -> matched -> usable | 是：事件关联 |
| [[07-多站协同/Multi-Station Observation Fusion]] | 形成站序、D 矩阵和协方差输入包 | Timing Observation、TDOA model | ToA -> D -> covariance | 是：TDOA 输入 |
| [[07-多站协同/Synchronization Validation Ledger]] | 分层验证同步、校准、关联和降级 | 采数清单、TDOA ledger | loopback -> replay -> field | 是：验收与复现 |

## P3：标准定位扩展

| 知识点 | 学习目标 | 前置知识 | 建议阅读顺序 | 与当前项目代码直接相关 |
|---|---|---|---|---|
| NR Positioning | 区分标准定位流程与本项目被动方案 | TDOA、3GPP 架构 | 38.305 -> 38.455 | 间接：术语和边界 |
| PRS | 了解下行定位参考信号的标准用途 | PDSCH/资源网格 | 38.211 -> 38.305 | 暂无：需确认设备可见性 |
| SRS | 了解上行探测信号及其定位潜力 | PUSCH、DM-RS | 38.211 -> 38.214 | 候选：依采集能力 |
| UL-TDOA | 了解标准上行到达时差接口 | ToA/TDOA | 38.305/38.215 | 是：项目定制主线需对照 |
| DL-TDOA | 了解下行参考与接收机角色 | PRS、同步 | 38.305 | 否/待确认：固定站观测边界 |
| Multi-RTT | 了解往返时延与被动监测差异 | ToA、时钟 | 38.305 | 否：暂不作为第一版主线 |
| AoA/AoD | 了解角度观测与阵列约束 | MIMO、阵列校准 | 38.215/38.305 | 否：后续扩展 |
| LPP / SLPP / NRPPa | 区分 UE/侧链/NG-RAN 与定位服务器的协议边界 | RRC、定位架构 | 38.355 -> 38.455（跨代 LPP 对照 36.355/37.355） | 否：仅作标准背景 |

## 推荐总顺序

真实工程代码导读：[[08-MATLAB代码/NR_decode_test 代码学习与协议映射]]。先按该页核对入口参数、变量维度和时频坐标，再按下面的协议顺序阅读；代码中的硬编码和未验证项不能直接当作网络配置。

```text
[[08-MATLAB代码/NR_decode_test 代码学习与协议映射]]
  -> [[01-NR基础/NR Frame Slot]]
  -> [[01-NR基础/Numerology]] -> [[01-NR基础/SCS]]
  -> [[01-NR基础/PRB RE Resource Grid]] -> [[01-NR基础/NR TDD]]
  -> [[02-PRACH/PRACH Overview]] -> [[02-PRACH/PRACH Configuration]]
  -> [[02-PRACH/PRACH Occasion]] -> [[02-PRACH/PRACH Detection]]
  -> [[02-PRACH/RA-RNTI]] -> [[02-PRACH/RAR]] -> [[02-PRACH/Msg3]]
  -> [[02-PRACH/Random Access Procedure]] -> [[02-PRACH/C-RNTI]]
  -> [[03-PDCCH/PDCCH Implementation Contract]]
  -> [[03-PDCCH/CORESET]] -> [[03-PDCCH/Search Space]]
  -> [[03-PDCCH/CCE REG]] -> [[03-PDCCH/DCI]]
  -> [[03-PDCCH/PDCCH Blind Decoding]] -> [[04-PDSCH/PDSCH]]
  -> [[05-定位观测量/Timing Observation]]
  -> [[07-多站协同/Clock Offset and Drift]]
  -> [[07-多站协同/RF and Digital Delay Calibration]]
  -> [[07-多站协同/Cross-Station Event Association]]
  -> [[07-多站协同/Multi-Station Observation Fusion]]
  -> [[07-多站协同/Synchronization Validation Ledger]]
  -> [[06-TDOA定位/TDOA Measurement Model]]
  -> [[06-TDOA定位/TDOA Geometry and Solvers]]
  -> [[06-TDOA定位/TDOA Robust Estimation]]
  -> [[06-TDOA定位/TDOA Geometry Quality]]
  -> [[06-TDOA定位/TDOA Validation Ledger]]
```

## 当前最大缺口

- 本项目 MATLAB 工程、版本和入口脚本尚未进入该 Vault。
- 当前网络的 2-step/4-step、CBRA/CFRA、PRACH 配置和 TDD pattern 未锁定。
- 未确认 RAR、Msg3、Msg4 是否在第三方设备的 IQ 窗口中可见。
- 未有真实多站公共时钟、RF 延迟、滤波群时延和采样偏差记录。

## Related Notes

- [[5G NR Passive Positioning Pipeline]]
- [[项目知识地图]]
- [[00-导航与入口/5G 定位与 TDOA｜MOC]]

## P2 补充：观测接口强化

在进入 [[06-TDOA定位/TDOA]] 前，按下面顺序补齐观测层：

| 知识点 | 学习目标 | 产物 |
| --- | --- | --- |
| [[05-定位观测量/Observation Taxonomy]] | 区分时间、频率、功率、空间、信道、身份和几何观测 | 信号选择矩阵和术语边界 |
| [[05-定位观测量/Standard Positioning Observables]] | 区分标准定位方法、标准信号和项目被动观测 | 发射源/测量主体/参考信号对照 |
| [[05-定位观测量/Timing Observation]] | 把参考点、样点、峰、校准和 TDoA 组织成单站时间观测 | ToA/RToA 字段和峰策略 |
| [[05-定位观测量/Observation Event Schema]] | 让单站结果可以跨站关联并回查原始证据 | event/observation/calibration schema |
| [[05-定位观测量/Quality and Uncertainty]] | 将偏置、漂移、随机误差和结构性风险分开 | 质量等级、协方差和 Q0-Q10 矩阵 |

这四页的状态仍受真实配置、设备校准和实验运行约束；阅读完成不等于定位精度已验证。
