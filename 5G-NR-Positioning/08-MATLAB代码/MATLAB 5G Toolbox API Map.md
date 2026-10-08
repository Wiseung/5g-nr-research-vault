---
title: MATLAB 5G Toolbox API Map
aliases:
  - MATLAB 5G Toolbox 函数地图
  - NR MATLAB API 入口
type: implementation-map
status: seed
created: 2026-09-04
tags:
  - project/5g-nr-positioning
  - topic/matlab
  - topic/5g-toolbox
source:
  - "[[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]"
  - "[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]"
  - MathWorks 官方文档（待本机 Release 核验）
related:
  - "[[NR_decode_test 代码学习与协议映射]]"
  - "[[02-PRACH/PRACH Detection]]"
  - "[[03-PDCCH/PDCCH Blind Decoding]]"
  - "[[04-PDSCH/PDSCH]]"
  - "[[09-采数实验/Capture Experiment Checklist]]"
---

# MATLAB 5G Toolbox API Map

## 1. 一句话定义

本页把项目链路中可能用到的 MATLAB/5G Toolbox 函数按输入输出边界归类，作为核验清单，不把文档示例当作本项目已运行结果。

## 2. 为什么项目需要它

项目已有 PRACH、PDCCH/PDSCH 仿真骨架，但缺少真实工程版本和 API 输入维度记录；统一地图可以减少函数名记忆错误和跨 Release 误用。

## 3. 它位于整个 5G 空口链路的什么位置

它横跨同步、PRACH、控制、数据、信道估计和测量支路，连接概念笔记与 `08-MATLAB代码` 实际脚本。

## 4. 输入

MATLAB 版本、5G Toolbox 版本、carrier/BWP/PRACH/PDCCH/PDSCH 配置、IQ 波形、资源网格和测试向量。

## 5. 输出

版本化 API 清单、每个函数的输入/输出维度、最小调用示例、已验证/未验证状态和对应实验编号。

## 6. 关键参数

Release、对象属性、采样率、FFT/CP、数据类型（实数/复数/LLR）、天线/端口/层维度、RNTI、索引基准和随机种子。

## 7. 时域位置

波形生成、OFDM 解调和 PRACH/PDCCH/PDSCH API 的时间窗口必须绑定 frame/slot/symbol；函数返回的样点偏移要与 [[01-NR基础/NR Frame Slot]] 对齐。

## 8. 频域位置

资源网格 API 的索引可能是 BWP 局部或载波相对索引；记录 `grid_index` 与 `absolute_subcarrier` 的转换，不能直接用数组下标推断射频频点。

## 9. 数学原理

API 只是算法实现接口，底层仍需满足：资源解映射 $\rightarrow$ 信道估计 $\rightarrow$ 均衡 $\rightarrow$ 软解调 $\rightarrow$ 38.212 逆处理。每个边界应保存中间向量和维度。

## 10. 3GPP 对应规范

函数对应的标准边界主要涉及 TS 38.211/38.212/38.213/38.214；MATLAB 函数签名不是 3GPP 规范内容。精确条款、Release 和 API 文档版本均标记 `NEEDS_EXTERNAL_REFERENCE`，需在本机核验。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

| 链路 | API 线索 | 核验状态 |
|---|---|---|
| PRACH | `nrPRACHConfig`、`nrPRACH`、`nrPRACHDetect` | `NEEDS_EXTERNAL_REFERENCE` |
| 同步/资源网格 | `nrOFDMInfo`、`nrOFDMModulate`、`nrOFDMDemodulate`、`nrCarrierConfig` | `NEEDS_EXTERNAL_REFERENCE` |
| PDCCH/DCI | `nrPDCCHSpace`、`nrPDCCHDecode`、`nrDCIDecode` | `NEEDS_EXTERNAL_REFERENCE` |
| 资源/估计 | `nrExtractResources`、`nrChannelEstimate`、`nrEqualizeMMSE` | `NEEDS_EXTERNAL_REFERENCE` |
| PDSCH/DL-SCH | `nrPDSCHIndices`、`nrPDSCHDMRSIndices`、`nrPDSCHDMRS`、`nrPDSCHDecode`、`nrDLSCHDecoder` | `NEEDS_EXTERNAL_REFERENCE` |
| 测量 | 基础 `xcorr`、`findpeaks`、`resample`；NR 专用测时函数需核验 | 部分可用，整体待核验 |

## 12. 本项目中的用途

先用 API 构造可控正例和负例，再把接口边界迁移到第三方设备 IQ；每次运行同时记录版本、配置、输入维度、输出维度和状态，不以函数返回非空作为协议关联证明。

## 13. 常见误区

- 把旧 Release 的对象属性直接用于新 Release。
- 只复制官方示例而不核对采样率、天线和端口维度。
- 把 `nrPRACHDetect` 的 strongest peak 当成完整多用户检测器。
- 把 PDCCH CRC 通过当成 C-RNTI 已确认。

## 14. 与相似概念的区别

- API 参考是实现入口，标准条款是协议依据，实验日志是本项目证据。
- 仿真波形是受控输入，第三方设备 IQ 还包含时钟、射频、量化和未知配置误差。
- 函数存在不等于本机许可证、版本或输入契约满足。

## 15. 代码实现注意事项

为每个函数建立最小 smoke test；用 `ver`、`help`/`doc` 和 `which` 记录版本与路径；保存中间索引/LLR；避免把机器绝对路径和凭据写入笔记；脚本与参数分离。

## 16. 待实验验证的问题

- 本机 MATLAB/5G Toolbox Release 下各 API 的实际签名和返回维度。
- PRACH 多实例、短/长前导和 CFO/时延输入行为。
- PDCCH 候选循环、RNTI 参数和 DCI 格式长度的边界。
- PDSCH DM-RS、层/端口和 `nrDLSCHDecoder` 的闭环。

## 17. Related Notes

- [[NR_decode_test 代码学习与协议映射]]
- [[02-PRACH/PRACH Detection]]
- [[03-PDCCH/PDCCH Blind Decoding]]
- [[04-PDSCH/PDSCH]]
- [[09-采数实验/Capture Experiment Checklist]]
- [[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]
- [[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]

## 证据与状态

- `PERSONAL_NOTE`：已有 Vault 的 API 线索整理。
- `NEEDS_EXTERNAL_REFERENCE`：本机 Release、签名和真实运行结果尚未核对。
