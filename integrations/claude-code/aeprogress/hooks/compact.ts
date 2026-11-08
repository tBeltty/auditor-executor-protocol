// Compacting the Auditor's session when a phase closes: the Auditor schedules it with a
// tool, a countdown starts when its turn ends, and at zero the session is compacted and
// the Auditor resumed. The owner can cancel, compact now, type, or compact by hand.
import { atom, read, update } from 'claude-code'
import type { EngineInterface } from 'claude-code'

import type { PendingCompaction } from '../types'

export const TOOL = 'compact_and_resume'

const pending = atom(
  { plugin: 'aeprogress', key: 'pendingCompaction' } as const,
  null as PendingCompaction | null,
  { shape: 'pending-1' },
)
const secondsLeft = atom({ plugin: 'aeprogress', key: 'compactSecondsLeft' } as const, 0)

// Module state: a reload drops the timer, and `resumeCountdown` arms it again.
let ticker: { cancel: () => void } | undefined
let firing = false

/** The scheduled compaction, if any. */
export async function pendingJob($: EngineInterface): Promise<PendingCompaction | null> {
  return read($, pending)
}

/** Seconds left in a running countdown, read while drawing the band. */
export async function countdownLeft($: EngineInterface): Promise<number> {
  return read($, secondsLeft)
}

function stopTicker(): void {
  ticker?.cancel()
  ticker = undefined
}

/** Keeps what to compact for and how to resume; the countdown waits for the turn's end. */
export async function schedule($: EngineInterface, resume: string, instructions?: string): Promise<void> {
  stopTicker()
  await update($, pending, () => ({ resume, ...(instructions ? { instructions } : {}), deadline: null }))
}

/** Drops a scheduled or running countdown: nothing is compacted or resumed. */
export async function cancel($: EngineInterface): Promise<void> {
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
export async function startCountdown($: EngineInterface, seconds: number): Promise<void> {
  const job = await read($, pending)
  if (!job || job.deadline !== null) return
  const deadline = (await $.clock.now()) + seconds * 1000
  await update($, pending, old => (old ? { ...old, deadline } : old))
  await update($, secondsLeft, () => seconds)
  arm($)
}

/** After a reload: a countdown that was running keeps running toward the same deadline. */
export async function resumeCountdown($: EngineInterface): Promise<void> {
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
export async function compactNow($: EngineInterface): Promise<void> {
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
