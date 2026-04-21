from django.contrib import admin
from .models import Orders, OrderDetails, OrdersStatus, OrdersTaxStatus, Invoices
# Register your models here.




@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "employee", "order_date", "shipped_date", "status", "shipper")
    search_fields = ("id", "customer__company", "employee__first_name", "employee__last_name")
    list_filter = ("status", "shipper", "order_date", "shipped_date")


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "unit_price", "discount", "status")
    search_fields = ("order__id", "product__product_name")
    list_filter = ("status",)


@admin.register(OrdersStatus)
class OrdersStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "status_name")


@admin.register(OrdersTaxStatus)
class OrdersTaxStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "tax_status_name")


@admin.register(Invoices)
class InvoicesAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "invoice_date", "due_date", "amount_due")
    list_filter = ("invoice_date", "due_date")