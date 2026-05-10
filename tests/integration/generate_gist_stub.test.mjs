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

describe('generate_gist fallback', () => {
  it('creates stub gist when fallbacks are empty', () => {
    const todayFile = `Weekly_Gist_${new Date().toISOString().split('T')[0]}.md`
    const targetPath = path.join(process.cwd(), 'Weekly_Gist', todayFile)
    
    // Remove existing file if it exists to ensure fresh test
    if (fs.existsSync(targetPath)) {
      fs.unlinkSync(targetPath)
    }

    const res = runScript('node', ['scripts/generate_gist.mjs'], {
      MODEL_FALLBACKS: ''
    })

    expect(res.status).toBe(0)

    // Check that the file was created
    expect(fs.existsSync(targetPath)).toBe(true)

    const content = fs.readFileSync(targetPath, 'utf-8')
    expect(content).toContain('## WEEKLY BRIEF')
    expect(content).toContain('Top Items')
    expect(content).toMatch(/PER-ITEM BLOG NOTES/)
  })
})