CONFIG
TIME_WINDOW_PRIMARY = "last 7 days"
TIME_WINDOW_FALLBACK1 = "last 30 days"
TIME_WINDOW_FALLBACK2 = "last 90 days"
AGENT_KOLS = ["Andrej Karpathy (YouTube, blog)", "Yannic Kilcher (YouTube)", "Shane Legg (talks/interviews)", "Mixture of Experts (podcast)", "Luis Serrano (YouTube)", "Latent Space (YouTube/Podcast)"]
SIM_KOLS = ["Closer To Truth (YouTube)", "Rizwan Virk (interviews/podcast)", "David Chalmers (lectures/interviews)", "Latent Space (simulation episodes if any)"]
PAPER_SOURCES = ["arXiv", "NeurIPS", "ICLR", "ICML", "AAAI", "Science", "Nature", "Semantic Scholar", "Google Scholar"]
KEYWORDS_AGENT = ["agent","agentic","autonomous agent","LLM agent","toolformer","RAG","chain-of-thought","prompt engineering","multi-agent","agentic AI"]
KEYWORDS_SIM = ["simulation hypothesis","simulation argument","ancestor simulation","are we living in a simulation","simulation evidence","reality+","simulation theory"]
MAX_PAPERS = 5
MAX_ITEMS = 20

TASK (explicit steps)
1. Search each AGENT_KOLS and SIM_KOLS for new public items (video, podcast episode, blog, talk, preprint) within TIME_WINDOW_PRIMARY. If none found, expand to FALLBACK1, then FALLBACK2.
2. For each candidate, require at least one matching keyword in title/description/transcript OR explicit focus on agentic systems or simulation hypothesis. Discard otherwise.
3. For papers: search PAPER_SOURCES with KEYWORDS_AGENT ∪ KEYWORDS_SIM. Select up to MAX_PAPERS prioritized by: (a) recency ≤12 months & relevance, (b) citations/attention, (c) direct applicability to agent design or simulation theory. Include one classic paper if highly relevant.(d) author's credibility
4. For each retained item compute:
   - Relevance (0–10): topical closeness to agentic-AI or simulation.
   - Novelty (0–10): new insights or methods.
   - Actionability (0–10): direct implication for agentic AI or simulation experiments.
   - CompositeScore = 0.4*Relevance + 0.3*Novelty + 0.3*Actionability.
5. Sort items by CompositeScore desc, limit to MAX_ITEMS.

FILTER RULES
- Exclude pieces only talks about AI safety.
- Prefer items with transcripts/slides; include transcript link if available.
- For simulation KOLs only include channels/podcasts where ≥10% historical content discusses simulation; otherwise exclude.

OUTPUT (produce all three sections in one response)

A) WEEKLY BRIEF (compact)
- Header: Coverage window, Items found, Papers included.
- For each item (top MAX_ITEMS):
  - Source / KOL — Title (Type) — Date — Link
  - TL;DR (≤20 words)
  - 3 key takeaways (each ≤12 words)
  - Implication for Rex Ren (Agent infra / Simulation research) — 1 line ≤20 words
  - CompositeScore (X.X) and Tags: Agent/Simulation/Paper/Podcast

B)
Produce a markdown table with columns:
KOL | Title | Date | Type | Link | ShortSummary(30–50 words) | Relevance | Novelty | Actionability | CompositeScore | Tags | SuggestedAction | TranscriptOrPaperLink

RANKING GUIDELINES
- CompositeScore ≥ 8 → Must-Read
- 6–7 → Worth Watching/Skimming
- <6 → Archive unless classic paper

FAILURE MODE
- If ZERO items found within TIME_WINDOW_FALLBACK2, return:
  - "NO_NEW_CONTENT" and a list of the last 3 relevant items (title+link+date) from the past 365 days for each KOL.

FORMAT & LANGUAGE
- Reply primarily in English.
- Keep the WEEKLY BRIEF section concise (aim ≤900 words).

EXECUTION NOTES
- Include direct links to videos/podcast episodes/papers.
- Prioritize sources that have public URLs.
- Do not invent links or dates. If unsure, mark item as “VERIFY_NEEDED” and include the search query used.