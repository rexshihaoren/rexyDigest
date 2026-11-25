# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年11月01日 至 2026年11月08日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 Agent-R²：通过真实来源数据合成扩展智能体以完成现实生产力工作 ｜ Agent-R$^2$: Scaling Agents for Realistic Productivity Work via Real-Source Data Synthesis
- 🏅 AttnSR：用于长程智能体强化学习的注意力步骤奖励 ｜ AttnSR: Attention Step Reward for Long-Horizon Agentic RL
- 🏅 CORE：用于深度研究的由粗到精搜索与上下文管理 ｜ CORE: Coarse-to-Fine Search with Context Management for Deep Research

---


**标题｜Title**
📄 **Teng Pan, Zixuan Wang, Yuchen Yan, Qifei Wu, Yao Chen, Yingqi Qu, Ruiqing Zhang, Yongliang Shen** — Agent-R²：通过真实来源数据合成扩展智能体以完成现实生产力工作（论文，2026-11-05） ｜ 📄 **Teng Pan, Zixuan Wang, Yuchen Yan, Qifei Wu, Yao Chen, Yingqi Qu, Ruiqing Zhang, Yongliang Shen** — Agent-R$^2$: Scaling Agents for Realistic Productivity Work via Real-Source Data Synthesis (Paper, 2026-11-05)

**来源｜Source**：https://arxiv.org/abs/2611.08219

**摘要｜TL;DR**
Agent-R² 引入真实来源数据合成方法训练智能体执行现实生产力任务，提升性能并抑制捷径行为。 ｜ Agent-R^2 introduces real-source data synthesis for training agents on realistic productivity tasks, improving performance and mitigating shortcut behavior.

**要点｜Takeaways**
• 使用真实职业种子、工作流证据和真实网络文件构建 4k 个任务实例，配备交付级评分标准。 ｜ Uses real occupational seeds, workflow evidence, and authentic web files to create 4k task instances with deliverable-level rubrics.
• 仅用 4k 实例训练的 4B 模型在 GDPval 和 OfficeQA 上超越 Qwen3-235B。 ｜ Trained 4B model surpasses Qwen3-235B on GDPval and OfficeQA despite only 4k instances.
• 基于评分标准的强化学习改进了文件依据推理和端到端生产力。 ｜ Rubric-based reinforcement learning improves file-grounded reasoning and end-to-end productivity.
• 减少了智能体在充分依据、构建或验证前就生成表面可信交付物的捷径行为。 ｜ Reduces shortcut behavior where agents produce superficially plausible deliverables before grounding, constructing, or verifying them.
• 展示了无需人工指定工作流或 LLM 生成文件的可扩展后训练数据合成方法。 ｜ Demonstrates scalable post-training data synthesis without manually specified workflows or LLM-generated files.

**启示｜Implication**
对于构建自主智能体的人，基于真实世界数据源的训练是避免表面行为、实现可靠生产力的关键。 ｜ For those building autonomous agents, grounding training in authentic real-world data sources is critical to avoid superficial behavior and achieve reliable productivity.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Mengsong Wu, Tianchen Zhou, Zhaochen Su, Zhenhua Liu, Zhe Cui, Aimin Zhou** — AttnSR：用于长程智能体强化学习的注意力步骤奖励（论文，2026-11-05） ｜ 📄 **Mengsong Wu, Tianchen Zhou, Zhaochen Su, Zhenhua Liu, Zhe Cui, Aimin Zhou** — AttnSR: Attention Step Reward for Long-Horizon Agentic RL (Paper, 2026-11-05)

**来源｜Source**：https://arxiv.org/abs/2611.07932

**摘要｜TL;DR**
AttnSR 在训练回放中从策略注意力派生步骤级奖励，无需单独奖励模型或额外采样即可改进长程 LLM 智能体。 ｜ AttnSR derives step-level rewards from policy attention during training replay, improving long-horizon LLM agents without a separate reward model or extra rollouts.

**要点｜Takeaways**
• AttnSR 反向追踪策略注意力，估计早期步骤对最终响应的相关性。 ｜ AttnSR traces policy attention backward to estimate step relevance to the final response.
• 基于终端步骤的基线决定是强化还是惩罚中间步骤。 ｜ A terminal-step baseline decides whether to reinforce or penalize intermediate steps.
• 在 ALFWorld 上，最终留出成功率从 91.2% 提升到 97.1%，超过 PPO。 ｜ On ALFWorld, final held-out success improves from 91.2% to 97.1% over PPO.
• 在 ScienceWorld 上，AttnSR 在所有检查点均有提升，并将环境交互减少 29.9%。 ｜ On ScienceWorld, AttnSR improves all checkpoints while cutting environment interactions by 29.9%.
• 代码已开源，方法可直接复现测试。 ｜ Code is available, making the method directly testable.

**启示｜Implication**
对于构建自主智能体的实践者，策略注意力可以作为一种廉价的内在步骤级奖励信号，减少对仅结果强化学习和环境样本的依赖。 ｜ For practitioners building autonomous agents, policy attention can serve as a cheap, intrinsic step-level reward signal, reducing reliance on outcome-only RL and environment samples.

**综合评分｜CompositeScore**
4.6

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Hoang Tran Vuong, Ngoc Quan Pham, Hung Bui, Fatih Porikli, Dat Quoc Nguyen** — CORE：用于深度研究的由粗到精搜索与上下文管理（论文，2026-11-05） ｜ 📄 **Hoang Tran Vuong, Ngoc Quan Pham, Hung Bui, Fatih Porikli, Dat Quoc Nguyen** — CORE: Coarse-to-Fine Search with Context Management for Deep Research (Paper, 2026-11-05)

**来源｜Source**：https://arxiv.org/abs/2611.07859

**摘要｜TL;DR**
CORE 是一种无需训练的搜索协调器，通过由粗到精检索与上下文管理改进深度研究智能体，仅返回最相关的片段以减少上下文膨胀，并取得最先进的答案准确率和证据召回率。 ｜ CORE is a training-free search harness that improves deep research agents by coarse-to-fine retrieval with context management, yielding only the most relevant snippets to reduce context bloat and achieve state-of-the-art answer accuracy and evidence recall.

**要点｜Takeaways**
• CORE 将搜索段落长度与上下文长度解耦：检索长段落，但通过后期交互的 token 级相似度只返回最相关的片段。 ｜ CORE decouples search passage length from context length: retrieve long passages but return only top relevant snippets via late-interaction token similarities.
• 上下文管理抑制重复片段，并允许智能体围绕已检索来源扩展上下文，从而减轻认知负荷。 ｜ Context management suppresses repeated snippets and lets agents expand context around already retrieved sources, reducing cognitive load.
• 在三个智能体模型和三个 BrowseComp 基准（最多 5.53 亿篇文档）上，CORE 优于 Tongyi DeepResearch 和 OpenResearcher 协调器。 ｜ Across three agent models and three BrowseComp benchmarks with up to 553M documents, CORE outperforms Tongyi DeepResearch and OpenResearcher harnesses.
• 该方法无需训练，因此可以集成到现有的深度研究智能体框架中，无需重新训练模型。 ｜ The method is training-free, so it can be integrated into existing deep research agent frameworks without model retraining.

**启示｜Implication**
对于将 AI 智能体视为现实操纵工具的实践哲学家而言，CORE 表明策展智能体的上下文（即它从搜索中‘看到’什么）是引导其推理和输出的控制面，从而强化了信息管理就是模拟环境中一种代码操纵形式的观点。 ｜ For practitioner-philosophers treating AI agents as reality-manipulating tools, CORE shows how curating an agent's context—what it 'sees' from search—is a control surface for steering its reasoning and output, reinforcing the idea that information management is a form of code manipulation in simulated environments.

**综合评分｜CompositeScore**
4.5

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Xiaojun Wu, Cehao Yang, Xuhui Jiang, Chengjin Xu, Jia Li, Jian Guo** — 终端式数学建模基准：首个智能体可验证的数学建模基准（论文，2026-11-05） ｜ 📄 **Xiaojun Wu, Cehao Yang, Xuhui Jiang, Chengjin Xu, Jia Li, Jian Guo** — Terminal-style Mathematical Modeling Bench: The First Agentic and Verifiable Benchmark for Mathematical Modeling (Paper, 2026-11-05)

**来源｜Source**：https://arxiv.org/abs/2611.08237

**摘要｜TL;DR**
TB-MathModel 是首个智能体终端式基准，通过对照多篇优秀论文评分数值输出并用 Lean 4 执行可行性验证，来评估完整数学建模竞赛题目。 ｜ TB-MathModel is the first agentic, terminal-style benchmark that verifies complete mathematical-modeling contest problems by scoring numeric outputs against multiple outstanding papers and enforcing feasibility with Lean 4.

**要点｜Takeaways**
• 提出 TB-MathModel，涵盖 18 道 2023–2025 年真实 CUMCM/MCM 题目，置于容器化终端环境。 ｜ Introduces TB-MathModel, covering 18 real CUMCM/MCM problems (2023–2025) in containerized terminal environments.
• 采用方向感知单边评分，对照多篇人类优秀论文，从不惩罚超越锚点的答案。 ｜ Uses direction-aware one-sided scoring against a panel of human outstanding papers, never penalizing answers that beat the anchor.
• 应用双层可行性验证：对六种可判定不变式进行程序化检查，外加 624 条 Lean 4 义务，不可行答案归零。 ｜ Applies two-layer feasibility verification: programmatic checks over six invariant forms plus 624 Lean 4 obligations, zeroing infeasible submissions.
• 在七个多模态模型上，最强多参考 O-Eval 达 64.58%，而 2.54 美元开源模型以 1/100 成本达到 59.81%。 ｜ Across seven multimodal models, strongest multi-reference O-Eval is 64.58%, while a $2.54 open model reaches 59.81% at 1/100 cost.
• 为长时程建模能力和智能体轨迹收集提供可复现、机器可检的信号。 ｜ Provides a reproducible, machine-checkable signal for long-horizon modeling competence and agent trajectory collection.

**启示｜Implication**
该基准将智能体评估从 LLM 评判报告转向可验证的数值与可行性检查，这是让智能体模型在高风险建模任务中作为现实代码操控者被信任的必要一步。 ｜ This benchmark shifts agent evaluation from LLM-judged report grading to verifiable numeric and feasibility checks, a necessary step if agentic models are to be trusted as reality-code manipulators in high-stakes modeling tasks.

**综合评分｜CompositeScore**
4.5

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Yingjie Tan, Haiquan Qiu, Quanming Yao, Manyi Zhong, Xianzhi Yu, Yaqing Wang** — QRAE：深度搜索智能体中用于上下文压缩的查询相关注意力熵（论文，2026-11-05） ｜ 📄 **Yingjie Tan, Haiquan Qiu, Quanming Yao, Manyi Zhong, Xianzhi Yu, Yaqing Wang** — QRAE: Query-Relevant Attention Entropy for Context Compression in DeepSearch Agents (Paper, 2026-11-05)

**来源｜Source**：https://arxiv.org/abs/2611.07976

**摘要｜TL;DR**
QRAE 是一种在线上下文压缩方法，利用查询相关注意力熵在 DeepSearch 智能体中选择相关的检索块用于推理，将任务成功率提高 2.35 个百分点，同时将延迟和 token 用量分别降低 30% 和 45%。 ｜ QRAE is an online context compression method that uses query-relevant attention entropy to select relevant retrieved chunks for reasoning in DeepSearch agents, improving task success by 2.35 points while cutting latency and token usage by 30% and 45%.

**要点｜Takeaways**
• QRAE 使用稀疏证据评估头和成对预填充对块的相关性进行打分，无需改变注意力或增加生成式压缩步骤。 ｜ QRAE uses sparse evidence-assessment heads and paired prefills to score chunk relevance without altering attention or adding a generative pass.
• 高分块进入持久证据白名单，不确定块保留在候选缓存中以便后续重新评估。 ｜ High-scoring chunks enter a persistent evidence whitelist; uncertain chunks are cached for later reevaluation.
• 在多个基准和推理模型上，QRAE 将任务成功率平均提高 2.35 个百分点，并降低 30% 延迟和 45% token 用量。 ｜ Across benchmarks and reasoning models, QRAE improves task success by 2.35 pp and reduces latency 30%, token usage 45%.
• 该方法可扩展到近 100B 参数的模型，表明其实用稳健性。 ｜ The approach scales to a nearly 100B parameter model, suggesting robust practical applicability.

**启示｜Implication**
对于构建或驾驭 DeepSearch 智能体的实践者，QRAE 提供了一种模型无关的方式来抑制不断增长的上下文并提高推理效率，使智能体搜索更加可行和可控。 ｜ For practitioners building or steering DeepSearch agents, QRAE offers a model-agnostic way to tame runaway context growth and improve reasoning efficiency, making agentic search more viable and controllable.

**综合评分｜CompositeScore**
4.5

**主题｜Topics**
智能体 ｜ Agent
