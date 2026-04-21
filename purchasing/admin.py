from django.contrib import admin
from .models import PurchaseOrders, PurchaseOrderDetails, PurchaseOrderStatus, InventoryTransactions, InventoryTransactionTypes


@admin.register(PurchaseOrders)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "created_by", "creation_date", "status", "expected_date")
    search_fields = ("id", "supplier__company", "created_by__first_name", "created_by__last_name")
    list_filter = ("status", "creation_date", "expected_date")


@admin.register(PurchaseOrderDetails)
class PurchaseOrderDetailsAdmin(admin.ModelAdmin):
    list_display = ("id", "purchase_order", "product", "quantity", "unit_cost", "date_received")
    search_fields = ("purchase_order__id", "product__product_name")


@admin.register(PurchaseOrderStatus)
class PurchaseOrderStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "status")


@admin.register(InventoryTransactions)
class InventoryTransactionsAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction_type", "product", "quantity", "transaction_created_date")
    list_filter = ("transaction_type", "transaction_created_date")
    search_fields = ("product__product_name",)


@admin.register(InventoryTransactionTypes)
class InventoryTransactionTypesAdmin(admin.ModelAdmin):
    list_display = ("id", "type_name")