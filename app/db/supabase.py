import json
import os
from datetime import datetime, timezone
from app.config import settings

# In-memory / JSON fallback store (used when Supabase is not configured,
# e.g. demo mode or local dev without a database).
_conversations: dict[str, list] = {}
_escalations: list[dict] = []

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
CONV_FILE = os.path.join(DATA_DIR, "conversations.json")
ESC_FILE = os.path.join(DATA_DIR, "escalations.json")


def _load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _db_enabled() -> bool:
    return bool(settings.supabase_url and settings.supabase_key)


def _client():
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_key)


# --- Conversations ---

async def get_conversation(customer_identifier: str) -> list:
    if _db_enabled():
        try:
            client = _client()
            res = client.table("conversations").select("messages").eq("customer_identifier", customer_identifier).maybe_single().execute()
            if res.data and res.data.get("messages"):
                return res.data["messages"]
            return []
        except Exception as e:
            print(f"Supabase get_conversation error: {e}")
            return []
    global _conversations
    if not _conversations:
        _conversations = _load_json(CONV_FILE)
    return _conversations.get(customer_identifier, [])


async def save_conversation(customer_identifier: str, messages: list):
    if _db_enabled():
        try:
            client = _client()
            now = datetime.now(timezone.utc).isoformat()
            existing = client.table("conversations").select("id").eq("customer_identifier", customer_identifier).maybe_single().execute()
            if existing.data:
                client.table("conversations").update({"messages": messages, "updated_at": now}).eq("customer_identifier", customer_identifier).execute()
            else:
                client.table("conversations").insert({
                    "customer_identifier": customer_identifier,
                    "messages": messages,
                    "created_at": now,
                    "updated_at": now,
                }).execute()
            return
        except Exception as e:
            print(f"Supabase save_conversation error: {e}; falling back to JSON")
    global _conversations
    _conversations[customer_identifier] = messages
    _save_json(CONV_FILE, _conversations)


async def get_all_conversations() -> dict:
    if _db_enabled():
        try:
            client = _client()
            res = client.table("conversations").select("customer_identifier, messages").execute()
            return {row["customer_identifier"]: row["messages"] for row in (res.data or [])}
        except Exception as e:
            print(f"Supabase get_all_conversations error: {e}")
            return {}
    global _conversations
    if not _conversations:
        _conversations = _load_json(CONV_FILE)
    return _conversations


# --- Escalations ---

async def get_all_escalations() -> list:
    if _db_enabled():
        try:
            client = _client()
            res = client.table("escalations").select("*").order("created_at", desc=True).execute()
            return list(res.data or [])
        except Exception as e:
            print(f"Supabase get_all_escalations error: {e}")
            return []
    global _escalations
    if not _escalations:
        loaded = _load_json(ESC_FILE)
        _escalations = loaded if isinstance(loaded, list) else []
    return _escalations


def log_escalation(customer_message: str, conversation_history: str, reason: str):
    if _db_enabled():
        try:
            client = _client()
            client.table("escalations").insert({
                "customer_message": customer_message,
                "conversation_snapshot": conversation_history,
                "reason": reason,
                "resolved": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            return
        except Exception as e:
            print(f"Supabase log_escalation error: {e}; falling back to JSON")
    global _escalations
    entry = {
        "id": len(_escalations) + 1,
        "customer_message": customer_message,
        "conversation_snapshot": conversation_history,
        "reason": reason,
        "resolved": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _escalations.append(entry)
    _save_json(ESC_FILE, _escalations)
