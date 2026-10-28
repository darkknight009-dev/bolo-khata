"""Unit tests for the session, parser matching/normalising and payment link."""
import time

from backend import auth, payments
from backend.bolo_parse import match_customer, normalize_name, normalize_parsed
from backend.models import Bill, Customer, Setting


def test_session_token_roundtrip_and_tamper():
    token = auth.make_session_token(42)
    assert auth._decode_session_token(token) == 42
    assert auth._decode_session_token(token + "x") is None
    bad = token[:-4] + "0000"
    assert auth._decode_session_token(bad) is None


def test_normalize_name_strips_punctuation_and_honorifics():
    assert normalize_name("Sharma ji,") == "sharma"
    assert normalize_name("  Ramesh   Kumar ") == "ramesh kumar"


def test_match_customer_handles_ji_and_exact():
    customers = [Customer(id=1, owner_id=1, name="Sharma"), Customer(id=2, owner_id=1, name="Lakshmi")]
    assert match_customer("sharma ji", customers).id == 1
    assert match_customer("lakshmi", customers).id == 2
    assert match_customer("unknown person", customers) is None
    assert match_customer("", customers) is None


def test_normalize_parsed_ok():
    parsed = normalize_parsed({
        "customer": "Sharma", "language": "Hi",
        "items": [{"name": "doodh", "qty": "1", "unit": "packet", "price": "30"},
                  {"name": "suji", "qty": 2, "unit": "packet", "price": 8}],
        "total": 38, "notes": "kal de dena",
    })
    assert parsed["customer"] == "Sharma"
    assert parsed["language"] == "hi"
    assert parsed["total"] == 38.0
    assert len(parsed["items"]) == 2
    assert parsed["items"][0]["qty"] == 1.0
    assert parsed["notes"] == "kal de dena"


def test_normalize_parsed_derives_total_when_missing():
    parsed = normalize_parsed({
        "customer": "Sharma",
        "items": [{"name": "doodh", "qty": 1, "unit": "", "price": 30},
                  {"name": "suji", "qty": 2, "unit": "", "price": None}],
        "total": 0,
    })
    assert parsed["total"] == 30.0
    assert parsed["items"][1]["price"] is None


def test_normalize_parsed_rejects_empty():
    for bad in ({}, {"customer": ""}, {"customer": "Sharma", "items": []},
                {"customer": "Sharma", "items": [{"name": "", "qty": 1}]}):
        try:
            normalize_parsed(bad)
            raise AssertionError(f"should have raised for {bad}")
        except ValueError:
            pass


def test_pay_link_upi_deep_link_and_paid_suppressed():
    bill = Bill(id=7, owner_id=1, customer_id=1, total=38.0)
    setting = Setting(owner_id=1, shop_name="Sharma General Store", upi_vpa="owner@upi")
    link = payments.pay_link(bill, setting)
    assert link.startswith("upi://pay?pa=owner%40upi")
    assert "am=38" in link and "tr=BILL7" in link
    bill.payment_status = "paid"
    assert payments.pay_link(bill, setting) == ""
    setting.upi_vpa = ""
    bill.payment_status = "unpaid"
    assert payments.pay_link(bill, setting) == ""
