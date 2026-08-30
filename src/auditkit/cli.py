"""auditkit — mechanical support for the Auditor/Executor protocol.

See SKILL.md in the repo root for the protocol itself. This CLI operationalizes the
parts of it that are checklist work, not judgment: scaffolding the document set,
cross-checking it for drift, running a negative control end to end, and reporting
status.
"""
from __future__ import annotations

import sys

from . import lint, negcontrol, scaffold, status
from . import __version__


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit", description=__doc__)
    parser.add_argument("--version", action="version", version=f"auditkit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold the four-document set")
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

    p_status = sub.add_parser("status", help="tally verdicts in the compliance log")
    p_status.add_argument("target_dir")

    args = parser.parse_args(argv)

    if args.command == "init":
        return scaffold.run(args.target_dir, args.project_name, args.force)
    if args.command == "lint":
        return lint.run(args.target_dir, args.annex_threshold)
    if args.command == "negcontrol":
        return negcontrol.run(args.test_cmd, args.break_cmd, args.file_path, args.restore_cmd)
    if args.command == "status":
        return status.run(args.target_dir)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
