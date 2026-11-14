"""Helper for the stretch-goal reference code in `EXERxxx/stretch/`.

Stretch goals extend an exercise after its checks pass. Their reference code
builds on the reference solution instead of copying it:

    from aicourse.stretch import solution_module

    base = solution_module(__file__, "chatbot.py")     # EXER005/solution/chatbot.py
    convo = base.Conversation()

Because the stretch code lives in its own folder and only imports the
solution, `check.py` keeps checking exactly what it checked before.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def solution_path(stretch_file: str, exercise: str | None = None) -> Path:
    """Put an exercise's `solution/` folder on `sys.path` and return it.

    For solutions made of several files that import each other by name
    (EXER037): after this call, `import assistant` finds the reference one,
    and every file sees the same module objects.
    """
    exercise_dir = Path(stretch_file).resolve().parent.parent
    if exercise:
        exercise_dir = exercise_dir.parent / exercise
    code_dir = exercise_dir / "solution"
    if not code_dir.is_dir():
        raise FileNotFoundError(f"No reference solution folder at {code_dir}")
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    return code_dir


def solution_module(stretch_file: str, filename: str, exercise: str | None = None) -> ModuleType:
    """Import `solution/<filename>` of the exercise that `stretch_file` belongs to.

    `exercise` names another exercise folder ("EXER004") when a goal connects
    two exercises. The solution folder is put on `sys.path`, so the module's
    own sibling imports (`from tools import ...`) keep working.
    """
    code_dir = solution_path(stretch_file, exercise)
    file = code_dir / filename
    if not file.exists():
        raise FileNotFoundError(f"No reference solution at {file}")
    name = f"_solution_{code_dir.parent.name}_{file.stem}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
