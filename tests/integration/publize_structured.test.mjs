import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { spawnSync } from 'child_process'

function runScript(command, args = [], env = {}) {
  const result = spawnSync(command, args, {
    env: { ...process.env, ...env },
    cwd: process.cwd(),
    encoding: 'utf-8'
  })
  return result
}

describe('publize_brief structured mode', () => {
  it('publishes bilingual strict template without network using empty fallbacks', () => {
    const tempDir = fs.mkdtempSync(path.join(process.cwd(), 'tmp-public-'))

    const res = runScript('node', ['scripts/publize_brief.mjs'], {
      TRANSFORM_MODE: 'structured',
      MODEL_FALLBACKS: '',
      PUBLIC_DIR: tempDir
    })

    expect(res.status).toBe(0)

    const files = fs.readdirSync(tempDir).filter(f => f.startsWith('Weekly_Brief_Public_') && f.endsWith('.md'))
    expect(files.length).toBeGreaterThan(0)

    const outFile = path.join(tempDir, files[0])
    const content = fs.readFileSync(outFile, 'utf-8')

    // The bilingual headers appear after the initial title and metadata
    expect(content).toContain('标题｜Title')
    expect(content).toContain('摘要｜TL;DR')
    expect(content).toContain('要点｜Takeaways')
    expect(content).toContain('启示｜Implication')
    expect(content).toContain('主题｜Topics')
  })
})