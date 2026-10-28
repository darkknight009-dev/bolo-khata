"""Payments (v1: stub interface, real rails later).

Today: build a UPI deep-link (`upi://pay?pa=...`) from the owner's VPA — every UPI
app on the customer's phone can pay it, no gateway account needed. The customer
taps the link in the Telegram receipt; the owner marks bills paid (or it flips
automatically once a gateway webhook exists).

Tomorrow: set `payment_gateway` + keys in Setting and `pay_link()` gains a branch
for the hosted page — the receipt text and API contract do not change.
"""
from urllib.parse import quote

from .models import Bill, Setting


def pay_link(bill: Bill, setting: Setting) -> str:
    if bill.payment_status == "paid":
        return ""
    vpa = (setting.upi_vpa or "").strip()
    if not vpa:
        return ""
    return (
        f"upi://pay?pa={quote(vpa)}"
        f"&pn={quote(setting.shop_name or 'Bolo Khata')}"
        f"&am={bill.total:g}"
        f"&tr=BILL{bill.id or 0}"
        f"&tn={quote(f'{setting.shop_name} bill {bill.id or 0}')}"
        "&cu=INR"
    )
