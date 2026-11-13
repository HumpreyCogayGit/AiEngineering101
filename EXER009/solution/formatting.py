"""EXER009 — Response Formatting (reference solution).

Programs need data, not prose. Three levels of control over the output:
  1. JSON mode      — the reply is guaranteed to be valid JSON (any shape)
  2. Structured     — the reply is guaranteed to match YOUR schema
  3. Validate+repair — when you can't use 2, validate and ask the model to fix it
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from aicourse.llm import get_openai_client, model_params
from aicourse.settings import get_settings

SAMPLE_EMAIL = """Hi team,
Quick reminder that the Q2 planning workshop is on Saturday 14 March 2026,
starting 9:30am in the Makati office, 12th floor boardroom. Maria, Jun and
Priya are presenting; Ken will join remotely. Bring your roadmap drafts!
— Liza"""


class Event(BaseModel):
    title: str = Field(description="Short name of the event")
    date: str = Field(description="Date in ISO format YYYY-MM-DD")
    start_time: str | None = Field(description="24h time HH:MM, or null if unknown")
    location: str | None = Field(description="Where it happens, or null if unknown")
    attendees: list[str] = Field(description="First names of people attending or presenting")


# ------------------------------------------------------------ 1. JSON mode
JSON_MODE_SYSTEM = (
    "Extract the event from the user's text. Respond in JSON with the keys "
    '"title", "date" (YYYY-MM-DD), "start_time" (HH:MM or null), "location" (or null) '
    'and "attendees" (list of first names).'
)


def extract_json_mode(client, text: str) -> dict:
    response = client.chat.completions.create(
        model=get_settings().chat_deployment,
        messages=[
            {"role": "system", "content": JSON_MODE_SYSTEM},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        **model_params(temperature=0),
    )
    return json.loads(response.choices[0].message.content)


# ------------------------------------------------- 2. structured outputs
def extract_structured(client, text: str) -> Event:
    """The SDK turns the Pydantic model into a strict JSON schema and parses the reply."""
    completion = client.chat.completions.parse(
        model=get_settings().chat_deployment,
        messages=[
            {"role": "system", "content": "Extract the event from the user's text."},
            {"role": "user", "content": text},
        ],
        response_format=Event,
        **model_params(temperature=0),
    )
    message = completion.choices[0].message
    if message.refusal:
        raise ValueError(f"model refused: {message.refusal}")
    return message.parsed


# ---------------------------------------------------- 3. validate + repair
def parse_with_repair(client, messages: list[dict], model_cls: type[BaseModel],
                      max_attempts: int = 3) -> BaseModel:
    """Ask for JSON, validate it with Pydantic, and on failure send the error back."""
    messages = list(messages)
    last_error = ""
    for _ in range(max_attempts):
        response = client.chat.completions.create(
            model=get_settings().chat_deployment,
            messages=messages,
            response_format={"type": "json_object"},
            **model_params(temperature=0),
        )
        raw = response.choices[0].message.content or ""
        try:
            return model_cls.model_validate_json(raw)
        except ValidationError as exc:
            last_error = str(exc)
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": f"Your JSON was invalid:\n{last_error}\n"
                       "Return the corrected JSON only.",
        })
    raise ValueError(f"no valid output after {max_attempts} attempts: {last_error}")


def main() -> None:
    client = get_openai_client()
    print("1) JSON mode:\n", json.dumps(extract_json_mode(client, SAMPLE_EMAIL), indent=2))
    event = extract_structured(client, SAMPLE_EMAIL)
    print("\n2) Structured output (a real Python object):")
    print("  ", event)
    print("   attendees:", ", ".join(event.attendees))
    repaired = parse_with_repair(
        client,
        [{"role": "system", "content": JSON_MODE_SYSTEM}, {"role": "user", "content": SAMPLE_EMAIL}],
        Event,
    )
    print("\n3) Validated with repair loop:\n  ", repaired)


if __name__ == "__main__":
    main()
