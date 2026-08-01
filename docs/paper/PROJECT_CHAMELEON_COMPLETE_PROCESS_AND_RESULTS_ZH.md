# Project Chameleon 完整研究过程与成果

版本：2026-08-01
性质：中文技术总报告、项目事实底稿与论文写作依据
研究状态：理论结果已冻结；轻量 full-binary MFE v3 已完成并成为当前本地数值主结果

> Project Chameleon 研究的不是“怎样把一个电池模型写得更复杂”，而是“一个复杂灵活资源最少必须向调度者披露什么信息，才能让外部合同在时间、激活和不确定性下仍然可信”。

---

## 摘要

复杂灵活资源通常不会把完整内部模型直接交给电网调度者。电池、光伏加储能、聚合资源和其他混合资源往往被压缩成一组功率范围、备用容量、爬坡能力或能量约束。压缩可以保护隐私、降低市场接口复杂度并提高计算效率，但也可能丢掉决定未来可行性的关键信息。

Project Chameleon 将 capability contract 定义为物理灵活性的 information projection，并围绕“信息压缩在给定运行语义下是否仍然精确、可交付和可组合”建立了一个逐层理论体系。项目从最小的两周期 discharge-only 电池反例出发，依次加入双向充放电、效率损耗、充放电互斥、terminal SOC、确定性光伏、弃光、备用来源、连续激活和有限情景树不确定性。每一步均保持模型尽可能小，并通过解析推导、3-6 周期精确枚举、显式内部 witness 和独立物理 replay 验证。

十八个命题最终收束为四个结构性主结果：

1. 精确的逐时局部能力不保证整条轨迹可行；
2. 物理转换效率和模式结构决定精确合同能否保持凸性；
3. 一次调用的 existential feasibility 不保证连续调用可组合；
4. 不确定性下，边际状态信息不足，情景对应关系和信息时序本身成为合同状态。

在数值部分，项目经历了四轮有记录的仪器修订。v1 和 v2 分别暴露容量算术遗漏、truth model 被过度缩减，以及保守合同漏掉弃光 recourse。v3 恢复了完整 24 小时有损双向物理模型，但 384-scenario extensive form 在本机计算预算内 unresolved。v4 证明连续松弛并不安全：备用条件化分支会利用 10.625 MW 同时充放电制造虚假灵活性。新的轻量 full-binary 复现实验进一步表明，正确方向不是删除物理结构，而是减少重复求解规模。

当前本地主实验保留 24 小时 horizon、完整充放电 mode binaries、损耗、弃光、真实 recourse、备用激活和 terminal SOC，只把网格缩为 6 个代表性 PV+BESS cells、construction scenarios 缩为 32、held-out paths 缩为每格 32 条，并固定共同随机种子。六个 C_full-32 全部达到 0.1% gap，求解时间为 2.19-60.10 秒。共 768 条 held-out line-path records，物理 replay、成本对账和 stage-2 求解均为零失败。C1 相比 C_ASSOC market proxy 降低 10.66%-13.94% 平均 realized cost；C1 距 full-binary C_full-32 仅 1.06%-2.55%。

项目的最终实践结论不是要求资源公开完整模型，而是披露足以定义下一步可行 continuation 的最小状态：局部功率与备用字段、明确激活语义、跨期能量包络、状态和 terminal boundary、效率约定；连续调用时增加 activation-conditioned reachable-state transition；要求随机保证时再增加 scenario correspondence、nonanticipativity、belief 和 remaining risk budget。

---

## 1. 用最直白的话解释这个项目

### 1.1 一个“看起来能做到”的承诺为什么可能是假的

设想一个电池告诉调度者：

- 第一小时最多可以放 1 MWh；
- 第二小时最多也可以放 1 MWh。

如果电池总共只有 1 MWh，这两句话分别看都是真的，但调度者不能同时在两个小时各取 1 MWh。问题不在于任何一句局部承诺造假，而在于两句承诺共同使用了同一份隐藏能量。

这就是 Project Chameleon 的起点：

> time-local truthfulness 不自动推出 trajectory feasibility。

### 1.2 为什么不能要求资源把所有内部信息全部公开

完整内部模型当然最安全，但代价也最大：

- 市场接口会变得技术专用；
- 聚合资源可能不愿暴露内部设备；
- 调度模型的维度和整数变量急剧增加；
- 资源每次内部结构变化都需要重新注册模型；
- 对调度者而言，大量细节可能没有边际价值。

因此真正的问题不是“公开还是隐藏”，而是：

> 哪些信息可以隐藏，哪些信息一旦隐藏就会破坏可行性或可组合性？

### 1.3 Chameleon 这个名字代表什么

Chameleon 强调同一个复杂资源可以针对不同运行语义呈现不同的外部能力表示：

- 静态调度只需要较少字段；
- 多周期调度需要跨期能量信息；
- 连续备用调用需要 post-activation state；
- 随机多阶段决策需要情景节点和信息时序。

合同不是资源永恒不变的“外壳”，而是相对于运营用途的信息投影。

---

## 2. 中央研究问题与研究边界

### 2.1 中央问题

给定完整物理可行集 F_full 和调度者可见变量 y，能力合同可以理解为投影：

$$
C_exact = Pi_y(F_full).
$$

实践中可能使用：

$$
C_inner subseteq C_exact subseteq C_outer.
$$

项目研究三类问题：

1. 什么信息投影是 exact 的？
2. 如果无法 exact，哪些 inner 或 outer approximation 是诚实的？
3. 当合同被跨时间、跨激活或跨情景复用时，什么状态才是 sufficient？

### 2.2 为什么从小模型开始

项目刻意先使用 2-6 周期模型，因为小模型允许：

- 穷举所有可行轨迹；
- 手工构造最小 counterexample；
- 给出双向集合包含证明；
- 显式列出内部 witness；
- 在优化器之外独立 replay。

小模型用于验证结构性命题，不用于估计现实市场总体效应。

### 2.3 明确没有加入的内容

理论阶段未加入：

- transmission network；
- unit commitment；
- generalized function model；
- dynamic frequency response；
- grid-forming dynamics；
- large-scale multi-resource market simulation。

这些内容会增加应用范围，但不是回答最小信息问题所必需。

---

## 3. 统一模型语言

### 3.1 电池变量

| 符号 | 含义 |
|---|---|
| e_t | 时段 t 开始时的 SOC 或储能量 |
| c_t | 充电功率 |
| d_t | 放电功率 |
| p_t = d_t - c_t | 电池净注入，正值为向外放电 |
| P_ch, P_dis | 最大充电和放电功率 |
| eta_c, eta_d | 充电和放电效率 |
| E_min, E_max | SOC 上下界 |
| E_0 | 初始能量 |
| E_term | terminal energy requirement |

Lossy 电池的状态递推为：

$$
e_(t+1) = e_t + eta_c c_t Delta_t - d_t Delta_t / eta_d.
$$

### 3.2 Hybrid 变量

| 符号 | 含义 |
|---|---|
| w_t | 可用 PV |
| q_t | 弃光 |
| g_t = w_t - q_t | 实际送出的 PV |
| h_t = g_t + d_t - c_t | hybrid 对外净注入 |
| r_t^+, r_t^- | 上调和下调备用 |

### 3.3 合同与真值集合

| 名称 | 含义 |
|---|---|
| C0 exact-marginal | 精确逐时局部投影的笛卡尔积 |
| C1 prefix | 加入跨期 prefix energy 信息 |
| C_ASSOC | CAISO 式电池 SOC 规则的 market proxy |
| C_full det | 显式 SOC 的确定性 lifted physical model |
| C_full | 两阶段完整信息与真实 recourse 模型 |
| C_WS | 每条路径事先已知的 wait-and-see 成本下界 |

### 3.4 四种集合关系

- Exact：合同集合等于完整物理模型的目标变量投影。
- Inner：合同接受的每个点都可实现，但可能拒绝真实能力。
- Outer：包含全部真实能力，但可能接受不可实现点。
- Relaxed：通过删除互斥或非凸结构得到的计算模型，通常是 outer。

### 3.5 两种激活语义

- Isolated：每个备用调用都从同一 nominal base state 单独测试。
- Sequential：第一次调用后的实际 SOC 成为第二次调用的初始状态。

这两个语义不能混用。很多“备用可行”结论只对 isolated call 成立。

---

## 4. Phase I：discharge-only 电池

### 4.1 最小两周期反例

考虑：

- 两个时段；
- 初始可用能量为 1；
- 每时段最大放电为 1；
- 无充电；
- 无损耗。

逐时投影允许：

$$
0 <= p_1 <= 1, 0 <= p_2 <= 1.
$$

其笛卡尔积接受 (p_1,p_2) = (1,1)，但完整 SOC 递推给出：

$$
e_3 = E_0 - p_1 - p_2 = -1,
$$

因此不可行。

### 4.2 C0 的根本问题

C0 exact-marginal 在每个时段都说真话，却没有告诉调度者：

- 两个时段共享同一份能量；
- 当前动作会减少未来能力；
- 备用激活也消耗同一份 SOC。

因此：

$$
C_full subsetneq C0.
$$

### 4.3 加入一条 prefix cut

加入：

$$
sum_(s<=t) p_s Delta_s + r_t tau <= E_0 - E_min.
$$

它要求截至任意前缀的累计能量和当前备用持续能量不超过可用预算。

### 4.4 Proposition 1

在以下严格假设下：

- battery-only；
- discharge-only；
- deterministic；
- lossless 或极简单效率处理；
- fixed reserve semantics；
- no charging opportunity；
- no PV；
- no repeated calls；
- terminal coupling 不超过 prefix budget；

reserve-conditional prefix constraints 是完整 lifted model 在 (p,r) 上的 exact projection。

### 4.5 为什么这个命题必须写得窄

正确表述：

> For the Phase-I discharge-only model, reserve-conditional prefix constraints provide an exact projection.

错误扩张：

> Prefix contracts exactly represent storage capability.

后续 charging、losses 和 sequential activation 都会破坏宽泛版本。

### 4.6 Gap disappearance

如果：

- 电池能量非常充足；
- horizon 很短；
- 功率约束先于能量约束绑定；

则 C0、C1 和 C_full 可能在关注区域内相同。这说明信息价值具有 regime dependence，而不是所有场景都必须披露同样多字段。

### 4.7 这一章应该怎样理解

C0 的问题不是任何一个逐时区间说了假话，而是把分别真实的区间做笛卡尔积以后，丢掉了“这些动作共享同一份能量”的联合关系。局部真实性和轨迹可组合性是两件不同的事。

Prefix cut 的作用就是把隐藏的能量记忆补回来。对于两周期例子，逐时约束只给出 p_1 <= 1 和 p_2 <= 1；prefix constraint 还会给出 p_1 + p_2 <= 1，于是 (1,1) 被正确排除。

之所以要检查每一个前缀，而不是只检查最终总量，是因为物理系统不能用未来充电修复过去已经发生的 SOC 越界。某条轨迹可能最终回到合法电量，但中途已经低于 E_min；这种轨迹仍然不可执行。

因此 Proposition 1 建立的是一个受限基准：在 discharge-only、deterministic、single-call 的简单模型中，累计能量前缀就是充分状态。以后每加入一种新语义，都要重新检查这份状态是否仍然充分。

---

## 5. 双向充放电：Proposition 2 与 3

### 5.1 为什么 upper prefix 不够

加入充电后：

$$
-P_ch <= p_t <= P_dis.
$$

旧的 upper energy prefix 只防止过度放电，不能防止过度充电突破 E_max。

例如 E_0 = E_max = 1，p_1 = -0.5 表示充电 0.5。它不会违反放电预算，却会把 SOC 推到 1.5。

### 5.2 Proposition 2：lossless two-sided prefix exactness

Lossless 时：

$$
e_(t+1) = e_t - p_t Delta_t.
$$

因此需要同时约束：

$$
E_0 - E_max <= sum_(s<=t) p_s Delta_s <= E_0 - E_min.
$$

在 deterministic、lossless、bidirectional、fixed single-call reserve 且无额外 terminal coupling 的受限模型中，two-sided reserve-conditional prefix formulation 等于完整物理投影。

### 5.3 Lossy efficiency 改变映射

定义 signed depletion map：

$$
phi(p) =
  p / eta_d,  if p >= 0;
  eta_c p,    if p < 0.
$$

精确 prefix 必须累计 phi(p)，而不是 p。

当 eta_c = eta_d = 0.8：

- p = 0.5 实际消耗 0.625 MWh；
- p = -0.6 实际增加 0.48 MWh。

所以 naive lossless net-energy envelope 既可能错误接受，也可能错误拒绝。它 neither inner nor outer。

### 5.4 Proposition 3：exact net-injection projection 可以非凸

在 lossy bidirectional battery 且充放电互斥时，可以找到两个可行轨迹 p^A、p^B，其 midpoint 因 SOC upper bound violation 不可行。

因此：

$$
Pi_p(F_physical)
$$

一般不必是凸集。

### 5.5 两个 corollaries

1. 在该模型类中，没有额外 lifted 或 discrete variables 时，continuous convex net-injection contract 一般不能同时 exact 和 complete。
2. 删除 charge/discharge complementarity 会扩大投影：

$$
Pi_p(F_physical) subsetneq Pi_p(F_relaxed).
$$

同时充放电可以人为耗散能量，从而制造虚假 SOC feasibility。

### 5.6 电网侧与电池侧的两本账

无损时，累计净注入 sum p_t Delta_t 可以直接恢复 SOC。正值表示累计净放电，负值表示累计净充电。两侧 prefix bound 分别表示最多能放多少和最多能充多少。

有损时必须区分：

- 电网侧账本：sum p_t Delta_t，表示电网实际收入或支出的能量；
- 电池侧账本：sum phi(p_t) Delta_t，表示电池内部真正减少或增加的能量。

两本账的差异是能量损耗。它首先是 MWh 损失；只有再结合分时电价、备用价格或退化成本，才能转化为货币成本。

非凸性的准确含义是：两个端点轨迹分别可行，不保证连接它们的线段上每个平均轨迹都可行。损耗本身并非单独充分条件；真正造成困难的是方向相关效率、充放电互斥、跨期 SOC 和上下界共同作用。若真实投影非凸，单一 continuous convex contract 一般只能在 outer optimism、inner conservatism 或增加 mode variables 之间取舍。

---

## 6. Terminal SOC：Proposition 4 与 5

### 6.1 Terminal requirement 的意义

加入：

$$
e_(T+1) >= E_term.
$$

这不是当前功率能力，而是一项未来保留义务。

### 6.2 Discharge-only lossless

可用总能量从：

$$
E_0 - E_min
$$

收缩为：

$$
E_0 - E_term.
$$

### 6.3 Proposition 4

在 lossless bidirectional Phase-I 模型中，exact terminal projection 等于：

$$
two-sided prefix set intersection terminal cut.
$$

Terminal cut 为：

$$
sum_t p_t Delta_t <= E_0 - E_term.
$$

该条件不会破坏 compact convex polytope 结构。

### 6.4 Proposition 5

在 lossy complementary 模型中，terminal cut 变为：

$$
sum_t phi(p_t) Delta_t <= E_0 - E_term.
$$

Exact projection 仍为 mode-aware、piecewise-linear，并且一般非凸。Terminal SOC 不会自动恢复凸性。

### 6.5 Relaxation relation

加入 terminal target 后仍有：

$$
Pi_p(F_physical^term) subseteq Pi_p(F_relaxed^term),
$$

且包含关系可以严格。

### 6.6 Terminal SOC 与 reserve 的区别

Terminal SOC 可以理解为面向未来保留的 energy reserve，但它不等同于逐时备用功率 r_t。E_term 的单位通常是 MWh；r_t 的单位通常是 MW，只有 r_t tau 才是一次持续 tau 的调用所需能量。

运行过程中仍然要求：

$$
E_min <= e_t <= E_max.
$$

只有最终时刻额外要求：

$$
e_(T+1) >= E_term.
$$

因此 E_term 不会替代所有中间时刻的 E_min。它只把最终时刻的有效下界提高到 max(E_min,E_term)，并把最终累计放电上界从 E_0-E_min 收紧到 E_0-E_term。

Prefix constraints 保证沿途合法，terminal cut 保证做完当前任务以后还留下约定能量。两者缺一不可：一条轨迹可以中途越界、后来充电并最终满足 terminal target，但它仍然不是合法物理轨迹。

---

## 7. Deterministic PV+BESS：Proposition 6-10

### 7.1 Stage A：must-take PV

无弃光时：

$$
h_t = w_t + b_t.
$$

### 7.2 Proposition 6

固定且 operator-visible 的 PV trajectory w 下：

$$
H_A^exact = w + B^exact.
$$

Must-take PV 只是 battery feasible set 的 affine translation，不产生新的几何。它主要带来 contract versioning 问题：合同必须说明自己基于哪条 PV trajectory 构造。

### 7.3 Stage B：加入 curtailment

允许：

$$
h_t = w_t - q_t + d_t - c_t,
0 <= q_t <= w_t.
$$

给定 h_t，battery net power 不再唯一，而是位于一个 interval。

### 7.4 Proposition 7：reachable-interval projection

从 SOC interval [L_t,U_t] 出发，对给定 hybrid injection h_t，可以精确计算下一时段 reachable SOC interval。

轨迹 h 可行，当且仅当：

- 每个时段的 feasible battery-power interval 非空；
- 每一步 reachable SOC interval 非空。

这说明 net injection 决定的是 reachable state set，而不是唯一 SOC。

### 7.5 Lossless convexity

Lossless 时 lifted model 为线性模型，hybrid projection 是 convex polytope。连续 charge/discharge relaxation 与 complementary model 在 net-injection projection 上一致。

### 7.6 Proposition 8：curtailment 不消除 lossy nonconvexity

即使允许弃光，lossy complementary PV+BESS 的 exact hybrid net-injection projection 仍可能非凸。

原因是：

- 弃光提供额外 decomposition；
- 但某些 midpoint 即使完全弃光仍会过度充电；
- simultaneous charge/discharge relaxation 仍能通过人为耗散修复。

### 7.7 Proposition 9：相同 h，不同 SOC

设 w_1 = 1、h_1 = 0：

1. 全部弃光，电池 idle；
2. 送出 PV 同时给电池充电。

二者对外 h_1 相同，但下一 SOC 不同。

因此 hybrid net injection 不是 internal state trajectory 的 sufficient statistic。

### 7.8 Proposition 10：reserve-source non-identifiability

相同的 (h,r^+) 可以由：

- 释放弃光；
- 减少充电；
- 增加电池放电；

提供。

相同的 (h,r^-) 可以由：

- 增加弃光；
- 增加充电；
- 减少放电；

提供。

这些来源对 post-call SOC 的影响不同。Aggregate reserve 可以作为 isolated existential projection 的坐标，但不能唯一决定激活后的状态。

### 7.9 为什么弃光以后只能得到 SOC 区间

不允许弃光时，q_t=0，因此：

$$
b_t = h_t - w_t.
$$

当 w_t 和 h_t 都已知，电池净功率唯一，充电或放电行为以及下一期 SOC 都能确定。Must-take PV 只是把电池可行域整体平移 w，不改变其形状。

允许弃光时：

$$
b_t = h_t - w_t + q_t,
0 <= q_t <= w_t.
$$

因此给定 h_t 后：

$$
b_t in [h_t-w_t,h_t] intersection [-P_ch,P_dis].
$$

例如 w_t=3、h_t=2，同一个对外结果可以由“不弃光并充电 1”“弃光 1 且电池不动”或“弃光 2 并放电 1”实现。电网看到的 h_t 都是 2，但 SOC 分别上升、不变和下降。

所以外部净注入不再决定唯一内部状态，只决定一组可能的电池动作。把这组动作通过 SOC 递推映射，就得到下一期 reachable interval [L_(t+1),U_(t+1)]。逐期传播这些区间，可以判断整条 hybrid injection 轨迹是否至少存在一种内部实现。

---

## 8. Sequential reserve：Proposition 11-14

### 8.1 两种语义的本质区别

Isolated 语义问：

> 如果只调用这一次，资源能否完成？

Sequential 语义问：

> 第一次调用真实发生以后，资源还能否完成第二次？

### 8.2 最小 two-witness counterexample

第一次 upward reserve 可以通过：

- Witness A：释放弃光，SOC 不变；
- Witness B：电池放电，SOC 下降。

两者暴露相同的 first-stage tuple，也都支持第一次调用。但第二次调用需要电池能量时，A 可行、B 不可行。

### 8.3 Proposition 11

Aggregate one-shot reserve tuple (h,r^+,r^-) 在 deterministic lossless PV+BESS 中也不一定是 sequential activation 的 sufficient Markov state。

因此：

$$
one-shot feasible does not imply sequentially composable.
$$

### 8.4 Memoryless continuation impossibility

只读取当前 aggregate tuple 的规则无法同时做到：

1. 接受所有 first-call feasible witnesses；
2. 保证第二次调用。

它必须：

- 披露 post-activation state 或 source information；或者
- 保守地拒绝一部分第一次可行 witness。

### 8.5 Proposition 12：lossless set-valued Markov contract

在受限 lossless PV+BESS 中，activation-conditioned reachable SOC interval 是 exact path-conditioned sequential feasibility 的 sufficient state：

$$
S_(t+1) = T_(alpha_t)(S_t; h_t, r_t^+, r_t^-).
$$

合同由一个 set-valued transition map 表示。

### 8.6 Proposition 13：lossy transition 仍可用 interval，但必须 mode-aware

在当前一维 deterministic 模型中，lossy complementarity 本身不一定使 scalar reachable-SOC set 断裂；沿固定 activation path，interval 仍可充分。

但是 external transition relation：

- piecewise linear；
- direction dependent；
- 在 aggregate contract variables 中一般非凸。

因此 globally exact convex contract 仍可能需要 lifted mode information 或 conservatism。

### 8.7 Proposition 14：source labels 的作用

Source label sigma 将 any-source contract 细分为：

$$
C_seq^sigma subseteq C_seq^any,
C_seq^any = union_sigma C_seq^sigma.
$$

Source label 可以消除 Proposition 11 中的特定 ambiguity，但粗标签不一定唯一决定 SOC。Exact update 仍可能需要 pre-call SOC 和足够的 battery-energy information。

### 8.8 第八章的完整逻辑

一次调用结果相同，不代表内部状态相同。最小例子中，第一次上调 1 MW 可以来自释放弃光，也可以来自电池放电。两者对外都成功，但前者 SOC 不变，后者 SOC 下降；第二次调用需要电池时，未来可行性立刻分化。

因此 (h,r^+,r^-) 不是 sufficient Markov state，即使 PV 已知、没有损耗也不够。只读取 aggregate tuple 的 memoryless rule 必须在两种错误之间选择：接受全部 first-call witnesses 会误接未来不可行状态；为了保证未来而全部拒绝，又会浪费真实能力。

Proposition 12 的修复不是每次都披露一个唯一 SOC，而是更新 activation-conditioned reachable set：

$$
S_t -> S_(t+1) = T_(alpha_t)(S_t;h_t,r_t^+,r_t^-).
$$

如果实际动作完全可见，S_(t+1) 可以缩成单点；如果内部来源仍有歧义，就保留区间。关键是第二次调用从更新后的状态出发，而不是重新使用最初 nominal SOC。

有损时，区间传播仍可能成立，但 T 必须用 phi(p) 区分充放电方向。Source label 可以把“释放弃光”“减少充电”“增加放电”拆开，使更新更准确；粗标签若没有调用前 SOC、持续时间和实际电池能量，仍不一定足够。

---

## 9. Stochastic extension：Proposition 15-18

### 9.1 为什么不直接上大型 stochastic UC

项目只加入：

- one PV+BESS；
- 3-4 periods；
- finite PV scenario tree；
- sequential reserve；
- robust、chance 和 adaptive recourse 三种语义。

目标仍然是研究 information sufficiency，而不是市场规模。

### 9.2 Proposition 15：unconditional interval 和 marginal belief 都不够

构造两个 stochastic states：

- 它们有相同 unconditional SOC support；
- 它们有相同 marginal SOC distribution；
- 但 SOC 与 future-scarcity node 的对应关系不同。

一个 continuation success probability 为 1，另一个为 1/2。

所以仅保留 SOC interval 或 marginal belief 会丢失关键 dependence。

### 9.3 缺失的信息

缺失的是：

- observation history 或 scenario-tree node；
- hidden SOC；
- future PV continuation；

之间的 joint correspondence。

### 9.4 Proposition 16：robust Markov state

有限树 robust dynamic programming 的 sufficient state 可写为：

$$
{node n, reachable set S_n, transition T_n, child relation}.
$$

Child intersection 强制当前一个共同动作支持所有可能 continuation，从而实现 nonanticipativity。

### 9.5 Proposition 17：chance contract 需要 probability 和 risk state

Chance-constrained continuation 一般需要：

$$
(node, joint/node-conditioned SOC belief, remaining risk budget beta_n).
$$

只有 support 无法计算 violation probability；只有 probability 而没有 remaining risk budget，则连续决策可能时间不一致。

### 9.6 Proposition 18：leaf-wise witnesses 是 strict outer benchmark

如果每个 leaf 可以提前知道自己的未来，则每个 leaf 都能选择不同 root action。

Nonanticipative policy 必须在分叉前选择同一个 root action。

因此：

$$
C_NA subseteq C_FI,
$$

且可以严格包含。

这就是 wait-and-see、EVPI 与真实 multistage feasibility 之间的合同解释。

### 9.7 为什么边际 SOC 分布仍然不够

设未来只有两个等概率节点：PV 充足 G 和 PV 短缺 S。两个 stochastic states 都满足 Pr(SOC=0)=Pr(SOC=1)=1/2。

- 状态 A：G 对应 SOC=0，S 对应 SOC=1；PV 充足时不需要电池，PV 短缺时恰好有电，因此 continuation success probability 为 1。
- 状态 B：G 对应 SOC=1，S 对应 SOC=0；电量出现在不需要它的节点，PV 短缺时反而没电，因此成功概率只有 1/2。

两个状态的 SOC support、SOC marginal distribution 和 PV marginal distribution 都相同，差别只在 SOC 与 future-scarcity node 的联合对应关系。因此不确定性下的状态必须包含 observation history、scenario-tree node、node-conditioned SOC 和 future continuation 的 correspondence。

Robust contract 需要一个共同 root action 支持所有仍可能发生的 child nodes，这就是 child intersection 和 nonanticipativity。Chance contract 还要知道概率与剩余风险预算 beta_n；只知道 support 无法算违约概率，只知道概率而不记录已经用掉的风险，会导致跨期风险预算失控。

Leaf-wise wait-and-see 允许每条路径提前知道未来并选择不同 root action，因此只能作为成本下界或 outer information benchmark，不能当作真实可执行合同。

---

## 10. 十八个命题如何收束为四个主结果

### Main Result I：局部真实性不等于轨迹可组合性

覆盖：

- Proposition 1；
- lossless prefix exactness；
- terminal cuts；
- memoryless Cartesian-product failure。

核心句：

$$
time-local truthfulness does not imply trajectory feasibility.
$$

### Main Result II：物理转换结构决定合同几何

覆盖：

- Proposition 2-5；
- lossless convex exactness；
- lossy direction-aware mapping；
- complementarity nonconvexity；
- strict continuous outer relaxation；
- terminal extension；
- deterministic PV translation 和 curtailment variants。

核心句：

$$
lossless restricted model -> compact convex exact abstraction;
$$

但：

$$
lossy + mode exclusivity -> exact projection may be nonconvex.
$$

### Main Result III：one-shot feasibility 不等于动态可组合性

覆盖：

- Proposition 9-14；
- hidden hybrid decomposition；
- reserve source ambiguity；
- two-call counterexample；
- reachable-state transition；
- source labels。

核心句：

$$
one-shot feasible does not imply sequentially composable.
$$

### Main Result IV：不确定性下 information pattern 本身就是 state

覆盖：

- Proposition 15-18；
- unconditional state failure；
- node-conditioned sets；
- belief and risk budget；
- nonanticipativity；
- leaf-wise outer benchmark。

核心句：

$$
state marginal information does not imply stochastic continuation sufficiency.
$$

### 四个结果的递进关系

四个主结果分别修复四种不同的信息遗漏：

1. Main Result I：逐时边界遗漏共享能量，需要 prefix memory；
2. Main Result II：净注入遗漏方向相关转换模式，需要 phi 与 mode information；
3. Main Result III：one-shot tuple 遗漏调用后状态，需要 reachable-state transition；
4. Main Result IV：边际状态遗漏情景对应和信息时序，需要 node-conditioned stochastic state。

因此项目不是简单地给合同不断加约束。某些新增字段会缩小过宽的 outer contract，排除虚假能力；另一些字段会恢复保守 proxy 错误拒绝的真实 recourse。目标始终是让合同集合尽量贴近真实物理投影，同时保留足够 continuation information。

---

## 11. 信息合同层级

项目最终得到的 sufficient-state evolution 为：

$$
local bounds
  -> prefix energy envelopes
  -> activation-conditioned reachable-state sets
  -> node-conditioned stochastic states.
$$

| 运营语义 | 被隐藏的关键信息 | 最小候选合同状态 |
|---|---|---|
| 单时段静态调度 | 局部功率范围 | power/reserve bounds |
| 多周期调度 | 共享能量预算 | prefix energy envelopes |
| terminal obligation | horizon-end energy | terminal cut 或 terminal field |
| 单次备用 | branch deliverability | reserve-conditioned envelope |
| 连续备用 | post-call SOC | activation-conditioned reachable set |
| hybrid source | flexibility 来源 | source label 或等价 state transition |
| robust uncertainty | node-state correspondence | node-conditioned sets |
| chance constraint | probability 与已用风险 | joint belief + remaining risk budget |
| multistage recourse | information timing | scenario tree + nonanticipativity |

### 11.1 层级不是要求所有资源公开所有字段

信息合同层级必须与运营用途匹配。单时段静态调度可能只需要功率与备用边界；多周期调度才需要 energy memory；连续调用才需要 post-call state transition；只有市场要求 stochastic guarantee 时，scenario node、belief、risk budget 和 nonanticipativity 才成为必要字段。

所以“需要披露多少”没有统一维数。正确答案是一条 operational-semantics-dependent disclosure band：从最少字段开始，直到主要物理 failure 消失；再从 full model 向下投影，直到继续删除字段会破坏 continuation。

---

## 12. 为什么必须做数值实验

理论能够证明某个信息字段在逻辑上必要，但不能告诉我们：

- 这个字段在典型参数下值多少钱；
- 哪些 regime 中差距几乎消失；
- 更丰富合同是否只是理论正确但经济价值很小；
- market proxy 相比推荐合同损失多少。

因此项目引入 Minimal Frontier Experiment，试图在 C0 与 full information 之间测量 cost-reliability frontier。

### 12.1 理论必要性不等于经济价值一定很大

理论反例可以证明 C0 在某些参数下错误，但不能说明错误每天发生还是极少发生，也不能说明修复后节省 0.1% 还是 20%。如果电池能量充足、horizon 短、PV 波动小或备用要求低，理论差距可能在关注区域内消失。

MFE 因此同时观察成本与可靠性。简单 outer contract 可能给出较低的日前成本，却在真实执行中支付昂贵修复；过度保守 inner contract 可能可靠，却拒绝大量真实能力；理想合同应在相同可靠性下更便宜，或在相同成本下更可靠。

数值实验的任务不是再次证明 Proposition，而是测量：哪些理论必要字段在代表性 regime 中具有实质边际价值，以及推荐合同距离完整物理信息边界还有多远。

---

## 13. MFE v1：正确停止，错误仪器

### 13.1 原设计

早期 MFE 使用：

- 四台火电机组；
- 一个 PV+BESS；
- 24 小时；
- 三档不确定性；
- 三种电池时长；
- 三档 initial SOC；
- 两档 reserve；
- 54 cells。

### 13.2 暴露的三个问题

F1：未先检查静态容量算术。
装机 headroom 不足以满足最高备用档，这在跑场景前即可发现。

F2：truth model 被 gate 过度缩减。
充电、弃光、场景内火电 redispatch 和经济 penalty 被删除，导致电池被迫独自吸收 PV 缺口。

F3：frontier 在设计上退化。
C1 被要求对过度受限模型 exact，C_full 退化为逐场景 witness，实际只剩 C0 与其余线比较。

### 13.3 为什么停止是正确的

停止发生在只看到可行性计数、未看 comparative gap 时。项目没有根据结果就地调参，而是重新设计仪器。

v1 的失败属于 experimental design failure，不是被比较合同的结果。F1 会把装机 headroom 不足误认为信息合同失败；F2 会把删除真实 recourse 后产生的不可行误认为电池能力不足；F3 则让不同合同实际上测量相同或不公平的问题。继续运行只会产生更多无解释力的数据。

---

## 14. MFE v2：保守合同为什么会变成空集

### 14.1 v2 修复

恢复 Blueprint 中的完整 truth model：

- bidirectional battery；
- eta = 0.95；
- charge/discharge complementarity；
- PV curtailment；
- battery and thermal redispatch；
- imbalance settlement；
- reserve shortfall penalty；
- load shedding；
- spill；
- terminal SOC。

### 14.2 v2 C1 的错误

注册的 charging-side box budget 假设 PV 上偏必须全部由电池吸收。

但 truth model 允许：

$$
0 <= q_t <= w_t.
$$

PV 上偏可以付出较低 curtailment cost 直接弃掉，不需要占用 battery energy headroom。

### 14.3 空集证书

在部分参数下，错误的双侧 band 要求电池吸收约 497 MWh，而 4h 电池能量预算仅约 200 MWh。

这不是普通 conservatism，而是合同漏掉真实 recourse channel。

### 14.4 可发表的机制

> 如果 conservative inner contract 没有表示真实 recourse channel，其能力损失可以达到 100%。

v2 的关键教训是：inner contract 不等于自动正确。若合同假设所有 PV 上偏必须由电池吸收，它会要求约 497 MWh charging headroom；真实 4h 电池只有约 200 MWh，于是合同变成空集。但 truth model 可以直接弃光，所以真实可行域并不为空。

这不是普通的“小幅保守”，而是合同把系统实际拥有的 recourse channel 删除了。设计 inner approximation 时，必须先完整列出资源应对不确定性的物理动作，再决定哪些动作可以安全压缩。

---

## 15. MFE v3：recourse-aware C1 与 runtime wall

### 15.1 v3 唯一结构修订

删除错误的 charging-side band energy budget：

- PV 上偏由 curtailment 保证；
- 放电侧保留 worst-direction energy protection；
- downward reserve 由减放电、充电和弃光依次提供；
- 保留 terminal cut。

### 15.2 v3 完成的验证

- 24h deterministic lossy bidirectional reconciliation；
- C0、C1 1/99、C1 5/95、C_full det 对账；
- independent replay；
- C1 safety audit；
- inside-band zero physical failure；
- regression tests 保持绿色。

### 15.3 为什么仍然停止

384-scenario extensive-form MILP 在 900 秒注册上限内 unresolved。

停止原因是计算可执行性，而不是 C1 safety failure 或 comparative result 不利。

### 15.4 2026-08-01 的修正结论

后续诊断证明，v3 的 24 小时完整物理设计本身可以保留。把 construction scenarios 从 384 降至 32，并把网格固定为 duration {1h,2h,4h} x reserve {5%,20%} 后，六个 full-binary C_full-32 全部在单线程本机完成。

最慢的 1h/5% 格点约 60.10 秒，1h/20% 约 40.10 秒，其余四个格点约 2-5 秒。全部满足 0.1% relative-gap gate，并完成 32/32 construction replay。

因此 v3 的准确结论不是“完整模型在本机不可运行”，而是：

> 384-scenario 重复规模不可执行；32-scenario 的完整 binary v3 extensive form 可执行。

---

## 16. V4：连续松弛为什么失败，以及为什么不再作为主路线

### 16.1 原希望

如果 positive round-trip loss 和 positive throughput cost 使 simultaneous charge/discharge 严格劣势，则删除 mode binaries 可能得到 exact LP。

### 16.2 最小市场反例

在 1h battery、75% initial SOC、20% reserve 的 deterministic benchmark：

| 指标 | Full MILP | 全模式 LP relaxation |
|---|---:|---:|
| objective | 201,327.897881 USD | 201,322.091094 USD |
| mode binaries | 72 | 0 |
| max simultaneous power | 0 MW | 10.625 MW |

Relaxed down-activation branch 在 hour 1 同时充放 10.625 MW，在 hour 18 同时充放 0.125 MW。

### 16.3 三段式结论

1. LP objective 比 MILP 便宜 5.8068 USD；
2. LP 合同依赖 physical model 禁止的同时充放；
3. 固定 LP stage-1 后恢复真实 physical recourse，成本上升到 204,203.165340 USD。

所以：

> relaxed model 更优，不代表 relaxed contract 更好；它可能先制造不可实现的灵活性，再在真实物理中付出更高修复成本。

### 16.4 Partial-integrality sandwich certificate

算法：

1. 从 LP 开始；
2. 找出 simultaneous charge/discharge 的 branch-hours；
3. 只在这些位置恢复 binary；
4. 重复求解；
5. 如果最终所有 relaxed positions 都满足 complementarity，则 mode recovery 得到完整 MILP feasible point；
6. partial relaxation lower bound 与 feasible upper point 相等，从而给出 exact certificate。

### 16.5 N=32 staircase

三个 sentinel 均通过：

| Sentinel | Final binaries | Adaptive solve time | Replay |
|---|---:|---:|---|
| S1: 1h, high uncertainty, 20% reserve | 736 | 72.04 s | 32/32 |
| S2: 2h, medium uncertainty, 20% reserve | 736 | 7.96 s | 32/32 |
| S3: 4h, low uncertainty, 5% reserve | 672 | 6.57 s | 32/32 |

因此 freeze N = 32，N = 16 不再运行。

### 16.6 v4 的最终定位

v4 证明了一项仍然重要的负结果：正损耗与正 throughput cost 不保证 LP 自动避免同时充放电。Relaxed objective 更低不代表 relaxed contract 更好；它可能先制造物理不可实现的灵活性，再在真实 recourse 中支付更高修复成本。

Partial-integrality sandwich 在 lower bound 与 full-MILP feasible upper point 相等时可以提供精确证书，但它增加了额外算法层。既然新的 6-cell、32-scenario 实验可以直接求解完整 binary MILP，v4 不再作为当前主实验求解器，只保留为 relaxation counterexample 和未来大规模加速研究。

---

## 17. 最终实验怎样轻量化而不改物理

完整 54-cell、218 held-out paths、384-scenario construction 和 per-cell C0 fitting 会产生大量重复 scenario MILP。本地瓶颈来自重复规模，而不是单个 24 小时 truth model。

当前设计遵循“先缩重复数量，最后才考虑缩物理模型”的原则：

- 保留 24 小时 horizon；
- 保留 full charge/discharge binaries；
- duration 只取 1h、2h、4h；
- reserve 只取 5%、20%；
- initial SOC 固定 50%；
- PV error sigma 固定 0.08；
- construction scenarios 每格 32 条；
- paired held-out paths 每格 32 条；
- 合同线固定为 C0-fixture、C1、C_ASSOC、C_full-32；
- construction seed 2026080101；
- held-out seed 2026080104；
- one process、one numerical thread。

轻量化只降低覆盖范围和统计精度，不删除损耗、弃光、真实 recourse、备用激活、terminal SOC 或 mode exclusivity。

---

## 18. 最终 full-binary lightweight experiment

### 18.1 数据与真实性

输入来自公开 RTS-GMLC reproducible synthetic benchmark，并固定到 upstream commit：

$$
3ece0d3725c844056132393ee252b3083dd4eab4.
$$

这些文件是真实存在、可核验的公共 benchmark，但不是 observed CAISO operating data。

### 18.2 四条线

| Line | 含义 |
|---|---|
| C0-fixture | 静态参数 (15,35,35,50)，不做 per-cell refit |
| C1 | recourse-aware 1/99 intertemporal inner envelope |
| C_ASSOC | CAISO-style SOC rule market proxy |
| C_full-32 | 32 construction scenarios 上的 full-binary nonanticipative extensive form |

C_full-32 不提前看到 held-out path。它和其他合同一样，在 held-out evaluation 前冻结 stage-1 decision，再使用同一个真实 stage-2 optimizer。

### 18.3 Full-binary 求解规模与时间

每个 C_full-32 包含 2,304 个 binary variables，约 24,440 个变量和 27,172 条约束。

| Duration | Reserve | Solve time | Relative gap | Construction replay |
|---:|---:|---:|---:|---:|
| 1h | 5% | 60.10 s | 0.0014% | 32/32 |
| 1h | 20% | 40.10 s | 0.00002% | 32/32 |
| 2h | 5% | 3.96 s | 0.0392% | 32/32 |
| 2h | 20% | 2.90 s | 0.0026% | 32/32 |
| 4h | 5% | 4.69 s | 0.0131% | 32/32 |
| 4h | 20% | 2.19 s | approximately 0% | 32/32 |

六格合计 full-binary solve time 为 113.94 秒，全部达到 0.1% relative-gap gate。

### 18.4 数据完整性

$$
6 cells x 32 paths x 4 lines = 768 records.
$$

| 检查 | 结果 |
|---|---:|
| duplicate cell-path-line keys | 0 |
| incomplete four-line pairs | 0 |
| construction physical replay failures | 0 |
| construction cost reconciliation failures | 0 |
| held-out physical replay failures | 0 |
| held-out cost reconciliation failures | 0 |
| held-out stage-2 unresolved | 0 |

---

## 19. 最终成本结果

### 19.1 C1 相比 C_ASSOC

负值表示 C1 更便宜。

| Duration | Reserve | Mean C1-C_ASSOC | 95% paired interval | Relative saving |
|---:|---:|---:|---:|---:|
| 1h | 5% | -25,501 USD | [-43,359, -7,643] | 11.32% |
| 1h | 20% | -34,192 USD | [-51,580, -16,805] | 13.94% |
| 2h | 5% | -23,753 USD | [-41,676, -5,830] | 10.66% |
| 2h | 20% | -33,253 USD | [-49,771, -16,735] | 13.57% |
| 4h | 5% | -23,993 USD | [-41,853, -6,133] | 10.80% |
| 4h | 20% | -31,916 USD | [-46,863, -16,969] | 13.05% |

所有六个 registered cells 的 paired interval 均排除零。

### 19.2 C1 距 full-binary C_full-32

| Duration | Reserve | Mean C1-C_full-32 | 95% paired interval | Relative gap |
|---:|---:|---:|---:|---:|
| 1h | 5% | 2,104 USD | [-296, 4,503] | 1.06% |
| 1h | 20% | 2,266 USD | [511, 4,021] | 1.09% |
| 2h | 5% | 2,192 USD | [-970, 5,355] | 1.11% |
| 2h | 20% | 3,648 USD | [1,330, 5,965] | 1.75% |
| 4h | 5% | 2,113 USD | [-1,142, 5,367] | 1.08% |
| 4h | 20% | 5,280 USD | [3,473, 7,088] | 2.55% |

部分区间包含零，所以不能宣称 C_full-32 在每格都显著优于 C1；但均值方向一致，而且 C1 已明显接近 full-binary benchmark。

[[FIGURE: results/mfe_v3_lightweight_full_binary/figures/full_binary_frontier.png]]

图 1. 六个代表性格点相对 full-binary C_full-32 的平均 realized-cost gap。每格 32 条 paired held-out paths；图中为描述性均值，不是总体市场推断。

### 19.3 解释

C1 在所有代表性 regime 中回收了 market proxy 与 full-binary benchmark 之间的大部分成本差距。

这支持：

> intertemporal disclosure 在当前 benchmark 中具有实质经济价值。

但它不支持：

> CAISO 采用该合同一定节省 10.66%-13.94%。

---

## 20. Delivery、replay 与 sequential 含义

当前 768 条 held-out records 中，四条线全部通过物理 replay 与成本对账。Isolated up/down shortfall 仅为约 1e-13 的数值容差量级，所以成本改善没有用一次调用不交付换取。

但是，这仍不代表合同自动支持任意连续调用。第 8 章的解析反例继续成立：如果市场需要 repeated reserve，就必须显式更新 activation-conditioned reachable state。

当前成本实验衡量的是固定 stage-1 contract 在一条实际 PV path 上的真实 recourse 成本，不是对所有未来多次调用序列的 robust guarantee。旧 lean fixed-policy two-call stress 仍可作为历史机制证据，但不与本次 32-path full-binary成本表混合成同一统计结果。

---

## 21. 我们最终回答了“需要披露多少”

### 21.1 实践 lower edge

Energy-limited resource 至少应披露：

1. scheduled net-injection envelope；
2. up/down reserve envelope；
3. activation duration、timing 和 call count；
4. intertemporal energy envelope；
5. initial/current/terminal state boundary；
6. efficiency 与 conversion convention；
7. guarantee type：exact、inner 或 outer。

如果这些字段不齐，项目中的 verified counterexamples 反复出现 trajectory 或 activation failure。

### 21.2 Deterministic sequential upper edge

当资源会被连续调用，再增加：

1. activation-conditioned reachable-state transition；
2. source attribution，当不同来源产生不同 future state consequence。

超过这一层后，披露完整 component schedule、device identity 或全部内部 topology，目前没有已验证的边际收益。

### 21.3 Stochastic extension

只有当市场要求 stochastic guarantee 时，再按语义增加：

- scenario-node correspondence；
- nonanticipativity；
- joint state-scenario belief；
- remaining risk budget。

### 21.4 为什么不是一个固定数字

“需要披露几维”取决于合同用途：

- 一次静态调度可能只需少数维度；
- 多周期调度必须加入 energy memory；
- 连续调用必须加入 state transition；
- 随机多阶段保证必须加入 information state。

所以正确答案是一个 operational-semantics-dependent disclosure band，而不是统一的 C5 或 C9。

---

## 22. 信息维度的边际成本与边际收益

项目提出的决策原则：

1. 从 C0 向上增加字段，直到主要 physical failure 消失；
2. 从 C_full 向下投影，直到继续删除字段开始破坏 continuation；
3. 在这两个边界之间测量经济成本；
4. 保留能显著降低成本或 failure 的字段；
5. 拒绝只增加接口复杂度、却没有已验证边际价值的字段。

在当前实验中：

- 从 static market proxy 到 intertemporal C1，成本收益很大；
- C1 相比 C_ASSOC 降低 10.66%-13.94% 平均 realized cost；
- C1 距 full-binary C_full-32 仍有 1.06%-2.55% 均值 gap；
- one-shot fields 到 sequential state transition 的必要性由 stress test 和解析反例共同支持；
- 更深 stochastic fields 的经济价值尚未由 powered market study 定价。

---

## 23. 项目中最重要的负结果

1. Exact marginals 的 Cartesian product 不 exact。
2. Lossless prefix 不能直接用于 lossy battery。
3. Lossy complementary projection 可能非凸。
4. Continuous relaxation 可能使用 artificial dissipation。
5. Terminal SOC 不会恢复凸性。
6. Hybrid net injection 不确定 internal SOC。
7. Aggregate reserve 不确定 flexibility source。
8. One-shot existential contract 不能直接连续复用。
9. Unconditional SOC interval 不足以支持 stochastic continuation。
10. Marginal SOC belief 仍可能丢失 scenario correspondence。
11. Leaf-wise witnesses 忽略 nonanticipativity，是 outer benchmark。
12. 漏掉 curtailment recourse 的 conservative contract 可以直接变成空集。
13. Positive losses 与 throughput cost 不足以保证 reserve-conditioned relaxation exact。

这些负结果共同定义了合同压缩不能越过的边界。

---

## 24. 项目中最重要的正结果

1. Restricted discharge-only 模型存在 exact prefix projection。
2. Restricted lossless bidirectional 模型存在 exact two-sided prefix projection。
3. Terminal requirement 可在受限模型中通过 terminal cut 吸收。
4. Must-take deterministic PV 是 affine translation。
5. Curtailable hybrid feasibility 可通过 exact reachable-interval recursion 判断。
6. Lossless sequential model 可用 reachable-SOC interval 作为 exact Markov state。
7. Node-conditioned reachable sets 支持 exact robust dynamic programming。
8. Chance semantics 可以通过 belief 加 remaining risk budget 表达。
9. 32-scenario full-binary extensive form 在六个轻量 cells 上全部完成并通过 replay。
10. C1 在所有六个 cells 中显著缩小相对 C_ASSOC 的 realized-cost gap，并接近 C_full-32。

---

## 25. Reviewer 风险与当前回答

| 可能质疑 | 当前回答 | 仍然不支持的部分 |
|---|---|---|
| 范围太广 | 四个主结果分别列出独立假设，不包装成万能 theorem | general resource theorem |
| 电池假设太窄 | 电池和 PV+BESS 是 canonical model classes | wind/hydro exact extension |
| 与 storage projection 文献重叠 | prefix exactness 降为基础；sequential 和 stochastic sufficiency 为主线 | 仍需 manuscript 中逐条件对比 |
| 是 definition dressed as theorem | 有最小反例、双向集合包含、严格 inclusion 和枚举 | taxonomy 本身不能当 theorem |
| POMDP/DP 早已知道 belief state | 贡献是指出 marginal SOC belief 仍不够，以及合同字段解释 | 不声称 belief sufficiency 本身新颖 |
| 小 horizon 不够 | 用于 exact structural verification | 不代表 market-scale effect |
| 数值不够大 | 明确是 representative-regime validation | 54-cell powered inference |
| CAISO 解释过度 | C_ASSOC 明确叫 market proxy | observed CAISO performance |

---

## 26. 数据、代码与复现

### 26.1 当前 GitHub publication package

仓库仅保留：

- formal modeling documents；
- final paper plan；
- current research reports；
- source code；
- 79 tests；
- necessary RTS-GMLC CSV inputs；
- consolidated raw results；
- paired statistics；
- final figure；
- N=32 certificate JSON。

未发布：

- source paper PDFs；
- stopped-run archives；
- intermediate cell checkpoints；
- local caches。

### 26.2 测试

最终测试命令：

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
PYTHONPATH=src python -m pytest -q tests
```

结果：

$$
79 passed.
$$

### 26.3 Full-binary lightweight execution and analysis

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
PYTHONPATH=src python -m chameleon.mfe_v3_lightweight all

MPLCONFIGDIR=/tmp/chameleon-mpl
PYTHONPATH=src python -m chameleon.mfe_v3_lightweight_analysis
```

### 26.4 关键文件

| 文件 | 用途 |
|---|---|
| README.md | 仓库入口 |
| PROJECT_PROGRESS.md | 当前状态 |
| BLUEPRINT.md | 原始研究蓝图 |
| docs/modeling | Proposition 1-18 正式推导 |
| docs/paper/THEORY_DISTILLATION_AND_PAPER_PLAN.md | 最终论文结构 |
| docs/paper/RECOMMENDED_DISCLOSURE_SPECIFICATION.md | 建议披露规范 |
| docs/research/MFE_LEAN_PAPER_VALIDATION_REPORT.md | 最终数值报告 |
| src/chameleon/mfe_v3_lightweight.py | full-binary 轻量执行器 |
| src/chameleon/mfe_v3_lightweight_analysis.py | 验证、配对统计与主图生成 |
| results/mfe_v3_lightweight_full_binary/v3full_*.json | 六个 cell 原始结果 |
| results/mfe_v3_lightweight_full_binary/paired_statistics.csv | 配对统计 |
| results/mfe_v3_lightweight_full_binary/regime_summary.csv | cell-line 汇总 |
| results/mfe_v3_lightweight_full_binary/figures/full_binary_frontier.png | 主结果图 |

---

## 27. 当前项目真正建立了什么

已经建立：

- restricted exact projection theorems；
- minimal analytical counterexamples；
- exact/inner/outer set relations；
- lossy complementarity nonconvexity；
- strict relaxation gap；
- sequential reachable-state sufficiency；
- stochastic correspondence insufficiency；
- 3-6 period exact enumeration；
- 3-4 period scenario-tree enumeration；
- independent physical and cost replay；
- 24h deterministic truth model；
- representative synthetic cost frontier。

尚未建立：

- 所有 flexible resources 的 universal theorem；
- observed CAISO cost saving；
- network-constrained generalization；
- unit commitment interaction；
- wind 和 hydro 专门模型；
- GFM 或 frequency dynamics；
- full powered 54-cell market inference；
- 每个 disclosure field 的精确货币价值。

---

## 28. 最终结论

Project Chameleon 从一个简单问题开始：

> 一个复杂资源可以隐藏多少内部信息？

项目最终得到的答案是：

> 可以隐藏所有不会改变调度者所需 continuation 的内部细节；必须披露足以使该 continuation 在给定时间、激活和信息语义下保持定义良好的最小状态。

对于多周期 energy-limited resource，这通常意味着 prefix energy memory。
对于连续激活，这意味着 activation-conditioned reachable state。
对于 stochastic multistage operation，这意味着 scenario correspondence 和 information timing。

最终 numerical evidence 进一步表明，这种信息并非只有理论价值。在六个代表性 PV+BESS regimes 中，recourse-aware intertemporal C1 contract 相比 C_ASSOC market proxy 降低 10.66%-13.94% 平均 realized cost，并且仅比 full-binary C_full-32 高 1.06%-2.55%。全部 32-scenario C_full-32 在完整 mode binaries 下完成，768 条 held-out records 均通过物理 replay 与成本对账。

因此，项目的统一原则可以写成：

> Capability contracts are information projections of physical flexibility. As operational semantics progress from static scheduling to sequential execution and stochastic recourse, exact and composable contracts require progressively richer sufficient state representations.

---

## 附录 A：Proposition 1-18 总表

| 编号 | 主题 | 核心结论 | 最终定位 |
|---:|---|---|---|
| 1 | discharge-only prefix | restricted model 中 prefix exact | supporting proposition |
| 2 | lossless bidirectional | two-sided prefix exact | supporting proposition |
| 3 | lossy complementarity | exact net-injection projection may be nonconvex | Main Result II |
| 4 | lossless terminal | prefix + terminal cut exact | appendix proposition |
| 5 | lossy terminal | mode-aware terminal projection remains nonconvex | appendix proposition |
| 6 | must-take PV | hybrid set is affine translation | lemma |
| 7 | curtailed PV | reachable-interval recursion exact | supporting proposition |
| 8 | lossy curtailed hybrid | nonconvexity survives curtailment | corollary/support |
| 9 | hybrid state | net injection does not identify SOC | example/proposition |
| 10 | reserve source | aggregate reserve does not identify SOC transition | supporting proposition |
| 11 | repeated calls | one-shot tuple not Markov sufficient | Main Result III |
| 12 | lossless sequential | reachable interval is exact Markov state | Main Result III |
| 13 | lossy sequential | interval state sufficient on path, transition mode-aware | supporting proposition |
| 14 | source labels | labels refine transition and remove ambiguity | corollary |
| 15 | uncertain state | unconditional interval and marginal SOC belief insufficient | Main Result IV |
| 16 | robust tree | node-conditioned sets are robust-Markov sufficient | Main Result IV |
| 17 | chance state | joint belief and remaining risk budget required | supporting proposition |
| 18 | nonanticipativity | leaf-wise recourse is strict outer benchmark | Main Result IV |

---

## 附录 B：受限 exactness 结果的假设矩阵

| 特征 | P1 | P2 | P4 | P7 | P12 |
|---|---|---|---|---|---|
| deterministic | yes | yes | yes | yes | yes |
| battery-only | yes | yes | yes | no | no |
| PV+BESS | no | no | no | yes | yes |
| discharge-only | yes | no | no | no | no |
| bidirectional | no | yes | yes | yes | yes |
| lossless | yes | yes | yes | optional via phi | yes |
| curtailment | no | no | no | yes | yes |
| terminal cut | limited | no | yes | no | no |
| repeated calls | no | no | no | no | yes |
| uncertainty | no | no | no | no | no |

---

## 附录 C：论文主线建议

正文保留：

1. 两周期 memoryless counterexample；
2. restricted prefix exactness；
3. lossy midpoint nonconvexity；
4. reserve-conditioned LP relaxation counterexample；
5. sequential two-witness counterexample；
6. stochastic correspondence counterexample；
7. four-level information hierarchy；
8. full-binary lightweight frontier figure；
9. recommended disclosure table。

附录保留：

- 3-6 period enumeration；
- terminal SOC case splits；
- must-take PV translation；
- repeated relaxation variants；
- full Proposition 1-18 inventory；
- replay and checksum details。

---

## 附录 D：建议论文题目

首选：

> What Must Flexible Resources Reveal? Information, Geometry, and Composability of Capability Contracts

候选二：

> Capability Contracts as Information Projections: Sufficient State for Composable Flexibility

候选三：

> From Local Flexibility to Composable Contracts: Intertemporal, Sequential, and Stochastic Information States
