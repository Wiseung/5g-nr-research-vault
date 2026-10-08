---
title: 07-多站协同
type: directory-index
status: partial
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/synchronization
  - topic/calibration
  - topic/multi-station
source:
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
related:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
---

# 07-多站协同

> [!abstract] 目录边界
> 本目录解决“多个接收站是否在同一个可校准的时间和事件坐标系中”这一前置问题。它不替代 [[06-TDOA定位/README]] 的几何解算，也不把标准定位协议流程写成第三方被动设备已经实现的能力。

## 1. 目录地图

| 页面 | 负责的问题 | 主要输出 |
| --- | --- | --- |
| [[07-多站协同/Multi-Station Synchronization]] | 总体架构、层级和进入门 | 多站协同总览与最小闭环 |
| [[07-多站协同/Clock Offset and Drift]] | 固定钟差、采样率偏差、漂移和重锁 | `clock_model`、有效区间和残差 |
| [[07-多站协同/RF and Digital Delay Calibration]] | 天线/RF/线缆/数字链路延迟和参考面 | `delay_model`、校准表和不确定度 |
| [[07-多站协同/Cross-Station Event Association]] | 跨站同一事件判定、碰撞和错配 | `event_id` 候选、证据和状态 |
| [[07-多站协同/Multi-Station Observation Fusion]] | 将单站观测组成 TDOA 输入包 | 站点顺序、差分矩阵、协方差 |
| [[07-多站协同/Synchronization Validation Ledger]] | 回环、漂移、关联和端到端验收 | `run_id`、指标和失败分类 |

## 2. 推荐阅读顺序

~~~text
总览
  -> Clock Offset and Drift
  -> RF and Digital Delay Calibration
  -> Cross-Station Event Association
  -> Multi-Station Observation Fusion
  -> Synchronization Validation Ledger
  -> [[06-TDOA定位/TDOA Measurement Model]]
~~~

先读“时间基准”和“链路延迟”，再读“事件关联”和“观测融合”。若事件尚未证明是同一物理事件，不能跳过关联页直接计算 TDOA。

## 3. 最小输入契约

- `station_id`、站点坐标、天线参考点和坐标系。
- `capture_id`、原始 IQ、实际采样率、中心频率、有效带宽和处理链版本。
- 时钟源、PPS/PTP/触发状态、锁定/重锁时间和外部时间戳。
- 天线、线缆、RF、ADC、数字下变频、抽取和滤波配置。
- 上游 `config_id`、信号角色、资源快照、`event_id` 候选和峰轨迹。

缺失字段用 `null`/`unknown` 和状态表达；不能用零表示“没有偏置”或“已经校准”。

## 4. 输出契约

本目录输出的记录至少能回查：

~~~json
station_id: null
event_id: null
calibration_id: null
clock_model_id: null
reference_station_id: null
station_order: []
toa_raw_seconds: null
toa_corrected_seconds: null
tdoa_seconds: null
covariance_ref: null
sync_state: unknown
association_state: unknown
quality_reasons: []
~~~

`tdoa_seconds` 非空不代表可定位；只有 `sync_state`、`association_state`、协方差和下游几何门均通过，才可进入 `tdoa_usable`。

## 5. 层级和状态

~~~text
metadata_known
  -> clock_observable
  -> delay_calibrated
  -> cross_station_matched
  -> covariance_ready
  -> tdoa_usable
~~~

任一阶段失败都要保留前一阶段证据，并写明失败原因。`clock_observable`、`delay_calibrated` 和 `cross_station_matched` 不是同义词。

## 6. 与 05/06/09 层的边界

| 上游/下游 | 07 层使用什么 | 不重复负责什么 |
| --- | --- | --- |
| 05-定位观测量 | raw/corrected ToA、参考点、质量和 event schema | 单站峰估计器的全部实现细节 |
| 06-TDOA定位 | 站序、TDOA、协方差和同步状态 | 双曲线求解器、几何优化和鲁棒解算 |
| 09-采数实验 | 设备元数据、文件和运行版本 | 现场设备格式的最终定义 |
| 标准定位页 | 术语/角色边界 | 标准合规实现或现场精度结论 |

## 7. 目录验收清单

- [ ] 每个站点有稳定 `station_id`、坐标系和参考面。
- [ ] 原始时间戳、样点索引和实际采样率可回放。
- [ ] 时钟偏置、漂移和重锁区间与校准版本绑定。
- [ ] RF/数字延迟按频率、带宽、滤波配置记录。
- [ ] event_id 的候选、替代配对和拒绝原因可审计。
- [ ] TDOA 的参考站、站点顺序、D 矩阵和协方差齐全。
- [ ] 所有阈值和结果区分 `EXPERIMENT` 与 `NEEDS_VERIFICATION`。

## 8. 当前缺口

- 真实设备的硬件时间戳和 PPS/PTP 语义未确认。
- 尚无跨频率/带宽/温度的 RF/数字延迟校准表。
- 尚无多站同一 UE 事件的正例、碰撞和重传回放。
- 尚无本项目运行得到的同步残差、TDOA RMSE 或位置误差。

## 证据与状态

- `PERSONAL_NOTE`：目录结构和数据契约承接既有项目笔记。
- `STANDARD + partial`：TS 38.215/38.305 的标准测量/定位角色仅作边界参考。
- `EXPERIMENT + NEEDS_VERIFICATION`：所有校准数值、阈值和现场结果待运行。
