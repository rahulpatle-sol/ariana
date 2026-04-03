"""
whatsapp.py — WhatsApp remote control via Twilio Sandbox (FREE)
Setup: twilio.com/console → WhatsApp Sandbox
"""
import threading
import requests
import os
from flask import Flask, request, Response

_ai_ref = None
_app = Flask(__name__)
_twilio_sid = "AC689a0d8eb4eb2c15f0778d46e47bda49"
_twilio_token = "69ff5dc2b8a02e272041f3b7c3825c32"
_twilio_from = "whatsapp:+14155238886"  # Twilio sandbox number
_your_number = "+919098842899"

def setup(ai, sid, token, your_number):
    global _ai_ref, _twilio_sid, _twilio_token, _your_number
    _ai_ref = ai
    _twilio_sid = sid
    _twilio_token = token
    _your_number = your_number

@_app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Twilio calls this when you send a WhatsApp message"""
    msg = request.form.get("Body","").strip()
    sender = request.form.get("From","")

    if not msg or not _ai_ref:
        return Response(status=200)

    # Process in background
    def _reply():
        from modules.ops import route
        result = route(msg, _ai_ref)
        reply = result if result else _ai_ref.chat(msg)
        send_whatsapp(reply[:1500], sender)

    threading.Thread(target=_reply, daemon=True).start()
    return Response(status=200)

def send_whatsapp(msg, to=None):
    """Send WhatsApp message via Twilio"""
    if not _twilio_sid or not _twilio_token:
        return False
    to = to or f"whatsapp:{_your_number}"
    try:
        requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{_twilio_sid}/Messages.json",
            auth=(_twilio_sid, _twilio_token),
            data={"From": _twilio_from, "To": to, "Body": msg}
        )
        return True
    except Exception as e:
        print(f"WhatsApp send error: {e}")
        return False

def start_server(port=5000):
    """Start Flask webhook server in background"""
    def _run():
        _app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
