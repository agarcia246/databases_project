"""Tests for back-office sales services.

The core business tables (``products``, ``customers``, ``orders``, ...) are
``managed = False`` because the Northwind schema is shared and not owned by
Django. We rely on mocking ORM hits rather than full integration tests
against those tables.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from .services import OrderLineInput, OrderPlacementError, place_order


def _fake_product(pk: int = 1, *, name: str = 'Earl Grey', price: str = '12.50',
                  discontinued: int = 0, category: str = 'Beverages'):
    return SimpleNamespace(
        pk=pk, id=pk, product_name=name, list_price=Decimal(price),
        discontinued=discontinued, category=category,
        product_code=f'NW-{pk:03d}', description='', quantity_per_unit='',
    )


class PlaceOrderTests(TestCase):
    """``TestCase`` because ``place_order`` opens a transaction on ``default``."""

    databases = {'default'}

    def test_empty_lines_raises(self):
        with self.assertRaises(OrderPlacementError):
            place_order(
                customer=MagicMock(pk=1), lines=[],
                ship_name='Acme', ship_address='1 St', ship_city='Madrid',
            )

    def test_missing_customer_raises(self):
        with self.assertRaises(OrderPlacementError):
            place_order(
                customer=None,
                lines=[OrderLineInput(1, 1, Decimal('1'))],
                ship_name='Acme', ship_address='1 St', ship_city='Madrid',
            )

    @patch('sales.services.OrderDetails')
    @patch('sales.services.Orders.objects')
    @patch('sales.services._resolve_tax_status', return_value=None)
    @patch('sales.services._resolve_status', return_value=None)
    @patch('sales.services.Products.objects')
    def test_happy_path_creates_order_and_lines(
        self, products_mgr, _status, _tax, orders_mgr, order_details_cls,
    ):
        products_mgr.filter.return_value = [
            _fake_product(pk=1, price='10.00'),
            _fake_product(pk=2, price='2.50'),
        ]
        fake_order = MagicMock(pk=42)
        orders_mgr.create.return_value = fake_order

        customer = MagicMock(pk=7)
        order = place_order(
            customer=customer,
            lines=[
                OrderLineInput(1, 2, Decimal('10.00')),
                OrderLineInput(2, 4, Decimal('2.50')),
            ],
            ship_name='Acme', ship_address='1 Plaza Mayor', ship_city='Madrid',
            payment_type='Credit Card',
        )

        self.assertIs(order, fake_order)
        orders_mgr.create.assert_called_once()
        self.assertEqual(order_details_cls.call_count, 2)
        order_details_cls.objects.bulk_create.assert_called_once()
        created = order_details_cls.objects.bulk_create.call_args.args[0]
        self.assertEqual(len(created), 2)

    @patch('sales.services.Products.objects')
    def test_discontinued_product_blocks_order(self, products_mgr):
        products_mgr.filter.return_value = [_fake_product(pk=1, discontinued=1)]
        with self.assertRaises(OrderPlacementError):
            place_order(
                customer=MagicMock(pk=1),
                lines=[OrderLineInput(1, 1, Decimal('1'))],
                ship_name='Acme', ship_address='1 St', ship_city='Madrid',
            )
