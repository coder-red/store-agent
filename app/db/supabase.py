"""Conversation + escalation storage.

Default backend is SQLite (zero setup, no account, no key). Supabase
Postgres is used automatically only if SUPABASE_URL/KEY are set.

Every function falls back to a JSON file if neither is available, so the
app always runs even with no persistence configured.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from app.config import settings

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "store.db")
CONV_FILE = os.path.join(DATA_DIR, "conversations.json")
ESC_FILE = os.path.join(DATA_DIR, "escalations.json")

_conversations: dict[str, list] = {}
_escalations: list[dict] = []


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
    return settings.db_backend == "sqlite" or bool(settings.supabase_url and settings.supabase_key)


def _db_backend() -> str:
    if settings.supabase_url and settings.supabase_key:
        return "supabase"
    return "sqlite"


def _connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            customer_identifier TEXT PRIMARY KEY,
            messages TEXT NOT NULL DEFAULT '[]',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_message TEXT NOT NULL,
            conversation_snapshot TEXT,
            reason TEXT,
            resolved INTEGER NOT NULL DEFAULT 0,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def _supabase_client():
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_key)


# --- Conversations ---

async def get_conversation(customer_identifier: str) -> list:
    global _conversations
    if _db_enabled():
        try:
            if _db_backend() == "sqlite":
                conn = _connect()
                row = conn.execute("SELECT messages FROM conversations WHERE customer_identifier=?", (customer_identifier,)).fetchone()
                conn.close()
                if row:
                    return json.loads(row["messages"])
                return []
            else:
                client = _supabase_client()
                res = client.table("conversations").select("messages").eq("customer_identifier", customer_identifier).maybe_single().execute()
                if res.data and res.data.get("messages"):
                    return res.data["messages"]
                return []
        except Exception as e:
            print(f"get_conversation error ({_db_backend()}): {e}; falling back to JSON")
            _fallback_json_load()
            return _conversations.get(customer_identifier, [])

    _fallback_json_load()
    return _conversations.get(customer_identifier, [])


async def save_conversation(customer_identifier: str, messages: list):
    if _db_enabled():
        try:
            now = datetime.now(timezone.utc).isoformat()
            if _db_backend() == "sqlite":
                conn = _connect()
                conn.execute("""
                    INSERT INTO conversations (customer_identifier, messages, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(customer_identifier) DO UPDATE SET
                        messages=excluded.messages, updated_at=excluded.updated_at
                """, (customer_identifier, json.dumps(messages, default=str), now, now))
                conn.commit()
                conn.close()
                return
            else:
                client = _supabase_client()
                existing = client.table("conversations").select("id").eq("customer_identifier", customer_identifier).maybe_single().execute()
                if existing.data:
                    client.table("conversations").update({"messages": messages, "updated_at": now}).eq("customer_identifier", customer_identifier).execute()
                else:
                    client.table("conversations").insert({
                        "customer_identifier": customer_identifier,
                        "messages": messages, "created_at": now, "updated_at": now,
                    }).execute()
                return
        except Exception as e:
            print(f"save_conversation error ({_db_backend()}): {e}; falling back to JSON")
    global _conversations
    _conversations[customer_identifier] = messages
    _save_json(CONV_FILE, _conversations)


async def get_all_conversations() -> dict:
    global _conversations
    if _db_enabled():
        try:
            if _db_backend() == "sqlite":
                conn = _connect()
                rows = conn.execute("SELECT customer_identifier, messages FROM conversations").fetchall()
                conn.close()
                return {r["customer_identifier"]: json.loads(r["messages"]) for r in rows}
            else:
                client = _supabase_client()
                res = client.table("conversations").select("customer_identifier, messages").execute()
                return {row["customer_identifier"]: row["messages"] for row in (res.data or [])}
        except Exception as e:
            print(f"get_all_conversations error ({_db_backend()}): {e}; falling back to JSON")
            _fallback_json_load()
            return _conversations
    _fallback_json_load()
    return _conversations


# --- Escalations ---

async def get_all_escalations() -> list:
    global _escalations
    if _db_enabled():
        try:
            if _db_backend() == "sqlite":
                conn = _connect()
                rows = conn.execute("SELECT * FROM escalations ORDER BY id DESC").fetchall()
                conn.close()
                return [dict(r) for r in rows]
            else:
                client = _supabase_client()
                res = client.table("escalations").select("*").order("created_at", desc=True).execute()
                return list(res.data or [])
        except Exception as e:
            print(f"get_all_escalations error ({_db_backend()}): {e}; falling back to JSON")
            _fallback_json_load()
            return _escalations
    _fallback_json_load()
    return _escalations


def log_escalation(customer_message: str, conversation_history: str, reason: str):
    if _db_enabled():
        try:
            now = datetime.now(timezone.utc).isoformat()
            if _db_backend() == "sqlite":
                conn = _connect()
                conn.execute(
                    "INSERT INTO escalations (customer_message, conversation_snapshot, reason, resolved, created_at) VALUES (?,?,?,0,?)",
                    (customer_message, conversation_history, reason, now),
                )
                conn.commit()
                conn.close()
                return
            else:
                client = _supabase_client()
                client.table("escalations").insert({
                    "customer_message": customer_message,
                    "conversation_snapshot": conversation_history,
                    "reason": reason, "resolved": False, "created_at": now,
                }).execute()
                return
        except Exception as e:
            print(f"log_escalation error ({_db_backend()}): {e}; falling back to JSON")
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


def _fallback_json_load():
    global _conversations, _escalations
    if not _conversations:
        _conversations = _load_json(CONV_FILE)
    if not _escalations:
        loaded = _load_json(ESC_FILE)
        _escalations = loaded if isinstance(loaded, list) else []
