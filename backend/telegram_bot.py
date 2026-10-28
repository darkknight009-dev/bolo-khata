"""Telegram integration without a webhook: a getUpdates polling thread runs in the app.

Bind flow (no auth token needed by the customer):
  1. Owner opens the bot in Telegram and taps "Send receipt" for a customer.
  2. The customer messages our bot: /bind <bind_code> (6-hex code on each customer).
  3. The poller stores the chat_id on that customer — receipts can now be delivered.
"""
import asyncio
import logging
import time

import httpx

from . import config
from .db import get_session
from .models import Bill, Customer, load

log = logging.getLogger("bolo.telegram")

API = "https://api.telegram.org"
_offset_state: int = 0


def _api_url(method: str) -> str:
    return f"{API}/bot{config.TELEGRAM_BOT_TOKEN}/{method}"


def configured() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN)


async def bot_status() -> dict:
    if not configured():
        return {"configured": False}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_api_url("getMe"))
            payload = resp.json()
    except httpx.HTTPError as exc:
        return {"configured": True, "ok": False, "error": f"network: {exc}"}
    if not payload.get("ok"):
        return {"configured": True, "ok": False, "error": payload.get("description", "bad token")}
    me = payload["result"]
    return {"configured": True, "ok": True, "username": me.get("username", "")}


async def send_message(chat_id: str, text: str) -> dict:
    if not configured():
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(_api_url("sendMessage"),
                                 json={"chat_id": chat_id, "text": text,
                                       "parse_mode": "HTML", "disable_web_page_preview": True})
    return resp.json()


def poll_once(offset: int) -> int:
    """Synchronous single getUpdates cycle; returns the next offset (0 on failure)."""
    try:
        with httpx.Client(timeout=35) as client:
            resp = client.get(_api_url("getUpdates"), params={
                "offset": offset, "timeout": 25, "allowed_updates": ["message"]})
            payload = resp.json()
    except httpx.HTTPError as exc:
        log.warning("telegram getUpdates network error: %s", exc)
        return offset
    if not payload.get("ok"):
        log.warning("telegram getUpdates error: %s", payload.get("description"))
        return offset
    next_offset = offset
    for update in payload.get("result", []):
        next_offset = max(next_offset, update["update_id"] + 1)
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        text = str(message.get("text") or "").strip()
        chat_id = str(chat.get("id") or "")
        if not chat_id or not text:
            continue
        _handle_text(chat, chat_id, text)
    return next_offset


def _handle_text(chat: dict, chat_id: str, text: str) -> None:
    """Bind codes are the only command surface in v1."""
    lowered = text.lower()
    if lowered.startswith("/start"):
        send_message(chat_id,
                     "Namaste! Main Bolo Khata bot hoon.\n"
                     "Apni dukaan wale ne aapko ek binding code diya hoga — "
                     "yahan bhejein: <code>/bind CODE</code>")
        return
    if lowered.startswith("/bind"):
        parts = lowered.split()
        code = parts[1] if len(parts) > 1 else ""
        with get_session() as session:
            customer = session.get(Customer, _customer_id_by_code(code))
            if customer is None:
                send_message(chat_id, "Ye code galat hai. Dukaan wale se sahi code lein.")
                return
            customer.telegram_chat_id = chat_id
            customer.telegram_username = chat.get("username")
            session.add(customer)
            session.commit()
            name = customer.name
        send_message(chat_id,
                     f"Bind ho gaya! Ab aapko <b>{name}</b> ki dukaan se "
                     "receipt aur payment link isi chat par aayenge. 🧾")
        return
    send_message(chat_id, "Kripya /bind CODE bhejein (code dukaan wale se milega).")


_customer_ids: dict[str, int] = {}


def _customer_id_by_code(code: str) -> int | None:
    # refreshed lazily by the poll loop; keeps SQLite lookups cheap
    return _customer_ids.get(code.strip().lower())


def refresh_bind_index() -> None:
    with get_session() as session:
        for customer in session.query(Customer).all():
            _customer_ids[customer.bind_code.lower()] = customer.id


async def poll_loop() -> None:
    """Background task started with the app when a token is configured."""
    global _offset_state
    log.info("telegram poll loop started")
    while True:
        try:
            refresh_bind_index()
            _offset_state = await asyncio.to_thread(poll_once, _offset_state)
            await asyncio.sleep(1)  # getUpdates long-polls 25s, this just guards busy-looping on errors
        except Exception:
            log.exception("telegram poll loop error")
            await asyncio.sleep(10)


def receipt_text(bill: Bill, customer: Customer, shop_name: str, payment_link: str) -> str:
    lines = [f"🧾 <b>{shop_name}</b> — {customer.name} ka khata"]
    items = load(bill.items_json, [])
    for item in items:
        qty = f"{item.get('qty'):g} {item['unit']} ".strip()
        price = item.get("price")
        price_s = f"₹{price:g}" if price is not None else ""
        lines.append(f"• {item['name']} {qty} — {price_s}".rstrip(" -—"))
    lines.append(f"<b>Total: ₹{bill.total:g}</b>")
    if bill.payment_status == "paid":
        lines.append("✅ payment received — dhanyavaad!")
    elif payment_link:
        lines.append(f"💰 Pay here: {payment_link}")
    return "\n".join(lines)


async def poll_step_now() -> None:
    """Force one poll cycle (used by the settings refresh button)."""
    global _offset_state
    refresh_bind_index()
    _offset_state = await asyncio.to_thread(poll_once, _offset_state)
