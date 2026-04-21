"""Application-layer helpers for sales.

The order placement flow lives here because the actual table layout is
``managed = False`` (the Northwind schema is shared across teams) and so we
prefer one small, well-tested function over scattered ``Orders.objects.create``
calls in views.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from catalog.models import Products
from crm.models import Customers, Shippers

from .models import (
    OrderDetails,
    OrderDetailsStatus,
    Orders,
    OrdersStatus,
    OrdersTaxStatus,
)


# Northwind status names we look up by name rather than hard-coding the IDs
# – the ``orders_status`` reference table can be re-keyed by an admin.
_NEW_ORDER_STATUS_NAMES = ('New', 'Open')
_NEW_DETAIL_STATUS_NAMES = ('Allocated', 'On Order', 'No Stock')
_TAX_STATUS_NAMES = ('Tax Inclusive', 'Inclusive', 'Taxable')


class OrderPlacementError(Exception):
    """Raised when an order cannot be created with the supplied data."""


@dataclass(frozen=True)
class OrderLineInput:
    product_id: int
    quantity: int
    unit_price: Decimal


def _resolve_status(model, names: Iterable[str]):
    """Return the first row in ``model`` whose ``status_name`` is in ``names``.

    Falls back to the lowest-id row so checkout still succeeds on a partially
    seeded reference table; returns ``None`` only if the table is empty.
    """
    candidates = list(model.objects.all())
    if not candidates:
        return None
    by_name = {(c.status_name or '').strip().lower(): c for c in candidates}
    for name in names:
        match = by_name.get(name.strip().lower())
        if match:
            return match
    return min(candidates, key=lambda c: c.pk)


def _resolve_tax_status():
    candidates = list(OrdersTaxStatus.objects.all())
    if not candidates:
        return None
    by_name = {(c.tax_status_name or '').strip().lower(): c for c in candidates}
    for name in _TAX_STATUS_NAMES:
        match = by_name.get(name.strip().lower())
        if match:
            return match
    return min(candidates, key=lambda c: c.pk)


def _validate_lines(lines: list[OrderLineInput]) -> list[tuple[OrderLineInput, Products]]:
    if not lines:
        raise OrderPlacementError('Your cart is empty.')

    ids = [ln.product_id for ln in lines]
    products = {p.pk: p for p in Products.objects.filter(pk__in=ids)}
    resolved: list[tuple[OrderLineInput, Products]] = []
    for line in lines:
        product = products.get(line.product_id)
        if product is None:
            raise OrderPlacementError(
                f'Product #{line.product_id} no longer exists.'
            )
        if product.discontinued:
            raise OrderPlacementError(
                f'"{product.product_name}" has been discontinued.'
            )
        if line.quantity < 1:
            raise OrderPlacementError(
                f'Invalid quantity for "{product.product_name}".'
            )
        resolved.append((line, product))
    return resolved


@transaction.atomic
def place_order(
    *,
    customer: Customers,
    lines: list[OrderLineInput],
    ship_name: str,
    ship_address: str,
    ship_city: str,
    ship_state_province: str = '',
    ship_zip_postal_code: str = '',
    ship_country_region: str = '',
    payment_type: str = '',
    notes: str = '',
    shipper: Shippers | None = None,
    shipping_fee: Decimal = Decimal('0'),
    tax_rate: float = 0.0,
) -> Orders:
    """Create an ``Orders`` row plus the matching ``OrderDetails`` lines.

    Wrapped in ``transaction.atomic`` so a failure mid-insert cannot leave a
    half-built order in the database.
    """
    if customer is None or customer.pk is None:
        raise OrderPlacementError('A customer is required to place an order.')

    resolved = _validate_lines(lines)
    order_status = _resolve_status(OrdersStatus, _NEW_ORDER_STATUS_NAMES)
    detail_status = _resolve_status(OrderDetailsStatus, _NEW_DETAIL_STATUS_NAMES)
    tax_status = _resolve_tax_status()

    order = Orders.objects.create(
        customer=customer,
        order_date=timezone.now(),
        ship_name=ship_name[:50],
        ship_address=ship_address,
        ship_city=ship_city[:50],
        ship_state_province=ship_state_province[:50],
        ship_zip_postal_code=ship_zip_postal_code[:50],
        ship_country_region=ship_country_region[:50],
        shipper=shipper,
        shipping_fee=shipping_fee,
        taxes=Decimal('0'),
        payment_type=payment_type[:50] if payment_type else None,
        notes=notes or None,
        tax_rate=tax_rate,
        tax_status=tax_status,
        status=order_status,
    )

    OrderDetails.objects.bulk_create([
        OrderDetails(
            order=order,
            product=product,
            quantity=Decimal(line.quantity),
            unit_price=Decimal(line.unit_price),
            discount=0.0,
            status=detail_status,
        )
        for line, product in resolved
    ])

    return order


def order_summary(order: Orders) -> dict:
    """Compute totals for an existing order. Used by the confirmation view."""
    lines = list(
        OrderDetails.objects
        .filter(order=order)
        .select_related('product', 'status')
    )
    for ln in lines:
        unit = ln.unit_price or Decimal('0')
        qty = ln.quantity or Decimal('0')
        ln.line_total = (unit * qty).quantize(Decimal('0.01'))
    subtotal = sum((ln.line_total for ln in lines), Decimal('0'))
    shipping = order.shipping_fee or Decimal('0')
    taxes = order.taxes or Decimal('0')
    return {
        'lines': lines,
        'subtotal': subtotal,
        'shipping': shipping,
        'taxes': taxes,
        'total': subtotal + shipping + taxes,
    }
