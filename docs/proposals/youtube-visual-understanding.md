# YouTube Visual Understanding: Research And Proposed Architecture

Status: proposed; implementation intentionally not started.

## Decision summary

Build visual enrichment as a rexyDigest-owned extension of the existing
DeepNote workflow. Use `yt-dlp` as the acquisition boundary, PySceneDetect
plus fixed-interval fallback for candidate generation, local perceptual hashes
and OCR-derived signals for cheap filtering, and the existing Gemini boundary
for the final image-aware relevance judgment. Store candidates and approvals in
versioned sidecars. Render only explicitly approved local assets into final
DeepNote Markdown.

Do not import a publishing application, add a separate review application, or
change KnowledgeCard. Borrow small licensed algorithms only when they are
clearer than a native implementation; otherwise borrow concepts and tests.

## Current repository behavior

- The YouTube Source Adapter reads public Atom metadata, then uses
  `youtube-transcript-api`. It flattens transcript snippets into un-timestamped
  text. Transcript failure falls back to description or metadata-only Item.
- The only user-facing DeepNote workflow is `rexy deep-notes pick`. It asks Rex
  to select at most two eligible Items, writes `corpus/deep_picks/<date>.toml`,
  calls one DeepNote writer, validates the seven-section document, then writes
  directly to `KnowledgeCard_Inbox/`.
- DeepNote review is Item-level selection before generation. There is no
  section-level approval state, candidate sidecar, frame extraction, or visual
  review.
- The documented image syntax is currently `(配图: <URL-or-local-path>)`, at
  most one or two source-bound images. The requested final contract uses
  ordinary Markdown image syntax. This is a deliberate rexyDigest schema
  change and needs validator/template tests; KnowledgeCard must only receive
  the final ordinary Markdown.
- Corpus truth is structured data, while Markdown is a rendered artifact.
  Items are immutable and run-derived data belongs outside Item records. Visual
  evidence and approval therefore belong in versioned sidecars, not
  `items.jsonl` and not provider-specific Markdown.
- Baseline on 2026-07-11: `PYTHONPATH=python .venv/bin/pytest python/tests/`
  collected 143 tests; all 143 passed in 5.41 seconds. One warning came from
  `google.genai.types` using a Python API deprecated for removal in 3.17.

## Public repository comparison

Maintenance is assessed from visible activity/releases as of 2026-07-11. “No
license found” means code must not be copied without later verification.

| Repository | License / maturity | Acquisition and transcript | Visual pipeline | Long educational video / cost | Recommendation |
|---|---|---|---|---|---|
| [steipete/summarize](https://github.com/steipete/summarize) | MIT; active releases, broad tests and real users | `yt-dlp`, captions and transcription fallbacks; timed transcript segments | FFmpeg scene scoring, sparse fixed-interval fallback, screenshots, optional Tesseract OCR, transcript-aligned slide cards | Strong reference; local extraction is cheap, optional model/OCR cost; already handles sparse slides and long transcripts | Strongest behavioral reference. Borrow focused extraction/OCR/alignment concepts and small MIT code only if advantageous; do not import its CLI/extension/publisher architecture. |
| [specstoryai/keyframe-blogger](https://github.com/specstoryai/keyframe-blogger) | MIT; 19 commits, 13 stars, no releases; prototype | Requires local MP4 plus matching SRT | Captures at complete transcript thoughts with minimum interval; generates visual transcript; Gemini selects referenced frames | Claims hour-long videos for low cost, but sends many frames and lacks robust scene/OCR/dedup stages | Borrow visual-transcript structure and “copy only selected frames” concept. Do not adopt pipeline wholesale. |
| [bradautomates/claude-video](https://github.com/bradautomates/claude-video) | MIT; young but popular; 11 commits and active PRs | `yt-dlp` captions first, Groq/OpenAI Whisper fallback | Keyframe/scene/uniform modes; focused time windows; 16x16 grayscale frame-delta dedup; timestamps | Useful measured budgets, but >10-minute capped scans become sparse and every frame sent to a model costs tokens | Borrow focused-window and post-dedup budgeting concepts. Its sequential brightness dedup is a useful fallback, not sufficient for cross-section equivalence. |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | BSD-3-Clause; mature library since 2014, documented API/benchmarks | None | Robust content/adaptive/threshold scene detection; no OCR, transcript alignment, or dedup | Local CPU; appropriate candidate generator for long files when windows bound work | Reuse as dependency, behind a small adapter. Best mature scene boundary component. |
| [1ureka/video-keyframe-extract](https://github.com/1ureka/video-keyframe-extract) | No visible license; 11 commits; small experimental repo | Local videos only | PySceneDetect hard cuts + CLIP semantic-difference sampling + max-interval fallback + cap | Designed for short-form/high-throughput; GPU recommended; CPU slower | Concepts only. Its scene + embedding-change + coverage fallback combination validates proposed design, but license and long-video focus rule out code reuse. |
| [thatsrajan/vidlens-mcp](https://github.com/thatsrajan/vidlens-mcp) | MIT; active, 77 commits, 2 tags; early product | YouTube/local/social via `yt-dlp`; timestamped transcripts and persistent local store | Keyframes, Apple Vision OCR/feature prints, Gemini descriptions/embeddings, visual search returning paths/timestamps/reasons | Local persistence reduces repeat work; best features are macOS-specific or API-backed | Borrow evidence contract and persistent-cache concepts. Do not add MCP/SQLite or Apple-only core behavior; optional platform acceleration could come later. |
| [danielmiessler/Fabric](https://github.com/danielmiessler/Fabric) | MIT; very mature/popular, thousands of commits | `yt-dlp`-based YouTube transcript/metadata/comments; timestamp support | Recent visual OCR cues exist, but core value is prompt-pattern processing, not frame selection | Good transcript acquisition precedent; processing depends on chosen model | Borrow failure handling and modular provider-pattern ideas only. Too broad and not a visual-selection component. |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense; highly mature, frequent releases | Best-in-class media, metadata, chapters, manual/auto subtitles; site breakage requires frequent updates | Downloads/locates media and thumbnails; delegates frames to FFmpeg | Local and free apart from bandwidth/storage; suitable for long video; operationally volatile as YouTube changes | Reuse as external executable/acquisition adapter. Pin/test supported minimum and emit actionable degraded-state errors. Never treat thumbnail as section evidence. |
| [patrickmineault/vid2slides](https://github.com/patrickmineault/vid2slides) | License not established during review; small, low activity | Local/YouTube-derived video, no transcript alignment | FFmpeg thumbnails, face rejection, HMM slide changes, crop detection, Tesseract OCR | Lecture-specific and locally processed; promising concepts but older/narrow | Concepts only unless license is verified: face rejection, slide crop, OCR PDF diagnostics. |
| [timminator/VideOCR](https://github.com/timminator/VideOCR) | MIT; maintained releases, mature OCR utility | Local video | OCR with SSIM-based frame skipping; 200+ languages | Local CPU/GPU choices; aimed at hard subtitles, not instructional visual relevance | Possible OCR/SSIM reference, but wrong primary problem. Prefer Tesseract adapter plus perceptual hashes for first slice. |

No reviewed repository supplies the required end-to-end contract: transcript
learning units, section-bounded candidates, global duplicate ownership,
human-preserved approval, stale invalidation, and Markdown-only publishing.
That orchestration should be native to rexyDigest.

## Proposed domain additions

Use repo vocabulary and add four terms to `CONTEXT.md` when implementation is
approved:

- **Timed Transcript**: ordered source snippets with start and duration. Raw
  evidence, stored beside the text Payload rather than replacing it.
- **Learning Unit**: one stable DeepNote section-bound evidence window derived
  from a Timed Transcript and section text.
- **Visual Candidate**: one source-bound frame proposed for one Learning Unit,
  including timestamp, asset, deterministic signals, judge summary, and
  evidence fingerprint.
- **Visual Review**: durable human decision: `pending | approved | rejected |
  no_visual | stale`.

“Candidate” remains qualified as **Visual Candidate** to avoid confusing it
with an Item or Selection entry.

## Proposed pipeline and ownership

```text
YouTube Source Adapter
  -> Item + text Payload + Timed Transcript sidecar
  -> DeepNote writer -> validated seven-section draft
  -> section segmenter -> stable Learning Units
  -> yt-dlp acquisition cache -> local video + acquisition provenance
  -> bounded extractor per Learning Unit
       PySceneDetect scene candidates
       + fixed-interval fallback
  -> deterministic filtering
       low-information/talking-head heuristics
       + OCR/text density
       + global pHash grouping
  -> image-aware judge ranks surviving frames for each Learning Unit
  -> existing `deep-notes pick` terminal approval, extended in place
  -> versioned Visual Review sidecar
  -> deterministic Markdown renderer inserts approved images only
  -> KnowledgeCard publishes ordinary Markdown
```

DeepNote draft must exist before semantic frame judging because section text is
the query. Markdown is not final until its Visual Review is complete. Legacy
and non-YouTube Items bypass enrichment and retain present generation behavior.

## Sidecars and assets

Suggested layout, adapting the existing Corpus/audit convention:

```text
corpus/visuals/youtube_<video-id>/
  source.json                 # acquisition + transcript/video fingerprints
  transcript.json             # timestamped snippets
  deep_<end-date>/
    candidates.json           # units, candidates, signals, judge summary
    review.json               # durable human decisions and evidence hashes
assets/visuals/youtube_<video-id>/
  frame_000754_<hash8>.jpg    # only retained candidates/approved assets
```

Core candidate fields:

```json
{
  "schema_version": 1,
  "candidate_id": "youtube:<video>:754:<pixel-hash>",
  "section_id": "deep:<item-id>:04-key-evidence",
  "window": {"start_seconds": 720, "end_seconds": 780},
  "source": {
    "type": "youtube",
    "video_id": "...",
    "timestamp_seconds": 754,
    "timestamp_url": "https://www.youtube.com/watch?v=...&t=754s"
  },
  "asset_path": "assets/visuals/.../frame_000754_ab12cd34.jpg",
  "reason": "Shows the architecture diagram discussed in this section.",
  "signals": {
    "scene_score": 0.82,
    "duplicate_group": null,
    "perceptual_hash": "...",
    "ocr_text": "...",
    "text_density": 0.31,
    "judge_decision": "use",
    "judge_confidence": "high"
  },
  "evidence_fingerprint": "sha256:..."
}
```

Provider/model/raw judge response belongs in run provenance, not candidate
publishing fields. `reason`, normalized decision, and confidence are portable.

Review records should reference `candidate_id` plus `evidence_fingerprint`.
Fingerprint includes video identity/version, timed transcript range, section
text, extraction config/version, and pixel hash. Same fingerprint preserves an
approval on rerun. Changed fingerprint changes approved status to `stale`;
renderer treats stale exactly like pending and emits no image until reviewed.

`no_visual` is an explicit reviewed decision tied to the Learning Unit
fingerprint. It persists while evidence remains valid.

## Selection and review rules

- Search only within a Learning Unit's bounded transcript range plus a small,
  configurable lead/lag margin. Reject frames whose timestamp falls outside
  that effective window.
- Generate scene candidates first. If fewer than the minimum survive, add
  interval samples. Keep thumbnail separate as optional cover evidence only.
- Run cheap deterministic filters before any model call. OCR/text density is a
  positive signal, not a hard requirement: demonstrations and physical
  evidence may contain no text.
- Group perceptual equivalents across the entire DeepNote, not merely adjacent
  frames or one section. A group has one selectable representative by default.
- Judge only surviving candidates against one section's text and transcript
  excerpt. Judge may return `use`, `weak`, or `reject`; it cannot approve.
- Existing terminal workflow shows each section followed by candidate image
  path/preview capability, timestamp, timestamp URL, reason, and judge result.
  Actions: approve candidate, reject candidate, choose another, or no visual.
- A section with zero candidates is valid and records reviewed `no_visual` when
  the reviewer confirms it.
- Final render inserts `![<short section-specific alt>](<relative asset path>)`
  immediately after the supported section. It never emits sidecar data,
  timestamps, judge/provider fields, unreviewed paths, or stale approvals.

Review uses a dependency-free, localhost-only page launched by `deep-notes
pick`; `deep-notes review` resumes the same persisted sidecar. It shows the
readable Markdown draft beside candidate cards, autosaves visual decisions,
and exposes **Save changes** only while text is dirty. Saving changed section
text invalidates only that section's visual decision and reruns its comparison.
**Finish review** is enabled only when every section has an approved visual or
an explicit no-visual decision; an explicit text-only waiver handles visual
pipeline failure. **Close** is always available and never publishes.

## Dependency and reuse proposal

Approve for first slice:

1. `yt-dlp` executable: metadata/subtitle/video acquisition.
2. `ffmpeg`/`ffprobe` executable: probing and exact timestamp frame extraction.
3. PySceneDetect Python dependency: bounded scene transitions.
4. Pillow + `ImageHash`-style pHash, preferably a tiny native wrapper if Pillow
   is already pulled transitively; verify dependency cost before adding
   `imagehash` itself.
5. Tesseract executable behind an optional OCR adapter. Missing OCR degrades
   signals, never text ingestion.
6. Existing Gemini integration behind a new image-judge protocol; memory/mock
   implementation is default in tests.

Do not approve initially: CLIP/torch, vector DB, MCP, Apple Vision-only logic,
cloud OCR, a second LLM SDK, or any publishing framework. They increase install
weight/platform coupling before first-slice evidence justifies them.

## TDD delivery plan after approval

Follow vertical red-green slices, one observable behavior at a time:

1. **Timed evidence tracer:** ingest a fixture Timed Transcript, create one
   bounded Learning Unit, extract fixture frames, approve one candidate through
   the public DeepNote workflow, and observe one ordinary Markdown image.
2. **No visual:** zero candidates and explicit no-visual complete successfully.
3. **Global dedup:** perceptually equivalent fixture frames form one group and
   cannot normally be approved for multiple sections.
4. **Review actions:** approve, reject, replace, and no-visual persist through
   the workflow's public interface.
5. **Rerun semantics:** unchanged fingerprints preserve decisions; changed
   source/section/extractor evidence marks only affected approvals stale.
6. **Failure isolation:** acquisition/OCR/judge failure reports incomplete
   enrichment while text DeepNote remains usable; no live paid API in tests.
7. **Regression:** latest three existing DeepNote fixtures compare
   byte-for-byte or via an explicitly approved material-similarity rule;
   non-YouTube fixtures bypass visual work.
8. **Real-video characterization:** one opted-in YouTube DeepNote exercises
   transcript segmentation, distinct frames, dedup, judge, review, and output;
   recorded local fixtures make CI deterministic.

Acceptance tests from the request map directly onto slices 1–7. Avoid writing
all twelve tests first: each slice adds one failing behavior test, minimal
implementation, then refactor while green.

## Decisions approved after design review

1. Extract real source frames/images only; synthesized visuals are parked.
2. Use ordinary Markdown image syntax; keep evidence and approval metadata in
   rexyDigest sidecars under `corpus/visuals/`.
3. Treat three useful visuals per note as a soft target, with at most one per
   section. No visual is preferable to a weak visual.
4. Use comparative, image-aware Gemini judgment per section. Human approval is
   final; changed evidence or section text makes the prior decision stale.
5. Use the local minimalist review page described above rather than terminal
   image review. Keep `KnowledgeCard_Inbox/` limited to reviewed final notes.
