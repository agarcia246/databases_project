from django.db import models

# Create your models here.

class SalesReports(models.Model):
    group_by = models.CharField(primary_key=True, max_length=50)
    display = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=50, blank=True, null=True)
    filter_row_source = models.TextField(blank=True, null=True)
    default = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sales_reports'