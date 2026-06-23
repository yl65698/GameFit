from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nickname", "show_hashtags", "discount_alerts")
    search_fields = ("user__username", "nickname")
