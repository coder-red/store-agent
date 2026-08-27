from typing import Optional
from app.commerce.base import CommerceProvider, Order, Product, Variant
from app.commerce.demo_data import mock_products, mock_orders, mock_abandoned_carts


class MockStoreAdapter(CommerceProvider):
    """In-memory demo store. Runs the whole agent with no platform connected."""

    platform_name = "mock"

    #: Abandoned carts for the recovery feature. Adapters with real carts
    #: expose this the same way so analytics reads one source of truth.
    abandoned_carts = mock_abandoned_carts

    def _order_from_dict(self, o: dict) -> Order:
        line_items = o.get("line_items")
        if not line_items:
            line_items = [{
                "title": "Store order",
                "quantity": 1,
                "price": o["total_price"],
                "sku": "",
            }]
        return Order(
            id=o["id"], order_number=o["order_number"],
            customer_name=o["customer_name"], customer_email=o["customer_email"],
            total_price=o["total_price"], currency=o["currency"],
            financial_status=o["financial_status"], fulfillment_status=o["fulfillment_status"],
            created_at=o["created_at"], tracking_company=o["tracking_company"],
            tracking_number=o["tracking_number"], tracking_url=o["tracking_url"],
            line_items=line_items,
        )

    def _product_from_dict(self, p: dict) -> Product:
        return Product(
            id=p["id"], title=p["title"], body_html=p["body_html"],
            vendor=p["vendor"], image=p.get("image", ""),
            variants=[Variant(**v) for v in p["variants"]],
        )

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        for o in mock_orders:
            if str(o["order_number"]) == order_number or str(o["id"]) == order_number:
                return self._order_from_dict(o)
        return None

    async def get_order_by_email(self, email: str) -> Optional[Order]:
        for o in mock_orders:
            if o["customer_email"].lower() == email.lower():
                return self._order_from_dict(o)
        return None

    async def search_products(self, query: str) -> list[Product]:
        q = query.lower()
        results = []
        for p in mock_products:
            if q in p["title"].lower() or q in p["body_html"].lower() or q in p["vendor"].lower():
                results.append(self._product_from_dict(p))
        return results

    async def get_fulfillments(self, order_id: int) -> list[dict]:
        for o in mock_orders:
            if o["id"] == order_id:
                if o["tracking_number"]:
                    return [{
                        "status": o["fulfillment_status"],
                        "tracking_company": o["tracking_company"],
                        "tracking_number": o["tracking_number"],
                        "tracking_url": o["tracking_url"],
                    }]
                return [{"status": o["fulfillment_status"], "tracking_company": "", "tracking_number": "", "tracking_url": ""}]
        return []

    async def get_all_products(self) -> list[Product]:
        return [self._product_from_dict(p) for p in mock_products]

    async def get_all_orders(self) -> list[Order]:
        return [self._order_from_dict(o) for o in mock_orders]

    async def check_inventory(self) -> list[dict]:
        low_stock = []
        for p in mock_products:
            for v in p["variants"]:
                qty = v["inventory_quantity"]
                if qty <= 3:
                    low_stock.append({
                        "product": p["title"],
                        "variant": v["title"],
                        "stock": qty,
                        "sku": v["sku"],
                    })
        return low_stock
