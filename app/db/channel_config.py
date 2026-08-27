import json
from pathlib import Path

_CHANNEL_FILE = Path(__file__).parent.parent.parent / "data" / "channels.json"

DEFAULTS = {
    "channel": "webchat",
    "twilio_account_sid": "",
    "twilio_auth_token": "",
    "twilio_whatsapp_number": "whatsapp:+14155238886",
    "owner_whatsapp_number": "",
    "telegram_bot_token": "",
    "owner_telegram_chat_id": "",
    "resend_api_key": "",
    "support_email": "",
    "owner_email": "",
}


def _ensure_file():
    _CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _CHANNEL_FILE.exists():
        _CHANNEL_FILE.write_text(json.dumps(DEFAULTS, indent=2))


def load_channel_config() -> dict:
    _ensure_file()
    try:
        data = json.loads(_CHANNEL_FILE.read_text())
        merged = {**DEFAULTS, **data}
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save_channel_config(config: dict) -> dict:
    _ensure_file()
    current = load_channel_config()
    current.update({k: v for k, v in config.items() if k in DEFAULTS})
    _CHANNEL_FILE.write_text(json.dumps(current, indent=2))
    return current
