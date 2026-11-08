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

/** How busy the machine is: `busy` 1 means every core busy (Unix load over cores, Windows CPU % / 100). */
export type Machine = {
  busy: number
  detail: string
  os: 'linux' | 'macos' | 'bsd' | 'windows'
  /** CPU % of Spotlight's indexing processes, added up; 0 off macOS. */
  indexerCpu: number
}

/** Whether a launched worker builds, by Orca dispatch id or subagent id. */
export type Kinds = Record<string, 'build' | 'docs'>

/** A compaction the Auditor scheduled when a phase closed. */
export type PendingCompaction = {
  /** The message that resumes the Auditor once the session is compacted. */
  resume: string
  /** What the summary must keep, passed to the compaction. */
  instructions?: string
  /** When the countdown ends (ms since the epoch); null until the Auditor's turn ends. */
  deadline: number | null
}

/** A newer aeprogress than the one running, as the last check found it. */
export type UpdateInfo = {
  installed: string
  latest: string
  /** How this copy was installed: decides how the pane says to update it. */
  kind: 'marketplace' | 'local'
}

export type Snapshot = {
  /** The run folder read, as resolved; empty when none was found. */
  runDir: string
  items: Item[]
  phases: Phase[]
  workers: Worker[]
  readAt: number
  /** The machine's load at the last read; absent when no source answered. */
  machine?: Machine
  /** Spotlight's indexing CPU at the last few reads, newest last (macOS). */
  indexerHistory?: number[]
  /** Live Executors the launch limit counts, and how many of them build. */
  launches?: { live: number; builds: number }
  /** Why the last read failed, in words for the person. */
  error?: string
}

declare module 'claude-code' {
  interface PluginState {
    aeprogress: {
      snapshot: Shaped<Snapshot>
      /** Phases the owner opened (true) or closed (false) in the pane, by phase ID. */
      phaseToggles: Shaped<Record<string, boolean>>
      /** The run folder `/aeprogress <dir>` chose for this session. */
      chosenDir: string
      /** Subagent id -> task IDs its spawn prompt named. */
      spawned: Record<string, string[]>
      kinds: Shaped<Kinds>
      /** The repository root of the run, for the Spotlight recommendation. */
      projectRoot: string
      /** Whether the Spotlight recommendation was toasted this session. */
      spotlightToasted: boolean
      pendingCompaction: Shaped<PendingCompaction | null>
      /** Seconds left in the compaction countdown, for the band. */
      compactSecondsLeft: number
      updateAvailable: Shaped<UpdateInfo | null>
    }
  }
}
