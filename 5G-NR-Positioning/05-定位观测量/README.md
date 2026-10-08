---
title: 05-定位观测量
type: directory-index
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/measurement
  - stage/positioning
source:
  - "[[01-专题知识/5G定位/单用户时频截取与定位观测量]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]"
  - "[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]]"
  - "[[02-标准与参考/3GPP/3GPP TR 38.901｜Channel model]]"
related:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Observation Taxonomy]]"
  - "[[05-定位观测量/Standard Positioning Observables]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[06-TDOA定位/TDOA]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
---

# 05-定位观测量

> [!abstract] 目录边界
> 本目录定义“从已定位的 NR 资源得到什么测量、测量如何携带证据、何时可以进入 TDOA/位置解算”。它不是 3GPP 定位协议的完整实现，也不是把一个相关峰或一个最终坐标包装成精度结论。每个数值都要能反查到 <code>capture_id</code>、<code>config_id</code>、资源/方向快照、算法版本、校准版本和质量状态。

## 1. 这层解决什么问题

上游已经回答了“在哪个资源上看到什么信号”：

~~~text
Raw IQ
  ↓
frame/slot/symbol + BWP/PRB/RE + D/U/F
  ↓
PRACH/PDCCH/PDSCH/PUSCH/DM-RS/SRS 候选
  ↓
本目录：原始特征 → 校准观测 → 质量/不确定度 → 可用于融合的接口
  ↓
TDOA/几何解算/位置质量
~~~

本层必须同时保留四种东西：

1. **原始证据**：样点、频域 RE、相关轨迹、峰列表、复数参考和时间戳。
2. **估计结果**：ToA、CFO、功率、相位、角度或信道特征。
3. **校准结果**：时钟、RF、线缆、滤波、数字链和坐标系修正。
4. **可用性判定**：质量等级、协方差、失败原因和是否允许下游消费。

只保存第 2 项会失去诊断能力；只保存第 4 项则无法重算。

## 2. 目录地图

| 笔记 | 负责的问题 | 主要输出 | 当前边界 |
| --- | --- | --- | --- |
| [[05-定位观测量/Timing Observation]] | ToA/RToA/TDOA 前的时间观测接口 | 样点坐标、峰策略、校正时间、协方差入口 | 标准测量参考点和现场校准仍需核验 |
| [[05-定位观测量/Observation Taxonomy]] | 观测量分类、信号选择和术语边界 | 时间/频率/空间/功率/质量/身份/几何矩阵 | 精确 38.215/38.305 条款保留外部核验标记 |
| [[05-定位观测量/Standard Positioning Observables]] | 标准定位方法与被动观测的发射源/测量主体边界 | PRS、SRS、UL/DL-TDOA、Multi-RTT、AoA 对照 | 精确条款、配置和设备支持仍需核验 |
| [[05-定位观测量/Observation Event Schema]] | 统一事件和观测数据契约 | YAML/字段字典/状态机/关联键 | 这是项目 schema，不是 3GPP ASN.1 |
| [[05-定位观测量/Quality and Uncertainty]] | 质量门、误差预算和不确定度传播 | 质量等级、协方差、验证矩阵 | 尚无现场测量结果，不填经验精度 |

PRACH 的相关器和亚采样细节仍归 [[02-PRACH/Timing Estimation]]；本目录负责把不同信号的输出统一成可审计接口，而不复制 PRACH 专用算法。

## 3. 观测量分层

| 层 | 示例 | 能回答的问题 | 不能单独回答的问题 |
| --- | --- | --- | --- |
| L0 原始采样 | <code>iq[n]</code>、时间戳、丢样计数 | 实际捕获了什么？ | 传播时间是多少？ |
| L1 处理特征 | 相关轨迹、峰、FFT、功率、相位差 | 哪些候选可被检测？ | 候选是否属于目标 UE？ |
| L2 单站观测 | <code>toa_raw</code>、CFO、RSRP、角度候选 | 某站如何量化该事件？ | 跨站差分是否已校准？ |
| L3 校准观测 | <code>toa_corrected</code>、RToA、校准协方差 | 能否与其他站比较？ | 位置是否唯一且可信？ |
| L4 派生解 | TDOA、GDOP、残差、位置 | 几何约束和解算结果是什么？ | 算法是否在未验证场景下泛化？ |

L1 到 L4 必须携带上游 ID，不允许把派生结果写回覆盖原始结果。校准失败时可以保留 L2，但 L3 为空或降级；位置解算器不得把缺失校准静默当作零偏置。

## 4. 观测量总表

| 类别 | 代表字段 | 典型来源 | 主要混淆 |
| --- | --- | --- | --- |
| 时间 | ToA、RToA、TDOA、峰宽、首径/最大峰 | PRACH、PUSCH DM-RS、SRS、定位参考 | TA 不是接收机 ToA；样点网格不是物理分辨率 |
| 频率 | CFO、残余 CFO、频率斜率、Doppler 候选 | 参考序列、DM-RS、SRS、跨时刻相位 | 本振频偏和传播多普勒不能直接合并 |
| 功率 | 峰功率、噪声底、RSSI/RSRP/SNR/SINR 候选 | 相关器、RE、参考信号 | 窗口、归一化和分母不同会改变数值 |
| 空间 | 阵列相位差、AoA/AoD 候选、波束索引 | 多天线 DM-RS/SRS/CSI-RS | 未校准阵列相位不能当绝对角度 |
| 信道 | 路径数下界、延迟扩展、频率选择性、相关性 | 参考信号和时频网格 | 峰数不是用户数，模型参数不是现场测量 |
| 质量 | PSLR、峰宽、残差、EVM/NMSE、有效站率 | L1/L2/L3 处理链 | 质量分数不能替代原始测量 |
| 身份/上下文 | <code>event_id</code>、C-RNTI 状态、资源快照 | PRACH/RA/PDCCH/DCI | CRC pass 不等于用户确认 |
| 几何/解算 | TDOA 残差、GDOP、位置协方差 | 多站融合 | 单次坐标不等于定位精度 |

每个类别都要记录单位、参考点、估计器、配置版本和证据等级。没有这些元数据，字段名相同也不能横向比较。

## 5. 信号选择原则

| 信号/片段 | 方向 | 可先得到的观测 | 进入 UE 定位前的必要条件 |
| --- | --- | --- | --- |
| PRACH 前导 | UL | 接入事件、粗 ToA、峰簇、功率 | RO/根序列/循环移位已确认；碰撞和多径已标记 |
| PUSCH DM-RS | UL | 当前传输 ToA、参考质量、频偏候选 | DCI/RRC 资源、端口/层和用户关联闭合 |
| SRS/定位 SRS | UL | 跨站时间、频率和空间观测候选 | SRS 配置、序列和标准测量口径已核验 |
| PDSCH DM-RS | DL | 下行同步/质量或发射源观测 | 不能把固定站的下行差分直接解释为 UE 位置 |
| PDCCH DM-RS | DL | 控制候选质量和时频辅助 | CORESET/搜索空间/候选已知；不是 UE 上行定位信号 |
| CSI-RS/PRS | DL | CSI、波束或标准定位参考候选 | 配置、测量主体和标准流程需单独确认 |
| 未知业务片段 | UL/DL | 能量、盲相关候选 | 先有身份/资源/参考证据；否则只作低级特征 |

“适合作为观测”不等于“已经可定位”。优先级通常是：已知上行参考 > 已知上行数据重构 > 未知业务盲相关；最终选择必须由碰撞、多径、带宽、同步和设备可见性实验决定。

## 6. 统一键和数据流

~~~text
capture_id
  └─ config_id
      └─ event_id
          ├─ signal_context / resource_snapshot
          ├─ raw_feature (峰、轨迹、RE、IQ 引用)
          ├─ station_observation (单站值)
          ├─ calibration_snapshot
          ├─ quality_and_uncertainty
          └─ derived_solution (TDOA/位置)
~~~

- <code>capture_id</code> 标识不可变原始文件或连续采集段。
- <code>config_id</code> 标识 numerology、BWP、TDD、资源和软件解释版本。
- <code>event_id</code> 标识同一物理事件的候选关联；它不应只由“相近样点”生成。
- <code>observation_id</code> 标识单站、单信号、单估计器的一次输出。
- <code>calibration_id</code> 标识校准条件、参考面和有效时间范围。

关联键和数值字段的完整定义见 [[05-定位观测量/Observation Event Schema]]。

## 7. 单位与空值约定

| 字段类 | 统一单位/格式 | 缺失表示 |
| --- | --- | --- |
| 时间 | 秒（SI）；同时保留浮点样点 | null 或 unknown，不写 0 |
| 频率 | Hz；相对采样偏差用 ppm | 未估计为 null，不等同于零 |
| 功率 | dB/dBm 或线性功率，必须带口径 | null 并记录 power_reference_unknown |
| 角度 | 弧度或度，必须声明坐标系 | null 并记录阵列未校准 |
| 索引 | 明确 0/1 基、局部/绝对、是否模周期 | unknown，不能靠数组默认值 |
| 协方差 | 与观测向量同单位平方，注明轴顺序 | null，不得伪造对角矩阵 |

外部标准字段和项目字段不要共用一个未说明的名字。例如 <code>ta_command</code>、<code>toa_raw_seconds</code>、<code>ul_rtoa_standard</code> 和 <code>toa_corrected_seconds</code> 必须分列。

## 8. 进入下游的最小质量门

~~~text
资源/方向闭合？
  ├─ 否 → partial_observation
  └─ 是
      ↓
参考或模板可回放？
  ├─ 否 → feature_only
  └─ 是
      ↓
峰/估计在有效窗口且残差可接受？
  ├─ 否 → toa_unreliable / frequency_unreliable
  └─ 是
      ↓
站间时钟、RF、滤波校准可追溯？
  ├─ 否 → calibrated_pending
  └─ 是
      ↓
同一 event_id、协方差和几何检查通过？
  ├─ 否 → tdoa_rejected
  └─ 是 → tdoa_usable
~~~

这里的“可接受”是项目门限，而不是默认的 3GPP 合规阈值；门限必须在 [[05-定位观测量/Quality and Uncertainty]] 中绑定实验版本。

## 9. 证据分层

- STANDARD + partial：[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]] 的资源网格/参考信号职责、[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]] 的数据/CSI 接口、[[02-标准与参考/3GPP/3GPP TR 38.901｜Channel model]] 的传播模型边界。
- PERSONAL_NOTE：本目录对项目数据流、字段和术语的组织。
- HYPOTHESIS + NEEDS_VERIFICATION：用 PRACH/PUSCH/SRS 参考在无 LMF 协作条件下形成定制被动 UL-TOA/RTOA/TDOA。
- EXPERIMENT + NEEDS_VERIFICATION：所有检测率、ToA RMSE、TDOA RMSE、定位误差、覆盖率和实时延迟。
- NEEDS_EXTERNAL_REFERENCE：38.215/38.305 的精确测量参考点、表格、Release 差异以及 MATLAB API 版本行为。

标准定位方法（PRS、UL-TDOA、DL-TDOA、Multi-RTT）与本项目的被动监听方案必须在报告和代码字段中分开。

## 10. 阅读与验收顺序

1. 先读 [[05-定位观测量/Observation Taxonomy]]，确定术语和信号角色。
2. 读 [[05-定位观测量/Standard Positioning Observables]]，确定标准名称和项目名称的使用边界。
3. 再读 [[05-定位观测量/Timing Observation]]，建立时间坐标和估计接口。
4. 用 [[05-定位观测量/Observation Event Schema]] 固定日志结构和状态机。
5. 用 [[05-定位观测量/Quality and Uncertainty]] 设计质量门和验证矩阵。
6. 回到 [[02-PRACH/Timing Estimation]]、[[04-PDSCH/UE Resource Extraction]] 和 [[07-多站协同/Multi-Station Synchronization]] 实现上游输入。
7. 最后把通过门的观测交给 [[06-TDOA定位/TDOA]]。

## 11. 目录验收清单

- [ ] 每条观测可由 <code>observation_id → event_id → capture_id</code> 反查原始证据。
- [ ] <code>config_id</code>、<code>calibration_id</code> 和算法版本均有有效时间范围。
- [ ] ToA/RToA/TDOA、TA、CFO、Doppler 和 AoA 没有共用含义不明的字段。
- [ ] 所有功率/质量指标记录测量窗口、归一化和噪声/干扰口径。
- [ ] 每站保留 raw 值、校正项、协方差和降级原因。
- [ ] 事件关联区分同一 UE 重传、同一 RO 碰撞和不同站点观测。
- [ ] TDOA 输入通过同一参考、带宽/滤波配置和几何质量检查。
- [ ] 未运行的实验、未锁定的 Release 和未核验 API 保持显式状态。

## 12. Related Notes

- [[05-定位观测量/Timing Observation]]
- [[05-定位观测量/Observation Taxonomy]]
- [[05-定位观测量/Standard Positioning Observables]]
- [[05-定位观测量/Observation Event Schema]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[02-PRACH/Timing Estimation]]
- [[04-PDSCH/UE Resource Extraction]]
- [[06-TDOA定位/TDOA]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[09-采数实验/Capture Experiment Checklist]]
