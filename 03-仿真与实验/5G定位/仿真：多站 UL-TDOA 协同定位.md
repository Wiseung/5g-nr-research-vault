---
title: 仿真：多站 UL-TDOA 协同定位
aliases:
  - 仿真 5G 多站 TDOA
  - 仿真 UL-RTOA 定位
type: experiment
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/定位
  - topic/tdoa
  - topic/同步
  - stage/simulation
  - stage/verification
  - metric/toa
  - metric/position-error
  - evidence/3gpp
source:
  - 3GPP TS 38.305
  - 3GPP TS 38.215
  - 3GPP TR 38.901
  - 多站 UL-TDOA 定位与同步
simulation:
  - 仿真：多站 UL-TDOA 协同定位
related:
  - "[[仿真：PRACH 检测与 RA 事件关联]]"
  - "[[仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜]]"
  - "[[单用户时频截取与定位观测量]]"
  - "[[多站 UL-TDOA 定位与同步]]"
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA Measurement Model]]"
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA Geometry and Solvers]]"
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA Robust Estimation]]"
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA Geometry Quality]]"
  - "[[5G-NR-Positioning/06-TDOA定位/TDOA Validation Ledger]]"
---

# 仿真：多站 UL-TDOA 协同定位

> [!abstract] 实验性质
> 本页是 `EXPERIMENT + NEEDS_VERIFICATION` 的仿真设计。它先验证已知单用户上行波形在多站、理想公共时钟下的 TDOA 几何闭环，再逐一加入采样时钟漂移、RF/滤波群时延、CFO、多径、NLOS、碰撞和站点剔除；没有真实采集结果前不填写定位精度。

## 1. 实验问题

1. 多站能否把同一个 PRACH/PUSCH/DM-RS 事件稳定识别为同一 `event_id`？
2. 在已知传播延迟下，ToA/TDOA 估计误差如何传递到位置误差？
3. 三站二维和四站冗余在不同几何/GDOP、同步和多径条件下的差异是什么？
4. 采用首径、最大峰或峰簇拟合时，哪种策略在当前信道条件下更稳健？

## 2. 方法边界

本实验模拟的是多个固定接收站测量 UE 上行的定制被动 UL-TOA/RTOA/TDOA。它不模拟 LMF/gNB 的完整定位信令，也不把固定站对下行的时差解释成 UE 坐标。标准 UL-TDOA、DL-TDOA 与项目方案的差异见 [[多站 UL-TDOA 定位与同步#8. 标准流程与项目实现的分离]]。

## 3. 分层验收门

| 门 | 场景 | 通过条件 |
|---|---|---|
| T0 | 单径、理想公共时钟、已知延迟 | 每站 ToA 与真值闭合，几何解收敛 |
| T1 | AWGN 扫描 | ToA/TDOA/位置 RMSE 和样本量完整 |
| T2 | 固定 RF/滤波延迟 | 校准前后偏差方向可解释 |
| T3 | 采样率偏差和时钟漂移 | 随时间的 TDOA 漂移可量化 |
| T4 | TDL/CDL、多径/NLOS | 首径/最大峰/峰簇策略可比较 |
| T5 | 3/4 站、不同几何 | GDOP、残差和异常站处理可复现 |
| T6 | 由 PRACH/PUSCH 关联的真实事件键 | 碰撞/误关联不会静默进入解算 |

## 4. 场景与参数账本

| 参数 | 基线 | 扫描/记录 |
|---|---|---|
| UE 真值位置 | 场景内固定点/轨迹 | 坐标系、速度、时间戳 |
| 站点 | 三站二维；四站冗余 | 坐标、天线高度、参考站、几何/GDOP |
| 中心频率 | `120.88e6 Hz` 仅作候选 | 确认载频/带宽/采样率含义 |
| 有效带宽 | `B_eff` 待定 | 不把 PRACH 带宽等同整段采集带宽 |
| 采样率 | `F_s` 待定 | 每站相同/不同、重采样策略 |
| 上行信号 | PRACH、PUSCH DM-RS、SRS 或重构片段 | 事件长度、已知序列和资源快照 |
| 真值延迟 | `τ_i=true` | 浮点延迟、整数/亚采样生成方法 |
| 时钟 | 理想公共基准 | 固定偏置、漂移、丢锁、重同步 |
| 硬件延迟 | 0 或校准表 | RF、天线、线缆、数字滤波、群时延 |
| 载频误差 | 0、低、中、高 | CFO、相位连续性、补偿状态 |
| 信道 | AWGN、TDL/CDL、自定义 NLOS | 路径延迟/功率/速度/随机种子 |
| 峰策略 | first/strongest/cluster | 选择规则和置信度 |
| 解算器 | WLS/鲁棒 WLS | 初值、权重、残差门限、停止条件 |

## 5. 观测模型

对站点 $i$：

$$
t_i=t_0+\frac{\|\mathbf{x}-\mathbf{s}_i\|}{c}+b_i+d_i+e_i.
$$

以站 1 为参考：

$$
\Delta t_{i1}
=\frac{\|\mathbf{x}-\mathbf{s}_i\|-\|\mathbf{x}-\mathbf{s}_1\|}{c}
+(b_i-b_1)+(d_i-d_1)+(e_i-e_1).
$$

仿真必须同时保存 `true_delay`、`raw_toa`、`corrected_toa` 和 `tdoa_used`，否则无法区分传播误差与校准误差。

若使用 PRACH 产生事件，还要单独保存 timing advance/首径真值；它们属于协议或传播观测量，不应被当作已知的 UE 发射时刻。

## 6. 处理流程

```text
生成 UE 上行参考波形和真值事件
    ↓
按站点几何、传播延迟、CFO、时钟和多径生成接收 I/Q
    ↓
各站执行相同的同步、滤波、资源截取和相关器
    ↓
输出全峰轨迹、ToA、首径/最大峰策略和质量
    ↓
应用 RF/滤波/采样时钟校准
    ↓
按 event_id 形成 TDOA 向量及协方差
    ↓
WLS/鲁棒 WLS 双曲线解算
    ↓
残差、GDOP、异常站和位置置信区间
```

各站必须共享同一波形真值和事件标签；若仿真中把每站独立生成不同随机符号，却仍声称是同一用户事件，结果没有意义。

## 7. 首径与峰策略

至少比较三种策略：

- `first`：在门限和峰簇约束下选择最早可靠路径。
- `strongest`：选择最大相关峰，作为易实现但可能有 NLOS 偏差的基线。
- `cluster`：对峰簇拟合公共到达结构，并输出不确定度。

参考 TS 38.215 的 UL-RTOA/first detected path 测量边界时，应把“标准参考点”和本项目数字相关峰明确分开。不能把 strongest peak 的误差隐藏在“TOA 已校准”字段里。

## 8. 解算与质量控制

定义：

$$
g_i(\mathbf{x})=\|\mathbf{x}-\mathbf{s}_i\|-\|\mathbf{x}-\mathbf{s}_1\|-c\,\Delta t_{i1}.
$$

先最小化：

$$
J(\mathbf{x})=\mathbf{g}(\mathbf{x})^T\mathbf{W}\mathbf{g}(\mathbf{x}),
$$

再根据标准化残差、ToA 质量和 GDOP 进行鲁棒重加权或剔除。以同一参考站形成的 TDOA 共享测量误差，权重矩阵 $\mathbf{W}$ 不应默认是对角矩阵；先记录原始 ToA 协方差，再决定简化近似。

## 9. 指标

| 层级 | 指标 |
|---|---|
| 检测 | event recall、误关联率、碰撞漏检率 |
| ToA | bias、RMSE、标准差、95/99 分位数、首径偏差 |
| TDOA | pairwise bias/RMSE、协方差一致性、有效站比例 |
| 定位 | 2D/3D position RMSE、95% 分位数、最大误差 |
| 几何 | GDOP、条件数、残差、异常站数 |
| 实时性 | 每站处理延迟、融合延迟、吞吐量、丢帧率 |
| 鲁棒性 | CFO/时钟/群时延/NLOS 扰动下的退化曲线 |

## 10. 结果表模板

| 场景 | 站数 | 几何/GDOP | SNR | 时钟误差 | RF/滤波校准 | 信道 | 峰策略 | ToA RMSE | TDOA RMSE | 位置 RMSE | 95%误差 | 有效站率 |
|---|---:|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|
| T0 | 3 |  |  | 0 | ideal | 单径 | first |  |  |  |  |  |
| T1 | 3 |  |  | 0 | ideal | AWGN | first |  |  |  |  |  |
| T2 | 3/4 |  |  |  | calibrated | 单径 | strongest |  |  |  |  |  |
| T3 | 3/4 |  |  |  | drift | 单径 | first |  |  |  |  |  |
| T4 | 3/4 |  |  |  | calibrated | TDL/CDL | cluster |  |  |  |  |  |
| T5 | 3/4 |  |  |  | calibrated | NLOS |  |  |  |  |  |  |

## 11. 故障注入矩阵

| 注入 | 预期观察 | 定位到的层 |
|---|---|---|
| 单站固定延迟偏置 | 位置向相关方向系统偏移 | RF/滤波校准 |
| 采样率 ppm 偏差 | TDOA 随捕获时长漂移 | 时钟/重采样 |
| CFO 未补偿 | 相关峰下降/展宽 | 载频同步 |
| 首径被强峰遮盖 | strongest 与 first 分歧 | 多径/峰策略 |
| NLOS 路径 | 单站正偏差、残差升高 | 传播/异常站 |
| PRACH 碰撞 | event_id 不唯一 | 用户关联 |
| 参考站丢失 | TDOA 协方差/方程变化 | 融合器 |
| 近共线站点 | GDOP 急剧增大 | 几何设计 |
| 滤波器通带不同 | 频率相关 TDOA 偏差 | 数字前端 |

## 12. 可复现记录

- MATLAB/Python/工具版本：
- 代码提交号：
- 站点坐标和坐标系：
- 公共时钟/漂移模型：
- RF、天线、线缆和滤波群时延表：
- `B_eff`、采样率和中心频率确认记录：
- 传播信道和随机种子：
- 峰策略、门限、插值方法：
- 解算初值、权重和停止规则：
- 原始 ToA/TDOA/位置结果路径：

## 证据与出处

- `STANDARD + partial`： [ETSI TS 38.305 V18.5.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf)，核对 DL/UL-TDOA 方法和标准流程；项目方案不等同 LMF/gNB 合规实现。
- `STANDARD + partial`： [ETSI TS 38.215 V17.2.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf)，核对 UL-RTOA、参考点和 first detected path 的测量边界。
- `STANDARD + partial`：[[3GPP TR 38.901｜Channel model]]，用于 TDL/CDL、多径、多普勒和同步误差建模。
- `PERSONAL_NOTE`：[[多站 UL-TDOA 定位与同步]]、[[单用户时频截取与定位观测量]]、[[仿真：PRACH 检测与 RA 事件关联]]。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页所有数值栏为空，尚无实际运行结果。

## 当前状态

尚未运行。先完成 T0/T1 并保存每站原始 ToA，再进入时钟、校准和多径实验；不允许只保留最终定位坐标。

## 13. 与 TDOA 解算层的对应

本实验页负责生成场景和结果，几何层负责定义输入与诊断：

- [[5G-NR-Positioning/06-TDOA定位/TDOA Measurement Model]]：固定差分方向、矩阵和协方差。
- [[5G-NR-Positioning/06-TDOA定位/TDOA Geometry and Solvers]]：执行 WLS/约束求解并记录迭代。
- [[5G-NR-Positioning/06-TDOA定位/TDOA Robust Estimation]]：比较降权、剔除和替代站集。
- [[5G-NR-Positioning/06-TDOA定位/TDOA Geometry Quality]]：报告 rank、条件数和布局退化。
- [[5G-NR-Positioning/06-TDOA定位/TDOA Validation Ledger]]：登记 T0-T9 的运行和结果。

本页的空结果表仍保持 EXPERIMENT + NEEDS_VERIFICATION，不因新增链接而变成已运行结论。

## 14. 伪代码与 MATLAB/Python T0-T1 示例

以下示例直接在 ToA 测量层加入独立高斯误差，完成 T0/T1 的几何与 WLS 基线；它不生成 PRACH/PUSCH I/Q，也不模拟 TDL/CDL、CFO 或首径检测。时钟和硬件延迟数组默认为零，可按 T2 注入并使用独立校准值补偿。代码运行结果应填入结果表，不应把示例参数当成项目实测精度。

### 伪代码

```text
设置站点几何、UE 真值、ToA 噪声和固定随机种子
构造参考站差分矩阵 D，并从 ToA 协方差推导 TDOA 协方差
重复 Monte Carlo:
    计算几何真值距离和每站 ToA
    注入站时钟偏置、硬件延迟和 ToA 噪声
    用独立校准值修正 ToA，保存 raw/corrected 两套值
    生成参考站 TDOA 与距离差观测
    用完整协方差白化残差/Jacobian，迭代 WLS 到收敛
    记录 ToA/TDOA/位置误差和几何质量
汇总 RMSE、GDOP、条件数和有效样本数
```

### MATLAB

```matlab
rng(7);
c = 299792458;
stations = [0, 0; 1000, 0; 0, 1000; 1000, 1000];
xTrue = [420, 350];
nStation = size(stations, 1);
nTrial = 300;
t0 = 0.025;
sigmaToa = 20e-9 * ones(nStation, 1);
clockBias = zeros(nStation, 1);    % T0/T1 理想同步；T2/T3 在此注入
hardwareDelay = zeros(nStation, 1);
clockBiasCal = zeros(nStation, 1); % 校准估计值，不应直接复用真值
hardwareDelayCal = zeros(nStation, 1);

D = [-ones(nStation - 1, 1), eye(nStation - 1)];
covTdoaRange = c^2 * D * diag(sigmaToa.^2) * D.';
L = chol(covTdoaRange, "lower");
toaError = zeros(nTrial, nStation);
tdoaError = zeros(nTrial, nStation - 1);
toaRawHistory = zeros(nTrial, nStation);
toaCorrectedHistory = zeros(nTrial, nStation);
tdoaSecondsHistory = zeros(nTrial, nStation - 1);
rangeDiffHistory = zeros(nTrial, nStation - 1);
positionError = zeros(nTrial, 1);
gdopValues = zeros(nTrial, 1);

for trial = 1:nTrial
    trueRange = sqrt(sum((stations - xTrue).^2, 2));
    trueToa = t0 + trueRange / c;
    toaRaw = trueToa + clockBias + hardwareDelay + ...
        sigmaToa .* randn(nStation, 1);
    toaCorrected = toaRaw - clockBiasCal - hardwareDelayCal;

    rangeDiffObs = c * (D * toaCorrected);
    tdoaSecondsHistory(trial, :) = (D * toaCorrected).';
    rangeDiffHistory(trial, :) = rangeDiffObs.';
    rangeDiffTrue = trueRange(2:end) - trueRange(1);
    xHat = solveTdoaWls(stations, rangeDiffObs, L, mean(stations, 1));

    toaError(trial, :) = (toaCorrected - trueToa).';
    tdoaError(trial, :) = (rangeDiffObs - rangeDiffTrue).';
    toaRawHistory(trial, :) = toaRaw.';
    toaCorrectedHistory(trial, :) = toaCorrected.';
    positionError(trial) = norm(xHat - xTrue);
    gdopValues(trial) = tdoaGdop(stations, xHat);
end

fprintf("ToA RMSE = %.3f ns\n", 1e9 * sqrt(mean(toaError(:).^2)));
fprintf("TDOA distance-difference RMSE = %.3f m\n", ...
    sqrt(mean(tdoaError(:).^2)));
sortedPositionError = sort(positionError);
p95Index = max(1, ceil(0.95 * nTrial)); % nearest-rank P95
fprintf("位置 RMSE = %.3f m，位置 P95 = %.3f m\n", ...
    sqrt(mean(positionError.^2)), sortedPositionError(p95Index));
fprintf("平均 GDOP = %.3f，有效样本 = %d/%d\n", ...
    mean(gdopValues(isfinite(gdopValues))), ...
    nnz(isfinite(gdopValues)), nTrial);

function x = solveTdoaWls(stations, rangeDiffObs, L, x)
for iteration = 1:50
    ranges = sqrt(sum((stations - x).^2, 2));
    ranges = max(ranges, eps);
    residual = ranges(2:end) - ranges(1) - rangeDiffObs;
    J = (x - stations(2:end, :)) ./ ranges(2:end) - ...
        (x - stations(1, :)) / ranges(1);
    A = L \ J;
    z = L \ residual;
    H = A.' * A;
    assert(rcond(H) > 1e-12, "几何退化或当前迭代不可解");
    step = -(H \ (A.' * z)).';
    x = x + step;
    if norm(step) < 1e-5
        break;
    end
end
end

function gdop = tdoaGdop(stations, x)
ranges = sqrt(sum((stations - x).^2, 2));
ranges = max(ranges, eps);
J = (x - stations(2:end, :)) ./ ranges(2:end) - ...
    (x - stations(1, :)) / ranges(1);
if rank(J) < 2
    gdop = Inf;
else
    gdop = sqrt(trace((J.' * J) \ eye(2)));
end
end
```

### Python

```python
import numpy as np


def solve_tdoa_wls(stations, range_diff_obs, chol_cov, x):
    for _ in range(50):
        ranges = np.maximum(np.linalg.norm(stations - x, axis=1), 1e-12)
        residual = ranges[1:] - ranges[0] - range_diff_obs
        jacobian = ((x - stations[1:]) / ranges[1:, None]
                    - (x - stations[0]) / ranges[0])
        whitened_j = np.linalg.solve(chol_cov, jacobian)
        whitened_r = np.linalg.solve(chol_cov, residual)
        normal = whitened_j.T @ whitened_j
        if np.linalg.cond(normal) > 1e12:
            raise ValueError("几何退化或当前迭代不可解")
        step = -np.linalg.solve(normal, whitened_j.T @ whitened_r)
        x = x + step
        if np.linalg.norm(step) < 1e-5:
            break
    return x


def tdoa_gdop(stations, x):
    ranges = np.maximum(np.linalg.norm(stations - x, axis=1), 1e-12)
    jacobian = ((x - stations[1:]) / ranges[1:, None]
                - (x - stations[0]) / ranges[0])
    if np.linalg.matrix_rank(jacobian) < 2:
        return np.inf
    return float(np.sqrt(np.trace(np.linalg.solve(
        jacobian.T @ jacobian, np.eye(2)))))


rng = np.random.default_rng(7)
c = 299_792_458.0
stations = np.array([[0., 0.], [1000., 0.], [0., 1000.], [1000., 1000.]])
x_true = np.array([420., 350.])
n_station = len(stations)
n_trial = 300
t0 = 0.025
sigma_toa = np.full(n_station, 20e-9)
clock_bias = np.zeros(n_station)       # T0/T1; 后续门逐项注入误差
hardware_delay = np.zeros(n_station)
clock_bias_cal = np.zeros(n_station)   # 使用估计校准值，不直接泄漏真值
hardware_delay_cal = np.zeros(n_station)

d = np.column_stack((-np.ones(n_station - 1), np.eye(n_station - 1)))
cov_tdoa_range = c**2 * d @ np.diag(sigma_toa**2) @ d.T
chol_cov = np.linalg.cholesky(cov_tdoa_range)
toa_errors, tdoa_errors, position_errors, gdops = [], [], [], []
toa_raw_history, toa_corrected_history = [], []
tdoa_seconds_history, range_diff_history = [], []

for _ in range(n_trial):
    true_range = np.linalg.norm(stations - x_true, axis=1)
    true_toa = t0 + true_range / c
    toa_raw = (true_toa + clock_bias + hardware_delay
               + sigma_toa * rng.standard_normal(n_station))
    toa_corrected = toa_raw - clock_bias_cal - hardware_delay_cal
    range_diff_obs = c * (d @ toa_corrected)
    tdoa_seconds_history.append(d @ toa_corrected)
    range_diff_history.append(range_diff_obs)
    range_diff_true = true_range[1:] - true_range[0]
    x_hat = solve_tdoa_wls(
        stations, range_diff_obs, chol_cov, stations.mean(axis=0).copy()
    )

    toa_errors.append(toa_corrected - true_toa)
    tdoa_errors.append(range_diff_obs - range_diff_true)
    toa_raw_history.append(toa_raw)
    toa_corrected_history.append(toa_corrected)
    position_errors.append(np.linalg.norm(x_hat - x_true))
    gdops.append(tdoa_gdop(stations, x_hat))

toa_errors = np.asarray(toa_errors)
tdoa_errors = np.asarray(tdoa_errors)
position_errors = np.asarray(position_errors)
toa_raw_history = np.asarray(toa_raw_history)
toa_corrected_history = np.asarray(toa_corrected_history)
tdoa_seconds_history = np.asarray(tdoa_seconds_history)
range_diff_history = np.asarray(range_diff_history)
print(f"ToA RMSE = {1e9 * np.sqrt(np.mean(toa_errors**2)):.3f} ns")
print("TDOA distance-difference RMSE =",
      np.sqrt(np.mean(tdoa_errors**2)), "m")
print("位置 RMSE =", np.sqrt(np.mean(position_errors**2)), "m")
position_p95 = np.sort(position_errors)[max(0, int(np.ceil(0.95 * n_trial)) - 1)]
print("位置 P95 =", position_p95, "m")
print("平均 GDOP =", np.mean(gdops[np.isfinite(gdops)]))
```

Python 示例依赖 NumPy；MATLAB 脚本末尾的局部函数要求 MATLAB R2016b 或更新版本。该基线的 TDOA 差分共享参考站，因此通过 `D * Cov(ToA) * D'` 保留相关性。进入 T2/T3 时应分别注入偏置/漂移并用独立校准估计补偿；进入 T4/T5 时再接入波形级首径/多径模型与鲁棒站点处理。
