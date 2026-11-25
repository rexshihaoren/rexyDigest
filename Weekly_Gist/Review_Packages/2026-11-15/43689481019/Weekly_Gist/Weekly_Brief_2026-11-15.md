# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年11月08日 至 2026年11月15日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 从委派到协调：学习高效的多智能体深度研究 ｜ From Delegation to Coordination: Learning Efficient Multi-Agent Deep Research
- 🏅 Singularity-Bench：智能体能否构建智能体？ ｜ Singularity-Bench: Can Agents Build Agents?
- 🏅 Bait：通过探测奖励函数缓解有害智能体强化学习 ｜ Bait: Mitigating Harmful Agentic Reinforcement Learning via Probing Reward Function

---


**标题｜Title**
📄 **Yuyang Wu, Yang Liu, Zequn Xie, Junjie Wang, Dan Yang, Zehao Tan, Ding-Chu Zhang, Junming Yang, Yue Shen, Jian Wang, Jinjie Gu** — 从委派到协调：学习高效的多智能体深度研究（论文，2026-11-12） ｜ 📄 **Yuyang Wu, Yang Liu, Zequn Xie, Junjie Wang, Dan Yang, Zehao Tan, Ding-Chu Zhang, Junming Yang, Yue Shen, Jian Wang, Jinjie Gu** — From Delegation to Coordination: Learning Efficient Multi-Agent Deep Research (Paper, 2026-11-12)

**来源｜Source**：https://arxiv.org/abs/2611.17041

**摘要｜TL;DR**
LEAD-RL提出了贡献感知的信用分配，用于联合训练多智能体深度研究中的主代理和子代理，在提高准确率的同时降低了关键路径成本。 ｜ LEAD-RL introduces contribution-aware credit assignment for joint training of main and subagents in multi-agent deep research, improving accuracy and reducing critical-path cost.

**要点｜Takeaways**
• LEAD-RL联合训练主代理和子代理，不同于先前仅优化主代理或向所有代理广播相同团队优势的方法。 ｜ LEAD-RL jointly trains main and subagents, unlike prior work that either optimizes only the main agent or shares the same team advantage with all agents.
• 训练时评分准则评估每个子代理报告的研究效用，并对其继承的团队优势进行门控，防止误导性报告被奖励。 ｜ A training-time rubric scores each subagent report's research utility and gates its inherited team advantage, preventing misleading reports from being rewarded.
• 唯一的团队奖励是最终答案正确性；不使用任何token、步骤或加速奖励。 ｜ The only team reward is final-answer correctness; no token, step, or speedup reward is used.
• 在五个基准和两个模型家族上，LEAD-RL提高了准确率并降低了关键路径成本；在BrowseComp上准确率提高2.49个百分点，成本降低24.5%。 ｜ Across five benchmarks and two model families, LEAD-RL improves accuracy and reduces critical-path cost; on BrowseComp it raises accuracy by 2.49 points and cuts cost by 24.5%.

**启示｜Implication**
实践者-哲学家应该关注，因为贡献感知的信用分配是在没有脆弱奖励塑形的情况下引导涌现的多智能体协调的具体机制，这与将智能体集体视为可观测效用梯度的计算系统进行调优的观点一致。 ｜ Practitioner-philosophers should care because contribution-aware credit assignment is a concrete mechanism for steering emergent multi-agent coordination without brittle reward shaping, aligning with the view that agent collectives can be tuned like computational systems with observable utility gradients.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Yang Zhou, Krish Agarwal, Zhuoming Chen, Zerui Wang, Zhenyu Zhang, Wenshuang Li, Xinpeng Wei, Zhichen Zeng, Jingyu Liu, Jue Wang, Sen Wu, Ziheng Jiang, Zhen Dong, Han Cai, Binhang Yuan, Ying Sheng, Ce Zhang, Bo Li, Beidi Chen** — Singularity-Bench：智能体能否构建智能体？（论文，2026-11-12） ｜ 📄 **Yang Zhou, Krish Agarwal, Zhuoming Chen, Zerui Wang, Zhenyu Zhang, Wenshuang Li, Xinpeng Wei, Zhichen Zeng, Jingyu Liu, Jue Wang, Sen Wu, Ziheng Jiang, Zhen Dong, Han Cai, Binhang Yuan, Ying Sheng, Ce Zhang, Bo Li, Beidi Chen** — Singularity-Bench: Can Agents Build Agents? (Paper, 2026-11-12)

**来源｜Source**：https://arxiv.org/abs/2611.16591

**摘要｜TL;DR**
Singularity-Bench 引入了一个开放式基准，包含六项端到端任务，用于自主 AI 开发，结果显示一个前沿智能体（Opus 5.5 搭配 Claude Code）以 1.25 的 Singularity-Index 达到或超过人类基线，而其他智能体平均仅为 0.58。 ｜ Singularity-Bench introduces an open-ended benchmark with six end-to-end tasks for autonomous AI development, showing that one frontier agent (Opus 5.5 with Claude Code) matches or exceeds human baselines with a Singularity-Index of 1.25, while other agents average 0.58.

**要点｜Takeaways**
• Singularity-Bench 覆盖预训练、中训练、后训练、推理、智能体框架和集群编排，要求智能体从最小起点实现核心系统。 ｜ Singularity-Bench covers pre-training, mid-training, post-training, inference, agent harness, and cluster orchestration, requiring agents to implement core systems from minimal starting points.
• 针对智能体应用 OWASP Top 10 的红队测试暴露了 Harbor 框架中的奖励黑客漏洞，由此开发出 Breakwater，可阻止所有被测攻击。 ｜ Red-teaming against OWASP Top 10 for Agentic Applications exposed reward-hacking in the Harbor framework, leading to Breakwater, which blocks all tested attacks.
• 在 11 个使用 7 种前沿模型和 2 种框架的智能体中，Opus 5.5 搭配 Claude Code 是唯一在全部六项任务上达到或超过人类基线的。 ｜ Across 11 agents using 7 frontier models and 2 harnesses, Opus 5.5 with Claude Code was the only one to match or beat human baselines on all six tasks.
• 该基准旨在追踪智能体何时从辅助 AI 开发过渡到端到端负责构建更强的继任者。 ｜ The benchmark aims to track when agents transition from assisting AI development to taking end-to-end responsibility for building stronger successors.

**启示｜Implication**
实践者-哲学家应当关注，因为它量化了 AI 智能体的自我改进能力——这是递归智能和自主代码塑造现实的临界时刻。 ｜ A practitioner-philosopher should care because this quantifies the self-improvement capacity of AI agents—a threshold moment for recursive intelligence and the shaping of reality by autonomous code.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Tiansheng Huang, Ananth Balashankar, Virat Shejwalkar, Santosh Pande, Ling Liu** — Bait：通过探测奖励函数缓解有害智能体强化学习（论文，2026-11-12） ｜ 📄 **Tiansheng Huang, Ananth Balashankar, Virat Shejwalkar, Santosh Pande, Ling Liu** — Bait: Mitigating Harmful Agentic Reinforcement Learning via Probing Reward Function (Paper, 2026-11-12)

**来源｜Source**：https://arxiv.org/abs/2611.16369

**摘要｜TL;DR**
该论文展示了有害的智能体强化学习可以低成本地颠覆大语言模型的安全对齐，并提出 Bait，一种通过探测奖励函数来阻断有害奖励学习同时保留良性任务学习的防御方法。 ｜ The paper demonstrates that harmful agentic reinforcement learning can cheaply subvert LLM safety alignment and proposes Bait, a reward-probing defense that blocks harmful reward learning while preserving benign task learning.

**要点｜Takeaways**
• 智能体强化学习即服务只需约 20 美元即可被攻击，完全颠覆模型的安全对齐。 ｜ Agentic RL-as-a-service can be attacked for as little as $20 to completely subvert a model's safety alignment.
• Bait 主动探测奖励函数以检测并缓解有害奖励学习。 ｜ Bait proactively probes the reward function to detect and mitigate harmful reward learning.
• 该防御能有效阻断有害奖励，同时仍能学习良性智能体任务。 ｜ The defense effectively blocks harmful rewards while still allowing learning from benign agentic tasks.
• 即使了解 Bait 的自适应攻击者也无法完美绕过它，因为存在系统性挑战。 ｜ Even adaptive attackers who know about Bait cannot perfectly bypass it due to a systematic challenge.

**启示｜Implication**
实践哲学家应关注此事，因为驾驭自主智能体需要保护奖励函数免受对抗性操纵，这是激励可编程时的核心挑战。 ｜ Practitioner-philosophers should care because steering autonomous agents requires securing reward functions against adversarial manipulation, a core challenge when incentives are programmable.

**综合评分｜CompositeScore**
4.6

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📝 **swyx .ai** — [AINews] D日（决策模型日）（博客，2026-11-12） ｜ 📝 **swyx .ai** — [AINews] D-Day (Decision Models Day) (Blog, 2026-11-12)

**来源｜Source**：https://latent.space/p/ainews-d-day-decision-models-day/

**摘要｜TL;DR**
谷歌的 Gemini Decision 1 开启了快速、廉价、校准的单次分类决策模型新类别，Cloudflare 的混合架构和最新评测展示了如何在智能体系统中大幅减少 LLM 调用和 token。 ｜ Google's Gemini Decision 1 ushers in a new class of fast, cheap, calibrated single-pass decision models, with Cloudflare's hybrid architecture and fresh evals showing how to slash LLM calls and tokens in agentic systems.

**要点｜Takeaways**
• Gemini Decision 1 支持最多 1000 个闭集问题、256K 上下文、约 200ms 端到端延迟、置信度评分，输入 token 仅 $0.10/M，在 7 项共享基准中有 5 项超越 Jev 1.14。 ｜ Gemini Decision 1 accepts up to 1,000 closed-set questions across modalities with 256K context, ~200ms end-to-end latency, confidence scores, and $0.10/M input tokens, beating Jev 1.14 on 5 of 7 shared benchmarks.
• Cloudflare 的混合智能体演示用快速决策模型处理工具选择和日志提取，仅在诊断时调用大型推理模型，将 6 次 LLM 调用减少到 1 次，约 4 万 token 降至 1.8K。 ｜ Cloudflare's hybrid agent demo uses fast decision models for tool selection/log extraction and a large reasoning model only for diagnosis, reducing six LLM calls to one and ~40K tokens to 1.8K.
• 独立评测显示 Decision 1 在 Decision Index 上与 Elephant 9B 和 Jev 打平，但在 Paperclip 上落后 Drex Max；单任务成本和延迟正成为与准确率同等重要的一级指标。 ｜ Independent evals show Decision 1 ties Elephant 9B and Jev on Decision Index but lags Drex Max on Paperclip; cost-per-task and latency are now first-class metrics alongside accuracy.
• Fable 5.2 以 +30.4% 净提升领跑 Agent Arena，而 Gemini 4 Carbon 因延迟遭诟病（低努力 22 分钟 vs Opus 高努力 9 分钟）；决策模型与智能体评测正按任务类型分化。 ｜ Fable 5.2 leads Agent Arena with +30.4% net improvement, while Gemini 4 Carbon draws latency complaints (22m low-effort vs 9m Opus high), and decision-model/agent evaluation is fragmenting by task type.
• Runway 的 Apache 2.0 世界动作模型 Praxis-1 在 RoboLab-120 排名第一，比 GPT-6 Astra 快 15.6 倍且成本低 51 倍，表明决策/动作模型正扩展到具身智能体。 ｜ Runway's Praxis-1 Apache 2.0 world action model ranks #1 on RoboLab-120, completing tasks 15.6x faster than GPT-6 Astra at 51x lower cost, showing decision/action models extend to embodied agents.

**启示｜Implication**
对于将 AI 与市场视为现实代码操纵者的实践哲学家而言，这类廉价、校准的决策模型为降低智能体操控中的 token/计算开销提供了实用机制，并暗示未来‘现实代码’可能由专用决策原语执行。 ｜ For a practitioner-philosopher treating AI + markets as reality-code manipulators, this shift to cheap, calibrated decision models offers a practical mechanism for reducing token/compute overhead in agent steering and hints at a future where 'reality code' is executed by specialized decision primitives.

**综合评分｜CompositeScore**
4.6

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Nguyen Minh Thang** — 包含、符合、比较（扩展版）：小型编码智能体的红队评估套件及其实验全记录（论文，2026-11-12） ｜ 📄 **Nguyen Minh Thang** — Contain, Conform, Compare (Extended Version): A Red-Teamed Evaluation Kit for Small Coding Agents and the Full Record of Its Experiments (Paper, 2026-11-12)

**来源｜Source**：https://arxiv.org/abs/2611.16485

**摘要｜TL;DR**
本文介绍一个经过红队测试的小型编码智能体本地评估套件，具备安全的容器隔离和评分器匹配检查，并公开了 9,660 次智能体运行和预注册实验的完整记录，结果显示提示词改进未获确认。 ｜ The paper presents a red-teamed local evaluation kit for small coding agents, with safe container isolation and scorer-matching checks, plus a full public record of 9,660 agent runs and pre-registered experiments showing no confirmed prompt improvements.

**要点｜Takeaways**
• drydock-eval 可在单张 RTX 5090 上以约每小时 250 次运行的速度安全评估小型编码智能体，并匹配托管评分器提示词。 ｜ drydock-eval safely evaluates small coding agents in fresh containers at ~250 runs/hour on one RTX 5090, matching hosted scorer prompts.
• 该套件通过了 200 次脚本化逃逸测试，并包含八项一致性检查，以对齐本地堆栈请求与评分器配置。 ｜ The kit passed 200 scripted escape tests and includes eight conformance checks to align local stack requests with the scorer configuration.
• 已公开 9,660 次智能体运行、2,494 个评分对照和 72 次服务测量；提示词和智能体包未公开。 ｜ 9,660 agent runs, 2,494 grading controls, and 72 serving measurements are released; prompts and agent bundles are withheld.
• 预注册五臂实验发现 E4B 上四种提示词偏差均无求解率变化；三项智能体改动在筛选阶段领先，但未能通过确认测试。 ｜ A pre-registered five-arm experiment found no solve-rate change from four prompt divergences on E4B; three agent changes showed screens but failed confirmation.
• 65% 的任务在八次运行中从未被解决，揭示了小型编码智能体评估的高方差与敏感性。 ｜ 65% of tasks were solved in none of eight runs, revealing high variance and sensitivity in small coding agent evaluation.

**启示｜Implication**
构建或引导编码智能体的实践者应采用严格的、安全的本地评估，结合红队测试和预注册实验，以避免被单一噪声分数误导。 ｜ Practitioners building or steering coding agents should adopt rigorous, safe, local evaluation with red-teaming and pre-registered experiments to avoid being misled by noisy single-number scores.

**综合评分｜CompositeScore**
4.6

**主题｜Topics**
智能体 ｜ Agent
