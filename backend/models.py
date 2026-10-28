"""Bolo Khata data models (SQLModel + SQLite)."""
import json
import re
import secrets
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def load(text, default):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return default


class User(SQLModel, table=True):
    """The shop owner. One row per Google account (or dev login)."""
    id: int | None = Field(default=None, primary_key=True)
    google_sub: str = Field(index=True, unique=True)
    email: str = ""
    name: str = ""
    picture: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class Setting(SQLModel, table=True):
    """Per-owner settings: shop identity + payment destination."""
    owner_id: int = Field(primary_key=True, foreign_key="user.id")
    shop_name: str = "Meri Dukaan"
    upi_vpa: str = ""          # e.g. owner@upi — feeds the UPI deep-link on receipts
    # Reserved for a gateway (Razorpay keys etc.) — kept out of the MVP interface.
    payment_gateway: str = ""


class Customer(SQLModel, table=True):
    """A khaata customer of one owner."""
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(index=True, foreign_key="user.id")
    name: str = ""
    normalized_name: str = ""   # lowercased, punctuation-stripped for voice matching
    bind_code: str = Field(default_factory=lambda: secrets.token_hex(3), unique=True)
    telegram_chat_id: str | None = None
    telegram_username: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Bill(SQLModel, table=True):
    """One spoken entry: items parsed out of the transcript."""
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(index=True, foreign_key="user.id")
    customer_id: int = Field(index=True, foreign_key="customer.id")
    items_json: str = "[]"      # [{name, qty, unit, price}, ...]
    total: float = 0.0
    raw_transcript: str = ""
    language: str = "hi"
    notes: str = ""            # payment note the owner spoke (e.g. 'kal de dena')
    payment_status: str = "unpaid"   # unpaid | paid  (gateway ack comes later)
    payment_method: str = ""         # e.g. 'upi-deep-link' once a gateway exists
    telegram_sent: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class CreditLog(SQLModel, table=True):
    """Every paid provider request (kept from the Gnani client contract)."""
    id: int | None = Field(default=None, primary_key=True)
    ts: datetime | None = Field(default_factory=utcnow)
    function: str = ""
    model: str = ""
    units: float = 0
    unit_type: str = ""
    credits: float | None = None
    run_id: int | None = None
    request_id: str | None = None


def normalize_name(name: str) -> str:
    """Match a spoken customer name to stored names robustly across scripts.
    lowercase, punctuation stripped, honorifics (ji) dropped so 'Sharma ji' == 'Sharma'."""
    text = (name or "").strip().lower()
    text = re.sub(r"[।|,.;:?!—–\"'“”‘’()\[\]{}…]", " ", text)
    words = [w for w in re.split(r"\s+", text) if w and w not in ("ji", "je", "ge")]
    return " ".join(words).strip()
