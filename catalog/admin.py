from django.contrib import admin
from .models import Products
# Register your models here.

@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_code",
        "product_name",
        "category",
        "list_price",
        "discontinued",
        )
    search_fields = (
        "product_code",
        "product_name",
        "category",
    )
    list_filter = (
        "category",
        "discontinued"
    )