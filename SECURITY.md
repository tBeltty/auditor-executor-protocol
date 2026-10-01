# Security Policy

## Supported Versions

Only the latest minor release receives security fixes.

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Scope

`auditkit` reads and writes local Markdown files and makes no network calls. `auditkit negcontrol`
runs the shell commands you pass it, with your privileges, by design; that is not a
vulnerability. Reports that matter most: `negcontrol` leaving a file broken or deleting its
backup, `install-skill` writing outside its destination, and `lint` or `status` reporting a
document set as clean or closed when it is not.

## Reporting a Vulnerability

Do not open a public issue. Report it privately through
[GitHub's private vulnerability reporting](https://github.com/tBeltty/auditor-executor-protocol/security/advisories/new),
or by email to `jhonatan@tbelt.online`, with:

- a description of the issue and its impact;
- steps to reproduce or a proof of concept;
- the affected `auditkit` version, Python version, and OS.

You will get an acknowledgment within a week. Fixes are released as a patch version and
credited in `CHANGELOG.md` unless you ask otherwise.
