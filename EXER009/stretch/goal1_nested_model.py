"""EXER009 stretch goal 1 — a nested model: an `Address` inside the event.

    uv run python EXER009/stretch/goal1_nested_model.py

A field's type can be another Pydantic model. The JSON schema sent to the
model nests the same way, so the reply does too, and you read
`event.address.city` instead of picking a string apart.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from aicourse.llm import get_llm_client, model_params
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "formatting.py")


class Address(BaseModel):
    building: str | None = Field(description="Building or office name, or null if unknown")
    floor: str | None = Field(description="Floor, e.g. '12', or null if unknown")
    room: str | None = Field(description="Room name, or null if unknown")
    city: str | None = Field(description="City or district, or null if unknown")


class EventWithAddress(BaseModel):
    title: str = Field(description="Short name of the event")
    date: str = Field(description="Date in ISO format YYYY-MM-DD")
    start_time: str | None = Field(description="24h time HH:MM, or null if unknown")
    address: Address  # the nested model
    attendees: list[str] = Field(description="First names of people attending or presenting")


# The rules about values are in the prompt too: not every provider shows the
# field descriptions to the model (see the lecture).
SYSTEM = (
    base.STRUCTURED_SYSTEM
    + " Split the location into building, floor, room and city; use null for a part that is not stated."
    + " Write the floor as a number only."
)


def extract(client, text: str) -> EventWithAddress:
    completion = client.chat.completions.parse(
        model=get_settings().chat_model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
        response_format=EventWithAddress,
        **model_params(temperature=0),
    )
    message = completion.choices[0].message
    if message.refusal:
        raise ValueError(f"model refused: {message.refusal}")
    return message.parsed


def main() -> None:
    event = extract(get_llm_client(), base.SAMPLE_EMAIL)
    print(event.model_dump_json(indent=2))
    print(f"\nevent.address.city  -> {event.address.city!r}")
    print(f"event.address.floor -> {event.address.floor!r}")


if __name__ == "__main__":
    main()
