from langchain_core.tools import tool
from app.commerce.service import get_store_provider
from app.agents.knowledge_base import query_knowledge_base as _kb_search
from app.config import settings
from datetime import datetime, timezone


@tool
async def get_order_status(order_number: str = "", customer_email: str = "") -> str:
    """Fetch the current status, fulfillment info, and tracking details for an order. Provide either order_number or customer_email."""
    provider = get_store_provider()
    order = None
    if order_number:
        order = await provider.get_order_by_number(order_number)
    if not order and customer_email:
        order = await provider.get_order_by_email(customer_email)
    if not order:
        return f"No order found matching order_number='{order_number}' or email='{customer_email}'."
    parts = [
        f"Order #{order.order_number}",
        f"Status: {order.financial_status}",
        f"Fulfillment: {order.fulfillment_status}",
        f"Total: {order.currency} {order.total_price}",
    ]
    if order.tracking_number:
        parts.append(f"Tracking: {order.tracking_company} - {order.tracking_number}")
        parts.append(f"Track here: {order.tracking_url}")
    return "\n".join(parts)


@tool
async def check_return_eligibility(order_number: str) -> str:
    """Check whether an order is within the return window and eligible for a return."""
    provider = get_store_provider()
    order = await provider.get_order_by_number(order_number)
    if not order:
        return f"No order found with number {order_number}."
    created = datetime.fromisoformat(order.created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    days_since = (now - created).days
    window = settings.return_window_days
    remaining = window - days_since
    if remaining > 0:
        return f"Order #{order.order_number} is eligible for return. {remaining} days remaining in the {window}-day return window."
    return f"Order #{order.order_number} is outside the {window}-day return window ({days_since} days since delivery). Returns are no longer accepted."


@tool
async def get_product_info(query: str) -> str:
    """Search for products by name, description, or category. Returns availability and pricing."""
    provider = get_store_provider()
    products = await provider.search_products(query)
    if not products:
        return f"No products found matching '{query}'."
    results = []
    for p in products:
        variants = [f"  - {v.title}: ${v.price} ({v.inventory_quantity} in stock, SKU: {v.sku})" for v in p.variants]
        results.append(f"{p.title} (by {p.vendor})")
        results.extend(variants)
    return "\n".join(results)


@tool
async def check_fulfillment_status(order_number: str) -> str:
    """Get detailed fulfillment and shipping status for an order including carrier and tracking."""
    provider = get_store_provider()
    order = await provider.get_order_by_number(order_number)
    if not order:
        return f"No order found with number {order_number}."
    fulfillments = await provider.get_fulfillments(order.id)
    if not fulfillments:
        return f"Order #{order.order_number} has no fulfillment records yet."
    parts = [f"Order #{order.order_number} fulfillment:"]
    for f in fulfillments:
        parts.append(f"  Status: {f['status']}")
        if f["tracking_company"]:
            parts.append(f"  Carrier: {f['tracking_company']}")
            parts.append(f"  Tracking: {f['tracking_number']}")
            parts.append(f"  Track at: {f['tracking_url']}")
    return "\n".join(parts)


@tool
async def query_store_policies(query: str) -> str:
    """Search store policies, FAQs, and guidelines. Use for questions about returns, shipping, payment, warranties, cancellations, gift cards, size guides, privacy, and loyalty programs."""
    return await _kb_search(query)


@tool
async def escalate_to_human(customer_message: str, conversation_history: str = "", reason: str = "") -> str:
    """Escalate a customer issue to a human support agent. Use when you cannot resolve, confidence is low, or the customer asks for a person."""
    from app.db.supabase import log_escalation
    log_escalation(customer_message, conversation_history, reason)
    return "Your request has been escalated to our support team. A human agent will follow up with you shortly."
