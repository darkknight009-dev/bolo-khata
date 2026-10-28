"""LLM wrapper for persona generator, caller turns, judge and demo bot.

One place for OpenAI-compatible /chat/completions calls (LLM_BASE_URL + LLM_API_KEY).
LLM_MOCK=1 swaps in a deterministic mock for development and tests so the whole
text-mode pipeline runs with zero API credits.
"""
import json
import logging
import os
import random
import re

import httpx

from . import config

log = logging.getLogger("voiceqa.llm")

_RETRYABLE = (httpx.TimeoutException, httpx.TransportError)


class LLMError(RuntimeError):
    pass


def extract_json(text: str):
    """Robustly pull the first balanced JSON object/array out of an LLM reply."""
    if text is None:
        raise LLMError("empty LLM response")
    text = text.strip()
    # Strip markdown fences if present.
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    # Find first { or [ and take the balanced block from there.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        in_str = False
        esc = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:idx + 1])
                    except ValueError:
                        break
    raise LLMError(f"could not parse JSON from LLM response: {text[:120]!r}")


async def chat(messages: list[dict], temperature: float = 0.7,
               json_mode: bool = True, max_attempts: int = 3) -> str:
    """Return the raw content string of an OpenAI-compatible chat completion."""
    if config.LLM_MOCK:
        return _mock_reply(messages)

    url = config.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    # HTTP-Referer / X-Title are OpenRouter attribution headers, ignored elsewhere.
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "HTTP-Referer": os.getenv("VOICEQA_APP_URL", "http://localhost:3000"),
        "X-Title": "VoiceQA",
    }
    body = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 400 and "response_format" in body:
                    # Some OpenRouter free models reject response_format=json_object;
                    # our JSON extractor handles free-form replies, so drop it and retry.
                    body = {k: v for k, v in body.items() if k != "response_format"}
                    resp = await client.post(url, headers=headers, json=body)
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = LLMError(f"LLM HTTP {resp.status_code}")
            else:
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except _RETRYABLE as exc:
            last_err = exc
        except (httpx.HTTPStatusError, KeyError, ValueError) as exc:
            raise LLMError(f"LLM call failed: {exc}") from exc
        import asyncio
        await asyncio.sleep(1.5 * attempt)
    raise LLMError(f"LLM call failed after retries: {last_err}")


async def chat_json(messages: list[dict], temperature: float = 0.7):
    """chat() + strict JSON parsing. Retries once with a reminder on parse failure."""
    content = await chat(messages, temperature=temperature, json_mode=True)
    try:
        return extract_json(content)
    except LLMError as err:
        log.warning("JSON parse failed, retrying with reminder: %s", err)
        messages = messages + [{
            "role": "user",
            "content": "Your previous reply was not valid JSON. Return ONLY valid JSON.",
        }]
        content = await chat(messages, temperature=0.2, json_mode=True)
        return extract_json(content)


# ---------------------------------------------------------------- mock mode ---

_MOCK_GREETINGS = {
    "hi": "Haan hello, sunao kya baat hai",
    "ta": "வணக்கம், என் பிரச்சனை பற்றி பேசணும்",
    "mr": "नमस्कार, माझी अडचण ऐका",
    "kn": "ನಮಸ್ಕಾರ, ನನ್ನ ಸಮಸ್ಯೆ ಹೇಳಬೇಕು",
    "en": "Hello, I need help with my EMI",
}


def _mock_reply(messages: list[dict]) -> str:
    """Deterministic fake LLM for development. Clearly a mock, never used for live data."""
    sys_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
    user_text = " ".join(m.get("content", "") for m in messages if m.get("role") != "system")

    if "customer-service voice bot" in sys_text or "Indian phone callers" in sys_text:
        return json.dumps(_mock_personas(user_text))

    if "Sahayak Bank EMI helpline voice bot" in sys_text:
        return json.dumps(_mock_bot(user_text))

    if "strict QA reviewer" in sys_text:
        return json.dumps({
            "task_success": True, "language_handling": 4, "tone": 4, "recovery": 4,
            "failure_category": "none",
            "failure_reason": "Mock judge: transcript suggests the goal was addressed.",
        })

    if "kiryana" in sys_text or "Bolo Khata" in sys_text:
        return json.dumps({
            "customer": "Sharma",
            "language": "hi",
            "items": [
                {"name": "doodh", "qty": 1.0, "unit": "packet", "price": 30.0},
                {"name": "suji", "qty": 2.0, "unit": "packet", "price": 8.0},
            ],
            "total": 38.0,
            "notes": "",
        })

    # default: caller turn
    match = re.search(r"Language: ([a-z]+)", user_text)
    lang = match.group(1) if match else "hi"
    if "end_satisfied" in user_text or _count_caller_turns(user_text) >= 4:
        action = "end_satisfied"
    else:
        action = "continue"
    return json.dumps({"say": f"{_MOCK_GREETINGS.get(lang, 'Hello')} — mock caller line {random.randint(1, 99)}",
                       "action": action})


def _count_caller_turns(user_text: str) -> int:
    return user_text.count("Caller:") + user_text.count("[caller]")


def _mock_personas(user_text: str) -> list[dict]:
    langs = ["hi", "ta", "mr", "kn", "en"]
    mix = ["none", "light", "heavy"]
    emotions = ["calm", "confused", "angry", "rushed"]
    personas = []
    for i in range(6):
        personas.append({
            "name": f"Mock Persona {i + 1}",
            "language": langs[i % len(langs)],
            "code_mix": mix[i % len(mix)],
            "emotion": emotions[i % len(emotions)],
            "age_group": ["young", "middle", "elderly"][i % 3],
            "gender": ["female", "male"][i % 2],
            "noise": ["none", "street", "market", "train"][i % 4],
            "goal": "Find out this month's EMI amount and due date",
            "scenario": "customer wants EMI amount and due date",
            "hidden_facts": {"loan_id": f"LN{48000 + i}", "emi": 4200 + i * 100},
            "success_condition": "Bot states EMI amount and due date after verifying loan id",
            "opening_line": _MOCK_GREETINGS[langs[i % len(langs)]],
        })
    return personas


def _mock_bot(user_text: str) -> dict:
    if "LN" in user_text:
        return {"say": "Aapki EMI 4200 rupaye har mahine ki hai, due date 5 tarikh hai.",
                "action": "done", "language": "hi-IN"}
    return {"say": "Aapki EMI seva mein aapka swagat hai. Kripya loan ID batayein.",
            "action": "reply", "language": "hi-IN"}
