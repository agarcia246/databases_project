from django.db import models

# Create your models here.

class InventoryTransactionTypes(models.Model):
    id = models.IntegerField(primary_key=True)
    type_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'inventory_transaction_types'


class InventoryTransactions(models.Model):
    transaction_type = models.ForeignKey(InventoryTransactionTypes, models.DO_NOTHING, db_column='transaction_type')
    transaction_created_date = models.DateTimeField(blank=True, null=True)
    transaction_modified_date = models.DateTimeField(blank=True, null=True)
    product = models.ForeignKey('catalog.Products', models.DO_NOTHING)
    quantity = models.IntegerField()
    purchase_order = models.ForeignKey('PurchaseOrders', models.DO_NOTHING, blank=True, null=True)
    customer_order = models.ForeignKey('sales.Orders', models.DO_NOTHING, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'inventory_transactions'


class PurchaseOrderDetails(models.Model):
    purchase_order = models.ForeignKey('PurchaseOrders', models.DO_NOTHING)
    product = models.ForeignKey('catalog.Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=19, decimal_places=4)
    date_received = models.DateTimeField(blank=True, null=True)
    posted_to_inventory = models.IntegerField()
    inventory = models.ForeignKey(InventoryTransactions, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_order_details'


class PurchaseOrderStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    status = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_order_status'


class PurchaseOrders(models.Model):
    supplier = models.ForeignKey('crm.Suppliers', models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey('crm.Employees', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    submitted_date = models.DateTimeField(blank=True, null=True)
    creation_date = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(PurchaseOrderStatus, models.DO_NOTHING, blank=True, null=True)
    expected_date = models.DateTimeField(blank=True, null=True)
    shipping_fee = models.DecimalField(max_digits=19, decimal_places=4)
    taxes = models.DecimalField(max_digits=19, decimal_places=4)
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    approved_by = models.IntegerField(blank=True, null=True)
    approved_date = models.DateTimeField(blank=True, null=True)
    submitted_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_orders'
