"""Quick script to test WhatsApp Cloud API and show the exact error."""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
TEMPLATE_NAME = os.environ.get("WHATSAPP_TEMPLATE_NAME", "")
TEMPLATE_LANGUAGE = os.environ.get("WHATSAPP_TEMPLATE_LANGUAGE", "pt_BR")
API_URL = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"


async def main(to_phone: str) -> None:
    print(f"PHONE_NUMBER_ID : {PHONE_NUMBER_ID}")
    print(f"TOKEN           : {ACCESS_TOKEN[:20]}...{ACCESS_TOKEN[-10:]}")
    print(f"TEMPLATE        : {TEMPLATE_NAME} / {TEMPLATE_LANGUAGE}")
    print(f"API_URL         : {API_URL}")
    print(f"TO              : {to_phone}")
    print()

    to = to_phone.replace("+", "").replace(" ", "").replace("-", "")

    # ── 1. check phone number registration ───────────────────────────────────
    print("=== 1. Checking phone number ID ===")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )
    print(f"Status : {r.status_code}")
    print(f"Body   : {r.text}\n")

    # ── 2. send plain text message ────────────────────────────────────────────
    print("=== 2. Sending plain-text message ===")
    payload_text = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": "Teste de OTP - Parrot Trips (plain text)"},
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload_text,
            timeout=10.0,
        )
    print(f"Status : {r.status_code}")
    print(f"Body   : {r.text}\n")

    # ── 3. send template message ──────────────────────────────────────────────
    if TEMPLATE_NAME:
        print(f"=== 3. Sending template '{TEMPLATE_NAME}' ===")
        payload_tpl = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": TEMPLATE_NAME,
                "language": {"code": TEMPLATE_LANGUAGE},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": "123456"}]},
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [{"type": "text", "text": "123456"}],
                    },
                ],
            },
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                },
                json=payload_tpl,
                timeout=10.0,
            )
        print(f"Status : {r.status_code}")
        print(f"Body   : {r.text}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_whatsapp.py +5511999999999")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
