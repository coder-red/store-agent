from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    shopify_store_domain: str = "demo-store.myshopify.com"
    shopify_api_key: str = ""
    shopify_api_secret: str = ""

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    groq_api_key: Optional[str] = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    llm_provider: str = "groq"
    llm_model: str = "openai/gpt-oss-120b"

    supabase_url: str = ""
    supabase_key: str = ""

    demo_mode: bool = True
    # storefront plugin: "mock", "shopify", or "your.module:YourAdapterClass"
    platform: str = ""

    # persistence: "sqlite" (default, zero setup), "json", or "supabase"
    db_backend: str = "sqlite"

    @property
    def resolved_platform(self) -> str:
        return self.platform or ("mock" if self.demo_mode else "shopify")

    channel: str = "webchat"
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: Optional[str] = None
    owner_whatsapp_number: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    owner_telegram_chat_id: Optional[str] = None
    resend_api_key: Optional[str] = None
    support_email: Optional[str] = None
    owner_email: Optional[str] = None

    inventory_threshold: int = 5
    store_name: str = "Northlane"
    return_window_days: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def apply_stored_channel_config(self, config: dict):
        self.channel = config.get("channel", "webchat")
        self.twilio_account_sid = config.get("twilio_account_sid") or None
        self.twilio_auth_token = config.get("twilio_auth_token") or None
        self.twilio_whatsapp_number = config.get("twilio_whatsapp_number") or None
        self.owner_whatsapp_number = config.get("owner_whatsapp_number") or None
        self.telegram_bot_token = config.get("telegram_bot_token") or None
        self.owner_telegram_chat_id = config.get("owner_telegram_chat_id") or None
        self.resend_api_key = config.get("resend_api_key") or None
        self.support_email = config.get("support_email") or None
        self.owner_email = config.get("owner_email") or None


settings = Settings()
