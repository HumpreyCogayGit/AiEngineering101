"""Validate the self-check quizzes of the lecture site.

    uv run python check_quizzes.py

The quizzes are data in Lecture/assets/js/quizzes.js. This script reads that
file (no browser and no Node.js needed) and checks that:

- every lecture in the course manifest (course.js) has a quiz, and no quiz
  belongs to a lecture that does not exist
- each quiz has 4 questions (5 for the longer lectures listed in LONGER)
- every question has a text, exactly 4 distinct options, an answer index in
  range, and a non-empty explanation for every option
- every lecture page loads quizzes.js and has the "Check Yourself" section,
  between Discussion and Further Reading

check_all.py runs it as part of the full course check.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JS_DIR = ROOT / "Lecture" / "assets" / "js"
LECTURES = ROOT / "Lecture" / "lectures"

QUESTIONS = 4
QUESTIONS_LONGER = 5
LONGER = {9, 11, 23, 24, 29, 36}  # lectures with more ground to cover
OPTIONS = 4


def js_object_to_json(source: str) -> str:
    """Turn the object literal of quizzes.js into JSON.

    The file is data only, so three differences from JSON are enough to
    handle: comments, unquoted keys and trailing commas. Strings are copied
    untouched, so a `//` or a `key:` inside a question is safe.
    """
    out: list[str] = []
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        if ch == '"':  # a string: copy up to the closing quote
            j = i + 1
            while source[j] != '"':
                j += 2 if source[j] == "\\" else 1
            out.append(source[i : j + 1])
            i = j + 1
        elif source.startswith("//", i):
            i = source.find("\n", i)
            i = n if i == -1 else i
        elif source.startswith("/*", i):
            i = source.index("*/", i) + 2
        else:
            out.append(ch)
            i += 1
    text = "".join(out)
    text = re.sub(r"([{,]\s*)([A-Za-z_]\w*|\d+)\s*:", r'\1"\2":', text)  # keys
    text = re.sub(r",(\s*[}\]])", r"\1", text)  # trailing commas
    return text


def load_quizzes() -> dict[int, list[dict]]:
    source = (JS_DIR / "quizzes.js").read_text(encoding="utf-8")
    # The assignment itself, not the example in the header comment.
    start = re.search(r"^window\.QUIZZES\s*=", source, flags=re.M)
    if not start:
        raise ValueError("no `window.QUIZZES = {...}` assignment found")
    body = source[source.index("{", start.end()) : source.rindex("}") + 1]
    # Strings in the data file are written with double quotes; keep it that way.
    return {int(k): v for k, v in json.loads(js_object_to_json(body)).items()}


def course_lectures() -> list[int]:
    manifest = (JS_DIR / "course.js").read_text(encoding="utf-8")
    return [int(n) for n in re.findall(r"\{\s*n:\s*(\d+)", manifest)]


def check_question(where: str, item: object) -> list[str]:
    if not isinstance(item, dict):
        return [f"{where}: is not an object"]
    errors: list[str] = []
    extra = set(item) - {"q", "options", "answer", "why"}
    if extra:
        errors.append(f"{where}: unknown keys {sorted(extra)}")
    if not isinstance(item.get("q"), str) or not item["q"].strip():
        errors.append(f"{where}: `q` is missing or empty")
    options = item.get("options")
    if not isinstance(options, list) or len(options) != OPTIONS:
        errors.append(f"{where}: needs exactly {OPTIONS} options")
        return errors
    if any(not isinstance(o, str) or not o.strip() for o in options):
        errors.append(f"{where}: an option is empty")
    elif len({o.strip().lower() for o in options}) != OPTIONS:
        errors.append(f"{where}: two options are the same")
    answer = item.get("answer")
    if isinstance(answer, bool) or not isinstance(answer, int) or not 0 <= answer < OPTIONS:
        errors.append(f"{where}: `answer` must be an index from 0 to {OPTIONS - 1}")
    why = item.get("why")
    if not isinstance(why, list) or len(why) != OPTIONS:
        errors.append(f"{where}: needs one `why` per option ({OPTIONS})")
    elif any(not isinstance(w, str) or not w.strip() for w in why):
        errors.append(f"{where}: an explanation in `why` is empty")
    return errors


def check_page(n: int) -> list[str]:
    page = LECTURES / f"lec{n:03d}.html"
    if not page.exists():
        return [f"lecture {n:03d}: {page.name} does not exist"]
    html = page.read_text(encoding="utf-8")
    errors: list[str] = []
    if "assets/js/quizzes.js" not in html:
        errors.append(f"lecture {n:03d}: the page does not load quizzes.js")
    positions = [html.find(f'<section id="{name}"') for name in ("discussion", "quiz", "reading")]
    if positions[1] == -1 or 'id="quiz-box"' not in html:
        errors.append(f"lecture {n:03d}: the page has no Check Yourself section")
    elif not positions[0] < positions[1] < positions[2]:
        errors.append(f"lecture {n:03d}: Check Yourself must sit between Discussion and Further Reading")
    return errors


def validate() -> tuple[list[str], int, int]:
    quizzes = load_quizzes()
    lectures = course_lectures()
    errors: list[str] = []
    for n in lectures:
        if n not in quizzes:
            errors.append(f"lecture {n:03d}: has no quiz")
            continue
        expected = QUESTIONS_LONGER if n in LONGER else QUESTIONS
        if len(quizzes[n]) != expected:
            errors.append(f"lecture {n:03d}: has {len(quizzes[n])} questions, expected {expected}")
        seen: set[str] = set()
        for i, item in enumerate(quizzes[n], 1):
            where = f"lecture {n:03d}, question {i}"
            errors += check_question(where, item)
            text = item.get("q", "") if isinstance(item, dict) else ""
            if text in seen:
                errors.append(f"{where}: the same question appears twice")
            seen.add(text)
        errors += check_page(n)
    for n in sorted(set(quizzes) - set(lectures)):
        errors.append(f"quiz {n}: no such lecture in course.js")
    questions = sum(len(q) for q in quizzes.values())
    return errors, len(quizzes), questions


def main() -> int:
    try:
        errors, quiz_count, question_count = validate()
    except (OSError, ValueError) as exc:
        print(f"FAIL quizzes.js could not be read as data: {exc}")
        return 1
    for line in errors:
        print(f"FAIL {line}")
    if errors:
        print(f"\n{len(errors)} problem(s) in the quizzes")
        return 1
    print(f"ok   {quiz_count} quizzes, {question_count} questions: every lecture is covered and every question is well formed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
