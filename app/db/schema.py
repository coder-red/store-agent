"""Create the Supabase/Postgres tables if they do not exist.

Uses a single connection string from SUPABASE_DATABASE_URL (the direct
Postgres connection), falling back to REST DDL is not practical, so this
is intentionally optional: the tables can also be created once in the
Supabase dashboard SQL editor using the SQL below.

CREATE TABLE IF NOT EXISTS conversations (
  id bigserial primary key,
  customer_identifier text unique not null,
  messages jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

CREATE TABLE IF NOT EXISTS escalations (
  id bigserial primary key,
  customer_message text not null,
  conversation_snapshot text,
  reason text,
  resolved boolean not null default false,
  created_at timestamptz not null default now()
);
"""
import os
from app.config import settings


def init_schema():
    """Best-effort schema creation. No-op if no direct Postgres URL is set."""
    db_url = getattr(settings, "supabase_database_url", None) or os.getenv("SUPABASE_DATABASE_URL")
    if not db_url:
        return False
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed; skipping schema init (create tables in Supabase SQL editor)")
        return False
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
              id bigserial primary key,
              customer_identifier text unique not null,
              messages jsonb not null default '[]'::jsonb,
              created_at timestamptz not null default now(),
              updated_at timestamptz not null default now()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
              id bigserial primary key,
              customer_message text not null,
              conversation_snapshot text,
              reason text,
              resolved boolean not null default false,
              created_at timestamptz not null default now()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Supabase schema ready")
        return True
    except Exception as e:
        print(f"Supabase schema init failed: {e}")
        return False
