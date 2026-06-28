# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年06月21日 至 2026年06月28日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 世界模型中的幻觉是可预测且可预防的 ｜ Hallucination in World Models is Predictable and Preventable
- 🏅 [AINews] 元挽具之夏 ｜ [AINews] It's Meta-Harness Summer
- 🏅 Monday.com如何基于Deep Agents构建Sidekick / Interrupt 2026 ｜ How Monday.com Built Sidekick on Deep Agents / Interrupt 2026

---


**标题｜Title**
📺 **LangChain** — Monday.com如何基于Deep Agents构建Sidekick / Interrupt 2026（视频，2026-06-26） ｜ 📺 **LangChain** — How Monday.com Built Sidekick on Deep Agents / Interrupt 2026 (Video, 2026-06-26)

**来源｜Source**：https://www.youtube.com/watch?v=c2fLLS7np3Y

**摘要｜TL;DR**
讲解使用Deep Agents构建monday.com的Sidekick助理的生产实践，包含实现94%错误恢复率的四项关键原则。 ｜ A production walkthrough of building monday.com's Sidekick assistant using Deep Agents, with four key principles enabling 94% error recovery.

**要点｜Takeaways**
• 使用LangChain ReAct的V1版本因200个工具导致上下文污染而失败，需要基于Deep Agents重构。 ｜ V1 using LangChain ReAct failed due to context pollution with 200 tools; rebuild with Deep Agents was needed.
• 延迟工具发现的三层系统减少了上下文负荷并提升相关性。 ｜ Deferred tool discovery using a three-tier system reduces context load and improves relevance.
• 以委派为先的方法结合子代理和异步交接，最小化协调器任务。 ｜ Delegation-first approach with sub-agents and async handoff minimizes orchestrator tasks.
• 自愈循环在生产环境中实现了94%的错误恢复成功率。 ｜ Self-healing loops enable 94% error recovery rate in production.

**启示｜Implication**
它展示了代理系统的实用扩展模式，弥合了实验性LLM循环与稳健的现实世界AI助手之间的差距，这对于构建或理论化自主数字实体的人至关重要。 ｜ It demonstrates practical scaling patterns for agentic systems, bridging the gap between experimental LLM loops and robust real-world AI assistants—essential for those building or theorizing about autonomous digital entities.

**综合评分｜CompositeScore**
5.0

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Nicklas Hansen, Xiaolong Wang** — 世界模型中的幻觉是可预测且可预防的（论文，2026-06-25） ｜ 📄 **Nicklas Hansen, Xiaolong Wang** — Hallucination in World Models is Predictable and Preventable (Paper, 2026-06-25)

**来源｜Source**：https://arxiv.org/abs/2606.27326

**摘要｜TL;DR**
该论文表明，世界模型中的幻觉可通过数据覆盖信号进行预测和预防，从而实现可靠的智能体训练，并仅需少量真实轨迹进行微调。 ｜ The paper demonstrates that hallucinations in world models are predictable and preventable using data-coverage signals, enabling reliable agent training and finetuning on as few as 50 real trajectories.

**要点｜Takeaways**
• 幻觉集中于状态-动作空间的低覆盖区域。 ｜ Hallucinations concentrate in low-coverage regions of state-action space.
• 识别了三种幻觉模式：感知型、动作边缘化型和场景发散型。 ｜ Three distinct hallucination modes are identified: perceptual, action-marginalized, and scene-diverging.
• 轻量信号可准确预测世界模型将在何处失败。 ｜ Lightweight signals accurately predict where world models will fail.
• 训练时采用覆盖率感知采样来弥补覆盖缺口。 ｜ Coverage-aware sampling during training closes coverage gaps.
• 以幻觉预测器作为好奇心奖励进行数据收集，仅需50条真实轨迹即可适应全新环境。 ｜ Curiosity-driven data collection using hallucination predictors adapts models to unseen environments with minimal real data.

**启示｜Implication**
如果现实是可计算的模拟，那么构建无幻觉的世界模型对于构建能正确操纵该模拟的智能体至关重要。 ｜ If reality is a computable simulation, hallucination-free world models are essential for building agents that can reliably manipulate that simulation.

**综合评分｜CompositeScore**
5.0

**主题｜Topics**
智能体, 模拟 ｜ Agent, Simulation
---


**标题｜Title**
📝 **Latent Space** — [AINews] 元挽具之夏（博客，2026-06-25） ｜ 📝 **Latent Space** — [AINews] It's Meta-Harness Summer (Blog, 2026-06-25)

**来源｜Source**：https://www.latent.space/p/ainews-its-meta-harness-summer

**摘要｜TL;DR**
本周 AI 新闻重点包括元挽具框架、OpenAI 定制芯片、从工具到同事的智能体体验演变，以及开源智能体世界模型。 ｜ This week's AI news highlights meta-harness frameworks, OpenAI's custom chip, agent UX as coworkers, and open source agent world models.

**要点｜Takeaways**
• 元挽具正在成为生产中编排多样化 AI 智能体的关键模式。 ｜ Meta-harnesses are emerging as a key pattern for orchestrating diverse AI agents in production.
• 智能体体验正从工具转向同事，带来安全与成本挑战。 ｜ Agent UX is shifting from tools to coworkers, raising security and cost challenges.
• 记忆正成为智能体扩展与差异化的关键系统层。 ｜ Memory is becoming a critical systems layer for agent scaling and differentiation.
• 像 Qwen-AgentWorld 这样的开源智能体世界模型可能通过模拟引导更好的智能体训练。 ｜ Open-source agent world models like Qwen-AgentWorld could bootstrap better agent training through simulation.

**启示｜Implication**
实践哲学家应关注智能体编排与记忆基础设施的演进，它们正重塑自主系统如何与现实互动并潜在地模拟现实。 ｜ Practitioner-philosophers should track agent orchestration and memory infrastructure as they reshape how autonomous systems interact with and potentially simulate reality.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — 如何使用LangSmith Engine和Context Hub构建自我改进的智能体（视频，2026-06-24） ｜ 📺 **LangChain** — How To Build a Self-Improving Agent with LangSmith Engine and Context Hub (Video, 2026-06-24)

**来源｜Source**：https://www.youtube.com/watch?v=y6WUw2_Hhrs

**摘要｜TL;DR**
本教程演示了如何通过LangSmith Engine和Context Hub将生产追踪数据转化为持久性记忆更新，从而创建自我改进的智能体。 ｜ This tutorial demonstrates how to create a self-improving agent by converting production traces into durable memory updates using LangSmith Engine and Context Hub.

**要点｜Takeaways**
• 智能体可通过将追踪数据反馈到记忆中来克服重复性错误。 ｜ Agents can overcome repetitive mistakes by closing the loop from traces to memory.
• 工作记忆与长期记忆（包含三种类型）对智能体学习至关重要。 ｜ Working memory vs long-term memory (with three types) are essential for agent learning.
• LangSmith Engine自动扫描追踪数据，识别如禁用填充词等问题。 ｜ LangSmith Engine scans traces to automatically surface issues like banned filler words.
• Context Hub提供可版本化、持久化的记忆，跨会话持续存在。 ｜ The Context Hub allows versioned, durable memory that persists across sessions.
• 演示展示了从构建NOVA到应用自动修复的完整流程。 ｜ The demo shows a complete pipeline from building NOVA to applying automated fixes.

**启示｜Implication**
实践哲学家应关注，因为它实现了学习智能体的反馈循环，弥合了瞬时执行与持久智能提升之间的鸿沟。 ｜ Practitioner-philosophers should care because it operationalizes the feedback loop of learning agents, bridging the gap between transient execution and persistent intelligence improvement.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — Clay如何每月运行3.5亿个GTM智能体 / Interrupt 26（视频，2026-06-24） ｜ 📺 **LangChain** — How Clay runs 350 million GTM agents a month / Interrupt 26 (Video, 2026-06-24)

**来源｜Source**：https://www.youtube.com/watch?v=LmQtSORYPfw

**摘要｜TL;DR**
Clay的AI负责人详解他们如何通过解决基础设施可靠性、吞吐量、成本和智能体质量，每月运行3.5亿个面向市场的智能体。 ｜ Clay’s Head of AI details how they run 350 million go-to-market agents monthly by solving infrastructure reliability, throughput, cost, and agent quality.

**要点｜Takeaways**
• 通过持久化工作流执行实现可靠的智能体基础设施。 ｜ Achieve durable workflow execution for reliable agent infrastructure.
• 用类TCP/IP的方法处理速率限制和突发吞吐量。 ｜ Use a TCP/IP-inspired approach to handle rate limits and spiky throughput.
• 通过战略性缓存LLM调用降低70%成本。 ｜ Reduce costs by 70% with strategic caching of LLM calls.
• 通过恰当的上下文提供和系统性评估维持智能体质量。 ｜ Maintain agent quality through proper context provisioning and systematic evals.
• 新产品Audiences为智能体提供自主上下文以推荐行动。 ｜ New Audiences product gives agents autonomous context to recommend actions.

**启示｜Implication**
在生产环境中扩展智能体的从业者可以借鉴Clay经过实战检验的可靠性、成本和质量模式，而“3.5亿智能体”标志着自主市场操控作为可计算现实的成熟化。 ｜ Practitioners scaling agents in production can adopt Clay’s battle-tested patterns for reliability, cost, and quality, while the ‘350 million agents’ signal a maturation of autonomous market manipulation as computable reality.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
