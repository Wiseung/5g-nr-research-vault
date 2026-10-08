---
title: Capture Experiment Checklist
aliases:
  - 采数实验检查表
  - IQ 回放验收清单
type: experiment-protocol
status: seed
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/iq-capture
  - topic/reproducibility
source:
  - "[[01-专题知识/5G定位/第三方 5G 定位项目接手与数据契约]]"
  - "[[03-仿真与实验/5G定位/仿真：NR 被动监测从 PRACH 到 UL-TDOA 全流程]]"
related:
  - "[[08-MATLAB代码/MATLAB 5G Toolbox API Map]]"
  - "[[05-定位观测量/Timing Observation]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[06-TDOA定位/TDOA Validation Ledger]]"
---

# Capture Experiment Checklist

## 1. 一句话定义

本清单规定一次可回放、可追溯的第三方 IQ 采数实验应保存的配置、原始文件、事件和校准证据。

## 2. 为什么项目需要它

没有统一采数契约，就无法区分 PRACH 检测失败、配置错误、PDCCH 漏检、资源提取错误和多站时基误差，也无法重现实验。

## 3. 它位于整个 5G 空口链路的什么位置

它贯穿 Raw IQ -> NR 同步 -> PRACH/RA -> C-RNTI -> PDCCH/PDSCH -> Timing Observation -> TDOA，既是输入协议也是验收出口。

## 4. 输入

设备/站点信息、中心频率与采样率、天线通道、时钟源、PPS/PTP/触发、SCS/BWP/TDD/PRACH/CORESET 配置、已知正负样本和运行版本。

## 5. 输出

不可变原始 IQ、配置快照、事件表、处理版本、质量标志、校准记录、结果摘要和失败分类。

## 6. 关键参数

`capture_id`、`station_id`、时间戳定义、I/Q 数据类型、采样率、中心频率、帧号起点、丢样/溢出计数、温度、软件/硬件版本、随机种子。

## 7. 时域位置

记录捕获起止时间、frame/slot/symbol 对齐、触发延迟和窗口裁剪；所有事件保存相对样点与绝对时间，不用口头时间替代。

## 8. 频域位置

记录载波带宽、BWP、Point A、SCS、PRB 掩码、下变频/抽取/滤波参数；“120.88 兆”等口述值必须确认其物理含义。

## 9. 数学原理

把每个处理阶段看成带版本的映射：

$$
\mathrm{event}=f(\mathrm{IQ},\mathrm{config},\mathrm{software},\mathrm{calibration}).
$$

若任一输入未记录，输出不能被视为可复现实验事实；观测误差应按时钟、RF、数字链路和算法项分解。

## 10. 3GPP 对应规范

配置和事件字段分别涉及 TS 38.211/213/214/321/331；定位测量涉及 TS 38.215/305/455。具体 Release、条款和设备私有字段需核对，状态为 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

可用 `matfile`/`save` 保存结构化快照，`ver` 记录工具箱版本，`readmatrix`/二进制读取器导入设备数据；NR API 入口见 [[08-MATLAB代码/MATLAB 5G Toolbox API Map]]，均需本机验证。

## 12. 本项目中的用途

第一阶段先用单站正例、负例和碰撞样本验收 PRACH/RA；第二阶段保存候选级 PDCCH/DCI 和资源快照；第三阶段将同一 `event_id` 的多站 ToA/TDOA 与校准 ID 绑定。

## 13. 常见误区

- 只保存最终图/坐标，不保存原始 IQ 和配置。
- 用缺失字段的 0 表示已校准或未丢样。
- 把仿真成功样本当作设备现场成功。
- 不区分同一用户重传、不同用户碰撞和不同站点事件。

## 14. 与相似概念的区别

- 采数清单是实验输入/证据契约，不是协议规范本身。
- 配置快照描述“应如何解”，事件表描述“实际观察到什么”。
- 质量标志描述可用性，不替代原始测量值。

## 15. 代码实现注意事项

原始文件只读保存并以哈希/大小校验完整性；处理脚本写新输出目录；每次运行记录 Git/脚本版本（若有）、MATLAB 版本、参数 JSON/YAML 和失败日志；敏感设备信息脱敏。

## 16. 待实验验证的问题

- 设备 IQ 格式、通道顺序、时间戳和丢样计数的真实定义。
- PRACH/RAR/Msg3/Msg4 在捕获窗口中的可见性。
- PDCCH 配置来源（SIB1/RRC/设备元数据）和 C-RNTI 正负样本。
- 多站公共时钟、RF 延迟、滤波群时延和采样率漂移记录方式。

## 17. Related Notes

- [[08-MATLAB代码/MATLAB 5G Toolbox API Map]]
- [[05-定位观测量/Timing Observation]]
- [[07-多站协同/Multi-Station Synchronization]]
- [[01-专题知识/5G定位/第三方 5G 定位项目接手与数据契约]]
- [[03-仿真与实验/5G定位/仿真：PRACH 检测与 RA 事件关联]]

## 证据与状态

- `PERSONAL_NOTE`：用户项目字段契约和既有仿真页。
- `EXPERIMENT + NEEDS_VERIFICATION`：真实设备格式和现场结果尚未接入。

## 18. 定位观测数据包

每次采数除原始 IQ 和协议配置外，还应按以下顺序保存：

1. [[05-定位观测量/Observation Event Schema]] 定义的 capture/config/event/observation 记录。
2. [[05-定位观测量/Timing Observation]] 的参考点、样点索引、峰轨迹和 raw/corrected 时间。
3. [[05-定位观测量/Quality and Uncertainty]] 的质量等级、校准 ID、协方差和拒绝原因。
4. [[05-定位观测量/Observation Taxonomy]] 要求的信号角色、功率/频率/空间口径。

没有真值或真实运行时，结果字段保持 null，实验状态保持 EXPERIMENT + NEEDS_VERIFICATION。

## 19. TDOA 解算回放入口

采数包准备好后，按以下顺序交给解算层：

1. [[06-TDOA定位/TDOA Measurement Model]]：确认站序、参考点、差分矩阵和协方差。
2. [[06-TDOA定位/TDOA Geometry and Solvers]]：运行无鲁棒基线并保存诊断。
3. [[06-TDOA定位/TDOA Geometry Quality]]：检查站点布局和局部可观测性。
4. [[06-TDOA定位/TDOA Robust Estimation]]：按预注册策略处理异常站。
5. [[06-TDOA定位/TDOA Validation Ledger]]：回写场景、指标和失败分类。
