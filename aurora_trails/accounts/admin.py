from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import GuideProfile, User


class GuideProfileInline(admin.StackedInline):
    model = GuideProfile
    can_delete = False


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "role")}),
    ) + UserAdmin.add_fieldsets
    list_display = ("email", "username", "first_name", "last_name", "role", "is_staff")
    inlines = [GuideProfileInline]