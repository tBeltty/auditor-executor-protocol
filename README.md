# Auditor/Executor Protocol

A two-role protocol for running multi-phase work through an AI agent, a subagent, or a
human collaborator, without the plan quietly turning back into a discussion and without
"all tests pass" quietly turning into the whole verification.

One role — the Auditor — decides what "done" means and proves it independently. The
other — the Executor — implements one task at a time and reports evidence. Neither does
the other's job. `SKILL.md` is the protocol; `auditkit` is a small CLI that handles the
mechanical parts of following it.

## Vibe coding, and where this picks up

Vibe coding (describing what you want, letting an agent write it, judging the result by
whether it feels right) is a legitimate way to build, worth experiencing on its own
terms. A lot of real software gets made this way, and none of what follows argues
against it.

It runs into a specific wall: once a mistake is expensive to catch late (money moves,
permissions change, one user's data reaches another's screen), "it feels right" stops
being enough evidence, no matter how good the agent is. The gap is in verification, not
generation, and closing it takes a different process than vibe coding was ever built to
run. This repo calls that process Structured AI Engineering: an unambiguous instruction
sheet instead of a feel, and evidence that gets independently re-checked instead of a
diff that looks plausible.

Reach for it when the task is the kind above, not by default; vibe coding stays the
right tool for everything else. One role, the Auditor, decides what "done" means and
proves it independently; the other, the Executor, implements one task at a time and
reports evidence instead of an impression. You don't need a second person to run it —
they can be two sessions of the same agent, with you switching hats between them.

Handed to an agent that didn't write the plan, that instruction sheet still degrades
into a set of suggestions unless something forces two things to hold: the instructions
stay unambiguous, and the verification stays real. Two failure modes show up constantly
once work spans more than a session:

- **The plan drifts.** An implementing agent fills gaps with its own judgment, quietly,
  because nobody told it a gap was a stop rather than a choice.
- **The report isn't evidence.** "I reviewed it and it looks correct" reads exactly
  like "I ran it and it passed" unless the reporting format forces a difference.

The protocol closes both: a document set that can't be casually merged back into prose,
and a verification discipline built around negative controls. For anything that guards
money, permissions, or privacy, the Executor removes the protection, watches the check
fail, restores it, and watches the check pass. A check never seen failing has not been
verified.

It came out of running a real schema migration this way, over many days, and writing
down what broke, including two cases where the Auditor's own order was the thing that
was wrong, not the implementation. `SKILL.md` carries the rule that came out of each
one.

## What's in this repo

- **`SKILL.md`** — the protocol. Written to be loaded directly by an agent (Claude Code,
  a similar tool, or read by a person) and to work without any project-specific content
  stripped in first.
- **`auditkit`** — a Python CLI for the parts of this that are checklist work, not
  judgment.
- **`src/auditkit/templates/`** — the starting shape of the three documents the
  protocol produces.

## Install

```bash
git clone https://github.com/tBeltty/auditor-executor-protocol.git
cd auditor-executor-protocol
pip install -e .
```

No dependencies beyond the Python standard library — it runs against any project,
regardless of what that project is written in.

## Quickstart

```bash
auditkit init docs/<task-name> --name "<Task Name>"
```

This writes `plan-of-record.md`, `execution-guide.md`, `compliance-log.md`, and an empty
`annexes/` directory. Read `SKILL.md` for what belongs in each, then start writing tasks.

While work is in progress:

```bash
auditkit status docs/<task-name>     # what's open, what's approved
auditkit lint docs/<task-name>       # cross-document consistency
```

When a gate needs a negative control:

```bash
auditkit negcontrol \
  --file server/middleware/auth.js \
  --break-cmd "sed -i '' 's/requireAuth/\/\/requireAuth/' server/middleware/auth.js" \
  --test-cmd "npm test -- auth.test.js"
```

This backs the file up, applies the break, runs the test and expects it to fail, restores
the file from the backup, runs the test again and expects it to pass, then prints the
whole transcript in a shape that pastes directly into a compliance log entry.

## The two roles

| | Auditor | Executor |
|---|---|---|
| Owns | Instructions, gates, verdicts | Implementation, evidence |
| Never | Writes feature code | Redesigns, or decides scope |
| Output | Task expansions, verdicts, remediation orders | Working code, pasted command output |

Full rules — how to write a task, how to write a gate, how to audit instead of just
reading a report, the verdict vocabulary, and the failure modes this has actually hit —
are in [`SKILL.md`](SKILL.md).

## The CLI

| Command | Does |
|---|---|
| `auditkit init <dir>` | Scaffold the four-document set from templates |
| `auditkit lint <dir>` | Cross-check task IDs between the guide and the log, flag gates with no stated negative control, flag near-duplicate paragraphs left by append-only logging, warn when a phase's annex count signals an under-verified plan |
| `auditkit negcontrol` | Run the backup / break / test / restore / test sequence and print a paste-ready transcript |
| `auditkit status <dir>` | Tally verdicts in the compliance log and list what's still open |

Every command works on plain Markdown files. Nothing is stored outside the directory you
point it at.

## Using this with an agent

Point your agent's skill loader at `SKILL.md` — for Claude Code, copy it to
`.claude/skills/auditor-executor-protocol/SKILL.md` in the target project, or reference
this repo directly if your tooling supports remote skills. The document itself has no
dependency on this repo; it's self-contained.

## Contributing

Open an issue if you hit a failure mode this protocol doesn't yet name, or a case where
`auditkit`'s behavior doesn't match what `SKILL.md` says it should do.

## License

MIT — see [`LICENSE`](LICENSE).

---

Made with ♥️ by [tBelt](https://github.com/tBeltty).
