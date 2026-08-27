"""Commerce provider contract.

This is the plug that lets ANY storefront platform connect to the agent.
The agent core never talks to a platform API directly -- it only calls the
seven methods below. To support a new platform (WooCommerce, Medusa,
BigCommerce, a custom backend...), subclass CommerceProvider, map each
method onto that platform's API, and point PLATFORM at your adapter:

    PLATFORM=shopify                      # built-in reference adapter
    PLATFORM=mock                         # built-in demo adapter
    PLATFORM=my_pkg.adapters:WooAdapter   # any importable class

Data shapes are deliberately flat and platform-neutral: every adapter
normalises its platform's payloads into the Order/Product/Variant
dataclasses below. Tools, agents and the dashboard only ever see these.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    id: int
    order_number: int
    customer_name: str
    customer_email: str
    total_price: str
    currency: str
    financial_status: str          # e.g. paid, pending, refunded
    fulfillment_status: str        # e.g. fulfilled, partial, unfulfilled
    created_at: str                # ISO 8601 timestamp
    tracking_company: str
    tracking_number: str
    tracking_url: str
    line_items: list = None        # optional list of {title, quantity, price, sku}


@dataclass
class Variant:
    id: int
    title: str
    price: str                     # string decimal, e.g. "89.00"
    inventory_quantity: int
    sku: str


@dataclass
class Product:
    id: int
    title: str
    body_html: str
    vendor: str
    variants: list[Variant]
    image: str = ""                # URL or path to the product's primary image


class CommerceProvider(ABC):
    """Interface every storefront platform adapter must implement."""

    #: short identifier, e.g. "shopify", "woocommerce", "mock"
    platform_name: str = "abstract"

    @abstractmethod
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Look up one order by its human-facing number (e.g. '1006' or '#1006')."""

    @abstractmethod
    async def get_order_by_email(self, email: str) -> Optional[Order]:
        """Return the most recent order placed by this customer email."""

    @abstractmethod
    async def search_products(self, query: str) -> list[Product]:
        """Search products by title/description/vendor. Return top matches."""

    @abstractmethod
    async def get_fulfillments(self, order_id: int) -> list[dict]:
        """Fulfilment records for an order. Each dict has keys:
        status, tracking_company, tracking_number, tracking_url."""

    @abstractmethod
    async def get_all_products(self) -> list[Product]:
        """Every product in the catalogue (used by dashboards and alerts)."""

    @abstractmethod
    async def get_all_orders(self) -> list[Order]:
        """Recent orders, newest first (used by cart recovery and analytics)."""

    async def get_order(self, order_id: int) -> Optional[Order]:
        """Fetch one order by its internal id. Default scans get_all_orders;
        real adapters should override with a direct lookup."""
        for o in await self.get_all_orders():
            if o.id == order_id:
                return o
        return None

    @abstractmethod
    async def check_inventory(self) -> list[dict]:
        """Variants at or below the low-stock threshold. Each dict has keys:
        product, variant, stock, sku."""

    # --- Cart recovery (optional; base provides a no-op / in-memory default) ---

    #: Abandoned carts as a list of dicts. Real adapters that support cart
    #: recovery override this or the methods below. Each cart dict has keys:
    #: id, customer_name, customer_email, items, total, abandoned_at,
    #: recovery_status, recovery_attempts.
    abandoned_carts: list = None

    async def get_abandoned_carts(self) -> list:
        """Return abandoned carts for the recovery dashboard."""
        return list(getattr(self, "abandoned_carts", None) or [])

    async def mark_cart_recovered(self, cart_id: int, order_id: int = None) -> None:
        """Mark a cart as recovered (e.g. after a checkout completes)."""
        carts = getattr(self, "abandoned_carts", None)
        if carts is None:
            return
        from datetime import datetime, timezone
        for c in carts:
            if c["id"] == cart_id:
                c["recovery_status"] = "recovered"
                c["recovered_at"] = datetime.now(timezone.utc).isoformat()
                if order_id:
                    c["recovered_order_id"] = order_id
                break

    async def attempt_cart_recovery(self, cart_id: int, message: str) -> dict:
        """Record a recovery message sent for a cart. Returns the updated cart."""
        carts = getattr(self, "abandoned_carts", None)
        if carts is None:
            return {}
        from datetime import datetime, timezone
        for c in carts:
            if c["id"] == cart_id:
                c["recovery_attempts"] = c.get("recovery_attempts", 0) + 1
                c["last_recovery_at"] = datetime.now(timezone.utc).isoformat()
                c["recovery_status"] = "sent" if c["recovery_attempts"] < 3 else "pending"
                return c
        return {}
