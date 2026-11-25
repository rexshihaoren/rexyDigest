# Deep Note Template

Deep notes are final KnowledgeCard input files. They should be ready for human
review and KnowledgeCard rendering directly from `KnowledgeCard_Inbox/`.

## Contract

New Deep Notes use five required body sections and one optional section:

```markdown
# <中文判断句标题>

> 整理者：Rex Ren

──────────────────────────────

Source: <arXiv / YouTube / Blog / Podcast / RSS / ...>
Original Title: <source original title>
Author: <source author or Unknown>

---

### 00｜钩子与变化

- <A concrete scene from the source>
- <What changed>

---

### 01｜核心主张

- 主张：<One falsifiable claim>
- 边界：<Where it applies and what key terms mean>

---

### 02｜证据

- <Named source, observation and limits> [二手] [单源] [仅轶事]

---

### 03｜反方

- 最强反解释：<Best competing explanation and how to distinguish it>

---

### 04｜与我的地图的关系

- <Personal inference>
- <What follows from it>

---

### 05｜沉淀

- 可复用的视角：<A reusable question ending in ？ or an if-then rule>
- 待验证预测：<Observable outcome and future deadline or test condition>

---

### 参考文献

- <Original Title>, <Author>, <URL if available>
```

## Rules

- H1 must be a Chinese judgment sentence. Do not use the source title as H1.
- Metadata `Source`, `Original Title`, and `Author` are required.
- `Source` is human-readable, such as `arXiv` or `YouTube`; it is not a URL.
- `URL` is not allowed in metadata. Put the URL only in `### 参考文献`.
- `ItemID` is not emitted in Markdown. Internal item ids remain in generated
  filenames and `corpus/deep_picks/<end-date>.toml`.
- Use the headings in order and put required bullet content on the same line.
  Claim-specific scopes may be nested under the single `边界` bullet.
- Use one or two opening bullets. Omit section 04 when the personal connection
  lacks two substantive points. A short topic tag can go in an opening bullet.
- State the claim once. For independent assertions, use consecutive labels
  `主张1`, `主张2`, etc. Prefix each evidence bullet with the corresponding
  label (for example, `主张1：`). Cover every claim and give its scope in `边界`.
- Tag evidence with exactly one of `[一手]` or `[二手]` and one of `[单源]` or
  `[多源]`. Optionally add `[有数字]` or `[仅轶事]`. Name the source and note
  consequential gaps in sample size or replication. If support is missing,
  use `[未验证]` followed by the reason in place of evidence and tags.
- Make the prediction gradeable. Use YYYY-MM-DD for calendar deadlines and
  choose a date after generation. Otherwise give an explicit future test
  condition. Label personal inferences as such.
- During visual review, Rex may freely change headings, section order, bullets,
  and narrative structure when the note's content is better expressed another
  way. The generated template is guidance, not a constraint on reviewed notes.
- Do not use inline numeric citations such as `[1]` in the body.
- `### 参考文献` is required and uses bullet references, not numbered labels.
- Chinese is the main language. English should stay around 10% overall and be
  limited to necessary terms such as `agent`, `world model`, `benchmark`, or
  `challenge`.
- Extra references are allowed only when explicitly present in the source
  payload. Do not invent URLs, paper IDs, venues, authors, or dates.
- Ground factual claims in the item payload. If the payload is thin, say so.
- Do not emit fallback error text into the Markdown. LLM failures should fail
  the run.

## Normalization And Validation

Before a note is written to `KnowledgeCard_Inbox/`, `rexyDigest` applies only
deterministic cleanup:

- Trim prose before the first H1.
- Normalize `整理者：...` variants to `> 整理者：Rex Ren`.
- Insert the decorative separator after the author line when missing.
- Normalize delimiter variants to `---`.
- Normalize known aliases within their section, such as `适用范围` to `边界`
  in section 01 and `最强替代解释` to `最强反解释` in section 03.

After cleanup, validation fails hard if required structure or content is still
missing. Near-duplicate wording between claim and synthesis bullets logs a
warning. Whether a claim is compound or a prediction is genuinely falsifiable
requires editorial judgment. Existing seven-section notes remain valid for
review and publishing. Deadline freshness is checked at generation time so a
saved note can still be reviewed after its prediction comes due.

The pipeline does not use an LLM repair loop.
Review UI validation allows structural edits; it only rejects empty Markdown,
generator fallback text, and base64 image data URIs.
Saving returns after the Markdown is persisted. Any visual reevaluation runs in
the background, and publishing remains disabled until it finishes.
Transient visual-judge failures can be retried from the review UI. A successful
retry clears the persisted incomplete/error state.

Generation validation rejects:

- Non-Chinese H1 titles.
- Missing metadata or URL metadata.
- Missing or misordered sections, missing required bullet content, and
  evidence without provenance tags or an explicit unverified reason.
- Inline numeric citations in the body.
- Missing `### 参考文献`.
- Generator fallback text.
- Base64 image data URIs.

## Images

Images are optional and source-bound.

- Include an image only when the source payload already contains a real image
  URL or local asset path.
- Place the image immediately after the section it supports.
- Use KnowledgeCard visual placeholder syntax:

```markdown
(配图: https://source.example/image.png)
```

- Keep images rare: at most 1-2 per deep note.
- `rexyDigest` must not generate or convert images to base64 data URIs.
- If KnowledgeCard needs local copies or base64 assets, that belongs in the
  KnowledgeCard import/render stage, not in this digest pipeline.
