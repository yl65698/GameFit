"""
Naver 쇼핑 검색 API로 장비 가격 데이터 수집

사용법:
  python manage.py fetch_naver              # 기존 장비 가격 업데이트
  python manage.py fetch_naver --add-new    # 인기 신규 장비도 추가
"""

import html
import time
import requests
from django.core.management.base import BaseCommand

from hardware.models import Hardware, HardwarePriceHistory

NAVER_ID = '6ugifIEvi8wHgDm_8Ny8'
NAVER_SECRET = 'oZ3eVQUnT_'
NAVER_URL = 'https://openapi.naver.com/v1/search/shop.json'

# 카테고리별 검색어 접미사 + 최저가 기준 (원)
CATEGORY_META = {
    'cpu':     {'suffix': 'CPU 프로세서',   'min_price': 50_000},
    'gpu':     {'suffix': '그래픽카드',      'min_price': 150_000},
    'ram':     {'suffix': 'RAM 메모리',     'min_price': 15_000},
    'storage': {'suffix': 'SSD',           'min_price': 15_000},
    'vr':      {'suffix': 'VR 헤드셋',      'min_price': 150_000},
    'console': {'suffix': '게임기',         'min_price': 100_000},
    'other':   {'suffix': '',              'min_price': 5_000},
}

# 신규 수집 대상 (--add-new)
NEW_HARDWARE = [
    ('AMD Ryzen 7 7700X',             'cpu',     'AMD'),
    ('Intel Core i7-13700K',          'cpu',     'Intel'),
    ('Intel Core i5-13600K',          'cpu',     'Intel'),
    ('NVIDIA RTX 4070 Ti SUPER',      'gpu',     'NVIDIA'),
    ('NVIDIA RTX 4060 Ti',            'gpu',     'NVIDIA'),
    ('AMD RX 7900 XTX',              'gpu',     'AMD'),
    ('AMD RX 6700 XT',               'gpu',     'AMD'),
    ('Samsung DDR5 32GB PC5-44800',  'ram',     'Samsung'),
    ('Corsair Vengeance DDR4 16GB',  'ram',     'Corsair'),
    ('Samsung 990 Pro 1TB NVMe',     'storage', 'Samsung'),
    ('WD Black SN850X 1TB',          'storage', 'WD'),
    ('Sony PlayStation VR2',          'vr',      'Sony'),
]


def _clean(text: str) -> str:
    return html.unescape(text).replace('<b>', '').replace('</b>', '')


def _search(query: str, display: int = 5) -> list:
    try:
        r = requests.get(
            NAVER_URL,
            headers={
                'X-Naver-Client-Id': NAVER_ID,
                'X-Naver-Client-Secret': NAVER_SECRET,
            },
            params={'query': query, 'display': display, 'sort': 'sim'},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get('items', [])
    except Exception:
        return []


def _filter_items(items: list, category: str, keyword: str) -> list:
    """카테고리 최저가 + 제목 키워드 기반 필터링"""
    min_price = CATEGORY_META.get(category, CATEGORY_META['other'])['min_price']
    kw_lower = keyword.lower().split()[0]  # 첫 키워드만 체크

    valid = []
    for item in items:
        lprice = int(item.get('lprice', 0) or 0)
        if lprice < min_price:
            continue
        title = _clean(item.get('title', '')).lower()
        if kw_lower not in title:
            continue
        valid.append(item)
    return valid


class Command(BaseCommand):
    help = 'Naver 쇼핑 API로 장비 가격이력 수집 및 현재 가격 업데이트'

    def add_arguments(self, parser):
        parser.add_argument('--add-new', action='store_true',
                            help='인기 장비 신규 추가')
        parser.add_argument('--display', type=int, default=5,
                            help='검색당 최대 결과 수 (기본 5)')
        parser.add_argument('--reset', action='store_true',
                            help='기존 가격이력 삭제 후 재수집')

    def handle(self, *args, **options):
        self.display = options['display']

        if options['reset']:
            cnt, _ = HardwarePriceHistory.objects.all().delete()
            self.stdout.write(f'기존 가격이력 {cnt}건 삭제 완료')

        self.stdout.write(self.style.SUCCESS('=== Naver 쇼핑 데이터 수집 시작 ==='))
        self._update_existing()

        if options['add_new']:
            self._add_new_hardware()

        self.stdout.write(self.style.SUCCESS('\n=== 완료 ==='))
        self.stdout.write(f'  장비        : {Hardware.objects.count()}개')
        self.stdout.write(f'  가격 이력   : {HardwarePriceHistory.objects.count()}건')

    # ── 기존 장비 가격 이력 수집 ──────────────────────────────────

    def _update_existing(self):
        hardwares = list(Hardware.objects.all())
        self.stdout.write(f'\n기존 장비 {len(hardwares)}개 가격 수집 중...')

        for hw in hardwares:
            meta = CATEGORY_META.get(hw.category, CATEGORY_META['other'])
            query = f'{hw.name} {meta["suffix"]}'.strip()

            items = _search(query, self.display)
            valid = _filter_items(items, hw.category, hw.name)

            if not valid:
                self.stdout.write(f'  [skip] {hw.name[:40]}: 유효 결과 없음')
                time.sleep(0.2)
                continue

            best_price = None
            created_count = 0

            for item in valid:
                lprice = int(item.get('lprice', 0))
                mall = _clean(item.get('mallName', ''))

                HardwarePriceHistory.objects.create(
                    hardware=hw,
                    shop_name=mall,
                    price=lprice,
                    original_price=hw.original_price,
                    discount_percent=hw.discount_percent,
                )
                created_count += 1

                if best_price is None or lprice < best_price:
                    best_price = lprice

            # 최저가로 Hardware 가격 갱신
            if best_price:
                orig = int(hw.original_price) or best_price
                disc = max(0, round((1 - best_price / orig) * 100)) if orig > 0 else 0
                hw.price = best_price
                hw.discount_percent = disc
                hw.save(update_fields=['price', 'discount_percent'])
                self.stdout.write(
                    f'  [OK] {hw.name[:38]}: {best_price:,}원 (이력 +{created_count}건)'
                )

            time.sleep(0.25)

    # ── 신규 장비 추가 ────────────────────────────────────────────

    def _add_new_hardware(self):
        self.stdout.write('\n신규 장비 추가 중...')
        added = 0

        for name, category, manufacturer in NEW_HARDWARE:
            # 이미 비슷한 이름 존재하면 스킵
            keyword = name.split()[0]
            if Hardware.objects.filter(name__icontains=keyword).exists():
                continue

            meta = CATEGORY_META.get(category, CATEGORY_META['other'])
            query = f'{name} {meta["suffix"]}'.strip()
            items = _search(query, 5)
            valid = _filter_items(items, category, name)

            if not valid:
                time.sleep(0.25)
                continue

            best = min(valid, key=lambda x: int(x.get('lprice', 999_999_999)))
            lprice = int(best.get('lprice', 0))
            if not lprice:
                time.sleep(0.25)
                continue

            title = _clean(best.get('title', name))[:200]
            image_url = best.get('image', '')

            hw = Hardware.objects.create(
                name=title,
                category=category,
                manufacturer=manufacturer,
                price=lprice,
                original_price=lprice,
                discount_percent=0,
                image_url=image_url,
            )

            for item in valid:
                p = int(item.get('lprice', 0) or 0)
                mall = _clean(item.get('mallName', ''))
                if p and mall:
                    HardwarePriceHistory.objects.create(
                        hardware=hw,
                        shop_name=mall,
                        price=p,
                        original_price=p,
                        discount_percent=0,
                    )

            added += 1
            self.stdout.write(f'  + {title[:45]} {lprice:,}원')
            time.sleep(0.25)

        self.stdout.write(f'  -> 신규 장비 {added}개 추가 완료')
