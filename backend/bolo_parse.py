"""Voice-entry parser: audio -> STT (Gnani) -> LLM -> validated bill structure."""
import logging
from pathlib import Path

from . import config, llm
from .gnani_client import GnaniClient
from .models import Customer, normalize_name

log = logging.getLogger("bolo.parser")
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _fill(template: str, values: dict) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def match_customer(spoken: str, customers: list[Customer]) -> Customer | None:
    """Match the spoken customer name to the owner's khaata book (normalised contains)."""
    spoken_norm = normalize_name(spoken)
    if not spoken_norm:
        return None
    # strip honorifics so "sharma ji" matches "sharma"
    spoken_norm = " ".join(w for w in spoken_norm.split() if w not in ("ji", "je", "ge"))
    for customer in customers:
        cnorm = normalize_name(customer.name)
        cwords = set(cnorm.split())
        swords = set(spoken_norm.split())
        if cnorm and (cnorm in spoken_norm or spoken_norm in cnorm or cwords & swords):
            return customer
    return None


def normalize_parsed(raw: dict) -> dict:
    """Validate/normalise the LLM-parsed entry. Raises ValueError when unusable:
    either no customer name or no item line at all."""
    if not isinstance(raw, dict):
        raise ValueError("parse result is not an object")
    customer = str(raw.get("customer") or "").strip()
    if not customer:
        raise ValueError("no customer found in the spoken entry")

    items_raw = raw.get("items")
    if not isinstance(items_raw, list):
        items_raw = []
    items: list[dict] = []
    for it in items_raw[:30]:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        try:
            qty = float(it.get("qty") or 1)
        except (TypeError, ValueError):
            qty = 1.0
        qty = max(0.0, qty)
        unit = str(it.get("unit") or "").strip()
        price = it.get("price")
        try:
            price = None if price is None else max(0.0, float(price))
        except (TypeError, ValueError):
            price = None
        items.append({"name": name[:60], "qty": qty, "unit": unit[:16], "price": price})
    if not items:
        raise ValueError("no items found in the spoken entry")

    try:
        total = float(raw.get("total") or 0)
    except (TypeError, ValueError):
        total = 0.0
    if total <= 0:
        total = round(sum(i["price"] for i in items if i["price"] is not None), 2)

    language = str(raw.get("language") or "hi").lower()[:2]
    if language not in ("hi", "ta", "mr", "kn", "en"):
        language = "hi"
    notes = str(raw.get("notes") or "").strip()[:200]

    return {"customer": customer[:80], "language": language,
            "items": items, "total": round(total, 2), "notes": notes}


async def transcribe(audio_wav: bytes, language: str = "") -> dict:
    """Owner's recorded WAV -> transcript via Gnani STT (credits logged by the client)."""
    result = await GnaniClient().stt(
        audio_wav, language=language or config.STT_LANGUAGE)
    return {"text": result["text"], "language": result.get("language", "")}


async def parse_entry(transcript: str, customers: list[Customer]) -> dict:
    """One LLM call per spoken entry -> normalised bill dict."""
    known = [{"name": c.name, "code": c.bind_code} for c in customers]
    prompt = _fill(load_prompt("bolo_parse"), {
        "customers_json": str(known),
        "transcript": transcript[:1500],
    })
    raw = await llm.chat_json(
        [{"role": "system", "content": prompt},
         {"role": "user", "content": "Parse this entry. JSON object only."}],
        temperature=0.2)
    return normalize_parsed(raw)
