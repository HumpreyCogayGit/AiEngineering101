"""The single place that reads configuration for the whole course.

Every exercise gets its settings from here:

    from aicourse.settings import get_settings
    settings = get_settings()
    print(settings.chat_deployment)

Values come from the `.env` file at the repository root (or from real
environment variables, which win over `.env`).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The repository root: the folder that contains this `aicourse/` package.
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
DATA_DIR = ROOT_DIR / "data"


class ConfigError(RuntimeError):
    """Raised when `.env` is missing or a setting is invalid."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    endpoint: str = Field(alias="AZURE_OPENAI_ENDPOINT")
    api_key: SecretStr = Field(alias="AZURE_OPENAI_API_KEY")
    chat_deployment: str = Field(alias="AZURE_OPENAI_CHAT_DEPLOYMENT")
    embedding_deployment: str = Field(
        default="text-embedding-3-small", alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    request_timeout: float = Field(default=60.0, alias="AICOURSE_REQUEST_TIMEOUT")
    chroma_dir: str = Field(default=".chroma", alias="AICOURSE_CHROMA_DIR")
    # None = detect automatically (see aicourse.llm.supports_temperature).
    supports_temperature: bool | None = Field(default=None, alias="AICOURSE_SUPPORTS_TEMPERATURE")

    @field_validator("endpoint")
    @classmethod
    def _normalize_endpoint(cls, value: str) -> str:
        """Accept the endpoint in the forms people usually paste it.

        `https://x.openai.azure.com/`, `https://x.openai.azure.com/openai/v1`
        and `https://x.openai.azure.com/openai/deployments/...` all become
        `https://x.openai.azure.com`.
        """
        value = value.strip().rstrip("/")
        if "YOUR-RESOURCE" in value:
            raise ValueError("still has the placeholder value from .env.example")
        if not value.startswith(("https://", "http://")):
            raise ValueError("must start with https://")
        if "/openai" in value:
            value = value.split("/openai", 1)[0]
        if "/api/projects" in value:
            value = value.split("/api/projects", 1)[0]
        return value

    @field_validator("api_key")
    @classmethod
    def _check_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip() or "paste-your-key" in value.get_secret_value():
            raise ValueError("still has the placeholder value from .env.example")
        return value

    @property
    def base_url(self) -> str:
        """The OpenAI-compatible v1 base URL of the Azure resource."""
        return f"{self.endpoint}/openai/v1/"

    @property
    def chroma_path(self) -> Path:
        return ROOT_DIR / self.chroma_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate settings once, with a readable error if something is wrong."""
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        lines = []
        for err in exc.errors():
            name = err["loc"][0] if err["loc"] else "?"
            reason = "is missing" if err["type"] == "missing" else err["msg"]
            lines.append(f"  - {name}: {reason}")
        hint = (
            f"No .env file found at {ENV_FILE}. Run:  cp .env.example .env  and fill it in."
            if not ENV_FILE.exists()
            else f"Check the values in {ENV_FILE}."
        )
        raise ConfigError(
            "Course configuration problem:\n" + "\n".join(lines) + f"\n{hint}"
        ) from None
