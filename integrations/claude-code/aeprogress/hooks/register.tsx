import { atom, read, update } from 'claude-code'
import type { EngineInterface, ProcessRunResult, Register } from 'claude-code'

import type { Kinds, Machine, PendingCompaction, Snapshot, UpdateInfo, Worker } from '../types'
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
import { linuxMachine, numbers, sysctlMachine, windowsMachine } from './machine'
import { catalogEntryVersion, howToUpdate, installKind, isNewer, marketplaceDir } from './update'
import type { UpdateMode } from './update'
import {
  bandLayout,
  barParts,
  chipLines,
  chipOf,
  cells,
  cut,
  footerRows,
  header,
  listRow,
  paneWidth,
  phaseBarLine,
  phaseRows,
  readLine,
  weighingLine,
} from './layout'
import type { PhaseInput, Seg } from './layout'
import {
  ATTENTION,
  commandWorkers,
  orcaWorkers,
  overall,
  parseStatus,
  percent,
  phaseShares,
  subagentWorkers,
  taskIdsIn,
} from './progress'

const PANE = 'aeprogress'
// The pane's side padding, in cells on each side.
const PAD = 1
const REFRESH_MS = 20_000
// Turn ends and subagent starts and stops come in bursts; one read covers a burst.
const MIN_GAP_MS = 2_000
const SEARCH_DEPTH = 3
const SKIP_DIRS = new Set(['node_modules', 'venv', 'dist', 'build', 'target', '__pycache__'])
// Spotlight's indexing CPU is kept for this many reads, newest last.
const INDEXER_HISTORY = 5
const LIVE_AGENT = new Set(['pending', 'running', 'waiting'])

const snapshot = atom(
  { plugin: 'auditor-executor-protocol', key: 'snapshot' } as const,
  { runDir: '', items: [], phases: [], workers: [], readAt: 0 } as Snapshot,
  { shape: 'snapshot-1' },
)
// The owner's own toggles of the pane's phases, written only by a press; a phase with
// none is open while it is the active one.
const phaseToggles = atom({ plugin: 'auditor-executor-protocol', key: 'phaseToggles' } as const, {} as Record<string, boolean>, {
  shape: 'phase-toggles-1',
})
const chosenDir = atom({ plugin: 'auditor-executor-protocol', key: 'chosenDir' } as const, '')
const closedByOwner = atom({ plugin: 'auditor-executor-protocol', key: 'closedByOwner' } as const, false)
const spawned = atom({ plugin: 'auditor-executor-protocol', key: 'spawned' } as const, {} as Record<string, string[]>)
const kinds = atom({ plugin: 'auditor-executor-protocol', key: 'kinds' } as const, {} as Kinds, { shape: 'kinds-1' })
const projectRoot = atom({ plugin: 'auditor-executor-protocol', key: 'projectRoot' } as const, '')
const spotlightToasted = atom({ plugin: 'auditor-executor-protocol', key: 'spotlightToasted' } as const, false)

type Options = {
  runDir: string
  externalWorkers: string
  workersFile: string
  autoOpen: boolean
  launchLimit: boolean
  limits: Limits
  spotlightTip: boolean
  spotlightCpu: number
  compactOnClose: boolean
  compactSeconds: number
  updateCheck: UpdateMode
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
    workersFile: text('workersFile', ''),
    autoOpen: raw.autoOpen !== false,
    launchLimit: raw.launchLimit !== false,
    limits: {
      maxWorkers: count('maxWorkers', 2),
      maxBuilds: count('maxBuilds', 1),
      maxBusy: count('maxBusyPercent', 75) / 100,
    },
    spotlightTip: raw.spotlightTip !== false,
    spotlightCpu: count('spotlightCpuPercent', 50),
    compactOnClose: raw.compactOnClose !== false,
    compactSeconds: Math.max(1, Math.round(count('compactCountdownSeconds', 40))),
    updateCheck: raw.updateCheck === 'off' ? 'off' : 'on',
  }
}

function join(dir: string, name: string): string {
  return dir === '' || dir === '.' ? name : `${dir.replace(/[\\/]+$/, '')}/${name}`
}

function isAbsolute(path: string): boolean {
  return /^(?:[\\/]|[A-Za-z]:[\\/])/.test(path)
}

/**
 * A path the owner gave, made absolute against `base`. The session's own folder moves with
 * every shell `cd`, so a relative path never goes through it.
 */
export function anchored(base: string, path: string): string {
  return path === '' || isAbsolute(path) ? path : join(base, path)
}

/** A run folder as the owner sees it: relative to the project root when it lies beneath it. */
export function shown(root: string, dir: string): string {
  const base = root.replace(/[\\/]+$/, '')
  return base && (dir.startsWith(`${base}/`) || dir.startsWith(`${base}\\`)) ? dir.slice(base.length + 1) : dir
}

function baseName(dir: string): string {
  return dir.replace(/[\\/]+$/, '').split(/[\\/]/).pop() || dir
}

/** The newest compliance-log.md under the project root, a few levels down, as an absolute path. */
async function findRun($: EngineInterface, root: string): Promise<string> {
  let best = { dir: '', mtime: -1 }
  let level = [root]
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

/** The run folder, absolute: the one /aeprogress named, the option, or the newest found. */
async function resolveRun($: EngineInterface, options: Options): Promise<string> {
  const root = await $.session.root()
  const chosen = await read($, chosenDir)
  if (chosen) return anchored(root, chosen)
  if (options.runDir) return anchored(root, options.runDir)
  return findRun($, root)
}

// Module state: what a reload starts over with and works out again.
let options: Options = optionsOf({})
let aepkitWay: number | undefined
let orcaRepo: { dir: string; repoId: string | undefined } | undefined
let reading: Promise<void> | undefined
let lastRead = 0
let interactive = true

/**
 * `aepkit status --json` for the run folder, run from that folder with fixed arguments.
 * pipx puts aepkit on the PATH; Windows names Python `python` or `py`. The way that worked
 * is kept for the session.
 */
async function aepkitStatus($: EngineInterface, way: number, dir: string): Promise<ProcessRunResult | Error> {
  const failed = (err: unknown) => (err instanceof Error ? err : new Error(String(err)))
  if (way === 0) return $.process.run(['aepkit', 'status', '--json', '.'], { cwd: dir, timeoutMs: 15_000 }).catch(failed)
  if (way === 1) return $.process.run(['python3', '-m', 'aepkit', 'status', '--json', '.'], { cwd: dir, timeoutMs: 15_000 }).catch(failed)
  if (way === 2) return $.process.run(['python', '-m', 'aepkit', 'status', '--json', '.'], { cwd: dir, timeoutMs: 15_000 }).catch(failed)
  return $.process.run(['py', '-m', 'aepkit', 'status', '--json', '.'], { cwd: dir, timeoutMs: 15_000 }).catch(failed)
}

/** What became of the first way tried, when no way ran aepkit: why it could not start. */
let aepkitFailure = ''

async function runAepkit($: EngineInterface, dir: string) {
  const ways = aepkitWay !== undefined ? [aepkitWay] : [0, 1, 2, 3]
  let tooOld: ProcessRunResult | undefined
  aepkitFailure = ''
  for (const way of ways) {
    const ran = await aepkitStatus($, way, dir)
    if (ran instanceof Error) {
      aepkitFailure ||= ran.message
      continue
    }
    // `python3 -m aepkit` without aepkit installed exits 1 with "No module named".
    if (/No module named/.test(ran.stderr)) continue
    // An aepkit older than 0.7.0: a newer one may still be reachable the next way.
    if (/unrecognized arguments: --json/.test(ran.stderr)) {
      tooOld ??= ran
      continue
    }
    aepkitWay = way
    return ran
  }
  return tooOld
}

/** Whether to ask Orca: always with External workers on `orca`; on `auto`, inside an Orca terminal. */
async function usesOrca($: EngineInterface): Promise<boolean> {
  if (options.externalWorkers === 'orca') return true
  return options.externalWorkers === 'auto' && Boolean(await $.env.get('ORCA_WORKTREE_ID'))
}

async function externalWorkers($: EngineInterface, dir: string, known: Set<string>): Promise<Worker[]> {
  const mode = options.externalWorkers
  if (mode === 'off') return []
  if (mode === 'file' || (mode === 'auto' && options.workersFile)) {
    if (!options.workersFile) return []
    const text = await $.fs.read(anchored(dir, options.workersFile)).catch(() => undefined)
    return typeof text === 'string' ? commandWorkers(text, known) : []
  }
  if (!(await usesOrca($))) return []
  if (orcaRepo?.dir !== dir) {
    const current = await $.process.run(['orca', 'worktree', 'current', '--json'], { cwd: dir, timeoutMs: 15_000 }).catch(() => undefined)
    let repoId: string | undefined
    try {
      repoId = current?.exitCode === 0 ? JSON.parse(current.stdout).result?.worktree?.repoId : undefined
    } catch {
      repoId = undefined
    }
    orcaRepo = { dir, repoId }
  }
  const ps = await $.process.run(['orca', 'worktree', 'ps', '--json'], { cwd: dir, timeoutMs: 15_000 }).catch(() => undefined)
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
  const git = await $.process.run(['git', 'rev-parse', '--show-toplevel'], { cwd: dir || '.', timeoutMs: 15_000 }).catch(() => undefined)
  const root = git?.exitCode === 0 && git.stdout.trim() ? git.stdout.trim() : await $.session.root()
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
      'No compliance-log.md under the project root. Name the run folder with /aeprogress <folder>, ' +
        'or set "Run folder" in /config.',
    )
  }
  // Checked before aepkit runs: a missing folder would fail the start like a missing program.
  if (!(await $.fs.exists(join(dir, 'compliance-log.md')))) {
    return fail(`No compliance-log.md in ${dir}. Check "Run folder" in /config, or name the folder with /aeprogress <folder>.`)
  }
  const ran = await runAepkit($, dir)
  if (!ran) {
    const reason = aepkitFailure ? ` (${aepkitFailure})` : ''
    return fail(
      `Claude Code could not run aepkit${reason}. Install it with \`pipx install aepkit\`; if it is ` +
        'installed, its folder must be on the PATH Claude Code started with.',
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
  const ran = await $.process.run(['orca', 'orchestration', 'worker-list', '--json'], { timeoutMs: 15_000 })
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
  // An Executor is a live subagent recorded at its launch, or one whose description or name
  // names a task of the run (a foreground subagent reports its id only when it ends).
  const runIds = new Set((await read($, snapshot)).items.map(i => i.id.toUpperCase()))
  const namesTask = (text: string) => taskIdsIn(text).some(id => runIds.size === 0 || runIds.has(id))
  const live: LiveWorker[] = agents
    .filter(a => LIVE_AGENT.has(a.status) && (a.id in executors || namesTask(`${a.description} ${a.name ?? ''}`)))
    .map(a => ({ id: a.id, kind: known[a.id] ?? 'build' }))
  let orca = orcaIds
  if (!orca && (await usesOrca($))) orca = await orcaLiveIds($).catch(() => [])
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


// ---- Machine load ----

/** The machine's load now, or undefined when no source answers. Never throws. */
async function readMachine($: EngineInterface): Promise<Machine | undefined> {
  try {
    if (await $.fs.exists('/proc/loadavg')) {
      const loadavg = (await $.fs.read('/proc/loadavg')) as string
      const cpuinfo = ((await $.fs.read('/proc/cpuinfo').catch(() => '')) as string) || ''
      const fromProc = linuxMachine(loadavg, cpuinfo)
      if (fromProc) return fromProc
      // A /proc/cpuinfo without "processor" lines (some ARM boards): ask nproc.
      const nproc = await $.process.run(['nproc'], { timeoutMs: 3_000 }).catch(() => undefined)
      const cores = nproc?.exitCode === 0 ? (numbers(nproc.stdout)[0] ?? 0) : 0
      return cores > 0 ? linuxMachine(loadavg, 'processor :\n'.repeat(cores)) : undefined
    }
    if (await $.fs.exists('/usr/sbin/sysctl')) {
      const isMac = await $.fs.exists('/System/Library/CoreServices')
      const loadavg = await $.process.run(['/usr/sbin/sysctl', '-n', 'vm.loadavg'], { timeoutMs: 3_000 }).catch(() => undefined)
      const ncpu = await $.process.run(['/usr/sbin/sysctl', '-n', 'hw.ncpu'], { timeoutMs: 3_000 }).catch(() => undefined)
      // Spotlight only exists on macOS; nowhere else is ps run for it.
      const ps = isMac ? await $.process.run(['/bin/ps', '-A', '-o', '%cpu=,comm='], { timeoutMs: 3_000 }).catch(() => undefined) : undefined
      return sysctlMachine(loadavg?.stdout ?? '', ncpu?.stdout ?? '', isMac ? 'macos' : 'bsd', ps?.stdout ?? '')
    }
    if (await $.fs.exists('/sbin/sysctl')) {
      const loadavg = await $.process.run(['/sbin/sysctl', '-n', 'vm.loadavg'], { timeoutMs: 3_000 }).catch(() => undefined)
      const ncpu = await $.process.run(['/sbin/sysctl', '-n', 'hw.ncpu'], { timeoutMs: 3_000 }).catch(() => undefined)
      return sysctlMachine(loadavg?.stdout ?? '', ncpu?.stdout ?? '', 'bsd')
    }
    if ((await $.env.get('SystemRoot')) || (await $.env.get('WINDIR'))) {
      const out = await $.process.run(['typeperf', '\\Processor(_Total)\\% Processor Time', '-sc', '1'], { timeoutMs: 8_000 }).catch(() => undefined)
      return out?.exitCode === 0 ? windowsMachine(out.stdout) : undefined
    }
  } catch {
    // Falls through: the load is unknown.
  }
  return undefined
}

// ---- Compacting when a phase closes ----

const TOOL = 'compact_and_resume'

const pending = atom(
  { plugin: 'auditor-executor-protocol', key: 'pendingCompaction' } as const,
  null as PendingCompaction | null,
  { shape: 'pending-1' },
)
const secondsLeft = atom({ plugin: 'auditor-executor-protocol', key: 'compactSecondsLeft' } as const, 0)

// Module state: a reload drops the timer, and `resumeCountdown` arms it again.
let ticker: { cancel: () => void } | undefined
let firing = false

/** The scheduled compaction, if any. */
async function pendingJob($: EngineInterface): Promise<PendingCompaction | null> {
  return read($, pending)
}

/** Seconds left in a running countdown, read while drawing the band. */
async function countdownLeft($: EngineInterface): Promise<number> {
  return read($, secondsLeft)
}

function stopTicker(): void {
  ticker?.cancel()
  ticker = undefined
}

/** Keeps what to compact for and how to resume; the countdown waits for the turn's end. */
async function schedule($: EngineInterface, resume: string, instructions?: string): Promise<void> {
  stopTicker()
  await update($, pending, () => ({ resume, ...(instructions ? { instructions } : {}), deadline: null }))
}

/** Drops a scheduled or running countdown: nothing is compacted or resumed. */
async function cancel($: EngineInterface): Promise<void> {
  stopTicker()
  await update($, pending, () => null)
  await update($, secondsLeft, () => 0)
}

async function tick($: EngineInterface): Promise<void> {
  const job = await read($, pending)
  if (!job || job.deadline === null) return stopTicker()
  const left = Math.max(0, Math.ceil((job.deadline - (await $.clock.now())) / 1000))
  await update($, secondsLeft, () => left)
  if (left === 0) await compactNow($)
}

function arm($: EngineInterface): void {
  stopTicker()
  ticker = $.clock.every(1000, () => tick($))
}

/** Starts the countdown of a scheduled compaction, once the Auditor's turn has ended. */
async function startCountdown($: EngineInterface, seconds: number): Promise<void> {
  const job = await read($, pending)
  if (!job || job.deadline !== null) return
  const deadline = (await $.clock.now()) + seconds * 1000
  await update($, pending, old => (old ? { ...old, deadline } : old))
  await update($, secondsLeft, () => seconds)
  arm($)
}

/** After a reload: a countdown that was running keeps running toward the same deadline. */
async function resumeCountdown($: EngineInterface): Promise<void> {
  const job = await read($, pending)
  if (job && job.deadline !== null) {
    arm($)
    await tick($)
  }
}

/**
 * Compacts, then resumes the Auditor with its `resume` message. A compaction that is
 * refused (a turn is running) or vetoed (`{ skip }`) resumes nothing: the owner decides.
 */
async function compactNow($: EngineInterface): Promise<void> {
  if (firing) return
  firing = true
  try {
    const job = await read($, pending)
    if (!job) return
    await cancel($)
    let compacted
    try {
      compacted = await $.session.compact(job.instructions ? { instructions: job.instructions } : {})
    } catch (err) {
      $.ui.toast(`aeprogress did not compact (${String(err)}), so the Auditor was not resumed.`)
      return
    }
    if (compacted.skip) {
      $.ui.toast('aeprogress: another hook vetoed the compaction, so the Auditor was not resumed.')
      return
    }
    await $.prompt.submit({ text: job.resume })
  } finally {
    firing = false
  }
}

// ---- Update check ----

/** This copy's version; a test keeps it equal to the manifest's and the marketplace entry's. */
const VERSION = '0.5.6'

const available = atom(
  { plugin: 'auditor-executor-protocol', key: 'updateAvailable' } as const,
  null as UpdateInfo | null,
  { shape: 'update-1' },
)

/** The version the on-disk marketplace catalog lists for this plugin, refreshed whenever Claude Code updates it. */
async function catalogVersion($: EngineInterface, root: string): Promise<string | undefined> {
  const dir = marketplaceDir(root)
  if (!dir) return undefined
  const text = await $.fs.read(`${dir}/.claude-plugin/marketplace.json`).catch(() => undefined)
  return typeof text === 'string' ? catalogEntryVersion(text, $.plugin.name) : undefined
}

/**
 * Looks for a newer version in the marketplace catalog Claude Code keeps on disk, and keeps
 * what it found for the pane. No network: copies from a GitHub marketplace learn of new
 * versions when Claude Code refreshes the catalog (auto-update), and copies from the claude.ai
 * directory update themselves. Never throws.
 */
async function checkForUpdate($: EngineInterface, mode: UpdateMode): Promise<void> {
  try {
    if (mode === 'off') return
    const root = $.plugin.root
    const kind = installKind(root)
    if (kind !== 'marketplace') return
    const latest = await catalogVersion($, root)
    if (!latest || !isNewer(latest, VERSION)) {
      await update($, available, () => null)
      return
    }
    await update($, available, () => ({ installed: VERSION, latest, kind }))
    $.ui.toast(`aeprogress ${latest} is available (you have ${VERSION}). ${howToUpdate(kind)}`)
  } catch {
    // An update check that fails changes nothing.
  }
}

/** What the last check found, read while drawing the pane. */
async function updateNotice($: EngineInterface): Promise<UpdateInfo | null> {
  return read($, available)
}

// ---- Launch limit: what each launch hook decides, before and after the call ----

type LaunchPlan = { refusal?: string; isLaunch: boolean; ids: string[]; isExecutor: boolean; kind: Kind; live: LiveWorker[] }

/** Whether a Claude Code Agent call launches an Executor past the limits. Never throws. */
async function planAgentLaunch($: EngineInterface, input: { prompt?: unknown; description?: unknown }): Promise<LaunchPlan> {
  const prompt = typeof input.prompt === 'string' ? input.prompt : ''
  const description = typeof input.description === 'string' ? input.description : ''
  const ids = taskIdsIn(`${description} ${prompt}`)
  const kind: Kind = isDocsOnly(prompt) ? 'docs' : 'build'
  const plan: LaunchPlan = { isLaunch: false, ids, isExecutor: false, kind, live: [] }
  try {
    const snap = await read($, snapshot)
    const runIds = new Set(snap.items.map(i => i.id.toUpperCase()))
    plan.isExecutor = ids.some(id => runIds.size === 0 || runIds.has(id))
    if (plan.isExecutor && (await runActive($))) {
      plan.isLaunch = true
      plan.live = await liveExecutors($)
      plan.refusal = await judgeLaunch($, kind, plan.live)
    }
  } catch {
    if (plan.isLaunch) {
      plan.refusal = 'aeprogress launch limit: the live workers could not be counted, so this Executor is not launched.'
    }
  }
  return plan
}

/** After an Agent call: keep the new subagent's id with the task IDs its prompt named. Never throws. */
async function afterAgentLaunch($: EngineInterface, result: unknown, plan: LaunchPlan): Promise<void> {
  try {
    const record = result as { agentId?: unknown } | undefined
    const agentId = record && typeof record.agentId === 'string' ? record.agentId : undefined
    if (agentId && plan.ids.length > 0) {
      await update($, spawned, old => ({ ...old, [agentId]: plan.ids }))
      if (plan.isExecutor) await remember($, agentId, plan.kind, plan.live)
    }
  } catch {
    // A launch that could not be recorded still ran.
  }
  void refresh($)
}

/** Whether a Bash command launches an Orca worker past the limits. Never throws. */
async function planOrcaLaunch($: EngineInterface, command: string): Promise<LaunchPlan> {
  const plan: LaunchPlan = { isLaunch: false, ids: [], isExecutor: false, kind: 'build', live: [] }
  try {
    if (!mentionsOrcaLaunch(command) || !(await runActive($))) return plan
  } catch {
    return plan
  }
  let orcaIds: string[]
  try {
    orcaIds = await orcaLiveIds($)
  } catch {
    plan.isLaunch = true
    plan.refusal =
      'aeprogress launch limit: the live Orca workers could not be counted (orca orchestration ' +
      'worker-list failed), so this worker is not launched. Turn "Launch limit" off in /config ' +
      'to launch without it.'
    return plan
  }
  try {
    if (!orcaLaunch(command, new Set(orcaIds))) return plan
    plan.isLaunch = true
    const spec = specFile(command)
    const specText = spec ? ((await $.fs.read(spec).catch(() => '')) as string) : ''
    plan.kind = isDocsOnly(command) || isDocsOnly(specText) ? 'docs' : 'build'
    plan.live = await liveExecutors($, orcaIds)
    plan.refusal = await judgeLaunch($, plan.kind, plan.live)
  } catch {
    plan.refusal = 'aeprogress launch limit: the live workers could not be counted, so this worker is not launched.'
  }
  return plan
}

/** After an Orca launch: keep the dispatch id it printed, with what it builds. Never throws. */
async function afterOrcaLaunch($: EngineInterface, result: unknown, plan: LaunchPlan): Promise<void> {
  try {
    const dispatch = dispatchIdIn(JSON.stringify(result ?? ''))
    if (dispatch) await remember($, dispatch, plan.kind, plan.live)
  } catch {
    // A launch that could not be recorded still ran.
  }
  void refresh($)
}

/** The owner typed a prompt: a scheduled compaction gives way. Never throws. */
async function ownerTookOver($: EngineInterface): Promise<void> {
  try {
    if (await pendingJob($)) await cancel($)
  } catch {
    // Nothing scheduled, or nothing to drop.
  }
}

/** The owner runs /compact by hand: drop the countdown and hand back the resume text, if any. */
async function manualCompaction($: EngineInterface): Promise<string | undefined> {
  try {
    const job = await pendingJob($)
    if (!job) return undefined
    await cancel($)
    return job.resume
  } catch {
    return undefined
  }
}

/** After a manual /compact, the Auditor's resume message, once. */
async function resumeAfterManual($: EngineInterface, text: string): Promise<void> {
  try {
    await $.prompt.submit({ text })
  } catch {
    $.ui.toast('aeprogress could not resume the Auditor after /compact.')
  }
}

export const register: Register = (on, rawOptions) => {
  options = optionsOf(rawOptions)

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'aeprogress',
      description: 'Open the Auditor/Executor progress pane (optional: the run folder), or close it',
      argumentHint: '[run folder | close]',
    })
    interactive = e.isInteractive
    // A refused registration costs this feature alone, never the pane or the launch limit.
    if (options.compactOnClose) {
      await $.tool.register({
        name: TOOL,
        description:
          'Auditor/Executor protocol, Autonomous mode: call this when a phase has just closed (its gate ' +
          'APPROVED, the work pushed, and the Auditor brief up to date on disk), then end your turn. ' +
          `When the turn ends, a ${options.compactSeconds}-second countdown lets the owner cancel; then ` +
          'the session is compacted and `resume` is sent as the next message, which resumes you. Put in ' +
          '`resume` what to do next (for example: "Resume the plan from the brief: launch the first task ' +
          'of P2"), and in `instructions` what the summary must keep. In Guided mode do not call it: ' +
          'end the phase report with a resume message for the owner, who compacts by hand.',
        inputSchema: {
          type: 'object',
          properties: {
            resume: { type: 'string', description: 'The message that resumes the Auditor after compacting.' },
            instructions: { type: 'string', description: 'What the compaction summary must keep.' },
          },
          required: ['resume'],
        },
      }).catch(() => undefined)
      await resumeCountdown($)
    }
    await refresh($, true)
    // Read again on a timer only while the pane is open: a closed pane costs nothing.
    $.clock.every(REFRESH_MS, async () => {
      if (await isOpen($)) await refresh($, true)
    })
    const snap = await read($, snapshot)
    // A pane the owner closed stays closed, through a reload too, until /aeprogress.
    const closed = await read($, closedByOwner)
    if (options.autoOpen && !closed && snap.runDir && !snap.error && e.isInteractive) void open($)
    // In the background: a slow or failed check never holds the session up.
    void checkForUpdate($, options.updateCheck)
    return next(e)
  })

  // The owner's close, by the frame's mark or key or by /aeprogress close, is remembered.
  on('ui.close', async ($, e, next) => {
    if (e.id === PANE && e.origin.kind !== 'unload') await update($, closedByOwner, () => true)
    return next(e)
  })

  on('command.run', { command: 'aeprogress' }, async ($, e) => {
    const given = e.args.trim()
    if (given.toLowerCase() === 'close') {
      const wasOpen = await isOpen($)
      await $.ui.close({ id: PANE })
      await update($, closedByOwner, () => true)
      return { text: wasOpen ? 'Progress pane closed. /aeprogress opens it again.' : 'The progress pane is not open.' }
    }
    await update($, closedByOwner, () => false)
    if (given) {
      const dir = anchored(await $.session.root(), given)
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
    const found = await updateNotice($)
    const later = found ? ` aeprogress ${found.latest} is available (you have ${found.installed}).` : ''
    const where = shown(await $.session.root(), snap.runDir)
    return { text: `${whole} of ${where}: ${approved}/${snap.items.length} approved. Progress pane opened.${later}` }
  })

  // Claude Code subagents: an Agent call whose prompt names a task of the run is an
  // Executor launch, which the launch limit holds back past the limits. Any other Agent
  // call goes through untouched. After it starts, the subagent's id is kept with the task
  // IDs its prompt named, so the pane can show it in progress.
  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    const plan = await planAgentLaunch($, e as unknown as { prompt?: unknown; description?: unknown })
    if (plan.refusal) return { deny: plan.refusal }
    const ran = await next(e)
    await afterAgentLaunch($, ran.result, plan)
    return ran
  })

  // Orca: a worker-start, or a send that reopens a worker, goes through the same limit.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const plan = await planOrcaLaunch($, e.command)
    if (plan.refusal) return { deny: plan.refusal }
    const ran = await next(e)
    if (plan.isLaunch) await afterOrcaLaunch($, ran.result, plan)
    return ran
  })

  // A verdict or a report lands when the log is edited, and a subagent's turn ending means
  // it finished, so read the run again after any turn.
  // The main loop's turn ending also starts a scheduled compaction's countdown; an
  // aborted turn (the owner pressed Esc) cancels it.
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (await isOpen($)) void refresh($)
    if (!e.agentId && (await pendingJob($))) {
      if (e.isAborted) await cancel($)
      else await startCountdown($, options.compactSeconds)
    }
    return result
  })

  // The Auditor schedules the compaction; it runs once its turn ends.
  on('tool.call', { tool: 'mcp__auditor-executor-protocol__compact_and_resume' }, async ($, e, next) => {
    if (!options.compactOnClose) return next(e)
    const input = e as unknown as { resume?: unknown; instructions?: unknown }
    const resume = typeof input.resume === 'string' ? input.resume.trim() : ''
    const instructions = typeof input.instructions === 'string' ? input.instructions.trim() : ''
    if (!resume) return { result: 'Not scheduled: `resume` is required, the message that resumes you.' }
    if (!interactive) {
      return { result: 'Not scheduled: this session is not interactive, so nothing would resume it.' }
    }
    try {
      await schedule($, resume, instructions || undefined)
    } catch {
      return { result: 'Not scheduled: aeprogress failed to keep the compaction. Nothing will happen.' }
    }
    return {
      result:
        `Compaction scheduled. End your turn now: a ${options.compactSeconds}-second countdown starts ` +
        'when it ends, the owner may cancel it, and then the session is compacted and resumed with your ' +
        '`resume` message.',
    }
  })

  // The owner typing a prompt takes over: the countdown is dropped.
  on('prompt.submit', async ($, e, next) => {
    if (e.origin.kind === 'composer') await ownerTookOver($)
    return next(e)
  })

  // The owner compacting by hand (/compact) does the work: clear the countdown and resume once.
  on('session.compact', async ($, e, next) => {
    const resume = e.trigger === 'manual' && !e.agentId ? await manualCompaction($) : undefined
    const result = await next(e)
    if (resume && !result.skip) void resumeAfterManual($, resume)
    return result
  })

  // One line: the countdown and its two buttons, the words shortened to fit the band.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const job = await pendingJob($)
    if (!job || e.props.hasSurvey) return next(e)
    const { Box, Button, Text } = $.ui.resolve(e)
    const left = await countdownLeft($)
    const cols = e.props.bodyColumns ?? e.viewport?.columns ?? 60
    const band = bandLayout(job.deadline === null ? null : left, cols)
    return (
      <Box flexDirection="row">
        <Text wrap="truncate-end">
          {band.text}
          {band.seconds && (
            <Text weight="bold" color="warning" tabular>
              {band.seconds}
            </Text>
          )}{' '}
        </Text>
        <Button key="compact-cancel" label={band.cancel} onPress={() => cancel($)} />
        {band.now && <Text> </Text>}
        {band.now && <Button key="compact-now" label={band.now} variant="primary" onPress={() => compactNow($)} />}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const snap = await read($, snapshot)
    const cols = e.props.bodyColumns ?? e.viewport?.columns ?? 60
    const width = paneWidth(cols, PAD)

    // Every row but prose is one line of `width` cells at most; the cut is a safety net.
    const run = (s: Seg) => {
      const props: { color?: Seg['color']; dimColor?: boolean; weight?: 'bold' } = {}
      if (s.color) props.color = s.color
      if (s.dim) props.dimColor = true
      if (s.bold) props.weight = 'bold'
      return <Text {...props}>{s.text}</Text>
    }
    const row = (segs: readonly Seg[], mono = false) =>
      mono ? (
        <Text wrap="truncate-end" mono>
          {segs.map(run)}
        </Text>
      ) : (
        <Text wrap="truncate-end">{segs.map(run)}</Text>
      )
    const label = (text: string) => (
      <Text dimColor weight="semibold" size="caption" wrap="truncate-end">
        {cut(text, width)}
      </Text>
    )
    const blank = <Text> </Text>

    const notice = await updateNotice($)
    const noticeLine = notice && (
      <Text color="suggestion" wrap="wrap">
        {`aeprogress ${notice.latest} is available (you have ${notice.installed}). ${howToUpdate(notice.kind)}`}
      </Text>
    )

    if (snap.phases.length === 0) {
      return (
        <Box flexDirection="column" paddingX={PAD}>
          <Text weight="bold" wrap="truncate-end">
            {cut('AEP progress', width)}
          </Text>
          <Text dimColor wrap="wrap">
            {snap.error ?? 'The run has no phases or tasks yet.'}
          </Text>
          {noticeLine}
        </Box>
      )
    }

    const shares = phaseShares(snap.phases, snap.items)
    const whole = overall(shares)
    const weighted = snap.phases.some(p => p.weight !== 1)
    const working = new Set(snap.workers.map(w => w.taskId))
    const awaiting = snap.items.filter(i => i.state === 'AWAITING AUDIT' && !working.has(i.id.toUpperCase()))
    const attention = snap.items.filter(i => ATTENTION.has(i.state))
    const time = snap.readAt ? new Date(snap.readAt).toTimeString().slice(0, 5) : '--:--'
    const sourceLabel = { subagent: 'subagent', orca: 'Orca', command: 'worker' } as const
    const m = snap.machine
    const limitOn = options.launchLimit && snap.runDir !== ''
    const tip =
      options.spotlightTip && spotlightBusy(snap.indexerHistory ?? [], options.spotlightCpu)
        ? spotlightAdvice(m, await read($, projectRoot))
        : undefined

    const head = header(baseName(snap.runDir), percent(whole), width)
    const [title, ...rest] = head.left.split(' · ')
    const overallBar = barParts(whole, width)
    // The active phase, open until the owner closes it: the first with items not all APPROVED.
    const toggles = await read($, phaseToggles)
    const active = shares.find(p => p.total > 0 && p.approved < p.total)?.id
    const isPhaseOpen = (id: string) => toggles[id] ?? id === active
    const toggle = (id: string) => update($, phaseToggles, old => ({ ...old, [id]: !(old[id] ?? id === active) }))
    const inputs: PhaseInput[] = shares.map(p => ({ ...p, percent: percent(p.fraction), open: isPhaseOpen(p.id) }))
    const phases = phaseRows(inputs, width)
    const byId = new Map(snap.items.map(i => [i.id.toUpperCase(), i]))
    const workerOf = new Map<string, string>()
    for (const w of snap.workers) if (!workerOf.has(w.taskId)) workerOf.set(w.taskId, w.who)
    const chipsOf = (p: PhaseInput & { items: string[] }) =>
      p.items.map(id => chipOf(id, byId.get(id.toUpperCase())?.state ?? 'PENDING', workerOf.get(id.toUpperCase())))
    const INDENT = 2
    const phaseBlock = (p: (typeof inputs)[number] & { items: string[] }, segs: Seg[]) => {
      const name = p.title || 'untitled'
      const press = () => toggle(p.id)
      if (p.open) {
        const lead = `▾ ${p.id} `
        return (
          <Box flexDirection="column">
            <Box flexDirection="row">
              <Button key={`phase-${p.id}`} plain label={`${p.id} ${name}`} onPress={press}>
                <Text mono>
                  <Text color="inactive">▾ </Text>
                  <Text weight="bold">{p.id}</Text>
                </Text>
              </Button>
              <Text> </Text>
              <Box width={Math.max(4, width - cells(lead))}>
                <Text wrap="wrap">{name}</Text>
              </Box>
            </Box>
            <Box flexDirection="column" paddingLeft={INDENT}>
              {row(phaseBarLine(p, width - INDENT), true)}
              {chipLines(chipsOf(p), width - INDENT).map(line => row(line))}
            </Box>
          </Box>
        )
      }
      const button = (
        <Button key={`phase-${p.id}`} plain label={`${p.id} ${name}`} onPress={press}>
          <Text wrap="truncate-end" mono>
            {segs.map(run)}
          </Text>
        </Button>
      )
      return button
    }
    const item = (dot: Seg['color'], id: string, main: string, tail: string): Seg[] => {
      const fit = listRow(id, main, tail, width)
      return [{ text: '● ', color: dot }, { text: id }, { text: fit.main ? `  ${fit.main}` : '' }, { text: fit.tail, dim: true }]
    }
    const footer = footerRows(
      {
        busy: m ? Math.round(m.busy * 100) : undefined,
        detail: m?.detail,
        limit: limitOn
          ? {
              live: snap.launches?.live ?? 0,
              maxWorkers: options.limits.maxWorkers,
              builds: snap.launches?.builds ?? 0,
              maxBuilds: options.limits.maxBuilds,
              maxBusy: options.limits.maxBusy,
            }
          : undefined,
      },
      width,
    )
    const dot: Seg['color'] = !m ? 'inactive' : m.busy > options.limits.maxBusy ? 'error' : m.busy > 0.4 ? 'warning' : 'success'

    return (
      <Box flexDirection="column" paddingX={PAD}>
        <Box flexDirection="row" justifyContent="space-between">
          <Text wrap="truncate-end">
            <Text weight="bold">{title}</Text>
            {rest.length > 0 && <Text dimColor>{` · ${rest.join(' · ')}`}</Text>}
          </Text>
          <Text weight="bold" size="heading" tabular>
            {head.right}
          </Text>
        </Box>
        {row([{ text: overallBar.done, color: 'claude' }, { text: overallBar.rest, color: 'subtle' }], true)}
        {row([{ text: weighingLine(snap.phases.length, weighted, width), dim: true }])}
        {blank}
        {phases.map((segs, n) => phaseBlock({ ...inputs[n]!, items: shares[n]!.items }, segs))}
        {blank}
        {snap.workers.length > 0 && label('IN PROGRESS')}
        {snap.workers.map(w => row(item('warning', w.taskId, w.who, sourceLabel[w.source])))}
        {awaiting.length > 0 && label('AWAITING AUDIT')}
        {awaiting.map(i => row(item('suggestion', i.id, i.executor ?? '', '')))}
        {attention.length > 0 && label('NEEDS ATTENTION')}
        {attention.map(i => row(item('error', i.id, i.state.toLowerCase(), i.executor ?? '')))}
        {(snap.workers.length > 0 || awaiting.length > 0 || attention.length > 0) && blank}
        {footer.lines.map((line, n) => row(n === 0 ? [{ text: '● ', color: dot }, { text: line }] : [{ text: `  ${line}` }]))}
        {footer.detail && row([{ text: `  ${footer.detail}`, dim: true }])}
        {noticeLine}
        {tip && (
          <Text color="warning" wrap="wrap">
            {tip}
          </Text>
        )}
        {snap.error ? (
          <Text wrap="wrap">
            <Text color="error">Last read failed: </Text>
            <Text dimColor>{snap.error}</Text>
          </Text>
        ) : (
          row([{ text: readLine(baseName(snap.runDir), time, width), dim: true }])
        )}
        {snap.items.length === 0 && row([{ text: cut('No tasks in the log yet.', width), dim: true }])}
      </Box>
    )
  })
}
