---
title: TDOA Geometry and Solvers
aliases:
  - TDOA 几何解算
  - 双曲线定位求解器
type: atomic
status: partial
created: 2026-09-05
tags:
  - project/5g-nr-positioning
  - topic/tdoa
  - topic/geometric-solver
  - topic/wls
  - stage/positioning
source:
  - "[[06-TDOA定位/TDOA Measurement Model]]"
  - "[[01-专题知识/5G定位/多站 UL-TDOA 定位与同步]]"
  - "[[05-定位观测量/Quality and Uncertainty]]"
  - "[[03-仿真与实验/5G定位/仿真：多站 UL-TDOA 协同定位]]"
related:
  - "[[06-TDOA定位/TDOA]]"
  - "[[06-TDOA定位/TDOA Geometry Quality]]"
  - "[[06-TDOA定位/TDOA Robust Estimation]]"
  - "[[06-TDOA定位/TDOA Validation Ledger]]"
  - "[[05-定位观测量/Observation Event Schema]]"
  - "[[07-多站协同/Multi-Station Synchronization]]"
---

# TDOA Geometry and Solvers

> [!abstract] 解算边界
> 本页定义从已通过关联、校准和质量门的 TDOA 向量到位置候选的数值接口。WLS、Gauss-Newton、LM、网格初值和约束优化都是项目候选实现；没有真实数据或合成真值运行时，不给出精度或收敛率结论。

## 1. 输入、输出和状态

### 1.1 输入

| 类别 | 字段 | 要求 |
| --- | --- | --- |
| 几何 | station_ids、坐标、coordinate_frame、dimension | 坐标同系、参考面明确 |
| 观测 | tdoa_seconds、station_order、reference_station_id | 差分方向与矩阵可回放 |
| 不确定度 | tdoa_covariance 或每方程标准差 | 与观测顺序一致 |
| 传播 | propagation_speed、model_id | 单位和假设显式记录 |
| 约束 | 搜索区域、地面/高度/速度边界 | 没有边界时写 unknown |
| 证据 | event_id、observation_ids、calibration_ids | 能回溯上游记录 |

### 1.2 输出

解算器必须同时返回数值和诊断：

~~~json
solution_id: null
event_id: null
status: unknown
estimate:
  position: null
  coordinate_frame: null
  dimension: null
  local_covariance: null
input:
  station_ids_used: []
  reference_station_id: null
  tdoa_seconds: []
  covariance_seconds2: []
solver:
  name: null
  version: null
  initialization: null
  constraints: null
  iterations: null
  termination_reason: null
diagnostics:
  residual_seconds: []
  standardized_residual: []
  weighted_cost: null
  jacobian_rank: null
  condition_number: null
  geometry_state: null
  outlier_stations: []
evidence_status: NEEDS_VERIFICATION
~~~

position 为空时仍应保留输入、残差和拒绝原因；不要通过删除失败记录制造“全是成功”的数据集。

## 2. 几何观测函数

设站点 $i$ 与参考站 $r$ 的坐标分别为 $\mathbf{s}_i$,$\mathbf{s}_r$，位置状态为 $\mathbf{x}$，则：

$$
h_{i,r}(\mathbf{x})
 = \frac{\|\mathbf{x}-\mathbf{s}_i\|
       -\|\mathbf{x}-\mathbf{s}_r\|}{c}.
$$

观测向量 $\mathbf{z}$ 由同一 event_id 的 TDOA 组成：

$$
\mathbf{z}=\mathbf{h}(\mathbf{x})+\boldsymbol{\varepsilon}.
$$

定义残差方向为“模型减观测”：

$$
\mathbf{q}(\mathbf{x})=\mathbf{h}(\mathbf{x})-\mathbf{z}.
$$

所有页面和实现都要沿用这个方向，避免把残差反号后仍使用同一 Jacobian 和门限。

## 3. Jacobian 与局部线性化

对 $r_i=\|\mathbf{x}-\mathbf{s}_i\|\neq 0$，第 $i$ 行的导数为：

$$
\mathbf{J}_{i,:}(\mathbf{x})
 = \frac{1}{c}
   \left(
   \frac{(\mathbf{x}-\mathbf{s}_i)^T}{r_i}
   -\frac{(\mathbf{x}-\mathbf{s}_r)^T}{r_r}
   \right).
$$

在当前迭代点 $\mathbf{x}_k$ 附近：

$$
\mathbf{q}(\mathbf{x}_k+\delta)
\approx
\mathbf{q}(\mathbf{x}_k)+\mathbf{J}_k\delta.
$$

若实现以米为单位的距离差残差，则应把时间观测乘以 $c$，并删除 Jacobian 中的 $1/c$。时间残差和距离残差不能混用权重或停止阈值。

## 4. 加权最小二乘基线

给定 TDOA 协方差 $\mathbf{\Sigma}_z$，令 $\mathbf{W}=\mathbf{\Sigma}_z^{-1}$（必要时使用有记录的广义逆），目标函数为：

$$
\min_{\mathbf{x}\in\mathcal{X}}
J(\mathbf{x})
=\mathbf{q}(\mathbf{x})^T\mathbf{W}\mathbf{q}(\mathbf{x}).
$$

其中 $\mathcal{X}$ 是可选的坐标/高度/区域约束。无可靠协方差时可以用质量等级生成对角 baseline，但结果必须标记 covariance_approximate，而不是宣称统计最优。若输入来自全 pair 差分，$\mathbf{\Sigma}_z$ 可能秩亏；应改用独立差分基、SVD/广义逆或在原始 ToA 域求解，并记录有效秩，不能直接调用普通逆矩阵。

### 4.1 Gauss-Newton 更新

在当前点求解：

$$
\delta_k
=-(\mathbf{J}_k^T\mathbf{W}\mathbf{J}_k)^{-1}
  \mathbf{J}_k^T\mathbf{W}\mathbf{q}_k,
\qquad
\mathbf{x}_{k+1}=\mathbf{x}_k+\delta_k.
$$

矩阵接近奇异时不要直接求逆；用 QR/SVD 或带阻尼的线性解，并记录 rank、奇异值和阻尼参数。

### 4.2 Levenberg-Marquardt 候选

可用阻尼形式：

$$
(\mathbf{J}^T\mathbf{W}\mathbf{J}
 +\lambda\mathbf{R})\delta
=-\mathbf{J}^T\mathbf{W}\mathbf{q},
$$

其中 $\lambda\ge0$，$\mathbf R$ 可取单位阵或对角尺度矩阵。这里的阻尼方案是工程候选，不代表本项目已经比较过 LM 与 Gauss-Newton。

## 5. 初值策略

非线性双曲线目标可能有多解或局部极小值，初值要成为结果的一部分。可记录以下候选：

| 初值 | 适用 | 风险 |
| --- | --- | --- |
| 站点质心/加权质心 | 快速 baseline | 远离真实区域时收敛差 |
| 搜索区域粗网格 | 有地图边界、维度低 | 网格分辨率与计算量耦合 |
| 多起点随机/拉丁超立方 | 检查多解和敏感性 | 需要固定种子和停止规则 |
| 线性化闭式候选 | 作为快速 warm start | 线性化误差、额外未知量和退化 |
| 上一事件位置 | 连续轨迹场景 | 可能把错误轨迹锁住 |

“最接近真值的初值”只能用于诊断上界，不能作为现场性能的默认初值；验证报告应区分 oracle initialization 和 operational initialization。

## 6. 约束和可行域

可以把先验写成：

$$
\mathbf{x}\in\mathcal{X}
=\{\mathbf{x}: \mathbf{l}\le\mathbf{x}\le\mathbf{u},
\;g_j(\mathbf{x})\le0\}.
$$

常见约束包括地面高度、已知楼层、测试区域边界和速度连续性。每个约束都要记录来源：

- 物理/测量约束：来自站点坐标、天线高度或场景定义；
- 项目先验：人为设定的搜索区域；
- 评估辅助：只用于诊断，不应混入无约束基线。

若约束把错误 TDOA 强行压进区域，残差可能仍然很大；报告必须同时给出无约束/有约束状态和边界活跃情况。

## 7. 2D、3D 和未知钟差

### 7.1 二维

已知高度并在平面上求解时，位置状态有两个自由度。三站通常提供两个独立差分方程，但双曲线交点可能不唯一，必须用可行域、额外站或多时刻信息检查。不要把“方程数等于未知数”写成必然唯一。

### 7.2 三维

三维位置有三个自由度，至少需要足够的独立空间约束；四站在理想已同步模型下可形成三个独立差分，但共面/退化几何仍可能无法稳定估计高度。站点数量是必要性提示，不是充分性保证。

### 7.3 联合估计站间钟差

若每个站有未知偏置 $b_i$，可以扩展状态：

$$
\boldsymbol{\theta}
=[\mathbf{x}^T,\;b_2-b_r,\ldots,b_M-b_r]^T.
$$

单事件同时估计位置和偏置通常不可辨识或高度相关；需要已知位置校准、多事件共享参数、锚定站或先验协方差。联合模型必须输出参数 rank 和 gauge 约定，不能把任意一个坐标偏移误称为钟差估计。

## 8. 迭代流程伪代码

~~~text
读取 event_id、站点坐标、TDOA、协方差和可行域
    ↓
检查站点顺序、符号、单位、物理上界和最小数量
    ↓
生成一个或多个记录完整的初值
    ↓
对每个初值：
    计算 h(x)、残差 q(x)、Jacobian J(x)
    计算 rank/条件数并选择 QR/SVD/阻尼线性步
    求解步长，执行可行域投影或约束子问题
    评估代价是否下降；必要时调整阻尼/步长
    按预先固定的步长、梯度、残差和迭代上限停止
    保存每次迭代摘要和终止原因
比较候选：代价、残差、几何状态、边界活跃和初始化敏感性
输出最佳候选及其替代候选，不删除失败候选
~~~

停止条件至少包括：

1. 步长范数阈值；
2. 代价相对变化阈值；
3. 梯度或正规方程残差阈值；
4. 最大迭代/时间预算；
5. 数值异常（NaN、rank 下降、不可行）。

阈值是实验配置的一部分，不得在结果表中只写“收敛”。

## 9. 解算后诊断

对最终 $\widehat{\mathbf{x}}$ 计算：

$$
\mathbf{q}_{final}
=\mathbf{h}(\widehat{\mathbf{x}})-\mathbf{z}.
$$

至少保存：

| 诊断 | 作用 |
| --- | --- |
| 每方程残差 | 定位具体站/差分冲突 |
| 标准化残差 | 与观测不确定度比较 |
| 加权代价 | 比较同一配置下的候选 |
| Jacobian rank | 检查局部可观测性 |
| 奇异值/条件数 | 暴露近共线或高度退化 |
| 约束活跃集 | 判断结果是否被边界夹住 |
| 多起点分散度 | 检查多解/局部极小值 |
| 有效站集合 | 回到异常站和质量账本 |

低残差只说明模型与当前输入相容，不能证明 event_id、站点坐标或发射源身份正确。

## 10. 局部协方差和误差椭圆

在线性化和模型正确的前提下，可用：

$$
\mathbf{\Sigma}_x
\approx
(\mathbf{J}^T\mathbf{W}\mathbf{J})^{-1}.
$$

这不是全局置信区域；当约束活跃、非线性强、站点被剔除或存在多解时，应用重复仿真、bootstrap 或网格轮廓辅助诊断，并标记其方法和范围。二维误差椭圆的轴、方向和置信约定必须与坐标系及覆盖率定义一起记录。

## 11. MATLAB / Python 实现边界

基础 MATLAB 可用矩阵运算、svd、qr、pinv 以及 lsqnonlin/fmincon 类数值工具构造原型；Python 可用 NumPy/SciPy 等等价工具。具体函数签名、版本、约束行为和运行性能属于 NEEDS_EXTERNAL_REFERENCE，不能因为函数名称存在就声称本机已验证。

NR 5G Toolbox 负责波形/资源/参考信号接口，不自动提供本项目的站点几何、事件关联、RF 校准或 TDOA 质量门。解算器应接收 [[05-定位观测量/Observation Event Schema]] 的结构化记录，而不是直接读取未经审计的数组。

## 12. 实现验收

- [ ] 模型残差、观测符号和 Jacobian 使用同一约定。
- [ ] 时间/距离单位、传播速度和坐标单位在输入中显式记录。
- [ ] WLS 权重来自协方差或明确的近似配置。
- [ ] 线性代数退化使用 QR/SVD/阻尼并保存诊断。
- [ ] 初值、多起点、约束和停止条件可重放。
- [ ] 失败候选、边界解和异常站不被静默删除。
- [ ] 局部协方差不被表述为无条件的全局精度。

## 13. 证据与限制

- PERSONAL_NOTE：本页的几何函数、Jacobian、WLS 和求解器输出契约来自项目 TDOA 方程整理。
- STANDARD + partial：标准定位方法的角色和测量边界见 TS 38.305/38.215 入口；本页数值求解不是标准协议实现。
- HYPOTHESIS + NEEDS_VERIFICATION：多起点、联合钟差、约束和鲁棒解算在当前设备/信道中的相对收益。
- EXPERIMENT + NEEDS_VERIFICATION：任何收敛率、位置误差、协方差覆盖率和运行时数值。

## Related Notes

- [[06-TDOA定位/TDOA]]
- [[06-TDOA定位/TDOA Measurement Model]]
- [[06-TDOA定位/TDOA Robust Estimation]]
- [[06-TDOA定位/TDOA Geometry Quality]]
- [[06-TDOA定位/TDOA Validation Ledger]]
- [[05-定位观测量/Quality and Uncertainty]]
- [[05-定位观测量/Observation Event Schema]]
- [[07-多站协同/Multi-Station Synchronization]]
