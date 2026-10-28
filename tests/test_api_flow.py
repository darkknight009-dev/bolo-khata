"""In-process API test of the core owner flow with LLM_MOCK=1 and no external calls."""
import os

os.environ["LLM_MOCK"] = "1"
os.environ["VOICEQA_DB_PATH"] = "data/test_bolo.db"

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

client = TestClient(app)


def authed_client():
    resp = client.post("/api/auth/dev")
    assert resp.status_code == 200, resp.text
    return resp


def test_owner_flow_dev_login_entry_bill_paid():
    authed_client()

    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["user"]["name"] == "Dev Owner"

    # the owner already knows Sharma — the parser must match the spoken name to him
    cust = client.post("/api/customers", json={"name": "Sharma"})
    assert cust.status_code == 200

    # parse a spoken entry via the mocked LLM
    entry = client.post("/api/entries", json={
        "transcript": "Sharma ji ka doodh 1 packet 30 aur suji 2 packet 8, total 38"})
    assert entry.status_code == 200, entry.text
    parsed = entry.json()["entry"]
    assert parsed["customer_matched"] == "Sharma"
    assert parsed["total"] == 38.0

    # save it as a bill
    saved = client.post("/api/bills", json={
        "customer_name": parsed["customer_matched"],
        "transcript": parsed["transcript"],
        "items": parsed["items"], "total": parsed["total"],
        "language": parsed["language"], "notes": ""})
    assert saved.status_code == 200, saved.text
    bill = saved.json()["bill"]
    assert bill["payment_status"] == "unpaid"

    # it shows up in the customer's bills and the recent list
    bills_before = client.get(f"/api/customers/{bill['customer_id']}/bills").json()
    assert len(bills_before["bills"]) == 1
    recents = client.get("/api/bills/recent").json()
    assert any(b["id"] == bill["id"] for b in recents["bills"])

    # set a VPA -> UPI link appears; mark paid -> link is suppressed
    upd = client.patch("/api/me/settings", json={"upi_vpa": "owner@upi"})
    assert upd.status_code == 200
    after = client.get(f"/api/customers/{bill['customer_id']}/bills").json()
    assert after["bills"][0]["payment_link"].startswith("upi://pay?pa=owner%40upi")

    mark = client.post(f"/api/bills/{bill['id']}/mark-paid")
    assert mark.status_code == 200 and mark.json()["bill"]["payment_status"] == "paid"
    after = client.get(f"/api/customers/{bill['customer_id']}/bills").json()
    assert after["bills"][0]["payment_link"] == ""

    # telegram send fails honestly when the customer isn't bound (no fake success)
    tg = client.post(f"/api/bills/{bill['id']}/send-telegram")
    assert tg.status_code == 409 and "bind" in tg.json()["detail"].lower()


def test_auth_required():
    anon = TestClient(app)
    assert anon.get("/api/customers").status_code == 401
    assert anon.post("/api/entries", json={"transcript": "x"}).status_code == 401
