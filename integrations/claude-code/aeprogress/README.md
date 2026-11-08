# aeprogress: progress pane and launch limit for Claude Code

An optional Claude Code mod that keeps a pane beside the chat with the progress of an
Auditor/Executor run. The protocol does not depend on it. It reads the run's
`compliance-log.md` through `aepkit status --json` and shows:

- the overall percentage and a bar for the whole run;
- one bar per phase, with approved items over the total, and phases the plan declares
  that the execution guide has not broken down yet;
- **In progress**: who is working on which task ID right now, whether a Claude Code
  subagent, an Orca worker or a worker of any other harness;
- **Awaiting audit**: items reported `DONE` that have no verdict yet;
- **Needs attention**: `CONDITIONAL`, `REJECTED`, `CONFLICT`, `BLOCKED` and `FAILED` items;
- the machine's load, with a colored dot, and how full the launch limit is.

When a phase closes, the Auditor can also **compact its own session and resume itself**,
after a countdown the owner can cancel.

It also carries a **launch limit**: while a run is found, it holds back launching another
Executor past a worker count or a machine load, with a message saying why. And on macOS
it recommends excluding the project from Spotlight when indexing keeps the machine busy.

In Autonomous mode the owner only gets a report per phase; the pane lets them follow
the run without interrupting the Auditor.

> **Early access.** Claude Code marks its mod API as early access: it can change between
> Claude Code releases. This mod is tested on Claude Code 2.1.319.

## Requirements

- Claude Code with mods (function hooks): the terminal app, the desktop app's local
  sessions, or the IDE extensions.
- `aepkit` 0.7.0 or newer on the machine (`pipx install aepkit`, or
  `pipx upgrade aepkit`). The pane says so when it is missing or too old.

## Install

At the prompt of a Claude Code terminal session:

```
/plugin install aeprogress --marketplace tBeltty/auditor-executor-protocol
```

Answer `y` to add the marketplace, then pick a scope (user scope loads it in every
session). From a shell:

```bash
claude plugin install aeprogress --marketplace tBeltty/auditor-executor-protocol
```

In the desktop app, where `/plugin` does not run: click **+** next to the prompt box,
then **Plugins**, **Add marketplace** with `tBeltty/auditor-executor-protocol`, then
**Add plugin**. A mod installed from a terminal at user scope also loads in the desktop
app's local sessions.

## Use

```
/aeprogress              # open the pane on the run found under the working directory
/aeprogress docs/my-run  # open it on this run folder for the rest of the session
```

The command also answers with a one-line summary (`50% of docs/my-run: 1/2 approved`),
which helps where no pane is drawn.

The pane opens by itself when a session starts in a workspace with a run, where the
surface has room for it as a sidebar (in the terminal, from 144 columns). Turn that off
with **Open at session start** in `/config`.

### Which run it reads

1. The folder given to `/aeprogress <folder>`, for the rest of the session.
2. **Run folder** in `/config`, relative to the workspace or absolute.
3. Otherwise the most recently modified `compliance-log.md` up to three levels under the
   working directory (hidden folders, `node_modules`, `venv`, `dist`, `build`, `target`
   skipped).

## Who is working on what

The pane matches task IDs (`P<n>-T<m>`, `P<n>-G<m>`, in any case) against the IDs of the
run, so a worker of another project never shows. It looks in three places:

| Source | How it is read | When |
|---|---|---|
| Claude Code subagents | The session's own agent list, plus the task ID the spawn prompt named (`ROLE: Executor, reporting on P1-T3`), so an Auditor in Autonomous mode is followed with no setup | Always |
| Orca workers | `orca worktree ps --json`: a worktree whose name, branch or folder names the task ID and whose agent has not finished. Only worktrees of the run's repository count | **External workers** `auto` inside an Orca terminal, or `orca` |
| Any other harness | **Workers command**: a command that prints the workers running now, one per line. Every line that names a task ID of the run marks it in progress, and the line is shown as who | **External workers** `auto` or `command`, when the command is set |

A status board column named `Executor` (or `Worker`, `Agent`, `Owner`, `Assignee`) is
shown next to items awaiting audit or needing attention.

A workers command for a harness that writes one JSON object per running job could be
as small as `sh -c "my-harness jobs --running"`, as long as each line names the task ID.

## The launch limit

Several Executors that compile at once can saturate a machine, and a saturated machine
makes every one of them slower and flakier. While the session has a run, the mod holds
back an Executor launch that would pass any of these limits (each one a `/config` option):

| Limit | Default | Applies to |
|---|---|---|
| Most live workers | 2 | Every launch |
| Most building workers | 1 | A launch that builds |
| Busiest machine for a build | 75% | A launch that builds |

A refused launch never runs. The Auditor gets the reason back, such as
`2 workers are live (limit 2)` or `the machine is 90% busy (load 7.2 of 8 cores; limit 75%
for a build)`, and can wait for a worker to finish.

**Which launches it sees:**

| Launcher | What counts as a launch | How live workers are counted |
|---|---|---|
| Claude Code subagents | A subagent whose prompt names a task ID of the run (an Executor handoff). Exploration, review and workflow subagents are never held back | The session's own agent list |
| Orca | `orca orchestration worker-start`, and `orca orchestration send --to dispatch:<id>` when that dispatch is not live (it reopens the worker). A message to a live worker or to the coordinator, such as a worker's own report, is never held back. `orca` must be the command itself: the same words inside an `echo` or a commit message are not a launch | `orca orchestration worker-list --json`: workers `live` and `in_progress`. Without a bound Run that is every Orca worker on the machine, which is what a machine-wide limit wants. If Orca cannot be asked, the launch is refused, the safe side |
| Any other harness | Not seen: its launches go through without the limit. Its workers still show in the pane through the workers command | |

Claude Code subagents and Orca workers are counted together.

**Builds or not.** A handoff that compiles, builds and tests nothing (documentation, a
plan, a review) carries the line `Load: docs-only`, as `references/handoffs.md` describes.
The mod looks for it in the subagent's prompt, in the Orca command (`--spec "..."`), or in
the file `--spec-file` names (read from the session's working directory). Anything without
it counts as a build. A docs-only launch only answers to the worker count.

Turn the limit off with **Launch limit** in `/config`; without a run it does nothing.

## Machine load

The mod API does not say which system it runs on, so the mod tries each source by what
exists, and turns it into one number, the busy fraction:

| System | Source | Busy fraction | Tested |
|---|---|---|---|
| Linux | `/proc/loadavg` over the processors in `/proc/cpuinfo` (`nproc` when cpuinfo lists none) | 1-minute load / cores | Parser checked against a real kernel's output (arm64 container); not yet run inside Claude Code on Linux |
| macOS, BSD | `sysctl -n vm.loadavg` over `sysctl -n hw.ncpu` | 1-minute load / cores | macOS: run for real |
| Windows | PowerShell, `Win32_Processor` `LoadPercentage` averaged | CPU % / 100 | Simulated output only |

A system where no source answers shows "Machine load unknown", and the limit then
applies only its worker counts.

## Spotlight recommendation (macOS)

Spotlight indexes new files as they appear, and a build that writes thousands of them
can keep `mds_stores` and `mdworker` busy for minutes. When their CPU, added up, stays at
or above 50% on two reads in a row (20 seconds apart while the pane is open), the pane
recommends excluding the project folder (the run's git repository root) in
**System Settings > Spotlight > Search Privacy** (**Spotlight > Privacy** on older
macOS), shows the exact path, and toasts once per session. A launch the limit refuses
while Spotlight is busy says so too.

The mod only recommends. It never changes a setting, runs `mdutil` or writes into the
folder. Turn it off with **Spotlight recommendation** in `/config`, or change its
threshold. Other systems never show it.

## Compacting when a phase closes

In Autonomous mode the Auditor waits on its workers for long stretches, and a session
that carries every earlier phase gets expensive whenever its prompt cache expires.
When a phase closes (gate `APPROVED`, work pushed, Auditor brief up to date on disk),
everything needed to go on is on disk, so the session can be compacted.

The mod gives the Auditor a tool, `compact_and_resume` (`mcp__aeprogress__compact_and_resume`):

| Input | What it is |
|---|---|
| `resume` (required) | The message that resumes the Auditor after compacting, such as `Resume the plan from the brief: launch the first task of P2` |
| `instructions` | What the compaction summary must keep |

The Auditor calls it and ends its turn. When the turn ends, a band above the prompt
counts down 40 seconds with **Cancel** and **Compact now**. At zero the session is
compacted, as `/compact` does, and the `resume` message is sent, which opens the
Auditor's next turn.

The owner can always step in:

- **Cancel**: nothing is compacted or resumed.
- **Typing a prompt** during the countdown takes over: the countdown is dropped.
- **Pressing Esc** on the Auditor's turn drops it too.
- **`/compact` by hand** while the countdown runs: the countdown is cleared and the
  `resume` message is sent once, after that compaction.

If the compaction is refused (a turn is running) or another plugin vetoes it, the
Auditor is not resumed: a toast says so and the owner decides. A countdown survives a
reload of the mod. The tool is offered only in interactive sessions, where something
can resume; turn it off, or change the seconds, in `/config`.

## How the percentage is computed

- Each phase weighs 1, unless the plan's phase table has a `Weight` column:

  ```markdown
  | Phase | Delivers | Risk | Weight |
  |---|---|---|---|
  | P0 | Groundwork | low | 1 |
  | P1 | The core feature | high | 3 |
  ```

- Inside a phase every task and gate counts the same. `APPROVED` counts 1, since only
  `APPROVED` closes an item. `CONDITIONAL` counts 0.5: the work is accepted except for
  named items, so it moves the bar but never lets a phase reach 100%. Every other state
  counts 0.
- A phase the guide has not broken down counts 0 with its full weight, so the overall
  percentage does not jump when a new phase is expanded.
- Task IDs the guide lists and the log has no row for yet count as `PENDING`.

## What it runs, and when

- `aepkit status --json <run>` (and, with Orca or a workers command, that command),
  each one a short process with a 15-second limit. Nothing keeps running in the
  background.
- The machine load: on macOS `sysctl` twice and `ps` once (for Spotlight), on Linux two
  file reads, on Windows one PowerShell call. Again before every launch the limit judges.
- With the launch limit on and Orca around, `orca orchestration worker-list --json`.
- At session start, when `/aeprogress` runs, after each turn, when a subagent starts
  or stops, and every 20 seconds **only while the pane is open**. A closed pane costs
  nothing.
- When `aepkit` is not on the `PATH` Claude Code sees (the desktop app's `PATH` is often
  shorter than a terminal's), the pane tries `~/.local/bin/aepkit` and then
  `python3 -m aepkit`. **aepkit command** in `/config` names it outright.

## Options (`/config`)

| Option | Default | What it does |
|---|---|---|
| Run folder | empty | The run to read; empty searches the working directory |
| External workers | `auto` | `auto`, `orca`, `command` or `off` |
| Workers command | empty | The command for any other harness |
| aepkit command | empty | How to run aepkit, such as a full path |
| Open at session start | on | Open the pane when a run is found |
| Launch limit | on | Hold back Executor launches past the limits below, while a run is found |
| Most live workers | 2 | Subagents and Orca workers together |
| Most building workers | 1 | Live Executors without `Load: docs-only` |
| Busiest machine for a build (%) | 75 | No building launch above this load |
| Spotlight recommendation (macOS) | on | Recommend excluding the project from Spotlight |
| Spotlight CPU that triggers the recommendation (%) | 50 | Indexing CPU held on two reads in a row |
| Compact on phase close | on | Offer the Auditor the `compact_and_resume` tool |
| Compaction countdown (seconds) | 40 | How long the band waits before compacting |

## Develop

```bash
claude plugin validate integrations/claude-code/aeprogress
claude plugin test integrations/claude-code/aeprogress
claude --plugin-dir integrations/claude-code/aeprogress
```

The tests stand in for `aepkit` with `tests/fixtures/status.ts`, the JSON that
`aepkit status --json` prints for the sample run in the repository's
`tests/test_status.py`. That Python test checks that aepkit still prints exactly that
JSON, so a change to either side fails a test.
