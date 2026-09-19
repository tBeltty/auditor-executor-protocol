"""Zero-dependency test runner.

Runs all tests using standard library shims for tmp_path and capsys
when running in pure Python environments without pytest installed.
"""

from __future__ import annotations

import importlib
import inspect
import io
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# Ensure src/ and repo root are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))


class CapsysShim:
    def __init__(self, stdout_io: io.StringIO, stderr_io: io.StringIO) -> None:
        self._stdout_io = stdout_io
        self._stderr_io = stderr_io

    class Output:
        def __init__(self, out: str, err: str) -> None:
            self.out = out
            self.err = err

    def readouterr(self) -> Output:
        out = self._stdout_io.getvalue()
        err = self._stderr_io.getvalue()
        return self.Output(out, err)


def run_tests() -> int:
    test_dir = REPO_ROOT / "tests"
    test_files = sorted(test_dir.glob("test_*.py"))

    passed = 0
    failed = 0

    for test_file in test_files:
        module_name = f"tests.{test_file.stem}"
        module = importlib.import_module(module_name)
        test_funcs = [
            (name, func)
            for name, func in inspect.getmembers(module, inspect.isfunction)
            if name.startswith("test_")
        ]

        for name, func in test_funcs:
            sig = inspect.signature(func)
            params = sig.parameters

            try:
                with tempfile.TemporaryDirectory(prefix="auditkit-test-") as tmp_dir:
                    tmp_path = Path(tmp_dir)
                    stdout_buf = io.StringIO()
                    stderr_buf = io.StringIO()
                    capsys = CapsysShim(stdout_buf, stderr_buf)

                    kwargs = {}
                    if "tmp_path" in params:
                        kwargs["tmp_path"] = tmp_path
                    if "capsys" in params:
                        kwargs["capsys"] = capsys

                    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                        func(**kwargs)

                print(f"PASS {test_file.name}::{name}")
                passed += 1
            except Exception as e:
                print(f"FAIL {test_file.name}::{name} -> {e}")
                failed += 1

    total = passed + failed
    print(f"\nRan {total} test(s): {passed} passed, {failed} failed.")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(run_tests())
