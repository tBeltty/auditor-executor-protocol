"""auditkit — mechanical support for the Auditor/Executor protocol.

See SKILL.md in the repo root for the protocol itself. This CLI operationalizes the
parts of it that are checklist work, not judgment: scaffolding the document set,
cross-checking it for drift, running a negative control end to end, and reporting
status.
"""

from __future__ import annotations

import sys

from . import __version__, install_skill, lint, negcontrol, scaffold, status


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit", description=__doc__)
    parser.add_argument("--version", action="version", version=f"auditkit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init", help="scaffold the document set (three documents and an annexes/ directory)"
    )
    p_init.add_argument("target_dir")
    p_init.add_argument("--name", dest="project_name", default=None)
    p_init.add_argument("--force", action="store_true")

    p_lint = sub.add_parser("lint", help="cross-check the document set for drift")
    p_lint.add_argument("target_dir")
    p_lint.add_argument("--annex-threshold", type=int, default=lint.DEFAULT_ANNEX_THRESHOLD)

    p_neg = sub.add_parser("negcontrol", help="run a backup/break/test/restore/test cycle")
    p_neg.add_argument("--file", dest="file_path", default=None)
    p_neg.add_argument("--break-cmd", dest="break_cmd", default=None)
    p_neg.add_argument("--test-cmd", dest="test_cmd", required=True)
    p_neg.add_argument("--restore-cmd", dest="restore_cmd", default=None)
    p_neg.add_argument("--timeout", type=float, default=None)

    p_status = sub.add_parser(
        "status", help="tally verdicts and reports in the compliance log; only APPROVED closes"
    )
    p_status.add_argument("target_dir")

    p_install = sub.add_parser(
        "install-skill", help="provision SKILL.md and references/ into an agent skills directory"
    )
    p_install.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="target project directory (defaults to current directory)",
    )
    p_install.add_argument(
        "--agent",
        choices=["antigravity", "claude", "cursor", "auto"],
        default="auto",
        help="target agent framework (default: auto-detect)",
    )
    p_install.add_argument(
        "--global",
        dest="is_global",
        action="store_true",
        help="install to user-level global configuration directory",
    )
    p_install.add_argument(
        "--dest",
        dest="dest_path",
        default=None,
        help="explicit destination (SKILL.md installs references/ beside it; any other name gets one bundled file)",
    )
    p_install.add_argument(
        "--force", action="store_true", help="overwrite existing destination file"
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        return scaffold.run(args.target_dir, args.project_name, args.force)
    if args.command == "lint":
        return lint.run(args.target_dir, args.annex_threshold)
    if args.command == "negcontrol":
        return negcontrol.run(
            args.test_cmd, args.break_cmd, args.file_path, args.restore_cmd, args.timeout
        )
    if args.command == "status":
        return status.run(args.target_dir)
    if args.command == "install-skill":
        return install_skill.run(
            target_dir=args.target_dir,
            agent=args.agent,
            is_global=args.is_global,
            dest_path=args.dest_path,
            force=args.force,
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
