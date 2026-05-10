import { describe, it, expect } from "vitest";
import { isPerItemBlogNotesHeader } from "../../scripts/lib/transform_strict.mjs";

describe("isPerItemBlogNotesHeader", () => {
  it("matches ## PER-ITEM BLOG NOTES and ### C) variants", () => {
    expect(isPerItemBlogNotesHeader("## PER-ITEM BLOG NOTES")).toBe(true);
    expect(isPerItemBlogNotesHeader("## C) PER-ITEM BLOG NOTES (PE-style)")).toBe(true);
    expect(isPerItemBlogNotesHeader("### C) PER-ITEM BLOG NOTES (bilingual)")).toBe(true);
    expect(isPerItemBlogNotesHeader("# PER-ITEM BLOG NOTES")).toBe(true);
  });

  it("matches bold C) and plain bold headers", () => {
    expect(isPerItemBlogNotesHeader("**C) PER-ITEM BLOG NOTES**")).toBe(true);
    expect(isPerItemBlogNotesHeader("**PER-ITEM BLOG NOTES (CN/EN)**")).toBe(true);
  });

  it("rejects non-section-C lines", () => {
    expect(isPerItemBlogNotesHeader("# Some Article Title")).toBe(false);
    expect(isPerItemBlogNotesHeader("## WEEKLY BRIEF")).toBe(false);
  });
});
