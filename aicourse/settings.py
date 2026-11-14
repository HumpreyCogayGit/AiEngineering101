"""The single place that reads configuration for the whole course.

Every exercise gets its settings from here:

    from aicourse.settings import get_settings
    settings = get_settings()
    print(settings.chat_model)

Values come from the `.env` file at the repository root (or from real
environment variables, which win over `.env`).

The course runs on more than one inference provider. `AICOURSE_PROVIDER`
picks one, and each provider has its own block of variables in `.env`:

    azure   Azure Foundry (Azure OpenAI), in the cloud      AZURE_OPENAI_*
    ollama  Ollama, running models on your own machine      OLLAMA_*

Both speak the same OpenAI-compatible API, so the rest of the course only
ever uses the provider-neutral names below: `provider`, `endpoint`,
`base_url`, `api_key`, `chat_model`, `embedding_model`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The repository root: the folder that contains this `aicourse/` package.
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
DATA_DIR = ROOT_DIR / "data"

PROVIDER_LABELS = {"azure": "Azure Foundry", "ollama": "Ollama"}
_PLACEHOLDER = "still has the placeholder value from .env.example"


class ConfigError(RuntimeError):
    """Raised when `.env` is missing or a setting is invalid."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["azure", "ollama"] = Field(default="azure", alias="AICOURSE_PROVIDER")

    # --- Provider block: Azure Foundry. Required only when provider is "azure".
    azure_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_api_key: SecretStr | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_chat_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_embedding_deployment: str = Field(
        default="text-embedding-3-small", alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    # --- Provider block: Ollama. Every value has a default that works locally.
    ollama_endpoint: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    # Ollama does not check the key, but the SDKs refuse to send an empty one.
    ollama_api_key: SecretStr = Field(default=SecretStr("ollama"), alias="OLLAMA_API_KEY")
    ollama_chat_model: str = Field(default="gemma4:e4b", alias="OLLAMA_CHAT_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text:latest", alias="OLLAMA_EMBEDDING_MODEL")
    # Text put in front of every query / document before it is embedded. Some open
    # embedding models are trained with such task prefixes and retrieve poorly without
    # them. The defaults belong to the default embedding model: change them together.
    ollama_embedding_query_prefix: str = Field(default="search_query: ", alias="OLLAMA_EMBEDDING_QUERY_PREFIX")
    ollama_embedding_document_prefix: str = Field(
        default="search_document: ", alias="OLLAMA_EMBEDDING_DOCUMENT_PREFIX"
    )

    # --- Provider-independent
    # None = the provider's default (see `request_timeout`).
    request_timeout_override: float | None = Field(default=None, alias="AICOURSE_REQUEST_TIMEOUT")
    chroma_dir: str = Field(default=".chroma", alias="AICOURSE_CHROMA_DIR")
    # None = leave it to the model (see `reasoning_effort`).
    reasoning_effort_override: str | None = Field(default=None, alias="AICOURSE_REASONING_EFFORT")
    # None = detect automatically (see aicourse.llm.supports_temperature).
    supports_temperature: bool | None = Field(default=None, alias="AICOURSE_SUPPORTS_TEMPERATURE")

    # ------------------------------------------------------------ validation
    @field_validator("provider", mode="before")
    @classmethod
    def _normalize_provider(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("azure_endpoint")
    @classmethod
    def _normalize_azure_endpoint(cls, value: str | None) -> str | None:
        """Accept the endpoint in the forms people usually paste it.

        `https://x.openai.azure.com/`, `https://x.openai.azure.com/openai/v1`
        and `https://x.openai.azure.com/openai/deployments/...` all become
        `https://x.openai.azure.com`.
        """
        if value is None:
            return None
        value = value.strip().rstrip("/")
        if "YOUR-RESOURCE" in value:
            raise ValueError(_PLACEHOLDER)
        if not value.startswith(("https://", "http://")):
            raise ValueError("must start with https://")
        if "/openai" in value:
            value = value.split("/openai", 1)[0]
        if "/api/projects" in value:
            value = value.split("/api/projects", 1)[0]
        return value

    @field_validator("azure_api_key")
    @classmethod
    def _check_azure_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        if not value.get_secret_value().strip() or "paste-your-key" in value.get_secret_value():
            raise ValueError(_PLACEHOLDER)
        return value

    @field_validator("ollama_endpoint")
    @classmethod
    def _normalize_ollama_endpoint(cls, value: str) -> str:
        """`http://localhost:11434/`, `.../v1` and `.../api` all become `http://localhost:11434`."""
        value = value.strip().rstrip("/")
        if not value.startswith(("https://", "http://")):
            raise ValueError("must start with http:// (the default is http://localhost:11434)")
        for suffix in ("/v1", "/api"):
            if value.endswith(suffix):
                value = value[: -len(suffix)]
        return value

    @field_validator("ollama_chat_model", "ollama_embedding_model")
    @classmethod
    def _check_model_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("is empty")
        return value.strip()

    @model_validator(mode="after")
    def _require_selected_provider(self) -> "Settings":
        """Only the block of the selected provider has to be filled in."""
        if self.provider == "azure":
            required = {
                "AZURE_OPENAI_ENDPOINT": self.azure_endpoint,
                "AZURE_OPENAI_API_KEY": self.azure_api_key,
                "AZURE_OPENAI_CHAT_DEPLOYMENT": (self.azure_chat_deployment or "").strip(),
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError("missing:" + ",".join(missing))
        return self

    # ------------------------------------------- the provider-neutral view
    @property
    def provider_label(self) -> str:
        """The provider's name for humans, e.g. "Azure Foundry" or "Ollama"."""
        return PROVIDER_LABELS[self.provider]

    @property
    def endpoint(self) -> str:
        """Where the provider lives, without any API path."""
        return self.ollama_endpoint if self.provider == "ollama" else str(self.azure_endpoint)

    @property
    def base_url(self) -> str:
        """The provider's OpenAI-compatible v1 base URL (ends with a slash)."""
        path = "/v1/" if self.provider == "ollama" else "/openai/v1/"
        return f"{self.endpoint}{path}"

    @property
    def api_key(self) -> SecretStr:
        if self.provider == "ollama":
            return self.ollama_api_key
        assert self.azure_api_key is not None  # guaranteed by _require_selected_provider
        return self.azure_api_key

    @property
    def chat_model(self) -> str:
        """What to send as `model` for chat (on Azure: your deployment name)."""
        return self.ollama_chat_model if self.provider == "ollama" else str(self.azure_chat_deployment)

    @property
    def embedding_model(self) -> str:
        """What to send as `model` for embeddings (on Azure: your deployment name)."""
        if self.provider == "ollama":
            return self.ollama_embedding_model
        return self.azure_embedding_deployment

    @property
    def embedding_query_prefix(self) -> str:
        """Text to put in front of a search query before embedding it ("" for none)."""
        return self.ollama_embedding_query_prefix if self.provider == "ollama" else ""

    @property
    def embedding_document_prefix(self) -> str:
        """Text to put in front of a document before embedding it ("" for none)."""
        return self.ollama_embedding_document_prefix if self.provider == "ollama" else ""

    @property
    def reasoning_effort(self) -> str | None:
        """How much hidden "thinking" to ask for: none, low, medium, high. None = don't say.

        Set with AICOURSE_REASONING_EFFORT. Unset (or the word `default`), the
        parameter is not sent and the model uses its own default. Less thinking
        is faster and cheaper, but a small model chooses tools noticeably worse
        without it, so the course does not turn it off for you.
        """
        if self.reasoning_effort_override is None:
            return None
        value = self.reasoning_effort_override.strip().lower()
        return None if value in ("", "default") else value

    @property
    def max_tokens_param(self) -> str:
        """The request parameter that limits the length of the answer.

        The chat completions API has two names for it. `max_completion_tokens`
        is the current one and the only one reasoning models accept;
        `max_tokens` is the original one and the only one Ollama applies.
        """
        return "max_tokens" if self.provider == "ollama" else "max_completion_tokens"

    @property
    def request_timeout(self) -> float:
        """Seconds before a request gives up.

        A local model may first have to be loaded into memory, and it answers
        slower than a cloud one, so Ollama gets a longer default.
        """
        if self.request_timeout_override is not None:
            return self.request_timeout_override
        return 300.0 if self.provider == "ollama" else 60.0

    @property
    def chroma_path(self) -> Path:
        return ROOT_DIR / self.chroma_dir


def _problems(exc: ValidationError) -> list[str]:
    lines: list[str] = []
    for err in exc.errors():
        message = err["msg"].removeprefix("Value error, ")
        if message.startswith("missing:"):
            lines += [f"  - {name}: is missing" for name in message.removeprefix("missing:").split(",")]
            continue
        # Report the name people see in `.env`, not the Python field name.
        field = Settings.model_fields.get(str(err["loc"][0])) if err["loc"] else None
        name = (field.alias if field and field.alias else None) or (err["loc"][0] if err["loc"] else "?")
        if name == "AICOURSE_PROVIDER":
            message = "must be one of: " + ", ".join(PROVIDER_LABELS)
        lines.append(f"  - {name}: {'is missing' if err['type'] == 'missing' else message}")
    return lines


def _config_error(exc: ValidationError, hint: str) -> ConfigError:
    return ConfigError("Course configuration problem:\n" + "\n".join(_problems(exc)) + f"\n{hint}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate settings once, with a readable error if something is wrong."""
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        hint = (
            f"No .env file found at {ENV_FILE}. Run:  cp .env.example .env  and fill it in."
            if not ENV_FILE.exists()
            else f"Check the values in {ENV_FILE}."
        )
        raise _config_error(exc, hint) from None


def settings_from_environment() -> Settings:
    """Settings from real environment variables ONLY: any `.env` file is ignored.

    This is how a deployed service is configured (EXER041): the platform injects
    the variables, and no file with secrets is shipped inside the image. Not
    cached, so a health check always sees the current environment.
    """
    try:
        return Settings(_env_file=None)  # type: ignore[call-arg]
    except ValidationError as exc:
        raise _config_error(exc, "Set these as environment variables of the running service.") from None
