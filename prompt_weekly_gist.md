GOAL
Find the highest-value new items on agentic AI and the simulation hypothesis. Score, rank, and summarize for Rex Ren.

CONFIG
TIME_WINDOWS = ["last 7 days","last 30 days","last 90 days"]
AGENT_KOLS = [
  "Andrej Karpathy (YouTube, blog)","Yannic Kilcher (YouTube)","Shane Legg (talks/interviews)",
  "Mixture of Experts (podcast)","Luis Serrano (YouTube)","Latent Space (YouTube/Podcast)",
  "Lilian Weng (blog)","Harrison Chase (LangChain/LangGraph)","Jerry Liu (LlamaIndex)",
  "Simon Willison (blog)","Jim Fan (NVIDIA)","Pieter Abbeel (Berkeley/robotics)",
  "Hamel Husain (blog)","Oriol Vinyals (DeepMind)"
]
SIM_KOLS = [
  "Closer To Truth (YouTube)","Rizwan Virk (interviews/podcast)","David Chalmers (lectures/interviews)",
  "Latent Space (simulation episodes if any)","Nick Bostrom (Oxford/Simulation Argument)","Scott Aaronson (blog)",
  "Max Tegmark (MIT)","Sean Carroll (podcast/blog)","Sabine Hossenfelder (YouTube)",
  "Stephen Wolfram (Wolfram/Blog)","Anil Seth (neuroscience)"
]
PAPER_SOURCES = ["arXiv","NeurIPS","ICLR","ICML","AAAI","Science","Nature","Semantic Scholar","Google Scholar"]
KEYWORDS_AGENT = ["agent","agentic","autonomous agent","LLM agent","toolformer","RAG","chain-of-thought","prompt engineering","multi-agent","agentic AI"]
KEYWORDS_SIM = ["simulation hypothesis","simulation argument","ancestor simulation","are we living in a simulation","simulation evidence","reality+","simulation theory"]
KEYWORDS_ALL = KEYWORDS_AGENT + KEYWORDS_SIM
MAX_PAPERS = 5
MAX_ITEMS = 20

TASKS
1) Windowed search: iterate TIME_WINDOWS; for each window, query all AGENT_KOLS and SIM_KOLS for public items (video, podcast, blog, talk, preprint) published in-window. Stop at the first window with ≥1 hit; set COVERAGE_WINDOW.
2) Filter: keep a candidate only if title/description/transcript matches ≥1 term in KEYWORDS_ALL OR it explicitly focuses on agentic systems or the simulation hypothesis.
3) Papers: query PAPER_SOURCES with KEYWORDS_ALL. Select up to MAX_PAPERS prioritized by: (a) recency ≤12 months + relevance, (b) citations/attention, (c) direct applicability, (d) author credibility. Optionally include one classic if highly relevant.
4) Score each item:
   - Relevance (0–10): closeness to agentic AI or simulation under this lens:
     "Reality = computable simulation; AI+markets = reality-code manipulators."
     Prefer: digital physics; predictive AI & attention as capital; market feedback loops; neurophysics/consciousness; techno-time/control.
   - Novelty (0–10) • Actionability (0–10)
   - CompositeScore = 0.4*Relevance + 0.3*Novelty + 0.3*Actionability (1 decimal)
5) Rank by CompositeScore desc, then date desc. Deduplicate cross-posts. Limit to MAX_ITEMS.

FILTER RULES
- Exclude AI-safety-only pieces.
- Prefer items with transcripts/slides. **Only include a Link if it is a URL you would paste after verifying it resolves** (your retrieval/search step returned it). If you do not have a verified URL, **do not fabricate one**.
- Simulation KOLs: include only channels/podcasts where ≥10% historical content covers simulation.
- Never invent links or dates. If uncertain, mark VERIFY_NEEDED and include the exact query used.

LINK INTEGRITY (hard rules — overrides “fill in Link” habits)
- **Forbidden:** `example.com`, `example.org`, `localhost`, made-up paths on real domains, “plausible” YouTube/arXiv/blog URLs you did not verify, or URLs built by slugifying the title + date.
- **Allowed:** A link field may be exactly `VERIFY_NEEDED` plus **one** concrete web search query (in quotes) that a human can run, e.g. `VERIFY_NEEDED: "Max Tegmark digital physics podcast May 2026"`.
- **arXiv / DOI / YouTube:** Only include if the identifier matches a real resolved source from retrieval. If you are synthesizing from general knowledge without a live fetch, use VERIFY_NEEDED instead of guessing `arxiv.org/abs/...`.
- **Section C “资源 / Resources”:** Same rules — raw URL only if verified; otherwise `VERIFY_NEEDED` + search query only (no fake URL).

OUTPUT
A) WEEKLY BRIEF (≤900 words)
   Header: COVERAGE_WINDOW | Items found N | Papers M
   For each item (up to MAX_ITEMS):
   • Source/KOL — Title (Type) — Date — Link
   • TL;DR ≤20 words
   • 3 takeaways, each ≤12 words
   • Implication for Rex Ren (Agent infra / Simulation research) ≤20 words
   • CompositeScore (X.X) and Topics: Agent/Simulation

B) TABLE (Markdown)
   Columns (order exact):
   KOL | Title | Date | Topics | Type | Link | ReadPriority | ShortSummary (30–50 words) | CompositeScore | Relevance | Novelty | Actionability
   Rules:
   - Topics only ∈ {Agent, Simulation} (can be both).
   - ReadPriority:
     • CompositeScore ≥ 8.0 → Must-Read
     • 6.0–7.9 → Worth Skimming
     • <6.0 → Archive unless classic

C) PER-ITEM BLOG NOTES (PE-style; Must-Read or Worth Skimming)
   Purpose: For each eligible item, output one compact bilingual note (CN/EN) using format X. Raw material for later conversion. Length per item: 600–1200 words across CN+EN.

   Selection: all eligible items, ordered by CompositeScore desc then date; cap at min(MAX_ITEMS, 10).

   FORMAT X (apply to EACH item)
   ROLE
   Produce one compact bilingual (CN/EN) Markdown note. Output only the doc.

   INPUTS
   - TOPIC: <Source/KOL — Title>                 # no type/date here
   - URLS: [<primary link>, <secondary link?>]
   - SECTIONS: 3–8 (default 5; pick using Guardrails)
   - SUBTITLES_CN / SUBTITLES_EN: [auto-generate if missing]
   - EMOJIS: [optional]

   STYLE
   - H1: “<TOPIC> 极简笔记”
   - Blockquote (2 lines): brief CN context; “整理者：Rex Ren”
   - Thin rule: long box-drawing line
   - “资源 / Resources”: raw URLs only, followed by:
       Type: <Paper|Podcast|Video|Blog|Talk>  
       Date: <YYYY-MM-DD>
   - “核心内容”: 3–4 bullets using Unicode `•`
   - For each section i=1..SECTIONS:
     - H2: `## <emoji?> Section i｜<CN subtitle i> / <EN subtitle i>`
     - **中文** then 3–4 `-` bullets, one line each  
       • If a bullet has concrete examples in the source, add a nested “例:” list (1–3 items). Translate if needed.  
         `  - 例: <示例1>`  
         `  - 例: <示例2>`  
     - **English** then 3–4 mirrored bullets  
       • If the CN bullet had examples, add a nested “Examples:” list (1–3 items) under the matching EN bullet.  
         `  - Examples: <example 1>`  
         `  - <example 2>`  
     - Visuals (when available): insert 1–2 relevant charts/tables/photos from the source in the most relevant section(s).  
       • Embed via Markdown `![alt ≤12 chars](<direct_image_url>)` then a caption ≤15 words.  
       • For source tables, reproduce a small Markdown table (≤8 rows).  
       • Only use visuals clearly from the source; if none, skip.
     - Separate sections with `---`
   - Symbols: use full-width `｜`; allow `→` for flows
   - Emphasis: only **中文**/**English** labels
   - Code fences: only if helpful; CN then EN versions; each ≤3 lines
   - Layout: two trailing spaces for hard wraps; single-line bullets
   - No emojis inside bullets

   OUTPUT TEMPLATE
   # <TOPIC> 极简笔记  
   > <一句话中文背景>  
   > 整理者：Rex Ren  

   ──────────────────────────────

   📍 资源 / Resources  
   <URL_1>  
   <URL_2?>  
   Type: <type>  
   Date: <YYYY-MM-DD>  

   📚 核心内容  
   • <CN 模块1>  
   • <CN 模块2>  
   • <CN 模块3>  

   ## <EMOJI_1?> Section 1｜<CN 小标题1> / <EN Subtitle 1>
   **中文**  
   - <要点1>  
     - 例: <示例1>  
     - 例: <示例2>  
   - <要点2>  
   - <要点3>  

   **English**  
   - <Point 1>  
     - Examples: <example 1>  
     - <example 2>  
   - <Point 2>  
   - <Point 3>  

   ![<alt>](<direct_image_url_if_any>)  
   <short caption if visual included>  

   ---
   ## <EMOJI_2?> Section 2｜<CN 小标题2> / <EN Subtitle 2>
   **中文**  
   - <…>  
     - 例: <…>  
   **English**  
   - <…>  
     - Examples: <…>  

   <!-- Add Sections 3–8 similarly; include at most 2 visuals total -->

TOKEN GUARDRAILS
- If eligible items ≥ 7 → SECTIONS = 3–4 (use 3 if many)
- If eligible items 3–6 → SECTIONS = 5
- If eligible items ≤ 2 and source depth is high → SECTIONS = 6–8
- Limit bullets per language to 3 when SECTIONS > 5
- Omit EMOJIS to reduce tokens if needed.
- Avoid code fences unless essential.
- Examples: max 1–3 per bullet; concise; only from the source.
- For visuals, prefer small assets; avoid multi-MB images.

FAILURE MODE
If no items across TIME_WINDOWS:
- Return "NO_NEW_CONTENT".
- For each KOL, list last 3 relevant items from past 365 days (Title | Link | Date).

FORMAT
- English for sections A/B; Section C bilingual per item.
- ISO dates. Topics = Agent and/or Simulation only.

EXECUTION NOTES (token-thrifty)
- Stop at first window with hits; skip later windows.
- Cache and reuse channel/feed URLs.
- Fetch metadata first; avoid full transcripts unless needed for KEYWORDS_ALL.
- Enforce word caps; reuse summaries for cross-posts.
- Avoid downloading PDFs when abstract suffices.