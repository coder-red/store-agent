from app.commerce.service import get_store_provider
from app.channels.manager import channel_manager
from app.config import settings


async def check_inventory_and_alert():
    provider = get_store_provider()
    low_stock_items = await provider.check_inventory()
    if not low_stock_items:
        return
    lines = ["⚠️ Low Stock Alert", ""]
    for item in low_stock_items:
        lines.append(f"• {item['product']} ({item['variant']}) — {item['stock']} left")
        lines.append(f"  SKU: {item.get('sku', 'N/A')}")
    alert_text = "\n".join(lines)
    await channel_manager.send_to_owner(alert_text)
    print(f"Inventory alert sent: {len(low_stock_items)} items low")
