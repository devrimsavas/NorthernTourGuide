from django.contrib import admin

from .models import ActivityType, Location, Tour,TourSlot

admin.site.register(ActivityType)
admin.site.register(Location)

class TourSlotInline(admin.TabularInline):
    model = TourSlot
    extra = 1

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("title", "guide", "activity_type", "location", "price", "is_active")
    inlines=[TourSlotInline]