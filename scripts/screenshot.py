from playwright.sync_api import sync_playwright
from pathlib import Path
import time

ASSETS = Path(__file__).parent.parent / "assets"
BASE = "https://store-agent-app.onrender.com"

pages = [
    ("dashboard", "/"),
    ("storefront", "/store.html"),
    ("conversations", "/conversations"),
    ("orders", "/orders"),
    ("settings", "/settings"),
    ("analytics", "/analytics"),
    ("cart-recovery", "/cart-recovery"),
    ("descriptions", "/product-descriptions"),
    ("email-inbox", "/email"),
    ("order-detail", "/orders/5001"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    for name, path in pages:
        url = BASE + path
        print(f"Capturing {name}... {url}")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            page.screenshot(path=str(ASSETS / f"{name}.png"), full_page=False)
            if name == "storefront":
                try:
                    page.click(".product-card")
                    time.sleep(1.5)
                    page.screenshot(path=str(ASSETS / "storefront-product.png"), full_page=False)
                    print("  saved storefront-product.png")
                except Exception as e:
                    print(f"  product modal FAILED: {e}")
            print(f"  saved {name}.png")
        except Exception as e:
            print(f"  FAILED: {e}")

    browser.close()
    print("Done")
