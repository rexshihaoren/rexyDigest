import fs from "fs";
import path from "path";
import dayjs from "dayjs";
import { GoogleGenerativeAI } from "@google/generative-ai";
import dotenv from "dotenv";

// Load environment variables with .env.local precedence
dotenv.config({ path: path.resolve(process.cwd(), ".env.local") });
dotenv.config({ path: path.resolve(process.cwd(), ".env") });

// Configurable strict mode & error type for missing keys
class ConfigurationError extends Error {
  constructor(message) { super(message); this.name = "ConfigurationError"; }
}
const isStrict = () => process.env.STRICT_ENV === "1" || process.env.STRICT_ENV === "true";

// Resilient model fallbacks (configurable via env)
const DEFAULT_MODEL_FALLBACKS = [
  "gemini-2.5-flash-lite",
  "gemini-2.5-flash",
  "gemini-2.5-pro",
  "gemini-2.0-flash-001"
].join(",");
const MODEL_FALLBACKS_RAW = process.env.MODEL_FALLBACKS;
const MODEL_FALLBACKS = (MODEL_FALLBACKS_RAW !== undefined ? MODEL_FALLBACKS_RAW : DEFAULT_MODEL_FALLBACKS).split(",").map((s) => s.trim()).filter(Boolean);

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const genAI = GEMINI_API_KEY ? new GoogleGenerativeAI(GEMINI_API_KEY) : null;

// #region debug-point A:model-fallbacks
(process.env.TRAE_DEBUG_SESSION && fetch(process.env.TRAE_DEBUG_SERVER_URL || "http://127.0.0.1:7777/event", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId: process.env.TRAE_DEBUG_SESSION, runId: process.env.TRAE_DEBUG_RUN || "pre-fix", hypothesisId: "A", location: "scripts/generate_gist.mjs", msg: "[DEBUG] computed MODEL_FALLBACKS", data: { raw: process.env.MODEL_FALLBACKS, computedCount: MODEL_FALLBACKS.length, computedPreview: MODEL_FALLBACKS.slice(0, 3), hasGeminiKey: Boolean(GEMINI_API_KEY) } }) }).catch(() => {}));
// #endregion

async function generateWithFallbacks(promptText) {
  if (!genAI) throw new ConfigurationError("GEMINI_API_KEY missing. Set it in .env/.env.local or export in shell.");
  for (const name of MODEL_FALLBACKS) {
    try {
      const model = genAI.getGenerativeModel({ model: name });
      const res = await model.generateContent(promptText);
      const text = res?.response?.text?.();
      if (text && text.length) return text;
      console.warn(`[generate_gist] model ${name} returned empty response`);
    } catch (err) {
      console.warn(`[generate_gist] model ${name} failed: ${err?.status || ""} ${err?.statusText || ""} ${err?.message || err}`);
    }
  }
  throw new Error("All fallback models failed");
}

const prompt = fs.readFileSync("prompt_weekly_gist.md", "utf8");
const date = dayjs();
const start = date.subtract(7, "day").format("YYYY-MM-DD");
const end = date.format("YYYY-MM-DD");
const folder = "Weekly_Gist";
const file = `Weekly_Gist_${end}.md`;
const augmentedPrompt = `${prompt}\n\nEXECUTION CONTEXT\n- Coverage window: ${start} to ${end}\n- Generated at: ${end}\n- If no items in window, apply fallbacks per prompt and use VERIFY_NEEDED where appropriate.`;

(async () => {
  let md = "";
  const header = `# Weekly Gist – ${date.format("YYYY-MM-DD")}`;
  try {
    md = await generateWithFallbacks(augmentedPrompt);
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
    ].join("\n");
  }

  fs.mkdirSync(folder, { recursive: true });
  fs.writeFileSync(path.join(folder, file), `${header}\n\n${md}\n`);
  console.log("✅ Created:", file);
})();
