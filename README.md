# Bolo Khata

**Speak your khaata.** A voice-first ledger PWA for Indian kiryana store owners:
the owner holds a mic button and says *"Sharma ji ko do doodh packet, do suji ka
athaat rupaye"* — the entry lands in the ledger automatically, no typing. Each
bill can be sent to the customer's Telegram with a UPI "pay here" link, and the
owner marks payments received (webhook-verified payments slot in later).

## How it works

```
owner's voice ──▶ PWA records 16 kHz WAV ──▶ Gnani STT ──▶ LLM parse ──▶ bill
                                                                        │
                        Telegram receipt ◀── owner taps "send" ─────────┘
                        + upi://pay link (customer pays from any UPI app)
```

- **Auth**: official Google Sign-In button → FastAPI verifies the ID token
  server-side → signed httponly session cookie. No third-party auth service.
- **Voice entry**: browser captures audio (AudioWorklet → 16 kHz mono WAV),
  server STT adapter (Gnani Prisma, credits logged), then one LLM call turns the
  transcript into `{customer, items[], total, notes}`.
- **Customer matching**: spoken "Sharma ji" matches the stored "Sharma" (name
  normalization strips honorifics/punctuation); unknown spoken names create a
  new customer automatically.
- **Telegram**: token-free binding for customers (`/bind CODE`), a polling bot
  thread (no webhook/public URL needed), HTML receipts built per bill.
- **Payments (v1)**: `upi://pay` deep-link built from the owner's UPI ID — works
  with GPay/PhonePe/Paytm without a gateway account. `pay_link()` has a clean
  seam for a hosted gateway (Razorpay keys etc.) later; payment status flips
  manually until then.

## Setup

```bash
# backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env       # fill the keys below (never commit .env)
.venv/bin/python -m uvicorn backend.main:app --port 8000

# frontend (second shell)
cd frontend && npm install && npm run dev    # http://localhost:3000
```

On mobile, open the site on your phone (same network) and "Add to Home Screen"
for the standalone PWA experience.

### Environment keys

| Key | Needed for | Where to get it |
|---|---|---|
| `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` | voice-entry parsing | Preconfigured for **OpenRouter free models** (`https://openrouter.ai/api/v1`, key from openrouter.ai/keys) |
| `GNANI_API_KEY` | STT (voice → text) | Gnani.ai dashboard |
| `GOOGLE_CLIENT_ID` (+ same value as `NEXT_PUBLIC_GOOGLE_CLIENT_ID` for the frontend) | sign-in | Google Cloud Console → OAuth client (web), authorized origin `http://localhost:3000` |
| `TELEGRAM_BOT_TOKEN` | receipts on Telegram | @BotFather → /newbot |
| Owner's UPI ID | payment links | entered in Settings inside the app |

Without keys: `LLM_MOCK=1` runs a deterministic mock parser, and
`BOLO_DEV_LOGIN=1` (default while Google is unconfigured) adds a **dev login**
button that creates a clearly-labelled demo owner so the whole flow works
locally with zero external calls.

## Tests

```bash
.venv/bin/python -m pytest -q
```

Covers session sign/verify + tampering, honorific-aware customer matching,
parsed-entry normalization (missing totals, unpriced items, rejection cases),
the UPI link builder, and a full in-process owner flow (login → parse →
bill → paid) with the mocked LLM.

## Known limitations

- Payment status is manual (`mark-paid`); gateway auto-acknowledgements arrive
  with the Razorpay integration.
- No barge-in or live transcription preview yet — transcription happens after
  you release the button (double-tap keeps recording across sentences).
- Customer matching is text/romanized-based; two different people with the same
  normalized name merge into one khaata.
- The Telegram bot process polls `getUpdates` from the backend process only
  (works locally and on a single-host deploy; a serverless deploy needs the
  webhook mode).
- FREE OpenRouter models can under-count items on mumbled input; every entry
  shows the parsed preview before saving, and the raw transcript is stored.
- All model names stay disclosed: Gnani Prisma STT + whatever `LLM_MODEL` points
  to.
