import fs from "fs";
import path from "path";
import dayjs from "dayjs";
import { GoogleGenerativeAI } from "@google/generative-ai";
import dotenv from "dotenv";
import { resolveModelFallbacks } from "./lib/config.mjs";

// Load environment variables with .env.local precedence
dotenv.config({ path: path.resolve(process.cwd(), ".env.local") });
dotenv.config({ path: path.resolve(process.cwd(), ".env") });

// Configurable strict mode & error type for missing keys
class ConfigurationError extends Error {
  constructor(message) { super(message); this.name = "ConfigurationError"; }
}
const isStrict = () => process.env.STRICT_ENV === "1" || process.env.STRICT_ENV === "true";

// Resilient model fallbacks (configurable via env)
const MODEL_FALLBACKS = resolveModelFallbacks();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";
const GEMINI_API_KEY_TRIMMED = GEMINI_API_KEY.trim();
const genAI = GEMINI_API_KEY_TRIMMED ? new GoogleGenerativeAI(GEMINI_API_KEY_TRIMMED) : null;

async function generateWithFallbacks(promptText) {
  if (!GEMINI_API_KEY_TRIMMED || !genAI) {
    throw new ConfigurationError("GEMINI_API_KEY missing. Set it in .env/.env.local or export in shell.");
  }
  for (const name of MODEL_FALLBACKS) {
    try {
      const model = genAI.getGenerativeModel({ model: name });
      const res = await model.generateContent(promptText);
      const text = res?.response?.text?.();
      if (text && text.length) return { text, model: name };
      console.warn(`[generate_gist] model ${name} returned empty response`);
    } catch (err) {
      console.warn(`[generate_gist] model ${name} failed: ${err?.status || ""} ${err?.statusText || ""} ${err?.message || err}`);
    }
  }
  throw new Error("All fallback models failed");
}

const prompt = fs.readFileSync("prompt_weekly_gist.md", "utf8");
const endOverride = process.env.END_DATE || process.env.TARGET_DATE;
const date = endOverride ? dayjs(endOverride) : dayjs();
if (!date.isValid()) throw new Error(`Invalid END_DATE/TARGET_DATE: ${endOverride}`);
const start = date.subtract(7, "day").format("YYYY-MM-DD");
const end = date.format("YYYY-MM-DD");
const folder = "Weekly_Gist";
const file = `Weekly_Gist_${end}.md`;
const linkIntegrityBlock = `
MANDATORY LINK INTEGRITY (repeat of prompt — do not skip)
- Never output links under example.com / example.org or other placeholders.
- Never invent YouTube, arXiv, blog, or podcast URLs. If you cannot verify a canonical URL from retrieval, use VERIFY_NEEDED plus one search query string — not a fake URL.
- Slug-style URLs that encode the title or date are almost always wrong; do not generate them.
`.trim();

const augmentedPrompt = `${prompt}\n\nEXECUTION CONTEXT\n- Coverage window: ${start} to ${end}\n- Generated at: ${end}\n- If no items in window, apply fallbacks per prompt and use VERIFY_NEEDED where appropriate.\n\n${linkIntegrityBlock}`;

(async () => {
  let md = "";
  let usedModel = "";
  const header = `# Weekly Gist – ${date.format("YYYY-MM-DD")}`;
  try {
    const res = await generateWithFallbacks(augmentedPrompt);
    md = res?.text || "";
    usedModel = res?.model || "";
  } catch (err) {
    const reason = (err && err.message) ? err.message : "Unknown error";
    if (isStrict() && err instanceof ConfigurationError) {
      // In strict mode, propagate missing-key error to fail fast
      throw err;
    }
    console.warn("[generate_gist] Falling back to stub content:", reason);
    // Minimal stub WEEKLY BRIEF section to keep the publish pipeline testable
    md = [
      "## WEEKLY BRIEF",
      "",
      `**COVERAGE_WINDOW:** ${start} to ${end}`,
      "",
      "### Top Items for Rex Ren",
      "",
      `1. ⭐️ **Pipeline Test (Demo)** — **End-to-End Flow Validation (Demo)** — ${end} — [Demo Link](https://example.com)`,
      "* **TL;DR:** Pipeline test stub entry for performance validation.",
      "* **Key Takeaways:** Confirms gist generation, parsing, and strict-template publishing.",
      "* **Implication for Rex Ren:** Ensures reliable end-to-end formatting and separators.",
      "* **CompositeScore:** 8.0. Topics: Pipeline, Test",
      "",
      "### C) PER-ITEM BLOG NOTES (stub)",
      "",
      "# Pipeline Test (Demo) — End-to-End Article",
      "",
      "> 整理者：Rex Ren",
      "",
      "──────────────────────────────",
      "",
      "### Summary | 摘要",
      "",
      "**中文**",
      "演示条目，用于验证 Section C 与 strict 转换。",
      "",
      "**English**",
      "Demo entry for Section C and strict-transform review.",
      "",
      "---",
      "",
    ].join("\n");
  }

  fs.mkdirSync(folder, { recursive: true });
  fs.writeFileSync(path.join(folder, file), `${header}\n\n${md}\n`);
  const dbg = String(process.env.GEN_DEBUG || "").toLowerCase();
  if (dbg === "1" || dbg === "true") {
    const metaDir = path.join(folder, "Debug");
    fs.mkdirSync(metaDir, { recursive: true });
    const meta = {
      start,
      end,
      usedModel,
      modelFallbacks: MODEL_FALLBACKS,
      strict: isStrict(),
      mdLength: md.length
    };
    fs.writeFileSync(path.join(metaDir, `Weekly_Gist_${end}.meta.json`), JSON.stringify(meta, null, 2));
  }
  console.log("✅ Created:", file);
})();
