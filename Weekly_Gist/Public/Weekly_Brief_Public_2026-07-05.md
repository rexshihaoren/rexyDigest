# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年06月28日 至 2026年07月05日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 Fable的判断力 ｜ Fable's judgement
- 🏅 Vercel的Andrew Qu谈为什么智能体是一种新型软件 ｜ Vercel's Andrew Qu on why agents are a new kind of software
- 🏅 如何正确自动化AI评估 ｜ How to Automate AI Evals (Correctly)

---


**标题｜Title**
📝 **Simon Willison** — Fable的判断力（博客，2026-07-03） ｜ 📝 **Simon Willison** — Fable's judgement (Blog, 2026-07-03)

**来源｜Source**：https://simonwillison.net/2026/Jul/3/judgement/

**摘要｜TL;DR**
一种实用技巧，让AI编程代理自行判断何时编写测试以及将任务委派给更便宜的模型，从而提高效率和节约成本。 ｜ A practical tip to let AI coding agents use their own judgment for when to write tests and delegate coding tasks to cheaper models, improving efficiency and cost.

**要点｜Takeaways**
• 指示AI自行判断何时编写测试，而不是硬编码规则。 ｜ Instruct the AI to use its own judgment on when to write tests instead of hard-coding rules.
• 告诉Claude根据自身判断将实现任务委派给较小的模型（如Sonnet、Haiku）。 ｜ Tell Claude to delegate implementation tasks to smaller models (e.g., Sonnet, Haiku) based on its own judgment.
• 这样可以节省昂贵模型的令牌成本，同时将高质量工作保留在主模型中。 ｜ This saves expensive model tokens while keeping quality work in the main model.
• 将委派提示作为项目的持久记忆文件保存。 ｜ Store the delegation prompt as a persistent memory file for the project.

**启示｜Implication**
这一技巧将更多自主权交给AI，将其视为有判断力的合作者而非僵化的工具，这是构建有效自主代理的关键模式。 ｜ This technique shifts more autonomy to the AI, treating it as a judgmental collaborator rather than a rigid tool, a key pattern for building effective autonomous agents.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📝 **Richard MacManus** — Vercel的Andrew Qu谈为什么智能体是一种新型软件（博客，2026-07-03） ｜ 📝 **Richard MacManus** — Vercel's Andrew Qu on why agents are a new kind of software (Blog, 2026-07-03)

**来源｜Source**：https://www.latent.space/p/vercel-agents-new-software

**摘要｜TL;DR**
Vercel首席软件官解释智能体为何是新的软件范式，需要可恢复性、技能和智能体可读内容等新原语，并分享构建自有智能体框架eve的经验。 ｜ Vercel's Chief of Software explains why agents are a new software paradigm requiring new primitives like resumability, skills, and agent-readable content, and shares lessons from building their own agent framework eve.

**要点｜Takeaways**
• 智能体不仅是另一种应用，它们需要为动态、长时运行、可恢复交互而设计的新基础设施。 ｜ Agents are not just another app; they demand new infrastructure for dynamic, long-running, resumable interactions.
• 技能是便携的按需知识，可纠正模型中过时的信息，让智能体更可靠。 ｜ Skills are portable, on-demand knowledge that correct outdated model information, making agents more reliable.
• 检测智能体请求并提供机器可读格式（如Markdown）可提升智能体可用性。 ｜ Detecting agent requests and serving machine-readable formats (e.g., Markdown) improves agent usability.
• 多人智能体开发旨在跨团队共享情境技巧。 ｜ Multiplayer agent development aims to share contextual techniques across teams.
• Vercel自身正在成为智能体，将智能体能力集成到整个平台。 ｜ Vercel is becoming an agent itself, integrating agent capabilities across its platform.

**启示｜Implication**
对实践哲学家而言，这次访谈勾画了将LLM转化为高效自主智能体的前沿，这是认识到一切现实可能皆为由此类代码实体操控的计算过程的第一步。 ｜ For a practitioner-philosopher, this interview maps the frontier of turning LLMs into effective autonomous agents, which is step one toward recognizing that all reality may be a computational process manipulable by such code-entities.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **Hamel Husain** — 如何正确自动化AI评估（视频，2026-07-03） ｜ 📺 **Hamel Husain** — How to Automate AI Evals (Correctly) (Video, 2026-07-03)

**来源｜Source**：https://www.youtube.com/watch?v=tqUDjc1HzO4

**摘要｜TL;DR**
Shreya Shankar 阐述了自动化AI评估的三个常见误区，并演示了一个有效规模化人工判断的工作流程。 ｜ Shreya Shankar explains three common pitfalls in automating AI evaluations and demonstrates a workflow to scale human judgment effectively.

**要点｜Takeaways**
• 自动化评估需要与人类判断对齐，而非仅检测表面问题。 ｜ Automating evals requires aligning with human judgment, not just surface-level issue detection.
• 构建评审界面以标注轨迹并建立故障模式分类法。 ｜ Build a review interface to annotate traces and create a failure mode taxonomy.
• 迭代审查数据；一次性分析会遗漏不断演变的错误。 ｜ Iteratively review data; one-time analysis misses evolving errors.
• 不同应用有不同的准确性要求，需定制评估。 ｜ Different applications have different accuracy requirements; tailor evals accordingly.
• 通用型智能体有时可超越专用评估工具。 ｜ General-purpose agents can sometimes outperform dedicated eval tools.

**启示｜Implication**
对于构建自主智能体的实践型哲学家而言，掌握评估方法对于可靠地驾驭和调试智能体至关重要，而该方法桥接了自动化指标与有意义的人类监督之间的鸿沟。 ｜ For a practitioner-philosopher building autonomous agents, mastering evals is essential to steer and debug them reliably, and this methodology bridges the gap between automated metrics and meaningful human oversight.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — 动态子代理：如何在 Deep Agents 中可靠地并行运行代理（视频，2026-06-29） ｜ 📺 **LangChain** — Dynamic Subagents: How to Run Parallel Agents Reliably in Deep Agents (Video, 2026-06-29)

**来源｜Source**：https://www.youtube.com/watch?v=5AkdMangfNk

**摘要｜TL;DR**
LangChain 的 Deep Agents 允许通过代码编程生成和协调并行子代理，利用六种模式确保可靠的控制流和可扩展的编排。 ｜ LangChain's Deep Agents enables programmatic spawning and coordination of parallel subagents via code, ensuring reliable control flow and scalable orchestration through six distinct patterns.

**要点｜Takeaways**
• 动态子代理将编排从代理推理转移到代码，防止上下文丢失和错误。 ｜ Dynamic subagents shift orchestration from agent reasoning to code, preventing context loss and errors.
• 六种模式（分类与行动、分发与综合、对抗验证、生成与过滤、锦标赛、循环至完成）覆盖常见的多代理工作流。 ｜ Six patterns (Classify & Act, Fan Out & Synthesize, Adversarial Verification, Generate & Filter, Tournament, Loop Until Done) cover common multi‑agent workflows.
• 通过代码解释器中间件，代理可以使用任务全局变量和工作流关键字编程生成子代理。 ｜ Using a code interpreter middleware, the agent can spawn subagents programmatically with a task global and workflow keyword.
• 实时的 LangSmith 追踪展示了可靠的 15 代理并行执行与综合。 ｜ Live LangSmith traces demonstrate reliable 15‑agent parallel execution and synthesis.
• 该方法已可用于生产，为非确定性 LLM 调用提供了确定性控制。 ｜ The approach is production‑ready, offering deterministic control over otherwise non‑deterministic LLM calls.

**启示｜Implication**
这项技术在代理自主性与工程师控制的执行之间架起桥梁，为模拟架构师信赖的稳健、大规模代理系统提供了蓝图。 ｜ This technique bridges agentic autonomy with engineer‑controlled execution, offering a blueprint for robust, large‑scale agent systems that a simulation architect could rely on.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — GLM 5.2 + dcode：借助开源模型的前沿编码（视频，2026-07-01） ｜ 📺 **LangChain** — GLM 5.2 + dcode: Frontier Coding with Open Models (Video, 2026-07-01)

**来源｜Source**：https://www.youtube.com/watch?v=wVB95vLg_FQ

**摘要｜TL;DR**
一份实践指南，展示如何使用具备百万 token 上下文窗口的开源模型 GLM 5.2 搭配开源编程智能体 dcode，并通过 LangSmith 追踪其执行过程。 ｜ A hands-on guide to using GLM 5.2, an open-weight model with a 1M context window, with dcode, an open-source coding agent, and tracing its execution in LangSmith.

**要点｜Takeaways**
• GLM 5.2 在编程基准上接近 Claude Opus/GPT-5.5，且采用 MIT 许可证。 ｜ GLM 5.2 achieves near-Claude Opus/GPT-5.5 coding benchmarks with an MIT license.
• dcode 是一个模型无关的开源智能体，可利用此类模型完成编码任务。 ｜ dcode is a model-agnostic open-source agent that can leverage such models for coding tasks.
• LangSmith 提供对智能体工具调用和推理过程的逐步追踪。 ｜ LangSmith provides full step-by-step tracing of the agent's tool calls and reasoning.
• 组合开源模型与专用智能体可以弥合与前沿闭源方案的差距。 ｜ Combining open models with specialized agents bridges the gap to frontier proprietary solutions.
• 安装配置简便，支持快速实验。 ｜ The setup is straightforward, enabling rapid experimentation.

**启示｜Implication**
对于实践哲学家而言，这表明可检查的开源智能系统正在接近黑箱前沿模型的水平，使“现实代码操纵者”更加易于获取和审计。 ｜ For the practitioner-philosopher, this demonstrates that open, inspectable agentic systems are approaching parity with black-box frontier models, making the 'reality-code manipulators' more accessible and auditable.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
