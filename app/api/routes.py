from fastapi import APIRouter, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from app.agents.multi_agent import run_agent_sync
from app.agents.sentiment import analyze_sentiment
from app.db.supabase import get_conversation, save_conversation, get_all_conversations, get_all_escalations
from app.db.channel_config import load_channel_config, save_channel_config
from app.channels.manager import channel_manager
from app.commerce.service import get_store_provider, reset_provider
from app.config import settings

router = APIRouter()


class TestMessage(BaseModel):
    message: str
    customer_identifier: str = "test-user"


class DemoConfig(BaseModel):
    demo_mode: bool
    store_name: Optional[str] = None
    return_window_days: Optional[int] = None


class EmailMessage(BaseModel):
    from_address: str
    subject: str
    body: str


class DescriptionRequest(BaseModel):
    name: str
    category: str
    features: str
    audience: str = "online shoppers"


class ChannelConfig(BaseModel):
    channel: str = "webchat"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"
    owner_whatsapp_number: str = ""
    telegram_bot_token: str = ""
    owner_telegram_chat_id: str = ""
    resend_api_key: str = ""
    support_email: str = ""
    owner_email: str = ""


# In-memory email store (for demo, supersedes supabase)
_mailbox: dict[str, list[dict]] = {}
_email_timestamps: list[dict] = []


async def _process_message(message: str, customer_identifier: str) -> str:
    history = await get_conversation(customer_identifier)
    response_text = await run_agent_sync(message, history)
    sentiment = await analyze_sentiment(message)
    now = __import__("datetime").datetime.now().isoformat()
    updated_messages = history + [
        {"role": "user", "content": message, "timestamp": now, "sentiment": sentiment},
        {"role": "assistant", "content": response_text, "timestamp": now},
    ]
    await save_conversation(customer_identifier, updated_messages)
    return response_text


@router.post("/webhook/test")
async def test_webhook(payload: TestMessage):
    response = await _process_message(payload.message, payload.customer_identifier)
    return {"response": response}


@router.post("/webhook/email")
async def email_webhook(email: EmailMessage):
    cid = f"email:{email.from_address}"
    body = f"Subject: {email.subject}\n\n{email.body}"
    _mailbox.setdefault(cid, [])
    _mailbox[cid].append({
        "role": "user", "content": body, "timestamp": __import__("datetime").datetime.now().isoformat(),
        "subject": email.subject, "from": email.from_address, "channel": "email",
    })
    _email_timestamps.append({"from": email.from_address, "subject": email.subject, "received_at": __import__("datetime").datetime.now().isoformat()})
    response = await _process_message(body, cid)
    _mailbox[cid].append({
        "role": "assistant", "content": response, "timestamp": __import__("datetime").datetime.now().isoformat(),
        "channel": "email",
    })
    return {"response": response, "customer_identifier": cid}


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From", "")
    body = form.get("Body", "")
    if not body or not from_number:
        return PlainTextResponse("<Response></Response>", media_type="application/xml")
    cid = f"whatsapp:{from_number}"
    response = await _process_message(body, cid)
    await channel_manager.send_message(from_number, response)
    return PlainTextResponse("<Response></Response>", media_type="application/xml")


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")
    if not text or not chat_id:
        return {"ok": True}
    cid = f"telegram:{chat_id}"
    response = await _process_message(text, cid)
    await channel_manager.send_message(chat_id, response)
    return {"ok": True}


@router.get("/api/emails")
async def list_emails():
    return {"emails": sorted(_email_timestamps, key=lambda e: e["received_at"], reverse=True), "mailbox": {k: len(v) for k, v in _mailbox.items()}}


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "store": settings.store_name,
        "channel": settings.channel,
        "demo_mode": settings.demo_mode,
        "llm_provider": settings.llm_provider,
    }


@router.get("/api/conversations")
async def list_conversations():
    convs = await get_all_conversations()
    result = []
    for cid, msgs in convs.items():
        status = "open"
        last_msg = ""
        last_sentiment = "neutral"
        channel = "webchat"
        if msgs:
            last = msgs[-1] if isinstance(msgs[-1], dict) else {}
            last_content = last.get("content", "")
            for keyword in ["escalated", "human agent will follow up", "escalate"]:
                if keyword in last_content.lower():
                    status = "escalated"
                    break
            last_msg = last_content[:100] if len(last_content) > 100 else last_content
            if last.get("channel"):
                channel = last["channel"]
            if cid.startswith("email:"):
                channel = "email"
            last_sentiment = last.get("sentiment", "neutral") if isinstance(msgs[-1], dict) else "neutral"
            sent = [m.get("sentiment", "") for m in msgs if isinstance(m, dict) and m.get("sentiment")]
            if sent:
                last_sentiment = sent[-1]
        result.append({
            "customer_identifier": cid,
            "message_count": len(msgs),
            "status": status,
            "channel": channel,
            "last_message": last_msg,
            "last_sentiment": last_sentiment,
            "last_updated": msgs[-1].get("timestamp", "") if msgs else "",
        })
    result.sort(key=lambda x: x["last_updated"], reverse=True)
    return {"conversations": result}


@router.get("/api/conversations/{customer_id}")
async def get_conversation_detail(customer_id: str):
    msgs = await get_conversation(customer_id)
    return {"customer_identifier": customer_id, "messages": msgs}


@router.get("/api/escalations")
async def list_escalations():
    escalations = await get_all_escalations()
    return {"escalations": escalations}


@router.get("/api/analytics")
async def get_analytics():
    convs = await get_all_conversations()
    escalations = await get_all_escalations()
    total = len(convs)
    total_msgs = sum(len(v) for v in convs.values())
    escalated_count = len(escalations)

    # Revenue + order stats come from the real store via the commerce
    # provider, so the numbers reflect actual orders, not mock data.
    provider = get_store_provider()
    orders = await provider.get_all_orders()
    paid_orders = [o for o in orders if o.financial_status == "paid"]
    total_revenue = sum(float(o.total_price) for o in paid_orders)
    fulfilled = sum(1 for o in orders if o.fulfillment_status == "fulfilled")
    pending = sum(1 for o in orders if o.financial_status == "pending")

    # Cart recovery. Uses the provider's abandoned carts through the
    # CommerceProvider contract so it works for real stores too.
    carts = await provider.get_abandoned_carts()
    total_carts = len(carts)
    recovered_carts = sum(1 for c in carts if c.get("recovery_status") == "recovered")
    recovered_revenue = sum(float(c["total"]) for c in carts if c.get("recovery_status") == "recovered")

    pos = neg = neutral = 0
    for msgs in convs.values():
        for m in msgs:
            s = m.get("sentiment", "") if isinstance(m, dict) else ""
            if s == "positive": pos += 1
            elif s == "negative": neg += 1
            else: neutral += 1
    total_sentiment = pos + neg + neutral

    return {
        "total_conversations": total,
        "total_messages": total_msgs,
        "escalated_count": escalated_count,
        "escalation_rate": round(escalated_count / total * 100, 1) if total > 0 else 0,
        "channels": [settings.channel],
        "orders": {
            "total_orders": len(orders),
            "paid": len(paid_orders),
            "fulfilled": fulfilled,
            "pending": pending,
            "total_revenue": f"${total_revenue:.2f}",
        },
        "cart_recovery": {
            "total_carts": total_carts,
            "recovered": recovered_carts,
            "recovery_rate": round(recovered_carts / total_carts * 100, 1) if total_carts > 0 else 0,
            "recovered_revenue": f"${recovered_revenue:.2f}",
        },
        "sentiment": {
            "positive": pos,
            "negative": neg,
            "neutral": neutral,
            "positive_rate": round(pos / total_sentiment * 100, 1) if total_sentiment > 0 else 0,
            "negative_rate": round(neg / total_sentiment * 100, 1) if total_sentiment > 0 else 0,
        },
    }


@router.post("/api/generate-descriptions")
async def generate_descriptions(req: DescriptionRequest):
    from app.agents.product_describer import ProductDescriber
    describer = ProductDescriber()
    result = await describer.generate(req.name, req.category, req.features, req.audience)
    return {"product": req.name, "variations": result}


@router.get("/api/settings")
async def get_settings():
    return {
        "demo_mode": settings.demo_mode,
        "store_name": settings.store_name,
        "return_window_days": settings.return_window_days,
        "channel": settings.channel,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }


@router.put("/api/settings")
async def update_settings(config: DemoConfig):
    settings.demo_mode = config.demo_mode
    if config.store_name:
        settings.store_name = config.store_name
    if config.return_window_days:
        settings.return_window_days = config.return_window_days
    reset_provider()
    return {"status": "updated", "demo_mode": settings.demo_mode}


@router.get("/api/channels")
async def get_channels():
    return load_channel_config()


@router.put("/api/channels")
async def update_channels(config: ChannelConfig):
    saved = save_channel_config(config.model_dump())
    settings.channel = saved["channel"]
    settings.twilio_account_sid = saved["twilio_account_sid"] or None
    settings.twilio_auth_token = saved["twilio_auth_token"] or None
    settings.twilio_whatsapp_number = saved["twilio_whatsapp_number"] or None
    settings.owner_whatsapp_number = saved["owner_whatsapp_number"] or None
    settings.telegram_bot_token = saved["telegram_bot_token"] or None
    settings.owner_telegram_chat_id = saved["owner_telegram_chat_id"] or None
    settings.resend_api_key = saved["resend_api_key"] or None
    settings.support_email = saved["support_email"] or None
    settings.owner_email = saved["owner_email"] or None
    return {"status": "updated", "channel": saved["channel"]}


@router.get("/api/products")
async def list_products():
    provider = get_store_provider()
    products = await provider.get_all_products()
    return {"products": [{"id": p.id, "title": p.title, "vendor": p.vendor, "variants": [{"title": v.title, "price": v.price, "stock": v.inventory_quantity, "sku": v.sku} for v in p.variants]} for p in products]}


@router.get("/api/orders")
async def list_orders():
    provider = get_store_provider()
    orders = await provider.get_all_orders()
    return {"orders": [{
        "id": o.id,
        "order_number": o.order_number,
        "customer_name": o.customer_name,
        "customer_email": o.customer_email,
        "total": o.total_price,
        "currency": o.currency,
        "status": o.financial_status,
        "fulfillment": o.fulfillment_status,
        "created_at": o.created_at,
        "tracking_company": o.tracking_company,
        "tracking_number": o.tracking_number,
        "tracking_url": o.tracking_url,
    } for o in orders]}


@router.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    provider = get_store_provider()
    order = await provider.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "total": order.total_price,
        "currency": order.currency,
        "status": order.financial_status,
        "fulfillment": order.fulfillment_status,
        "created_at": order.created_at,
        "tracking_company": order.tracking_company,
        "tracking_number": order.tracking_number,
        "tracking_url": order.tracking_url,
        "line_items": order.line_items or [],
    }


connected_websockets: set[WebSocket] = set()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg = data.get("message", "")
            customer_id = data.get("customer_id", "web-user")
            response = await _process_message(msg, customer_id)
            await websocket.send_json({"type": "response", "message": response, "customer_id": customer_id})
    except WebSocketDisconnect:
        connected_websockets.discard(websocket)
