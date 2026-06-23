"""
ITAD(IsThereAnyDeal) API로 게임 가격·할인 데이터 수집

사용법:
  python manage.py fetch_itad               # 기존 게임 업데이트 + 신규 50개 수집
  python manage.py fetch_itad --new 100     # 신규 게임 100개까지 수집
  python manage.py fetch_itad --skip-new    # 기존 게임 업데이트만
  python manage.py fetch_itad --country US  # USD 기준 가격
"""

import time
import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError

from games.models import Game, GamePriceHistory

ITAD_KEY = '0141c91def3919fc9b7f469f5410376827846cc7'
BASE_URL = 'https://api.isthereanydeal.com'

PLATFORM_MAP = {
    'steam': 'steam',
    'epic': 'epic',
    'ubisoft': 'ubisoft',
    'gog': 'other',
}


def _platform(shop_name: str) -> str:
    lower = shop_name.lower()
    for key, val in PLATFORM_MAP.items():
        if key in lower:
            return val
    return 'other'


class Command(BaseCommand):
    help = 'ITAD API로 게임·가격이력·할인 데이터 수집'

    def add_arguments(self, parser):
        parser.add_argument('--country', default='KR', help='ISO 국가 코드 (기본 KR)')
        parser.add_argument('--new', type=int, default=50, dest='new_limit',
                            help='신규 게임 최대 수집 개수 (기본 50)')
        parser.add_argument('--skip-new', action='store_true',
                            help='신규 게임 수집 건너뜀')
        parser.add_argument('--add-titles', nargs='+', metavar='TITLE',
                            help='특정 타이틀을 ITAD에서 검색해 추가')

    def handle(self, *args, **options):
        self.country = options['country']
        self.stdout.write(self.style.SUCCESS('=== ITAD 데이터 수집 시작 ==='))
        self.stdout.write(f'  국가: {self.country}')

        if options.get('add_titles'):
            self._add_by_titles(options['add_titles'])
            return

        self._update_existing_games()

        if not options['skip_new']:
            self._fetch_new_deals(options['new_limit'])

        self.stdout.write(self.style.SUCCESS('\n✅ 완료'))
        self.stdout.write(f'  게임        : {Game.objects.count()}개')
        self.stdout.write(f'  가격 이력   : {GamePriceHistory.objects.count()}건')
        disc_cnt = GamePriceHistory.objects.filter(discount_percent__gt=0).count()
        self.stdout.write(f'  할인 이력   : {disc_cnt}건 (discount_percent > 0)')

    # ── HTTP ─────────────────────────────────────────────────────

    def _get(self, path, **params):
        params['key'] = ITAD_KEY
        r = requests.get(f'{BASE_URL}{path}', params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def _post(self, path, body, **params):
        params['key'] = ITAD_KEY
        r = requests.post(f'{BASE_URL}{path}', json=body, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    # ── ITAD UUID 검색 ────────────────────────────────────────────

    def _search(self, title: str):
        try:
            results = self._get('/games/search/v1', title=title, results=5)
            if not results:
                return None
            # 정확히 일치하는 제목 우선
            for item in results:
                if item.get('title', '').lower() == title.lower():
                    return item['id']
            return results[0]['id']
        except Exception as e:
            self.stdout.write(f'    검색 오류 ({title}): {e}')
            return None

    # ── 기존 게임 업데이트 ─────────────────────────────────────────

    def _update_existing_games(self):
        games = list(Game.objects.all())
        self.stdout.write(f'\n[1/2] 기존 게임 {len(games)}개 처리 중...')

        # UUID 매핑
        uuid_map: dict[int, str] = {}
        for game in games:
            if game.itad_id:
                uuid_map[game.pk] = game.itad_id
                continue
            uid = self._search(game.title)
            if uid:
                game.itad_id = uid
                game.save(update_fields=['itad_id'])
                uuid_map[game.pk] = uid
                self.stdout.write(f'  ✓ ITAD 매핑: {game.title}')
            else:
                self.stdout.write(self.style.WARNING(f'  ✗ 미발견: {game.title}'))
            time.sleep(0.35)

        mapped = [(g, uuid_map[g.pk]) for g in games if g.pk in uuid_map]
        if not mapped:
            return

        # 배치 현재가격 조회
        uuids = [uid for _, uid in mapped]
        prices_by_id: dict = {}
        try:
            prices = self._post('/games/prices/v3', uuids, country=self.country)
            prices_by_id = {p['id']: p for p in prices}
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  가격 배치 조회 실패: {e}'))

        for game, uid in mapped:
            p = prices_by_id.get(uid, {})
            deals = p.get('deals', [])

            if deals:
                best = min(deals, key=lambda d: d['price']['amount'])
                changed = []
                if float(game.price) != best['price']['amount']:
                    game.price = best['price']['amount']
                    changed.append('price')
                if float(game.original_price) != best['regular']['amount']:
                    game.original_price = best['regular']['amount']
                    changed.append('original_price')
                if game.discount_percent != best.get('cut', 0):
                    game.discount_percent = best.get('cut', 0)
                    changed.append('discount_percent')
                if changed:
                    game.save(update_fields=changed)

            # 가격 히스토리
            self._fetch_history(game, uid)
            time.sleep(0.35)

    # ── 가격 히스토리 수집 ─────────────────────────────────────────

    def _fetch_history(self, game: Game, uid: str):
        try:
            history = self._get(
                '/games/history/v2', id=uid, country=self.country,
                since='2020-01-01T00:00:00Z'
            )
        except Exception as e:
            self.stdout.write(f'    히스토리 오류 ({game.title}): {e}')
            return

        ph_new = 0

        for entry in history:
            ts = parse_datetime(entry.get('timestamp', ''))
            if not ts:
                continue
            shop = entry['shop']['name']
            deal = entry['deal']
            price_amt = deal['price']['amount']
            regular_amt = deal['regular']['amount']
            cut = deal.get('cut', 0)
            currency = deal['price'].get('currency', 'KRW')

            _, created = GamePriceHistory.objects.get_or_create(
                game=game,
                shop_name=shop,
                recorded_at=ts,
                defaults={
                    'price': price_amt,
                    'original_price': regular_amt,
                    'discount_percent': cut,
                    'currency': currency,
                }
            )
            if created:
                ph_new += 1

        self.stdout.write(
            f'    {game.title[:30]}: 가격이력 +{ph_new}건'
        )

    # ── 신규 게임 (ITAD 딜 목록, 다중 페이지) ──────────────────────

    def _fetch_new_deals(self, limit: int):
        self.stdout.write(f'\n[2/2] ITAD 딜에서 신규 게임 수집 (최대 {limit}개)...')

        new_items: list[dict] = []
        offset = 0
        page = 0
        max_pages = 30  # 페이지당 ~10개 게임 → 30페이지면 최대 300개

        while len(new_items) < limit and page < max_pages:
            try:
                raw = self._get('/deals/v2', country=self.country,
                                limit=200, offset=offset, sort='rank')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  딜 조회 실패: {e}'))
                break

            deals_list = raw.get('list', []) if isinstance(raw, dict) else raw
            has_more = raw.get('hasMore', False) if isinstance(raw, dict) else False
            next_offset = raw.get('nextOffset', offset + 200) if isinstance(raw, dict) else offset + 200

            found_this_page = 0
            for item in deals_list:
                if len(new_items) >= limit:
                    break
                if item.get('type') != 'game':
                    continue
                title = item.get('title', '')
                uid = item.get('id', '')
                if not title or not uid:
                    continue
                if Game.objects.filter(title=title).exists():
                    continue
                if Game.objects.filter(itad_id=uid).exists():
                    continue
                if any(x['id'] == uid for x in new_items):
                    continue
                new_items.append(item)
                found_this_page += 1

            self.stdout.write(
                f'  페이지 {page + 1}: 딜 {len(deals_list)}개 / 신규 게임 +{found_this_page}개'
                f' (누적 {len(new_items)}개)'
            )

            if not has_more or not deals_list:
                break

            offset = next_offset
            page += 1
            time.sleep(0.5)

        if not new_items:
            self.stdout.write('  신규 게임 없음')
            return

        # 배치 가격 조회 (200개 단위)
        uuids = [item['id'] for item in new_items]
        prices_by_id: dict = {}
        try:
            for i in range(0, len(uuids), 200):
                batch = self._post('/games/prices/v3', uuids[i:i + 200],
                                   country=self.country)
                for p in batch:
                    prices_by_id[p['id']] = p
            time.sleep(0.5)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  가격 배치 조회 실패: {e}'))

        added = 0
        for item in new_items:
            uid = item['id']
            title = item.get('title', '')

            deal_sub = item.get('deal', {})
            raw_price = deal_sub.get('price', {}).get('amount', 0)
            raw_regular = deal_sub.get('regular', {}).get('amount', 0)
            raw_cut = deal_sub.get('cut', 0)
            shop_name = deal_sub.get('shop', {}).get('name', '')

            p = prices_by_id.get(uid, {})
            pd = p.get('deals', [])
            if pd:
                best = min(pd, key=lambda d: d['price']['amount'])
                raw_price = best['price']['amount']
                raw_regular = best['regular']['amount']
                raw_cut = best.get('cut', 0)
                shop_name = best['shop']['name']

            assets = item.get('assets', {})
            image = (assets.get('banner300') or assets.get('banner145')
                     or assets.get('boxart') or '')

            try:
                game = Game.objects.create(
                    title=title,
                    itad_id=uid,
                    platform=_platform(shop_name),
                    price=raw_price or 0,
                    original_price=raw_regular or raw_price or 0,
                    discount_percent=raw_cut,
                    image_url=image,
                )
                added += 1
                self.stdout.write(f'  + {title[:45]} ({raw_cut}% off, {shop_name})')

                self._fetch_history(game, uid)
                time.sleep(0.35)

            except IntegrityError:
                pass

        self.stdout.write(f'  -> {added}개 신규 게임 추가 완료')

    # ── 특정 타이틀 직접 추가 ─────────────────────────────────────

    def _add_by_titles(self, titles: list[str]):
        self.stdout.write(f'\n타이틀 지정 수집: {len(titles)}개')
        added = 0
        for title in titles:
            if Game.objects.filter(title__iexact=title).exists():
                self.stdout.write(f'  [skip] 이미 존재: {title}')
                continue

            uid = self._search(title)
            if not uid:
                self.stdout.write(self.style.WARNING(f'  [miss] ITAD 미발견: {title}'))
                time.sleep(0.35)
                continue

            prices_by_id = {}
            try:
                batch = self._post('/games/prices/v3', [uid], country=self.country)
                prices_by_id = {p['id']: p for p in batch}
            except Exception:
                pass

            p = prices_by_id.get(uid, {})
            deals = p.get('deals', [])
            raw_price = raw_regular = raw_cut = 0
            shop_name = image = ''

            if deals:
                best = min(deals, key=lambda d: d['price']['amount'])
                raw_price = best['price']['amount']
                raw_regular = best['regular']['amount']
                raw_cut = best.get('cut', 0)
                shop_name = best['shop']['name']

            try:
                game = Game.objects.create(
                    title=title,
                    itad_id=uid,
                    platform=_platform(shop_name),
                    price=raw_price or 0,
                    original_price=raw_regular or raw_price or 0,
                    discount_percent=raw_cut,
                    image_url=image,
                )
                added += 1
                self.stdout.write(f'  + {title} ({raw_cut}% off, {shop_name or "N/A"})')
                self._fetch_history(game, uid)
            except IntegrityError:
                pass

            time.sleep(0.5)

        self.stdout.write(f'\n완료: {added}개 추가')
        self.stdout.write(f'  게임 총 {Game.objects.count()}개 / 가격이력 {GamePriceHistory.objects.count()}건')
