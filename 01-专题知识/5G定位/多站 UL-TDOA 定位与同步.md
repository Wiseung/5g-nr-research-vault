---
title: 多站 UL-TDOA 定位与同步
aliases:
  - 5G 多站到达时间差定位
  - NR UL-RTOA TDOA
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/定位
  - topic/tdoa
  - topic/同步
  - process/measurement
  - process/geometric-solver
  - evidence/3gpp
source:
  - 3GPP TS 38.305
  - 3GPP TS 38.215
  - 3GPP TR 38.901
  - 用户项目流程说明
related:
  - "[[NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]"
  - "[[单用户时频截取与定位观测量]]"
  - "[[5G TDD 上下行监测与资源解析]]"
  - "[[时变信道]]"
  - "[[TDL 信道模型]]"
simulation:
  - 仿真：多站 UL-TDOA 协同定位
---

# 多站 UL-TDOA 定位与同步

> [!warning] 方法边界
> 多个固定第三方站同时接收同一个 UE 的 PRACH/PUSCH，并由到达时间差反推 UE 位置，属于本项目的定制被动 UL-TOA/RTOA/TDOA 方案。它与 3GPP TS 38.305 中需要定位参考配置、测量报告和 LMF/gNB 协作的标准 UL-TDOA 流程相关但不等同；固定站对下行做差分只能直接定位下行发射源，不能仅凭此给出 UE 位置。

## 1. ToA、RTOA 与 TDOA

设 UE 位置为 $\mathbf{x}$，第 $i$ 个接收站位置为 $\mathbf{s}_i$，发射时刻为 $t_0$：

$$
t_i=t_0+\frac{\|\mathbf{x}-\mathbf{s}_i\|}{c}+b_i+d_i+e_i
$$

其中：

- $b_i$：站点时钟相对公共时间基准的偏置。
- $d_i$：射频、天线、线缆和采样链固定延迟。
- $e_i$：噪声、多径、NLOS、峰选择和估计误差。

UE 的 timing advance、调度时序和发射链延迟会进入未知发射时刻 $t_0$ 或观测偏置；它们不能在没有协议上下文时直接换算成 UE 到某一站的绝对距离。

以站 1 为参考，观测 TDOA 为：

$$
\Delta t_{i1}=t_i-t_1
=\frac{\|\mathbf{x}-\mathbf{s}_i\|-\|\mathbf{x}-\mathbf{s}_1\|}{c}
+(b_i-b_1)+(d_i-d_1)+(e_i-e_1).
$$

因此“相关峰差”只有在时钟和硬件延迟已校准后，才可转换为几何距离差 $c\Delta t_{i1}$。

## 2. 为什么项目主观测应是上行

| 测量方向 | 接收者 | 直接反映的发射源 | 与项目目标的关系 |
|---|---|---|---|
| 项目 UL-TOA/RTOA/TDOA | 多个固定站 | UE 上行发射 | 可直接形成 UE 的双曲线约束，但属于定制观测 |
| DL-TDOA | UE 或专用测量端 | 多个 gNB/TRP 下行 | 标准化方法通常由 UE 测量并回报；固定第三方站测到的是 gNB 到各站的差异 |
| OTDOA | UE 测多个传输点 | 下行参考信号 | 不能替代多站接收 UE 上行的方案 |

TS 38.305 V18.5.0 的方法章节同时列出 DL-TDOA、UL-TDOA；本项目应在文档中使用 `passive UL-TOA/RTOA/TDOA` 或“定制被动 UL-TDOA”。只有满足标准的 SRS/定位参考时间和报告接口时，才使用更窄的 `UL-RTOA` 标准测量名称，避免把第三方实现写成 OTDOA 或标准 UL-TDOA 合规流程。

## 3. 观测链路

```text
各站连续采集同一载频
    ↓
独立完成小区/帧同步和 TDD 方向判定
    ↓
用 PRACH、DM-RS、SRS 或重构片段检测同一用户事件
    ↓
每站输出 ToA/RTOA、峰策略、质量和绝对时间戳
    ↓
校正站间时钟、采样率、RF/滤波群时延
    ↓
构造相对 TDOA 和协方差
    ↓
加权双曲线解算、残差检验和异常站剔除
    ↓
输出位置、置信区间、GDOP 和不可用原因
```

同一用户事件的判定应优先使用 `(C-RNTI, 方向, 帧/时隙, 资源快照, 参考序列)`；只有 PRACH 前导相同而没有后续关联证据时，必须保留碰撞不确定性。

## 4. 站间同步与校准清单

| 项目 | 需记录/测量 | 影响 |
|---|---|---|
| 公共时间基准 | GNSS/PPS、PTP、线缆触发或其他方案 | 站间时钟偏置 |
| 采样时钟 | 频率误差、漂移、重采样状态 | TDOA 随时间变化 |
| RF/天线链 | 天线相位中心、线缆、射频 group delay | 固定距离偏差 |
| 数字滤波 | FIR/IIR 频响、群时延、抽 decimation 和数字下变频 | 频率相关时延 |
| 载频同步 | CFO、相位参考、校正时刻 | 相关峰和相位一致性 |
| 几何坐标 | 站点坐标、坐标系、天线高度 | 双曲线解和 GDOP |
| 多径策略 | 首径/最大峰/峰簇选择 | NLOS 偏差和异常值 |

校准结果应和 `capture_id`、频率、采样率绑定；不能把一次频段或温度条件下的延迟表永久复用于所有采集。

## 5. 站点数量和几何

- 二维、公共时钟已校准且高度已知时，至少需要两个独立 TDOA 约束，通常对应三站；站点不能近似共线。
- 三维位置或未知额外钟差通常需要更多站，工程上可用四站或以上并进行冗余检验。
- 站点数量不是充分条件；几何稀疏、遮挡和高 GDOP 仍会让位置不稳定。

可将几何约束写为：

$$
g_i(\mathbf{x})=\|\mathbf{x}-\mathbf{s}_i\|-\|\mathbf{x}-\mathbf{s}_1\|-c\,\Delta t_{i1}=0.
$$

在线解算可先用加权最小二乘，再根据残差、站点质量和 GDOP 做鲁棒重加权。以同一参考站形成的 TDOA 共享 $t_1$，其误差通常相关，不能把所有差分当成独立观测而忽略协方差。

## 6. 误差预算和质量门限

建议把总误差先近似拆成：

$$
\sigma^2_{\Delta t}
=\sigma^2_{sync}
+\sigma^2_{sample}
+\sigma^2_{RF}
+\sigma^2_{filter}
+\sigma^2_{multipath}
+\sigma^2_{estimator}.
$$

上式只是独立误差项的工程近似；以同一参考站形成的差分共享测量误差时，应保留 ToA 协方差并用完整权重矩阵。报告位置时至少给出：TDOA RMSE/分位数、位置 RMSE/95% 分位数、有效站数、GDOP、残差、剔除站点数和 `toa_valid` 比例。单次漂亮的坐标不构成定位精度结论。

## 7. 与 PRACH/PUSCH 的关系

- PRACH 相关峰适合做接入事件触发和粗 ToA；必须保留全峰轨迹、碰撞标记和首径策略。
- PUSCH DM-RS/SRS 或重构的已知片段可提供更长相关积累，但需要准确的 UL 资源、端口和用户关联。
- C-RNTI 主要帮助跨时隙/跨消息关联和调度解析，不会自动消除传播多径或站间时钟误差。
- 过滤/截断造成的群时延应在形成 TDOA 前统一补偿；否则会把接收机处理差异误判为位置变化。

## 8. 标准流程与项目实现的分离

3GPP TS 38.305 的标准 UL-TDOA 流程包含定位能力、辅助数据、上行定位参考配置、多个测量点报告和 LMF 交互；本项目若没有 gNB/LMF 协作、改用 PRACH/PUSCH 被动监听，应记录为 `HYPOTHESIS + NEEDS_EXTERNAL_REFERENCE` 的工程路线。标准条款能约束术语和测量边界，但不能替项目证明算法精度或实时性。

## 9. MATLAB 示例：二维加权 TDOA 解算

以下脚本使用相对 ToA 构造 TDOA，并通过完整差分协方差进行加权最小二乘。合成数据只用于验证几何求解闭环；实测时应替换为同一 UL 事件经时钟、RF 和滤波延迟校正后的多站 ToA。

```matlab
c = 299792458; % m/s
stationsXY = [0, 0; 1000, 0; 0, 1000; 1000, 1000]; % m
xTrue = [420, 350]; % 仅用于本地仿真
t0 = 0.025;         % 未知发射时刻，会在差分中消去
sigmaToa = 15e-9 * ones(size(stationsXY, 1), 1);

rng(7);
rangeTrue = sqrt(sum((stationsXY - xTrue).^2, 2));
toaRaw = t0 + rangeTrue / c + sigmaToa .* randn(size(sigmaToa));

nStation = size(stationsXY, 1);
assert(nStation >= 3 && numel(toaRaw) == nStation);
assert(all(sigmaToa > 0) && all(isfinite(toaRaw)));
D = [-ones(nStation - 1, 1), eye(nStation - 1)];
tdoaSeconds = D * toaRaw;
rangeDifference = c * tdoaSeconds;
Rrange = c^2 * D * diag(sigmaToa.^2) * D.';
L = chol(Rrange, "lower"); % 保留共享参考站造成的差分相关性

x = mean(stationsXY, 1); % 初值；实际部署可用上次有效位置
for iteration = 1:50
    ranges = sqrt(sum((stationsXY - x).^2, 2));
    ranges = max(ranges, eps);
    predicted = ranges(2:end) - ranges(1);
    residual = predicted - rangeDifference;

    J = (x - stationsXY(2:end, :)) ./ ranges(2:end) - ...
        (x - stationsXY(1, :)) / ranges(1);
    whitenedResidual = L \ residual;
    whitenedJ = L \ J;
    normalMatrix = whitenedJ.' * whitenedJ;
    assert(rcond(normalMatrix) > 1e-12, ...
        "站点几何退化或初值不可用，不能可靠解算");
    step = -(normalMatrix \ (whitenedJ.' * whitenedResidual)).';
    x = x + step;
    if norm(step) < 1e-4
        break;
    end
end

ranges = sqrt(sum((stationsXY - x).^2, 2));
predicted = ranges(2:end) - ranges(1);
residualMeters = predicted - rangeDifference;
J = (x - stationsXY(2:end, :)) ./ max(ranges(2:end), eps) - ...
    (x - stationsXY(1, :)) / max(ranges(1), eps);
whitenedJ = L \ J;
normalMatrix = whitenedJ.' * whitenedJ;
positionCovariance = normalMatrix \ eye(2);
if rank(J) == 2
    gdop = sqrt(trace((J.' * J) \ eye(2)));
else
    gdop = Inf;
end

fprintf("估计位置: x=%.2f m, y=%.2f m\n", x(1), x(2));
fprintf("位置误差: %.2f m, GDOP=%.3f, 迭代=%d\n", ...
    norm(x - xTrue), gdop, iteration);
disp("位置协方差估计 [m^2]:");
disp(positionCovariance);
disp("各非参考站距离差残差 [m]:");
disp(residualMeters);
```

实测输入应先按事件 ID 确认各站观测来自同一 UE 上行发射，再应用每站时钟、RF、滤波群时延和采样率漂移校正。该基线没有自动剔除 NLOS/异常站；上线时需结合 `toa_valid`、残差门限、站点几何和冗余站做鲁棒重加权或重新求解。至少三站才能形成二维两个独立 TDOA 约束，站点近共线时即使数值收敛也不代表定位可靠。

## 证据与出处

- `STANDARD + partial`： [ETSI TS 38.305 V18.5.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf)，重点核对 §4.3.13 DL-TDOA、§4.3.14 UL-TDOA、§8.12/§8.13；版本应与项目采用的 Release 对齐。
- `STANDARD + partial`： [ETSI TS 38.215 V17.2.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf)，§5.2.2 用于核对含 SRS 的 UL-RTOA、接收参考点，§5.2.7 用于核对 PRACH/TADV 与 first detected path 的边界。
- `STANDARD + partial`：[[3GPP TR 38.901｜Channel model]]，用于 TDL/CDL、多径、多普勒和同步误差的仿真分层。
- `PERSONAL_NOTE`：用户项目说明中的“三台或四台设备协同 TDOA”和“先得到干净单用户数据再定位”。
- `HYPOTHESIS + NEEDS_VERIFICATION`：用 PRACH/PUSCH 相关峰作为定制被动 UL-TOA/RTOA 观测，可在没有 LMF 配置时工作；只有满足标准 SRS/参考时间条件时才升级为标准 UL-RTOA，必须以校准采集和仿真对照验证。

## 当前状态

- `EXPERIMENT + NEEDS_VERIFICATION`：尚未获得站点坐标、公共时钟方案、RF group delay 和真实多径数据。
- `TODO`：先用三站二维、理想公共时钟和单径仿真建立闭环，再逐一加入时钟漂移、群时延、CFO、NLOS 和站点剔除；确认用户口述的“120.88 兆”是载频、带宽、采样率还是其他参数。

## 项目化入口

- 多站同步：[[5G-NR-Positioning/07-多站协同/Multi-Station Synchronization]]
- 时钟偏置与漂移：[[5G-NR-Positioning/07-多站协同/Clock Offset and Drift]]
- RF/数字链路延迟：[[5G-NR-Positioning/07-多站协同/RF and Digital Delay Calibration]]
- 跨站事件关联：[[5G-NR-Positioning/07-多站协同/Cross-Station Event Association]]
- 多站观测融合：[[5G-NR-Positioning/07-多站协同/Multi-Station Observation Fusion]]
- 同步验证台账：[[5G-NR-Positioning/07-多站协同/Synchronization Validation Ledger]]
- TDOA 解算：[[5G-NR-Positioning/06-TDOA定位/TDOA]]
- 时间观测：[[5G-NR-Positioning/05-定位观测量/Timing Observation]]
