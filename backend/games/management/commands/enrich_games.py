"""
GMS API (gpt-5-nano)로 게임 description · genre · 시스템 사양 자동 생성

사용법:
  python manage.py enrich_games              # description 없는 게임 전체 처리
  python manage.py enrich_games --all        # 이미 채워진 것도 재생성
  python manage.py enrich_games --genre-only # genre=other 인 것만 재분류
  python manage.py enrich_games --batch 20   # 최대 N개만 처리
"""

import json
import time
import requests
from django.core.management.base import BaseCommand
from games.models import Game

GMS_URL = 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions'
GMS_KEY = 'S15P02AE07-357d1395-3321-4eaa-b133-0b212facf6b2'
MODEL = 'gpt-5-nano'

GENRE_CHOICES = {'rpg', 'fps', 'strategy', 'simulation', 'adventure', 'sports', 'horror', 'indie', 'other'}

SYSTEM_PROMPT = (
    "You are a video game database assistant. "
    "Given a game title, return ONLY a JSON object (no markdown, no explanation) with these fields:\n"
    "- description: 2~3 sentences in Korean that describe the game's core gameplay and appeal\n"
    "- genre: exactly one string from [rpg, fps, strategy, simulation, adventure, sports, horror, indie, other]\n"
    "- min_cpu: minimum CPU (e.g. \"Intel Core i5-4460\")\n"
    "- min_gpu: minimum GPU (e.g. \"NVIDIA GTX 970\")\n"
    "- min_ram: minimum RAM (e.g. \"8GB\")\n"
    "- rec_cpu: recommended CPU (e.g. \"Intel Core i7-8700K\")\n"
    "- rec_gpu: recommended GPU (e.g. \"NVIDIA RTX 2060\")\n"
    "- rec_ram: recommended RAM (e.g. \"16GB\")\n"
    "Use realistic system requirements based on known game data. "
    "If unsure, estimate based on the game's release year and complexity."
)


def _call_gms(title: str) -> dict | None:
    try:
        r = requests.post(
            GMS_URL,
            headers={
                'Authorization': f'Bearer {GMS_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': MODEL,
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': f'Game title: {title}'},
                ],
                'temperature': 0.2,
            },
            timeout=30,
        )
        r.raise_for_status()
        raw = r.json()['choices'][0]['message']['content'].strip()

        # 마크다운 코드블록 제거
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)
    except Exception as e:
        return None


class Command(BaseCommand):
    help = 'GMS API로 게임 description · genre · 시스템사양 자동 생성'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', dest='all_games',
                            help='이미 채워진 필드도 재생성')
        parser.add_argument('--genre-only', action='store_true',
                            help='genre=other 인 게임만 재분류')
        parser.add_argument('--batch', type=int, default=0,
                            help='최대 처리 개수 (0=전체)')

    def handle(self, *args, **options):
        if options['genre_only']:
            games = list(Game.objects.filter(genre='other').order_by('id'))
        elif options['all_games']:
            games = list(Game.objects.all().order_by('id'))
        else:
            games = list(Game.objects.filter(description='').order_by('id'))

        if options['batch']:
            games = games[:options['batch']]

        total = len(games)
        self.stdout.write(self.style.SUCCESS(f'=== 게임 정보 자동 생성 ({total}개) ==='))

        ok = fail = 0
        for i, game in enumerate(games, 1):
            label = game.title[:42]
            self.stdout.write(f'[{i:>3}/{total}] {label:<42}', ending=' ')
            self.stdout.flush()

            data = _call_gms(game.title)
            if not data:
                self.stdout.write(self.style.ERROR('FAIL'))
                fail += 1
                time.sleep(1.5)
                continue

            update_fields = []

            if not options['genre_only']:
                desc = (data.get('description') or '').strip()
                if desc:
                    game.description = desc
                    update_fields.append('description')
                for field in ('min_cpu', 'min_gpu', 'min_ram', 'rec_cpu', 'rec_gpu', 'rec_ram'):
                    val = (data.get(field) or '').strip()
                    if val:
                        setattr(game, field, val)
                        update_fields.append(field)

            genre = (data.get('genre') or '').lower().strip()
            if genre in GENRE_CHOICES:
                game.genre = genre
                update_fields.append('genre')

            if update_fields:
                game.save(update_fields=list(set(update_fields)))

            self.stdout.write(
                self.style.SUCCESS(f'OK  genre={game.genre}')
            )
            ok += 1
            time.sleep(0.4)

        self.stdout.write(f'\n완료: {ok}개 성공 / {fail}개 실패')
        self.stdout.write(f'  genre 분포: ', ending='')
        from django.db.models import Count
        dist = Game.objects.values('genre').annotate(n=Count('id')).order_by('-n')
        self.stdout.write(' | '.join(f"{r['genre']}:{r['n']}" for r in dist))
