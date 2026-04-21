from django.db import models

# Create your models here.

class Customers(models.Model):
    company = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    email_address = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=50, blank=True, null=True)
    business_phone = models.CharField(max_length=25, blank=True, null=True)
    home_phone = models.CharField(max_length=25, blank=True, null=True)
    mobile_phone = models.CharField(max_length=25, blank=True, null=True)
    fax_number = models.CharField(max_length=25, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state_province = models.CharField(max_length=50, blank=True, null=True)
    zip_postal_code = models.CharField(max_length=15, blank=True, null=True)
    country_region = models.CharField(max_length=50, blank=True, null=True)
    web_page = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    attachments = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers'




class EmployeePrivileges(models.Model):
    pk = models.CompositePrimaryKey('employee_id', 'privilege_id')
    employee = models.ForeignKey('Employees', models.DO_NOTHING)
    privilege = models.ForeignKey('Privileges', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'employee_privileges'


class Employees(models.Model):
    company = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    email_address = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=50, blank=True, null=True)
    business_phone = models.CharField(max_length=25, blank=True, null=True)
    home_phone = models.CharField(max_length=25, blank=True, null=True)
    mobile_phone = models.CharField(max_length=25, blank=True, null=True)
    fax_number = models.CharField(max_length=25, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state_province = models.CharField(max_length=50, blank=True, null=True)
    zip_postal_code = models.CharField(max_length=15, blank=True, null=True)
    country_region = models.CharField(max_length=50, blank=True, null=True)
    web_page = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    attachments = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employees'


class Shippers(models.Model):
    company = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    email_address = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=50, blank=True, null=True)
    business_phone = models.CharField(max_length=25, blank=True, null=True)
    home_phone = models.CharField(max_length=25, blank=True, null=True)
    mobile_phone = models.CharField(max_length=25, blank=True, null=True)
    fax_number = models.CharField(max_length=25, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state_province = models.CharField(max_length=50, blank=True, null=True)
    zip_postal_code = models.CharField(max_length=15, blank=True, null=True)
    country_region = models.CharField(max_length=50, blank=True, null=True)
    web_page = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    attachments = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'shippers'


class Suppliers(models.Model):
    company = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    email_address = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=50, blank=True, null=True)
    business_phone = models.CharField(max_length=25, blank=True, null=True)
    home_phone = models.CharField(max_length=25, blank=True, null=True)
    mobile_phone = models.CharField(max_length=25, blank=True, null=True)
    fax_number = models.CharField(max_length=25, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state_province = models.CharField(max_length=50, blank=True, null=True)
    zip_postal_code = models.CharField(max_length=15, blank=True, null=True)
    country_region = models.CharField(max_length=50, blank=True, null=True)
    web_page = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    attachments = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'suppliers'

class Privileges(models.Model):
    privilege_name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'privileges'
