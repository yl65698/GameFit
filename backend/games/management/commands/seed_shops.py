import os
import requests
from django.core.management.base import BaseCommand
from games.models import GameShop

SHOP_URLS = {
    19:  "https://www.2game.com",
    2:   "https://www.allyouplay.com",
    4:   "https://us.battle.net/shop",
    15:  "https://www.dreamgame.com",
    52:  "https://www.ea.com/games",
    16:  "https://store.epicgames.com",
    67:  "https://etail.market",
    6:   "https://www.fanatical.com",
    17:  "https://firefowergames.com",
    75:  "https://www.fortunadigital.com",
    20:  "https://www.gamebillet.com",
    24:  "https://www.gamersgate.com",
    27:  "https://de.gamesplanet.com",
    28:  "https://fr.gamesplanet.com",
    26:  "https://uk.gamesplanet.com",
    29:  "https://us.gamesplanet.com",
    76:  "https://www.gamesporium.com",
    35:  "https://www.gog.com",
    36:  "https://www.greenmangaming.com",
    37:  "https://www.humblebundle.com/store",
    42:  "https://store.indiegala.com",
    65:  "https://www.joybuggy.com",
    47:  "https://www.macgamestore.com",
    48:  "https://www.microsoft.com/store",
    50:  "https://www.nuuvem.com",
    73:  "https://www.planetplay.com",
    74:  "https://playerland.com",
    70:  "https://www.playsum.com",
    61:  "https://store.steampowered.com",
    62:  "https://store.ubisoft.com",
    64:  "https://www.wingamestore.com",
    72:  "https://www.zoom-platform.com",
}


class Command(BaseCommand):
    help = "ITAD API로 게임 샵 목록을 가져와 DB에 저장"

    def handle(self, *args, **options):
        key = os.environ.get("IS_THERE_ANY_DEAL_API_KEY", "")
        try:
            resp = requests.get(
                "https://api.isthereanydeal.com/service/shops/v1",
                params={"country": "KR", "key": key},
                timeout=10,
            )
            resp.raise_for_status()
            shops = resp.json()
        except Exception as e:
            self.stderr.write(f"API 오류: {e}")
            return

        created = updated = 0
        for shop in shops:
            itad_id = shop["id"]
            name = shop["title"]
            url = SHOP_URLS.get(itad_id, "")
            obj, is_new = GameShop.objects.update_or_create(
                itad_id=itad_id,
                defaults={"name": name, "url": url},
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"완료: {created}개 생성, {updated}개 업데이트 (총 {GameShop.objects.count()}개)"
        ))
