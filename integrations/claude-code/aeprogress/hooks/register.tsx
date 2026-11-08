import { atom, read, update } from 'claude-code'
import type { EngineInterface, ProcessRunResult, Register } from 'claude-code'

import type { Kinds, Machine, Snapshot, Worker } from '../types'
import {
  dispatchIdIn,
  isDocsOnly,
  mentionsOrcaLaunch,
  orcaLaunch,
  orcaLive,
  refusals,
  specFile,
  spotlightBusy,
} from './limit'
import type { Kind, Limits, LiveWorker } from './limit'
import { readMachine } from './machine'
import {
  ATTENTION,
  bar,
  commandWorkers,
  orcaWorkers,
  overall,
  parseStatus,
  percent,
  phaseShares,
  splitCommand,
  subagentWorkers,
  taskIdsIn,
} from './progress'

const PANE = 'aeprogress'
const REFRESH_MS = 20_000
// Turn ends and subagent starts and stops come in bursts; one read covers a burst.
const MIN_GAP_MS = 2_000
const RUN_TIMEOUT_MS = 15_000
const SEARCH_DEPTH = 3
const SKIP_DIRS = new Set(['node_modules', 'venv', 'dist', 'build', 'target', '__pycache__'])
// Spotlight's indexing CPU is kept for this many reads, newest last.
const INDEXER_HISTORY = 5
const LIVE_AGENT = new Set(['pending', 'running', 'waiting'])

const snapshot = atom(
  { plugin: 'aeprogress', key: 'snapshot' } as const,
  { runDir: '', items: [], phases: [], workers: [], readAt: 0 } as Snapshot,
  { shape: 'snapshot-1' },
)
const chosenDir = atom({ plugin: 'aeprogress', key: 'chosenDir' } as const, '')
const spawned = atom({ plugin: 'aeprogress', key: 'spawned' } as const, {} as Record<string, string[]>)
const kinds = atom({ plugin: 'aeprogress', key: 'kinds' } as const, {} as Kinds, { shape: 'kinds-1' })
const projectRoot = atom({ plugin: 'aeprogress', key: 'projectRoot' } as const, '')
const spotlightToasted = atom({ plugin: 'aeprogress', key: 'spotlightToasted' } as const, false)

type Options = {
  runDir: string
  externalWorkers: string
  workersCommand: string
  aepkitCommand: string
  autoOpen: boolean
  launchLimit: boolean
  limits: Limits
  spotlightTip: boolean
  spotlightCpu: number
}

function optionsOf(raw: Readonly<Record<string, unknown>>): Options {
  const text = (key: string, fallback: string): string =>
    typeof raw[key] === 'string' ? (raw[key] as string).trim() || fallback : fallback
  const count = (key: string, fallback: number): number =>
    typeof raw[key] === 'number' && Number.isFinite(raw[key]) && (raw[key] as number) >= 0
      ? (raw[key] as number)
      : fallback
  return {
    runDir: text('runDir', ''),
    externalWorkers: text('externalWorkers', 'auto'),
    workersCommand: text('workersCommand', ''),
    aepkitCommand: text('aepkitCommand', ''),
    autoOpen: raw.autoOpen !== false,
    launchLimit: raw.launchLimit !== false,
    limits: {
      maxWorkers: count('maxWorkers', 2),
      maxBuilds: count('maxBuilds', 1),
      maxBusy: count('maxBusyPercent', 75) / 100,
    },
    spotlightTip: raw.spotlightTip !== false,
    spotlightCpu: count('spotlightCpuPercent', 50),
  }
}

function join(dir: string, name: string): string {
  return dir === '' || dir === '.' ? name : `${dir.replace(/[\\/]+$/, '')}/${name}`
}

function baseName(dir: string): string {
  return dir.replace(/[\\/]+$/, '').split(/[\\/]/).pop() || dir
}

/** The newest compliance-log.md under the working directory, a few levels down. */
async function findRun($: EngineInterface): Promise<string> {
  let best = { dir: '', mtime: -1 }
  let level = ['.']
  for (let depth = 0; depth <= SEARCH_DEPTH && level.length > 0; depth++) {
    const next: string[] = []
    for (const dir of level) {
      const entries = await $.fs.list(dir).catch(() => [])
      for (const entry of entries) {
        if (entry.kind === 'file' && entry.name === 'compliance-log.md' && entry.mtimeMs > best.mtime) {
          best = { dir, mtime: entry.mtimeMs }
        } else if (entry.kind === 'dir' && !entry.name.startsWith('.') && !SKIP_DIRS.has(entry.name)) {
          next.push(join(dir, entry.name))
        }
      }
    }
    level = next
  }
  return best.dir
}

async function resolveRun($: EngineInterface, options: Options): Promise<string> {
  const chosen = await read($, chosenDir)
  if (chosen) return chosen
  if (options.runDir) return options.runDir
  return findRun($)
}

// Module state: what a reload starts over with and works out again.
let options: Options = optionsOf({})
let aepkit: string[] | undefined
let orcaRepo: { dir: string; repoId: string | undefined } | undefined
let reading: Promise<void> | undefined
let lastRead = 0

async function runAepkit($: EngineInterface, dir: string) {
  const home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? ''
  // pipx puts aepkit in ~/.local/bin on every system; Windows names Python `python` or `py`.
  const candidates = aepkit
    ? [aepkit]
    : options.aepkitCommand
      ? [splitCommand(options.aepkitCommand)]
      : [
          ['aepkit'],
          [`${home}/.local/bin/aepkit`],
          ['python3', '-m', 'aepkit'],
          ['python', '-m', 'aepkit'],
          ['py', '-m', 'aepkit'],
        ]
  let tooOld: ProcessRunResult | undefined
  for (const argv of candidates) {
    const ran = await $.process
      .run([...argv, 'status', '--json', dir], { timeoutMs: RUN_TIMEOUT_MS })
      .catch(() => undefined)
    // `python3 -m aepkit` without aepkit installed exits 1 with "No module named".
    if (!ran || /No module named/.test(ran.stderr)) continue
    // An aepkit older than 0.7.0: a newer one may still be reachable the next way.
    if (/unrecognized arguments: --json/.test(ran.stderr)) {
      tooOld ??= ran
      continue
    }
    aepkit = argv
    return ran
  }
  return tooOld
}

async function orcaBinary($: EngineInterface): Promise<string | undefined> {
  const binDir = await $.env.get('ORCA_CLI_BIN_DIR')
  if (binDir) return `${binDir.replace(/[\\/]+$/, '')}/orca`
  if (options.externalWorkers === 'orca') return 'orca'
  // auto: only inside an Orca terminal, so no session spawns a binary it lacks.
  return (await $.env.get('ORCA_WORKTREE_ID')) ? 'orca' : undefined
}

async function externalWorkers($: EngineInterface, dir: string, known: Set<string>): Promise<Worker[]> {
  const mode = options.externalWorkers
  if (mode === 'off') return []
  if (mode === 'command' || (mode === 'auto' && options.workersCommand)) {
    const argv = splitCommand(options.workersCommand)
    if (argv.length === 0) return []
    const ran = await $.process.run(argv, { cwd: dir, timeoutMs: RUN_TIMEOUT_MS }).catch(() => undefined)
    return ran && ran.exitCode === 0 ? commandWorkers(ran.stdout, known) : []
  }
  const orca = await orcaBinary($)
  if (!orca) return []
  if (orcaRepo?.dir !== dir) {
    const current = await $.process
      .run([orca, 'worktree', 'current', '--json'], { cwd: dir, timeoutMs: RUN_TIMEOUT_MS })
      .catch(() => undefined)
    let repoId: string | undefined
    try {
      repoId = current?.exitCode === 0 ? JSON.parse(current.stdout).result?.worktree?.repoId : undefined
    } catch {
      repoId = undefined
    }
    orcaRepo = { dir, repoId }
  }
  const ps = await $.process
    .run([orca, 'worktree', 'ps', '--json'], { cwd: dir, timeoutMs: RUN_TIMEOUT_MS })
    .catch(() => undefined)
  if (!ps || ps.exitCode !== 0) return []
  try {
    return orcaWorkers(ps.stdout, orcaRepo.repoId, known)
  } catch {
    return []
  }
}

/** The machine's load and Spotlight's history into the snapshot, and the tip once. */
async function readLoad($: EngineInterface, dir: string): Promise<void> {
  const machine = await readMachine($)
  await update($, snapshot, old => ({
    ...old,
    machine,
    indexerHistory: machine?.os === 'macos' ? [...(old.indexerHistory ?? []), machine.indexerCpu].slice(-INDEXER_HISTORY) : [],
  }))
  const snap = await read($, snapshot)
  if (!options.spotlightTip || !spotlightBusy(snap.indexerHistory ?? [], options.spotlightCpu)) return
  await rootOf($, dir)
  if (!(await read($, spotlightToasted))) {
    await update($, spotlightToasted, () => true)
    $.ui.toast(`Spotlight keeps indexing (${Math.round(machine?.indexerCpu ?? 0)}% CPU). See the progress pane.`)
  }
}

/** The repository root of the run folder, or the session's folder outside git. */
async function rootOf($: EngineInterface, dir: string): Promise<string> {
  const known = await read($, projectRoot)
  if (known) return known
  const git = await $.process
    .run(['git', 'rev-parse', '--show-toplevel'], { cwd: dir || '.', timeoutMs: RUN_TIMEOUT_MS })
    .catch(() => undefined)
  const root = git?.exitCode === 0 && git.stdout.trim() ? git.stdout.trim() : await $.session.cwd()
  await update($, projectRoot, () => root)
  return root
}

function spotlightAdvice(machine: Machine | undefined, root: string): string {
  return (
    `Spotlight is indexing at ${Math.round(machine?.indexerCpu ?? 0)}% CPU. If it is indexing build ` +
    `output, exclude ${root || 'the project folder'} in System Settings > Spotlight > Search Privacy ` +
    '(Spotlight > Privacy on older macOS).'
  )
}

async function readRun($: EngineInterface): Promise<void> {
  const readAt = await $.clock.now()
  const dir = await resolveRun($, options)
  if (dir !== (await read($, snapshot)).runDir) await update($, projectRoot, () => '')
  await readLoad($, dir)
  const fail = async (error: string): Promise<void> => {
    await update($, snapshot, old => ({ ...old, runDir: dir, readAt, error }))
  }
  if (!dir) {
    return fail(
      'No compliance-log.md under this folder. Name the run folder with /aeprogress <folder>, ' +
        'or set "Run folder" in /config.',
    )
  }
  const ran = await runAepkit($, dir)
  if (!ran) {
    return fail(
      'aepkit is not installed where Claude Code can run it. Install it with ' +
        '`pipx install aepkit`, or set "aepkit command" in /config to its full path.',
    )
  }
  if (ran.exitCode !== 0) {
    const old = /unrecognized arguments: --json/.test(ran.stderr)
    return fail(
      old
        ? 'This aepkit has no `status --json`. Upgrade it to 0.7.0 or newer: `pipx upgrade aepkit`.'
        : ran.stderr.trim().split('\n').pop() || `aepkit exited with ${ran.exitCode}`,
    )
  }
  let parsed
  try {
    parsed = parseStatus(ran.stdout)
  } catch (err) {
    return fail(String(err))
  }
  const known = new Set(parsed.items.map(i => i.id.toUpperCase()))
  const agents = await $.agent.list().catch(() => [])
  const workers = [
    ...subagentWorkers(agents, await read($, spawned), known),
    ...(await externalWorkers($, dir, known)),
  ]
  const executors = options.launchLimit ? await liveExecutors($).catch(() => []) : []
  const launches = { live: executors.length, builds: executors.filter(w => w.kind === 'build').length }
  await update($, snapshot, old => ({ ...old, runDir: dir, ...parsed, workers, readAt, launches, error: undefined }))
}

/** Live Orca workers, by dispatch id; throws when Orca cannot be asked. */
async function orcaLiveIds($: EngineInterface): Promise<string[]> {
  const orca = (await orcaBinary($)) ?? 'orca'
  const ran = await $.process.run([orca, 'orchestration', 'worker-list', '--json'], { timeoutMs: RUN_TIMEOUT_MS })
  if (ran.exitCode !== 0) throw new Error(ran.stderr.trim() || `orca exited with ${ran.exitCode}`)
  return orcaLive(ran.stdout)
}

/**
 * The Executors live now: subagents whose spawn prompt named a task, and Orca workers.
 * `orcaIds` is the Orca count when the caller has it; otherwise Orca is asked only
 * inside an Orca terminal, and a failure there counts no Orca workers.
 */
async function liveExecutors($: EngineInterface, orcaIds?: readonly string[]): Promise<LiveWorker[]> {
  const known = await read($, kinds)
  const executors = await read($, spawned)
  const agents = await $.agent.list()
  const live: LiveWorker[] = agents
    .filter(a => LIVE_AGENT.has(a.status) && a.id in executors)
    .map(a => ({ id: a.id, kind: known[a.id] ?? 'build' }))
  let orca = orcaIds
  if (!orca && (await orcaBinary($))) orca = await orcaLiveIds($).catch(() => [])
  for (const id of orca ?? []) live.push({ id, kind: known[id] ?? 'build' })
  return live
}

async function remember($: EngineInterface, id: string, kind: Kind, live: readonly LiveWorker[]): Promise<void> {
  const keep = new Set([id, ...live.map(w => w.id)])
  await update($, kinds, old => ({
    ...Object.fromEntries(Object.entries(old).filter(([k]) => keep.has(k))),
    [id]: kind,
  }))
}

/** The refusal a held-back launch answers with, or undefined when it may go. */
async function judgeLaunch($: EngineInterface, kind: Kind, live: readonly LiveWorker[]): Promise<string | undefined> {
  const machine = await readMachine($)
  const reasons = refusals(kind, live, machine, options.limits)
  if (reasons.length === 0) return undefined
  let advice = ''
  if (options.spotlightTip && machine?.os === 'macos' && machine.indexerCpu >= options.spotlightCpu) {
    advice = ` ${spotlightAdvice(machine, await rootOf($, (await read($, snapshot)).runDir))}`
  }
  $.ui.toast('aeprogress held back a worker launch: see why in the transcript')
  return (
    `aeprogress launch limit: this worker is not launched because ${reasons.join('; ')}. ` +
    `Wait for a worker to finish or for the load to drop, or change the limits in /config.${advice}`
  )
}

/** Whether the session has a run, so the launch limit applies. */
async function runActive($: EngineInterface): Promise<boolean> {
  return options.launchLimit && (await read($, snapshot)).runDir !== ''
}

async function refresh($: EngineInterface, force = false): Promise<void> {
  const now = await $.clock.now()
  if (reading) return reading
  if (!force && now - lastRead < MIN_GAP_MS) return
  lastRead = now
  reading = readRun($)
    .catch(async err => {
      await update($, snapshot, old => ({ ...old, readAt: now, error: String(err) }))
    })
    .finally(() => {
      reading = undefined
    })
  return reading
}

async function isOpen($: EngineInterface): Promise<boolean> {
  const panes = await $.ui.panes().catch(() => [])
  return panes.some(p => p.id === PANE)
}

async function open($: EngineInterface): Promise<void> {
  const snap = await read($, snapshot)
  const title = snap.runDir ? `AEP progress · ${baseName(snap.runDir)}` : 'AEP progress'
  await $.ui.open({ id: PANE, title })
}

export const register: Register = (on, rawOptions) => {
  options = optionsOf(rawOptions)

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'aeprogress',
      description: 'Open the Auditor/Executor progress pane (optional: the run folder)',
      argumentHint: '[run folder]',
    })
    await refresh($, true)
    // Read again on a timer only while the pane is open: a closed pane costs nothing.
    $.clock.every(REFRESH_MS, async () => {
      if (await isOpen($)) await refresh($, true)
    })
    const snap = await read($, snapshot)
    if (options.autoOpen && snap.runDir && !snap.error && e.isInteractive) void open($)
    return next(e)
  })

  on('command.run', { command: 'aeprogress' }, async ($, e) => {
    const dir = e.args.trim()
    if (dir) {
      if (!(await $.fs.exists(join(dir, 'compliance-log.md')))) {
        return { text: `No compliance-log.md in ${dir}.` }
      }
      await update($, chosenDir, () => dir)
    }
    await refresh($, true)
    await open($)
    const snap = await read($, snapshot)
    if (snap.error) return { text: `Progress pane opened: ${snap.error}` }
    const whole = percent(overall(phaseShares(snap.phases, snap.items)))
    const approved = snap.items.filter(i => i.state === 'APPROVED').length
    return { text: `${whole} of ${snap.runDir}: ${approved}/${snap.items.length} approved. Progress pane opened.` }
  })

  // A subagent's spawn prompt names the task it executes: that makes it an Executor, which
  // the launch limit holds back past the limits. Any other subagent goes untouched.
  on('agent.spawn', async ($, e, next) => {
    const ids = taskIdsIn(`${e.description} ${e.prompt}`)
    const snap = await read($, snapshot)
    const runIds = new Set(snap.items.map(i => i.id.toUpperCase()))
    const isExecutor = ids.some(id => runIds.size === 0 || runIds.has(id)) && !e.workflow
    const kind: Kind = isDocsOnly(e.prompt) ? 'docs' : 'build'
    let live: LiveWorker[] = []
    if (isExecutor && (await runActive($))) {
      live = await liveExecutors($)
      const refusal = await judgeLaunch($, kind, live)
      if (refusal) return { deny: refusal }
    }
    const result = await next(e)
    if ('agentId' in result && result.agentId && ids.length > 0) {
      const agentId = result.agentId
      await update($, spawned, old => ({ ...old, [agentId]: ids }))
      if (isExecutor) await remember($, agentId, kind, live)
    }
    void refresh($)
    return result
  }).catch(($, e, next) =>
    next.called
      ? next(e)
      : { deny: 'aeprogress launch limit: the live workers could not be counted, so this Executor is not launched.' },
  )

  // Orca: a worker-start, or a send that reopens a worker, goes through the same limit.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (!mentionsOrcaLaunch(e.command) || !(await runActive($))) return next(e)
    const orcaIds = await orcaLiveIds($)
    if (!orcaLaunch(e.command, new Set(orcaIds))) return next(e)
    const spec = specFile(e.command)
    const specText = spec ? ((await $.fs.read(spec).catch(() => '')) as string) : ''
    const kind: Kind = isDocsOnly(e.command) || isDocsOnly(specText) ? 'docs' : 'build'
    const live = await liveExecutors($, orcaIds)
    const refusal = await judgeLaunch($, kind, live)
    if (refusal) return { deny: refusal }
    const ran = await next(e)
    const dispatch = dispatchIdIn(JSON.stringify(ran.result ?? ''))
    if (dispatch) await remember($, dispatch, kind, live)
    void refresh($)
    return ran
  }).catch(($, e, next) =>
    next.called
      ? next(e)
      : {
          deny:
            'aeprogress launch limit: the live Orca workers could not be counted (orca orchestration ' +
            'worker-list failed), so this worker is not launched. Turn "Launch limit" off in /config ' +
            'to launch without it.',
        },
  )

  on('classic.SubagentStop', async ($, e, next) => {
    const result = await next(e)
    void refresh($)
    return result
  }).catch(($, e, next) => next(e))

  // A verdict or a report lands when the log is edited, so read it again after a turn.
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (await isOpen($)) void refresh($)
    return result
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const snap = await read($, snapshot)
    const cols = e.props.bodyColumns ?? e.viewport?.columns ?? 60
    const barWidth = Math.max(10, Math.min(40, cols - 22))

    const shares = phaseShares(snap.phases, snap.items)
    const whole = overall(shares)
    const weighted = snap.phases.some(p => p.weight !== 1)
    const byId = new Map(snap.items.map(i => [i.id.toUpperCase(), i]))
    const working = new Set(snap.workers.map(w => w.taskId))
    const awaiting = snap.items.filter(i => i.state === 'AWAITING AUDIT' && !working.has(i.id.toUpperCase()))
    const attention = snap.items.filter(i => ATTENTION.has(i.state))
    const time = snap.readAt ? new Date(snap.readAt).toTimeString().slice(0, 5) : '--:--'
    const sourceLabel = { subagent: 'subagent', orca: 'Orca', command: 'worker' } as const
    const m = snap.machine
    const limitOn = options.launchLimit && snap.runDir !== ''
    const liveCount = snap.launches?.live ?? 0
    const buildCount = snap.launches?.builds ?? 0
    const tip =
      options.spotlightTip && spotlightBusy(snap.indexerHistory ?? [], options.spotlightCpu)
        ? spotlightAdvice(m, await read($, projectRoot))
        : undefined

    if (snap.phases.length === 0) {
      return (
        <Box flexDirection="column" paddingX={1}>
          <Text weight="bold">Auditor/Executor progress</Text>
          <Text dimColor>{snap.error ?? 'The run has no phases or tasks yet.'}</Text>
        </Box>
      )
    }

    return (
      <Box flexDirection="column" paddingX={1}>
        <Text weight="bold" size="title">
          {percent(whole)}
        </Text>
        <Text color="claude">{bar(whole, barWidth + 10)}</Text>
        <Text dimColor>
          {snap.phases.length} {snap.phases.length === 1 ? 'phase' : 'phases'} · {weighted ? 'weighted by the plan' : 'equal weights'} · only
          APPROVED closes
        </Text>
        <Text> </Text>
        {shares.map(p => (
          <Box flexDirection="column">
            <Text>
              <Text weight="bold">{p.id}</Text> {p.title || 'untitled'}
            </Text>
            <Text color={p.fraction >= 1 ? 'success' : p.total === 0 ? 'inactive' : 'claude'}>
              {bar(p.fraction, barWidth)}{' '}
              <Text dimColor>
                {p.total === 0 ? 'not broken down' : `${p.approved}/${p.total} · ${percent(p.fraction)}`}
              </Text>
            </Text>
          </Box>
        ))}
        <Text> </Text>
        {snap.workers.length > 0 && <Text weight="bold">In progress</Text>}
        {snap.workers.map(w => (
          <Text>
            <Text color="warning">●</Text> {w.taskId} · {w.who} <Text dimColor>({sourceLabel[w.source]})</Text>
          </Text>
        ))}
        {awaiting.length > 0 && <Text weight="bold">Awaiting audit</Text>}
        {awaiting.map(i => (
          <Text>
            <Text color="suggestion">●</Text> {i.id}
            {i.executor ? ` · ${i.executor}` : ''}
          </Text>
        ))}
        {attention.length > 0 && <Text weight="bold">Needs attention</Text>}
        {attention.map(i => (
          <Text>
            <Text color="error">●</Text> {i.id} · {i.state}
            {i.executor ? ` · ${i.executor}` : ''}
          </Text>
        ))}
        {m && (
          <Text>
            <Text color={m.busy > options.limits.maxBusy ? 'error' : m.busy > 0.4 ? 'warning' : 'success'}>●</Text>{' '}
            Machine {Math.round(m.busy * 100)}% busy <Text dimColor>({m.detail})</Text>
          </Text>
        )}
        {!m && <Text dimColor>Machine load unknown on this system</Text>}
        {limitOn && (
          <Text dimColor>
            Launch limit: {liveCount}/{options.limits.maxWorkers} workers · {buildCount}/{options.limits.maxBuilds}{' '}
            building · builds held above {Math.round(options.limits.maxBusy * 100)}%
          </Text>
        )}
        {tip && <Text color="warning">{tip}</Text>}
        <Text dimColor>
          {snap.error
            ? `Last read failed: ${snap.error}`
            : `Read from ${baseName(snap.runDir)}/compliance-log.md at ${time}`}
        </Text>
        {byId.size === 0 && <Text dimColor>No tasks in the log yet.</Text>}
      </Box>
    )
  })
}
