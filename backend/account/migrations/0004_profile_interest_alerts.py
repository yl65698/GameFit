from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_profile_game_platforms"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="interest_alerts",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
