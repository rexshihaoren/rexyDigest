import { describe, it, expect } from 'vitest';
import {
  extractBrief,
  removeWeeklyBriefHeader,
  extractTopItemsSection,
  extractTitleSegment,
  parseMetaFromHeading,
  extractComposite,
  extractTopics,
  parseItemsFromBrief
} from '../../scripts/lib/parser.mjs';

describe('parser', () => {
  describe('extractBrief', () => {
    it('extracts weekly brief section from markdown', () => {
      const md = `# Title
Some content
## WEEKLY BRIEF
Brief content here
### Top Items
More content
## Other Section`;
      const result = extractBrief(md);
      expect(result).toBeTruthy();
      expect(result.join('\n')).toContain('WEEKLY BRIEF');
      expect(result.join('\n')).toContain('Brief content');
      expect(result.join('\n')).not.toContain('Other Section');
    });

    it('returns null if weekly brief not found', () => {
      const md = '# Title\nSome content';
      expect(extractBrief(md)).toBeNull();
    });
  });

  describe('removeWeeklyBriefHeader', () => {
    it('removes weekly brief header lines', () => {
      const lines = ['## WEEKLY BRIEF', 'Content line'];
      const result = removeWeeklyBriefHeader(lines);
      expect(result).toEqual(['Content line']);
    });
  });

  describe('extractTopItemsSection', () => {
    it('extracts top items section', () => {
      const lines = ['### Top Items for Rex Ren', 'Item 1', 'Item 2'];
      const result = extractTopItemsSection(lines);
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('extractTitleSegment', () => {
    it('extracts title before date separator', () => {
      const heading = 'Title Name — 2025-10-26 — [link](url)';
      expect(extractTitleSegment(heading)).toBe('Title Name');
    });

    it('handles simple title without separator', () => {
      expect(extractTitleSegment('Simple Title')).toBe('Simple Title');
    });
  });

  describe('parseMetaFromHeading', () => {
    it('parses type, date, and url from heading', () => {
      const heading = '(Blog Post) Title — 2025-10-26 — [Link](https://example.com)';
      const result = parseMetaFromHeading(heading);
      expect(result.type).toBe('Blog Post');
      expect(result.date).toBe('2025-10-26');
      expect(result.url).toBe('https://example.com');
    });
  });

  describe('extractComposite', () => {
    it('extracts numeric score', () => {
      expect(extractComposite('8.5. Topics: Test')).toBe('8.5');
      expect(extractComposite('10 Topics: Test')).toBe('10');
    });

    it('returns empty string for invalid input', () => {
      expect(extractComposite('')).toBe('');
      expect(extractComposite(null)).toBe('');
    });
  });

  describe('extractTopics', () => {
    it('extracts topics from text', () => {
      expect(extractTopics('8.5. Topics: AI, ML, Test')).toBe('AI, ML, Test');
    });

    it('returns empty string if no topics found', () => {
      expect(extractTopics('8.5')).toBe('');
    });
  });

  describe('parseItemsFromBrief', () => {
    it('parses items from brief lines', () => {
      const lines = [
        '1. Title — 2025-10-26 — [Link](url)',
        '* **TL;DR:** Summary text',
        '* **Key Takeaways:** Takeaway text',
        '* **CompositeScore:** 8.5. Topics: Test'
      ];
      const result = parseItemsFromBrief(lines);
      expect(result.length).toBe(1);
      expect(result[0].titleText).toBeTruthy();
      expect(result[0].hasTLDR).toBe(true);
      expect(result[0].hasTakeaways).toBe(true);
      expect(result[0].hasComposite).toBe(true);
    });
  });
});


