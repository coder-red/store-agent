"""Generates stock-style product placeholder images (SVG tiles) for the
Northlane mock store, and injects the matching image path into demo_data.py."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "app" / "static" / "images"
DEMO = ROOT / "app" / "commerce" / "demo_data.py"

# product_id -> (slug, [gradient colors], inline white icon svg)
# The tile is 400x300, icon centered around 200,150.
SPECS = {
    1001: ("backpack", ["#8E9AAF", "#5E6B8C"], '<rect x="150" y="70" width="100" height="150" rx="14" fill="none" stroke="#fff" stroke-width="9"/><path d="M150 150 h100" stroke="#fff" stroke-width="9" stroke-linecap="round"/><path d="M178 70 v-14 a22 22 0 0 1 44 0 v14" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>'),
    1002: ("headphones", ["#3B82F6", "#1E3A8A"], '<path d="M150 150 v-20 a50 50 0 0 1 100 0 v20" fill="none" stroke="#fff" stroke-width="9"/><rect x="140" y="150" width="26" height="55" rx="10" fill="#fff"/><rect x="234" y="150" width="26" height="55" rx="10" fill="#fff"/>'),
    1003: ("hoodie", ["#10B981", "#065F46"], '<path d="M130 105 l30 -25 h80 l30 25 v110 a12 12 0 0 1 -12 12 h-116 a12 12 0 0 1 -12 -12 z" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/><path d="M160 80 v25 a40 40 0 0 0 80 0 v-25" fill="none" stroke="#fff" stroke-width="9"/>'),
    1004: ("desk-lamp", ["#F59E0B", "#92400E"], '<path d="M155 70 h90 l-40 55 a50 50 0 0 1 -50 0 z" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/><rect x="178" y="130" width="44" height="90" rx="6" fill="#fff"/><rect x="155" y="220" width="90" height="14" rx="7" fill="#fff"/>'),
    1005: ("coffee-set", ["#A78BFA", "#5B21B6"], '<path d="M140 180 c0 -40 40 -60 60 -60 c20 0 60 20 60 60 v50 a10 10 0 0 1 -10 10 h-100 a10 10 0 0 1 -10 -10 z" fill="none" stroke="#fff" stroke-width="9"/><path d="M190 95 a30 22 0 0 1 0 -55" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/>'),
    1006: ("yoga-mat", ["#818CF8", "#4338CA"], '<path d="M120 210 c0 -70 50 -110 80 -110 s80 40 80 110" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round"/><path d="M160 210 c0 -60 20 -90 40 -90" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" opacity="0.5"/>'),
    1007: ("water-bottle", ["#06B6D4", "#0E7490"], '<rect x="165" y="55" width="70" height="190" rx="22" fill="none" stroke="#fff" stroke-width="9"/><rect x="178" y="40" width="44" height="28" rx="10" fill="#fff"/><circle cx="200" cy="130" r="13" fill="#fff" opacity="0.55"/>'),
    1008: ("sweater", ["#64748B", "#334155"], '<path d="M135 80 h55 v45 q10 15 10 15 q0 -15 10 -15 v-45 h55 l22 55 -40 18 v72 a8 8 0 0 1 -8 8 h-98 a8 8 0 0 1 -8 -8 v-72 l-40 -18 z" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/>'),
    1009: ("speaker", ["#F43F5E", "#9F1239"], '<rect x="158" y="75" width="84" height="150" rx="22" fill="none" stroke="#fff" stroke-width="9"/><circle cx="200" cy="150" r="30" fill="none" stroke="#fff" stroke-width="9"/><circle cx="200" cy="150" r="8" fill="#fff"/>'),
    1010: ("cutting-board", ["#D97706", "#92400E"], '<rect x="150" y="65" width="100" height="170" rx="16" fill="none" stroke="#fff" stroke-width="9"/><circle cx="200" cy="150" r="34" fill="none" stroke="#fff" stroke-width="9"/>'),
    1011: ("running-shoes", ["#22C55E", "#15803D"], '<path d="M120 150 h100 a45 45 0 0 1 45 33 l16 17 a8 8 0 0 1 -6 13 h-160 a8 8 0 0 1 -8 -8 v-40 a8 8 0 0 1 13 -15 z" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/><path d="M150 150 v1520" stroke="#fff" stroke-width="0"/>'),
    1012: ("french-press", ["#94A3B8", "#475569"], '<path d="M170 85 h60 l18 20 v90 a18 18 0 0 1 -18 18 h-60 a18 18 0 0 1 -18 -18 v-90 z" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/><rect x="182" y="55" width="36" height="30" rx="6" fill="#fff"/><path d="M200 85 v18" stroke="#fff" stroke-width="9"/>'),
    1013: ("candles", ["#FBBF24", "#B45309"], '<rect x="150" y="90" width="34" height="110" rx="10" fill="#fff"/><rect x="214" y="110" width="34" height="90" rx="10" fill="#fff" opacity="0.85"/><path d="M167 80 l4 -12 4 12" fill="#fff"/><path d="M231 100 l4 -12 4 12" fill="#fff" opacity="0.85"/>'),
    1014: ("wallet", ["#B08968", "#7C5C43"], '<rect x="145" y="105" width="110" height="75" rx="12" fill="none" stroke="#fff" stroke-width="9"/><path d="M175 105 v45 a12 12 0 0 0 12 12 h58 v-8 a12 12 0 0 1 12 -12 v-25 a12 12 0 0 0 -12 -12 z" fill="#fff"/><circle cx="245" cy="138" r="6" fill="#ffdca8"/>'),
    1015: ("lunch-box", ["#38BDF8", "#0369A1"], '<rect x="150" y="95" width="100" height="110" rx="12" fill="none" stroke="#fff" stroke-width="9"/><path d="M150 125 v-18 a8 8 0 0 1 8 -8 h84 a8 8 0 0 1 8 8 v18" fill="none" stroke="#fff" stroke-width="9"/><path d="M176 130 v32 a18 18 0 0 0 36 0 v-32" fill="none" stroke="#fff" stroke-width="9"/>'),
    1016: ("sanitizer", ["#34D399", "#047857"], '<rect x="158" y="60" width="84" height="170" rx="20" fill="none" stroke="#fff" stroke-width="9"/><rect x="172" y="84" width="56" height="92" rx="12" fill="#fff" opacity="0.5"/><path d="M170 204 a30 20 0 0 0 60 0" fill="none" stroke="#fff" stroke-width="9"/>'),
    1017: ("beanie", ["#A16207", "#713F12"], '<path d="M140 150 a60 60 0 0 1 120 0 l-14 60 a10 10 0 0 1 -10 9 h-72 a10 10 0 0 1 -10 -9 z" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/><circle cx="200" cy="118" r="10" fill="#fff"/>'),
    1018: ("dumbbell", ["#F97316", "#7C2D12"], '<path d="M120 130 h160 v40 h-160 z" fill="#fff"/><rect x="98" y="112" width="26" height="76" rx="8" fill="#fff"/><rect x="276" y="112" width="26" height="76" rx="8" fill="#fff"/>'),
    1019: ("linen-shirt", ["#7DD3FC", "#0C4A6E"], '<path d="M125 100 l22 -22 h30 v30 q15 18 23 18 q8 0 23 -18 v-30 h30 l22 22 -20 55 -38 8 v77 h-34 v-77 l-38 -8 z" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/>'),
    1020: ("wooden-watch", ["#CA8A04", "#713F12"], '<circle cx="200" cy="150" r="60" fill="none" stroke="#fff" stroke-width="9"/><path d="M200 150 v-34 m0 34 l18 18" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/><path d="M150 150 h-30 m110 0 h30" stroke="#fff" stroke-width="9"/>'),
    1021: ("dutch-oven", ["#EF4444", "#7F1D1D"], '<path d="M145 135 h110 a20 20 0 0 1 20 20 v45 a20 20 0 0 1 -20 20 h-110 a20 20 0 0 1 -20 -20 v-45 a20 20 0 0 1 20 -20 z" fill="none" stroke="#fff" stroke-width="9"/><path d="M160 135 v-22 a40 40 0 0 1 80 0 v22" fill="none" stroke="#fff" stroke-width="9"/><path d="M150 155 h100" stroke="#fff" stroke-width="9" opacity="0.4"/>'),
    1022: ("pillowcase", ["#EC4899", "#831843"], '<rect x="140" y="110" width="120" height="80" rx="14" fill="none" stroke="#fff" stroke-width="9"/><path d="M150 120 l110 60 m0 -60 l-110 60" stroke="#fff" stroke-width="6" opacity="0.5"/>'),
}

SIZE = (400, 300)

# Real stock-photo source (Unsplash) for each mock product, so the demo store
# shows genuine photography by default. If a URL ever fails to load, the
# storefront swaps to the local SVG tile via `image_fallback`.
IMG_PHOTO = {
    1001: "1601987078664-863b07dc0907",
    1002: "1614860243518-c12eb2fdf66c",
    1003: "1604074273911-6030c1fee7f6",
    1004: "1682827923239-9517e6d445a5",
    1005: "1590140103794-ce43de8e44c8",
    1006: "1767605523281-8b54b3692078",
    1007: "1725730929864-31959a4f1e50",
    1008: "1758398332796-514bcc9a1029",
    1009: "1692351014024-97edd83a7b5a",
    1010: "1676282827704-db50057ad7f5",
    1011: "1637437757614-6491c8e915b5",
    1012: "1641266886437-28abcc2b3288",
    1013: "1773739685635-76be879b058f",
    1014: "1741417657684-1fa606afd701",
    1015: "1658863173663-607c0feef366",
    1016: "1584744982491-665216d95f8b",
    1017: "1544967919-44c1ef2f9e7a",
    1018: "1770493895453-4f758c40d11d",
    1019: "1753369232904-a8a888319d28",
    1020: "1622823251669-9da2507aa52d",
    1021: "1770672438590-413eae05e595",
    1022: "1621960144410-36da870e29b6",
}


def img_url(pid):
    return f"https://images.unsplash.com/photo-{IMG_PHOTO[pid]}?w=700&q=70&auto=format&fit=crop"


def build_svg(slug, colors, icon):
    c1, c2 = colors
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE[0]}" height="{SIZE[1]}" viewBox="0 0 {SIZE[0]} {SIZE[1]}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.35" r="0.75">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{SIZE[0]}" height="{SIZE[1]}" fill="url(#bg)"/>
  <rect width="{SIZE[0]}" height="{SIZE[1]}" fill="url(#glow)"/>
  <g stroke-linecap="round" stroke-linejoin="round">
    {icon}
  </g>
</svg>
'''


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for pid, (slug, colors, icon) in SPECS.items():
        path = IMG_DIR / f"{slug}.svg"
        path.write_text(build_svg(slug, colors, icon), encoding="utf-8")
        written.append(slug)

    # Inject image fields into each mock product dict in demo_data.py.
    # `image` is the real stock-photo URL (Unsplash), `image_fallback` is the
    # local SVG tile the storefront swaps to if the remote image fails to load.
    # Keys stay ordered: id, title, body_html, vendor, image, image_fallback, variants.
    text = DEMO.read_text(encoding="utf-8")
    for pid, (slug, colors, icon) in SPECS.items():
        marker = f'"id": {pid}, '
        idx = text.find(marker)
        assert idx != -1, f"product {pid} not found"
        variants_at = text.find('"variants"', idx)
        assert variants_at != -1, f"variants missing for product {pid}"
        seg = text[idx:variants_at]

        new_seg = re.sub(
            r'"image":\s*"[^"]*"',
            f'"image": "{img_url(pid)}"',
            seg,
        )
        new_seg = re.sub(
            r'"image_fallback":\s*"[^"]*"',
            f'"image_fallback": "/images/{slug}.svg"',
            new_seg,
        )
        if '"image_fallback"' not in new_seg:
            new_seg = re.sub(
                r'("image":\s*"[^"]*")',
                rf'\1, "image_fallback": "/images/{slug}.svg"',
                new_seg,
                count=1,
            )

        text = text[:idx] + new_seg + text[variants_at:]

    DEMO.write_text(text, encoding="utf-8")
    print(f"Wrote {len(written)} SVGs to {IMG_DIR}")
    print("demo_data.py updated")


if __name__ == "__main__":
    main()
