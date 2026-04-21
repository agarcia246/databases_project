from django.db import models

# Create your models here.

class Invoices(models.Model):
    order = models.ForeignKey('Orders', models.DO_NOTHING, blank=True, null=True)
    invoice_date = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    tax = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    shipping = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    amount_due = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'invoices'


class OrderDetails(models.Model):
    order = models.ForeignKey('Orders', models.DO_NOTHING)
    product = models.ForeignKey('catalog.Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    discount = models.FloatField()
    status = models.ForeignKey('OrderDetailsStatus', models.DO_NOTHING, blank=True, null=True)
    date_allocated = models.DateTimeField(blank=True, null=True)
    purchase_order_id = models.IntegerField(blank=True, null=True)
    inventory_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_details'


class OrderDetailsStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    status_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'order_details_status'


class Orders(models.Model):
    employee = models.ForeignKey('crm.Employees', models.DO_NOTHING, blank=True, null=True)
    customer = models.ForeignKey('crm.Customers', models.DO_NOTHING, blank=True, null=True)
    order_date = models.DateTimeField(blank=True, null=True)
    shipped_date = models.DateTimeField(blank=True, null=True)
    shipper = models.ForeignKey('crm.Shippers', models.DO_NOTHING, blank=True, null=True)
    ship_name = models.CharField(max_length=50, blank=True, null=True)
    ship_address = models.TextField(blank=True, null=True)
    ship_city = models.CharField(max_length=50, blank=True, null=True)
    ship_state_province = models.CharField(max_length=50, blank=True, null=True)
    ship_zip_postal_code = models.CharField(max_length=50, blank=True, null=True)
    ship_country_region = models.CharField(max_length=50, blank=True, null=True)
    shipping_fee = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    taxes = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    paid_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    tax_rate = models.FloatField(blank=True, null=True)
    tax_status = models.ForeignKey('OrdersTaxStatus', models.DO_NOTHING, blank=True, null=True)
    status = models.ForeignKey('OrdersStatus', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class OrdersStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    status_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'orders_status'


class OrdersTaxStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    tax_status_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'orders_tax_status'
