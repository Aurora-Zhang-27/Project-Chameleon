# 文献核对：N≤3 定理与 N=4 反例（2026-09-29）

**对象：** `N3_THEOREM_N4_COUNTEREXAMPLE_ZH.md` 中的命题 1、定理 2、引理 3、定理 4、例 A/B。二维定理的检索见 09-25 总结（已归档）§3；储能与控制方向的第一轮检索见 `research_gate_20260905/Chameleon_复杂度方向排除_20260925.md`。

**结论先说：**
- **已知的工具：** 三明治定理（F4）、卷积（F3），以及引理 3(a)(b)（由三明治定理直接推出）。论文中应作为工具引用，不当成贡献。
- **没有找到先例的部分：** 命题 1、引理 3(c)(d) 的三维闭式、“N≤3 成立、N=4 失败”的分界、定理 4 在储能问题上的结论、例 B。
- **最近的相关工作都不覆盖我们的结果：**
  - 储能 g-polymatroid 系列只处理逐路径集合；
  - Evans–Tindemans–Angeli 只处理“先放电、后回充”两阶段；
  - Xie & Chen 的精确方法是指数级的；
  - 离散凸分析里最接近的是 Moriguchi–Murota 关于 L 凸集之和的 {0,±1} 描述，但对象不同。

**“没找到”不等于“已排除”。** 这一轮有三本关键的书读不到全文，见 §5。

---

## 0. 逐项结论

| 我们的结论 | 最近的已知结果 | 判断 |
|---|---|---|
| F4 实值三明治定理 | Frank 1982；实值版本的公式见 Murota 2016 讲义第 38 页（本轮已亲自核对） | **已知**，作为工具引用 |
| F3 向量卷积保持子模 | 子模系统按向量的 reduction，是标准运算（Fujishige 书第 3 章一带） | **已知**，本轮没有核到书中页码 |
| 引理 3(a) 单点紧界 β(i) = min_{S∋i}[b(S) − a(S∖i)]；(b) β(V) = b(V) | 由 F4 直接推出，没有找到逐字相同的陈述 | **按工具引理处理**，不主张新意 |
| 命题 1：（多拟阵 ∩ 反多拟阵）+ 盒与超平面之交，有显式 {0,±1} H-表示 | 最接近：Moriguchi–Murota 2110.10445 定理 4.1（两个 L 凸集之和，由 x(J) − x(I) ≤ γ 描述）；Danilov–Koshevoy 定理（幺模向量组给出的边方向类在 Minkowski 和下封闭） | **没找到先例**，对象和结论都不同，见 §1 |
| 引理 3(c)(d) 与分界：子模/超模描述的紧界，N=3 时仍子模/超模，N=4 时不成立 | Frank–Király–Pap–Pritchard（g-polymatroid 的全对偶层状刻画，没有维数结论）；Moriguchi–Murota §6.3（一般 M♮₂ 的描述函数不必子模/超模） | **没找到先例**，见 §2 |
| 定理 4：N≤3 双向异构储能，因果盒式承诺下可兑现集合的精确 O(T) 递推 | Mukhi 等 2503.23458、2504.00484、2509.16134（逐路径）；Evans–Tindemans–Angeli 2110.08549（两阶段）；Angeli–Dong–Strbac 2203.08659（只放电，双向列为开放）；Xie & Chen 2508.14477（精确法指数级）；Elsaadany & Almassalkhi 2606.01562（充分条件） | **没找到先例**，见 §3 |
| 例 B：N=4 真实递推出现混号 facet | 没有看到任何储能因果可兑现集合的非子集面反例 | **没找到先例** |
| 复杂度的背景（N 作为输入） | Atamtürk–Zhang 2007：两阶段鲁棒网络流，分离问题在二部图上 NP-hard，在全序或树形网络上可解；Gottschalk 等 2018：鲁棒流随时间，可行性验证 NP-hard | 只作背景，与我们的结论不冲突，见 §4 |

---

## 1. 命题 1：Minkowski 和之后的法向量

**我们的结论：** K = P(b) ∩ Q(a)（b 子模，a 超模，不要求交叉条件），P_y = {p ∈ [−C,D] : p(V) = y}。K + P_y 由同号子集约束加上

  e(A) − e(B) ≤ b(A∪M) − a(B∪M) + D(A) + C(B)

描述，其中 A、B、M 两两不交。

**已知结果逐一对比：**

- **Murota 的运算综述（1907.09161）：**
  - 表 4 列出：M♮ 凸集在 Minkowski 和、投影、限制、与整数盒取交之下封闭，在一般取交之下不封闭。
  - 综述没有讨论 M♮₂（两个 M♮ 之交）与 M♮ 的 Minkowski 和，也没有讨论“多拟阵 ∩ 反多拟阵”这类不满足交叉条件的集合。
- **Danilov–Koshevoy 定理（据 Murota–Tamura 2312.01822 定理 3.1）：**
  - 若 A 是幺模矩阵，那么“每个面的线性包都由 A 的某些列张成”的多面体类，在 Minkowski 和之下封闭。它约束的是**边方向**，不是 facet 法向量。
  - 我们的 K 的边可以是 (1,−1,−1)（蓝图 §4.1 的 K₀），不属于 M♮ 的边方向组。而全部子集向量在 N≥3 时不是幺模的：det[1₁₂, 1₁₃, 1₂₃] = −2。
  - 所以命题 1 不是这个定理的推论。它也解释了为什么一般情形会出现 (2,1,1) 这类法向量（蓝图 §4.2）。
- **Moriguchi–Murota 2110.10445：**
  - 定理 4.1：两个 L 凸集的 Minkowski 和（L₂ 凸集）由 x(J) − x(I) ≤ γ(C) 描述，其中 |I| = |J|、I ∩ J = ∅，系数都在 {−1,0,+1} 中。形式上与命题 1 相近。
  - 但它的对象是 L 凸集之和，约束要求 |I| = |J|。我们的对象是“M♮₂ 的一个特殊子类”加上一个 M 凸集，约束是一般的 1_A − 1_B，并且依赖 b 子模、a 超模。
- **2312.01822、2110.10445、Murota 综述** 这三篇都没有给出“M♮₂ + M 凸集”的描述。

**判断：** 没有找到命题 1 的先例。写论文时应引用 Moriguchi–Murota 定理 4.1 和 Danilov–Koshevoy 作为背景，并说明两点不同：我们约束的是 facet 法向量而不是边方向；我们处理的是不满足交叉条件的三明治集合。

---

## 2. 引理 3 的维数分界

**我们的结论：** 对 K = P(b) ∩ Q(a)（b 子模、a 超模，描述不要求紧），N=3 时紧界仍子模/超模，并有闭式；N=4 时不一定成立。

**已知结果：**
- **Frank–Király–Pap–Pritchard（EGRES TR-2012-03，Math. Program. 2014）：**
  - 一个多面体是 g-polymatroid，当且仅当它有“全对偶层状”（TDL）的线性表示；判断任意给定系统是否 TDL 是 NP-hard；但判断一个线性规划是否定义 g-polymatroid 有多项式算法。
  - 他们讨论的是任意 Q(p,b) 是否为 g-polymatroid。我们的 H3″ 集合一般不是 g-polymatroid（交叉条件可以失败），而引理 3 讨论的是它们的紧界是否子模。两者是不同的问题。
  - 报告中没有与维数相关的结论。
- **Moriguchi–Murota 2110.10445 §6.3：** 连续 M♮₂ 多面体定义为两个 g-polymatroid 之交，描述函数取两者的 max/min，不必子模/超模。这支持蓝图 §4.2 的判断“H3″ 是 M♮₂ 的真子类”，但没有讨论我们这个子类。
- **EGRES Open 的 g-polymatroid 词条：** 只列了定义和已知刻画，没有涉及交集的紧界。
- **定向检索**“intersection of two g-polymatroids”加“dimension three / n ≤ 3 / four elements”：没有相关结果。

**判断：** 没有找到先例。引理 3(a)(b) 在我们的文档里本来就是工具，这里再确认一次。**真正可能的新内容是 (c)(d) 和 N=4 的失败。**

---

## 3. 储能：因果兑现的精确刻画

逐篇核对到摘要或正文关键句：

| 文献 | 处理的问题 | 与定理 4 的区别 |
|---|---|---|
| Mukhi, Loho, Abate 2503.23458（v2，2025-06） | 用 g-polymatroid 精确计算聚合灵活性（多面体的 Minkowski 和） | 确定性、逐路径；不涉及不确定请求或因果执行 |
| Mukhi & Abate 2509.16134 | EV 灵活性加网络约束；分解程序 | 分解时需要事先知道整条聚合曲线（原文：“Given this optimal aggregate load profile … we focus on disaggregating”），不是在线的；不讨论区间承诺 |
| 2504.00484（温控负荷的 g-polymatroid） | 推广到带耗散的储能 | 仍是逐路径 |
| Evans, Tindemans, Angeli 2110.08549（IEEE TSG 2022） | 带回充保证的储能聚合；调度是因果的 | 原文限定请求“先一段放电，再一段回充”；不允许同一时段区间跨 0 或任意换号 |
| Angeli, Dong, Strbac 2203.08659 | 只放电（或只充电）、部分可用；显式反馈策略 | 双向功率被列为开放问题 |
| Xie & Chen 2508.14477（v1） | 多阶段鲁棒 TSO–DSO 灵活性聚合；精确法、内近似、外近似 | 精确法随时段数指数增长；没有子集和或 polymatroid 结构 |
| Elsaadany & Almassalkhi 2606.01562 | 异构电池群的可实现性保证 | 在优先级控制器下的线性充分条件；异构的精确刻画列为开放 |
| Liu 等 2609.03252（IEEE TSG 2026） | 异构 DER 用于备用调度的聚合 | 多面体投影加“灵活性损失”，属于近似，不涉及因果兑现 |
| 2111.02395、2501.04508（09-25 已查） | 精确聚合（只充电、逐路径）；同构线性模型 | 已在 09-25 的文档中排除 |

**判断：** 没有找到“双向异构储能在因果盒式承诺下，可兑现集合精确刻画”的结果，N≤3 或任何固定 N 都没有；也没有看到 N=4 的结构性反例。**最近的邻居是 Evans–Tindemans–Angeli 2022**（因果、有回充，但限定两阶段），论文中应当明确和它比较。

---

## 4. 运筹与控制的类比（背景）

- **Atamtürk & Zhang 2007（Oper. Res.）：** 两阶段鲁棒网络流。第一阶段可行性由指数多条约束刻画；分离问题在二部图上 NP-hard；第二阶段网络为全序（批量问题）或树形时可解。我们的问题是**多阶段**（每个时段都能调整），每个时段的结构是“多台设备共享一个聚合请求”。它可以作为“N 作为输入时可能困难”的背景，但不能直接推出我们问题的复杂度。
- **Gottschalk 等，“Robust flows over time: models and complexity results”（Math. Program. 2018）：** 在动态鲁棒设定下，连验证候选解的可行性都是 NP-hard。同样只作背景。
- **鲁棒可控不变集：** 一般线性系统的计算方法是投影法、提升表示或内外近似，没有看到针对“积分器加和约束”这类储能结构的精确子模结论。09-25 的检索结论不变。

---

## 5. 没能核对到的部分（风险）

1. **三本书没有读到全文：** Frank《Connections in Combinatorial Optimization》（2011）第 14 章、Fujishige《Submodular Functions and Optimization》（2005）、Murota《Discrete Convex Analysis》（2003）。引理 3(a)(b) 类的公式，以及“g-polymatroid 与平面或盒之交”的紧界公式，最可能出现在这三本书里。**建议借助图书馆或请 Yize 帮忙确认**，重点查 Frank 第 14 章关于 Q(p,b) 在不满足交叉条件时的讨论。
2. **IEEE 全文不可访问：** Evans–Tindemans–Angeli 2022 的期刊版可能比 arXiv 版多内容。本轮按 arXiv 版核对。
3. **Frank 1982 原文：** 只核到出版信息和 Murota 讲义的转述，没有读到原文定理编号。
4. **bisubmodular 多面体：** 它们的约束形如 x(A) − x(B) ≤ f(A,B)，与命题 1 的形式相同。但我们的 K 可以有 (1,−1,−1) 这样的边，而 Minkowski 和保留加数的边方向，所以 K+P_y 一般不会是 bisubmodular 多面体。这里用到“bisubmodular 多面体的边只沿 e_i、e_i ± e_j 方向”这一刻画，本轮**没有核到原文**（Ando–Fujishige 1996；Fujishige 2014），论文中如果要提，需要先查证。
5. **检索工具的限制：** 网页检索只覆盖英文开放资源；中文期刊和会议论文没有覆盖。

---

## 6. 对论文写法的建议

- **工具部分：** 三明治定理（Frank 1982，实值版本）、卷积、引理 3(a)(b) 放在预备知识，不作为贡献。
- **主要贡献按新意排序：**
  1. 定理 4（N≤3 精确递推，附带因果选择器和复杂度）；
  2. 例 B 与 N=4 的失效机制；
  3. 命题 1（任意 N 的单请求 {0,±1} 描述）；
  4. 引理 3(c)(d) 作为定理 4 的数学核心。
- **必须比较的文献：** Evans–Tindemans–Angeli 2022（最近的邻居）、Angeli–Dong–Strbac 2022（双向开放）、Xie & Chen 2025（指数精确法）、Mukhi 等（逐路径 g-polymatroid）、Moriguchi–Murota 2110.10445（{0,±1} 描述的离散凸分析背景）、Danilov–Koshevoy（Minkowski 和与幺模性）。
- **措辞：** 新意只能写“据我们检索所及未见”，并在投稿前完成 §5 第 1 项的核对。

---

## 7. 检索记录（09-29）

**关键词组合：**
- polymatroid ∩ contrapolymatroid、sandwich、tight bounds
- M♮ 与 M♮₂ 的 Minkowski 和
- bisubmodular 多面体
- Frank discrete separation 的实值版本
- 交叉条件不成立时的 Q(p,b)
- g-polymatroid 之交与维数
- 因果或非预见的聚合灵活性，2025–2026
- g-polymatroid 与储能的因果、在线情形
- 鲁棒多阶段网络流与 flows over time
- 鲁棒可控不变集与积分器、储能
- Atamtürk–Zhang
- Evans、Angeli、Tindemans 的回充框架
- 2026 年的储能精确可行域

**读到正文或关键段落的：**
- 1907.09161（表 4）
- 2312.01822（定理 3.1 与定义）
- 2110.10445（定理 4.1、§6.3）
- EGRES TR-2012-03（本地提取全文后检索）
- Murota 2016 讲义（第 38 页）
- 2110.08549（正文关键句）
- 2509.16134（§IV）

**只读到摘要的：** 2503.23458、2508.14477、2609.03252、Atamtürk–Zhang 2007、Gottschalk 等 2018。

PDF 文本用本地的标准库脚本提取（zlib 解压内容流），数学符号有乱码，但关键词和陈述可以辨认。

**来源（09-29；10-07 新增的见 §8）：**
- [Murota, A Survey of Fundamental Operations on Discrete Convex Functions of Various Kinds (1907.09161)](https://arxiv.org/abs/1907.09161)
- [Murota & Tamura, Note on Minkowski Summation and Unimodularity in Discrete Convex Analysis (2312.01822)](https://arxiv.org/abs/2312.01822)
- [Moriguchi & Murota, Note on the Polyhedral Description of the Minkowski Sum of Two L-convex Sets (2110.10445)](https://arxiv.org/abs/2110.10445)
- [Frank, Király, Pap, Pritchard, Characterizing and Recognizing Generalized Polymatroids (EGRES TR-2012-03)](https://egres.elte.hu/tr/egres-12-03.pdf)
- [EGRES Open: Generalized polymatroid](https://oldlemon.cs.elte.hu/egres/open/Generalized_polymatroid)
- [Murota, Discrete Convex Analysis II (2016 lecture slides)](https://kzmurota.fpark.tmu.ac.jp/paper/160510BonnHCMecon2web.pdf)
- [Frank, An Algorithm for Submodular Functions on Graphs (1982)](https://www.sciencedirect.com/science/article/pii/S0304020808724460)
- [Schoot Uiterkamp, A characterization of simultaneous optimization, majorization, and (bi)submodular polyhedra (2201.06596)](https://arxiv.org/abs/2201.06596)
- [Mukhi, Loho, Abate, Exact Characterization of Aggregate Flexibility via Generalized Polymatroids (2503.23458)](https://arxiv.org/abs/2503.23458)
- [Mukhi & Abate, Polymatroidal Representations of Aggregate EV Flexibility Considering Network Constraints (2509.16134)](https://arxiv.org/abs/2509.16134)
- [Aggregate Flexibility of Thermostatically Controlled Loads using Generalized Polymatroids (2504.00484)](https://arxiv.org/abs/2504.00484)
- [Evans, Tindemans, Angeli, Flexibility Framework with Recovery Guarantees for Aggregated Energy Storage Devices (2110.08549)](https://arxiv.org/abs/2110.08549)
- [Angeli, Dong, Strbac, On optimal coordinated dispatch for heterogeneous storage fleets with partial availability (2203.08659)](https://arxiv.org/abs/2203.08659)
- [Xie & Chen, Multistage Robust Optimization for Time-Decoupled Power Flexibility Aggregation with Energy Storage (2508.14477)](https://arxiv.org/abs/2508.14477)
- [Elsaadany & Almassalkhi, Making Aggregations Reliable (2606.01562)](https://arxiv.org/abs/2606.01562)
- [Liu et al., Preference-Oriented Aggregation of Heterogeneous DERs for Reserve Dispatch (2609.03252)](https://arxiv.org/abs/2609.03252)
- [Atamtürk & Zhang, Two-Stage Robust Network Flow and Design Under Demand Uncertainty (Oper. Res. 2007)](https://pubsonline.informs.org/doi/10.1287/opre.1070.0428)
- [Gottschalk et al., Robust flows over time: models and complexity results (Math. Program. 2018)](https://dl.acm.org/doi/abs/10.1007/s10107-017-1170-3)

---

## 8. 10-07 补查（回应“程序分析和鲁棒控制两块可能漏了”，以及同类车队）

**核对深度：** 程序分析和控制两块读到摘要、综述或教程层面，没有读到逐条定理。同类车队这一块，Evans 2019 博士论文第 8 章读到了定理和引理。

| 方向 | 文献 | 与我们的关系 | 判断 |
|---|---|---|---|
| 模板多面体 | Sankaranarayanan–Sipma–Manna, VMCAI 2005 | 用固定方向、每个方向一个 LP 求界，与我们的子集界递推是同一类做法。但它关心的是前向不变式的近似，没有讨论“哪类系统下模板恰好精确” | 背景；定理 4 可以用这个语言表述：对储能的一步前驱算子，子集方向模板在 N≤3 时恰好精确 |
| octagon、TVPI | Miné 2006 等 | 约束只含两个变量（±x_i ± x_j ≤ c），研究强闭包和规范形。我们的约束最多含 N 个变量，形式不同 | 背景，未见重叠 |
| zone、DBM | Dill 1989；Bengtsson–Yi 2004 教程 | 差分约束在时间自动机的操作（时间流逝、重置、与卫式取交）下恰好封闭。这是“特定结构下某个固定模板恰好精确”的经典先例 | 最好的类比，应在论文中引用；就所读的教程层面看，约束族和算子都不同，未见适用于我们问题的结果 |
| 广义置换多面体 | Postnikov 等 | 法向扇被 braid 扇细分的多面体类（即子模函数的基多面体），在 Minkowski 和下封闭 | 背景。K_t 的法向量虽然是子集方向，但边可以是 (1,−1,−1)，不在这个类里，所以定理 4 的封闭性不能由它推出 |
| target tube | Bertsekas–Rhodes 1971（Automatica 7） | 鲁棒后向可达集递推的起点 | 只核对到书目。一般线性系统的多面体可达集计算随步数增长，没有看到针对储能结构的精确结论 |
| 鲁棒不变集、可生存核 | 综述与计算方法（投影、提升、zonotope 内近似等） | 一般方法 | 未见“积分器加和约束”结构下某个多面体族保持的结论 |
| 同类车队的通用最优策略 | **Evans 2019 博士论文（Imperial）第 8 章，定理 8.3.4、引理 8.3.10** | 无损、各设备充放电功率之比相同、最大可持续时间相同（设备成比例）时，任意符号请求下“拉平剩余可持续时间”使可行请求集合始终最大 | **已知**。我们的命题 6 是它的特例，优超证明只是另一种证法 |
| 同类车队的可兑现初态集合 | 同上第 8 章、第 4 章（10-09 复核又核对了原文） | 第 8 章只给策略和离散时间算法；第 4 章（定理 4.2.8）是非负请求下的 E-p 变换比较，不是任意换号的区间承诺递推 | 所查来源中未见定理 H 的递推；优先权仍待进一步查证 |
| 优超与负荷灵活性 | Nayyar 等 1404.1112（duration-differentiated） | 用优超刻画可延迟负荷的可行性，确定性、单向 | 背景 |
| 聚合模型精确的条件 | Appino–Hagenmeyer–Faulwasser 1906.09183 | 确定性调度下聚合模型不损失最优性的条件 | 与命题 5 相关，但不涉及因果 |
| 最小优超元 | Tamir 1995；Fujishige 1980；Schoot Uiterkamp 2201.06596 | 基多面体有最小优超元（盒与超平面之交时就是注水点） | 已知工具 |

**三本书**（Frank 2011 第 14 章、Fujishige 2005、Murota 2003）这次仍然没有拿到全文，状态不变。

**对新意判断的影响：**
- 命题 6 降为已知结果。
- 新增的可能新结果是定理 H：只能说“所查来源中未见”，优先权仍待查证（需要继续查引用 Evans 2019 的后续工作和三本书）。
- 定理 4、命题 1、N=3/N=4 的分界，判断不变：所查来源中没有找到先例。
- 程序分析与控制两块只读到摘要、综述或教程层面，结论应表述为“未见适用结果”，不能说已经排除了整个“模板精确性”方向的文献（10-09 复核建议）。


---

## 9. 10-11 补查：仿射策略（线性决策规则）用于单初态判定

**问的问题：** `AFFINE_DECISION_ZH.md` 用历史相关的（分段）仿射策略判定单个初态能否兑现，发现它几乎总是精确，但有精确反例。这个方法和这个现象是否已知？

**核对深度：**
- Lauinger 等、Zamudio 等两篇读到正文公式。
- Xie & Chen 读到数值实验的表格。
- Bertsimas–Iancu–Parrilo 只读到目录：PDF 的字体编码无法提取正文。
- 其余只读到摘要。

| 文献 | 内容 | 与我们的关系 | 判断 |
|---|---|---|---|
| Ben-Tal–Goryashko–Guslitzer–Nemirovski，Math. Program. 2004 | 仿射可调鲁棒对应（AARC） | 我们的方法就是它 | **方法已知** |
| Chen–Sim–Sun–Zhang，Oper. Res. 2008；Georghiou–Wiesemann–Kuhn，Math. Program. 2015 | 把随机量拆成正负部的决策规则；提升（lifting）后的决策规则 | 我们的“分段仿射”是其最简单情形 | **方法已知** |
| Kuhn–Wiesemann–Georghiou，Math. Program. 2011 | 原始/对偶线性决策规则，给出上下界 | 夹逼框架的现成工具 | 已知工具 |
| Bertsimas–Iancu–Parrilo，Math. Oper. Res. 2010 | 一维、有约束、多阶段鲁棒问题中，仿射策略最优 | 我们的 N=1 情形在其范围内。论文目录里有“对可能推广的反例”一节，据检索摘要，多维系统等推广不成立；正文未能提取 | 一维精确已知；多维“可能不精确”在一般意义上已知 |
| Bertsimas–Goyal，Math. Program. 2012 | 两阶段、右端不确定时，仿射策略在最坏情况下可以很差 | 一般性的负面结果 | 背景 |
| Iancu–Sharma–Sviridenko，Oper. Res. 2013 | 超模条件下仿射策略最优 | 也许能用来证明某类车队上仿射精确 | 待读 |
| **Lauinger–Vuille–Kuhn，MSOM 2024（arXiv 2005.06042）** | 单辆电动车做调频，带损耗；证明鲁棒问题等价于一个 LP，用到“精确的线性决策规则重写” | 读到正文：仿射规则只用来描述电量，对可能取到最坏的情景与真实电量一致，所以没有误差。对象是**单个电池** | 单电池时仿射精确，已知；不涉及多台异构 |
| **Xie & Chen 2508.14477** | 多阶段鲁棒的灵活性聚合；对照组中有“带仿射策略的多阶段模型”（按 Su 等 2022 TSG 的约束生成算法求解） | 读到表 2：6 个 8 时段算例（1 到 33 台储能），**仿射模型的最优值与精确枚举全部相同**；24 时段时仿射模型 10,000 秒内不收敛。文中没有说仿射是否一般精确，也没有给反例 | **“仿射在储能聚合上与精确值一致”已有数值观察**（6 个算例）。我们 09-29 读这篇时漏记了这一点 |
| Zamudio–Falsone–Bianchi–Prandini（Polimi 预印本） | 储能型产消者聚合：分解策略 p_i(k) = β_i·p(k) + α_i，聚合灵活性取一个盒子，最大化体积 | 读到公式：只依赖当前总调用，各段系数相同。相当于我们的参与因子加常数项，是我们策略类的特例 | 背景。历史依赖正是我们把待定比例从 24–39% 降到 0 的原因 |
| Warrington–Goulart–Mariéthoz–Morari，IEEE TPS 2013；arXiv 1604.04890 | 发电机和储能的仿射备用策略；多阶段鲁棒机组组合里的仿射储能调度 | 仿射策略在电力系统里是标准的可解近似 | 背景 |
| arXiv 2605.13836（HVAC 车队） | 离线算后向可达集的多面体内近似，在线用闭式因果策略分解 | 内近似加因果分解，对象是建筑 | 背景 |
| **Tang–Zhai–Zhao，JMPSCE 2023（DOI 10.35833/MPCE.2022.000644）** | 储能调度的多阶段鲁棒：给出多面体不确定集下“充分必要的可行性条件”，不需要仿射假设；称在仿射方法失败时仍能找到可行解 | 只读到摘要。它可能是一种精确方法，也说明仿射可以失败。还不知道是否涉及“多台异构储能共同满足总功率” | **必须读全文**（IEEE Xplore 开放获取，本机抓不到）。同组还有 Zhou–Zhai–Wu（IEEE TSG）的后向推导可行性命题 |

**对新意判断的影响：**
- **方法不是新的：** 仿射或分段仿射决策规则、它的精确鲁棒对应，都是标准做法。
- **“几乎精确”的现象也不全新：** Xie & Chen 在 6 个算例上已经看到仿射值与精确值相同，但没有系统检验，也没有给反例。
- **可能是新的部分（所查来源中未见）：**
  - 对多台异构储能、区间承诺的单初态判定，系统检验仿射策略：21 万个初态、788 个实例的顶点检验；
  - 一个有理数精确证书，说明仿射（含分段）策略不总是精确；
  - 把单初态判定写成规模 O(NT²) 的 LP，并对接受做有理数核对。
- **待读：** Tang–Zhai–Zhao 2023 及同组工作。如果他们的充分必要条件覆盖多台异构储能，可能同时影响我们的定理 4 和仿射部分的定位。

**参考链接：**
- [Lauinger–Vuille–Kuhn, arXiv 2005.06042](https://arxiv.org/abs/2005.06042)
- [Xie & Chen, arXiv 2508.14477](https://arxiv.org/abs/2508.14477)
- [Zamudio et al. 预印本（Polimi）](https://re.public.polimi.it/handle/11311/1256266)
- [Bertsimas–Iancu–Parrilo, arXiv 0904.3986](https://arxiv.org/abs/0904.3986)
- [Bertsimas–Goyal（MIT DSpace）](https://dspace.mit.edu/handle/1721.1/69679)
- [Iancu–Sharma–Sviridenko 2013](https://ideas.repec.org/a/inm/oropre/v61y2013i4p941-956.html)
- [Chen–Sim–Sun–Zhang 2008](https://ideas.repec.org/a/inm/oropre/v56y2008i2p344-357.html)
- [Warrington et al., arXiv 1212.2119](https://arxiv.org/abs/1212.2119)
- [arXiv 1604.04890](https://arxiv.org/abs/1604.04890)
- [arXiv 2605.13836](https://arxiv.org/abs/2605.13836)
- [Tang–Zhai–Zhao 2023（IEEE Xplore）](https://ieeexplore.ieee.org/document/10106619)

---

## 10. 10-12 全文核对（用户下载的文献）

文件在 `papers/`（Zhai 组三篇、CASE 2024 一篇）和用户的下载目录（Murota 1998、Frank 一书的出版公告）。正文用自写的提取脚本读出，IEEE 和 Elsevier 的字体编码已解码。

| 文献 | 系统 | 精确性 | 与我们的关系 |
|---|---|---|---|
| **Tang–Zhai–Zhao，JMPSCE 11(6) 2023**，“Multi-Stage Robust Scheduling for Community Microgrid with Energy Storage” | 社区微网：**一个**储能加主网交换；预算型多面体不确定集；有充放电效率 | 给出单个储能电量逐段“安全上下界”的充分必要条件（单储能、多面体不确定集） | 相当于我们的 1 台情形，不涉及多台异构，与定理 4、定理 H **不重叠**。他们举的仿射策略失败例子来自损耗和预算型不确定集，与我们的反例不是同一机制 |
| **Zhou–Zhai–Wu，IEEE TSG 13(6) 2022**，“Optimal Operation of Regional Microgrids With Renewable and Energy Storage: Solution Robustness and Nonanticipativity Against Uncertainties” | 微网：火电机组加**一个**储能电量 E_t 加主网 | 命题 1：单个储能电量区间的逐段递推（式 17–18，min/max 形式）加火电出力区间；作者称“严格充分、近似必要” | 1 台情形的区间递推（与我们 N=1 的已知递推同类），**不重叠** |
| **J. Zhao、Q. Zhai 等，J. Energy Storage 2024**（S2352152X24016128），基于不确定集分解的多阶段鲁棒电池调度 | 配电网、**多台**电池 | 把不确定集拆成每台电池各一份（Minkowski 和的分解），每台用单电池的精确条件；定理 2 是**充分条件** | 保守的内近似，和我们的参与因子、分组策略同类。与精确结果**不重叠**。文中也引用了 BIP 2010，指出仿射策略可能缩小可行域 |
| **CASE 2024**，“Multi-stage Robust Implicit Decision Rule for Optimal Control Problem of Energy Storage System” | 多台储能 | 决策空间取“每台储能各自独立的可行区间”，是充分条件。定理 1：若决策只依赖当前一段的随机量，且期末电量须回到初值，则决策只能是常数 | 内近似。定理 1 从另一面说明只看当前调用的策略很受限，与我们“依赖历史是关键”的发现一致 |
| **Murota，Math. Program. 83 (1998) 313–371**，“Discrete convex analysis” | — | 定理 3.5：Frank 离散分离定理（整数版，引用 Frank [14]）；注 3.1：它与 Edmonds 交定理、Fujishige 的 Fenchel 型极小极大定理等价 | **F4 的正式出处**：整数版用定理 3.5，实数版可由同一结论推出（Murota 2016 讲义第 38 页有实数形式） |
| Frank，*Connections in Combinatorial Optimization* | — | 下载到的只是两页出版公告，不是书本身 | 拿不到全书，用 Frank–Tardos 1988 代替（见下一行） |
| **Frank–Tardos，Math. Program. 42 (1988) 489–563**，“Generalized polymatroids and submodular flows”（10-12 读原文） | — | 定理 I.2（引 Frank 1982）：**实数版**分离定理；命题 II.2.5：弱对（相交子模、弱交叉条件）给出 g-polymatroid；命题 II.2.10：与“板” α ≤ x(S) ≤ β 相交，上界为 min(b(X), β − p(S∖X))；命题 II.2.11：与盒子相交的公式；命题 II.2.1：子模多面体、基多面体都是 g-polymatroid | **F4 实数版的正式出处**（定理 I.2）；**F3 的出处**（命题 II.2.11 取 f = −∞）。全文只讨论满足交叉条件的情形，没有不满足交叉条件时紧界的结构，也没有与维数有关的结论。所以引理 3(c)(d) 和 N=3/N=4 的分界在此**未见先例**。同型号的引理 S 与命题 II.2.10 形式相同，但不要求交叉条件 |
| Evans 2019 博士论文的被引（Google Scholar，用户截图） | — | 只有 1 篇：Angeli–Dong–Strbac，IEEE TCST 2022（arXiv 2203.08659），我们 09-25 已读 | 引用链里没有同型号、区间承诺的精确递推，**对定理 H 的优先权有利**（只说明引用链，不是穷尽检索） |

**Guo–Wei–Chen–Shahidehpour–Mei，IEEE TPS 37(1): 738–749, 2022**，“Distribution System Operation With Renewables and Energy Storage: A Linear Programming Based Multistage Robust Feasibility Approach”（10-12 读完全文）：
- **系统：** 配电网加多台储能，可再生出力的不确定集每段是一个盒子。
- **做法：** 从最后一段往前，逐段定义“动态鲁棒可行域”（DRFR），这就是我们的 K_t。
  - Claim 1：只需检查不确定集的顶点，相当于端点引理；
  - Claim 2：每个 DRFR 都是多面体；
  - Claim 3：用对偶多面体的顶点写出 H-表示。由于对偶顶点枚举不可行，实际用割平面法：每次解一个双线性规划找最违反的约束，逐步加入。
- **精确性：** 是精确的逐段投影，但面数和迭代次数没有上界，最坏情况是指数级。文中没有研究可行域的结构，没有固定大小的描述，也没有设备数的分界。
- **与我们的关系：**
  - 它是“精确但无多项式保证”的已有方法，与请求树 LP、Xie & Chen 的状态递推并列；
  - 我们的定理 4、定理 H 正是在这个一般框架下，给出固定大小、闭式、O(T) 的精确递推，并指出 4 台时为什么不可能；
  - 新意判断不变，但凡是写“已有精确方法要枚举请求树”的地方，都应改为“请求树，或逐段多面体投影；均无多项式保证”。

**书拿不到（10-12）：** Frank 一书的全书和 Fujishige 一书都无法下载。我们文档里用到的书中结论（F3 卷积、F4 三明治定理、引理 3(a)(b)）都有完整的自证，引用只是标明出处。改读的 **Frank–Tardos 1988** 已核对（见上表）：F3、F4 都有了正式出处，引理 3(c)(d) 的维数结论在其中未见。

Fujishige 2005 若以后能在线看，对照以下几处：
  1. 子模系统按向量的约简（reduction）：P(f) ∩ {x ≤ c} 的上界函数 min_{Y⊆X}[f(Y) + c(X∖Y)] 仍子模（我们的 F3）；
  2. 离散分离或三明治定理的实数形式（我们的 F4）；
  3. 广义多拟阵与盒子、超平面之交的紧界（引理 3(a)(b) 一类公式）；
  4. 基多面体的字典序最优基、最小优超元（Fujishige 1980，用于命题 6）。

**结论：** Zhai 组的工作都是单储能的精确条件，或多储能的充分条件（分解、独立区间）。它们没有给出多台异构储能共同满足总功率时的精确刻画，所以对定理 4、定理 H、例 B、例 D 的新意判断不变。仿射部分的判断也不变（见 §9）。
