# AI×Simulation｜每周雷达
## 智能体×世界模型｜本周严选：论文·视频·博文

> 整理者：Rex Ren

覆盖范围 Coverage window：**2026年06月03日 至 2026年06月10日** ｜ 入选 Items: **5**

### 核心看点 Overview（双语）
- 🏅 SkillAxe: 通过评估引导的自我优化打磨LLM编写的智能体技能 ｜ SkillAxe: Sharpening LLM-Authored Agent Skills Through Evaluation-Guided Self-Refinement
- 🏅 ABC-Bench: 面向生物安全的智能体生物能力基准测试 ｜ ABC-Bench: An Agentic Bio-Capabilities Benchmark for Biosecurity
- 🏅 前沿编程智能体使用元编程适应不熟悉编程语言 ｜ Frontier Coding Agents Use Metaprogramming to Adapt to Unfamiliar Programming Languages

---


**标题｜Title**
📄 **Srishti Gautam, Arjun Radhakrishna, Sumit Gulwani** — SkillAxe: 通过评估引导的自我优化打磨LLM编写的智能体技能（论文，2026-06-09） ｜ 📄 **Srishti Gautam, Arjun Radhakrishna, Sumit Gulwani** — SkillAxe: Sharpening LLM-Authored Agent Skills Through Evaluation-Guided Self-Refinement (Paper, 2026-06-09)

**来源｜Source**：https://arxiv.org/abs/2606.10546

**摘要｜TL;DR**
SkillAxe使LLM能够迭代地优化自己的智能体技能文档，无需标签或奖励即可将成功率差距缩小至人类编写技能的67%。 ｜ SkillAxe enables LLMs to iteratively refine their own agent skill documents, closing up to 67% of the gap to human-authored skills without requiring labels or rewards.

**要点｜Takeaways**
• SkillAxe将技能质量分解为四个可解释维度：质量影响、触发精度、指令合规性与解决方案路径覆盖。 ｜ SkillAxe decomposes skill quality into four interpretable dimensions: quality impact, trigger precision, instruction compliance, and solution-path coverage.
• 仅利用执行轨迹即可生成结构化改进简报，无需真实标签或环境奖励。 ｜ It produces structured improvement briefs using only execution traces, without ground-truth labels or test suites.
• 在SkillsBench上，SkillAxe相较未优化的LLM技能相对提升了28%的通过率。 ｜ On SkillsBench, SkillAxe improves pass rates by 28% relative over unimproved LLM skills.
• 在SpreadsheetBench真实场景中，SkillAxe构建的技能库仅用22个技能就将通过率从16.0%提升至52.0%。 ｜ In the wild on SpreadsheetBench, a SkillAxe-built skill library raised pass rate from 16.0% to 52.0% using only 22 skills.
• 该方法可作为持续改进引擎，从过往智能体轨迹中学习。 ｜ The method functions as a continuous improvement engine that learns from past agent trajectories.

**启示｜Implication**
这表明自主智能体可以通过结构化自我反思来引导自身能力提升，是向自我改进AI系统迈进的一步。 ｜ This demonstrates that autonomous agents can bootstrap their own capabilities through structured self-reflection, marking a step toward self-improving AI systems.

**综合评分｜CompositeScore**
4.9

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Andrew Bo Liu, Samira Nedungadi, Bryce Cai, Alex Kleinman, Harmon Bhasin, Seth Donoughe** — ABC-Bench: 面向生物安全的智能体生物能力基准测试（论文，2026-06-09） ｜ 📄 **Andrew Bo Liu, Samira Nedungadi, Bryce Cai, Alex Kleinman, Harmon Bhasin, Seth Donoughe** — ABC-Bench: An Agentic Bio-Capabilities Benchmark for Biosecurity (Paper, 2026-06-09)

**来源｜Source**：https://arxiv.org/abs/2606.11150

**摘要｜TL;DR**
ABC-Bench评估了LLM智能体在生物安全任务中的表现，如机器人脚本编写、DNA设计和筛选逃避，结果显示它们超越了人类专家。 ｜ ABC-Bench evaluates LLM agents on biosecurity tasks like robot scripting, DNA design, and screening evasion, showing they outperform human experts.

**要点｜Takeaways**
• LLM智能体能够高度自动化完成湿实验室生物学任务。 ｜ LLM agents can automate wet-lab biology tasks with high proficiency.
• 智能体在基于知识的任务上表现出色，但在新颖推理上较弱。 ｜ Agents excel at knowledge-based tasks but struggle with novel reasoning.
• 该基准包含双重用途任务，凸显生物安全风险。 ｜ The benchmark includes dual-use tasks highlighting biosecurity concerns.
• 湿实验室验证确认智能体生成了功能性DNA组装脚本。 ｜ Wet-lab validation confirmed agents produced functional DNA assembly scripts.

**启示｜Implication**
实践者必须认识到，智能体AI现已具备操控生物现实的能力，亟需建立新的监督和协调框架。 ｜ Practitioners must consider that agentic AI is now capable of manipulating biological reality, demanding new frameworks for oversight and alignment.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Aman Sharma, Sushrut Thorat, Paras Chopra** — 前沿编程智能体使用元编程适应不熟悉编程语言（论文，2026-06-09） ｜ 📄 **Aman Sharma, Sushrut Thorat, Paras Chopra** — Frontier Coding Agents Use Metaprogramming to Adapt to Unfamiliar Programming Languages (Paper, 2026-06-09)

**来源｜Source**：https://arxiv.org/abs/2606.10933

**摘要｜TL;DR**
前沿编程智能体通过元编程（用Python生成目标代码）适应陌生编程语言，提炼的策略能提升较弱智能体；强智能体的性能随解释器调用次数和输出令牌数增加而提高。 ｜ Frontier coding agents adapt to unfamiliar programming languages by using metaprogramming (writing Python to generate target code), with distilled strategies improving weaker agents; performance scales with interpreter calls and output tokens for strong agents.

**要点｜Takeaways**
• 强编程智能体（例如 Claude Opus 4.6 和 GPT-5.4 xhigh）自发地使用元编程来解决深奥语言中的任务。 ｜ Strong coding agents like Claude Opus 4.6 and GPT-5.4 xhigh spontaneously use metaprogramming to solve tasks in esoteric languages.
• 禁止元编程会导致性能大幅下降，表明这是一项关键的适应策略。 ｜ Forbidding metaprogramming causes large performance drops, indicating it is a critical adaptation strategy.
• 从强智能体提炼的帮助代码可以显著提升较弱智能体（Sonnet 4.6、GPT-5.4 mini），而无需暴露已解决的基准测试答案。 ｜ Distilled helper code from strong agents can significantly boost weaker agents (Sonnet 4.6, GPT-5.4 mini) without exposing them to solved benchmarks.
• 更多的解释器调用和输出令牌能放大有效策略，但无法在弱智能体中凭空创造它们。 ｜ Extra interpreter calls and output tokens amplify useful strategies but do not create them from scratch in weak agents.
• 利用工具和反馈来构建陌生语言的工作模型的能力，凸显了通向更通用自主问题解决的路径。 ｜ The ability to build a working model of an unfamiliar language using tools and feedback highlights a path toward more general autonomous problem-solving.

**启示｜Implication**
这表明智能体可以通过构建元工具来学习‘新世界规则’（如同模拟），为创建能适应并操纵任意计算环境的系统提供了蓝图。 ｜ This shows that agents can learn the 'rules of a new world' (like a simulation) by building meta-tools, offering a blueprint for creating systems that adapt to and manipulate arbitrary computational environments.

**综合评分｜CompositeScore**
4.8

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Liya Zhu, Jingzhe Ding, Jian Zhang, Jianbo Xue, Shihao Liang, Ge Zhang, Xiang Gao, Qingshui Gu, Mailun Gao, Huimin Che, Yan Zhao, Peiheng Zhou, Haojun Wang, Chaobo Xian, Lili Le, Chi Wu, Yiwei Liu, Shengda Long, Jiale Yang, Fangzhi Xu, Sijin Wu, Haodong Duan, Yi Zhu, Chao He, Zhaojian Li, Minchao Wang, Huan Zhou, Jiani Hou, Chuqian Yu, Weiran Shi, Hongwan Gao, Jiamin Chen, Guanhong Chen, Tingqin Luo, Kaiyuan Zhang, Zhixin Yao, Qing Hua, Yuhao Jiang, Jin Chen, Pu Chen, Zhenyu Hu, Xingyu Li, Zhengxuan Jiang, Meng Cao, Tianfeng Long, Haozhe Wang, Mingzhang Wang, Yichen Zhang, Yiming Dai, Chenchen Zhang, Jiaying Wang, Zhiyong Wu, Shen Yan, Yujia Qin, Wenhao Huang, Zaiyuan Wang, Xiaolong Chang** — Workflow-GYM：面向专业领域真实计算机使用智能体任务的长程评测（论文，2026-06-09） ｜ 📄 **Liya Zhu, Jingzhe Ding, Jian Zhang, Jianbo Xue, Shihao Liang, Ge Zhang, Xiang Gao, Qingshui Gu, Mailun Gao, Huimin Che, Yan Zhao, Peiheng Zhou, Haojun Wang, Chaobo Xian, Lili Le, Chi Wu, Yiwei Liu, Shengda Long, Jiale Yang, Fangzhi Xu, Sijin Wu, Haodong Duan, Yi Zhu, Chao He, Zhaojian Li, Minchao Wang, Huan Zhou, Jiani Hou, Chuqian Yu, Weiran Shi, Hongwan Gao, Jiamin Chen, Guanhong Chen, Tingqin Luo, Kaiyuan Zhang, Zhixin Yao, Qing Hua, Yuhao Jiang, Jin Chen, Pu Chen, Zhenyu Hu, Xingyu Li, Zhengxuan Jiang, Meng Cao, Tianfeng Long, Haozhe Wang, Mingzhang Wang, Yichen Zhang, Yiming Dai, Chenchen Zhang, Jiaying Wang, Zhiyong Wu, Shen Yan, Yujia Qin, Wenhao Huang, Zaiyuan Wang, Xiaolong Chang** — Workflow-GYM: Towards Long-Horizon Evaluation of Computer-use Agentic tasks in Real-World Professional Fields (Paper, 2026-06-09)

**来源｜Source**：https://arxiv.org/abs/2606.11042

**摘要｜TL;DR**
Workflow-GYM 针对专业软件任务对长程 GUI 智能体进行评测，结果显示，即便是顶尖模型也因工作流一致性问题仅取得约30%的成功率。 ｜ Workflow-GYM benchmarks long-horizon GUI agents on professional software tasks, revealing that even top models achieve only ~30% success due to workflow consistency issues.

**要点｜Takeaways**
• 当前 GUI 智能体在长程专业工作流上的成功率仅略高于30%。 ｜ Current GUI agents achieve only slightly above 30% success on long-horizon professional workflows.
• 主要失败模式包括遗漏工作流阶段、错误传播、目标漂移以及对领域专用软件理解不足。 ｜ Key failure modes include workflow stage omission, error propagation, objective drift, and poor understanding of domain-specific software.
• 该评测基准覆盖多个专业领域和专用软件，超越了简单的短程应用。 ｜ The benchmark spans diverse professional domains and specialized software, moving beyond simple short-horizon apps.
• 结果凸显了智能体在长任务中需要保持上下文连贯性并避免级联错误的需求。 ｜ Results highlight the need for agents that maintain context coherence and avoid cascading errors over extended tasks.
• Workflow-GYM 为衡量现实经济场景下智能体部署的进展提供了严格的平台。 ｜ Workflow-GYM provides a rigorous platform to measure progress in real-world economic agent deployment.

**启示｜Implication**
对实践哲学家而言，这揭示了当前智能体架构与在复杂数字环境中维持连贯目标追求之间的巨大差距——这是构建能有效操纵专业领域“现实代码”的智能体的必要一步。 ｜ For practitioner-philosophers, this reveals the profound gap between current agent architectures and the demands of sustained, coherent goal pursuit in complex digital environments—a necessary step if we are to build agents that effectively manipulate the 'reality-code' of professional domains.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
---


**标题｜Title**
📄 **Tengchao Lv, Dongdong Zhang, Jiayu Ding, Yilin Jia, Yuzhong Zhao, Yupan Huang, Wenshan Wu, Xiangyang Zhou, Shaohan Huang, Nan Yang, Li Dong, Lei Cui, Furu Wei** — 注意差距：前沿大语言模型能通过标准化办公能力考试吗？（论文，2026-06-09） ｜ 📄 **Tengchao Lv, Dongdong Zhang, Jiayu Ding, Yilin Jia, Yuzhong Zhao, Yupan Huang, Wenshan Wu, Xiangyang Zhou, Shaohan Huang, Nan Yang, Li Dong, Lei Cui, Furu Wei** — Mind the Gap: Can Frontier LLMs Pass a Standardized Office Proficiency Exam? (Paper, 2026-06-09)

**来源｜Source**：https://arxiv.org/abs/2606.10956

**摘要｜TL;DR**
该论文引入基于中国NCRE办公任务的基准，发现即便最好的智能体系统也仅得68.8分，远低于人类参考的95.5分，暴露出文档自动化的巨大鸿沟。 ｜ This paper introduces a benchmark based on China's NCRE office tasks and finds that even the best agentic LLM system scores only 68.8%, far below the human reference of 95.5%, exposing large gaps in document automation.

**要点｜Takeaways**
• 7款前沿大语言模型在单轮模式下最高得分仅为36.6%。 ｜ 7 frontier LLMs score at most 36.6% in single-turn mode on standardized office tasks.
• 带执行反馈和迭代修复的智能体系统达到68.8%，但仍落后于人类表现。 ｜ An agentic system with execution feedback and iterative repair reaches 68.8%, but still lags behind human performance.
• 办公自动化需要长程规划、精确格式化和跨应用集成，当前AI在这些方面存在困难。 ｜ Office automation demands long-horizon planning, precise formatting, and cross-app integration, which current AI finds difficult.
• 结果表明，代码生成式大模型在专业级文档操作上尚不可靠。 ｜ The results indicate that code-generating LLMs are not yet reliable for professional-grade document manipulation.

**启示｜Implication**
正如掌握物理现实需要精度，掌握数字文档现实需要智能体在细粒度代码控制上的可靠性——该基准是对我们距离能够操纵计算世界结构的AI有多近的一次压力测试。 ｜ Just as mastering physical reality requires precision, mastering digital document reality requires an agent’s reliability at fine-grained code control—this benchmark serves as a stress test for how close we are to AI that can manipulate the fabric of our computational world.

**综合评分｜CompositeScore**
4.7

**主题｜Topics**
智能体 ｜ Agent
