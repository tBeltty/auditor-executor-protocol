// The pane's arithmetic and the readers of each worker source, with no `$` in them.
import type { Item, Phase, Worker } from '../types'

const TASK_ID_RE = /\bP(\d+)-([TG])(\d+)\b/gi

/** Task and gate IDs (P<n>-T<m>, P<n>-G<m>) named anywhere in a text, upper-cased. */
export function taskIdsIn(text: string): string[] {
  const found = new Set<string>()
  for (const m of text.matchAll(TASK_ID_RE)) found.add(`P${m[1]}-${m[2]!.toUpperCase()}${m[3]}`)
  return [...found]
}

/**
 * How much of an item is done. Only APPROVED closes an item; CONDITIONAL is accepted
 * work with named items still open, so it counts half and never lets a phase reach 100%.
 */
export function credit(state: string): number {
  if (state === 'APPROVED') return 1
  if (state === 'CONDITIONAL') return 0.5
  return 0
}

export type PhaseShare = Phase & { fraction: number; approved: number; total: number }

export function phaseShares(phases: readonly Phase[], items: readonly Item[]): PhaseShare[] {
  const byId = new Map(items.map(i => [i.id, i]))
  return phases.map(p => {
    const mine = p.items.map(id => byId.get(id)).filter((i): i is Item => i !== undefined)
    const got = mine.reduce((sum, i) => sum + credit(i.state), 0)
    return {
      ...p,
      fraction: mine.length === 0 ? 0 : got / mine.length,
      approved: mine.filter(i => i.state === 'APPROVED').length,
      total: mine.length,
    }
  })
}

/** The weighted share of the whole run; a phase not broken down yet counts as 0 done. */
export function overall(shares: readonly PhaseShare[]): number {
  const weight = shares.reduce((s, p) => s + p.weight, 0)
  return weight === 0 ? 0 : shares.reduce((s, p) => s + p.weight * p.fraction, 0) / weight
}

export function bar(fraction: number, width: number): string {
  const full = Math.round(Math.max(0, Math.min(1, fraction)) * width)
  return '█'.repeat(full) + '░'.repeat(Math.max(0, width - full))
}

export function percent(fraction: number): string {
  return `${Math.round(fraction * 1000) / 10}%`
}

/** IDs that stay open and need someone: everything but APPROVED, PENDING and AWAITING AUDIT. */
export const ATTENTION = new Set(['CONDITIONAL', 'REJECTED', 'CONFLICT', 'BLOCKED', 'FAILED'])

/** The items and phases out of `aepkit status --json`; throws on anything else. */
export function parseStatus(stdout: string): { items: Item[]; phases: Phase[] } {
  const data = JSON.parse(stdout) as { schema?: unknown; items?: unknown; phases?: unknown }
  if (data.schema !== 1 || !Array.isArray(data.items) || !Array.isArray(data.phases)) {
    throw new Error('aepkit status --json answered in a shape this pane does not know')
  }
  return { items: data.items as Item[], phases: data.phases as Phase[] }
}

/** Split a command line on spaces, keeping "double" or 'single' quoted parts whole. */
export function splitCommand(line: string): string[] {
  const out: string[] = []
  for (const m of line.matchAll(/"([^"]*)"|'([^']*)'|(\S+)/g)) out.push(m[1] ?? m[2] ?? m[3] ?? '')
  return out
}

type AgentLike = {
  id: string
  description: string
  type: string
  status: string
  name?: string
}

const LIVE_AGENT = new Set(['pending', 'running', 'waiting'])

/**
 * Claude Code subagents working on a known ID: the ID is read from the subagent's
 * description and name, and from its spawn prompt (`spawned`, by agent id).
 */
export function subagentWorkers(
  agents: readonly AgentLike[],
  spawned: Readonly<Record<string, readonly string[]>>,
  known: ReadonlySet<string>,
): Worker[] {
  const workers: Worker[] = []
  for (const a of agents) {
    if (!LIVE_AGENT.has(a.status)) continue
    const fromText = taskIdsIn(`${a.description} ${a.name ?? ''}`).filter(id => known.has(id))
    const ids = fromText.length > 0 ? fromText : (spawned[a.id] ?? []).filter(id => known.has(id))
    const who = a.name || a.description || a.type
    for (const taskId of ids) workers.push({ taskId, who, source: 'subagent' })
  }
  return workers
}

type OrcaAgent = { state?: string; taskTitle?: string | null; displayName?: string | null }
type OrcaWorktree = {
  repoId?: string
  displayName?: string
  branch?: string
  path?: string
  agents?: OrcaAgent[] | null
}

/**
 * Orca workers on a known ID, from `orca worktree ps --json`: a worktree whose name,
 * branch or folder names the ID and whose agent has not finished. With `repoId`, only
 * worktrees of that repository count.
 */
export function orcaWorkers(stdout: string, repoId: string | undefined, known: ReadonlySet<string>): Worker[] {
  const data = JSON.parse(stdout) as { result?: { worktrees?: OrcaWorktree[] } }
  const workers: Worker[] = []
  for (const w of data.result?.worktrees ?? []) {
    if (repoId && w.repoId !== repoId) continue
    const live = (w.agents ?? []).filter(a => a.state && a.state !== 'done')
    if (live.length === 0) continue
    const folder = (w.path ?? '').split(/[\\/]/).pop() ?? ''
    const names = [w.displayName, w.branch, folder, ...live.flatMap(a => [a.taskTitle, a.displayName])]
    const ids = taskIdsIn(names.filter(Boolean).join(' ')).filter(id => known.has(id))
    const state = live[0]!.state
    const who = (w.displayName || folder) + (state === 'working' ? '' : ` (${state})`)
    for (const taskId of ids) workers.push({ taskId, who, source: 'orca' })
  }
  return workers
}

/** Workers from any other harness: each output line that names a known ID marks it. */
export function commandWorkers(stdout: string, known: ReadonlySet<string>): Worker[] {
  const workers: Worker[] = []
  for (const line of stdout.split('\n')) {
    const who = line.trim()
    for (const taskId of taskIdsIn(who).filter(id => known.has(id))) {
      workers.push({ taskId, who: who.slice(0, 80), source: 'command' })
    }
  }
  return workers
}
