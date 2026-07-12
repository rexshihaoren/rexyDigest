# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年07月05日 至 2026年07月12日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 在 LangSmith 中跟踪每个 Claude Code 会话只需几分钟 ｜ Trace Every Claude Code Session in LangSmith in Minutes
- 🏅 全新的 GPT-5.6 系列：Luna、Terra、Sol ｜ The new GPT-5.6 family: Luna, Terra, Sol
- 🏅 黄仁勋：为何企业需要开放智能体系统 ｜ Jensen Huang: Why companies need open agent systems

---


**标题｜Title**
📺 **LangChain** — 在 LangSmith 中跟踪每个 Claude Code 会话只需几分钟（视频，2026-07-09） ｜ 📺 **LangChain** — Trace Every Claude Code Session in LangSmith in Minutes (Video, 2026-07-09)

**来源｜Source**：https://www.youtube.com/watch?v=jLOM_ahG78c

**摘要｜TL;DR**
一份分步指南，教您配置 Claude Code 以将每次会话追踪到 LangSmith 中，实现对代理消息、工具调用和子代理运行的全面可观测性。 ｜ A step-by-step guide to configuring Claude Code to trace every session into LangSmith, enabling full observability into agent messages, tool calls, and sub-agent runs.

**要点｜Takeaways**
• 安装 LangSmith 追踪插件以捕获 Claude Code 会话。 ｜ Install the LangSmith tracing plugin to capture Claude Code sessions.
• 配置一个小型 JSON 设置文件，将插件指向 LangSmith。 ｜ Configure a small JSON settings file to point the plugin at LangSmith.
• 在启用追踪的情况下启动 Claude Code，并在 LangSmith 中查看详细的追踪数据。 ｜ Launch Claude Code with tracing enabled and view detailed traces in LangSmith.
• 使用 Threads 标签页跟踪完整的多次往返会话并调试代理行为。 ｜ Use the Threads tab to follow full multi-turn sessions and debug agent behavior.

**启示｜Implication**
构建自主代理的实践哲学家可以立即获得代理决策的透明度，将黑盒会话转变为可调试、可观测的过程。 ｜ Practitioner-philosophers building autonomous agents gain immediate transparency into agent decision-making, turning black-box sessions into debuggable, observable processes.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📝 **Simon Willison** — 全新的 GPT-5.6 系列：Luna、Terra、Sol（博客，2026-07-09） ｜ 📝 **Simon Willison** — The new GPT-5.6 family: Luna, Terra, Sol (Blog, 2026-07-09)

**来源｜Source**：https://simonwillison.net/2026/Jul/9/gpt-5-6/

**摘要｜TL;DR**
OpenAI 发布了三个规格的 GPT-5.6 模型，声称在智能体基准测试中占据领先地位，并引入了多智能体编排和编程工具调用等 API 功能。 ｜ OpenAI released GPT-5.6 with three sizes, claiming top agentic benchmark performance and introducing API features for multi-agent orchestration and programmatic tool calling.

**要点｜Takeaways**
• GPT-5.6 提供 Luna、Terra、Sol 三种规格，针对智能体任务提供不同的定价和性能。 ｜ GPT-5.6 comes in Luna, Terra, Sol tiers with varying pricing and performance for agentic tasks.
• Sol 在 Agents’ Last Exam 基准测试中创下新高，超越 Claude Fable 5 13.1 分。 ｜ Sol achieves a new high on the Agents’ Last Exam benchmark, outperforming Claude Fable 5 by 13.1 points.
• 编程工具调用允许模型编写并运行 JavaScript 来协调工具调用，衔接 MCP 和 CLI 会话。 ｜ Programmatic Tool Calling lets models compose and run JavaScript to orchestrate tool calls, bridging MCPs and CLI sessions.
• 新的多智能体 API 可从核心模型直接生成子智能体，用于并行、专注的工作。 ｜ New Multi-agent API spins up subagents for parallel, focused work directly from the core model.
• 提示缓存断点提供显式控制以优化成本，与自动检测相辅相成。 ｜ Prompt cache breakpoints give explicit control for cost optimization, complementing automatic detection.

**启示｜Implication**
这些在智能体编排和工具使用能力上的进步，直接增强了创建更自主、更高效的 AI 智能体的能力，这些智能体在操纵数字现实。 ｜ These advancements in agentic orchestration and tool-use capabilities directly empower the creation of more autonomous and efficient AI agents that manipulate digital reality.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — 黄仁勋：为何企业需要开放智能体系统（视频，2026-07-08） ｜ 📺 **LangChain** — Jensen Huang: Why companies need open agent systems (Video, 2026-07-08)

**来源｜Source**：https://www.youtube.com/watch?v=Yy3JH6dDugc

**摘要｜TL;DR**
黄仁勋与Harrison Chase探讨构建开放、专业化的智能体系统，并宣布用于企业部署的Deep Agents + OpenShell蓝图。 ｜ Jensen Huang and Harrison Chase discuss building open, specialized agent systems, announcing the Deep Agents + OpenShell blueprint for enterprise deployment.

**要点｜Takeaways**
• 企业应基于开放框架构建领域特定的“超级智能体”，而非僵化的业务流程。 ｜ Companies should build domain-specific 'super agents' on open harnesses rather than rigid business processes.
• Nemotron 3 Ultra以低成本实现接近前沿的性能，使更便宜、更快速的智能成为可能。 ｜ Nemotron 3 Ultra offers near-frontier performance at low cost, enabling cheaper, faster intelligence.
• 前沿模型适合探索，而专用模型更适合生产部署。 ｜ Frontier models are best for exploration, while specialized models are better for production deployment.
• NVIDIA与LangChain的新蓝图（在OpenShell上运行Nemotron的Deep Agents）为企业智能体提供了安全、开放的运行时环境。 ｜ NVIDIA and LangChain's new blueprint (Deep Agents with Nemotron on OpenShell) provides a secure, open runtime for enterprise agents.
• 更多人工智能通过增强人类能力来创造更多就业机会。 ｜ More AI leads to more jobs by augmenting human capabilities.

**启示｜Implication**
这次讨论揭示了工具型大语言模型和自主智能体的前沿，展示了开放、专业化的系统如何成为操控复杂信息环境的基石，这是迈向在可计算系统中工程化智能的实际一步。 ｜ This discussion reveals the frontier of tool-using LLMs and autonomous agents, showing how open, specialized systems are becoming the building blocks for manipulating complex information environments, a practical step toward engineering intelligence in computable systems.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Corban Villa, Alp Eren Ozdarendeli, Sijun Tan, Raluca Ada Popa** — Prismata: 限制網頁代理中的跨站提示注入（论文，2026-07-09） ｜ 📄 **Corban Villa, Alp Eren Ozdarendeli, Sijun Tan, Raluca Ada Popa** — Prismata: Confining Cross-Site Prompt Injection in Web Agents (Paper, 2026-07-09)

**来源｜Source**：https://arxiv.org/abs/2607.08147

**摘要｜TL;DR**
Prismata 是一种防御系统，为网页代理动态执行上下文最小权限，以缓解跨站提示注入攻击，无需开发者注释。 ｜ Prismata is a defense system that dynamically enforces contextual least privilege for web agents to mitigate cross-site prompt injection attacks without requiring developer annotations.

**要点｜Takeaways**
• Prismata 利用结构限制保证为页面内容导出动态信任标签，减少攻击面。 ｜ Prismata derives dynamic trust labels for page content using structural confinement guarantees, reducing attack surface.
• 它根据这些标签机械地编辑不可信内容并限制代理能力。 ｜ It mechanically redacts untrusted content and restricts agent capabilities based on these labels.
• 该防御无需手动网站注释，可扩展到长尾网站。 ｜ The defense requires no manual website annotations, scaling to the long tail of the web.
• 评估显示，在各种网页代理攻击中，攻击成功率大幅降低，同时保持良性任务效用。 ｜ Evaluations show substantial reduction in attack success across various web agent attacks while preserving benign task utility.

**启示｜Implication**
它将经典安全完整性模型与现代 LLM 代理相结合，实现安全的自主网页交互，体现了对数字现实代码进行约束性操纵的原则。 ｜ It merges classical security integrity models with modern LLM agents, enabling safe autonomous web interaction and embodying the principle of constrained manipulation of the digital reality-code.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — OpenWiki 大脑：为智能体提供的通用记忆（视频，2026-07-10） ｜ 📺 **LangChain** — OpenWiki Brains, general-purpose memory for agents (Video, 2026-07-10)

**来源｜Source**：https://www.youtube.com/watch?v=sBg90v2qfas

**摘要｜TL;DR**
OpenWiki 0.1.0 通过自动维护的个人维基为智能体提供了通用记忆。 ｜ OpenWiki 0.1.0 provides agents with a general-purpose memory via an automatically maintained personal wiki.

**要点｜Takeaways**
• OpenWiki 使智能体能够拥有持久的、通用的记忆。 ｜ OpenWiki enables agents to have persistent, general-purpose memory.
• 它会在智能体交互时自动生成并更新维基。 ｜ It automatically generates and updates a wiki as the agent interacts.
• 与现有的 LangChain 工具和生态系统集成。 ｜ Integrates with existing LangChain tools and ecosystems.
• 提供了一种检查和调试智能体记忆的方法。 ｜ Provides a way to inspect and debug agent memory.
• 通过减少上下文丢失来增强智能体的自主性。 ｜ Enhances agent autonomy by reducing context loss.

**启示｜Implication**
实践哲学家应关注，因为强大的记忆基底对于构建能够长期保持连贯身份和知识的智能体至关重要，是迈向可能互动并塑造模拟现实的复杂自主系统的一步。 ｜ Practitioner-philosophers should care because a robust memory substrate is critical for building agents that can maintain coherent identity and knowledge over time, a step toward sophisticated autonomous systems potentially interacting with and shaping simulated realities.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
