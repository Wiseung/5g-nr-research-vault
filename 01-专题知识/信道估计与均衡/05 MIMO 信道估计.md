---
title: 05 MIMO 信道估计
aliases:
  - MIMO CSI 估计
created: 2026-08-20
tags:
  - domain/5G
  - domain/MIMO
  - topic/信道估计
  - topic/空间信道
  - object/Massive-MIMO
  - stage/接收机
---

# 05 MIMO 信道估计

## 一句话定义

MIMO 信道估计需要同时恢复多个发射端口到多个接收天线之间的复信道系数，并保留端口、天线、子载波和时间符号之间的空间结构，供预编码、均衡和检测使用。

## 前置知识

- [[00 5G 信道估计与均衡前置知识#复数与复向量基础]]：掌握复信道系数、相位、共轭和复噪声。
- [[00 5G 信道估计与均衡前置知识#矩阵论与线性代数]]：掌握矩阵维度、秩、SVD、奇异值、条件数和协方差矩阵。
- [[00 5G 信道估计与均衡前置知识#MIMO 与空间信道]]：理解空间复用、分集、波束成形、端口/层和 CSI 反馈。
- [[00 5G 信道估计与均衡前置知识#随机过程与相关函数]]：理解空间相关性、二阶统计和低秩信道结构。
- [[00 5G 信道估计与均衡前置知识#无线传播]]：理解角度扩展、多径、视距/非视距和移动性导致的空间信道变化。

## 1. MIMO 频域模型

在 OFDM 的第 $k$ 个子载波和第 $m$ 个符号上：

$$
\mathbf{y}[k,m]=\mathbf{H}[k,m]\mathbf{x}[k,m]+\mathbf{n}[k,m]
$$

其中：

- $\mathbf{x}\in\mathbb{C}^{N_t\times 1}$：发射端口或空间层符号。
- $\mathbf{y}\in\mathbb{C}^{N_r\times 1}$：接收天线观测。
- $\mathbf{H}\in\mathbb{C}^{N_r\times N_t}$：MIMO 信道矩阵。
- $\mathbf{n}\in\mathbb{C}^{N_r\times 1}$：接收噪声和未建模干扰。

在实际接收机中，至少要区分四种信道对象：

| 对象 | 表达 | 典型用途 |
|---|---|---|
| 传播信道 | $\mathbf{H}_{\mathrm{prop}}$ | 物理传播和阵列分析 |
| 射频端到端信道 | $\mathbf{H}_{\mathrm{obs}}=\mathbf{G}_r\mathbf{H}_{\mathrm{prop}}\mathbf{G}_t$ | 硬件链路实际观测 |
| 端口信道 | 端口到接收天线的矩阵 | 参考信号端口分离 |
| 层域等效信道 | $\mathbf{H}_{\mathrm{eff}}=\mathbf{H}\mathbf{W}$ | 数据层均衡和检测 |

如果参考信号和数据经历不同的预编码，参考信号估计结果不能直接作为数据层 CSI。估计器接口必须携带 `channel_domain` 或等价状态，说明矩阵属于哪一个域。

### MIMO 模型的维度账本

设发射端口数为 $N_t$、接收天线数为 $N_r$、数据层数为 $N_s$，预编码矩阵为：

$$
\mathbf{W}[k,m]\in\mathbb{C}^{N_t\times N_s}.
$$

则：

$$
\mathbf{s}[k,m]\in\mathbb{C}^{N_s\times1},
\qquad
\mathbf{x}[k,m]=\mathbf{W}[k,m]\mathbf{s}[k,m]
\in\mathbb{C}^{N_t\times1},
$$

$$
\mathbf{H}[k,m]\in\mathbb{C}^{N_r\times N_t},
\qquad
\mathbf{H}_{\mathrm{eff}}[k,m]
=\mathbf{H}[k,m]\mathbf{W}[k,m]
\in\mathbb{C}^{N_r\times N_s}.
$$

因此：

$$
\mathbf{y}[k,m]
=\mathbf{H}_{\mathrm{eff}}[k,m]\mathbf{s}[k,m]
+\mathbf{n}[k,m]
\in\mathbb{C}^{N_r\times1}.
$$

这组维度是 MIMO 信道估计的第一层单元测试。只要把端口、层或天线维度转置，矩阵乘法仍可能在某些方形配置下成功，但预编码和均衡的物理含义已经改变。

每个子载波拥有一个信道矩阵：

$$
\mathbf{H}[k]=
\begin{bmatrix}
 h_{1,1}[k] & \cdots & h_{1,N_t}[k]\\
 \vdots & \ddots & \vdots\\
 h_{N_r,1}[k] & \cdots & h_{N_r,N_t}[k]
\end{bmatrix}
$$

## 1.1 维度和索引约定

建议固定以下矩阵方向：

- 行索引：接收天线 $r=1,\ldots,N_r$。
- 列索引：发射端口或发射层 $t=1,\ldots,N_t$。
- 频率索引：子载波 $k$。
- 时间索引：OFDM 符号 $m$。

于是 $H_{r,t}[k,m]$ 表示发射端口 $t$ 到接收天线 $r$ 的复增益。不同工具可能使用 $N_t\times N_r$ 的转置约定，接入代码时应先用单位矩阵、单端口和已知单径信道验证方向。

建议把每个信道样本标记为：

$$
\mathsf{H}\left[
\mathrm{rx},\mathrm{tx},\mathrm{subcarrier},\mathrm{symbol},\mathrm{domain}
\right]
$$

其中 `domain` 指物理传播、射频观测、端口或层域。数组轴的顺序应写入接口文档或元数据，不能只依赖变量名。

### 1.1.1 端口到层的等效变换

如果估计得到端口域信道 $\widehat{\mathbf{H}}_{\mathrm{port}}$，且发送端预编码已知，则层域等效 CSI 为：

$$
\widehat{\mathbf{H}}_{\mathrm{eff}}
=\widehat{\mathbf{H}}_{\mathrm{port}}\mathbf{W}.
$$

若参考信号已经包含预编码，直接估计的可能就是 $\widehat{\mathbf{H}}_{\mathrm{eff}}$；此时再次乘以 $\mathbf{W}$ 会导致重复预编码。可以用已知无噪声信道验证：

$$
\left\|\widehat{\mathbf{H}}_{\mathrm{eff}}
-\mathbf{H}_{\mathrm{prop}}\mathbf{W}\right\|_F
$$

来检查估计域是否正确。

## 1.2 空间层数与可用秩

空间层数 $N_s$ 受以下因素共同限制：

$$
N_s\le\min(N_t,N_r,\operatorname{rank}_{\mathrm{eff}}(\mathbf{H}))
$$

有效秩不是简单的代数秩，还取决于奇异值阈值、SNR、估计误差和目标 BLER。估计器应为调度或检测提供奇异值、条件数或秩可靠度，而不是只输出一个平均 NMSE。

令奇异值按 $\sigma_1\geq\sigma_2\geq\cdots$ 排列，给定相对阈值 $\tau$，可定义数值有效秩：

$$
r_{\mathrm{eff}}(\tau)
=\#\{i:\sigma_i\geq\tau\sigma_1\}.
$$

也可以用能量阈值 $\beta$ 定义：

$$
r_{\mathrm{energy}}(\beta)
=\min\left\{r:
\frac{\sum_{i=1}^{r}\sigma_i^2}
{\sum_i\sigma_i^2}\geq\beta\right\}.
$$

这两个“有效秩”回答不同问题：相对阈值关注弱空间模态是否可稳定分离，能量阈值关注大部分信道能量是否被少数模态承载。报告 MIMO 估计性能时应说明使用哪一个定义。

## 2. 多端口导频分离

如果不同发射端口同时发送参考信号，接收机需要利用正交资源、码域序列或可分离结构估计各端口信道。对第 $p$ 个端口的导频位置，简化模型为：

$$
\mathbf{y}_p=\mathbf{h}_p x_p+\mathbf{n}_p
$$

逐接收天线执行 LS 后得到：

$$
\hat{\mathbf{h}}_p=\frac{\mathbf{y}_p}{x_p}
$$

所有端口和接收天线组合起来，形成 $\hat{\mathbf{H}}$。如果端口间不正交，导频互扰会直接成为估计偏差。

单个 RE 上同时激励多个端口时，观测是多个未知信道列的线性组合，不能对每个端口独立相除。需要收集 $Q$ 个训练资源：

$$
\mathbf{Y}_p
=\mathbf{H}_p\mathbf{S}_p+\mathbf{N}_p,
$$

其中：

$$
\mathbf{Y}_p\in\mathbb{C}^{N_r\times Q},
\quad
\mathbf{H}_p\in\mathbb{C}^{N_r\times N_t},
\quad
\mathbf{S}_p\in\mathbb{C}^{N_t\times Q}.
$$

每一列对应一个训练资源，每一行对应一个发射端口。若 $\mathbf{S}_p$ 满行秩，则所有端口信道在“训练窗口内近似相同”的条件下可被分离。

### 多端口可辨识性定理

在无噪声、静态训练窗口模型：

$$
\mathbf{Y}_p=\mathbf{H}_p\mathbf{S}_p
$$

下，$\mathbf{H}_p$ 可以由 $\mathbf{Y}_p$ 唯一恢复，当且仅当：

$$
\operatorname{rank}(\mathbf{S}_p)=N_t.
$$

若 $\mathbf{S}_p$ 不满行秩，则存在非零矩阵 $\mathbf{Z}$ 满足 $\mathbf{Z}\mathbf{S}_p=\mathbf{0}$，于是 $\mathbf{H}_p$ 和 $\mathbf{H}_p+\mathbf{Z}$ 产生相同观测。若满行秩，则右伪逆满足：

$$
\mathbf{S}_p\mathbf{S}_p^H
\left(\mathbf{S}_p\mathbf{S}_p^H\right)^{-1}
=\mathbf{I}_{N_t},
$$

从而可构造唯一的端口级 LS 解。

这个定理只说明端口“可分离”，不保证估计抗噪。抗噪性由 $\mathbf{S}_p\mathbf{S}_p^H$ 的最小特征值和条件数决定。

## 2.1 端口、层与等效信道

发送信号常可写成：

$$
\mathbf{x}=\mathbf{W}\mathbf{s}
$$

其中 $\mathbf{s}$ 是空间层符号，$\mathbf{W}$ 是预编码矩阵。接收信号为：

$$
\mathbf{y}=\mathbf{H}\mathbf{W}\mathbf{s}+\mathbf{n}
$$

如果接收机估计的是 $\mathbf{H}$，均衡器还需要知道 $\mathbf{W}$；如果参考信号随预编码映射，估计目标可能是等效信道：

$$
\mathbf{H}_{\mathrm{eff}}=\mathbf{H}\mathbf{W}
$$

报告 MIMO 信道估计结果时必须说明估计的是物理端口信道还是数据层等效信道。

如果参考信号端口使用训练矩阵 $\mathbf{S}_p$，而数据使用预编码 $\mathbf{W}$，则端口信道估计与数据层信道之间的关系为：

$$
\widehat{\mathbf{H}}_{\mathrm{data}}
=\widehat{\mathbf{H}}_{\mathrm{port}}\mathbf{W}.
$$

若参考信号和数据的预编码不同：

$$
\mathbf{H}_{\mathrm{RS}}
=\mathbf{H}_{\mathrm{prop}}\mathbf{W}_{\mathrm{RS}},
\qquad
\mathbf{H}_{\mathrm{data}}
=\mathbf{H}_{\mathrm{prop}}\mathbf{W}_{\mathrm{data}},
$$

则直接复用参考信号估计会产生结构化残差：

$$
\mathbf{H}_{\mathrm{data}}
-\mathbf{H}_{\mathrm{RS}}
=\mathbf{H}_{\mathrm{prop}}
\left(\mathbf{W}_{\mathrm{data}}-\mathbf{W}_{\mathrm{RS}}\right).
$$

这不是普通热噪声，除非预编码差异已知并被补偿，否则增加导频平均次数不能消除。

## 2.2 端口分离的矩阵模型

将多个参考符号观测堆叠为 $\mathbf{Y}$，端口参考序列组成 $\mathbf{X}$，可写成：

$$
\mathbf{Y}=\mathbf{H}\mathbf{X}+\mathbf{N}
$$

若 $\mathbf{X}\mathbf{X}^H$ 可逆，端口级 LS 为：

$$
\hat{\mathbf{H}}=\mathbf{Y}\mathbf{X}^H(\mathbf{X}\mathbf{X}^H)^{-1}
$$

当端口序列正交且功率归一化一致时，端口间交叉项较小；否则交叉相关会直接进入估计误差。

定义端口训练 Gram 矩阵：

$$
\mathbf{G}_p=\mathbf{X}\mathbf{X}^H.
$$

若：

$$
\mathbf{G}_p=E_p\mathbf{I}_{N_t},
$$

则端口级 LS 简化为匹配滤波：

$$
\widehat{\mathbf{H}}
=\frac{1}{E_p}\mathbf{Y}\mathbf{X}^H.
$$

在接收噪声元素独立、方差为 $\sigma_n^2$ 时，每个端口-接收天线系数的误差方差为：

$$
\operatorname{Var}
\left(\widehat{H}_{r,t}-H_{r,t}\right)
=\frac{\sigma_n^2}{E_p}.
$$

若不正交，通用误差协方差为：

$$
R_{e,r}
=\sigma_n^2
\left(\mathbf{X}\mathbf{X}^H\right)^{-1}
$$

其中 $R_{e,r}$ 描述固定接收天线 $r$ 上的端口估计误差。其非对角元素表示不同端口估计误差之间的相关性，不能只用一个标量噪声方差替代。

## 2.3 多端口训练的最小条件

在一个训练窗口内，若同时估计 $N_t$ 个端口，观测长度和训练矩阵需要满足：

- 训练观测数量不少于待分离端口数量。
- $\mathbf{X}\mathbf{X}^H$ 满秩且条件数可接受。
- 端口序列的功率和相位约定一致。
- 训练期间信道变化不会破坏端口分离假设。

若端口训练跨越多个 OFDM 符号，快速时变会使不同列观测对应不同的 $\mathbf{H}[m]$，此时简单的矩阵 LS 会把信道变化误认为端口互扰。

设第 $q$ 个训练资源上的真实信道为 $\mathbf{H}_q$：

$$
\mathbf{Y}[:,q]
=\mathbf{H}_q\mathbf{x}_q+\mathbf{n}_q.
$$

使用静态矩阵 LS 估计一个参考时刻 $\mathbf{H}_0$ 时，误差包含：

$$
\widehat{\mathbf{H}}-\mathbf{H}_0
=\left(\sum_q\mathbf{H}_q\mathbf{x}_q\mathbf{x}_q^H\right)
\left(\mathbf{X}\mathbf{X}^H\right)^{-1}
-\mathbf{H}_0
+\mathbf{N}\mathbf{X}^H
\left(\mathbf{X}\mathbf{X}^H\right)^{-1}.
$$

第一部分是时变偏差，第二部分是热噪声传播。缩短训练窗口可以降低时变偏差，但会减少训练能量或端口正交长度。

## 3. MIMO 信道的空间统计

常用的 Kronecker 模型为：

$$
\mathbf{H}=R_r^{1/2}\mathbf{H}_wR_t^{1/2}
$$

其中 $R_r$ 和 $R_t$ 分别是接收端和发射端空间相关矩阵，$\mathbf{H}_w$ 是独立同分布复高斯矩阵。该模型便于分析，但未必能准确描述真实簇状传播和发射接收角度耦合。

空间相关性高时，信道列向量更相似，矩阵 $\mathbf{H}^H\mathbf{H}$ 可能病态，导致 ZF 均衡噪声增强。

Kronecker 模型的向量化形式为：

$$
\mathrm{vec}(\mathbf{H})
=\left(R_t^{T/2}\otimes R_r^{1/2}\right)
\mathrm{vec}(\mathbf{H}_w).
$$

因此空间信道协方差近似为：

$$
R_{hh}
=R_t^T\otimes R_r.
$$

该模型将发射和接收相关性分离，便于构造 MIMO LMMSE；但真实 CDL 信道中簇角度、极化和阵列几何可能产生不可分离的联合相关性。

若发射相关矩阵 $R_t$ 的特征值集中在少数方向，发射端可激励的独立空间模态减少；若接收相关矩阵 $R_r$ 退化，则不同接收天线提供的独立观测减少。两者都会同时影响端口可辨识性和数据检测。

## 3.1 奇异值与有效空间秩

对信道矩阵进行奇异值分解：

$$
\mathbf{H}=\mathbf{U}\mathbf{\Sigma}\mathbf{V}^H
$$

非零奇异值数量反映可支持的有效空间维度。最小奇异值过小意味着某些空间方向几乎不可分离，增加空间层数并不一定带来吞吐量收益。

估计场景中还应比较 $\hat{\mathbf{H}}$ 与 $\mathbf{H}$ 的奇异值和奇异向量，而不能只比较逐元素 NMSE。小的逐元素误差在病态信道上可能导致明显的预编码或均衡变化。

对接收模型：

$$
\mathbf{y}=\mathbf{U}\mathbf{\Sigma}\mathbf{V}^H\mathbf{x}+\mathbf{n},
$$

左乘 $\mathbf{U}^H$、右侧变量替换 $\mathbf{q}=\mathbf{V}^H\mathbf{x}$ 后得到空间模态：

$$
\widetilde{\mathbf{y}}
=\mathbf{\Sigma}\mathbf{q}+\widetilde{\mathbf{n}}.
$$

第 $i$ 个模态的观测 SNR 近似与 $\sigma_i^2P_i/\sigma_n^2$ 成正比。即使总信道功率不变，能量集中在少数奇异方向也会使弱模态无法稳定承载独立层。

### 3.1.1 奇异值扰动与估计误差

设 $\widehat{\mathbf{H}}=\mathbf{H}+\mathbf{E}$，则由奇异值扰动界可得，对应奇异值满足数量级约束：

$$
|\widehat{\sigma}_i-\sigma_i|
\leq\|\mathbf{E}\|_2.
$$

如果 $\sigma_i$ 本身接近零，即使 $\|\mathbf{E}\|_2$ 较小，相对误差：

$$
\frac{|\widehat{\sigma}_i-\sigma_i|}{\sigma_i}
$$

仍可能很大。因此 MIMO 信道估计应同时报告绝对奇异值误差和弱模态相对误差。

对 ZF 均衡器，理想 SVD 域中第 $i$ 个模态的噪声增强与：

$$
\frac{1}{\sigma_i^2}
$$

成正比。估计误差使均衡器使用 $\widehat{\sigma}_i$，会进一步造成增益估计偏差和层间泄漏。MMSE 均衡通过正则化限制弱模态增益，但无法恢复本身不可辨识的空间方向。

## 3.2 空间相关矩阵的性质

空间协方差应满足厄米特和半正定条件：

$$
R_t=R_t^H,\quad R_t\succeq0
$$

样本估计得到的矩阵可能因为有限样本或数值误差出现微小负特征值。用于平方根分解前，应进行特征值裁剪、对角加载或最近半正定投影，并记录处理方式。

Kronecker 模型 $R_r\otimes R_t$ 能降低参数量，但不能完整描述发射角和接收角之间的耦合。若采用它生成训练数据，不能直接声称结果适用于所有真实阵列。

空间相关矩阵的一个可解释性指标是归一化特征值熵：

$$
\eta_{\mathrm{entropy}}
=\exp\left(-\sum_i p_i\log p_i\right),
\qquad
p_i=\frac{\lambda_i}{\sum_j\lambda_j}.
$$

它可作为有效空间维度的连续近似。$\eta_{\mathrm{entropy}}$ 越接近 $1$，表示能量集中在少数特征方向；归一化时也可除以最大天线维度，便于比较不同阵列规模。该指标不能替代实际奇异值阈值或 BLER 判断，但有助于解释空间相关变化。

## 4. MIMO LMMSE 估计

向量化信道矩阵：

$$
\mathbf{h}=\mathrm{vec}(\mathbf{H})
$$

若向量化观测模型为：

$$
\mathbf{y}=\mathbf{A}\mathbf{h}+\mathbf{n},
$$

其中 $\mathbf{A}$ 是由训练序列、资源选择和预编码构成的观测矩阵。利用信道协方差 $R_{hh}$ 和噪声协方差 $R_{nn}$，有：

$$
R_{hy}=R_{hh}\mathbf{A}^H,
\qquad
R_{yy}=\mathbf{A}R_{hh}\mathbf{A}^H+R_{nn},
$$

$$
\hat{\mathbf{h}}=R_{hy}R_{yy}^{-1}\mathbf{y}
$$

空间、时间和频率相关性都可能被纳入协方差。实际实现通常不直接对全维向量求解，而是采用分解、低秩或维度分离。

若观测模型为：

$$
\mathbf{y}=\mathbf{A}\mathbf{h}+\mathbf{n},
$$

其中 $\mathbf{A}$ 包含端口训练、资源选择、预编码和导频缩放，则一般 MIMO LMMSE 为：

$$
\widehat{\mathbf{h}}_{\mathrm{LMMSE}}
=R_{hh}\mathbf{A}^H
\left(\mathbf{A}R_{hh}\mathbf{A}^H+R_{nn}\right)^{-1}
\mathbf{y}.
$$

后验误差协方差为：

$$
R_e
=R_{hh}
-R_{hh}\mathbf{A}^H
\left(\mathbf{A}R_{hh}\mathbf{A}^H+R_{nn}\right)^{-1}
\mathbf{A}R_{hh}.
$$

这里的 $R_{hh}$ 是向量化 MIMO 信道的协方差，而不是单个天线对的功率。若忽略空间非对角相关项，估计器会失去利用空间冗余的能力；若错误加入过强空间相关，可能把真实独立空间方向过度收缩。

### 全维求解的复杂度问题

对 $N_r\times N_t$ 的单个频率信道，向量化维度为 $P=N_rN_t$。若同时堆叠 $K$ 个子载波和 $M$ 个时间符号，参数维度可能达到：

$$
P_{\mathrm{full}}=N_rN_tKM.
$$

完整协方差需要 $O(P_{\mathrm{full}}^2)$ 存储，直接分解还需要更高的计算量，因此通常只能用于小规模验证。工程实现常采用：

- 每个子载波独立估计，再利用空间协方差。
- 时间、频率和空间维度分离。
- 低秩空间子空间投影。
- 局部时频窗口和滑动更新。
- 预计算固定配置下的线性滤波矩阵。

所有降维方法都应报告被忽略的相关项和重构误差，而不能只报告计算量下降。

## 4.1 向量化和 Kronecker 结构

若按列向量化，有：

$$
\mathrm{vec}(\mathbf{H}\mathbf{X})
=(\mathbf{X}^T\otimes\mathbf{I}_{N_r})\mathrm{vec}(\mathbf{H})
$$

因此多端口训练可转换为标准线性观测模型。实现时必须确认 `vec` 的行列顺序，否则协方差和观测矩阵会同时错位而不易察觉。

若空间、时间和频率相关性近似可分离，可使用：

$$
R_{hh}\approx R_f\otimes R_m\otimes R_r\otimes R_{\mathrm{port}}
$$

该结构能减少全维矩阵的存储，但每个分量的排序和张量维度必须在接口中固定。

在只考虑空间相关、导频训练矩阵为 $\mathbf{X}$ 时，向量化观测可以写成：

$$
\mathbf{y}
=\left(\mathbf{X}^T\otimes\mathbf{I}_{N_r}\right)\mathbf{h}
+\mathbf{n}.
$$

若：

$$
R_{hh}=R_t^T\otimes R_r,
$$

则：

$$
\mathbf{A}R_{hh}\mathbf{A}^H
=\left(\mathbf{X}^T\otimes\mathbf{I}_{N_r}\right)
\left(R_t^T\otimes R_r\right)
\left(\mathbf{X}^*\otimes\mathbf{I}_{N_r}\right).
$$

利用 Kronecker 乘积规则可将其整理为：

$$
\left(\mathbf{X}^TR_t^T\mathbf{X}^*\right)
\otimes R_r.
$$

这表明发射训练相关性和接收空间相关性可以在一定条件下分离计算。若训练矩阵、天线相关矩阵或索引顺序不满足这些条件，不能直接套用分离后的快速公式。

### 4.1.1 空间子空间投影

若接收空间协方差的主要特征向量组成 $U_{r,q}$，可先进行接收端空间投影：

$$
\mathbf{y}_{q}
=U_{r,q}^H\mathbf{y},
\qquad
\mathbf{H}_{q}
=U_{r,q}^H\mathbf{H}.
$$

当保留秩 $q<N_r$ 时，投影降低了观测维度和噪声存储，但丢失的正交补空间会产生截断误差：

$$
E_{\mathrm{space\,trunc}}
=\operatorname{tr}
\left((\mathbf{I}-U_{r,q}U_{r,q}^H)R_r\right).
$$

若弱空间方向对应某个数据层的有效信号，不应只依据平均接收功率裁剪；应同时检查层级 BLER 和预编码增益。

## 4.2 端口污染与结构化误差

若不同端口或用户的参考信号不完全可分离，可以将观测写成：

$$
\mathbf{Y}=\mathbf{H}_1\mathbf{X}_1+\mathbf{H}_2\mathbf{X}_2+\mathbf{N}
$$

用 $\mathbf{X}_1$ 估计 $\mathbf{H}_1$ 时，第二项会形成与端口序列相关的偏差。它不是简单增加白噪声方差，因此单纯提高 LMMSE 的噪声参数可能无效。

诊断时应保存端口交叉相关矩阵：

$$
\mathbf{C}_{12}=\mathbf{X}_1\mathbf{X}_2^H
$$

并分别测试正交、部分相关和完全复用三种情况。

若污染用户的训练序列已知，可以将两个用户联合写成：

$$
\mathbf{Y}
=\begin{bmatrix}\mathbf{H}_1&\mathbf{H}_2\end{bmatrix}
\begin{bmatrix}\mathbf{X}_1\\\mathbf{X}_2\end{bmatrix}
+\mathbf{N}
$$

在联合训练矩阵满行秩时，可同时估计 $\mathbf{H}_1$ 和 $\mathbf{H}_2$。但这只是在接收机拥有污染序列和足够训练资源时成立；未知污染源不能仅凭增加未知参数解决，因为未知量和观测数量会同时增长。

若仍使用 $\mathbf{X}_1$ 做目标用户 LS，估计结果为：

$$
\widehat{\mathbf{H}}_1
=\mathbf{H}_1
+\mathbf{H}_2\mathbf{X}_2\mathbf{X}_1^H
\left(\mathbf{X}_1\mathbf{X}_1^H\right)^{-1}
+\mathbf{N}\mathbf{X}_1^H
\left(\mathbf{X}_1\mathbf{X}_1^H\right)^{-1}.
$$

中间项是污染偏差。若 $\mathbf{X}_2\mathbf{X}_1^H=\mathbf{0}$，它在静态信道模型下消失；若仅仅是小而非零，污染大小还会被 $\mathbf{H}_2$ 的空间增益放大。

## 4.3 导频污染的可分解性

当污染源的参考序列已知时，可以扩展观测矩阵并联合估计；当污染源未知或与目标端口高度相关时，单帧观测通常无法仅凭线性方法将其分离。可行的辅助信息包括：

- 不同时间窗口的变化差异。
- 角度域或时延域稀疏性。
- 邻区调度和参考信号配置。
- 多用户联合检测或干扰协方差估计。

因此，导频污染实验必须说明污染源是否已知、是否共享序列、是否随时间变化。

可利用空间或时延结构进行辅助分离。例如，在接收空间投影 $U_q^H$ 后：

$$
\mathbf{Y}_q
=U_q^H\mathbf{H}_1\mathbf{X}_1
+U_q^H\mathbf{H}_2\mathbf{X}_2
+U_q^H\mathbf{N}.
$$

若两个用户的空间子空间近似正交，选择 $U_q$ 可降低第二项；若两者角度接近，空间投影不能从根本上消除污染。类似地，时延域稀疏性只有在有效带宽和路径结构足够区分时才有帮助。

污染源可分离性应至少用以下量评估：

$$
\rho_{12}
=\frac{\|\mathbf{X}_1\mathbf{X}_2^H\|_F}
{\|\mathbf{X}_1\mathbf{X}_1^H\|_F^{1/2}
\|\mathbf{X}_2\mathbf{X}_2^H\|_F^{1/2}},
$$

以及空间子空间相似度：

$$
\eta_{\mathrm{space}}
=\frac{1}{q}\|U_1^HU_2\|_F^2.
$$

序列相关性和空间相关性同时较高时，属于最难的导频污染场景，单纯更换 LS/LMMSE 估计器通常不能解决根因。

## 5. 估计误差的空间影响

定义：

$$
\tilde{\mathbf{H}}=\hat{\mathbf{H}}-\mathbf{H}
$$

当估计误差在不同接收天线或端口之间相关时，它可能表现为结构化干扰，而不是独立白噪声。影响包括：

- 波束成形方向偏移。
- 预编码增益下降。
- 空间层间串扰增加。
- ZF/MMSE 检测性能下降。
- CSI 反馈中的秩、预编码矩阵选择错误。

如果误差协方差具有空间结构，接收机可能在某个弱奇异方向上产生更大的误差。建议按奇异向量投影统计：

$$
\mathbf{E}_{\mathrm{svd}}=\mathbf{U}^H(\hat{\mathbf{H}}-\mathbf{H})\mathbf{V}
$$

这有助于区分“平均 NMSE 较大”和“关键空间方向受损”两类问题。

若数据层预编码为 $\mathbf{W}$，估计误差在等效层域为：

$$
\widetilde{\mathbf{H}}_{\mathrm{eff}}
=\left(\widehat{\mathbf{H}}-\mathbf{H}\right)\mathbf{W}
=\widetilde{\mathbf{H}}\mathbf{W}.
$$

因此同一个端口域误差，在不同预编码方向下会产生不同的层域误差。若 $\mathbf{W}$ 将能量集中到误差较大的空间方向，端到端 BLER 可能明显恶化，即使端口域 NMSE 不变。

在近似独立数据层、层功率为 $R_{ss}$ 时，估计误差产生的等效干扰协方差为：

$$
R_{\mathrm{CSI},\mathrm{eff}}
=E\left[
\widetilde{\mathbf{H}}\mathbf{W}
R_{ss}
\mathbf{W}^H\widetilde{\mathbf{H}}^H
\right].
$$

该矩阵可以和热噪声、导频污染或 ICI 协方差一起提供给广义 MMSE 均衡器；但当误差与数据或预编码选择相关时，只能把它视为近似，而不能当作严格白噪声。

## 6. Massive MIMO 的特殊问题

大规模天线阵列提高了空间自由度，但也带来：

- 参考信号端口数和开销增加。
- 信道矩阵存储和估计计算量增加。
- TDD 系统依赖信道互易性校准。
- FDD 系统需要压缩 CSI 反馈。
- 上行导频复用可能产生 pilot contamination。

在 TDD 中，上下行信道互易性通常指传播信道的互易性，射频链路的幅相响应仍需要校准，不能把两者混为一谈。

### 导频开销与复杂度

在无空间先验、平坦静态信道和线性端口分离模型下，若需要估计 $N_t$ 个独立发射端口，训练矩阵至少需要满足：

$$
Q_{\mathrm{RS}}\geq N_t.
$$

若一个信道相干块包含 $Q_{\mathrm{coh}}$ 个可用资源，导频开销可近似写为：

$$
\rho_{\mathrm{RS}}
=\frac{Q_{\mathrm{RS}}}{Q_{\mathrm{coh}}}.
$$

这个下界不包含保护间隔、重复导频、端口切换和协议规定的额外资源。当天线数增加而相干块大小不变时，$\rho_{\mathrm{RS}}$ 可能成为吞吐量瓶颈。若已知发射空间协方差只有 $r_t$ 个显著特征方向，则在严格低秩模型中，未知发射空间维度可以由 $N_t$ 降为 $r_t$；但模型失配会把被截断方向重新表现为估计偏差。

对 $N_r\times N_t$ 信道和长度为 $Q$ 的训练序列，正交训练下矩阵 LS 的主要计算量近似为：

$$
\mathcal{C}_{\mathrm{LS}}
=O(N_rQN_t),
$$

因为 $\left(\mathbf{X}\mathbf{X}^H\right)^{-1}$ 可以在训练配置固定时预先计算。通用 LMMSE 若在观测维度 $d_y$ 上直接求逆，其代价通常包含：

$$
\mathcal{C}_{\mathrm{LMMSE}}
=O(d_y^3),
\qquad
d_y=N_rQ
$$

的矩阵分解项。实际系统因此倾向于采用空间低秩投影、Kronecker 分解或按接收天线/子载波分块，不能把全维 LMMSE 的理论最优性直接当作部署方案。

## 6.1 TDD 与 FDD 的估计边界

TDD 中，上行导频可以用于推断下行传播信道，但仍依赖上下行射频链路校准和时变假设。FDD 中上下行载波不同，不能直接把上行信道当作下行信道，通常需要 CSI-RS 测量和反馈。

因此，MIMO 估计实验应明确：

- 是直接估计当前下行端口信道，还是由上行 CSI 推断。
- 是否包含反馈延迟、量化和压缩误差。
- 预编码使用的 CSI 与实际发送时刻相差多久。

TDD 的传播互易性可以抽象为：

$$
\mathbf{H}_{\mathrm{UL,obs}}
=\mathbf{G}_{r,\mathrm{UL}}
\mathbf{H}_{\mathrm{prop}}^T
\mathbf{G}_{t,\mathrm{UL}},
$$

$$
\mathbf{H}_{\mathrm{DL,obs}}
=\mathbf{G}_{r,\mathrm{DL}}
\mathbf{H}_{\mathrm{prop}}
\mathbf{G}_{t,\mathrm{DL}}.
$$

这里的转置只表达传播路径的收发交换，$\mathbf{G}$ 矩阵表示上下行射频链路响应。只有在射频响应已经校准、频率差异可忽略且信道在切换间隔内近似不变时，才可以由上行观测推断下行传播信道。FDD 中上下行载波不同，通常不存在这样的直接转置关系。

### 6.1.1 互易性校准误差

若使用的校准响应存在误差：

$$
\widehat{\mathbf{G}}_r
=\mathbf{G}_r+\Delta\mathbf{G}_r,
\qquad
\widehat{\mathbf{G}}_t
=\mathbf{G}_t+\Delta\mathbf{G}_t,
$$

则一阶近似下，传播信道恢复误差包含：

$$
\Delta\mathbf{H}
\approx
\Delta\mathbf{G}_r\mathbf{H}_{\mathrm{prop}}\mathbf{G}_t
+\mathbf{G}_r\mathbf{H}_{\mathrm{prop}}\Delta\mathbf{G}_t.
$$

校准误差沿强传播方向传播，可能显著影响波束方向和零陷形成。实验应至少区分未校准、理想校准和带随机校准误差三种基线。

## 6.2 射频链路与传播信道

实际观测可分解为发射射频响应、传播信道和接收射频响应：

$$
\mathbf{H}_{\mathrm{obs}}
=\mathbf{G}_r\mathbf{H}_{\mathrm{prop}}\mathbf{G}_t
$$

其中 $\mathbf{G}_t$ 和 $\mathbf{G}_r$ 包含幅相失配。若估计目标是传播信道，必须校准射频链路；若估计目标是端到端等效信道，则这些响应应保留在 $\mathbf{H}_{\mathrm{obs}}$ 中。两种目标的 NMSE 不应直接比较。

如果只关心端到端解调，直接估计 $\mathbf{H}_{\mathrm{obs}}$ 可能比显式分离 $\mathbf{G}_r$、$\mathbf{H}_{\mathrm{prop}}$、$\mathbf{G}_t$ 更稳健；如果要做跨频段传播分析、阵列校准或波束迁移，则必须明确估计传播信道和硬件响应的分解假设。不可辨识的分解不应被报告为唯一物理解。

## 7. 评估指标

除整体 NMSE 外，还应评估：

- 每个端口和接收天线的 NMSE。
- 信道矩阵奇异值误差。
- 波束方向或预编码增益损失。
- 条件数分布。
- 估计 CSI 下的层间 BER/BLER。

信道矩阵的条件数为：

$$
\kappa(\mathbf{H})=\frac{\sigma_{\max}(\mathbf{H})}{\sigma_{\min}(\mathbf{H})}
$$

条件数越大，矩阵逆问题通常越不稳定。

还可以使用归一化信道重构误差：

$$
\epsilon_H=\frac{\|\hat{\mathbf{H}}-\mathbf{H}\|_F^2}{\|\mathbf{H}\|_F^2}
$$

以及子空间相似度评价预编码方向：

$$
\eta_{\mathrm{sub}}=\frac{\|\hat{\mathbf{V}}^H\mathbf{V}\|_F^2}{r}
$$

其中 $r$ 是比较的空间维度。它们与元素级 NMSE 结合使用，能更好解释 MIMO 性能。

若真实和估计的右奇异向量子空间分别由 $V_r$ 和 $\widehat{V}_r$ 张成，可以用投影矩阵距离评价预编码方向：

$$
d_{\mathrm{sub}}
=\left\|V_rV_r^H-\widehat{V}_r\widehat{V}_r^H\right\|_F.
$$

该指标不受子空间内部基向量旋转影响，比逐列比较奇异向量更合理。对已经归一化的真实波束 $\mathbf{w}$ 和估计波束 $\widehat{\mathbf{w}}$，还可以定义波束方向损失：

$$
G_{\mathrm{loss}}
=1-\left|\mathbf{w}^H\widehat{\mathbf{w}}\right|^2.
$$

当信道存在相位不定性时，应使用幅度平方内积或先对齐全局相位；否则同一个物理波束可能因为复数相位不同而被错误判为方向完全不一致。

## 7.1 CSI 反馈的误差链路

FDD 或压缩反馈场景中，接收端估计的 CSI 还要经过量化、压缩、反馈和重构：

$$
\hat{\mathbf{H}}_{\mathrm{gNB}}
=\mathcal{D}(\mathcal{Q}(\mathcal{C}(\hat{\mathbf{H}}_{\mathrm{UE}})))
$$

其中 $\mathcal{C}$、$\mathcal{Q}$ 和 $\mathcal{D}$ 分别表示压缩、量化和解码重构。应把本地估计误差、反馈误差和时间过期误差分开统计。

常见反馈指标包括：

- 信道重构 NMSE。
- 预编码向量夹角或子空间相似度。
- 波束成形增益损失。
- 反馈比特数和有效吞吐量。

反馈延迟 $\Delta t$ 会与信道时间相关性共同影响预编码。若预编码基于 $t$ 时刻的估计 CSI，而数据在 $t+\Delta t$ 发送，则实际层域信道为：

$$
\mathbf{H}_{\mathrm{eff}}[t+\Delta t]
=\mathbf{H}[t+\Delta t]\widehat{\mathbf{W}}[t].
$$

即使 $\widehat{\mathbf{H}}[t]=\mathbf{H}[t]$，当 $\Delta t$ 较大时也会产生预编码失配。反馈量化误差和时间老化应分别冻结或扫描，不能只用一个“CSI 误差”参数合并解释。

## 7.2 MIMO 估计到均衡的接口

均衡器至少需要知道：

- $\hat{\mathbf{H}}$ 的天线、端口和层顺序。
- 每个子载波和时间符号的有效 CSI 标志。
- 噪声或估计误差的协方差近似。
- 预编码矩阵是否已经包含在等效信道中。

若上述信息缺失，均衡器可能把端口信道再次乘以预编码矩阵，或把已经等效化的信道错误地逆变换。

对数据模型：

$$
\mathbf{y}
=\mathbf{H}_{\mathrm{eff}}\mathbf{s}+\mathbf{v},
$$

若层符号协方差为 $R_{ss}$、总等效干扰协方差为 $R_{vv}$，线性 MMSE 均衡器可写为：

$$
\mathbf{G}_{\mathrm{MMSE}}
=R_{ss}\widehat{\mathbf{H}}_{\mathrm{eff}}^H
\left(
\widehat{\mathbf{H}}_{\mathrm{eff}}R_{ss}
\widehat{\mathbf{H}}_{\mathrm{eff}}^H
+R_{vv}
\right)^{-1}.
$$

若只把 $R_{vv}$ 设置为热噪声 $\sigma_n^2\mathbf{I}$，而估计误差具有明显空间相关性，则均衡器会错误地分配不同空间方向的可靠度。近似条件下可使用：

$$
R_{vv}
\approx \sigma_n^2\mathbf{I}_{N_r}
+R_{\mathrm{CSI},\mathrm{eff}}
+R_{\mathrm{ICI}}
+R_{\mathrm{pilot\,contam}},
$$

但每一项都应说明是否由观测估计、由模型给定，还是仅用于仿真中的已知上界。

## 8. 与其他概念的关系

- **维度与信道域**：[[01 5G 物理层与信道模型]]定义层映射、端口映射和预编码；本页必须区分 $\mathbf{H}_{\mathrm{prop}}$、射频观测信道、端口域 CSI 与 $\mathbf{H}_{\mathrm{eff}}=\mathbf{H}_{\mathrm{port}}\mathbf{W}$。数组维度正确不等价于该矩阵可直接交给层域均衡器。
- **训练与可辨识性**：[[02 参考信号与导频设计]]中的[[DM-RS]]、[[CSI-RS]]和[[SRS]]提供多端口训练资源；[[LS 信道估计]]要求训练矩阵满秩且条件数可接受，[[LMMSE 信道估计]]可利用时频空间协方差。[[导频污染]]是多用户或端口训练不可分离造成的结构化偏差，不能只视为白噪声。
- **空间结构**：[[CDL 信道模型]]和[[空间相关性]]决定协方差、有效秩和可分离空间方向；[[MIMO 信道矩阵条件数]]将其转化为 ZF/MMSE 检测稳定性。相关性可帮助匹配的低秩估计，却也可能损失空间复用自由度。
- **反馈与预编码**：[[CSI-RS]]测量经[[CSI 反馈]]量化和延迟后用于预编码。量化、时间老化、端口/层转换和射频校准是不同的误差源，必须分别记录而不能并入单一 CSI NMSE。
- **均衡与性能**：[[06 OFDM 接收与频域均衡]]使用层域等效 CSI；[[MMSE 均衡]]中的 $R_{vv}$ 应区分热噪声、CSI 误差、ICI 和污染。[[07 信道估计误差与性能分析]]应同时报告端口域/层域 NMSE、条件数、每层 SINR、EVM 与[[BLER 与 BER]]。

## 待验证问题

所有实验应固定天线、端口、层和预编码维度，并保存完整域标签；否则“空间估计误差”无法解释为哪一种 CSI 的错误。

| 验证问题 | 对照设计 | 最低记录量 | 判定规则与入口 |
|---|---|---|---|
| 端口正交方式与开销 | 固定总训练 RE、总训练能量、信道实现与端口数；比较时分、频分、码分和可控非正交序列 | 训练矩阵秩、最小奇异值、条件数、端口串扰 NMSE、PAPR、缓存与每时隙计算量 | 满秩只能证明理论可辨识；若条件数恶化导致 NMSE 上升，应区分噪声增强和资源/功率变化。入口：[[DM-RS]]、[[09 仿真实验：MIMO 均衡]] |
| 空间相关性下估计与均衡收益 | 扫描 $R_t$、$R_r$ 或 CDL 角度扩展，分别比较 LS/LMMSE 与 ZF/MMSE；保持 SNR、层数和导频一致 | 端口/层域 NMSE、有效秩、条件数、每层 SINR、EVM、BLER | LMMSE 的 NMSE 收益和 MMSE 的检测收益需要分别报告；不能把空间相关性造成的秩损失误算为估计器退化。入口：[[空间相关性]]、[[MIMO 信道矩阵条件数]] |
| Massive MIMO 的低秩失配 | 用高维 CDL 或可控空间协方差生成真值，扫描低秩阶数、角度扩展与训练样本数 | 协方差特征谱、PSD 状态、端口/层域 NMSE、内存、在线延迟、最差层 SINR | 低秩模型必须在独立测试信道上评估；训练和测试共用生成器真值时标为 oracle。入口：[[LMMSE 信道估计]]、[[CDL 信道模型]] |
| 哪个 CSI 域的 NMSE 预测 BLER | 同时构造端口域、传播域和层域等效 CSI 估计；固定真实接收波形与均衡器 | 各域 NMSE、$\|\hat{\mathbf{H}}_{\mathrm{eff}}-\mathbf{H}_{\mathrm{port}}\mathbf{W}\|_F$、后均衡 SINR、BLER | 优先选择与均衡器实际输入域相同的误差指标；若端口域 NMSE 与层域 BLER 不相关，应检查预编码投影和误差方向。入口：[[信道估计误差]]、[[09 仿真实验：MIMO 均衡]] |
| 反馈延迟与量化 | 固定测量 CSI，独立扫描反馈比特数、码本误差和 $\Delta t$，再联合扫描 | 波束增益损失、层间干扰、CSI 年龄、预编码增益、BLER、反馈开销 | 即使测量 CSI 完美，时间老化仍可导致损失；量化和延迟不得合并为无来源的随机误差。入口：[[CSI 反馈]]、[[CSI-RS]] |
| 协方差 PSD 修正与接口选择 | 比较未修正、特征值截断、对角加载和不同最小特征值阈值；同时比较传播、端口和等效 CSI 接口 | 最小特征值、秩、NMSE、后验误差校准、均衡稳定性、BLER | 修正若改善数值可逆性但产生偏差，应报告 Pareto 取舍；接收机接口选择必须与参考信号及预编码关系一致。入口：[[空间相关性]]、[[MMSE 均衡]] |
