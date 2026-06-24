from django.contrib import admin

from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['date', 'event_type', 'title']
    list_filter = ['event_type']
    ordering = ['date']
    search_fields = ['title', 'description']
    date_hierarchy = 'date'
