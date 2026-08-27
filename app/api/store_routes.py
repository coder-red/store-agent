from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.commerce.service import get_store_provider
from app.commerce.demo_data import mock_products, mock_orders
from app.agents.cart_recovery import CartRecoveryAgent

router = APIRouter()


class PlaceOrderRequest(BaseModel):
    customer_name: str
    customer_email: str
    product_id: int
    variant_id: int
    quantity: int = 1


_next_order_id = 5016
_next_variant_id = 2060
_next_cart_id = 9006


# --- Cart recovery ---

recovery_agent = CartRecoveryAgent()


@router.get("/store/carts/abandoned")
async def list_abandoned_carts():
    provider = get_store_provider()
    carts = await provider.get_abandoned_carts()
    return {"carts": sorted(carts, key=lambda c: c.get("abandoned_at", ""), reverse=True)}


@router.post("/store/carts/{cart_id}/recover")
async def attempt_recovery(cart_id: int):
    provider = get_store_provider()
    carts = await provider.get_abandoned_carts()
    cart = next((c for c in carts if c["id"] == cart_id), None)
    if not cart:
        raise HTTPException(404, "Cart not found")
    if cart["recovery_status"] == "recovered":
        return {"message": "Cart was already recovered."}
    msg = await recovery_agent.generate_recovery_message(cart)
    updated = await provider.attempt_cart_recovery(cart_id, msg)
    return {"recovery_message": msg, "cart": updated or cart}


@router.post("/store/carts/auto-recover")
async def auto_recover():
    provider = get_store_provider()
    carts = await provider.get_abandoned_carts()
    sent = []
    for cart in carts:
        if cart["recovery_status"] != "recovered":
            msg = await recovery_agent.generate_recovery_message(cart)
            await provider.attempt_cart_recovery(cart["id"], msg)
            sent.append({"cart_id": cart["id"], "customer": cart["customer_name"], "message": msg})
    return {"recovered": len(sent), "messages": sent}


@router.get("/store/carts/recovery-stats")
async def recovery_stats():
    provider = get_store_provider()
    carts = await provider.get_abandoned_carts()
    total = len(carts)
    recovered = sum(1 for c in carts if c["recovery_status"] == "recovered")
    sent = sum(1 for c in carts if c["recovery_status"] == "sent")
    pending = sum(1 for c in carts if c["recovery_status"] == "pending")
    total_revenue = sum(float(c["total"]) for c in carts if c["recovery_status"] == "recovered")
    return {
        "total_carts": total,
        "recovered": recovered,
        "sent": sent,
        "pending": pending,
        "recovery_rate": round(recovered / total * 100, 1) if total > 0 else 0,
        "recovered_revenue": f"${total_revenue:.2f}",
        "potential_revenue": f"${sum(float(c['total']) for c in carts):.2f}",
    }


@router.get("/store/products")
async def store_products():
    provider = get_store_provider()
    products = await provider.get_all_products()
    return {"products": [
        {
            "id": p.id,
            "title": p.title,
            "description": p.body_html,
            "vendor": p.vendor,
            "variants": [
                {"id": v.id, "title": v.title, "price": v.price, "stock": v.inventory_quantity, "sku": v.sku}
                for v in p.variants
            ],
        }
        for p in products
    ]}


@router.get("/store/track")
async def track_order(order_number: str = "", email: str = ""):
    """Customer-facing order lookup. Requires BOTH order number and the
    email used at checkout -- customers can only ever see their own order."""
    order_number = order_number.strip().lstrip("#")
    email = email.strip().lower()
    if not order_number or not email:
        raise HTTPException(400, "Order number and email are both required.")
    provider = get_store_provider()
    order = await provider.get_order_by_number(order_number)
    if not order or order.customer_email.strip().lower() != email:
        raise HTTPException(404, "We couldn't find an order matching those details.")
    return {
        "order_number": order.order_number,
        "status": order.financial_status,
        "fulfillment": order.fulfillment_status,
        "placed_at": order.created_at,
        "total": order.total_price,
        "currency": order.currency,
        "tracking": {
            "company": order.tracking_company,
            "number": order.tracking_number,
            "url": order.tracking_url,
        },
    }


@router.post("/store/orders")
async def place_order(req: PlaceOrderRequest):
    global _next_order_id, _next_variant_id

    product = None
    variant = None
    for p in mock_products:
        if p["id"] == req.product_id:
            product = p
            for v in p["variants"]:
                if v["id"] == req.variant_id:
                    variant = v
                    break
            break
    if not product or not variant:
        raise HTTPException(404, "Product or variant not found")
    if variant["inventory_quantity"] < req.quantity:
        raise HTTPException(400, "Not enough stock")

    price = float(variant["price"]) * req.quantity
    order_id = _next_order_id
    _next_order_id += 1
    order_number = order_id - 4000

    new_order = {
        "id": order_id,
        "order_number": order_number,
        "customer_name": req.customer_name,
        "customer_email": req.customer_email,
        "total_price": f"{price:.2f}",
        "currency": "USD",
        "financial_status": "paid",
        "fulfillment_status": "unfulfilled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tracking_company": "",
        "tracking_number": "",
        "tracking_url": "",
    }
    mock_orders.append(new_order)

    variant["inventory_quantity"] -= req.quantity

    return {"order": new_order, "message": f"Order #{order_number} placed successfully! You can ask the agent about it."}
