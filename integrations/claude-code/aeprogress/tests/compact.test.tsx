import { describe, expect, mock, test } from 'claude-code/testing'
import type { TestBody } from 'claude-code/testing'
import type { On } from 'claude-code'

const TOOL = 'mcp__aeprogress__compact_and_resume'
const BAND = {
  plugin: 'aeprogress',
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 4,
    bodyColumns: 80,
    scroll: { offset: 0, bodyRows: 4 },
    view: {},
  },
} as const

const SUMMARY = [{ role: 'user', text: 'Summary of the session so far.', toolUses: [] }] as never
type Seen = { compacts: (string | undefined)[]; submits: string[]; toasts: string[] }

/** The engine beneath the plugin, with no run: what compacting and resuming reach is kept. */
function engine(on: On, given: { skip?: boolean } = {}) {
  const seen: Seen & { registered: number } = { compacts: [], submits: [], toasts: [], registered: 0 }
  const clock = mock.clock(on)
  on('command.register', () => ({ value: { command: 'aeprogress' } }))
  on('tool.register', () => {
    seen.registered += 1
    return { value: { tool: TOOL } }
  })
  on('turn.complete', () => ({ text: '' }) as never)
  on('tool.call', () => ({ result: 'no such tool' }) as never)
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine band</Text>
  })
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
  on('session.compact', (_, e) => {
    seen.compacts.push(e.instructions)
    return given.skip ? { skip: 'vetoed by a test hook' } : { messages: SUMMARY }
  })
  on('prompt.submit', (_, e) => {
    seen.submits.push(e.text)
    return { text: e.text }
  })
  return { seen, clock }
}

const turnEnd = (extra: Record<string, unknown> = {}) =>
  ({ answer: '', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer', ...extra }) as never

async function start($: Parameters<TestBody>[0]) {
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
}

async function scheduleIt($: Parameters<TestBody>[0]) {
  return JSON.stringify(
    await $.tool.call({ tool: TOOL, resume: 'Resume the plan from the brief: launch P2-T1.', instructions: 'Keep the brief.' } as never),
  )
}

describe('compact on phase close', () => {
  test('the tool schedules the compaction and nothing runs yet', async ($, on) => {
    const { seen, clock } = engine(on)
    await start($)
    expect(await scheduleIt($)).toMatch(/Compaction scheduled/)
    await clock.advance(120_000)
    expect(seen.compacts).toEqual([])
    expect(seen.submits).toEqual([])

    const band = await $.ui.mount({ ...BAND, surface: 'terminal' })
    expect(await band.find({ type: 'Text', text: /Compaction scheduled for the end of this turn/ })).toBeDefined()
    await band.unmount()
  })

  test('at zero it compacts, then resumes with the resume message', async ($, on) => {
    const { seen, clock } = engine(on)
    await start($)
    await scheduleIt($)
    await $.turn.complete(turnEnd())

    const band = await $.ui.mount({ ...BAND, surface: 'desktop' })
    expect(await band.find({ type: 'Text', text: /Compacting in 40s/ })).toBeDefined()
    await band.unmount()

    await clock.advance(39_000)
    expect(seen.compacts).toEqual([])
    await clock.advance(1_000)
    expect(seen.compacts).toEqual(['Keep the brief.'])
    expect(seen.submits).toEqual(['Resume the plan from the brief: launch P2-T1.'])
  })

  test('Cancel compacts nothing and resumes nothing', async ($, on) => {
    const { seen, clock } = engine(on)
    await start($)
    await scheduleIt($)
    await $.turn.complete(turnEnd())
    const band = await $.ui.mount({ ...BAND, surface: 'terminal' })
    await band.press({ key: 'compact-cancel' })
    await band.unmount()
    await clock.advance(60_000)
    expect(seen.compacts).toEqual([])
    expect(seen.submits).toEqual([])
  })

  test('the owner typing a prompt during the countdown cancels it', async ($, on) => {
    const { seen, clock } = engine(on)
    await start($)
    await scheduleIt($)
    await $.turn.complete(turnEnd())
    await clock.advance(10_000)
    await $.prompt.submit({ text: 'wait, one more thing', origin: { kind: 'composer' }, wait: false } as never)
    await clock.advance(60_000)
    expect(seen.compacts).toEqual([])
    expect(seen.submits).toEqual(['wait, one more thing'])
  })

  test('a manual /compact with the countdown pending resumes once', async ($, on) => {
    const { seen, clock } = engine(on)
    await start($)
    await scheduleIt($)
    await $.turn.complete(turnEnd())
    await clock.advance(5_000)
    await $.session.compact({ trigger: 'manual', messages: SUMMARY } as never)
    await clock.advance(60_000)
    expect(seen.compacts).toEqual([undefined])
    expect(seen.submits).toEqual(['Resume the plan from the brief: launch P2-T1.'])
  })

  test('a compaction another hook vetoes ({ skip }) resumes nothing', async ($, on) => {
    const { seen, clock } = engine(on, { skip: true })
    await start($)
    await scheduleIt($)
    await $.turn.complete(turnEnd())
    await clock.advance(40_000)
    expect(seen.compacts).toEqual(['Keep the brief.'])
    expect(seen.submits).toEqual([])
    expect(seen.toasts.some(t => /vetoed/.test(t))).toBe(true)
  })

  test('Compact now does not wait for the countdown', async ($, on) => {
    const { seen } = engine(on)
    await start($)
    await scheduleIt($)
    await $.turn.complete(turnEnd())
    const band = await $.ui.mount({ ...BAND, surface: 'desktop' })
    await band.press({ key: 'compact-now' })
    await band.unmount()
    expect(seen.compacts).toEqual(['Keep the brief.'])
    expect(seen.submits).toEqual(['Resume the plan from the brief: launch P2-T1.'])
  })

  test('a subagent ending its turn does not start the countdown; an aborted turn cancels', async ($, on) => {
    const { seen, clock } = engine(on)
    await start($)
    await scheduleIt($)
    await $.turn.complete(turnEnd({ agentId: 'a1' }))
    await clock.advance(60_000)
    expect(seen.compacts).toEqual([])
    await $.turn.complete(turnEnd({ isAborted: true, reason: 'aborted' }))
    await clock.advance(60_000)
    expect(seen.compacts).toEqual([])
    const band = await $.ui.mount({ ...BAND, surface: 'terminal' })
    expect(await band.find({ type: 'Text', text: /Compact/ })).toBeUndefined()
    await band.unmount()
  })

  test('with the option off, the tool is not offered', { options: { compactOnClose: false } }, async ($, on) => {
    const { seen } = engine(on)
    await start($)
    expect(seen.registered).toBe(0)
    expect(JSON.stringify(await $.tool.call({ tool: TOOL, resume: 'x' } as never))).not.toMatch(/Compaction scheduled/)
  })
})
