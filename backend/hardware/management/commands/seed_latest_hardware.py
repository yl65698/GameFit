import hashlib
import html
import math
import os
import re
import time
from decimal import Decimal
from pathlib import Path

import requests
from django.core.management.base import BaseCommand, CommandError

from hardware.models import Hardware, HardwarePriceHistory


NAVER_URL = "https://openapi.naver.com/v1/search/shop.json"

EXCLUDED_TITLE_WORDS = (
    "used",
    "refurb",
    "rental",
    "rent",
    "case for",
    "cover",
    "protector",
    "stand",
    "holder",
    "cable",
    "adapter",
    "battery",
    "remote",
    "accessory",
    "accessories",
    "controller",
    "joy-con",
    "dock",
    "cooling fan",
    "carrying case",
    "skin",
    "strap",
    "grip",
    "charging",
    "replacement",
    "protector",
    "game card",
    "game title",
    "racing wheel",
    "flight yoke",
    "throttle",
    "rudder",
    "sidestick",
    "disc drive",
    "disk drive",
    "케이스",
    "커버",
    "컨트롤러",
    "조이콘",
    "게임",
    "타이틀",
    "스트랩",
    "독",
    "도크",
    "어댑터",
    "충전",
    "보호",
    "파우치",
    "가방",
    "스탠드",
    "쿨러",
    "팬",
    "카드",
    "브래킷",
    "그립",
    "스킨",
    "실리콘",
    "쿠션",
    "렌즈",
    "부품",
    "마스크",
    "밴드",
    "액세서리",
    "요크",
    "러더",
    "쓰로틀",
    "레이싱휠",
    "레이싱 휠",
    "스티어링",
    "페달",
    "시프터",
    "조이스틱",
    "핸들",
    "디스크드라이브",
    "디스크 드라이브",
    "광디스크",
    "게이밍패드",
)

CATEGORY_SEARCHES = {
    "gpu": {
        "queries": [
            "RTX 5090 graphics card",
            "RTX 5080 graphics card",
            "RTX 5070 Ti graphics card",
            "RTX 5070 graphics card",
            "RTX 5060 Ti graphics card",
            "Radeon RX 9070 XT graphics card",
            "Radeon RX 7800 XT graphics card",
            "Radeon RX 7900 XTX graphics card",
        ],
        "min_price": 180_000,
        "score": 88,
    },
    "cpu": {
        "queries": [
            "Ryzen 9 9950X3D CPU",
            "Ryzen 9 9900X3D CPU",
            "Ryzen 7 9800X3D CPU",
            "Intel Core Ultra 9 285K CPU",
            "Intel Core Ultra 7 265K CPU",
            "Intel Core i9 14900K CPU",
            "Intel Core i7 14700K CPU",
            "Ryzen 7 9700X CPU",
        ],
        "min_price": 90_000,
        "score": 86,
    },
    "ram": {
        "queries": [
            "DDR5 64GB 6400 memory",
            "DDR5 32GB 6000 memory",
            "DDR5 32GB 5600 memory",
            "G.Skill DDR5 64GB memory",
            "Corsair DDR5 32GB memory",
            "Samsung DDR5 32GB memory",
        ],
        "min_price": 35_000,
        "score": 72,
    },
    "storage": {
        "queries": [
            "Samsung 9100 PRO NVMe SSD",
            "Samsung 990 PRO NVMe SSD",
            "WD BLACK SN8100 NVMe SSD",
            "WD BLACK SN850X NVMe SSD",
            "Crucial T705 NVMe SSD",
            "SK hynix Platinum P41 SSD",
        ],
        "min_price": 40_000,
        "score": 78,
    },
    "power": {
        "queries": [
            "ATX 3.1 1000W power supply",
            "ATX 3.0 850W power supply",
            "80PLUS Gold 850W power supply",
            "Corsair RM1000x power supply",
            "Seasonic Focus GX power supply",
            "FSP Hydro power supply",
        ],
        "min_price": 45_000,
        "score": 66,
    },
    "monitor": {
        "queries": [
            "OLED gaming monitor 27",
            "OLED gaming monitor 32",
            "QHD 180Hz gaming monitor",
            "4K 144Hz gaming monitor",
            "Samsung Odyssey monitor",
            "LG UltraGear monitor",
        ],
        "min_price": 80_000,
        "score": 74,
    },
    "mouse": {
        "queries": [
            "wireless gaming mouse",
            "Logitech G Pro X Superlight",
            "Razer Viper V3 Pro",
            "Pulsar gaming mouse",
            "Zowie wireless mouse",
        ],
        "min_price": 20_000,
        "score": 62,
    },
    "keyboard": {
        "queries": [
            "mechanical gaming keyboard",
            "wireless mechanical keyboard",
            "Razer Huntsman keyboard",
            "Logitech G Pro keyboard",
            "Keychron mechanical keyboard",
        ],
        "min_price": 25_000,
        "score": 64,
    },
    "headset": {
        "queries": [
            "wireless gaming headset",
            "SteelSeries Arctis headset",
            "Logitech G Pro X headset",
            "Razer BlackShark headset",
            "HyperX Cloud headset",
        ],
        "min_price": 25_000,
        "score": 62,
    },
    "motherboard": {
        "queries": [
            "X870E motherboard",
            "B850 motherboard",
            "Z890 motherboard",
            "B760 motherboard",
            "ASUS ROG motherboard",
            "MSI MAG motherboard",
        ],
        "min_price": 80_000,
        "score": 70,
    },
    "cooler": {
        "queries": [
            "360mm AIO liquid cooler",
            "240mm AIO liquid cooler",
            "Noctua CPU cooler",
            "DeepCool CPU cooler",
            "Thermalright CPU cooler",
        ],
        "min_price": 20_000,
        "score": 58,
    },
    "case": {
        "queries": [
            "ATX gaming PC case",
            "mesh airflow PC case",
            "Lian Li PC case",
            "Fractal Design PC case",
            "HYTE PC case",
        ],
        "min_price": 30_000,
        "score": 56,
    },
    "vr": {
        "queries": [
            "Meta Quest 3 512GB",
            "Meta Quest 3S 256GB",
            "PlayStation VR2",
            "PICO 4 Ultra",
            "HTC Vive XR Elite",
            "Valve Index full kit",
            "VIVE Pro 2 full kit",
            "VR headset main unit",
        ],
        "min_price": 180_000,
        "score": 68,
    },
    "console": {
        "queries": [
            "Nintendo Switch 2 본체",
            "PlayStation 5 Pro 본체",
            "PlayStation 5 Slim 본체",
            "Xbox Series X 본체",
            "Xbox Series S 본체",
            "Steam Deck OLED 본체",
            "ROG Ally X 본체",
            "Lenovo Legion Go 본체",
            "gaming console main unit",
        ],
        "min_price": 180_000,
        "score": 70,
    },
}

MANUFACTURERS = [
    "AMD",
    "Intel",
    "NVIDIA",
    "ASUS",
    "MSI",
    "Gigabyte",
    "ZOTAC",
    "Sapphire",
    "Samsung",
    "LG",
    "Western Digital",
    "WD",
    "Crucial",
    "SK hynix",
    "Corsair",
    "Seasonic",
    "FSP",
    "Logitech",
    "Razer",
    "SteelSeries",
    "HyperX",
    "Keychron",
    "Pulsar",
    "Zowie",
    "Noctua",
    "DeepCool",
    "Thermalright",
    "Lian Li",
    "Fractal",
    "HYTE",
]


def clean(text):
    return html.unescape(text or "").replace("<b>", "").replace("</b>", "").strip()


def compact_spaces(text):
    return re.sub(r"\s+", " ", text).strip()


def load_env_value(key):
    if os.environ.get(key):
        return os.environ[key]

    env_path = Path(__file__).resolve().parents[4] / ".env"
    if not env_path.exists():
        return ""

    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == key:
            return value.strip()
    return ""


class Command(BaseCommand):
    help = "Seed hardware rows and Naver shopping price history."

    def add_arguments(self, parser):
        parser.add_argument("--target", type=int, default=500)
        parser.add_argument("--display", type=int, default=100)
        parser.add_argument("--history-limit", type=int, default=1)
        parser.add_argument("--delay", type=float, default=0.05)
        parser.add_argument("--reset-generated", action="store_true")
        parser.add_argument("--balanced", action="store_true", default=True)

    def handle(self, *args, **options):
        client_id = load_env_value("NAVER_CLIENT_ID")
        client_secret = load_env_value("NAVER_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise CommandError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET are required.")

        target = options["target"]
        display = min(max(options["display"], 1), 100)
        history_limit = max(options["history_limit"], 1)
        delay = options["delay"]
        category_quota = math.ceil(target / len(CATEGORY_SEARCHES))

        if options["reset_generated"]:
            generated = Hardware.objects.filter(specs__contains="Source: Naver Shopping")
            deleted_count, _ = generated.delete()
            self.stdout.write(f"deleted generated rows: {deleted_count}")

        before_count = Hardware.objects.count()
        added = 0
        updated = 0
        skipped = 0
        histories = 0
        seen_keys = set(
            Hardware.objects.values_list("name", flat=True)
        )

        for category, category_meta in CATEGORY_SEARCHES.items():
            if Hardware.objects.count() >= target:
                break

            for query in category_meta["queries"]:
                if Hardware.objects.count() >= target:
                    break
                if options["balanced"] and Hardware.objects.filter(category=category).count() >= category_quota:
                    break

                items = self.search_naver(
                    query=query,
                    display=display,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                created_for_query = 0

                for item in items:
                    if Hardware.objects.count() >= target:
                        break
                    if options["balanced"] and Hardware.objects.filter(category=category).count() >= category_quota:
                        break

                    normalized = self.normalized_item(item, category, category_meta)
                    if not normalized:
                        skipped += 1
                        continue
                    if normalized["name"] in seen_keys:
                        skipped += 1
                        continue

                    hardware, created = Hardware.objects.update_or_create(
                        name=normalized["name"],
                        defaults={
                            "category": category,
                            "manufacturer": normalized["manufacturer"],
                            "price": normalized["price"],
                            "original_price": normalized["price"],
                            "discount_percent": 0,
                            "image_url": normalized["image_url"],
                            "specs": normalized["specs"],
                            "benchmark_score": normalized["benchmark_score"],
                        },
                    )
                    seen_keys.add(normalized["name"])

                    if created:
                        added += 1
                    else:
                        updated += 1

                    HardwarePriceHistory.objects.filter(hardware=hardware).delete()
                    for history_item in [item][:history_limit]:
                        HardwarePriceHistory.objects.create(
                            hardware=hardware,
                            shop_name=clean(history_item.get("mallName"))[:200],
                            price=normalized["price"],
                            original_price=normalized["price"],
                            discount_percent=0,
                        )
                        histories += 1

                    created_for_query += 1

                self.stdout.write(
                    f"{category:11} {query[:34]:34} +{created_for_query:3} total={Hardware.objects.count()}"
                )
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS("done"))
        self.stdout.write(f"hardware: {before_count} -> {Hardware.objects.count()}")
        self.stdout.write(f"added: {added}, updated: {updated}, skipped: {skipped}")
        self.stdout.write(f"price histories created: {histories}")

    def search_naver(self, query, display, client_id, client_secret):
        response = requests.get(
            NAVER_URL,
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            params={"query": query, "display": display, "sort": "sim"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("items", [])

    def normalized_item(self, item, category, category_meta):
        price = int(item.get("lprice") or 0)
        title = compact_spaces(clean(item.get("title")))
        lower_title = title.lower()

        if not title or price < category_meta["min_price"]:
            return None
        if any(word in lower_title for word in EXCLUDED_TITLE_WORDS):
            return None

        name = self.simplify_name(title)
        if len(name) < 8:
            return None

        manufacturer = self.infer_manufacturer(name)
        specs = self.build_specs(category, item)

        return {
            "name": name[:200],
            "manufacturer": manufacturer,
            "price": Decimal(price),
            "image_url": (item.get("image") or "")[:200],
            "specs": specs,
            "benchmark_score": self.score_for_item(category_meta["score"], name, price),
        }

    def simplify_name(self, title):
        name = re.sub(r"\[[^\]]+\]|\([^\)]*\)", " ", title)
        name = re.sub(r"\b(병행수입|정품|벌크|리퍼|중고|해외구매|해외직구)\b", " ", name)
        name = compact_spaces(name)
        if len(name) <= 200:
            return name
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:6]
        return f"{name[:193]} {digest}"

    def infer_manufacturer(self, name):
        lower_name = name.lower()
        for manufacturer in MANUFACTURERS:
            if manufacturer.lower() in lower_name:
                if manufacturer == "WD":
                    return "Western Digital"
                return manufacturer
        return ""

    def build_specs(self, category, item):
        product_id = item.get("productId") or ""
        mall = clean(item.get("mallName"))
        parts = [
            f"Category: {category}",
            "Source: Naver Shopping",
        ]
        if mall:
            parts.append(f"Mall: {mall}")
        if product_id:
            parts.append(f"Naver product ID: {product_id}")
        return " | ".join(parts)

    def score_for_item(self, base_score, name, price):
        score = base_score
        lower_name = name.lower()
        if any(token in lower_name for token in ("5090", "9950x3d", "oled", "9100 pro")):
            score += 8
        elif any(token in lower_name for token in ("5080", "9900x3d", "9070 xt", "4k")):
            score += 5
        elif any(token in lower_name for token in ("5070", "9800x3d", "ddr5", "qhd")):
            score += 3
        if price > 1_000_000:
            score += 3
        return min(score, 100)
