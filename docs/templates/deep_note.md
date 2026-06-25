# Deep Note Template

Deep notes are final KnowledgeCard input files. They should be ready for human
review and KnowledgeCard rendering directly from `KnowledgeCard_Inbox/`.

## Contract

Each generated deep note must use the Rex-native 7-section KnowledgeCard
Markdown structure:

```markdown
# <中文判断句标题>

> 整理者：Rex Ren

──────────────────────────────

Source: <arXiv / YouTube / Blog / Podcast / RSS / ...>
Original Title: <source original title>
Author: <source author or Unknown>

---

### 00｜为什么在意这篇

- 直觉：
- 它戳中的变化：
- 持续观察的方向：

---

### 01｜尝试回答的问题

- 长期问题：
- 急迫性：
- 切入点：

---

### 02｜创新点

- 关键论点：
- 为什么成立：
- 我的视角：<only if this is the one body section with a personal view>

---

### 03｜与 AI X Simulation 的关系

- 连接点：
- 重要性：
- 还差一步：
- 我的视角：<only if this is the one body section with a personal view>

---

### 04｜关键论据

- 支撑材料：
- 最可信的点：
- 可被challenge：

---

### 05｜习惯性反思

- 还没说清：
- 不能推出：
- 容易误读：

---

### 06｜沉淀一下

- 一个判断：
- 可复用的视角：
- 继续追的问题：

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
- The 7 numbered sections are fixed and must keep their exact headings.
- The bullet labels inside each section are fixed.
- Required bullets may either carry content on the same line or introduce
  indented nested bullets immediately below the label.
- `### 00｜为什么在意这篇` is the personal opening layer. The LLM may draft
  it, and Rex edits the generated Markdown afterward in an editor when needed.
- Body sections contain exactly one `我的视角：` bullet. It must appear in
  either `02｜创新点` or `03｜与 AI X Simulation 的关系`, not both.
- `05｜习惯性反思` is mandatory. It handles boundaries, likely misreadings, and
  what the source does not prove.
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
- Normalize known section-aware bullet label aliases when the intended strict
  label is unambiguous, for example `为什么这个判断成立` -> `为什么成立`
  only inside `### 02｜创新点`, `为什么重要` -> `重要性` only inside
  `### 03｜与 AI X Simulation 的关系`, and `证据材料` -> `支撑材料`
  only inside `### 04｜关键论据`.

After cleanup, validation fails hard if required structure or content is still
missing. The pipeline does not use an LLM repair loop.

Validation rejects:

- Non-Chinese H1 titles.
- Missing metadata or URL metadata.
- Missing fixed sections or fixed bullet labels.
- Missing or duplicate `我的视角：`.
- `我的视角：` outside section 02 or 03.
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
