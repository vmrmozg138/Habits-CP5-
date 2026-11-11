from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "phone_number", "city", "is_staff", "is_active")
    search_fields = ("email", "phone_number", "city")
    list_filter = ("is_staff", "is_active", "city")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("phone_number", "city", "avatar", "tg_chat_id")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
