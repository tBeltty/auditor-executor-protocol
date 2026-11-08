import { describe, expect, mock, test } from 'claude-code/testing'
import type { AgentInfo, On, ProcessRunResult } from 'claude-code'

import { commandWorkers, orcaWorkers, overall, percent, phaseShares, taskIdsIn } from '../hooks/progress'
import { STATUS } from './fixtures/status'

const RUN = 'docs/run'
const PANE = {
  plugin: 'aeprogress',
  component: 'Pane',
  requestId: 'aeprogress',
  props: {
    title: 'AEP progress · run',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

const ran = (stdout: string, exitCode = 0, stderr = ''): { value: ProcessRunResult } => ({
  value: { exitCode, stdout, stderr, isStdoutTruncated: false, isStderrTruncated: false },
})

type Engine = {
  env?: Record<string, string>
  agents?: AgentInfo[]
  aepkit?: (argv: readonly string[]) => { value: ProcessRunResult } | { deny: string }
  orcaPs?: unknown
  orcaRepo?: string
  workersOut?: string
}

/** Hooks standing for the engine beneath the plugin, aepkit and the harnesses. */
function engine(on: On, given: Engine = {}): string[][] {
  const calls: string[][] = []
  mock.clock(on)
  on('command.register', () => ({ value: { command: 'aeprogress' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('env.get', (_, e) => ({ value: given.env?.[e.name] }))
  on('agent.list', () => ({ value: given.agents ?? [] }))
  on('process.run', (_, e) => {
    const argv = [...e.argv]
    calls.push(argv)
    if (argv.includes('status')) return given.aepkit ? given.aepkit(argv) : ran(JSON.stringify(STATUS))
    if (argv.includes('current')) {
      return ran(JSON.stringify({ result: { worktree: { repoId: given.orcaRepo ?? 'repo-1' } } }))
    }
    if (argv.includes('ps')) return ran(JSON.stringify(given.orcaPs ?? { result: { worktrees: [] } }))
    return ran(given.workersOut ?? '')
  })
  return calls
}

describe('the arithmetic', () => {
  test('phases are weighted by the plan and CONDITIONAL counts half', async () => {
    const shares = phaseShares(STATUS.phases, STATUS.items)
    expect(shares.map(p => [p.id, p.approved, p.total, p.fraction])).toEqual([
      ['P0', 2, 2, 1],
      ['P1', 1, 4, 0.375],
      ['P2', 0, 0, 0],
    ])
    // (1 * 1 + 2 * 0.375 + 1 * 0) / 4
    expect(percent(overall(shares))).toBe('43.8%')
  })

  test('task IDs are read in any case and once each', async () => {
    expect(taskIdsIn('ana-p1-t3 | Ana | P1-T3 and P2-G1, not P1-X2')).toEqual(['P1-T3', 'P2-G1'])
  })

  test('a workers command marks only the IDs this run has', async () => {
    const known = new Set(['P1-T3'])
    expect(commandWorkers('w1 working on P1-T3\nw2 on P9-T9\n', known)).toEqual([
      { taskId: 'P1-T3', who: 'w1 working on P1-T3', source: 'command' },
    ])
  })

  test('an Orca worktree counts while its agent has not finished, in this repository', async () => {
    const ps = JSON.stringify({
      result: {
        worktrees: [
          { repoId: 'r', displayName: 'Cy | P1-T3', agents: [{ state: 'working' }] },
          { repoId: 'r', displayName: 'Bo | P1-T2', agents: [{ state: 'done' }] },
          { repoId: 'other', displayName: 'Zed | P1-G1', agents: [{ state: 'working' }] },
          { repoId: 'r', path: '/w/dee-p1-g1', agents: [{ state: 'waiting' }] },
        ],
      },
    })
    const known = new Set(['P1-T2', 'P1-T3', 'P1-G1'])
    expect(orcaWorkers(ps, 'r', known)).toEqual([
      { taskId: 'P1-T3', who: 'Cy | P1-T3', source: 'orca' },
      { taskId: 'P1-G1', who: 'dee-p1-g1 (waiting)', source: 'orca' },
    ])
  })
})

test('the pane draws the %, a bar per phase and the open items, on every surface', { options: { runDir: RUN } }, async ($, on) => {
  const calls = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(calls[0]).toEqual(['aepkit', 'status', '--json', RUN])

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^43\.8%$/ }))?.text).toBe('43.8%')
    expect(await ui.find({ type: 'Text', text: /weighted by the plan/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /2\/2 · 100%/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /1\/4 · 37\.5%/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /not broken down/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /P1-T3 · Cy/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /P1-T2 · CONDITIONAL · Bo/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /In progress/ })).toBeUndefined()
    await ui.unmount()
  }
})

test('a subagent whose spawn prompt names a task shows it in progress', { options: { runDir: RUN } }, async ($, on) => {
  engine(on, {
    agents: [{ id: 'a1', description: 'Executor', type: 'general-purpose', status: 'running' }],
  })
  on('agent.spawn', () => ({ model: 'haiku', agentId: 'a1' }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  await $.agent.spawn({
    tool_use_id: 't1',
    prompt: 'ROLE: Executor, reporting on P1-G1.',
    description: 'Executor',
    subagentType: 'general-purpose',
    provider: { plugin: 'engine', tier: 'core' },
    parentModel: 'opus',
    background: true,
    fork: false,
  })
  const opened = await $.command.run({
    command: 'aeprogress',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: true, columns: 160 },
  })
  expect(opened.text).toBe('43.8% of docs/run: 3/6 approved. Progress pane opened.')

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /In progress/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /P1-G1 · Executor \(subagent\)/ })).toBeDefined()
  await ui.unmount()
})

test('inside Orca, a worker of this repository shows in progress', { options: { runDir: RUN } }, async ($, on) => {
  const calls = engine(on, {
    env: { ORCA_WORKTREE_ID: 'w', ORCA_CLI_BIN_DIR: '/opt/orca/bin' },
    orcaRepo: 'repo-1',
    orcaPs: {
      result: {
        worktrees: [
          { repoId: 'repo-1', displayName: 'Dee | P1-G1', agents: [{ state: 'working' }] },
          { repoId: 'repo-2', displayName: 'Eve | P1-T1', agents: [{ state: 'working' }] },
        ],
      },
    },
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(calls.some(c => c[0] === '/opt/orca/bin/orca' && c.includes('ps'))).toBe(true)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /P1-G1 · Dee \| P1-G1 \(Orca\)/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /Eve/ })).toBeUndefined()
  await ui.unmount()
})

test('outside Orca, nothing asks Orca', { options: { runDir: RUN } }, async ($, on) => {
  const calls = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(calls.some(c => c.some(a => a.endsWith('orca')))).toBe(false)
})

test(
  'any other harness reports through the workers command',
  { options: { runDir: RUN, workersCommand: 'my-harness list --running' } },
  async ($, on) => {
    const calls = engine(on, { workersOut: 'job 7  P1-G1  running\n' })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    expect(calls.some(c => c.join(' ') === 'my-harness list --running')).toBe(true)

    const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /P1-G1 · job 7 {2}P1-G1 {2}running \(worker\)/ })).toBeDefined()
    await ui.unmount()
  },
)

test('without aepkit the pane says how to install it', { options: { runDir: RUN } }, async ($, on) => {
  engine(on, { aepkit: () => ({ deny: 'ENOENT' }) })
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /pipx install aepkit/ })).toBeDefined()
  await ui.unmount()
})

test('an aepkit without --json is told to upgrade', { options: { runDir: RUN } }, async ($, on) => {
  engine(on, { aepkit: () => ran('', 2, 'aepkit: error: unrecognized arguments: --json') })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /pipx upgrade aepkit/ })).toBeDefined()
  await ui.unmount()
})

test('an old aepkit on the PATH does not hide a newer one', { options: { runDir: RUN } }, async ($, on) => {
  const calls = engine(on, {
    aepkit: argv =>
      argv[0] === 'aepkit' ? ran('', 2, 'aepkit: error: unrecognized arguments: --json') : ran(JSON.stringify(STATUS)),
    env: { HOME: '/home/me' },
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(calls.map(c => c[0])).toEqual(['aepkit', '/home/me/.local/bin/aepkit'])

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /^43\.8%$/ }))?.text).toBe('43.8%')
  await ui.unmount()
})
