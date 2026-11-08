# aeprogress: progress pane for Claude Code

An optional Claude Code mod that keeps a pane beside the chat with the progress of an
Auditor/Executor run. The protocol does not depend on it. It reads the run's
`compliance-log.md` through `aepkit status --json` and shows:

- the overall percentage and a bar for the whole run;
- one bar per phase, with approved items over the total, and phases the plan declares
  that the execution guide has not broken down yet;
- **In progress**: who is working on which task ID right now, whether a Claude Code
  subagent, an Orca worker or a worker of any other harness;
- **Awaiting audit**: items reported `DONE` that have no verdict yet;
- **Needs attention**: `CONDITIONAL`, `REJECTED`, `CONFLICT`, `BLOCKED` and `FAILED` items.

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
