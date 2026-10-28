"""The only module that talks to Gnani. Endpoint details live here and nowhere else.

Contract verified against docs.gnani.ai (Quick Start, STT REST, TTS REST/SSE,
VC REST pages, "Last verified" 2026-08-05):

  Base URL:     https://api.vachana.ai          (env GNANI_BASE_URL)
  Auth header:  X-API-Key-ID: <key>
  STT REST:     POST /stt/v3   multipart: audio_file, model, language_code, format
                -> {"success", "request_id", "transcript", "model", ...}
  TTS REST:     POST /api/v1/tts/inference  JSON {text, voice, model, language, speed,
                audio_config{sample_rate, num_channels, sample_width, encoding, container}}
                -> 200 binary WAV
  VC:           POST /api/v1/tts/voice-clone/embeddings (multipart audio_file)
                -> {"embedding", "shape", "dtype"}; then TTS with model=vachana-vc-v1
                and speaker_embedding.

Errors: STT errors use {"success": false, "error": {"type": ...}}; TTS/VC use flat
{"success": false, "message", "status_code"}; auth/rate-limit errors use
{"detail": {"error_code", "message", "status_code"}}. Rate limits carry no
Retry-After; we back off and retry at most twice (PRD rule).
"""
import asyncio
import base64
import hashlib
import logging
import time

import httpx

from . import config
from .models import CreditLog, load, dump

log = logging.getLogger("voiceqa.gnani")

_MAX_RETRIES = 2
_GNANI_LIMIT = asyncio.Semaphore(max(1, config.GNANI_CONCURRENCY))


class GnaniError(RuntimeError):
    """Provider failure the caller must see as a real failure (never fabricated)."""

    def __init__(self, category: str, message: str, status: int | None = None):
        super().__init__(f"{category}: {message}")
        self.category = category      # auth | rate_limited | insufficient_credit | invalid_audio | service | unknown
        self.message = message
        self.status = status


def _raise_for_status_payload(payload: dict | list, status: int) -> None:
    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, dict):
        code = str(detail.get("error_code", "")).upper()
        msg = str(detail.get("message", "request failed"))
        if code in ("MISSING_API_KEY", "INVALID_API_KEY"):
            raise GnaniError("auth", msg, status)
        if code == "RATE_LIMITED":
            raise GnaniError("rate_limited", msg, status)
        if status == 402:
            raise GnaniError("insufficient_credit", msg, status)
        if code == "SCOPE_NOT_ALLOWED":
            raise GnaniError("auth", msg, status)
        raise GnaniError("service", msg, status)
    if isinstance(payload, dict) and payload.get("success") is False:
        err = payload.get("error")
        if isinstance(err, dict):
            etype = str(err.get("type", "")).upper()
            msg = str(err.get("message", "request failed"))
        else:
            msg = str(payload.get("message", "request failed"))
            etype = ""
        if "FORBIDDEN" in etype or "credit" in msg.lower():
            raise GnaniError("insufficient_credit", msg, status)
        if "Field required" in msg or "Value error" in msg or "not supported" in msg:
            raise GnaniError("invalid_audio", msg, status)
        raise GnaniError("service", msg, status)


class GnaniClient:
    def __init__(self, run_id: int | None = None):
        self.run_id = run_id

    # ---------------------------------------------------------------- helpers -

    def _headers(self, extra: dict | None = None) -> dict:
        if not config.GNANI_API_KEY:
            raise GnaniError("auth", "GNANI_API_KEY is not configured", None)
        headers = {"X-API-Key-ID": config.GNANI_API_KEY}
        if extra:
            headers.update(extra)
        return headers

    def _log_credit(self, function: str, model: str, units: int, unit_type: str,
                    request_id: str | None = None) -> None:
        from .db import get_session

        with get_session() as session:
            session.add(CreditLog(ts=None, function=function, model=model, units=units,
                                  unit_type=unit_type, credits=None, run_id=self.run_id,
                                  request_id=request_id))
            session.commit()

    # ------------------------------------------------------------------- STT --

    async def stt(self, audio_bytes: bytes, language: str = "hi-IN",
                  model: str = "", filename: str = "audio.wav") -> dict:
        """Transcribe WAV/MP3/OGG audio. Returns {'text', 'request_id', 'model', 'language'}."""
        model = model or config.GNANI_STT_MODEL
        url = config.GNANI_BASE_URL.rstrip("/") + "/stt/v3"
        data = {"language_code": language}
        if model and model != "auto":
            data["model"] = model
        files = {"audio_file": (filename, audio_bytes, "audio/wav")}

        last_err: GnaniError | None = None
        for attempt in range(_MAX_RETRIES + 1):
            started = time.monotonic()
            try:
                async with _GNANI_LIMIT:
                    async with httpx.AsyncClient(timeout=60) as client:
                        resp = await client.post(url, headers=self._headers(),
                                                 data=data, files=files)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_err = GnaniError("service", f"network error: {exc}", None)
                continue
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = GnaniError("rate_limited" if resp.status_code == 429
                                      else "service", f"HTTP {resp.status_code}",
                                      resp.status_code)
                await self._backoff(attempt)
                continue
            try:
                payload = resp.json()
            except ValueError:
                raise GnaniError("service", f"non-JSON STT response (HTTP {resp.status_code})",
                                 resp.status_code) from None
            _raise_for_status_payload(payload, resp.status_code)
            if not payload.get("success"):
                raise GnaniError("service", str(payload.get("message", "STT failed")),
                                 resp.status_code)
            result = {
                "text": str(payload.get("transcript", "")),
                "request_id": payload.get("request_id"),
                "model": str(payload.get("model", model)),
                "language": payload.get("detected_language_code", language),
                "elapsed_ms": int((time.monotonic() - started) * 1000),
            }
            self._log_credit("stt", result["model"], self._wav_seconds(audio_bytes),
                             "seconds", result["request_id"])
            return result
        raise last_err or GnaniError("service", "STT failed", None)

    # ------------------------------------------------------------------- TTS --

    async def tts(self, text: str, language: str = "hi-IN", voice_id: str = "",
                  speed: float = 1.0, model: str = "") -> bytes:
        """Synthesize text to WAV (16 kHz mono linear PCM best for our pipeline)."""
        model = model or config.GNANI_TTS_MODEL
        url = config.GNANI_BASE_URL.rstrip("/") + "/api/v1/tts/inference"
        payload = {
            "text": text,
            "voice": voice_id,
            "model": model,
            "language": language,
            "speed": speed,
            "audio_config": {
                "sample_rate": 16000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        }
        last_err: GnaniError | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with _GNANI_LIMIT:
                    async with httpx.AsyncClient(timeout=90) as client:
                        resp = await client.post(url, headers=self._headers(
                            {"Content-Type": "application/json"}), json=payload)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_err = GnaniError("service", f"network error: {exc}", None)
                continue
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = GnaniError("rate_limited" if resp.status_code == 429
                                      else "service", f"HTTP {resp.status_code}",
                                      resp.status_code)
                await self._backoff(attempt)
                continue
            content_type = resp.headers.get("content-type", "")
            if "audio/wav" in content_type and resp.status_code == 200:
                self._log_credit("tts", model, len(text), "chars")
                return resp.content
            try:
                body = resp.json()
            except ValueError:
                raise GnaniError("service",
                                 f"unexpected TTS response (HTTP {resp.status_code}, {content_type})",
                                 resp.status_code) from None
            _raise_for_status_payload(body, resp.status_code)
            raise GnaniError("service", str(body.get("message", "TTS failed")), resp.status_code)
        raise last_err or GnaniError("service", "TTS failed", None)

    # ------------------------------------------------------------------- VC ---

    async def clone_voice(self, sample_audio: bytes, consent_audio: bytes) -> str:
        """Create a speaker_embedding from consent + sample audio (P1; consent required)."""
        url = config.GNANI_BASE_URL.rstrip("/") + "/api/v1/tts/voice-clone/embeddings"
        try:
            async with _GNANI_LIMIT:
                async with httpx.AsyncClient(timeout=90) as client:
                    resp = await client.post(
                        url, headers=self._headers(),
                        files={"audio_file": ("sample.wav", sample_audio, "audio/wav")},
                        data={"consent": base64.b64encode(consent_audio).decode()})
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise GnaniError("service", f"network error: {exc}", None) from exc
        if resp.status_code in (429, 500, 502, 503, 504):
            raise GnaniError("service", f"HTTP {resp.status_code}", resp.status_code)
        try:
            payload = resp.json()
        except ValueError:
            raise GnaniError("service", "non-JSON embeddings response", resp.status_code) from None
        _raise_for_status_payload(payload, resp.status_code)
        if not payload.get("embedding"):
            raise GnaniError("service", "no embedding returned", resp.status_code)
        self._log_credit("clone", "vachana-vc-v1", 0, "seconds")
        return dump({"embedding": payload["embedding"], "shape": payload.get("shape"),
                     "dtype": payload.get("dtype")})

    # ---------------------------------------------------------------- misc ---

    @staticmethod
    async def _backoff(attempt: int) -> None:
        await asyncio.sleep(2.0 * (attempt + 1))

    @staticmethod
    def _wav_seconds(audio_bytes: bytes) -> int:
        """Rough duration estimate from a WAV header; falls back to byte-length estimate."""
        try:
            import io
            import wave

            with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate() or 16000
                return max(1, round(frames / rate))
        except Exception:
            return max(1, len(audio_bytes) // 32000)


def tts_cache_key(text: str, voice: str, language: str, speed: float) -> str:
    return hashlib.sha256(f"{text}|{voice}|{language}|{speed}".encode()).hexdigest()
