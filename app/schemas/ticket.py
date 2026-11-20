
import re
import unicodedata
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


_INVISIBLE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f"
    r"\u200b-\u200f\u202a-\u202e"
    r"\u2060-\u2064\ufeff]"
)


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = _INVISIBLE.sub("", value)
    return value.strip()


class TicketCreate(BaseModel):

    customer_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    order_id: Optional[str] = Field(default=None, max_length=30)
    subject: str = Field(min_length=3, max_length=150)
    message: str = Field(min_length=5, max_length=3000)

    @field_validator(
        "customer_name",
        "subject",
        "message",
        "order_id",
        mode="before"
    )
    @classmethod
    def clean_fields(cls, value):

        if isinstance(value, str):
            return clean_text(value)

        return value

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):

        if isinstance(value, str):
            return clean_text(value)

        return value

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, value):

        if value is None or value == "":
            return None

        if value.startswith("#"):
            value = value[1:]

        value = value.upper()

        if not re.fullmatch(r"[A-Z0-9-]{3,30}", value):
            raise ValueError("Invalid order ID format")

        return value
