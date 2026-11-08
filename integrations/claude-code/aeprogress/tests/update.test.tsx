import { describe, expect, mock, test } from 'claude-code/testing'
import type { TestBody } from 'claude-code/testing'
import type { On, ProcessRunResult } from 'claude-code'

import { catalogEntryVersion, installKind, isNewer, marketplaceDir, versionParts } from '../hooks/update'

type Seen = { fetched: string[]; reads: string[]; toasts: string[] }

/** The engine beneath the plugin, with no run: every file read and network request is kept. */
function engine(on: On): Seen & { clock: { settle: () => Promise<void> } } {
  const seen: Seen = { fetched: [], reads: [], toasts: [] }
  const clock = mock.clock(on)
  on('command.register', () => ({ value: { command: 'aeprogress' } }))
  on('tool.register', () => ({ value: { tool: 'mcp__auditor-executor-protocol__compact_and_resume' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('ui.toast', (_, e) => {
    seen.toasts.push(e.text)
    return { value: undefined }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('env.get', () => ({ value: undefined }))
  on('agent.list', () => ({ value: [] }))
  on('fs.list', () => ({ value: [] }))
  on('fs.exists', () => ({ value: false }))
  on('fs.read', (_, e) => {
    seen.reads.push(e.path)
    throw new Error(`ENOENT: ${e.path}`)
  })
  on('process.run', () => ({ value: { exitCode: 1, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } satisfies ProcessRunResult }))
  on('http.fetch', (_, e) => {
    seen.fetched.push(e.url)
    return { value: { status: 200, ok: true, headers: {}, text: '{"version":"9.9.9"}' } }
  })
  return { ...seen, clock }
}

async function start($: Parameters<TestBody>[0], clock: { settle: () => Promise<void> }) {
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await clock.settle()
}

describe('versions, install kinds and the catalog', () => {
  test('versions compare by number, and anything else never counts as newer', async () => {
    expect(versionParts('0.10.2')).toEqual([0, 10, 2])
    expect(isNewer('0.10.0', '0.9.9')).toBe(true)
    expect(isNewer('0.4.0', '0.4.0')).toBe(false)
    expect(isNewer('0.3.9', '0.4.0')).toBe(false)
    expect(isNewer('latest', '0.4.0')).toBe(false)
  })

  test('where the copy runs from says how it was installed', async () => {
    expect(installKind('/home/me/.claude/plugins/synced/auditor-executor-protocol')).toBe('synced')
    expect(installKind('/home/me/.claude/plugins/cache/auditor-executor-protocol/auditor-executor-protocol/0.5.4')).toBe('marketplace')
    expect(installKind('C:\\Users\\me\\.claude\\plugins\\cache\\m\\p\\0.5.4')).toBe('marketplace')
    expect(installKind('/work/repo/integrations/claude-code/aeprogress')).toBe('local')
    expect(marketplaceDir('/home/me/.claude/plugins/cache/auditor-executor-protocol/auditor-executor-protocol/0.5.4')).toBe(
      '/home/me/.claude/plugins/marketplaces/auditor-executor-protocol',
    )
  })

  test('the catalog entry names the version Claude Code would install', async () => {
    const catalog = JSON.stringify({ plugins: [{ name: 'other', version: '9.0.0' }, { name: 'auditor-executor-protocol', version: '0.6.0' }] })
    expect(catalogEntryVersion(catalog, 'auditor-executor-protocol')).toBe('0.6.0')
    expect(catalogEntryVersion(catalog, 'missing')).toBeUndefined()
    expect(catalogEntryVersion('not json', 'auditor-executor-protocol')).toBeUndefined()
  })
})

describe('the update check', () => {
  test('makes no network request, ever', async ($, on) => {
    const seen = engine(on)
    await start($, seen.clock)
    await $.command.run({ command: 'aeprogress', args: '', origin: { kind: 'composer' }, presentation: { isFullscreen: true, columns: 160 } })
    await seen.clock.settle()
    expect(seen.fetched).toEqual([])
  })

  test('a copy loaded in place reads no catalog and shows no notice', async ($, on) => {
    const seen = engine(on)
    await start($, seen.clock)
    expect(seen.reads.filter(p => p.endsWith('marketplace.json'))).toEqual([])
    expect(seen.toasts.some(t => /is available/.test(t))).toBe(false)
  })

  test('with the check off, nothing is read for it', { options: { updateCheck: 'off' } }, async ($, on) => {
    const seen = engine(on)
    await start($, seen.clock)
    expect(seen.reads.filter(p => p.endsWith('marketplace.json'))).toEqual([])
  })
})
