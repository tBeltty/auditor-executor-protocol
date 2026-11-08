/** One task or gate as `aepkit status --json` reads it. */
export type Item = {
  id: string
  phase: number | null
  kind: string
  state: string
  verdict: string | null
  report: string | null
  executor: string | null
  inLog: boolean
}

/** One phase as `aepkit status --json` reads it from the guide and the plan. */
export type Phase = {
  number: number
  id: string
  title: string
  weight: number
  brokenDown: boolean
  items: string[]
}

/** Someone working on a task ID right now, and where that was seen. */
export type Worker = {
  taskId: string
  who: string
  source: 'subagent' | 'orca' | 'command'
}

export type Snapshot = {
  /** The run folder read, as resolved; empty when none was found. */
  runDir: string
  items: Item[]
  phases: Phase[]
  workers: Worker[]
  readAt: number
  /** Why the last read failed, in words for the person. */
  error?: string
}

declare module 'claude-code' {
  interface PluginState {
    aeprogress: {
      snapshot: Shaped<Snapshot>
      /** The run folder `/aeprogress <dir>` chose for this session. */
      chosenDir: string
      /** Subagent id -> task IDs its spawn prompt named. */
      spawned: Record<string, string[]>
    }
  }
}
