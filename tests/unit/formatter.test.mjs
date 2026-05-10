import { describe, it, expect } from 'vitest';
import {
  mapTypeToEmoji,
  translateTypeCn,
  filterImplication,
  stripTrailingSeparators,
  enforceAggregatorBlockquote,
  enforceCnCoverageWindow,
  insertSeparatorBetweenOverviewAndFirstItem
} from '../../scripts/lib/formatter.mjs';

describe('formatter', () => {
  describe('mapTypeToEmoji', () => {
    it('maps content types to emojis', () => {
      expect(mapTypeToEmoji('Podcast Episode')).toBe('🎧');
      expect(mapTypeToEmoji('Blog Post')).toBe('📝');
      expect(mapTypeToEmoji('Paper')).toBe('📄');
      expect(mapTypeToEmoji('Talk')).toBe('🎤');
      expect(mapTypeToEmoji('YouTube Video')).toBe('📹');
      expect(mapTypeToEmoji('Unknown')).toBe('⭐️');
    });
  });

  describe('translateTypeCn', () => {
    it('translates types to Chinese', () => {
      expect(translateTypeCn('Podcast Episode')).toBe('播客集');
      expect(translateTypeCn('Blog Post')).toBe('博客');
      expect(translateTypeCn('Paper')).toBe('论文');
      expect(translateTypeCn('Unknown')).toBe('未知类型');
    });
  });

  describe('filterImplication', () => {
    it('filters out implication sections', () => {
      const lines = [
        '### Heading',
        '### Implication for Rex Ren',
        'Some implication text',
        '### Next Heading'
      ];
      const result = filterImplication(lines);
      expect(result.find(l => l.includes('Implication'))).toBeFalsy();
    });
  });

  describe('stripTrailingSeparators', () => {
    it('removes trailing separators and blank lines', () => {
      const md = 'Content\n---\n---\n\n';
      expect(stripTrailingSeparators(md)).toBe('Content');
    });

    it('preserves content with separators in middle', () => {
      const md = 'Content\n---\nMore content';
      expect(stripTrailingSeparators(md)).toBe('Content\n---\nMore content');
    });
  });

  describe('enforceAggregatorBlockquote', () => {
    it('ensures single aggregator blockquote', () => {
      const md = '> 整理者：Rex Ren\nContent\n> 整理者：Rex Ren\nMore';
      const result = enforceAggregatorBlockquote(md);
      const matches = result.match(/> 整理者：Rex Ren/g);
      expect(matches?.length).toBe(1);
    });
  });

  describe('enforceCnCoverageWindow', () => {
    it('formats coverage window in Chinese', () => {
      const md = '覆盖范围 Coverage window：2025-10-20 — 2025-10-27';
      const result = enforceCnCoverageWindow(md);
      expect(result).toContain('2025年');
      expect(result).toContain('至');
    });
  });

  describe('insertSeparatorBetweenOverviewAndFirstItem', () => {
    it('inserts separator before first top item', () => {
      const md = 'Overview\n## Top #1';
      const result = insertSeparatorBetweenOverviewAndFirstItem(md);
      expect(result).toContain('---');
    });

    it('does not duplicate existing separator', () => {
      const md = 'Overview\n---\n## Top #1';
      const result = insertSeparatorBetweenOverviewAndFirstItem(md);
      const matches = result.match(/---/g);
      expect(matches?.length).toBe(1);
    });
  });
});


