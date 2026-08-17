"""SMS + WhatsApp notifications — provider-agnostic.

Default provider is "console" (logs the message) so the whole flow works with no
credentials. Set env vars to activate a real provider:

  SMS:       NOTIFY_SMS_PROVIDER = console | msg91 | twilio
             msg91:  MSG91_AUTHKEY, MSG91_SENDER
             twilio: TWILIO_SID, TWILIO_TOKEN, TWILIO_SMS_FROM
  WhatsApp:  NOTIFY_WA_PROVIDER  = console | whatsapp_cloud | twilio
             whatsapp_cloud: WHATSAPP_TOKEN, WHATSAPP_PHONE_ID
             twilio:         TWILIO_SID, TWILIO_TOKEN, TWILIO_WA_FROM (e.g. whatsapp:+14155238886)

  NOTIFY_COUNTRY_CODE (default 91) is prefixed to 10-digit numbers.
"""

import os
import re
import json
import base64
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

SMS_PROVIDER = os.getenv("NOTIFY_SMS_PROVIDER", "console").lower()
WA_PROVIDER = os.getenv("NOTIFY_WA_PROVIDER", "console").lower()
CC = os.getenv("NOTIFY_COUNTRY_CODE", "91")


def normalize(phone: str, plus: bool = True) -> str | None:
    d = re.sub(r"\D", "", str(phone or ""))
    if not d:
        return None
    if len(d) == 10:
        d = CC + d
    return ("+" + d) if plus else d


def _post(url, data=None, headers=None, as_json=False):
    if as_json:
        body = json.dumps(data).encode()
    else:
        body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.read().decode("utf-8", "ignore")


# ─────────────────────────── SMS ───────────────────────────

def send_sms(to: str, text: str) -> tuple[bool, str]:
    num = normalize(to, plus=False)
    if not num:
        return False, "invalid number"
    try:
        if SMS_PROVIDER == "msg91":
            authkey = os.getenv("MSG91_AUTHKEY", "")
            sender = os.getenv("MSG91_SENDER", "SSJDCO")
            if not authkey:
                return False, "MSG91_AUTHKEY not set"
            qs = urllib.parse.urlencode({
                "authkey": authkey, "mobiles": num, "message": text,
                "sender": sender, "route": "4", "country": CC,
            })
            st, _ = _post("https://api.msg91.com/api/sendhttp.php?" + qs)
            return (200 <= st < 300), f"msg91 http {st}"

        if SMS_PROVIDER == "twilio":
            sid, token = os.getenv("TWILIO_SID", ""), os.getenv("TWILIO_TOKEN", "")
            frm = os.getenv("TWILIO_SMS_FROM", "")
            if not (sid and token and frm):
                return False, "Twilio SMS env not set"
            auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
            st, _ = _post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                data={"From": frm, "To": "+" + num, "Body": text},
                headers={"Authorization": f"Basic {auth}"},
            )
            return (200 <= st < 300), f"twilio http {st}"

        logger.info("[SMS:console] to=%s | %s", num, text)
        return True, "console (logged)"
    except Exception as e:  # noqa: BLE001
        logger.error("SMS send failed to %s: %s", num, e)
        return False, str(e)


# ─────────────────────────── WhatsApp ───────────────────────────

def send_whatsapp(to: str, text: str) -> tuple[bool, str]:
    num = normalize(to, plus=False)
    if not num:
        return False, "invalid number"
    try:
        if WA_PROVIDER == "whatsapp_cloud":
            token = os.getenv("WHATSAPP_TOKEN", "")
            phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
            if not (token and phone_id):
                return False, "WhatsApp Cloud env not set"
            st, _ = _post(
                f"https://graph.facebook.com/v19.0/{phone_id}/messages",
                data={"messaging_product": "whatsapp", "to": num, "type": "text",
                      "text": {"body": text}},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                as_json=True,
            )
            return (200 <= st < 300), f"whatsapp_cloud http {st}"

        if WA_PROVIDER == "twilio":
            sid, token = os.getenv("TWILIO_SID", ""), os.getenv("TWILIO_TOKEN", "")
            frm = os.getenv("TWILIO_WA_FROM", "")
            if not (sid and token and frm):
                return False, "Twilio WhatsApp env not set"
            auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
            st, _ = _post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                data={"From": frm, "To": f"whatsapp:+{num}", "Body": text},
                headers={"Authorization": f"Basic {auth}"},
            )
            return (200 <= st < 300), f"twilio http {st}"

        logger.info("[WhatsApp:console] to=%s | %s", num, text)
        return True, "console (logged)"
    except Exception as e:  # noqa: BLE001
        logger.error("WhatsApp send failed to %s: %s", num, e)
        return False, str(e)


def provider_status() -> dict:
    return {
        "sms_provider": SMS_PROVIDER,
        "whatsapp_provider": WA_PROVIDER,
        "sms_live": SMS_PROVIDER != "console",
        "whatsapp_live": WA_PROVIDER != "console",
    }
