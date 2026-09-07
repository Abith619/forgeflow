from django.contrib import admin
from .models import Company, User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active"]
    search_fields = ["name", "code"]
    list_filter = ["is_active"]

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["full_name"]
    list_display = ["email", "full_name", "company", "is_active", "is_staff", "date_joined"]
    search_fields = ["email", "full_name"]
    list_filter = ["is_active", "is_staff", "date_joined"]

    fieldsets = ((None, {"fields": ("email", "password")}),
                    ("Personal info", {"fields": ("full_name", "company")}),
                    ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
                    ("Important dates", {"fields": ("last_login", "date_joined")}
                ))

    add_fieldsets = ((None, {"classes": ("wide",),
                        "fields": ("email", "password1", "password2", "full_name", "company")}),
                    )

    filter_horizontal = ("groups", "user_permissions")