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
