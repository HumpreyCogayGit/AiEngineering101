"""Run every exercise check in one go.

    uv run python check_all.py              # solutions must pass, starters must fail
    uv run python check_all.py --offline    # skip checks that call the live API (free, fast, CI-friendly)
    uv run python check_all.py 16 17 31     # only these exercises
    uv run python check_all.py --mine       # check YOUR code in every starter/ (a progress report)

This is the course's definition of done, automated: each reference solution
passes its checks and each untouched starter does not.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_check(exercise: Path, *flags: str) -> tuple[bool, str, str]:
    """Return (all passed, 'passed/total', full output) for one check script."""
    proc = subprocess.run(
        [sys.executable, str(exercise / "check.py"), *flags],
        cwd=ROOT, capture_output=True, text=True, timeout=900,
    )
    output = ANSI.sub("", proc.stdout + proc.stderr)
    score = re.search(r"(\d+/\d+) checks passed", output)
    return proc.returncode == 0, score.group(1) if score else "crashed", output


def problems(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if re.match(r"\s+(FAIL|ERROR|TODO)\s", line)]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    offline = ["--offline"] if "--offline" in sys.argv else []
    mine = "--mine" in sys.argv
    wanted = {f"EXER{int(a):03d}" for a in args}
    exercises = sorted(p for p in ROOT.glob("EXER[0-9][0-9][0-9]") if not wanted or p.name in wanted)

    bad: list[str] = []
    started = time.perf_counter()
    for ex in exercises:
        if mine:
            ok, score, _ = run_check(ex, *offline)
            print(f"{ex.name}  {'done' if ok else '    '}  {score}")
            continue
        sol_ok, sol_score, sol_out = run_check(ex, "--solution", *offline)
        # A starter is checked offline: it only has to be incomplete.
        starter_ok, starter_score, _ = run_check(ex, "--offline")
        status = "ok  " if sol_ok and not starter_ok else "FAIL"
        print(f"{status} {ex.name}  solution {sol_score:<7} starter {starter_score}")
        if not sol_ok:
            bad.append(ex.name)
            for line in problems(sol_out):
                print(f"       {line}")
        if starter_ok:
            bad.append(ex.name)
            print("       the untouched starter passes every check: the checks prove nothing")
    if mine:
        return 0
    print(f"\n{len(exercises) - len(set(bad))}/{len(exercises)} exercises OK "
          f"in {time.perf_counter() - started:.0f}s" + (" (offline)" if offline else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
