from django.contrib import admin
from .models import Customers, Employees, Shippers, Suppliers
# Register your models here.


@admin.register(Customers)
class CustomersAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "first_name",
        "last_name",
        "email_address",
        "business_phone",
        "country_region",
        )
    search_fields = (
        "company",
        "first_name",
        "last_name",
        "email_address",
        "country_region",
    )
    list_filter = (
        "country_region",
        "state_province",
        "city"
    )


@admin.register(Employees)
class EmployeesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "job_title",
        "email_address",
        "business_phone",
        )
    search_fields = (
        "first_name",
        "last_name",
        "job_title",
        "email_address",
    )

@admin.register(Suppliers)
class SuppliersAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "first_name",
        "last_name",
        "business_phone",
        "country_region",
        )
    search_fields = (
        "company",
        "first_name",
        "last_name",
    )


@admin.register(Shippers)
class ShippersAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "first_name",
        "last_name",
        "business_phone",
        )
    search_fields = (
        "company",
        "first_name",
        "last_name",
    )