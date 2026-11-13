"""EXER001 checks. Run from the repo root:  uv run python EXER001/check.py"""

import subprocess

from aicourse.check import Checker
from aicourse.settings import ENV_FILE, ROOT_DIR

checker = Checker(__file__, offline_settings=False)  # these checks are about your real .env
mod = checker.load("check_setup.py")


@checker.check("python_version_ok() returns True on this machine")
def _():
    assert mod.python_version_ok() is True


@checker.check("masked_key() keeps first 4 and last 4 characters")
def _():
    assert mod.masked_key("abcd1234efgh5678") == "abcd****5678", mod.masked_key("abcd1234efgh5678")


@checker.check("masked_key() fully hides short keys")
def _():
    assert mod.masked_key("short") == "****"
    assert mod.masked_key("exactly12chr") == "****"


@checker.check(".env file exists at the repository root  [needs .env]")
def _():
    assert ENV_FILE.exists(), "Run: cp .env.example .env  and fill in your values"


@checker.check(".env is ignored by git (never commit secrets)")
def _():
    gitignore = (ROOT_DIR / ".gitignore").read_text()
    assert ".env" in gitignore.splitlines(), ".env is missing from .gitignore"
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".env"], cwd=ROOT_DIR, capture_output=True
    )
    # returncode 0 = ignored; 128 = not a git repo (fine, .gitignore line is enough)
    assert result.returncode in (0, 128), "git does not ignore .env"


@checker.check("load_config() returns valid settings  [needs .env]")
def _():
    settings = mod.load_config()
    assert settings.endpoint.startswith("http"), "endpoint should be a URL"
    assert settings.base_url.endswith("/v1/"), settings.base_url
    assert settings.chat_model, "the chat model name is empty"
    assert settings.embedding_model, "the embedding model name is empty"


checker.run()
