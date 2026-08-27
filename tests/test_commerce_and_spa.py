"""Tests for the commerce provider factory and backend SPA serving.

Run: python -m pytest tests/ -v
"""
import importlib.util
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.commerce.base import CommerceProvider
from app.commerce.mock_adapter import MockStoreAdapter
from app.commerce import service as commerce_service


@pytest.fixture(autouse=True)
def _fresh_provider():
    commerce_service.reset_provider()
    yield
    commerce_service.reset_provider()


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# --- CommerceProvider factory ---

def test_mock_platform_loads_mock_adapter():
    assert isinstance(commerce_service._load_provider("mock"), MockStoreAdapter)


def test_shopify_platform_loads_shopify_adapter():
    from app.commerce.shopify_adapter import ShopifyAdapter
    assert isinstance(commerce_service._load_provider("shopify"), ShopifyAdapter)


def test_unknown_platform_raises():
    with pytest.raises(ValueError, match="Unknown PLATFORM"):
        commerce_service._load_provider("nonsense")


def test_external_plugin_loads_by_module_path():
    adapter = commerce_service._load_provider("app.commerce.mock_adapter:MockStoreAdapter")
    assert isinstance(adapter, CommerceProvider)


def test_external_plugin_rejects_non_provider(tmp_path):
    module = tmp_path / "not_a_provider.py"
    module.write_text("class Fake:\n    pass\n")
    spec = importlib.util.spec_from_file_location("not_a_provider", module)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spec and mod)
    sys.modules["not_a_provider"] = mod
    try:
        with pytest.raises(TypeError, match="does not implement"):
            commerce_service._load_provider("not_a_provider:Fake")
    finally:
        del sys.modules["not_a_provider"]


def test_provider_is_singleton():
    assert commerce_service.get_store_provider() is commerce_service.get_store_provider()


@pytest.mark.asyncio
async def test_mock_adapter_finds_order():
    order = await MockStoreAdapter().get_order_by_number("1006")
    assert order is not None
    assert order.financial_status == "paid"


# --- Backend SPA serving ---

def test_root_serves_dashboard(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Store Agent" in r.text


def test_spa_fallback_for_client_routes(client):
    r = client.get("/conversations")
    assert r.status_code == 200
    assert "Store Agent" in r.text


def test_path_traversal_serves_index_not_secrets(client):
    r = client.get("/..%2F..%2F.env")
    assert r.status_code == 200
    assert "API_KEY" not in r.text


def test_api_still_json_not_shadowed(client):
    r = client.get("/api/settings")
    assert r.status_code == 200
    assert r.json()["store_name"]


def test_api_orders_includes_owner_fields(client):
    r = client.get("/api/orders")
    assert r.status_code == 200
    orders = r.json()["orders"]
    assert orders, "mock store should have orders"
    o = orders[0]
    for field in ("customer_email", "created_at", "currency", "tracking_number"):
        assert field in o


def test_api_order_detail_has_line_items(client):
    orders = client.get("/api/orders").json()["orders"]
    detail = client.get(f"/api/orders/{orders[0]['id']}")
    assert detail.status_code == 200
    d = detail.json()
    for field in ("customer_email", "customer_name", "total", "line_items", "tracking_url"):
        assert field in d
    assert d["line_items"], "order detail should include line items"
    li = d["line_items"][0]
    for field in ("title", "quantity", "price", "sku"):
        assert field in li

    missing = client.get("/api/orders/999999")
    assert missing.status_code == 404


def test_cart_reads_through_provider_contract(client):
    carts = client.get("/store/carts/abandoned").json()["carts"]
    assert carts
    stats = client.get("/store/carts/recovery-stats").json()
    assert "total_carts" in stats
    assert stats["total_carts"] == len(carts)


def test_whatsapp_webhook_returns_twill(client):
    r = client.post("/webhook/whatsapp", data={"From": "whatsapp:+1234", "Body": "hi"})
    assert r.status_code == 200
    assert "Response" in r.text


def test_telegram_webhook_ok(client):
    r = client.post("/webhook/telegram", json={"message": {"chat": {"id": "99"}, "text": "hello"}})
    assert r.status_code == 200
    assert r.json()["ok"] is True


# --- Customer order tracking (privacy: only your own order) ---

def _place_order(client, email="track.me@example.com"):
    from app.commerce.demo_data import mock_products
    p = mock_products[0]
    v = p["variants"][0]
    r = client.post("/store/orders", json={
        "customer_name": "Track Me", "customer_email": email,
        "product_id": p["id"], "variant_id": v["id"], "quantity": 1,
    })
    assert r.status_code == 200
    return r.json()["order"]["order_number"]


def test_track_returns_own_order(client):
    num = _place_order(client)
    r = client.get(f"/store/track?order_number={num}&email=track.me@example.com")
    assert r.status_code == 200
    body = r.json()
    assert body["order_number"] == num
    assert "customer_email" not in body
    assert "customer_name" not in body


def test_track_rejects_wrong_email(client):
    num = _place_order(client)
    r = client.get(f"/store/track?order_number={num}&email=thief@example.com")
    assert r.status_code == 404


def test_track_rejects_unknown_order(client):
    r = client.get("/store/track?order_number=999999&email=nobody@example.com")
    assert r.status_code == 404


def test_track_requires_both_fields(client):
    assert client.get("/store/track?order_number=1006").status_code == 400
    assert client.get("/store/track?email=a@b.com").status_code == 400


def test_all_orders_endpoint_is_gone(client):
    # the public all-orders listing leaked every customer's email; it must not exist.
    # (a removed path falls through to the SPA fallback, so expect HTML, never JSON)
    r = client.get("/store/orders")
    assert "application/json" not in r.headers.get("content-type", "")
    assert "orders" not in r.text[:200] or "<html" in r.text.lower()


def test_analytics_reports_real_order_revenue(client):
    r = client.get("/api/analytics")
    assert r.status_code == 200
    body = r.json()
    assert "orders" in body
    assert body["orders"]["total_orders"] > 0
    assert body["orders"]["total_revenue"].startswith("$")
