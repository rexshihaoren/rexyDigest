import fs from "fs";
import path from "path";
import dayjs from "dayjs";
import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

const prompt = fs.readFileSync("prompt_weekly_gist.md", "utf8");
const date = dayjs();
const folder = "Weekly_Gist";
const file = `Weekly_Gist_${date.format("YYYY-[W]WW")}.md`;

(async () => {
  const res = await model.generateContent(prompt);
  const md = res.response.text();
  fs.mkdirSync(folder, { recursive: true });
  fs.writeFileSync(
    path.join(folder, file),
    `# Weekly Gist – ${date.format("YYYY-MM-DD")}\n\n${md}\n\n---\n## 🧠 Reflections\n- `
  );
  console.log("✅ Created:", file);
})();