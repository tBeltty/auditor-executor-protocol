import { describe, expect, mock, test } from 'claude-code/testing'
import type { TestBody } from 'claude-code/testing'
import type { On, ProcessRunResult } from 'claude-code'

import { REMOTE_MANIFEST, installKind, isNewer, marketplaceDir, versionParts } from '../hooks/update'

const PANE = {
  plugin: 'auditor-executor-protocol',
  component: 'Pane',
  requestId: 'aeprogress',
  props: {
    title: 'AEP progress',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

type Given = {
  installed?: string
  remote?: { status: number; text: string } | 'throws'
  env?: Record<string, string>
  stored?: { at: number; version?: string }
}

/** The engine beneath the plugin, with no run: what the update check reads and asks is kept. */
function engine(on: On, given: Given = {}) {
  const fetched: string[] = []
  const store = new Map<string, unknown>(given.stored ? [['updateCheck', given.stored]] : [])
  const toasts: string[] = []
  const clock = mock.clock(on)
  on('command.register', () => ({ value: { command: 'aeprogress' } }))
  on('tool.register', () => ({ value: { tool: 'mcp__auditor-executor-protocol__compact_and_resume' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('ui.toast', (_, e) => {
    toasts.push(e.text)
    return { value: undefined }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('env.get', (_, e) => ({ value: given.env?.[e.name] }))
  on('agent.list', () => ({ value: [] }))
  on('fs.list', () => ({ value: [] }))
  on('fs.exists', () => ({ value: false }))
  on('fs.read', (_, e) => {
    if (e.path.endsWith('/.claude-plugin/plugin.json')) return { value: JSON.stringify({ version: given.installed ?? '0.4.0' }) }
    throw new Error(`ENOENT: ${e.path}`)
  })
  on('process.run', () => ({ value: { exitCode: 1, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } satisfies ProcessRunResult }))
  on('store.get', (_, e) => ({ value: store.get(e.key) }))
  on('store.set', (_, e) => {
    store.set(e.key, e.value)
    return { value: undefined }
  })
  on('http.fetch', (_, e) => {
    fetched.push(e.url)
    if (given.remote === 'throws') throw new Error('offline')
    const remote = given.remote ?? { status: 200, text: JSON.stringify({ version: '0.4.0' }) }
    return { value: { status: remote.status, ok: remote.status < 300, headers: {}, text: remote.text } }
  })
  return { fetched, store, toasts, clock }
}

async function start($: Parameters<TestBody>[0], clock: { settle: () => Promise<void> }) {
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await clock.settle()
}

describe('versions and install kinds', () => {
  test('versions compare by number, and anything else never counts as newer', async () => {
    expect(versionParts('0.10.2')).toEqual([0, 10, 2])
    expect(isNewer('0.10.0', '0.9.9')).toBe(true)
    expect(isNewer('0.4.0', '0.4.0')).toBe(false)
    expect(isNewer('0.3.9', '0.4.0')).toBe(false)
    expect(isNewer('latest', '0.4.0')).toBe(false)
  })

  test('where the copy runs from says how it was installed', async () => {
    expect(installKind('/home/me/.claude/plugins/synced/aeprogress')).toBe('synced')
    expect(installKind('/home/me/.claude/plugins/cache/auditor-executor-protocol/aeprogress/0.4.0')).toBe('marketplace')
    expect(installKind('C:\\Users\\me\\.claude\\plugins\\cache\\m\\aeprogress\\0.4.0')).toBe('marketplace')
    expect(installKind('/work/repo/integrations/claude-code/aeprogress')).toBe('local')
    expect(marketplaceDir('/home/me/.claude/plugins/cache/auditor-executor-protocol/aeprogress/0.4.0')).toBe(
      '/home/me/.claude/plugins/marketplaces/auditor-executor-protocol',
    )
  })
})

describe('the update check', () => {
  test('a newer published version shows in the pane and once as a toast', async ($, on) => {
    const { fetched, toasts, clock } = engine(on, { installed: '0.4.0', remote: { status: 200, text: '{"version":"0.5.1"}' } })
    await start($, clock)
    expect(fetched).toEqual([REMOTE_MANIFEST])
    expect(toasts.filter(t => /0\.5\.1 is available \(you have 0\.4\.0\)/.test(t))).toHaveLength(1)

    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({ ...PANE, surface })
      expect(await ui.find({ type: 'Text', text: /aeprogress 0\.5\.1 is available \(you have 0\.4\.0\)/ })).toBeDefined()
      await ui.unmount()
    }
  })

  test('the same or an older version shows nothing', async ($, on) => {
    const { toasts, clock } = engine(on, { installed: '0.4.0', remote: { status: 200, text: '{"version":"0.4.0"}' } })
    await start($, clock)
    expect(toasts.some(t => /is available/.test(t))).toBe(false)
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /is available/ })).toBeUndefined()
    await ui.unmount()
  })

  test('GitHub is asked at most once a day; the stored answer stands in between', async ($, on) => {
    const { fetched, toasts, clock } = engine(on, { stored: { at: 0, version: '0.6.0' } })
    await clock.set(60 * 60 * 1000)
    await start($, clock)
    expect(fetched).toEqual([])
    expect(toasts.some(t => /0\.6\.0 is available/.test(t))).toBe(true)
  })

  test('a day later it asks again and keeps the new answer', async ($, on) => {
    const { fetched, store, clock } = engine(on, { stored: { at: 0, version: '0.4.0' }, remote: { status: 200, text: '{"version":"0.4.1"}' } })
    await clock.set(25 * 60 * 60 * 1000)
    await start($, clock)
    expect(fetched).toEqual([REMOTE_MANIFEST])
    expect(store.get('updateCheck')).toEqual({ at: 25 * 60 * 60 * 1000, version: '0.4.1' })
  })

  test('a failed or refused request shows nothing and breaks nothing', async ($, on) => {
    const { toasts, clock } = engine(on, { remote: 'throws' })
    await start($, clock)
    expect(toasts.some(t => /is available/.test(t))).toBe(false)
  })

  test('offline mode and Claude Code without non-essential traffic never ask GitHub', async ($, on) => {
    const { fetched, clock } = engine(on, { env: { CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1' } })
    await start($, clock)
    expect(fetched).toEqual([])
  })

  test('with the check off, nothing is read or asked', { options: { updateCheck: 'off' } }, async ($, on) => {
    const { fetched, toasts, clock } = engine(on, { remote: { status: 200, text: '{"version":"9.9.9"}' } })
    await start($, clock)
    expect(fetched).toEqual([])
    expect(toasts.some(t => /is available/.test(t))).toBe(false)
  })

  test('offline mode does not ask GitHub', { options: { updateCheck: 'offline' } }, async ($, on) => {
    const { fetched, clock } = engine(on, { remote: { status: 200, text: '{"version":"9.9.9"}' } })
    await start($, clock)
    expect(fetched).toEqual([])
  })
})
