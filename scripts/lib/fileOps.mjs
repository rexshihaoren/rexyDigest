import fs from "node:fs";
import path from "node:path";

/**
 * File system utility functions.
 */

/**
 * Finds the latest Weekly Gist file in a directory.
 * @param {string} dir - Directory to search
 * @returns {string|null} Path to latest file, or null if not found
 */
export function findLatest(dir) {
  try {
    const abs = path.resolve(dir);
    const files = fs.readdirSync(abs).filter((n) => /^Weekly_Gist_\d{4}-\d{2}-\d{2}\.md$/.test(n));
    const sorted = files
      .map((name) => ({ name, full: path.join(abs, name), mtimeMs: fs.statSync(path.join(abs, name)).mtimeMs }))
      .sort((a, b) => b.mtimeMs - a.mtimeMs);
    return sorted[0]?.full || null;
  } catch {
    return null;
  }
}

/**
 * Ensures a directory exists, creating it if necessary.
 * @param {string} d - Directory path
 * @returns {string} Absolute path to the directory
 */
export function ensureDir(d) {
  const abs = path.resolve(d);
  if (!fs.existsSync(abs)) fs.mkdirSync(abs, { recursive: true });
  return abs;
}

/**
 * Sets GitHub Actions outputs.
 * @param {Object<string, string>} o - Object with output key-value pairs
 */
export function setOutputs(o) {
  const f = process.env.GITHUB_OUTPUT;
  if (!f) return;
  fs.appendFileSync(f, Object.entries(o).map(([k, v]) => `${k}=${v}`).join("\n") + "\n");
}


