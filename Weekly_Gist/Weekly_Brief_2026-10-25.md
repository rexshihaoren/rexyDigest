# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年10月18日 至 2026年10月25日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 Claude Mods：由内而外翻转智能体 Harness ｜ Claude Mods: Flipping the Harness Inside Out
- 🏅 RIDAR：通过自动检测与运行时干预保障自主研究智能体的研究诚信 ｜ RIDAR: Safeguarding Research Integrity in Autonomous Research Agents via Automated Detection and Runtime Intervention
- 🏅 AfterDeleteBench：审计LLM智能体删除后信息持久性 ｜ AfterDeleteBench: Auditing Post-Deletion Information Persistence in LLM Agents

---


**标题｜Title**
📝 **Dan McAteer** — Claude Mods：由内而外翻转智能体 Harness（博客，2026-10-21） ｜ 📝 **Dan McAteer** — Claude Mods: Flipping the Harness Inside Out (Blog, 2026-10-21)

**来源｜Source**：https://latent.space/p/claude-mods/

**摘要｜TL;DR**
Claude Mods 将 Claude Code 的智能体 Harness 变成可编程的“注意力界面”，让用户控制自主智能体何时打断、展示什么信息以及需要哪些决策。 ｜ Claude Mods turn Claude Code's agent harness into a programmable 'Attention Interface' that lets users control how and when the autonomous agent interrupts, shows information, and requests decisions.

**要点｜Takeaways**
• Claude Mods 是智能体 Harness 的中间件，通过事件钩子自定义行为和渲染。 ｜ Claude Mods are middleware for the agent harness, customizing behavior and rendering via event hooks.
• Harness 正从面向机器转向面向人类，成为管理人类注意力的注意力界面。 ｜ The harness is reversing from machine-facing to human-facing, becoming an Attention Interface that manages human focus.
• 内置 mods（如 You Should Know）演示了侧智能体如何揭示隐藏的高影响信息。 ｜ Built-in mods like You Should Know demonstrate how side agents can surface hidden high-impact information.
• ModSmith 提供开源 mods/模板，Claude 可以根据自然语言请求生成 mods。 ｜ ModSmith provides open-source mods/templates, and Claude can generate mods from plain-language requests.
• 与 ChatGPT Intelligent UI 和 Cursor PR Routing 的对比显示了人类注意力管理的新兴行业模式。 ｜ Comparisons to ChatGPT Intelligent UI and Cursor PR Routing show an emerging industry pattern of human-attention management.

**启示｜Implication**
对实践者-哲学家而言，这表明智能体控制面正在变得可由人类和模型共同编程，将 Harness 重塑为人类判断与自主执行协商注意力的场所。 ｜ For practitioner-philosophers, this signals that the control surface for agent steering is becoming programmable by both human and model, reframing the harness as the site where human judgment and autonomous execution negotiate attention.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Jiening Siow, Amy Xin, Junjie Wang, Ziyu Tang, Zijun Yao, Yunjia Qi, Fanjin Zhang, Lei Hou, Jie Tang, Juanzi Li** — RIDAR：通过自动检测与运行时干预保障自主研究智能体的研究诚信（论文，2026-10-22） ｜ 📄 **Jiening Siow, Amy Xin, Junjie Wang, Ziyu Tang, Zijun Yao, Yunjia Qi, Fanjin Zhang, Lei Hou, Jie Tang, Juanzi Li** — RIDAR: Safeguarding Research Integrity in Autonomous Research Agents via Automated Detection and Runtime Intervention (Paper, 2026-10-22)

**来源｜Source**：https://arxiv.org/abs/2610.31372

**摘要｜TL;DR**
RIDAR 引入了一套分类法和框架，用于检测和纠正自主研究智能体轨迹中的 14 类研究诚信违规行为，在基准上达到 85.2% 的 F1，并在运行时将剩余违规减少 36.8%。 ｜ RIDAR introduces a taxonomy and frameworks for detecting and correcting 14 types of research integrity violations in autonomous research agent trajectories, achieving 85.2% F1 on a benchmark and reducing remaining violations by 36.8% at runtime.

**要点｜Takeaways**
• 定义了 RIVT，一个覆盖研究全生命周期的 14 类研究诚信违规分类法。 ｜ Defines RIVT, a taxonomy of 14 research integrity violation types across the research lifecycle.
• RIDAR-post-hoc 在 RIV-Gold 上以 85.2% 的 F1 检测轨迹中的违规，并在 300 条真实轨迹中发现 99.7% 存在共 3,964 次违规。 ｜ RIDAR-post-hoc detects violations in agent trajectories with 85.2% F1 on RIV-Gold and finds 3,964 violations in 99.7% of 300 wild trajectories.
• RIDAR-runtime 动态干预，使任务完成时剩余的违规减少 36.8%。 ｜ RIDAR-runtime dynamically intervenes, reducing remaining violations at task completion by 36.8%.
• 将发布代码和数据以支持后续的智能体诚信研究。 ｜ Code and data will be released to support further research on agent integrity.

**启示｜Implication**
对于部署自主研究智能体的从业者而言，RIDAR 提供了具体的工具来监控和纠正诚信违规，将抽象的可靠性担忧转化为可衡量、可操作的安全保障。 ｜ For practitioners deploying autonomous research agents, RIDAR provides concrete tools to monitor and correct integrity violations, turning abstract reliability concerns into measurable, actionable safeguards.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Ehsan Saleh, Roozbeh Nahavandi, Sama Salarian, Raef Bassily, Andrew Perrault** — AfterDeleteBench：审计LLM智能体删除后信息持久性（论文，2026-10-22） ｜ 📄 **Ehsan Saleh, Roozbeh Nahavandi, Sama Salarian, Raef Bassily, Andrew Perrault** — AfterDeleteBench: Auditing Post-Deletion Information Persistence in LLM Agents (Paper, 2026-10-22)

**来源｜Source**：https://arxiv.org/abs/2610.31366

**摘要｜TL;DR**
AfterDeleteBench 表明，从 LLM 智能体中删除原始记忆记录往往无法移除由派生状态携带的信息，除非应用溯源感知的闭包，否则恢复率很高。 ｜ AfterDeleteBench shows that deleting original memory records from LLM agents often fails to remove information carried by derived state, with high recovery rates unless provenance-aware closure is applied.

**要点｜Takeaways**
• 删除后恢复很常见：对 Qwen2.5-7B-Instruct 单次查询即可在约三分之二的情况下恢复已删除的秘密，而从未接触过的对照组恢复率为零。 ｜ Post-deletion recovery is common: a single query recovers the deleted secret in about two thirds of cases for Qwen2.5-7B-Instruct, while never-exposed controls have zero recovery.
• 在公开组合规则下，从分别存储的组件精确重建秘密在 Qwen、Mistral 和 Phi-3 上的成功率为 62–99%，即使没有逐字副本。 ｜ Exact reconstruction from separately stored components under a public composition rule succeeds in 62-99% of cases across Qwen, Mistral, and Phi-3, even without a verbatim copy.
• 响应界面与解析器不匹配会导致携带目标的回复被判定为失败；测量必须考虑格式。 ｜ Response interface and parser mismatch can cause target-bearing replies to be scored as failures; measurement must account for format.
• 溯源感知的闭包消除了观察到的恢复，但精确字面写入过滤器只阻止重新插入，无法删除已存在的信息。 ｜ Provenance-aware closure eliminates observed recovery, but exact-literal write filters only block reinsertion, not already-present information.
• 删除应在智能体及其记忆系统层面进行行为评估，而不仅仅是存储操作。 ｜ Deletion should be evaluated behaviorally at the agent and memory-system level, not just as a storage operation.

**启示｜Implication**
为 AI 智能体构建长期记忆的从业者必须将删除视为系统级行为属性，而不是简单的存储删除，否则可能泄露本应删除的信息。 ｜ Practitioners building long-term memory for AI agents must treat deletion as a system-level behavioral property, not a simple storage delete, or risk leaking supposedly removed information.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Qijin Zhang, Hanzhen Wang, Yuehan Zhao, Haoyu Dai, Yao Shu, Zhongxiang Dai, Shuang Qiu** — EpiSEM-Bench：评估缺失证据下 LLM 智能体的安全性与证据恢复（论文，2026-10-22） ｜ 📄 **Qijin Zhang, Hanzhen Wang, Yuehan Zhao, Haoyu Dai, Yao Shu, Zhongxiang Dai, Shuang Qiu** — EpiSEM-Bench: Evaluating Safety and Evidence Recovery in LLM Agents under Missing Evidence (Paper, 2026-10-22)

**来源｜Source**：https://arxiv.org/abs/2610.31650

**摘要｜TL;DR**
EpiSEM-Bench 是一个包含 300 对匹配任务的可执行基准，用于评估 LLM 智能体在工具响应缺失安全关键证据时是否能安全处理，以及是否会在行动前主动恢复该证据。 ｜ EpiSEM-Bench is an executable benchmark with 300 matched task pairs that evaluates whether LLM agents safely handle missing safety-relevant evidence in tool responses, and whether they actively recover that evidence before acting.

**要点｜Takeaways**
• 在十个 LLM 智能体中，基准揭示了它们在遗漏鲁棒性、证据获取和适当行动方面的显著差异。 ｜ The benchmark reveals substantial variation among ten LLM agents in omission robustness, evidence acquisition, and appropriate action.
• 对缺失证据的抵抗并不必然转化为有用的恢复；智能体在是否主动获取并使用缺失事实上表现不同。 ｜ Resistance to missing evidence does not necessarily translate into useful recovery; agents differ in whether they obtain and use missing facts.
• 恢复访问降低了所有十个模型的不安全执行，但主动寻求证据的行为因模型而异。 ｜ Recovery access reduces unsafe execution for all tested models, but active evidence-seeking behavior varies.
• 独立的审计工具测试智能体是否会寻求缺失事实，并在完成允许任务的同时避免被禁止的行动。 ｜ An independent audit tool tests whether agents withhold prohibited actions while completing permissible tasks.

**启示｜Implication**
对实践哲学家而言，这篇论文表明智能体安全不仅取决于遵循返回的事实，还取决于智能体查询缺失现实状态变量的能力，这强化了 AI 作为现实代码操纵者时对认识卫生的要求。 ｜ For a practitioner-philosopher, the paper shows that agent safety is not just about following returned facts but about the agent's ability to query missing reality-state variables, reinforcing the need for epistemic hygiene in AI as reality-code manipulators.

**综合评分｜CompositeScore**
4.6

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Aman Behera, Payal Payal** — 事后审计幻象：离线智能体验证的可识别性极限（论文，2026-10-22） ｜ 📄 **Aman Behera, Payal Payal** — Post-Audit Mirage: Identifiability Limits of Offline Agent Verification (Paper, 2026-10-22)

**来源｜Source**：https://arxiv.org/abs/2610.31130

**摘要｜TL;DR**
离线验证无法区分安全与有害的部署结果，当验证者可见证据相同时，需要在部署时监控才能解决可识别性差距。 ｜ Offline verification of agent updates cannot distinguish safe from harmful deployment outcomes when verifier-visible evidence is matched, requiring deployment-time monitoring to resolve the identifiability gap.

**要点｜Takeaways**
• 仅靠离线测试可能在结构上对部署后安全差异视而不见，因为安全与有害生命周期可产生完全相同的验证者可见证据。 ｜ Offline tests alone can be structurally blind to post-deployment safety differences because safe and harmful lifecycles can produce identical verifier-visible evidence.
• 论文将此形式化为观测等价定理，并给出错误-弃权权衡。 ｜ The paper formalizes this as an observational-equivalence theorem with an error-abstention tradeoff.
• IdentifiedRangeMonitor 利用新鲜的群体标记伤害结果输出部署、暂停、无法判定或不支持。 ｜ IdentifiedRangeMonitor uses fresh group-labelled harm outcomes to output deploy, hold, cannot determine, or unsupported.
• 监控仅在有利条件下能恢复缺失的区分；稀有群体、小效应或缺失观测可能导致无法判定。 ｜ Monitoring recovers the missing distinction only in favorable settings; rare groups, small effects, or missing observations may leave decisions undecided.
• 实践者应同时评估验证器计算的有效性以及现有证据是否真正支持部署决策。 ｜ Practitioners should evaluate both the verifier's calculation validity and whether the available evidence actually supports deployment.

**启示｜Implication**
实践者-哲学家应关注此论文，因为它表明离线审计可知性的边界本身就是一个形式化极限，迫使智能体治理转向运行时监控与认识论上的谦逊。 ｜ A practitioner-philosopher should care because this paper demonstrates that the boundary of what can be known from offline audits is itself a formal limit, forcing a shift toward runtime monitoring and epistemic humility in agent governance.

**综合评分｜CompositeScore**
4.5

**主题｜Topics**
智能体 ｜ Agent
