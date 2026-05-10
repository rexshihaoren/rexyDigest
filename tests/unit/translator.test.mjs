import { describe, it, expect, vi } from 'vitest';
import { translateStructured } from '../../scripts/lib/translator.mjs';

describe('translator', () => {
  describe('translateStructured', () => {
    it('returns null when llm function returns null', async () => {
      const llmTextFn = vi.fn().mockResolvedValue(null);
      const items = [{ titleText: 'Test', tldrText: '', takeawaysText: '', implicationText: '', compositeText: '' }];
      const result = await translateStructured(items, llmTextFn);
      expect(result).toBeNull();
    });

    it('parses JSON translation response', async () => {
      const translations = {
        translations: [
          { index: 0, titleZh: '测试', tldrZh: '摘要', takeawaysZh: '要点', implicationZh: '启示', topicsZh: '主题', compositeZh: '8.5' }
        ]
      };
      const llmTextFn = vi.fn().mockResolvedValue(JSON.stringify(translations));
      const items = [
        { titleText: 'Test', tldrText: 'Summary', takeawaysText: 'Takeaways', implicationText: 'Implication', compositeText: '8.5. Topics: Test' }
      ];
      const result = await translateStructured(items, llmTextFn);
      expect(result).toBeTruthy();
      expect(result?.get(0)?.titleZh).toBe('测试');
    });

    it('handles JSON wrapped in code fences', async () => {
      const translations = {
        translations: [{ index: 0, titleZh: '测试' }]
      };
      const llmTextFn = vi.fn().mockResolvedValue(`\`\`\`json\n${JSON.stringify(translations)}\n\`\`\``);
      const items = [{ titleText: 'Test', tldrText: '', takeawaysText: '', implicationText: '', compositeText: '' }];
      const result = await translateStructured(items, llmTextFn);
      expect(result).toBeTruthy();
      expect(result?.get(0)?.titleZh).toBe('测试');
    });

    it('returns null on parse error', async () => {
      const llmTextFn = vi.fn().mockResolvedValue('invalid json');
      const items = [{ titleText: 'Test', tldrText: '', takeawaysText: '', implicationText: '', compositeText: '' }];
      const result = await translateStructured(items, llmTextFn);
      expect(result).toBeNull();
    });
  });
});


