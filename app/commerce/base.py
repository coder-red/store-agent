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

    @abstractmethod
    async def check_inventory(self) -> list[dict]:
        """Variants at or below the low-stock threshold. Each dict has keys:
        product, variant, stock, sku."""
