"""Run the backup -> break -> test (expect fail) -> restore -> test (expect pass)
sequence this protocol requires for every gate that guards a security, privacy, or
financial-integrity boundary, and print a paste-ready transcript.

This replaces doing the same four shell commands by hand, which is where the sequence
tends to get shortened under time pressure.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(cmd: str) -> tuple[int, str]:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output


def run(
    test_cmd: str,
    break_cmd: str | None = None,
    file_path: str | None = None,
    restore_cmd: str | None = None,
) -> int:
    if not break_cmd and not restore_cmd:
        print("error: pass --break-cmd, or --restore-cmd for a break you apply yourself.")
        return 2
    if file_path and not restore_cmd:
        # default restore = copy the backup back over the file
        pass
    elif not file_path and not restore_cmd:
        print("error: without --file, --restore-cmd is required (nothing to copy back).")
        return 2

    backup_path = None
    transcript = []

    if file_path:
        src = Path(file_path)
        if not src.exists():
            print(f"error: {file_path} does not exist.")
            return 2
        tmp_dir = Path(tempfile.mkdtemp(prefix="auditkit-negcontrol-"))
        backup_path = tmp_dir / src.name
        shutil.copy2(src, backup_path)
        transcript.append(f"$ backed up {file_path} -> {backup_path}")

    if break_cmd:
        transcript.append(f"$ {break_cmd}")
        code, out = _run(break_cmd)
        transcript.append(out.rstrip("\n"))
        if code != 0:
            print(f"warning: break command exited {code}. Continuing, but check it did what you meant.")

    transcript.append(f"$ {test_cmd}   # expect FAILURE")
    code1, out1 = _run(test_cmd)
    transcript.append(out1.rstrip("\n"))
    broke_as_expected = code1 != 0
    transcript.append(f"(exit {code1})")

    if file_path and not restore_cmd:
        shutil.copy2(backup_path, file_path)
        transcript.append(f"$ restored {file_path} from backup (diff -q should show no output)")
        rc, diff_out = _run(f"diff -q {file_path!r} {str(backup_path)!r}")
        transcript.append((diff_out or "(no output — byte-identical)").rstrip("\n"))
    elif restore_cmd:
        transcript.append(f"$ {restore_cmd}")
        _, out = _run(restore_cmd)
        transcript.append(out.rstrip("\n"))

    transcript.append(f"$ {test_cmd}   # expect SUCCESS")
    code2, out2 = _run(test_cmd)
    transcript.append(out2.rstrip("\n"))
    restored_to_green = code2 == 0
    transcript.append(f"(exit {code2})")

    print("\n".join(transcript))
    print()

    if not broke_as_expected:
        print(
            "FAIL: the test did not fail when the protection was removed. "
            "Either the break command didn't do what you meant, or the protection isn't real."
        )
        return 1
    if not restored_to_green:
        print("FAIL: the test did not return to passing after restore. The tree may be dirty.")
        return 1

    print("OK: negative control verified — the check fails without the protection and passes with it.")
    return 0


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit negcontrol")
    parser.add_argument("--file", dest="file_path", default=None, help="file to back up and restore")
    parser.add_argument("--break-cmd", dest="break_cmd", default=None, help="shell command that removes the protection")
    parser.add_argument("--test-cmd", dest="test_cmd", required=True, help="shell command that should fail without the protection")
    parser.add_argument("--restore-cmd", dest="restore_cmd", default=None, help="shell command to restore, instead of copying --file back")
    args = parser.parse_args(argv)
    return run(args.test_cmd, args.break_cmd, args.file_path, args.restore_cmd)


if __name__ == "__main__":
    sys.exit(main())
