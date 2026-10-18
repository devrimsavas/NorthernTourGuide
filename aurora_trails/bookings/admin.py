from django.contrib import admin

from .models import Booking,Review


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "slot", "participants", "total_price", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("reference", "created_at")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display=("booking","rating","created_at")
    list_filter=("rating",)