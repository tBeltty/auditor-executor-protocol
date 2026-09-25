"""Run the backup -> break -> test (expect fail) -> restore -> test (expect pass)
sequence this protocol requires for every gate that guards a security, privacy, or
financial-integrity boundary, and print a paste-ready transcript.

This replaces doing the same four shell commands by hand, which is where the sequence
tends to get shortened under time pressure.

With --file, the backup is the source of truth: whatever --restore-cmd does, the file
must end byte-identical to the backup, or it is restored from the backup. The backup is
deleted only once the file is verified identical; otherwise its path is printed.
"""

from __future__ import annotations

import filecmp
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_EXIT = 124


def _kill_tree(proc: subprocess.Popen[str]) -> None:
    """Kill the shell and every process it started, not only the shell."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False
        )
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _run(cmd: str, timeout: float | None = None) -> tuple[int, str]:
    # Each command runs in its own process group (session), so a timeout can kill the
    # processes it started: a timed-out break must not keep changing the file afterwards.
    if os.name == "nt":
        group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}  # type: ignore[attr-defined]
    else:
        group = {"start_new_session": True}
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        **group,
    )
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        proc.communicate()
        return TIMEOUT_EXIT, f"(timed out after {timeout:g}s)"
    return proc.returncode, output or ""


def _is_identical(file_path: str, backup_path: Path) -> bool:
    try:
        return Path(file_path).is_file() and filecmp.cmp(file_path, str(backup_path), shallow=False)
    except OSError:
        return False


def _ensure_restored(
    file_path: str, backup_path: Path, transcript: list[str], after_restore_cmd: bool
) -> bool:
    """Leave file_path byte-identical to the backup, whatever the break or restore did
    (modified, deleted, moved). Returns False only if that could not be achieved."""
    if _is_identical(file_path, backup_path):
        transcript.append(f"$ {file_path} is byte-identical to the backup")
        return True
    if after_restore_cmd:
        transcript.append("WARNING: --restore-cmd did not restore the file; using the backup.")
    try:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target)
    except OSError as error:
        transcript.append(f"ERROR: could not restore {file_path} from the backup: {error}")
        return False
    identical = _is_identical(file_path, backup_path)
    transcript.append(
        f"$ restored {file_path} from backup "
        + ("(byte-identical)" if identical else "- WARNING: still differs from backup")
    )
    return identical


def run(
    test_cmd: str,
    break_cmd: str | None = None,
    file_path: str | None = None,
    restore_cmd: str | None = None,
    timeout: float | None = None,
) -> int:
    if not break_cmd and not restore_cmd:
        print("error: pass --break-cmd, or --restore-cmd for a break you apply yourself.")
        return 2
    if not file_path and not restore_cmd:
        print("error: without --file, --restore-cmd is required (nothing to copy back).")
        return 2

    tmp_dir: Path | None = None
    backup_path: Path | None = None
    transcript: list[str] = []
    # With --file, nothing counts as restored until the file is verified identical.
    restored_ok = not file_path

    try:
        if file_path:
            src = Path(file_path)
            if not src.exists():
                print(f"error: {file_path} does not exist.")
                return 2
            tmp_dir = Path(tempfile.mkdtemp(prefix="auditkit-negcontrol-"))
            backup_path = tmp_dir / src.name
            shutil.copy2(src, backup_path)
            transcript.append(f"$ backed up {file_path} -> {backup_path}")

        broke_as_expected = False
        try:
            if break_cmd:
                transcript.append(f"$ {break_cmd}")
                code, out = _run(break_cmd, timeout)
                transcript.append(out.rstrip("\n"))
                if code != 0:
                    print(
                        f"warning: break command exited {code}. Continuing, but check it did what you meant."
                    )

            transcript.append(f"$ {test_cmd}   # expect FAILURE")
            code1, out1 = _run(test_cmd, timeout)
            transcript.append(out1.rstrip("\n"))
            broke_as_expected = code1 != 0
            transcript.append(f"(exit {code1})")
        finally:
            if restore_cmd:
                transcript.append(f"$ {restore_cmd}")
                restore_code, out = _run(restore_cmd, timeout)
                transcript.append(out.rstrip("\n"))
                transcript.append(f"(restore exit {restore_code})")
                restored_ok = restore_code == 0
            if file_path and backup_path is not None:
                restored_ok = _ensure_restored(
                    file_path, backup_path, transcript, after_restore_cmd=bool(restore_cmd)
                )

        transcript.append(f"$ {test_cmd}   # expect SUCCESS")
        code2, out2 = _run(test_cmd, timeout)
        transcript.append(out2.rstrip("\n"))
        restored_to_green = code2 == 0
        transcript.append(f"(exit {code2})")

        print("\n".join(transcript))
        print()

        if not restored_ok:
            print("FAIL: the protection was not restored. Check the tree before continuing.")
            return 1
        if not broke_as_expected:
            print(
                "FAIL: the test did not fail when the protection was removed. "
                "Either the break command didn't do what you meant, or the protection isn't real."
            )
            return 1
        if not restored_to_green:
            print("FAIL: the test did not return to passing after restore. The tree may be dirty.")
            return 1

        print(
            "OK: negative control verified — the check fails without the protection and passes with it."
        )
        return 0
    finally:
        if tmp_dir and tmp_dir.exists():
            if restored_ok:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            else:
                print(f"Backup kept at {backup_path}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit negcontrol")
    parser.add_argument(
        "--file", dest="file_path", default=None, help="file to back up and restore"
    )
    parser.add_argument(
        "--break-cmd",
        dest="break_cmd",
        default=None,
        help="shell command that removes the protection",
    )
    parser.add_argument(
        "--test-cmd",
        dest="test_cmd",
        required=True,
        help="shell command that should fail without the protection",
    )
    parser.add_argument(
        "--restore-cmd",
        dest="restore_cmd",
        default=None,
        help="shell command to restore; with --file, the backup still wins if the file differs",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="seconds allowed per command (default: no limit)",
    )
    args = parser.parse_args(argv)
    return run(args.test_cmd, args.break_cmd, args.file_path, args.restore_cmd, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
