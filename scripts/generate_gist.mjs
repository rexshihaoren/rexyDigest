import fs from "fs";
import path from "path";
import dayjs from "dayjs";
import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

const prompt = fs.readFileSync("prompt_weekly_gist.md", "utf8");
const date = dayjs();
const start = date.subtract(7, "day").format("YYYY-MM-DD");
const end = date.format("YYYY-MM-DD");
const folder = "Weekly_Gist";
const file = `Weekly_Gist_${end}.md`;
const augmentedPrompt = `${prompt}\n\nEXECUTION CONTEXT\n- Coverage window: ${start} to ${end}\n- Generated at: ${end}\n- If no items in window, apply fallbacks per prompt and use VERIFY_NEEDED where appropriate.`;

(async () => {
  const res = await model.generateContent(augmentedPrompt);
  const md = res.response.text();
  fs.mkdirSync(folder, { recursive: true });
  fs.writeFileSync(
    path.join(folder, file),
    `# Weekly Gist – ${date.format("YYYY-MM-DD")}\n\n${md}\n`
  );
  console.log("✅ Created:", file);
})();