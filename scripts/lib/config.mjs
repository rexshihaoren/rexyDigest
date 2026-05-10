/**
 * Shared runtime configuration for all scripts.
 * Any value can be overridden at runtime via environment variables.
 */

export const DEFAULT_MODEL_FALLBACKS = [
  "gemini-2.5-flash-lite",
  "gemini-2.5-flash",
  "gemini-2.5-pro",
  "gemini-2.0-flash-001",
];

/**
 * Resolves the active model fallback list.
 * Precedence: MODEL_FALLBACKS env var > DEFAULT_MODEL_FALLBACKS above.
 */
export function resolveModelFallbacks() {
  const raw = process.env.MODEL_FALLBACKS;
  if (raw !== undefined) {
    return raw.split(",").map((s) => s.trim()).filter(Boolean);
  }
  return DEFAULT_MODEL_FALLBACKS;
}
