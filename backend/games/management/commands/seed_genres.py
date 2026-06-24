"""
python manage.py seed_genres
  - Genre 레코드 생성 (없으면 추가)
  - 기존 게임의 game.genre 필드 → GameGenre 매핑
  - 제목/설명 키워드 기반 추가 세부 장르 배정
"""
from django.core.management.base import BaseCommand

from games.models import Game, GameGenre, Genre


# ── 전체 장르 목록 ─────────────────────────────────────────────
GENRES = [
    # 기본 장르
    ("rpg",           "RPG"),
    ("action_rpg",    "액션 RPG"),
    ("jrpg",          "JRPG"),
    ("mmorpg",        "MMORPG"),
    ("turn_based",    "턴제"),
    ("fps",           "FPS"),
    ("tps",           "TPS"),
    ("shooter",       "슈터"),
    ("battle_royale", "배틀로얄"),
    ("strategy",      "전략"),
    ("rts",           "RTS"),
    ("tower_defense", "타워 디펜스"),
    ("simulation",    "시뮬레이션"),
    ("management",    "경영 시뮬"),
    ("life_sim",      "생활 시뮬"),
    ("adventure",     "어드벤처"),
    ("open_world",    "오픈월드"),
    ("visual_novel",  "비주얼 노벨"),
    ("sports",        "스포츠"),
    ("racing",        "레이싱"),
    ("fighting",      "격투"),
    ("horror",        "공포"),
    ("survival",      "서바이벌"),
    ("indie",         "인디"),
    ("platformer",    "플랫포머"),
    ("puzzle",        "퍼즐"),
    ("roguelike",     "로그라이크"),
    ("sandbox",       "샌드박스"),
    ("stealth",       "스텔스"),
    ("hack_slash",    "핵 앤 슬래시"),
    ("moba",          "MOBA"),
    ("card_game",     "카드 게임"),
    ("metroidvania",  "메트로바니아"),
    ("souls_like",    "소울즈라이크"),
    ("co_op",         "협동"),
    ("action",        "액션"),
    ("other",         "기타"),
]

# ── 기본 장르 키 → 추가 배정 세부 장르 ────────────────────────
BASE_GENRE_EXTRAS: dict[str, list[str]] = {
    "rpg":        ["rpg", "action_rpg"],
    "fps":        ["fps", "shooter"],
    "strategy":   ["strategy"],
    "simulation": ["simulation"],
    "adventure":  ["adventure"],
    "sports":     ["sports"],
    "horror":     ["horror"],
    "indie":      ["indie"],
    "other":      ["other"],
}

# ── 제목/설명 키워드 → 추가 장르 ─────────────────────────────
KEYWORD_RULES: list[tuple[list[str], list[str]]] = [
    # 소울즈라이크
    (["souls", "elden ring", "dark souls", "sekiro", "nioh", "lies of p", "remnant"],
     ["souls_like", "action_rpg", "action"]),
    # 로그라이크
    (["hades", "rogue", "roguelike", "roguelite", "dead cells", "slay the spire",
      "binding of isaac", "vampire survivors", "noita", "enter the gungeon"],
     ["roguelike"]),
    # 메트로바니아
    (["metroid", "castlevania", "hollow knight", "ori", "blasphemous", "bloodstained"],
     ["metroidvania", "platformer"]),
    # 오픈월드
    (["open world", "open-world", "witcher", "skyrim", "cyberpunk", "gta",
      "red dead", "assassin", "far cry", "breath of the wild"],
     ["open_world", "adventure"]),
    # MMORPG
    (["mmo", "online rpg", "world of warcraft", "final fantasy xiv", "ffxiv",
      "lost ark", "black desert", "guild wars"],
     ["mmorpg", "rpg"]),
    # JRPG
    (["persona", "dragon quest", "final fantasy", "tales of", "xenoblade",
      "ni no kuni", "nier", "octopath"],
     ["jrpg", "rpg"]),
    # 턴제
    (["turn", "xcom", "civilization", "into the breach", "banner saga",
      "divinity", "baldur", "fire emblem"],
     ["turn_based", "strategy"]),
    # RTS
    (["starcraft", "warcraft", "age of empires", "command & conquer",
      "total war", "company of heroes", "real-time strategy"],
     ["rts", "strategy"]),
    # 타워 디펜스
    (["tower defense", "tower defence", "bloons", "plants vs"],
     ["tower_defense", "strategy"]),
    # 배틀로얄
    (["battle royale", "pubg", "fortnite", "apex legends", "warzone"],
     ["battle_royale", "shooter", "fps"]),
    # TPS
    (["third person", "third-person", "gears of war", "uncharted", "tomb raider",
      "max payne"],
     ["tps", "shooter"]),
    # 핵 앤 슬래시
    (["hack and slash", "hack & slash", "diablo", "path of exile", "torchlight",
      "dungeon siege"],
     ["hack_slash", "action_rpg"]),
    # MOBA
    (["moba", "dota", "league of legends", "smite", "heroes of the storm"],
     ["moba"]),
    # 카드 게임
    (["card", "hearthstone", "gwent", "poker", "slay the spire"],
     ["card_game"]),
    # 비주얼 노벨
    (["visual novel", "visual_novel", "kinetic novel", "dating sim",
      "ace attorney", "danganronpa"],
     ["visual_novel"]),
    # 샌드박스
    (["minecraft", "terraria", "sandbox", "valheim", "rust", "ark survival",
      "don't starve", "dont starve"],
     ["sandbox", "survival"]),
    # 서바이벌
    (["survival", "subnautica", "green hell", "the forest", "stranded deep"],
     ["survival"]),
    # 플랫포머
    (["platformer", "platform", "mario", "sonic", "celeste", "shovel knight",
      "cuphead", "rayman"],
     ["platformer"]),
    # 퍼즐
    (["puzzle", "portal", "tetris", "baba is you", "the witness", "sudoku",
      "escape room"],
     ["puzzle"]),
    # 레이싱
    (["racing", "forza", "gran turismo", "need for speed", "f1", "dirt rally",
      "assetto corsa"],
     ["racing", "sports"]),
    # 격투
    (["fighting", "mortal kombat", "street fighter", "tekken", "guilty gear",
      "dragon ball fighterz"],
     ["fighting"]),
    # 스텔스
    (["stealth", "hitman", "dishonored", "thief", "metal gear"],
     ["stealth"]),
    # 경영 시뮬
    (["management", "tycoon", "city builder", "planet coaster", "two point",
      "football manager", "rimworld", "dwarf fortress"],
     ["management", "simulation"]),
    # 생활 시뮬
    (["stardew", "animal crossing", "sims", "life sim", "harvest moon",
      "rune factory"],
     ["life_sim", "simulation"]),
    # 협동
    (["co-op", "coop", "it takes two", "a way out", "left 4 dead",
      "deep rock galactic", "phasmophobia"],
     ["co_op"]),
    # 공포
    (["horror", "resident evil", "silent hill", "outlast", "amnesia",
      "fnaf", "five nights", "fear"],
     ["horror"]),
    # 액션
    (["action", "bayonetta", "devil may cry", "god of war", "monster hunter"],
     ["action"]),
    # 스포츠
    (["fifa", "nba", "nfl", "mlb", "pro evolution", "rocket league", "tennis",
      "golf"],
     ["sports"]),
]


def get_extra_genres(game: Game) -> set[str]:
    """제목 + 설명 키워드 기반으로 추가 장르 키 반환"""
    text = (game.title + " " + game.description).lower()
    result: set[str] = set()
    for keywords, genres in KEYWORD_RULES:
        if any(kw in text for kw in keywords):
            result.update(genres)
    return result


class Command(BaseCommand):
    help = "Genre / GameGenre 테이블에 장르 데이터를 생성하고 게임에 매핑합니다."

    def handle(self, *args, **options):
        # 1. 장르 레코드 생성
        self.stdout.write("▶ 장르 레코드 생성 중...")
        genre_map: dict[str, Genre] = {}
        for key, name in GENRES:
            genre, created = Genre.objects.get_or_create(key=key, defaults={"name": name})
            if created:
                self.stdout.write(f"  [신규] {name}")
            genre_map[key] = genre
        self.stdout.write(self.style.SUCCESS(f"  총 {len(genre_map)}개 장르 준비 완료"))

        # 2. 게임 → 장르 매핑
        self.stdout.write("▶ 게임 장르 매핑 중...")
        games = Game.objects.all()
        created_count = 0

        for game in games:
            # 기본 장르 (game.genre 필드 기반)
            genre_keys: set[str] = set(BASE_GENRE_EXTRAS.get(game.genre, ["other"]))
            # 키워드 기반 추가 장르
            genre_keys.update(get_extra_genres(game))

            for key in genre_keys:
                genre_obj = genre_map.get(key)
                if not genre_obj:
                    continue
                _, created = GameGenre.objects.get_or_create(game=game, genre=genre_obj)
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"  GameGenre 레코드 {created_count}개 생성 완료 (게임 {games.count()}개)"
        ))

        # 3. 결과 요약
        from django.db.models import Count
        self.stdout.write("\n▶ 장르별 게임 수:")
        for genre in Genre.objects.annotate(game_count=Count("game_genres")).filter(game_count__gt=0).order_by("-game_count"):
            self.stdout.write(f"  {genre.name}: {genre.game_count}개")
