---
title: CDL 信道模型
aliases:
  - Clustered Delay Line Channel Model
  - Clustered Delay Line
type: atomic
status: seed
tags:
  - domain/5G
  - domain/MIMO
  - topic/信道模型
  - object/时频域
  - stage/仿真
source:
  - 3GPP TR 38.901
simulation:
  - 09 仿真实验：MIMO 均衡
---

# CDL 信道模型

> [!abstract] 一句话结论
> CDL 以簇和簇内射线描述时延、角度、极化和阵列响应，适合研究 MIMO 信道估计、波束成形、空间相关性和预编码失配。

## 模型结构

一个频域 MIMO 信道可抽象为：

$$
\mathbf{H}[k,m]=
\sum_c\sum_{r\in c}
\alpha_{c,r}[m]\,
\mathbf{a}_R(\varphi_{c,r})
\mathbf{a}_T^H(\psi_{c,r})
e^{-j2\pi f_k\lambda_{c,r}}.
$$

其中 $c$ 是簇，$r$ 是簇内射线，$\alpha_{c,r}$ 是复增益，$\lambda_{c,r}$ 是相对时延，$\mathbf{a}_R$ 和 $\mathbf{a}_T$ 分别是收发阵列响应。实际 CDL 配置还包含阵列几何、极化、LOS/NLOS、载频、速度和采样接口。

## 为什么不能只看时延扩展

即使两个场景具有相近 RMS 时延扩展，它们也可能因角度扩展和阵列配置不同而具有不同的空间相关性、有效秩和条件数。这会改变端口导频分离、LMMSE 空间先验、ZF 噪声增强和预编码收益。

因此 CDL 实验应记录：天线阵列、端口与层定义、路径功率归一化、输出轴顺序和是否返回传播信道或已预编码的等效信道。

## 与其他概念的关系

- 前置：[[TDL 信道模型]]提供时延抽头视角；CDL 在此基础上加入空间和角度结构。
- 后续：[[空间相关性]]和[[MIMO 信道矩阵条件数]]解释不同空间模态的可分离程度。
- 应用：[[05 MIMO 信道估计]]必须区分传播信道、端口信道和层域等效信道；[[CSI 反馈]]基于观测 CSI 选择预编码。
- 对比：TDL 更适合快速建立时频估计基线，CDL 更适合回答阵列、波束和 MIMO 均衡问题。

## 待验证问题

- [ ] 固定导频资源、SNR、速度和总信道功率，比较 TDL 与 CDL 下 LS、LMMSE 的导频/数据 RE NMSE 与置信区间。
- [ ] 扫描阵列间距或角度扩展，记录空间相关系数、有效秩、条件数和 ZF/MMSE 后均衡 SINR。
- [ ] 用已知 $\mathbf{H}_{\mathrm{prop}}$ 和预编码矩阵验证端口域到层域的转换，记录 Frobenius 范数误差与数组轴顺序。

## 证据与仿真

- 规范入口：[[3GPP TR 38.901｜Channel model]]。
- 关联主题：[[05 MIMO 信道估计]]、[[06 OFDM 接收与频域均衡]]。
- 实验入口：[[09 仿真实验：MIMO 均衡]]、[[仿真实验：不同信道模型]]。