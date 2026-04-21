from django.contrib import admin

from .models import ShopProfile


@admin.register(ShopProfile)
class ShopProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'customer_id', 'created_at')
    search_fields = ('user__username', 'user__email', 'customer_id')
    raw_id_fields = ('user',)
