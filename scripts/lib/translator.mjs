import { extractComposite, extractTopics } from "./parser.mjs";

/**
 * Translation utilities for converting content to Simplified Chinese.
 */

/**
 * Translates structured items to Simplified Chinese using LLM.
 * @param {Array<Object>} items - Items to translate
 * @param {Function} llmTextFn - LLM text generation function
 * @returns {Promise<Map<number, Object>|null>} Map of index to translations, or null on failure
 */
export async function translateStructured(items, llmTextFn) {
  try {
    const payload = {
      items: items.map((it, index) => ({
        index,
        title: it.titleText,
        tldr: it.tldrText,
        takeaways: it.takeawaysText,
        implication: it.implicationText,
        topics: extractTopics(it.compositeText),
        composite: extractComposite(it.compositeText)
      }))
    };
    const raw = await llmTextFn(JSON.stringify(payload), {
      responseMimeType: "application/json",
      temperature: 0.2,
      systemInstruction:
        "Translate provided fields to Simplified Chinese, preserving Markdown and numbers. " +
        "Return JSON: {\"translations\":[{\"index\":0,\"titleZh\":\"...\",\"tldrZh\":\"...\",\"takeawaysZh\":\"...\",\"implicationZh\":\"...\",\"topicsZh\":\"...\",\"compositeZh\":\"...\"}, ...]}. Only JSON."
    });
    if (!raw) return null;
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      data = JSON.parse(raw.replace(/^```json\s*|\s*```$/g, ""));
    }
    const map = new Map();
    const arr = Array.isArray(data?.translations) ? data.translations : [];
    for (const item of arr) map.set(item.index, item);
    return map;
  } catch {
    return null;
  }
}


