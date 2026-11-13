"""Tiny test runner used by every `EXERxxx/check.py`.

Usage inside a check script:

    from aicourse.check import Checker

    checker = Checker(__file__)           # knows which exercise it belongs to
    mod = checker.load("main.py")         # imports starter/main.py (or solution/main.py)

    @checker.check("add() returns the sum")
    def _():
        assert mod.add(2, 3) == 5

    checker.run()

Run it from the repository root:

    uv run python EXER002/check.py              # checks YOUR code in starter/
    uv run python EXER002/check.py --solution   # checks the reference solution
    uv run python EXER002/check.py --offline    # skip the checks that call the live API
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable

GREEN, RED, YELLOW, DIM, BOLD, RESET = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m",
)


@dataclass
class _Check:
    description: str
    fn: Callable[[], None]


LIVE_TAG = "[live API]"
ENV_TAG = "[needs .env]"  # about your real configuration: skipped by --offline
_PLACEHOLDER_ENV = {
    "AICOURSE_PROVIDER": "azure",
    "AZURE_OPENAI_ENDPOINT": "https://offline-check.invalid",
    "AZURE_OPENAI_API_KEY": "offline-check-key",
    "AZURE_OPENAI_CHAT_DEPLOYMENT": "offline-check-model",
}


def _config_error() -> str | None:
    """The configuration problem as text, or None when `.env` is fine."""
    from aicourse.settings import ConfigError, get_settings

    try:
        get_settings()
    except ConfigError as exc:
        return str(exc)
    return None


@contextlib.contextmanager
def _offline(use_placeholders: bool):
    """Run an offline check: no detection calls, and no `.env` needed."""
    from aicourse import llm
    from aicourse.settings import get_settings

    llm._force_supports_temperature = True
    saved: dict[str, str | None] = {}
    if use_placeholders:
        saved = {k: os.environ.get(k) for k in _PLACEHOLDER_ENV}
        os.environ.update(_PLACEHOLDER_ENV)
        get_settings.cache_clear()
    try:
        yield
    finally:
        llm._force_supports_temperature = None
        if use_placeholders:
            for key, old in saved.items():
                if old is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = old
            get_settings.cache_clear()


class Checker:
    def __init__(self, check_file: str, offline_settings: bool = True) -> None:
        # offline_settings=False: the checks are ABOUT your .env (EXER001), so
        # never substitute placeholder settings for a missing one.
        self.offline_settings = offline_settings
        self.exercise_dir = Path(check_file).resolve().parent
        self.use_solution = "--solution" in sys.argv
        self.verbose = "-v" in sys.argv or "--verbose" in sys.argv
        self.offline = "--offline" in sys.argv
        self.target = "solution" if self.use_solution else "starter"
        self.code_dir = self.exercise_dir / self.target
        self._checks: list[_Check] = []
        # Let the exercise code import its sibling modules (e.g. `from tools import ...`).
        sys.path.insert(0, str(self.code_dir))

    # ------------------------------------------------------------------ loading
    def path(self, filename: str) -> Path:
        return self.code_dir / filename

    def load(self, filename: str) -> ModuleType:
        """Import a file from starter/ (or solution/) as a module."""
        file = self.code_dir / filename
        if not file.exists():
            print(f"{RED}Cannot find {file}{RESET}")
            sys.exit(2)
        name = f"_exercise_{self.exercise_dir.name}_{self.target}_{file.stem}"
        spec = importlib.util.spec_from_file_location(name, file)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        sys.modules.setdefault(file.stem, module)
        spec.loader.exec_module(module)
        return module

    # ------------------------------------------------------------------ checks
    def check(self, description: str):
        def decorator(fn: Callable[[], None]):
            self._checks.append(_Check(description, fn))
            return fn
        return decorator

    def run(self) -> None:
        title = f"{self.exercise_dir.name} — checking {self.target}/"
        print(f"\n{BOLD}{title}{RESET}\n{'-' * len(title)}")
        passed = skipped = offline_skipped = 0
        config_error = _config_error()
        for c in self._checks:
            start = time.perf_counter()
            live = LIVE_TAG in c.description
            if self.offline and (live or ENV_TAG in c.description):
                offline_skipped += 1
                print(f"{DIM}  SKIP  {c.description} (--offline){RESET}")
                continue
            if live and config_error:
                skipped += 1
                print(f"{YELLOW}  SKIP {RESET} {c.description}")
                print(f"{DIM}         needs a working .env (see the note below){RESET}")
                continue
            try:
                if live or not self.offline_settings:
                    c.fn()
                else:
                    with _offline(use_placeholders=bool(config_error)):
                        c.fn()
            except NotImplementedError as exc:
                print(f"{YELLOW}  TODO {RESET} {c.description}")
                print(f"{DIM}         not implemented yet: {exc}{RESET}")
            except AssertionError as exc:
                print(f"{RED}  FAIL {RESET} {c.description}")
                if str(exc):
                    print(f"{DIM}         {exc}{RESET}")
                if self.verbose:
                    traceback.print_exc()
            except Exception as exc:  # noqa: BLE001 - we want to report everything
                print(f"{RED}  ERROR{RESET} {c.description}")
                print(f"{DIM}         {type(exc).__name__}: {exc}{RESET}")
                if self.verbose:
                    traceback.print_exc()
            else:
                passed += 1
                secs = time.perf_counter() - start
                print(f"{GREEN}  PASS {RESET} {c.description} {DIM}({secs:.1f}s){RESET}")
        total = len(self._checks) - offline_skipped
        colour = GREEN if passed == total else RED
        print(f"\n{colour}{BOLD}{passed}/{total} checks passed{RESET}")
        if skipped:
            print(f"{YELLOW}{skipped} live check(s) skipped: your configuration is not ready.{RESET}")
            print(f"{DIM}{config_error}{RESET}")
        if passed == total:
            print(f"{GREEN}Exercise complete. Well done!{RESET}\n")
        else:
            print(f"{DIM}Run with -v to see full error tracebacks.{RESET}\n")
        sys.exit(0 if passed == total else 1)
