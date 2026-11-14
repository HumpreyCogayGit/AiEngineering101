"""EXER001 stretch goal 2 — show where each setting came from.

    uv run python EXER001/stretch/goal2_setting_sources.py
    AICOURSE_REQUEST_TIMEOUT=5 uv run python EXER001/stretch/goal2_setting_sources.py

A setting can come from three places, in this order of precedence:
a real environment variable, the `.env` file, or the default in
`aicourse/settings.py`. When a value is not the one you wrote in `.env`,
this tells you why.
"""

from __future__ import annotations

import os

from dotenv import dotenv_values

from aicourse.settings import ENV_FILE, Settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "check_setup.py")


def setting_sources() -> dict[str, str]:
    """Map every variable name the course reads to "environment", ".env" or "default"."""
    in_file = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}
    sources: dict[str, str] = {}
    for field in Settings.model_fields.values():
        name = field.alias
        if not name:
            continue
        if name in os.environ:  # real environment variables win over .env
            sources[name] = "environment"
        elif name in in_file:
            sources[name] = ".env"
        else:
            sources[name] = "default"
    return sources


def main() -> None:
    settings = base.load_config()
    print(f"Provider: {settings.provider_label}\n")
    # Only the selected provider's block is read, so only show that one.
    other = "OLLAMA_" if settings.provider == "azure" else "AZURE_"
    for name, source in setting_sources().items():
        if not name.startswith(other):
            print(f"  {name:<36} {source}")
    print("\nNames are shown, values are not: this output is safe to paste into a bug report.")


if __name__ == "__main__":
    main()
