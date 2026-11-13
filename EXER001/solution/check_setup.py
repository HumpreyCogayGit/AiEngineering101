"""EXER001 — Setup and First Check (reference solution)."""

import sys

from aicourse.settings import ConfigError, Settings, get_settings


def python_version_ok() -> bool:
    """Return True when the running Python is 3.12 or newer."""
    return sys.version_info >= (3, 12)


def masked_key(key: str) -> str:
    """Hide a secret so it is safe to print.

    "abcd1234efgh5678" -> "abcd****5678"
    Keys of 12 characters or fewer are fully hidden: "****".
    """
    if len(key) <= 12:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def load_config() -> Settings:
    """Load the course settings from the root .env file."""
    return get_settings()


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
