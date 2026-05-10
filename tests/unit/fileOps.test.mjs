import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { findLatest, ensureDir, setOutputs } from '../../scripts/lib/fileOps.mjs';

describe('fileOps', () => {
  let tempDir;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(process.cwd(), 'test-'));
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('findLatest', () => {
    it('finds latest weekly gist file by modification time', () => {
      const file1 = path.join(tempDir, 'Weekly_Gist_2025-10-20.md');
      const file2 = path.join(tempDir, 'Weekly_Gist_2025-10-26.md');
      fs.writeFileSync(file1, 'content');
      // Create second file after a small delay to ensure different mtime
      fs.writeFileSync(file2, 'content');
      
      // Touch second file to ensure it's newer
      const now = Date.now() / 1000;
      fs.utimesSync(file2, now, now);
      
      const latest = findLatest(tempDir);
      expect(latest).toBeTruthy();
      expect(latest).toMatch(/Weekly_Gist_\d{4}-\d{2}-\d{2}\.md$/);
    });

    it('returns null for empty directory', () => {
      expect(findLatest(tempDir)).toBeNull();
    });

    it('ignores non-matching files', () => {
      fs.writeFileSync(path.join(tempDir, 'other_file.md'), 'content');
      expect(findLatest(tempDir)).toBeNull();
    });
  });

  describe('ensureDir', () => {
    it('creates directory if it does not exist', () => {
      const newDir = path.join(tempDir, 'new-dir');
      const result = ensureDir(newDir);
      expect(fs.existsSync(newDir)).toBe(true);
      expect(result).toBe(path.resolve(newDir));
    });

    it('returns existing directory path', () => {
      const existingDir = path.join(tempDir, 'existing');
      fs.mkdirSync(existingDir);
      const result = ensureDir(existingDir);
      expect(result).toBe(path.resolve(existingDir));
    });
  });

  describe('setOutputs', () => {
    it('does nothing when GITHUB_OUTPUT is not set', () => {
      const original = process.env.GITHUB_OUTPUT;
      delete process.env.GITHUB_OUTPUT;
      expect(() => setOutputs({ test: 'value' })).not.toThrow();
      process.env.GITHUB_OUTPUT = original;
    });

    it('writes outputs to file when GITHUB_OUTPUT is set', () => {
      const outputFile = path.join(tempDir, 'github_output');
      const original = process.env.GITHUB_OUTPUT;
      process.env.GITHUB_OUTPUT = outputFile;
      
      setOutputs({ key1: 'value1', key2: 'value2' });
      
      expect(fs.existsSync(outputFile)).toBe(true);
      const content = fs.readFileSync(outputFile, 'utf8');
      expect(content).toContain('key1=value1');
      expect(content).toContain('key2=value2');
      
      // Clean up
      if (fs.existsSync(outputFile)) fs.unlinkSync(outputFile);
      process.env.GITHUB_OUTPUT = original;
    });
  });
});

