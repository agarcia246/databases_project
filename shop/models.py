"""Storefront-side models.

The only managed model in this app is :class:`ShopProfile`, which links a
Django ``User`` (storefront login) to a row in the unmanaged ``customers``
table that lives on the MySQL side. We can't use a real ``ForeignKey`` to
``Customers`` because the table is shared with the back-office CRM and we
don't want Django to attempt to manage its schema, so the link is stored as
a plain integer that we hydrate explicitly via :meth:`ShopProfile.customer`.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from crm.models import Customers


class ShopProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shop_profile',
    )
    # Soft pointer at the unmanaged ``customers.id`` column.
    customer_id = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shop_profile'

    def __str__(self):
        return f'ShopProfile<user={self.user_id}, customer={self.customer_id}>'

    @property
    def customer(self) -> Customers | None:
        """Return the linked ``Customers`` row, or ``None`` if it was deleted."""
        if not hasattr(self, '_customer_cache'):
            self._customer_cache = (
                Customers.objects.filter(pk=self.customer_id).first()
            )
        return self._customer_cache
