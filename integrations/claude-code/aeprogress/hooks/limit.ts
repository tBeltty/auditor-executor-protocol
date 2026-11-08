// The launch limit's rules, with no `$` in them: what counts as a launch, whether it
// builds, and whether the limits let it through.
import type { Machine } from '../types'

export type Kind = 'build' | 'docs'

export type Limits = {
  maxWorkers: number
  maxBuilds: number
  /** Busy fraction (1 = every core busy) above which a build is not launched. */
  maxBusy: number
}

export type LiveWorker = { id: string; kind: Kind }

/** A handoff that does not compile carries this line; everything else counts as a build. */
const DOCS_MARK = /\bLoad:\s*docs-only\b/i
// `orca` where a shell runs it: at the start, after a separator or `$(`, behind variable
// assignments or a path ("$ORCA_CLI_BIN_DIR/orca"). The words inside an echo or a commit
// message are not a launch.
const AT_COMMAND = String.raw`(?:^|[;&|(\n]|\$\()\s*(?:\w+=\S*\s+)*(?:["']?[^\s"';&|()]*[\\/])?orca["']?\s+(?:[^\n;&|]*\s)?`
const WORKER_START = new RegExp(`${AT_COMMAND}orchestration\\s+worker-start\\b`)
const SEND = new RegExp(`${AT_COMMAND}orchestration\\s+send\\b`)

export function isDocsOnly(text: string): boolean {
  return DOCS_MARK.test(text)
}

function flag(command: string, name: string): string | undefined {
  const m = command.match(new RegExp(`--${name}(?:=|\\s+)("([^"]*)"|'([^']*)'|(\\S+))`))
  return m ? (m[2] ?? m[3] ?? m[4]) : undefined
}

/**
 * Whether a shell command launches an Orca worker: every `worker-start`, and a `send`
 * addressed to a dispatch that is not live (it reopens that worker). A message to a live
 * worker or to the coordinator, such as a worker's own report, is no launch.
 */
export function orcaLaunch(command: string, liveIds: ReadonlySet<string>): boolean {
  if (WORKER_START.test(command)) return true
  if (!SEND.test(command)) return false
  const to = flag(command, 'to')
  const dispatch = to?.startsWith('dispatch:') ? to.slice('dispatch:'.length) : undefined
  return dispatch !== undefined && !liveIds.has(dispatch)
}

/** Whether a command could be an Orca launch at all, before anything is counted. */
export function mentionsOrcaLaunch(command: string): boolean {
  return WORKER_START.test(command) || SEND.test(command)
}

/** The `--spec-file` a worker-start reads its handoff from; `-` (stdin) is none. */
export function specFile(command: string): string | undefined {
  const path = flag(command, 'spec-file')
  return path && path !== '-' ? path : undefined
}

/** The dispatch id a worker-start printed, in its text or its JSON receipt. */
export function dispatchIdIn(output: string): string | undefined {
  return output.match(/\b(ctx_[A-Za-z0-9]+)\b/)?.[1]
}

/** Live Orca workers from `orca orchestration worker-list --json`; throws on another shape. */
export function orcaLive(stdout: string): string[] {
  const data = JSON.parse(stdout) as {
    ok?: boolean
    result?: { workers?: { dispatchId?: string; liveness?: string; outcome?: string }[] }
  }
  if (data.ok === false || !Array.isArray(data.result?.workers)) {
    throw new Error('orca worker-list answered in a shape the limit does not know')
  }
  return data.result.workers
    .filter(w => w.dispatchId && w.liveness === 'live' && w.outcome === 'in_progress')
    .map(w => w.dispatchId as string)
}

/** Why a launch of this kind is refused now; empty when the limits let it through. */
export function refusals(kind: Kind, live: readonly LiveWorker[], machine: Machine | undefined, limits: Limits): string[] {
  const reasons: string[] = []
  const builds = live.filter(w => w.kind === 'build').length
  if (live.length >= limits.maxWorkers) {
    reasons.push(`${live.length} ${live.length === 1 ? 'worker is' : 'workers are'} live (limit ${limits.maxWorkers})`)
  }
  if (kind === 'build' && builds >= limits.maxBuilds) {
    reasons.push(
      `${builds} building worker${builds === 1 ? ' is' : 's are'} live (limit ${limits.maxBuilds}); ` +
        'a handoff that does not compile carries the line "Load: docs-only"',
    )
  }
  if (kind === 'build' && machine && machine.busy > limits.maxBusy) {
    reasons.push(
      `the machine is ${Math.round(machine.busy * 100)}% busy (${machine.detail}; ` +
        `limit ${Math.round(limits.maxBusy * 100)}% for a build)`,
    )
  }
  return reasons
}

/**
 * Spotlight's indexing CPU stays high: true once the last `streak` readings were all at
 * or above `threshold` percent.
 */
export function spotlightBusy(history: readonly number[], threshold: number, streak = 2): boolean {
  const recent = history.slice(-streak)
  return recent.length === streak && recent.every(cpu => cpu >= threshold)
}
