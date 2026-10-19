from django.contrib import admin

from .models import ActivityType, Location, Tour,TourSlot,TourImage

admin.site.register(ActivityType)
admin.site.register(Location)

class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 1

class TourSlotInline(admin.TabularInline):
    model = TourSlot
    extra = 1

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("title", "guide", "activity_type", "location", "price", "is_active")
    inlines=[TourSlotInline,TourImageInline]