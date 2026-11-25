# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年08月23日 至 2026年08月30日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 破解 Claude Code Opus 5 自动模式 ｜ Breaking Claude Code Opus 5 Auto Mode
- 🏅 Clay 的 Eval 栈内部：3 亿次 Agent 运行，一条 LangSmith 流水线 ｜ Inside Clay's Eval Stack: 300M Agent Runs, One LangSmith Pipeline
- 🏅 如何实际评估AI智能体？ ｜ How Do You Actually Evaluate an AI Agent?

---


**标题｜Title**
📝 **Simon Willison** — 破解 Claude Code Opus 5 自动模式（博客，2026-08-27） ｜ 📝 **Simon Willison** — Breaking Claude Code Opus 5 Auto Mode (Blog, 2026-08-27)

**来源｜Source**：https://simonwillison.net/2026/Aug/27/breaking-claude-code-opus-5-auto-mode/

**摘要｜TL;DR**
Simon Willison 报道了 Johann Rehberger 的提示注入攻击，该攻击通过将恶意 struct.py 隐藏在 zip 中执行任意代码，80% 的情况下绕过了 Claude Code Opus 5 的自动模式，并建议将沙箱作为唯一安全防御。 ｜ Simon Willison reports on Johann Rehberger's prompt injection attack that bypasses Claude Code Opus 5's Auto Mode 80% of the time by hiding a malicious struct.py in a zip to execute arbitrary code, and recommends sandboxing as the only safe defense.

**要点｜Takeaways**
• 自动模式的安全分类器可能被诱骗允许恶意软件执行，同时阻止智能体自身的清理命令。 ｜ Auto Mode's safety classifier can be tricked into allowing malware execution while blocking the agent's cleanup attempt.
• 该攻击通过利用 zip 解压后导入本地 struct.py，成功率约 80%。 ｜ The attack works ~80% of the time by exploiting a local struct.py import after zip extraction.
• 即使智能体检测到入侵，自动模式也可能拒绝停止恶意进程的命令。 ｜ Even when the agent detects compromise, Auto Mode may deny the command to stop the malicious process.
• 对于无人值守的编码智能体，应在容器、虚拟机或操作系统沙箱中运行，限制网络出口，且不要暴露主目录、SSH 密钥或云凭据。 ｜ For unattended coding agents, run them in a container/VM/sandbox, restrict network egress, and avoid exposing credentials or home directories.
• 提示注入仍是自主智能体的核心未解决风险，因此监控至关重要。 ｜ Prompt injection remains a core unsolved risk for autonomous agents, so monitoring is essential.

**启示｜Implication**
构建或部署智能体的实践型哲学家必须将智能体自身的安全机制视为易受对抗性操纵的脆弱代码，从而强化对外部确定性沙箱边界的依赖，而不是信任模型判断。 ｜ Practitioner-philosophers building or deploying agents must treat the agent's own safety mechanisms as fallible code subject to adversarial manipulation, reinforcing the need for external, deterministic sandbox boundaries rather than trusting model judgment.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — Clay 的 Eval 栈内部：3 亿次 Agent 运行，一条 LangSmith 流水线（视频，2026-08-28） ｜ 📺 **LangChain** — Inside Clay's Eval Stack: 300M Agent Runs, One LangSmith Pipeline (Video, 2026-08-28)

**来源｜Source**：https://www.youtube.com/watch?v=Uny6LpmjraI

**摘要｜TL;DR**
Clay 的 AI 团队详细介绍了他们如何使用 LangSmith、数据湖和 Fable 的大上下文突破，为市场推广智能体（Claygent 和 Sculptor）在 3 亿次智能体运行中扩展评估。 ｜ Clay's AI team details how they scaled evaluations for their go-to-market agents (Claygent and Sculptor) across 300 million agent runs using LangSmith, a data lake, and Fable's large context breakthrough.

**要点｜Takeaways**
• 包含四个象限的评估已成为从本地开发到 CI 安全发布智能体变更的必备条件。 ｜ Evals with four quadrants became non-negotiable for safely shipping agentic changes from local dev to CI.
• 数据湖架构使智能体能够一等公民地访问 Clay 的生产数据。 ｜ A data lake architecture gives agents first-class access to Clay's production data.
• Fable 的大上下文突破让智能体可以处理更大的生产数据上下文。 ｜ Fable's large context breakthrough allows agents to handle much larger production data contexts.
• 通过 LangSmith 闭合生产与离线评估之间的循环，提高了智能体的可靠性。 ｜ Closing the loop between production and offline evals via LangSmith improves agent reliability.
• 外部智能体创造了一个通向智能体界面的内部飞轮。 ｜ External agents create an internal flywheel toward an agent interface.

**启示｜Implication**
这表明严格的评估和数据基础设施是大规模操纵现实代码的自主智能体的控制面。 ｜ This shows how rigorous evals and data infrastructure are the control surfaces for autonomous agents that manipulate reality-code at scale.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **LangChain** — 如何实际评估AI智能体？（视频，2026-08-26） ｜ 📺 **LangChain** — How Do You Actually Evaluate an AI Agent? (Video, 2026-08-26)

**来源｜Source**：https://www.youtube.com/watch?v=wiJk8b_vjt0

**摘要｜TL;DR**
评估AI智能体需要定义什么是“好”，并经常使用LLM作为裁判，基于真实世界数据集持续运行，而不是测试精确输出。 ｜ Evaluating AI agents requires defining what good looks like and using an LLM as judge, with a real-world dataset run continuously, rather than testing for exact outputs.

**要点｜Takeaways**
• 定义质量标准，而不是期望精确输出。 ｜ Define quality criteria instead of expecting exact outputs.
• 使用LLM作为自然语言输出的裁判。 ｜ Use an LLM as judge for natural language outputs.
• 构建包含真实世界示例和边缘情况的数据集。 ｜ Build a dataset of real-world examples and edge cases.
• 每次智能体发生变化时都运行评估，而不仅仅在发布前。 ｜ Run evals every time the agent changes, not just before shipping.
• 将评估视为持续练习，而非一次性检查。 ｜ Treat evals as a continuous practice, not a one-time check.

**启示｜Implication**
如果智能体是现实代码的操纵者，那么稳健的评估就是让自主系统在可计算世界中保持一致和可调试的反馈回路。 ｜ If agents are reality-code manipulators, robust evaluation is the feedback loop that keeps autonomous systems aligned and debuggable in a computable world.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📝 **Latent Space** — [AINews] 吴恩达进军 AI 工程（博客，2026-08-25） ｜ 📝 **Latent Space** — [AINews] Andrew Ng gets into AI Engineering (Blog, 2026-08-25)

**来源｜Source**：https://www.latent.space/p/ainews-andrew-ng-gets-into-ai-engineering

**摘要｜TL;DR**
Latent Space 的 AINews 重点介绍了吴恩达的 AI 工程技能分类，以及代理 harness、持久化代理和企业 MCP 基础设施的一系列实用进展。 ｜ Latent Space's AINews highlights Andrew Ng's AI Engineering skill taxonomy and a wave of practical agent-harness, persistent-agent, and enterprise-MCP infrastructure advances.

**要点｜Takeaways**
• 吴恩达提出四项核心 AI 工程技能：构建与部署 AI 应用、软件工程基础、使用编码代理以及塑造构建。 ｜ Andrew Ng identifies four core AI engineering skills: building/deploying AI applications, software fundamentals, using coding agents, and shaping the build.
• NVIDIA 提出“技能提升”（Skill Lift），通过相同任务在有无技能下的完成增量来衡量代理技能，而非静态清单评分（Spearman 0.14）。 ｜ NVIDIA proposes 'Skill Lift' to measure agent skills by task-completion delta rather than static checklist scores (Spearman 0.14).
• 开源持久化代理（Headlong、exo）引入连续运行、DAG 轨迹、回滚和自我修改，背景运行成本为每小时 1-2 美元。 ｜ Open-source persistent agents (Headlong, exo) introduce continuous operation, DAG trajectories, rollback, and self-modification with $1-2/hr background cost.
• Anthropic 的企业 MCP 认证和路线图（流式、HTTP、渐进发现）填补了企业级可审计代理部署的缺口。 ｜ Anthropic's enterprise MCP auth and roadmap (streaming, HTTP, discovery) close gaps for auditable enterprise agent deployment.

**启示｜Implication**
实践者-哲学家应关注，因为本周在代理 harness、持久化和度量上的进展，细化了我们驾驭计算代理的能力——这种驾驭能力正使现实代码变得越来越可调试。 ｜ A practitioner-philosopher should care because this week's advances in harness design, persistence, and measurement refine how we steer computational agents—the same steering capacity that makes reality code increasingly debuggable.

**综合评分｜CompositeScore**
4.6

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📺 **Hamel Husain** — 不要构建智能体，而要构建环境（视频，2026-08-25） ｜ 📺 **Hamel Husain** — Don't Build Agents, Build Environments Instead (Video, 2026-08-25)

**来源｜Source**：https://www.youtube.com/watch?v=JolFqvXj3BE

**摘要｜TL;DR**
哈梅尔·侯赛因和亚当·阿扎姆认为，在多智能体系统中，沙箱环境基础设施才是真正的产品，并分享了实现快速、安全、可观测智能体环境的架构模式。 ｜ Hamel Husain and Adam Azzam argue that for multi-agent systems, the sandbox environment infrastructure is the real product, and they share architecture patterns for fast, secure, observable agent environments.

**要点｜Takeaways**
• 裸沙箱是不够的；智能体需要像 CI 系统那样设计环境，以实现快速冷启动和隔离。 ｜ A bare sandbox is not enough; agents need environments designed like CI systems for fast cold starts and isolation.
• 任务与会话有区别：后台智能体通常需要类似会话的持久环境，而不仅仅是无状态任务。 ｜ Jobs vs sessions distinction: background agents often need session-like persistent environments, not just stateless jobs.
• 智能体的密钥与代码执行是另一种威胁模型，需要专门的控制。 ｜ Agent secrets and code execution are a different threat model requiring dedicated controls.
• 控制平面与数据平面分离是扩展到多智能体的关键。 ｜ Control plane/data plane separation is key to scaling to many agents.
• 环境才是产品；在打磨智能体之前先投入环境。 ｜ The environment is the product; invest there before polishing the agent.

**启示｜Implication**
实践型哲学家应当关注，因为承载智能体的环境是 AI 操纵计算现实的底层介质，掌握这一介质是引导智能体而不仅仅是构建它们的前提。 ｜ Practitioner-philosophers should care because the environments that host agents are the substrate through which AI manipulates computational reality, and mastering that substrate is prerequisite to steering agents rather than merely building them.

**综合评分｜CompositeScore**
4.6

**主题｜Topics**
智能体 ｜ Agent
