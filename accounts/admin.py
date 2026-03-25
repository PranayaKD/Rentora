from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'wallet_balance', 'is_verified', 'created_at')
    search_fields = ('user__username', 'phone')
    list_filter = ('is_verified',)
