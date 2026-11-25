# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年10月11日 至 2026年10月18日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 CoWorld Reasoner：基于演进的视频世界模型驱动框架的智能体多模态推理 ｜ CoWorld Reasoner: Agentic Multimodal Reasoning with the Evolving Video World Model-Driven Harness
- 🏅 智能体后训练的基础模型预热：一种开放的中期训练配方 ｜ Priming Base Models for Agentic Post-Training: An Open Midtraining Recipe
- 🏅 LEASH：面向计算机使用智能体的不确定性感知弱到强升级与监督 ｜ LEASH: Uncertainty-Aware Weak-to-Strong Escalation and Oversight for Computer-Use Agents

---


**标题｜Title**
📄 **Soumye Singhal, Joseph Jennings, Ka Shun Shum, Alexander Bukharin, Khushi Bhardwaj, Zirui Liu, Venkat Srinivasan, Jonathan Li, Yash Jain, Kezhi Kong, Markus Kliegl, Olivier Delalleau, Sanjeev Satheesh, Mostofa Patwary** — 智能体后训练的基础模型预热：一种开放的中期训练配方（论文，2026-10-15） ｜ 📄 **Soumye Singhal, Joseph Jennings, Ka Shun Shum, Alexander Bukharin, Khushi Bhardwaj, Zirui Liu, Venkat Srinivasan, Jonathan Li, Yash Jain, Kezhi Kong, Markus Kliegl, Olivier Delalleau, Sanjeev Satheesh, Mostofa Patwary** — Priming Base Models for Agentic Post-Training: An Open Midtraining Recipe (Paper, 2026-10-15)

**来源｜Source**：https://arxiv.org/abs/2610.22019

**摘要｜TL;DR**
一种开放的中期训练配方在长上下文软件工程数据和小比例智能体轨迹上对基础模型进行预热，提高了智能体编码基准和后训练鲁棒性。 ｜ An open midtraining recipe primes base models on long-context software-engineering data and a small share of agentic traces, improving agentic coding benchmarks and post-training robustness across model sizes.

**要点｜Takeaways**
• 在 256K 上下文上使用打包代码库、PR、提交和构建日志以及智能体轨迹进行中期训练，可提升智能体后训练性能。 ｜ Midtraining at 256K context on packed repos, PRs, commits, and build logs plus agentic traces boosts agentic post-training performance.
• 在 Nemotron 3.5 Lightning 上使用 500B 中期训练 token，SWE-bench Verified 从 60.7 提升到 64.5，Multilingual 从 55.8 提升到 62.8。 ｜ 500B midtraining tokens on Nemotron 3.5 Lightning raise SWE-bench Verified from 60.7 to 64.5 and Multilingual from 55.8 to 62.8.
• 在 Nemotron 3.5 Super 上使用 280B 中期训练 token，DeepSWE 从 11.7 提升到 15.7，SWE-bench Verified 从 72.9 提升到 74.3。 ｜ 280B midtraining tokens on Nemotron 3.5 Super improve DeepSWE from 11.7 to 15.7 and SWE-bench Verified from 72.9 to 74.3.
• 短固定 SFT 运行比基础模型指标更能预测后训练结果，因为基础模型代理指标与后训练结果没有可靠相关性。 ｜ Short fixed SFT runs give better proxy signals than base-model metrics, which do not correlate reliably with post-training results.
• 该配方开放且包含消融实验，便于智能体模型构建者复现。 ｜ The recipe is open and includes ablations, enabling replication for agentic model builders.

**启示｜Implication**
将 AI 智能体视为现实代码操纵者的实践哲学家，应该采用这种开放的中期训练配方来强化工具使用基座，从而驾驭模拟世界或市场。 ｜ Practitioner-philosophers treating AI agents as reality-code manipulators should adopt this open midtraining recipe to strengthen the tool-using substrate that steers simulated worlds or markets.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Qingni Wang, Changdae Oh, Yuzhe Yang, Sharon Li, Jiachen Yang, Ang Li, Xin Eric Wang** — LEASH：面向计算机使用智能体的不确定性感知弱到强升级与监督（论文，2026-10-15） ｜ 📄 **Qingni Wang, Changdae Oh, Yuzhe Yang, Sharon Li, Jiachen Yang, Ang Li, Xin Eric Wang** — LEASH: Uncertainty-Aware Weak-to-Strong Escalation and Oversight for Computer-Use Agents (Paper, 2026-10-15)

**来源｜Source**：https://arxiv.org/abs/2610.22280

**摘要｜TL;DR**
LEASH 是一个免训练框架，利用弱模型的潜在不确定性决定何时升级到强黑盒计算机使用智能体，并通过影子观察者加以约束，以提高任务成功率并降低推理成本。 ｜ LEASH is a training-free framework that uses a weak model's latent uncertainty to decide when to escalate to a strong black-box computer-use agent and keeps it on a leash via a shadow observer, improving task success while reducing inference cost.

**要点｜Takeaways**
• LEASH 通过将隐藏状态与过去成功和失败轨迹对比得到的不确定性信号，在弱智能体和强智能体之间进行升级。 ｜ LEASH escalates from weak to strong agents using uncertainty signals derived by comparing hidden states to past successful and failed trajectories.
• 它复用弱模型在动作生成时已经产生的激活，无需额外前向传播或专门训练监控器。 ｜ It reuses weak model activations already produced during action generation, requiring no extra forward pass or dedicated monitor training.
• 交接后，影子观察者在无需内部访问权限的情况下继续监督强黑盒智能体。 ｜ After handoff, a shadow observer continues oversight of the strong black-box agent without needing internal access.
• 在 OSWorld 上，LEASH 在匹配升级率下比随机升级高出 6.55–11.94 个百分点，使用 Qwen3.5-35B-A3B 时以低 19.2% 的成本达到与 Claude Opus 5 相当的成功率。 ｜ On OSWorld, LEASH outperforms random escalation by 6.55–11.94 points and matches Claude Opus 5 success with 19.2% lower cost using Qwen3.5-35B-A3B.

**启示｜Implication**
它展示了如何将潜在不确定性转化为自主计算机使用智能体的控制原语，使实践者能够更便宜、更安全地引导昂贵的黑盒模型而不放弃监督。 ｜ It shows how latent uncertainty can be turned into a control primitive for autonomous computer-use agents, letting practitioners steer expensive black-box models more cheaply and safely without surrendering oversight.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📝 **Simon Willison** — 引述 Geoffrey Huntley（博客，2026-10-13） ｜ 📝 **Simon Willison** — Quoting Geoffrey Huntley (Blog, 2026-10-13)

**来源｜Source**：https://simonwillison.net/2026/Oct/13/geoffrey-huntley/

**摘要｜TL;DR**
Simon Willison 引述 Geoffrey Huntley 的做法：使用 pre-commit 钩子检测代理代码绕过诊断库的情况，提交失败并注入提示以让代理遵守规范。 ｜ Simon Willison quotes Geoffrey Huntley on using a pre-commit hook to detect agent code that bypasses a diagnostics library, failing commits and injecting prompts to make agents comply.

**要点｜Takeaways**
• 代理可能忽略 AGENTS.md 指令；没有强制执行就会产生漂移。 ｜ Agents may ignore AGENTS.md instructions; drift is inevitable without enforcement.
• Pre-commit 钩子可以检查 git diff 以检测被禁止或绕过的 API 使用。 ｜ Pre-commit hooks can inspect git diffs to detect forbidden or bypassing API usage.
• 让提交失败并注入提示可以引导代理使用必需的库。 ｜ Failing a commit and injecting a prompt can steer agent behavior to use required libraries.
• 这把面向人类的 git 钩子变成了代理治理机制。 ｜ This turns a human-oriented git hook into an agent governance mechanism.
• 诊断/可观测性模块可以作为编码代理策略强制执行。 ｜ Diagnostics/observability modules can be enforced as coding-agent policy.

**启示｜Implication**
它表明代理行为可以通过基础设施层面的反馈循环来塑造，而不仅仅是提示指令，这对构建可靠自主编程系统的人很重要。 ｜ It demonstrates that agent behavior can be shaped through infrastructure-level feedback loops, not just prompt instructions, which matters for anyone building reliable autonomous coding systems.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Leyang Shen, Yaxin Gong, Yang Zhang, Chenxiao Fan, Jiakai Wang, Dong Wang, Yang Liu, Fuli Feng, Chun Kai Ling, Tat-Seng Chua** — 学习引导LLM智能体与多智能体系统（论文，2026-10-15） ｜ 📄 **Leyang Shen, Yaxin Gong, Yang Zhang, Chenxiao Fan, Jiakai Wang, Dong Wang, Yang Liu, Fuli Feng, Chun Kai Ling, Tat-Seng Chua** — Learning to Steer LLM Agents and Multi-Agent Systems (Paper, 2026-10-15)

**来源｜Source**：https://arxiv.org/abs/2610.22316

**摘要｜TL;DR**
一种经强化学习训练的引导智能体在运行时监控基于LLM的单智能体和多智能体执行，检测目标漂移并通过低成本快速路径或高成本慢速路径进行干预，使系统保持正轨，从而提升性能与效率，并能泛化到未见任务和执行器。 ｜ A reinforcement-learning-trained steering agent monitors LLM-based single- and multi-agent execution, detects goal drift, and intervenes via low-cost fast or high-cost slow paths to keep systems on track, improving performance and efficiency and generalizing to unseen tasks and executors.

**要点｜Takeaways**
• 引入一种引导智能体，在运行时监督使用工具的LLM智能体及多智能体系统，纠正目标漂移。 ｜ Introduces a steering agent that supervises tool-using LLM agents and multi-agent systems at runtime to correct goal drift.
• 采用双路径干预设计：低成本快速路径用于快速修正，高成本慢速路径用于更深入的干预。 ｜ Uses a two-path intervention design: low-cost fast path for quick correction and high-cost slow path for deeper intervention.
• 通过强化学习联合训练引导智能，结合成对排序目标与GRPO，实现学习到的漂移评估与干预生成。 ｜ Jointly trains steering intelligence with reinforcement learning, combining pairwise ranking and GRPO, enabling learned drift assessment and intervention generation.
• 在信息搜索任务上同时提升单智能体和多智能体系统的性能与效率。 ｜ Improves both performance and efficiency on information-seeking search tasks for single-agent and multi-agent setups.
• 学习到的引导能力可跨领域泛化、迁移到未见执行器，并支持无需重训练的可控干预频率。 ｜ Learned steering generalizes out-of-domain, transfers to unseen executors, and supports controllable intervention frequency without retraining.

**启示｜Implication**
实践哲学家应关注，因为它将“引导”操作化为LLM智能体之上的学习控制层，这是朝着将多智能体执行视为可治理计算过程而非不透明涌现系统迈出的具体一步。 ｜ Practitioner-philosophers should care because it operationalizes 'steering' as a learned control layer over LLM agents, a concrete step toward treating multi-agent execution as a governable computational process rather than an opaque emergent system.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Dongjie Cheng, Ruifeng Yuan, Ran Wei, Ning Song, Yongqi Li, Wenjie Li** — CoWorld Reasoner：基于演进的视频世界模型驱动框架的智能体多模态推理（论文，2026-10-15） ｜ 📄 **Dongjie Cheng, Ruifeng Yuan, Ran Wei, Ning Song, Yongqi Li, Wenjie Li** — CoWorld Reasoner: Agentic Multimodal Reasoning with the Evolving Video World Model-Driven Harness (Paper, 2026-10-15)

**来源｜Source**：https://arxiv.org/abs/2610.21910

**摘要｜TL;DR**
CoWorld Reasoner 是一个智能体框架，将视频世界模型作为统一推理引擎，通过工具和技能实现灵活视觉想象与协同演化，从而提升多模态时空推理。 ｜ CoWorld Reasoner is an agentic framework that uses a Video World Model as a unified reasoning engine, with tools and skills enabling flexible visual imagination and co-evolution for improved multimodal spatiotemporal reasoning.

**要点｜Takeaways**
• 用智能体式框架取代固定的视频世界模型流水线，让视觉语言模型通过工具决定何时及如何生成视觉证据。 ｜ Replaces fixed VWM pipelines with an agentic harness where a VLM decides when and how to generate visual evidence via tools.
• 提出 VLM-VWM 框架协同演化，基于执行反馈修订工具、技能和代码，无需更新模型权重。 ｜ Introduces VLM-VWM Harness Co-Evolution that revises tools, skills, and code based on execution feedback without updating model weights.
• 在七个基准上超越直接视觉语言模型推理，ERQA 上相对准确率提升最高达 13%。 ｜ Outperforms direct VLM reasoning across seven benchmarks, with relative gains up to 13% on ERQA.
• 表明通过世界模型进行灵活视觉想象是构建更强多模态智能体的可行路径。 ｜ Shows that flexible visual imagination through world models is a practical path to stronger multimodal agents.

**启示｜Implication**
对实践哲学家而言，它展示了将自主智能体与学习到的世界模型（本质上是视觉现实的迷你模拟）耦合，可以超越直接感知扩展推理，模糊了模型与模拟环境之间的界限。 ｜ For practitioner-philosophers, it demonstrates how coupling an autonomous agent with a learned world model—effectively a mini-simulation of visual reality—can extend reasoning beyond direct perception, blurring the line between model and simulated environment.

**综合评分｜CompositeScore**
4.5

**主题｜Topics**
智能体, 模拟 ｜ Agent, Simulation
