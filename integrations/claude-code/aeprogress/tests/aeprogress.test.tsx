import { describe, expect, mock, test } from 'claude-code/testing'
import type { AgentInfo, On, ProcessRunResult } from 'claude-code'

import { chipLines, chipOf } from '../hooks/layout'
import { orcaLaunch, refusals, spotlightBusy } from '../hooks/limit'
import { indexerCpu, linuxMachine, sysctlMachine, windowsMachine } from '../hooks/machine'
import { commandWorkers, orcaWorkers, overall, percent, phaseShares, taskIdsIn } from '../hooks/progress'
import { CPUINFO, LOADAVG } from './fixtures/linux'
import { STATUS } from './fixtures/status'
import { cardsOf, linesOf, overflowing } from './rows'

const RUN = 'docs/run'
const PANE = {
  plugin: 'auditor-executor-protocol',
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
  /** Files the machine reading finds (`/proc/loadavg`, `/usr/sbin/sysctl`, ...). */
  files?: Record<string, string>
  /** Answers for commands, by argv joined with spaces; checked before the defaults. */
  commands?: Record<string, string>
  /** Live Orca dispatch ids for `worker-list`, or 'fail' when Orca cannot be asked. */
  orcaLive?: string[] | 'fail'
  /** No run found under the working directory. */
  noRun?: boolean
}

/** Hooks standing for the engine beneath the plugin, aepkit and the harnesses. */
function engine(on: On, given: Engine = {}): string[][] {
  const calls: string[][] = []
  mock.clock(on)
  // The shell beneath the plugin: what reaches it is recorded, as `SHELL <command>`.
  // Beneath the plugin, an Agent call starts a subagent (a1, a2, ...) and any other tool
  // is the shell, recorded as `SHELL <command>`.
  let started = 0
  on('tool.call', (_, e) => {
    if (e.tool === 'Agent') {
      started += 1
      const id = `a${started}`
      if (given.agents && !given.agents.some(a => a.id === id)) {
        given.agents.push({ id, description: 'Executor', type: 'general-purpose', status: 'running' })
      }
      calls.push(['AGENT', id])
      return { result: { agentId: id, status: 'async_launched' } } as never
    }
    calls.push(['SHELL', String((e as { command?: string }).command)])
    return { result: 'Started worker dispatchId=ctx_new1' } as never
  })
  on('command.register', () => ({ value: { command: 'aeprogress' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('env.get', (_, e) => ({ value: given.env?.[e.name] }))
  on('agent.list', () => ({ value: given.agents ?? [] }))
  on('ui.toast', () => ({ value: undefined }))
  on('session.cwd', () => ({ value: '/work/session' }))
  on('fs.list', () => ({ value: [] }))
  // The engine hands a relative path over already resolved to an absolute one.
  const file = (path: string) =>
    given.files?.[path] ??
    Object.entries(given.files ?? {}).find(([name]) => !name.startsWith('/') && path.endsWith(`/${name}`))?.[1]
  on('fs.exists', (_, e) => ({ value: file(e.path) !== undefined }))
  on('fs.read', (_, e) => {
    const text = file(e.path)
    if (text === undefined) throw new Error(`ENOENT: ${e.path}`)
    return { value: text }
  })
  on('process.run', (_, e) => {
    const argv = [...e.argv]
    calls.push(argv)
    const answer = given.commands?.[argv.join(' ')]
    if (answer !== undefined) return ran(answer)
    if (argv.includes('worker-list')) {
      if (given.orcaLive === 'fail') return ran('', 1, 'orca: runtime not reachable')
      const workers = (given.orcaLive ?? []).map(dispatchId => ({ dispatchId, liveness: 'live', outcome: 'in_progress' }))
      return ran(JSON.stringify({ ok: true, result: { workers } }))
    }
    if (argv.includes('rev-parse')) return ran('/work/proj\n')
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

  test('a workers command marks only the IDs this run has, without repeating the ID', async () => {
    const known = new Set(['P1-T3', 'P1-G1'])
    expect(commandWorkers('w1 working on P1-T3\nw2 on P9-T9\nCy | P1-G1 | building\nP1-T3\n', known)).toEqual([
      { taskId: 'P1-T3', who: 'w1 working on', source: 'command' },
      { taskId: 'P1-G1', who: 'Cy building', source: 'command' },
      { taskId: 'P1-T3', who: 'worker', source: 'command' },
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
      { taskId: 'P1-T3', who: 'Cy', source: 'orca' },
      { taskId: 'P1-G1', who: 'dee (waiting)', source: 'orca' },
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
    expect(await ui.find({ type: 'Text', text: /1\/4 approved · 37\.5%/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /not broken down/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /AWAITING AUDIT/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /P1-T3 {2}Cy/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /NEEDS ATTENTION/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /P1-T2 {2}conditional · Bo/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /IN PROGRESS/ })).toBeUndefined()
    // The launch limit's occupancy and its load threshold.
    expect(await ui.find({ type: 'Text', text: /workers 0\/2 {3}building 0\/1/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Launch limit holds builds above 75%/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Read from run\/compliance-log\.md at/ })).toBeDefined()
    await ui.unmount()
  }
})

test('a subagent whose spawn prompt names a task shows it in progress', { options: { runDir: RUN } }, async ($, on) => {
  engine(on, {
    agents: [{ id: 'a1', description: 'Executor', type: 'general-purpose', status: 'running' }],
  })
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  await $.tool.call({ tool: 'Agent', prompt: 'ROLE: Executor, reporting on P1-G1.', description: 'Executor' } as never)
  const opened = await $.command.run({
    command: 'aeprogress',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: true, columns: 160 },
  })
  expect(opened.text).toBe('43.8% of docs/run: 3/6 approved. Progress pane opened.')

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /IN PROGRESS/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /P1-G1 {2}Executor · subagent/ })).toBeDefined()
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
  expect(await ui.find({ type: 'Text', text: /P1-G1 {2}Dee · Orca/ })).toBeDefined()
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
    expect(await ui.find({ type: 'Text', text: /P1-G1 {2}job 7 running · worker/ })).toBeDefined()
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

const MAC = {
  '/usr/sbin/sysctl': '',
  '/System/Library/CoreServices': '',
}
const macCommands = (load: string, ps = '') => ({
  '/usr/sbin/sysctl -n vm.loadavg': `{ ${load} 1.00 1.00 }\n`,
  '/usr/sbin/sysctl -n hw.ncpu': '8\n',
  '/bin/ps -A -o %cpu=,comm=': ps,
})
const START = 'orca orchestration worker-start --spec-file handoff.md --agent claude'

type Engine$ = { tool: { call: (input: never) => Promise<unknown> } }

/** Runs a Bash command through the plugin: what reached the shell, and the answer. */
async function bash($: Engine$, calls: string[][], command: string) {
  const before = calls.length
  const result = await $.tool.call({ tool: 'Bash', command } as never)
  const reached = calls.slice(before).filter(c => c[0] === 'SHELL').map(c => c[1])
  return { reached, text: JSON.stringify(result) }
}

describe('the machine readings', () => {
  test('Linux: load over the processors /proc/cpuinfo lists', async () => {
    const m = linuxMachine('1.52 1.20 1.01 2/345 6789\n', 'processor\t: 0\nprocessor\t: 1\nprocessor\t: 2\nprocessor\t: 3\n')
    expect(m).toEqual({ busy: 0.38, detail: 'load 1.5 of 4 cores', os: 'linux', indexerCpu: 0 })
  })

  test('Linux: what a real kernel prints', async () => {
    expect(linuxMachine(LOADAVG, CPUINFO)).toEqual({ busy: 0.06, detail: 'load 0.1 of 2 cores', os: 'linux', indexerCpu: 0 })
  })

  test('macOS: sysctl load over hw.ncpu, and Spotlight added up from ps', async () => {
    const ps = ' 60.1 /System/Library/Frameworks/CoreServices.framework/mds_stores\n 12.0 /usr/libexec/mdworker_shared\n 30.0 /usr/bin/clang\n'
    expect(Math.round(indexerCpu(ps) * 10)).toBe(721)
    expect(sysctlMachine('{ 6.40 5.10 4.20 }', '8', 'macos', ps)).toEqual({
      busy: 0.8,
      detail: 'load 6.4 of 8 cores',
      os: 'macos',
      indexerCpu: 72.1,
    })
  })

  test('Windows: the processors\' LoadPercentage', async () => {
    expect(windowsMachine('37\r\n')).toEqual({ busy: 0.37, detail: 'CPU at 37%', os: 'windows', indexerCpu: 0 })
    expect(windowsMachine('')).toBeUndefined()
  })

  for (const [name, given, lines] of [
    [
      'Linux',
      { files: { '/proc/loadavg': '3.00 2.00 1.00 1/2 3\n', '/proc/cpuinfo': 'processor : 0\nprocessor : 1\nprocessor : 2\nprocessor : 3\n' } },
      [/Machine 75% busy/, /Load 3\.0 of 4 cores/],
    ],
    ['macOS', { files: MAC, commands: macCommands('2.00') }, [/Machine 25% busy/, /Load 2\.0 of 8 cores/]],
    [
      'Windows',
      {
        env: { SystemRoot: 'C:\\Windows' },
        commands: {
          'powershell -NoProfile -Command (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average': '42\r\n',
        },
      },
      [/Machine 42% busy/, /CPU at 42%/],
    ],
    ['an unknown system', {}, [/Machine load unknown/]],
  ] as const) {
    test(`the pane shows the load on ${name}`, { options: { runDir: RUN } }, async ($, on) => {
      engine(on, given as Engine)
      await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
      const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
      for (const line of lines) expect(await ui.find({ type: 'Text', text: line })).toBeDefined()
      await ui.unmount()
    })
  }
})

describe('the launch limit rules', () => {
  const limits = { maxWorkers: 2, maxBuilds: 1, maxBusy: 0.75 }
  test('count, builds and load each refuse on their own', async () => {
    const one = [{ id: 'a', kind: 'build' as const }]
    expect(refusals('build', [], undefined, limits)).toEqual([])
    expect(refusals('docs', one, undefined, { ...limits, maxWorkers: 1 })[0]).toBe('1 worker is live (limit 1)')
    expect(refusals('docs', one, undefined, limits)).toEqual([])
    expect(refusals('build', one, undefined, limits)[0]).toMatch(/1 building worker is live/)
    expect(refusals('docs', [...one, { id: 'b', kind: 'docs' }], undefined, limits)[0]).toMatch(/2 workers are live/)
    const busy = { busy: 0.9, detail: 'load 7.2 of 8 cores', os: 'macos' as const, indexerCpu: 0 }
    expect(refusals('build', [], busy, limits)[0]).toMatch(/90% busy/)
    expect(refusals('docs', [], busy, limits)).toEqual([])
  })

  test('a send is a launch only when it reopens a dispatch that is not live', async () => {
    const live = new Set(['ctx_live'])
    expect(orcaLaunch('orca orchestration worker-start --spec x', live)).toBe(true)
    expect(orcaLaunch('orca orchestration send --to dispatch:ctx_old --subject go', live)).toBe(true)
    expect(orcaLaunch('orca orchestration send --to dispatch:ctx_live --subject more', live)).toBe(false)
    expect(orcaLaunch('orca orchestration send --type worker_done --subject done', live)).toBe(false)
    expect(orcaLaunch('git status', live)).toBe(false)
    expect(orcaLaunch('cd w && orca orchestration worker-start --spec x', live)).toBe(true)
    expect(orcaLaunch('"$ORCA_CLI_BIN_DIR/orca" orchestration worker-start --spec x', live)).toBe(true)
    expect(orcaLaunch('ORCA_ENV=1 orca --json orchestration worker-start --spec x', live)).toBe(true)
    expect(orcaLaunch('echo orca orchestration worker-start --spec x', live)).toBe(false)
    expect(orcaLaunch('git commit -m "docs: how orca orchestration worker-start works"', live)).toBe(false)
  })

  test('Spotlight counts as busy only when it stays busy', async () => {
    expect(spotlightBusy([72], 50)).toBe(false)
    expect(spotlightBusy([72, 10], 50)).toBe(false)
    expect(spotlightBusy([10, 72, 64], 50)).toBe(true)
  })
})

describe('the launch limit on Orca', () => {
  test('a worker-start under the limits goes through', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, { files: { ...MAC, 'handoff.md': 'TASK: P1-G1' }, commands: macCommands('1.00'), orcaLive: [] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const { reached } = await bash($, calls, START)
    expect(reached).toEqual([START])
  })

  test('a third worker is refused by count', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, { files: { ...MAC, 'handoff.md': 'Load: docs-only' }, commands: macCommands('1.00'), orcaLive: ['ctx_a', 'ctx_b'] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const { reached, text } = await bash($, calls, START)
    expect(reached).toEqual([])
    expect(text).toMatch(/2 workers are live \(limit 2\)/)
  })

  test('a build is refused while the machine is busy', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, { files: { ...MAC, 'handoff.md': 'TASK: P1-G1' }, commands: macCommands('7.20'), orcaLive: [] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const { reached, text } = await bash($, calls, START)
    expect(reached).toEqual([])
    expect(text).toMatch(/the machine is 90% busy/)
  })

  test('a "Load: docs-only" handoff goes beside a live build', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, {
      files: { ...MAC, 'handoff.md': 'ROLE: Executor.\nLoad: docs-only\nTASK: P1-G1' },
      commands: macCommands('7.20'),
      orcaLive: ['ctx_build'],
    })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const { reached } = await bash($, calls, START)
    expect(reached).toEqual([START])
  })

  test('an inline --spec carrying "Load: docs-only" goes beside a live build', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, { files: MAC, commands: macCommands('7.20'), orcaLive: ['ctx_build'] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const inline = 'orca orchestration worker-start --spec "ROLE: Executor. Load: docs-only. TASK: P1-G1" --agent claude'
    expect((await bash($, calls, inline)).reached).toEqual([inline])
  })

  test('a message to a live worker is never held back', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, { files: MAC, commands: macCommands('7.20'), orcaLive: ['ctx_a', 'ctx_b'] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const send = 'orca orchestration send --to dispatch:ctx_a --subject "one more check"'
    expect((await bash($, calls, send)).reached).toEqual([send])
  })

  test('when Orca cannot count its workers, the launch is refused', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, { files: MAC, commands: macCommands('1.00'), orcaLive: 'fail' })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const { reached, text } = await bash($, calls, START)
    expect(reached).toEqual([])
    expect(text).toMatch(/could not be counted/)
  })

  test('without a run, nothing is held back', { options: {} }, async ($, on) => {
    const calls = engine(on, { files: MAC, commands: macCommands('7.20'), orcaLive: ['ctx_a', 'ctx_b'] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    expect((await bash($, calls, START)).reached).toEqual([START])
  })

  test('with the limit off, nothing is held back', { options: { runDir: RUN, launchLimit: false } }, async ($, on) => {
    const calls = engine(on, { files: MAC, commands: macCommands('7.20'), orcaLive: ['ctx_a', 'ctx_b'] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    expect((await bash($, calls, START)).reached).toEqual([START])
  })
})

describe('the launch limit on Claude Code subagents', () => {
  /** Launches a subagent through the Agent tool and answers what the call returned, as text. */
  const launch = async ($: Engine$, prompt: string) =>
    JSON.stringify(await $.tool.call({ tool: 'Agent', prompt, description: 'Executor' } as never))

  test('a third Executor is refused; a subagent with no task of the run is not', { options: { runDir: RUN } }, async ($, on) => {
    const agents: AgentInfo[] = []
    engine(on, { files: MAC, commands: macCommands('1.00'), agents })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

    expect(await launch($, 'ROLE: Executor, reporting on P1-T3.\nLoad: docs-only')).toMatch(/"agentId":"a1"/)
    expect(await launch($, 'ROLE: Executor, reporting on P1-G1.\nLoad: docs-only')).toMatch(/"agentId":"a2"/)
    expect(await launch($, 'ROLE: Executor, reporting on P1-T2.')).toMatch(/2 workers are live \(limit 2\)/)
    expect(await launch($, 'Find where the parser is defined.')).toMatch(/"agentId":"a3"/)
  })

  test('a building Executor waits for the live build; a docs-only one does not', { options: { runDir: RUN } }, async ($, on) => {
    const agents: AgentInfo[] = []
    engine(on, { files: MAC, commands: macCommands('1.00'), agents })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

    expect(await launch($, 'ROLE: Executor, reporting on P1-T3.')).toMatch(/"agentId":"a1"/)
    expect(await launch($, 'ROLE: Executor, reporting on P1-G1.')).toMatch(/1 building worker is live/)
    expect(await launch($, 'ROLE: Executor, reporting on P1-G1.\nLoad: docs-only')).toMatch(/"agentId":"a2"/)
  })
})

describe('the Spotlight recommendation', () => {
  const ps = ' 64.0 /System/Library/Frameworks/CoreServices.framework/mds_stores\n 9.0 /usr/libexec/mdworker_shared\n'
  const reopen = { command: 'aeprogress', args: '', origin: { kind: 'composer' as const }, presentation: { isFullscreen: true, columns: 160 } }

  test('recommends excluding the project after two busy reads', { options: { runDir: RUN } }, async ($, on) => {
    engine(on, { files: MAC, commands: macCommands('1.00', ps) })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const first = await $.ui.mount({ ...PANE, surface: 'terminal' })
    expect(await first.find({ type: 'Text', text: /Spotlight/ })).toBeUndefined()
    await first.unmount()

    await $.command.run(reopen)
    const second = await $.ui.mount({ ...PANE, surface: 'desktop' })
    const tip = await second.find({ type: 'Text', text: /Spotlight is indexing at 73% CPU/ })
    expect(tip?.text).toMatch(/exclude \/work\/proj in System Settings > Spotlight > Search Privacy/)
    await second.unmount()
  })

  test('says nothing off macOS', { options: { runDir: RUN } }, async ($, on) => {
    engine(on, {
      files: { '/proc/loadavg': '0.50 0.40 0.30 1/2 3\n', '/proc/cpuinfo': 'processor : 0\nprocessor : 1\n' },
      commands: { '/bin/ps -A -o %cpu=,comm=': ps },
    })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    await $.command.run(reopen)
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /Machine 25% busy/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Spotlight/ })).toBeUndefined()
    await ui.unmount()
  })

  test('says nothing when it is off', { options: { runDir: RUN, spotlightTip: false } }, async ($, on) => {
    engine(on, { files: MAC, commands: macCommands('1.00', ps) })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    await $.command.run(reopen)
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /Spotlight/ })).toBeUndefined()
    await ui.unmount()
  })

  test('a refused build names Spotlight when it is part of the load', { options: { runDir: RUN } }, async ($, on) => {
    const calls = engine(on, { files: { ...MAC, 'handoff.md': 'TASK: P1-G1' }, commands: macCommands('7.20', ps), orcaLive: [] })
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const { text } = await bash($, calls, START)
    expect(text).toMatch(/90% busy/)
    expect(text).toMatch(/Spotlight is indexing at 73% CPU/)
  })
})

// The sample run with long titles, as a real plan has them.
const LONG = {
  ...STATUS,
  phases: STATUS.phases.map(p =>
    p.id === 'P1'
      ? { ...p, title: 'Platform interfaces for capture and recording' }
      : p.id === 'P2'
        ? { ...p, title: 'Hardening the capture pipeline for long sessions' }
        : p,
  ),
}
const LINUX = { '/proc/loadavg': '2.80 2.00 1.00 1/2 3\n', '/proc/cpuinfo': 'processor : 0\nprocessor : 1\nprocessor : 2\nprocessor : 3\n' }
const LIVE: Engine = {
  env: { ORCA_WORKTREE_ID: 'w', ORCA_CLI_BIN_DIR: '/opt/orca/bin' },
  orcaPs: {
    result: {
      worktrees: [{ repoId: 'repo-1', displayName: 'Dee with a rather long worktree name | P1-G1', agents: [{ state: 'working' }] }],
    },
  },
  files: LINUX,
  aepkit: () => ran(JSON.stringify(LONG)),
}
const at = (bodyColumns: number) => ({ ...PANE.props, bodyColumns })

describe('expandable phases', () => {
  test('the active phase opens by itself, with its full title and its chips', { options: { runDir: RUN } }, async ($, on) => {
    engine(on, LIVE)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({ ...PANE, surface, props: at(44) })
      // P0 is all APPROVED, so P1 is the active phase.
      expect(await ui.find({ type: 'Text', text: /^Platform interfaces for capture and recording$/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /^✓ T1 {2}◐ T2 {2}◌ T3 {2}● G1 Dee with a…$/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /^1\/4 approved · 37\.5%$/ })).toBeDefined()
      expect((await ui.find({ key: 'phase-P1' }))?.props.label).toBe('P1 Platform interfaces for capture and recording')
      // The others stay one row each, their titles cut.
      expect(await ui.find({ type: 'Text', text: /^▸ P0 Groundwork/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /^▸ P2 Hardening th…/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /^Hardening the capture pipeline for long sessions$/ })).toBeUndefined()
      await ui.unmount()
    }
  })

  test('a press opens a closed phase and a second press closes it', { options: { runDir: RUN } }, async ($, on) => {
    engine(on, LIVE)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal', props: at(44) })
    expect(await ui.find({ type: 'Text', text: /^✓ T1 {2}✓ G1$/ })).toBeUndefined()
    await ui.press({ key: 'phase-P0' })
    expect(await ui.find({ type: 'Text', text: /^Groundwork$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^✓ T1 {2}✓ G1$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /2\/2 approved · 100%/ })).toBeDefined()
    await ui.press({ key: 'phase-P0' })
    expect(await ui.find({ type: 'Text', text: /^✓ T1 {2}✓ G1$/ })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /^▸ P0 Groundwork/ })).toBeDefined()
    await ui.unmount()
  })

  test('the active phase, once closed, stays closed', { options: { runDir: RUN } }, async ($, on) => {
    engine(on, LIVE)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const first = await $.ui.mount({ ...PANE, surface: 'terminal', props: at(44) })
    await first.press({ key: 'phase-P1' })
    expect(await first.find({ type: 'Text', text: /^Platform interfaces for capture and recording$/ })).toBeUndefined()
    await first.unmount()

    // A new read and a new drawing keep the owner's choice.
    await $.command.run({ command: 'aeprogress', args: '', origin: { kind: 'composer' }, presentation: { isFullscreen: true, columns: 160 } })
    const again = await $.ui.mount({ ...PANE, surface: 'desktop', props: at(44) })
    expect(await again.find({ type: 'Text', text: /^Platform interfaces for capture and recording$/ })).toBeUndefined()
    expect(await again.find({ type: 'Text', text: /^▸ P1 Platform/ })).toBeDefined()
    await again.unmount()
  })

  test('each state has its glyph, and chips past two lines end with …+N', async () => {
    const glyphs = [
      chipOf('P2-T1', 'APPROVED', undefined),
      chipOf('P2-T2', 'CONDITIONAL', undefined),
      chipOf('P2-T3', 'PENDING', 'Ana'),
      chipOf('P2-T4', 'AWAITING AUDIT', undefined),
      chipOf('P2-T5', 'PENDING', undefined),
      ...['REJECTED', 'FAILED', 'BLOCKED', 'CONFLICT'].map(state => chipOf('P2-G1', state, undefined)),
    ].map(c => `${c.glyph} ${c.id}${c.who ? ` ${c.who}` : ''}`)
    expect(glyphs).toEqual(['✓ T1', '◐ T2', '● T3 Ana', '◌ T4', '○ T5', '✗ G1', '✗ G1', '✗ G1', '✗ G1'])

    const many = Array.from({ length: 14 }, (_, n) => chipOf(`P3-T${n + 1}`, 'PENDING', undefined))
    const text = chipLines(many, 26).map(line => line.map(s => s.text).join(''))
    expect(text).toEqual(['○ T1  ○ T2  ○ T3  ○ T4', '○ T5  ○ T6  ○ T7  …+7'])
    expect(chipLines(many.slice(0, 4), 26)).toHaveLength(1)
  })
})

describe('one line per row', () => {
  test('the pane fits every row at 28 to 120 columns, a phase opened', { options: { runDir: RUN } }, async ($, on) => {
    engine(on, LIVE)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    const opener = await $.ui.mount({ ...PANE, surface: 'terminal', props: at(60) })
    await opener.press({ key: 'phase-P0' })
    await opener.unmount()
    for (const surface of ['terminal', 'desktop'] as const) {
      for (const bodyColumns of [28, 30, 40, 44, 60, 120]) {
        const ui = await $.ui.mount({ ...PANE, surface, props: at(bodyColumns) })
        const tree = await ui.drawn()
        expect(overflowing(tree, bodyColumns, 1)).toEqual([])
        // Nothing is lost to the width: every phase, the live worker and the machine stay.
        for (const text of [/^43\.8%$/, /^P0$/, /^P1$/, /P2/, /P1-G1/, /P1-T3/, /P1-T2/, /Machine/, /workers 0\/2/]) {
          expect(await ui.find({ type: 'Text', text })).toBeDefined()
        }
        await ui.unmount()
      }
    }
  })
})

describe('no hover card', () => {
  test('no surface draws a card over the rows: the phase rows open instead', { options: { runDir: RUN } }, async ($, on) => {
    engine(on, LIVE)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({ ...PANE, surface, props: at(44) })
      expect(cardsOf(await ui.drawn())).toEqual([])
      await ui.unmount()
    }
  })
})
