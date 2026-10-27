# Tool and model provenance for the agent runs

Compiled 2026-10-26 from records on the machine where the runs were made. Nothing here is from memory. Every row names its source and the query that produced it. Times are local (UTC-5) and the runs took place on 2026-10-25 unless stated.

The versions were **not recorded by the harness at run time**. They are recovered afterwards from the tools' own records. Where a record is missing the row says so.

## Summary

| Experiment | Tool | Version | Model identifier | Evidence |
| :-- | :-- | :-- | :-- | :-- |
| Part B (10 sessions) | Claude Code | 2.1.308 | `claude-sonnet-5-5` | Claude Code sub-agent transcripts |
| Part C (12 sessions) | Claude Code | 2.1.308 | `claude-sonnet-5-5` | same |
| Pilot 1 | OpenCode | 2.1.3 | variant of the same model release, provider `opencode` (see the last section) | OpenCode `session_v2` |
| Pilot 2 | OpenCode | 2.1.3 | `deepseek-v4.1-flash`, provider `opencode-go` | OpenCode `session_v2` |
| Pilot 3, DeepSeek (41 sessions) | OpenCode | 2.1.4 | `deepseek-v4.1-flash` | OpenCode `session_v2`, driver log |
| Pilot 3, GLM (37 sessions) | OpenCode | 2.1.4 | `glm-5.3-flash` | same |
| Pilot 3, Qwen (39 sessions) | OpenCode | 2.1.3 for 12 sessions, 2.1.4 for 27 | `qwen3.8-flash` | same |
| Pilots 1 to 3 | Orca | not recorded per run (see below) | not applicable | Orca logs |

## Parts B and C: Claude Code

Source: transcripts under `~/.claude/projects/**/subagents/*.jsonl`, fields `version` and `message.model`.

- 22 sub-agent sessions were launched between 00:28 and 00:29 on 2026-10-25, which matches the 10 sessions of Part B plus the 12 of Part C.
- All 22 carry Claude Code `2.1.308` and the model identifier `claude-sonnet-5-5`.
- Attribution: 10 sessions match the Part B prompt text (`14.2` and `webhook`), 8 match Part C module words, and 4 were launched in the same minute with text that did not match either keyword set. Those 4 are attributed by timing only.
- The `claude` binary on this machine's PATH reports `2.1.296` (installed with nvm), which differs from `2.1.308` in the transcripts. At least two Claude Code installations were in use on that day.

## Pilots 1 to 3: OpenCode

Source: the OpenCode database `~/.local/share/opencode/opencode.db`, table `session_v2`, fields `version`, `model`, `title`, `time_created`, read from a copy opened read-only. The driver logs in `benchmarks/results/` give the launch times of each model block.

| Window (2026-10-25) | Sessions | Model identifier as stored | OpenCode | Attribution |
| :-- | :--: | :-- | :--: | :-- |
| 00:59 | 1 | `deepseek-v4.1-flash` | 2.1.3 | title `exec-U-neutral-1`, one session before the block below |
| 01:00 to 01:44 | 47 | `deepseek-v4.1-flash-free` | 2.1.3 | titles `exec-U-neutral-1`, `exec-AE-neutral-2`, and so on, the Pilot 1 naming |
| 01:44 to 08:16 | 85 | `deepseek-v4.1-flash` | 2.1.3 | Pilot 2 from 01:44 (titles `CRM ...`, `AE-neutral-1 guard audit`) and the first DeepSeek block of Pilot 3 (documented in `benchmarks/pilot/PILOT3_DEVIATIONS.md`) |
| 07:18 | 1 | `qwen3.8-flash` | 2.1.3 | before the driver's first Qwen launch (08:25:27), not counted |
| 08:25 to 08:57 | 12 | `qwen3.8-flash` | 2.1.3 | Pilot 3 Qwen |
| 09:20 to 11:01 | 27 | `qwen3.8-flash` | 2.1.4 | Pilot 3 Qwen |
| 11:11 to 12:41 | 37 | `glm-5.3-flash` | 2.1.4 | Pilot 3 GLM, equal to the 37 in `pilot3_model_check_glm.json` |
| 12:49 to 13:19 | 41 | `deepseek-v4.1-flash` | 2.1.4 | Pilot 3 DeepSeek rerun, equal to the 41 in `pilot3_model_check_deepseek-rerun.json` |

- Qwen: 12 + 27 = 39 sessions from the first launch, equal to the 39 in `pilot3_model_check_qwen.json`.
- The upgrade from 2.1.3 to 2.1.4 happened during the Qwen runs: the Homebrew install receipt (`/opt/homebrew/Cellar/opencode/2.1.4/INSTALL_RECEIPT.json`) is dated 09:01, and the last 2.1.3 Qwen session is at 08:57, the first 2.1.4 session at 09:20.
- Pilot 1 is attributed to its sessions by title and time window only. The identifier and the provider (`providerID`) that OpenCode stored for those sessions differ from those stored for Pilots 2 and 3: provider `opencode` for Pilot 1, provider `opencode-go` for Pilots 2 and 3. The last section compares the two models.
- Duration: the Pilot 1 sessions were launched from 01:00:11 and the last one ended at 01:47:28 (about 47 minutes, excluding 9 sessions that were reopened after 03:00). Pilot 2 took 55 minutes by its driver log (01:44:21 to 02:39:15). Pilot 1 reached the ceiling (every run killed every behavior-changing mutant), so it feeds no inference in the paper. The paper names the model as `DeepSeek 4.1 Flash` for both pilots and gives the identifier read from the records for Pilot 2 and Pilot 3.
- The OpenCode release installed by Homebrew is built from `https://github.com/anomalyco/opencode` at tag `v2.1.4` (commit `68bc26b7da1990ce10ffecfbc1e09eb13aa5d824`). Tag `v2.1.3` is commit `bb25a2f4a3f3f04d7c344bec0c0574ea3510b3b1`. These tags exist in the repository; the GitHub "Releases" page lists a separate 1.x line (latest `v1.19.4`, 2026-10-22).
- Tokens: `session_v2` stores `tokens_input`, `tokens_output`, `tokens_reasoning`, and cache columns for every session. The result files of the pilots do not link sessions to arms, so the paper does not report cost. A future analysis needs the session-to-run mapping.

## Orca

Orca launched the sessions. Its version at the time of each run was not recorded by the harness.

- Installed now: `1.4.240` (`Orca.app/Contents/Info.plist`, `orca --version`, and the `version` field of the current trace log). The app bundle was last modified on 2026-10-25 at 03:25.
- Release dates from the project's GitHub releases: `v1.4.239` on 2026-10-24 07:10 UTC, `v1.4.240` on 2026-10-25 04:02 UTC, `v1.4.241` on 2026-10-26 03:48 UTC.
- The Orca daemon log (`~/Library/Application Support/orca/logs/daemon.log`) records startups with a protocol number: 43 until 2026-10-25 07:09 local, then 51 from the startup at 09:36 local. The protocol change shows that the Orca process was replaced during the Qwen runs. The log does not name an application version.
- Therefore the Orca version used for Pilots 1 and 2 and for the early part of Pilot 3 is not recoverable from these records.

## Limits

- Session counts and attributions come from titles, models, and times. They were not cross-checked against the run directories beyond the counts that match the model-check files.
- The first DeepSeek block of Pilot 3 and one earlier Qwen session fall inside the windows above and are not part of the reported runs.
- For future runs, record `--version` of Claude Code, OpenCode, and Orca, the model identifier, and the tool's commit or tag in every result file at launch.

## Is the Pilot 1 model the same as in Pilots 2 and 3?

Sources, fetched 2026-10-26: the public model catalog `https://models.dev/api.json` (providers `opencode` and `opencode-go`), and the OpenCode documentation pages `https://opencode.ai/docs/zen/` and `https://opencode.ai/docs/go/`. `opencode models` on the same machine lists `opencode/deepseek-v4.1-flash-free` and `opencode-go/deepseek-v4.1-flash`, which agrees with the catalog. It was not verified that OpenCode itself reads this catalog.

| Catalog entry | Name | Family | Release date | Open weights | Context limit | Output limit | Input modalities |
| :-- | :-- | :-- | :--: | :--: | :--: | :--: | :-- |
| `opencode-go/deepseek-v4.1-flash` (Pilots 2 and 3) | DeepSeek V4.1 Flash | `deepseek-flash` | 2026-09-10 | yes | 1,000,000 | 384,000 | text, image |
| `opencode/deepseek-v4.1-flash` (pay per use, not used in the runs) | DeepSeek V4.1 Flash | `deepseek-flash` | 2026-09-10 | yes | 1,000,000 | 384,000 | text, image |
| `opencode/deepseek-v4.1-flash-free` (Pilot 1) | DeepSeek V4.1 Flash Free | `deepseek-flash` | 2026-09-10 | yes | 200,000 | 32,000 | text, image |

- What the sources establish: the three entries share the name, family, release date, and open-weights status. The Pilot 1 entry has smaller context and output limits and a zero price. The Zen documentation says that the provider of that entry follows a zero-retention policy and does not use data for training.
- What they do not establish: that the weights served are identical. None of the pages states it.
- Effect on the paper: Pilot 1 reached the ceiling and feeds no inference. The 32,000-token output limit was not checked against the Pilot 1 transcripts.
