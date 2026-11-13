"""EXER001 — Setup and First Check.

Complete the three TODO functions, then run:
    uv run python EXER001/starter/check_setup.py
    uv run python EXER001/check.py
"""

import sys

from aicourse.settings import ConfigError, Settings, get_settings


def python_version_ok() -> bool:
    """Return True when the running Python is 3.12 or newer.

    Hint: `sys.version_info` is a tuple you can compare, e.g. sys.version_info >= (3, 12)
    """
    # TODO: replace the line below with your implementation
    raise NotImplementedError("python_version_ok")


def masked_key(key: str) -> str:
    """Hide a secret so it is safe to print.

    "abcd1234efgh5678" -> "abcd****5678"
    Keys of 12 characters or fewer are fully hidden: "****".

    Hint: string slicing — key[:4] is the first 4 characters, key[-4:] the last 4.
    """
    # TODO: replace the line below with your implementation
    raise NotImplementedError("masked_key")


def load_config() -> Settings:
    """Load the course settings from the root .env file.

    Hint: one line — call get_settings() (already imported above) and return the result.
    """
    # TODO: replace the line below with your implementation
    raise NotImplementedError("load_config")


def main() -> None:
    print(f"Python {sys.version.split()[0]}  ->  {'OK' if python_version_ok() else 'TOO OLD'}")
    try:
        settings = load_config()
    except ConfigError as exc:
        print(exc)
        sys.exit(1)
    print(f"Provider        : {settings.provider_label}")
    print(f"Endpoint        : {settings.endpoint}")
    print(f"API base URL    : {settings.base_url}")
    print(f"Chat model      : {settings.chat_model}")
    print(f"Embedding model : {settings.embedding_model}")
    print(f"API key         : {masked_key(settings.api_key.get_secret_value())}")
    print("\nConfiguration looks good. Next: EXER002.")


if __name__ == "__main__":
    main()
