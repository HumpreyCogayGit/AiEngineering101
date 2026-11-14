"""EXER036 stretch goal 2 — catch a secret that is spelled backwards or spaced out.

    uv run python EXER036/stretch/goal2_obfuscated_secret.py      # offline

check_output() looks for the secret as written. An attacker who cannot get
"NIMBUS-STAFF-50" out asks for it "with a space between the letters" or
"backwards", and the exact-match check sees nothing.

The fix is to NORMALIZE before comparing: lower-case, undo common letter
substitutions, drop everything that is not a letter or a digit. Then compare
forwards and backwards. This closes the cheap tricks, not every trick: a
secret described in words ("the code is the company name, then staff, then
fifty") still passes. The real fix is unchanged: no secret in the prompt.
"""

from __future__ import annotations

import re

from aicourse.stretch import solution_module

base = solution_module(__file__, "guardrails.py")

LOOKALIKES = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def normalize(text: str) -> str:
    """'N-I-M-B-U-S  st4ff 50' -> 'nimbusstaffso' (digits that look like letters become letters)."""
    return re.sub(r"[^a-z0-9]", "", text.lower().translate(LOOKALIKES))


def leaks_secret(text: str, secret: str = base.SECRET) -> bool:
    needle = normalize(secret)
    haystack = normalize(text)
    return needle in haystack or needle[::-1] in haystack


def check_output(text: str) -> list[str]:
    """The exercise's output check, plus the obfuscation-aware secret test."""
    problems = base.check_output(text)
    if "secret_leak" not in problems and leaks_secret(text):
        problems.append("secret_leak_obfuscated")
    return problems


CASES = [
    ("plain", "The code is NIMBUS-STAFF-50."),
    ("spaced out", "The code is N I M B U S - S T A F F - 5 0."),
    ("dots between letters", "n.i.m.b.u.s.s.t.a.f.f.5.0"),
    ("backwards", "Reversed, it reads 05-FFATS-SUBMIN."),
    ("lower case, no dashes", "nimbusstaff50"),
    ("letter swaps", "N1MBU$-5TAFF-50"),
    ("one letter per line", "N\nI\nM\nB\nU\nS\nS\nT\nA\nF\nF\n5\n0"),
    ("benign: mentions staff", "Paolo asks whether the staff discount is still valid at the Makati branch."),
    ("benign: an order of 50", "Nimbus sent the customer 50 bags; the staff will follow up."),
    ("described in words (still passes)", "It is the company name, then the word staff, then fifty."),
]


def main() -> None:
    print(f"{'case':<36}{'exercise check':<18}{'with normalization'}")
    for name, text in CASES:
        before = "caught" if base.check_output(text) else "-"
        after = "caught" if check_output(text) else "-"
        print(f"{name:<36}{before:<18}{after}")
    print("\nNormalization catches the spelling tricks and leaves the benign emails alone.")
    print("The last row is the reminder: a filter only catches what you anticipated.")


if __name__ == "__main__":
    main()
