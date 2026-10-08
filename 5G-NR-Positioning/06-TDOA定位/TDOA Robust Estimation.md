---
title: TDOA Robust Estimation
aliases:
  - TDOA 鲁棒估计
  - NLOS 与异常站处理
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/tdoa
  - topic/robust-estimation
  - topic/nlos
  - stage/validation
source:
  - "[[06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[06-TDOA定位/TDOA Geometry Quality]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[03-仿真与实验/5G定位/仿真：多站 UL-TDOA 协同定位]]"
related:
  - "[[06-TDOA定位/TDOA]]"
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[06-TDOA定位/TDOA Geometry Quality]]"
  - "[[06-TDOA定位/TDOA Validation Ledger]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
---

# TDOA Robust Estimation

> [!warning] 状态边界
> 鲁棒损失、异常站剔除和 NLOS 补偿只能降低已识别的风险，不能修复错误的 event_id、错误的站点坐标或未校准的时钟。以下策略是项目候选方案，阈值和优劣必须由分层实验决定。

## 1. 为什么需要鲁棒层

TDOA 的几何方程通常假设每个差分来自同一发射事件、同一参考点和可描述的误差模型。实际输入可能含有：

- 首径漏检、最强峰代替首径或多径峰跳变；
- PRACH 碰撞、错误模板或错误 C-RNTI 关联；
- 某站丢样、饱和、重锁或 RF/滤波校准过期；
- NLOS/遮挡导致的结构性时间偏差；
- 某一 pair 的协方差被低估；
- 近共线几何放大某些方向的误差。

鲁棒层的作用是把这些记录变成“降权、替代候选或拒绝”，而不是无条件把所有站塞进一个优化器。

## 2. 三层防线

~~~text
输入前门：事件/资源/校准/物理上界检查
    ↓
观测门：峰质量、协方差、跨站一致性和标准化残差
    ↓
解算门：鲁棒目标、留一站重算、几何质量和边界检查
    ↓
输出：位置候选 + 有效站 + 被拒站 + 原因 + 替代候选
~~~

第一层失败时，不应靠第二层的低残差“挽救”；第三层也不能把结构性错误改写成随机噪声。

## 3. 质量权重的来源

初始权重应来自可追溯字段：

| 来源 | 可用字段 | 注意 |
| --- | --- | --- |
| ToA 不确定度 | 单站标准差、拟合协方差 | 估计方法和样本数必须存在 |
| 峰质量 | peak_to_floor、PSLR、峰宽、多峰标志 | 强峰不等于首径 |
| 校准状态 | clock/RF/filter calibration_id、有效期 | 过期时降级或拒绝 |
| 事件关联 | association_state、候选数、碰撞标志 | 不确定关联不能只靠权重隐藏 |
| 站点健康 | 丢样、饱和、重锁、通道掉线 | 记录原始设备状态 |
| 几何质量 | rank、奇异值、条件数 | 是解算后/布局级信息，不替代信号质量 |

把多个指标压成一个未经定义的 confidence 分数会丢失失败原因。建议保存每项原始指标，再通过版本化规则生成权重。

## 4. 标准化残差门

给定模型残差 $q_k$ 和观测协方差 $\mathbf{\Sigma}_z$，先计算：

$$
\mathbf{u}
=\mathbf{\Sigma}_z^{-1/2}\mathbf{q}.
$$

若只保存对角近似，可逐项使用 $u_k=q_k/\sigma_k$，并标记 covariance_approximate。相关协方差下不能逐项独立解释。

残差门的用途是发现冲突，不是预先宣称某个通用阈值。阈值配置应包含：

~~~yaml
gate_config_id: null
residual_domain: seconds
normalization: covariance_whitened
threshold: null
minimum_station_count: null
max_reweight_rounds: null
policy_version: null
evidence_status: NEEDS_VERIFICATION
~~~

## 5. 鲁棒目标函数候选

将平方损失替换为：

$$
\min_{\mathbf{x}}\sum_k
\rho\!\left(\frac{q_k(\mathbf{x})}{\sigma_k}\right).
$$

候选包括 Huber、Tukey bisquare 或带权截断损失。其共同要求是：

1. 记录具体函数、尺度参数和权重更新方式；
2. 说明尺度来自协方差、MAD、回环还是固定配置；
3. 保留原始残差和最终权重；
4. 把结果标为候选算法，直到 Q 场景完成比较。

鲁棒损失不是自动的 NLOS 校正；它通常只让大残差对位置更新的影响减小。

## 6. 迭代重加权流程

~~~text
用物理/关联门筛出初始站集合
    ↓
用观测协方差形成 W0
    ↓
运行一次 WLS/阻尼 WLS
    ↓
计算白化残差、几何质量和站级诊断
    ↓
按固定规则更新权重或生成剔除候选
    ↓
重新解算并保存每一轮的 station_set、权重、代价和位置
    ↓
达到轮数/稳定/拒绝条件后输出主候选与替代候选
~~~

不能在看到真值误差后再决定保留哪些站；验证时必须预先固定站点策略，避免数据泄漏。

## 7. 留一站重算

对于 $M$ 个站，主解之外可计算每次去掉一个站的替代解：

$$
\widehat{\mathbf{x}}_{(-i)}
=\operatorname{Solve}\bigl(\mathcal{S}\setminus\{i\}\bigr).
$$

若被去掉的是当前参考站，不能只删除一列或一行继续使用旧差分；应回到原始 ToA 向量，选择记录完整的替代参考站，重建差分矩阵和协方差，再运行同一求解策略。

比较位置变化、代价变化、残差变化和几何 rank：

| 现象 | 可能解释 | 动作 |
| --- | --- | --- |
| 去掉某站后残差显著下降 | 该站观测/校准/关联冲突 | 生成剔除候选，回查原始证据 |
| 去掉某站后几何急剧退化 | 该站提供关键几何 | 不应只按残差剔除，标记 trade-off |
| 所有子集都不一致 | 事件或模型整体错误 | 拒绝位置，保留诊断 |
| 子集解相近但协方差很大 | 几何弱或噪声高 | 降级 geometry_poor |

留一站结果是诊断工具，不是自动证明异常站；最终政策必须由实验和设备状态共同决定。

## 8. NLOS 与多径边界

多径会使首径、最强峰和峰簇给出不同时间。NLOS 风险可以由以下证据触发：

- 首径与最强峰差异持续偏大；
- 峰簇结构随窗口/带宽变化；
- 某站与其他站的标准化残差长期同方向；
- 现场遮挡/地图信息与事件一致；
- 回环校准正常而空口观测异常。

“大残差 = NLOS”不是充分条件：错误关联、时钟漂移和坐标错误也会产生同样现象。NLOS 偏差方向、补偿模型和阈值在本项目中都属于 HYPOTHESIS + NEEDS_VERIFICATION。

## 9. 站点选择和替代策略

站点策略应同时考虑信号质量和几何：

1. 先剔除明确 invalid 的观测；
2. 检查剩余站是否仍满足维度和 rank 要求；
3. 在满足几何门的子集里比较质量权重；
4. 保存主站集合、候选集合和未使用站的原因；
5. 若没有任何合格子集，返回 tdoa_rejected。

不能只选“残差最小”的子集，否则会过拟合噪声或错误事件。若尝试 RANSAC 或穷举子集，必须限制候选数量、固定随机种子、记录采样策略，并报告被选中的替代解。

## 10. 事件关联的优先级

鲁棒解算器不能替代上游关联状态机。优先级应是：

~~~text
同一 event_id + 同一方向/资源/参考序列
    > 仅同一帧时隙
    > 仅时间邻近
    > 仅峰形相似
~~~

低级证据只能生成 candidate，不能通过“位置残差很小”反向确认 UE 身份。PRACH 前导、RA-RNTI、RAR、临时 C-RNTI 和 C-RNTI 的协议证据仍由 [[02-PRACH/Random Access Procedure]] 等上游页面负责。

## 11. 拒绝状态建议

| 状态 | 触发 | 是否输出位置 |
| --- | --- | --- |
| candidate | 仍有多个事件/站点组合 | 否，输出候选集合 |
| downweighted | 观测保留但质量降低 | 可输出，必须标记权重 |
| station_excluded | 某站被规则排除 | 可输出，附替代集合 |
| geometry_poor | rank/条件数/布局不达门 | 仅诊断或降级 |
| model_inconsistent | 物理上界或残差整体冲突 | 否 |
| tdoa_rejected | 无合格站集合/关联不闭合 | 否 |
| position_candidate | 数值收敛但未通过质量门 | 仅候选，不作精度结果 |

状态与数值分离；即使 position 为空，也保存每轮残差、站集合和拒绝原因。

## 12. 鲁棒算法伪代码

~~~text
读取已关联且校准的观测
执行符号/单位/物理上界/最小站数检查
若失败：返回拒绝状态和原始证据
初始化站集合 S、权重 W 和候选初值
重复至固定轮数：
    求解受约束的加权几何问题
    计算残差、白化残差、rank、条件数
    按预注册规则更新权重或生成剔除候选
    保存本轮输入、输出和规则版本
比较主解与留一站/替代子集
应用几何和质量门
输出主候选、替代候选、站集合和状态
~~~

## 13. 验证要求

至少要覆盖：

| 场景 | 要验证什么 |
| --- | --- |
| 单径/AWGN | 鲁棒层不会损害闭合基线 |
| 单站固定偏置 | 能发现校准冲突，不把偏置解释为随机噪声 |
| 单站 NLOS/多径 | 首径/最强峰策略和降权行为可区分 |
| 两站冲突 | 站级诊断、留一站和替代解可回放 |
| 多站近共线 | 不用鲁棒权重掩盖几何退化 |
| 错误 event_id | 位置残差不能反向升级关联 |
| 站点丢失/重锁 | 状态和有效站率正确统计 |

所有阈值、权重参数、真值和结果留在 [[06-TDOA定位/TDOA Validation Ledger]]，目前保持空模板。

## 14. 证据与限制

- PERSONAL_NOTE：质量字段、状态和留一站诊断来自 [[05-定位观测量/Quality and Uncertainty]] 与项目多站笔记。
- HYPOTHESIS + NEEDS_VERIFICATION：Huber/Tukey、RANSAC、NLOS 标记和子集选择在当前 NR 被动数据上的收益。
- EXPERIMENT + NEEDS_VERIFICATION：所有阈值、误关联率、剔除率、定位误差和实时开销。
- STANDARD + partial：TS 38.305/38.215 只提供标准定位/测量边界，不规定本项目的鲁棒实现。

## Related Notes

- [[06-TDOA定位/TDOA]]
- [[06-TDOA定位/TDOA Measurement Model]]
- [[06-TDOA定位/TDOA Geometry and Solvers]]
- [[06-TDOA定位/TDOA Geometry Quality]]
- [[06-TDOA定位/TDOA Validation Ledger]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[05-定位观测量/Observation Event Schema]]
- [[07-多站协同/Multi-Station Synchronization]]
