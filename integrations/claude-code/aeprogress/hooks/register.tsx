import { atom, read, update } from 'claude-code'
import type { EngineInterface, ProcessRunResult, Register } from 'claude-code'

import type { Snapshot, Worker } from '../types'
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

const snapshot = atom(
  { plugin: 'aeprogress', key: 'snapshot' } as const,
  { runDir: '', items: [], phases: [], workers: [], readAt: 0 } as Snapshot,
  { shape: 'snapshot-1' },
)
const chosenDir = atom({ plugin: 'aeprogress', key: 'chosenDir' } as const, '')
const spawned = atom({ plugin: 'aeprogress', key: 'spawned' } as const, {} as Record<string, string[]>)

type Options = {
  runDir: string
  externalWorkers: string
  workersCommand: string
  aepkitCommand: string
  autoOpen: boolean
}

function optionsOf(raw: Readonly<Record<string, unknown>>): Options {
  const text = (key: string, fallback: string): string =>
    typeof raw[key] === 'string' ? (raw[key] as string).trim() || fallback : fallback
  return {
    runDir: text('runDir', ''),
    externalWorkers: text('externalWorkers', 'auto'),
    workersCommand: text('workersCommand', ''),
    aepkitCommand: text('aepkitCommand', ''),
    autoOpen: raw.autoOpen !== false,
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
  const home = (await $.env.get('HOME')) ?? ''
  const candidates = aepkit
    ? [aepkit]
    : options.aepkitCommand
      ? [splitCommand(options.aepkitCommand)]
      : [['aepkit'], [`${home}/.local/bin/aepkit`], ['python3', '-m', 'aepkit']]
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
  if (binDir) return `${binDir}/orca`
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

async function readRun($: EngineInterface): Promise<void> {
  const readAt = await $.clock.now()
  const dir = await resolveRun($, options)
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
  await update($, snapshot, () => ({ runDir: dir, ...parsed, workers, readAt }))
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

  // A subagent's spawn prompt names the task it executes; keep the ID by agent id.
  on('agent.spawn', async ($, e, next) => {
    const result = await next(e)
    const ids = taskIdsIn(`${e.description} ${e.prompt}`)
    if ('agentId' in result && result.agentId && ids.length > 0) {
      const agentId = result.agentId
      await update($, spawned, old => ({ ...old, [agentId]: ids }))
    }
    void refresh($)
    return result
  }).catch(($, e, next) => next(e))

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
