import importlib
from app.config import settings
from app.commerce.base import CommerceProvider
from app.commerce.mock_adapter import MockStoreAdapter
from app.commerce.shopify_adapter import ShopifyAdapter

_provider: CommerceProvider = None


def _load_provider(name: str) -> CommerceProvider:
    if name == "mock":
        return MockStoreAdapter()
    if name == "shopify":
        return ShopifyAdapter()
    if ":" in name:
        # external plugin: PLATFORM=your.module:YourAdapterClass
        module_path, class_name = name.split(":", 1)
        cls = getattr(importlib.import_module(module_path), class_name)
        adapter = cls()
        if not isinstance(adapter, CommerceProvider):
            raise TypeError(f"{name} does not implement CommerceProvider")
        return adapter
    raise ValueError(
        f"Unknown PLATFORM '{name}'. Use 'mock', 'shopify', or 'module.path:ClassName'."
    )


def get_store_provider() -> CommerceProvider:
    global _provider
    if _provider is not None:
        return _provider
    _provider = _load_provider(settings.resolved_platform)
    return _provider


def reset_provider():
    global _provider
    _provider = None
