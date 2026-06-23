from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            nickname=instance.username,
            hashtags=["전략", "협동", "인디"],
            pc_specs={
                "cpu": "AMD Ryzen 7 5800X",
                "memory": "64GB",
                "gpu": "NVIDIA RTX 3070 Ti",
                "storage": "C: 200GB / 2TB",
                "vr": "없음",
                "console": "없음",
            },
            owned_games=["Civilization VI", "Dead by Daylight", "Stardew Valley"],
            interested_games=["It Takes Two", "The Last of Us", "Hades II"],
            game_platforms={
                "Civilization VI": "Steam",
                "Dead by Daylight": "Steam",
                "Stardew Valley": "Steam",
                "It Takes Two": "Epic games",
                "The Last of Us": "Epic games",
                "Hades II": "Steam",
            },
        )
