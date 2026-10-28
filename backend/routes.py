"""Bolo Khata REST API."""
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlmodel import select

from . import auth, config, payments, telegram_bot
from .bolo_parse import match_customer, normalize_name, parse_entry, transcribe
from .db import get_session
from .models import Bill, Customer, Setting, User, dump, load

log = logging.getLogger("bolo.routes")
router = APIRouter(prefix="/api")

# ------------------------------------------------------------------- auth ----

class Credential(BaseModel):
    credential: str


@router.get("/auth/config")
async def auth_config():
    return {
        "google": bool(config.GOOGLE_CLIENT_ID),
        "client_id": config.GOOGLE_CLIENT_ID,
        "dev_login": bool(config.BOLO_DEV_LOGIN),
        "telegram": await telegram_bot.bot_status(),
    }


@router.post("/auth/google")
async def auth_google(body: Credential, response: Response):
    if not config.GOOGLE_CLIENT_ID:
        raise HTTPException(500, "GOOGLE_CLIENT_ID is not configured on the server")
    claims = await auth.verify_google_credential(body.credential)
    user = await auth.login_or_create_user(claims)
    auth.set_session_cookie(response, user.id)
    return {"user": {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture}}


@router.post("/auth/dev")
async def auth_dev(response: Response):
    """Local-run helper: signs in a demo owner without Google. Clearly labelled."""
    if not config.BOLO_DEV_LOGIN:
        raise HTTPException(403, "dev login is disabled (set BOLO_DEV_LOGIN=1)")
    user = await auth.login_or_create_user({
        "sub": "dev-owner", "email": "owner@bologhata.local", "name": "Dev Owner"})
    auth.set_session_cookie(response, user.id)
    return {"user": {"id": user.id, "email": user.email, "name": user.name, "picture": ""}}


@router.post("/auth/logout")
async def auth_logout(response: Response):
    auth.clear_session_cookie(response)
    return {"ok": True}


@router.get("/me")
async def me(user: User = Depends(auth.current_user)):
    with get_session() as session:
        setting = session.get(Setting, user.id)
        if setting is None:
            setting = Setting(owner_id=user.id, shop_name=f"{user.name}'s dukaan")
            session.add(setting)
            session.commit()
    return {"user": {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture},
            "setting": {"shop_name": setting.shop_name, "upi_vpa": setting.upi_vpa,
                        "payment_gateway": setting.payment_gateway}}


class SettingUpdate(BaseModel):
    shop_name: str | None = None
    upi_vpa: str | None = None


@router.patch("/me/settings")
async def update_settings(body: SettingUpdate, user: User = Depends(auth.current_user)):
    with get_session() as session:
        setting = session.get(Setting, user.id)
        if setting is None:
            setting = Setting(owner_id=user.id)
        if body.shop_name is not None:
            setting.shop_name = body.shop_name.strip()[:60] or "Meri Dukaan"
        if body.upi_vpa is not None:
            vpa = body.upi_vpa.strip()
            if vpa and "@" not in vpa:
                raise HTTPException(400, "UPI ID looks wrong — it must contain '@' (e.g. name@upi)")
            setting.upi_vpa = vpa[:80]
        session.add(setting)
        session.commit()
    return {"setting": {"shop_name": setting.shop_name, "upi_vpa": setting.upi_vpa,
                        "payment_gateway": setting.payment_gateway}}


# --------------------------------------------------------------- customers ---

class CustomerCreate(BaseModel):
    name: str


def _customer_out(c: Customer, due: float | None = None, unpaid: int | None = None) -> dict:
    out = {"id": c.id, "name": c.name, "bind_code": c.bind_code,
           "telegram_bound": bool(c.telegram_chat_id),
           "telegram_username": c.telegram_username, "created_at": str(c.created_at)}
    if due is not None:
        out["due"] = round(due, 2)
    if unpaid is not None:
        out["unpaid_bills"] = unpaid
    return out


def _ensure_customer(session, user: User, name: str) -> Customer:
    norm = normalize_name(name)
    existing = session.exec(select(Customer).where(
        Customer.owner_id == user.id, Customer.normalized_name == norm)).first()
    if existing:
        return existing
    customer = Customer(owner_id=user.id, name=name.strip()[:80], normalized_name=norm)
    session.add(customer)
    session.commit()
    return customer


@router.get("/customers")
async def list_customers(user: User = Depends(auth.current_user)):
    with get_session() as session:
        rows = session.exec(select(Customer).where(Customer.owner_id == user.id)).all()
        out = []
        for c in rows:
            bills = session.exec(select(Bill).where(
                Bill.customer_id == c.id, Bill.payment_status == "unpaid")).all()
            out.append(_customer_out(
                c, due=sum(b.total for b in bills), unpaid=len(bills)))
        return {"customers": sorted(out, key=lambda x: (-x.get("due", 0), x["name"]))}


@router.post("/customers")
async def create_customer(body: CustomerCreate, user: User = Depends(auth.current_user)):
    if not body.name.strip():
        raise HTTPException(400, "customer name is required")
    with get_session() as session:
        c = _ensure_customer(session, user, body.name)
        session.refresh(c)
        return {"customer": _customer_out(c)}


@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int, user: User = Depends(auth.current_user)):
    with get_session() as session:
        c = session.get(Customer, customer_id)
        if not c or c.owner_id != user.id:
            raise HTTPException(404, "customer not found")
        bills = session.exec(select(Bill).where(Bill.customer_id == customer_id)).all()
        for b in bills:
            session.delete(b)
        session.delete(c)
        session.commit()
    return {"ok": True}


@router.get("/customers/{customer_id}/bills")
async def customer_bills(customer_id: int, user: User = Depends(auth.current_user)):
    with get_session() as session:
        c = session.get(Customer, customer_id)
        if not c or c.owner_id != user.id:
            raise HTTPException(404, "customer not found")
        setting = _setting_of(session, user.id)
        bills = session.exec(select(Bill).where(Bill.customer_id == customer_id)
                             .order_by(Bill.id.desc())).all()
        return {
            "customer": _customer_out(c),
            "bills": [
                {"id": b.id, "items": _items(b), "total": b.total, "payment_status": b.payment_status,
                 "payment_link": payments.pay_link(b, setting),
                 "telegram_sent": b.telegram_sent, "raw_transcript": b.raw_transcript,
                 "notes": b.notes, "created_at": str(b.created_at)}
                for b in bills
            ],
        }


# ----------------------------------------------------- voice entry / bills ----

class AudioIn(BaseModel):
    audio_b64: str          # 16 kHz mono 16-bit WAV from the PWA
    language: str = ""


class EntryIn(BaseModel):
    transcript: str


def _setting_of(session, owner_id: int) -> Setting:
    setting = session.get(Setting, owner_id)
    if setting is None:
        setting = Setting(owner_id=owner_id, shop_name="Meri Dukaan")
        session.add(setting)
        session.commit()
    return setting


def _items(bill: Bill) -> list[dict]:
    return load(bill.items_json, [])


@router.post("/transcribe")
async def transcribe_audio(body: AudioIn, user: User = Depends(auth.current_user)):
    """Owner's speech -> transcript (Gnani STT server adapter, credits logged)."""
    try:
        audio = base64.b64decode(body.audio_b64)
    except Exception:
        raise HTTPException(400, "audio_b64 is not valid base64")
    if len(audio) < 100:
        raise HTTPException(400, "audio too short")
    result = await transcribe(audio, body.language)
    if not result["text"].strip():
        raise HTTPException(422, "STT returned an empty transcript")
    return result


@router.post("/entries")
async def create_entry(body: EntryIn, user: User = Depends(auth.current_user)):
    """Transcript -> parsed entry (preview; nothing is saved until /bills)."""
    transcript = body.transcript.strip()
    if not transcript:
        raise HTTPException(400, "empty transcript")
    with get_session() as session:
        customers = session.exec(select(Customer).where(Customer.owner_id == user.id)).all()
    parsed = await parse_entry(transcript, customers)
    with get_session() as session:
        matched = match_customer(parsed["customer"], customers)
        parsed["customer_id"] = matched.id if matched else None
        parsed["customer_matched"] = matched.name if matched else None
    parsed["transcript"] = transcript
    return {"entry": parsed}


class BillCreate(BaseModel):
    customer_name: str
    transcript: str
    items: list[dict]
    total: float
    language: str = "hi"
    notes: str = ""


def _bill_out(session, bill: Bill) -> dict:
    setting = _setting_of(session, bill.owner_id)
    return {"id": bill.id, "customer_id": bill.customer_id, "total": bill.total,
            "items": _items(bill), "payment_status": bill.payment_status,
            "payment_link": payments.pay_link(bill, setting), "telegram_sent": bill.telegram_sent,
            "raw_transcript": bill.raw_transcript, "notes": bill.notes,
            "created_at": str(bill.created_at)}


@router.post("/bills")
async def create_bill(body: BillCreate, user: User = Depends(auth.current_user)):
    """Persist a spoken entry as a bill (items/total already parsed + confirmed)."""
    if not body.customer_name.strip():
        raise HTTPException(400, "customer name required")
    if not body.items:
        raise HTTPException(400, "no items in the entry")
    if body.total <= 0:
        raise HTTPException(400, "total must be positive")
    with get_session() as session:
        c = _ensure_customer(session, user, body.customer_name)
        bill = Bill(owner_id=user.id, customer_id=c.id, items_json=dump(body.items),
                    total=round(body.total, 2), raw_transcript=body.transcript[:2000],
                    language=body.language, notes=body.notes[:200])
        session.add(bill)
        session.commit()
        session.refresh(bill)
        return {"bill": _bill_out(session, bill), "customer": _customer_out(c)}


@router.get("/bills/recent")
async def recent_bills(limit: int = 20, user: User = Depends(auth.current_user)):
    with get_session() as session:
        rows = session.exec(select(Bill).where(Bill.owner_id == user.id)
                            .order_by(Bill.id.desc()).limit(min(limit, 100))).all()
        setting = _setting_of(session, user.id)
        customers = {c.id: c for c in session.exec(
            select(Customer).where(Customer.owner_id == user.id)).all()}
        return {"bills": [
            {"id": b.id, "customer": customers.get(b.customer_id).name if customers.get(b.customer_id) else "?",
             "total": b.total, "payment_status": b.payment_status,
             "payment_link": payments.pay_link(b, setting), "created_at": str(b.created_at),
             "item_count": len(_items(b))}
            for b in rows
        ]}


@router.post("/bills/{bill_id}/mark-paid")
async def mark_paid(bill_id: int, user: User = Depends(auth.current_user)):
    with get_session() as session:
        bill = session.get(Bill, bill_id)
        if not bill or bill.owner_id != user.id:
            raise HTTPException(404, "bill not found")
        bill.payment_status = "paid" if bill.payment_status == "unpaid" else "unpaid"
        session.add(bill)
        session.commit()
    return {"bill": {"id": bill.id, "payment_status": bill.payment_status}}


# ---------------------------------------------------------------- telegram ---

@router.post("/bills/{bill_id}/send-telegram")
async def send_receipt(bill_id: int, user: User = Depends(auth.current_user)):
    with get_session() as session:
        bill = session.get(Bill, bill_id)
        if not bill or bill.owner_id != user.id:
            raise HTTPException(404, "bill not found")
        customer = session.get(Customer, bill.customer_id)
        setting = _setting_of(session, user.id)
        if not customer.telegram_chat_id:
            raise HTTPException(409,
                f"{customer.name} ka Telegram abhi bind nahi hua. "
                f"Unko invite karein: apne bot ko message karke /bind {customer.bind_code} bhejne ko kahein.")
    try:
        result = await telegram_bot.send_message(
            customer.telegram_chat_id,
            telegram_bot.receipt_text(bill, customer, setting.shop_name,
                                      payments.pay_link(bill, setting)))
    except Exception as exc:
        raise HTTPException(502, f"Telegram send failed: {exc}") from exc
    if not result.get("ok"):
        raise HTTPException(502, f"Telegram said: {result.get('description', 'error')}")
    with get_session() as session:
        bill.telegram_sent = True
        session.add(bill)
        session.commit()
    return {"ok": True, "chat": customer.telegram_username or customer.telegram_chat_id}


@router.get("/telegram/bind-info")
async def bind_info(user: User = Depends(auth.current_user)):
    with get_session() as session:
        customers = session.exec(select(Customer).where(Customer.owner_id == user.id)).all()
        codes = {c.name: c.bind_code for c in customers if not c.telegram_chat_id}
    status = await telegram_bot.bot_status()
    return {"bot": status, "unbound": [{"name": k, "code": v} for k, v in codes.items()]}


@router.post("/telegram/refresh")
async def telegram_refresh(user: User = Depends(auth.current_user)):
    if not telegram_bot.configured():
        raise HTTPException(400, "TELEGRAM_BOT_TOKEN is not configured on the server")
    await telegram_bot.poll_step_now()
    return await list_customers(user)
