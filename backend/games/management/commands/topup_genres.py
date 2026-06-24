"""
python manage.py topup_genres
  - 장르 3개 미만인 게임에 장르를 추가해 최소 3개를 보장
"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from games.models import Game, GameGenre, Genre

# 기본 장르 → 우선순위별 폴백 장르 (앞에서부터 필요한 만큼 채움)
FALLBACK_MAP: dict[str, list[str]] = {
    "rpg":        ["rpg", "action_rpg", "adventure", "action", "open_world"],
    "fps":        ["fps", "shooter", "action", "adventure", "survival"],
    "strategy":   ["strategy", "turn_based", "rts", "simulation", "action"],
    "simulation": ["simulation", "management", "life_sim", "adventure", "indie"],
    "adventure":  ["adventure", "action", "open_world", "rpg", "indie"],
    "sports":     ["sports", "racing", "action", "simulation", "fighting"],
    "horror":     ["horror", "survival", "adventure", "action", "indie"],
    "indie":      ["indie", "action", "adventure", "platformer", "puzzle"],
    "other":      ["action", "adventure", "indie", "other", "simulation"],
}

# 세부 장르 보강: 이미 가진 장르 기반으로 추가 연관 장르
GENRE_COMPANIONS: dict[str, list[str]] = {
    "action_rpg":     ["rpg", "action"],
    "jrpg":           ["rpg", "turn_based"],
    "mmorpg":         ["rpg", "adventure"],
    "souls_like":     ["action_rpg", "action"],
    "hack_slash":     ["action", "action_rpg"],
    "metroidvania":   ["platformer", "action"],
    "roguelike":      ["action", "indie"],
    "open_world":     ["adventure", "action"],
    "battle_royale":  ["fps", "shooter"],
    "tps":            ["shooter", "action"],
    "rts":            ["strategy", "simulation"],
    "tower_defense":  ["strategy", "action"],
    "turn_based":     ["strategy", "rpg"],
    "management":     ["simulation", "strategy"],
    "life_sim":       ["simulation", "adventure"],
    "visual_novel":   ["adventure", "indie"],
    "platformer":     ["action", "indie"],
    "puzzle":         ["indie", "adventure"],
    "sandbox":        ["survival", "adventure"],
    "survival":       ["action", "adventure"],
    "co_op":          ["action", "adventure"],
    "stealth":        ["action", "adventure"],
    "horror":         ["survival", "action"],
    "racing":         ["sports", "action"],
    "fighting":       ["action", "sports"],
    "card_game":      ["strategy", "indie"],
    "moba":           ["strategy", "action"],
}


class Command(BaseCommand):
    help = "각 게임이 최소 3개의 장르를 갖도록 장르를 추가합니다."

    def handle(self, *args, **options):
        genre_map: dict[str, Genre] = {g.key: g for g in Genre.objects.all()}
        games = (
            Game.objects.annotate(gc=Count("game_genres"))
            .filter(gc__lt=3)
            .prefetch_related("game_genres__genre")
        )

        self.stdout.write(f"▶ 3개 미만 게임: {games.count()}개 처리 중...")

        added_total = 0

        for game in games:
            existing_keys = {gg.genre.key for gg in game.game_genres.all()}
            needed = 3 - len(existing_keys)
            if needed <= 0:
                continue

            candidates: list[str] = []

            # 1단계: 이미 가진 장르의 연관 장르
            for key in list(existing_keys):
                for companion in GENRE_COMPANIONS.get(key, []):
                    if companion not in existing_keys and companion not in candidates:
                        candidates.append(companion)

            # 2단계: 기본 장르 폴백
            for key in FALLBACK_MAP.get(game.genre, FALLBACK_MAP["other"]):
                if key not in existing_keys and key not in candidates:
                    candidates.append(key)

            # 3단계: 최후 폴백 (action, adventure, indie)
            for key in ["action", "adventure", "indie", "other"]:
                if key not in existing_keys and key not in candidates:
                    candidates.append(key)

            added = 0
            for key in candidates:
                if added >= needed:
                    break
                genre_obj = genre_map.get(key)
                if not genre_obj:
                    continue
                _, created = GameGenre.objects.get_or_create(game=game, genre=genre_obj)
                if created:
                    added += 1

            added_total += added

        self.stdout.write(self.style.SUCCESS(f"  GameGenre {added_total}개 추가 완료"))

        # 결과 검증
        still_under = Game.objects.annotate(gc=Count("game_genres")).filter(gc__lt=3).count()
        if still_under:
            self.stdout.write(self.style.WARNING(f"  아직 3개 미만: {still_under}개"))
        else:
            self.stdout.write(self.style.SUCCESS("  모든 게임이 장르 3개 이상 보유"))

        # 분포 확인
        self.stdout.write("\n▶ 장르 수 분포:")
        for n in range(1, 8):
            cnt = Game.objects.annotate(gc=Count("game_genres")).filter(gc=n).count()
            if cnt:
                self.stdout.write(f"  {n}개: {cnt}게임")
        plus = Game.objects.annotate(gc=Count("game_genres")).filter(gc__gte=8).count()
        if plus:
            self.stdout.write(f"  8개+: {plus}게임")
