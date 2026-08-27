import httpx
from typing import Optional
from app.config import settings
from app.commerce.base import CommerceProvider, Order, Product, Variant


class ShopifyAdapter(CommerceProvider):
    """Reference adapter: Shopify Admin REST API (2024-10)."""

    platform_name = "shopify"

    def __init__(self):
        self.base = f"https://{settings.shopify_store_domain}/admin/api/2024-10"
        self.headers = {
            "X-Shopify-Access-Token": settings.shopify_api_key,
            "Content-Type": "application/json",
        }

    async def _get_json(self, path: str, params: dict = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base}{path}", headers=self.headers, params=params or {}, timeout=15)
            resp.raise_for_status()
            return resp.json()

    def _parse_order(self, o: dict) -> Order:
        fulfillments = o.get("fulfillments", [])
        tracking = fulfillments[0] if fulfillments else {}
        return Order(
            id=o["id"], order_number=o["order_number"],
            customer_name=f"{o.get('customer', {}).get('first_name', '')} {o.get('customer', {}).get('last_name', '')}",
            customer_email=o.get("email", ""),
            total_price=o["total_price"], currency=o["currency"],
            financial_status=o.get("financial_status", ""),
            fulfillment_status=o.get("fulfillment_status", ""),
            created_at=o["created_at"],
            tracking_company=tracking.get("tracking_company", ""),
            tracking_number=tracking.get("tracking_numbers", [""])[0] if tracking.get("tracking_numbers") else "",
            tracking_url=tracking.get("tracking_url", ""),
            line_items=[
                {
                    "title": li.get("title", ""),
                    "quantity": li.get("quantity", 0),
                    "price": li.get("price", "0"),
                    "sku": (li.get("variant", {}) or {}).get("sku", ""),
                }
                for li in o.get("line_items", [])
            ],
        )

    def _parse_product(self, p: dict) -> Product:
        return Product(
            id=p["id"], title=p["title"], body_html=p.get("body_html", ""),
            vendor=p.get("vendor", ""),
            variants=[Variant(**{
                "id": v["id"], "title": v["title"], "price": v["price"],
                "inventory_quantity": v["inventory_quantity"], "sku": v.get("sku", ""),
            }) for v in p.get("variants", [])],
        )

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        data = await self._get_json("/orders.json", {"name": order_number, "status": "any", "limit": 1})
        orders = data.get("orders", [])
        return self._parse_order(orders[0]) if orders else None

    async def get_order_by_email(self, email: str) -> Optional[Order]:
        data = await self._get_json("/orders.json", {"email": email, "status": "any", "limit": 1})
        orders = data.get("orders", [])
        return self._parse_order(orders[0]) if orders else None

    async def search_products(self, query: str) -> list[Product]:
        data = await self._get_json("/products.json", {"title": query, "limit": 10})
        return [self._parse_product(p) for p in data.get("products", [])]

    async def get_fulfillments(self, order_id: int) -> list[dict]:
        data = await self._get_json(f"/orders/{order_id}/fulfillments.json")
        return [
            {"status": f.get("status", ""), "tracking_company": f.get("tracking_company", ""),
             "tracking_number": (f.get("tracking_numbers") or [""])[0],
             "tracking_url": f.get("tracking_url", "")}
            for f in data.get("fulfillments", [])
        ]

    async def get_all_products(self) -> list[Product]:
        data = await self._get_json("/products.json", {"limit": 250})
        return [self._parse_product(p) for p in data.get("products", [])]

    async def get_all_orders(self) -> list[Order]:
        data = await self._get_json("/orders.json", {"status": "any", "limit": 50})
        return [self._parse_order(o) for o in data.get("orders", [])]

    async def get_order(self, order_id: int) -> Optional[Order]:
        try:
            data = await self._get_json(f"/orders/{order_id}.json")
            return self._parse_order(data.get("order", {}))
        except Exception:
            return None

    async def check_inventory(self) -> list[dict]:
        products = await self.get_all_products()
        low = []
        for p in products:
            for v in p.variants:
                if v.inventory_quantity <= settings.inventory_threshold:
                    low.append({"product": p.title, "variant": v.title, "stock": v.inventory_quantity, "sku": v.sku})
        return low
