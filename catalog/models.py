from django.db import models

# Create your models here.

class Products(models.Model):
    supplier_ids = models.TextField(blank=True, null=True)
    product_code = models.CharField(max_length=25, blank=True, null=True)
    product_name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    standard_cost = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    list_price = models.DecimalField(max_digits=19, decimal_places=4)
    reorder_level = models.IntegerField(blank=True, null=True)
    target_level = models.IntegerField(blank=True, null=True)
    quantity_per_unit = models.CharField(max_length=50, blank=True, null=True)
    discontinued = models.IntegerField()
    minimum_reorder_quantity = models.IntegerField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    attachments = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'