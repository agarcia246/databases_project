"""Session-backed shopping cart for the storefront.

The cart is stored as a dict of ``{product_id: {"quantity": int, "unit_price":
str}}`` under ``request.session[CART_SESSION_KEY]``. We persist the unit price
captured at the moment the item was added so a later catalog price change does
not silently re-price the cart between page loads. The displayed total is
re-validated on every page render against the live ``Products`` table.

Decimal values are serialised as strings because Django's default JSON session
backend cannot encode :class:`decimal.Decimal`.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable

from catalog.models import Products


CART_SESSION_KEY = 'shop_cart'
MAX_QUANTITY_PER_LINE = 999


class CartError(Exception):
    """Raised when an operation on the cart cannot be performed."""


class Cart:
    """Thin façade over ``request.session`` exposing cart operations."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not isinstance(cart, dict):
            cart = {}
            self.session[CART_SESSION_KEY] = cart
        self._cart = cart

    # ---------------------------------------------------------------- mutators
    def add(self, product: Products, quantity: int = 1) -> None:
        """Add ``quantity`` units of ``product`` (or increment if present)."""
        self._guard_product(product)
        quantity = self._coerce_quantity(quantity)

        key = str(product.pk)
        existing = self._cart.get(key, {})
        try:
            current_qty = int(existing.get('quantity', 0))
        except (TypeError, ValueError):
            current_qty = 0
        new_qty = current_qty + quantity
        if new_qty > MAX_QUANTITY_PER_LINE:
            raise CartError(
                f'Maximum {MAX_QUANTITY_PER_LINE} units per product per order.'
            )

        self._cart[key] = {
            'quantity': new_qty,
            'unit_price': str(product.list_price or Decimal('0')),
        }
        self._touch()

    def update(self, product_id: int, quantity: int) -> None:
        """Set the line quantity. ``quantity == 0`` removes the line."""
        key = str(product_id)
        if key not in self._cart:
            raise CartError('Item is not in your cart.')
        if quantity <= 0:
            self.remove(product_id)
            return

        quantity = self._coerce_quantity(quantity)
        if quantity > MAX_QUANTITY_PER_LINE:
            raise CartError(
                f'Maximum {MAX_QUANTITY_PER_LINE} units per product per order.'
            )
        self._cart[key]['quantity'] = quantity
        self._touch()

    def remove(self, product_id: int) -> None:
        self._cart.pop(str(product_id), None)
        self._touch()

    def clear(self) -> None:
        self._cart.clear()
        self._touch()

    # ---------------------------------------------------------------- queries
    def __len__(self) -> int:
        return sum(int(item.get('quantity', 0)) for item in self._cart.values())

    def __iter__(self) -> Iterable[dict]:
        return iter(self.detailed_items())

    def is_empty(self) -> bool:
        return not self._cart

    def detailed_items(self) -> list[dict]:
        """Return cart lines hydrated with the live ``Products`` row.

        Lines whose product no longer exists or has been discontinued are
        filtered out (and removed from the session) so checkout cannot fail on
        them later. Returned line totals use the *current* list price to keep
        the displayed math honest.
        """
        if not self._cart:
            return []

        ids = [int(pid) for pid in self._cart.keys()]
        products = {p.pk: p for p in Products.objects.filter(pk__in=ids)}

        lines: list[dict] = []
        invalid_keys: list[str] = []
        for key, raw in self._cart.items():
            product = products.get(int(key))
            if product is None or product.discontinued:
                invalid_keys.append(key)
                continue
            quantity = self._coerce_quantity(raw.get('quantity', 0))
            unit_price = self._coerce_price(
                raw.get('unit_price') or product.list_price or 0
            )
            lines.append({
                'product': product,
                'product_id': product.pk,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': (unit_price * quantity).quantize(Decimal('0.01')),
            })

        if invalid_keys:
            for key in invalid_keys:
                self._cart.pop(key, None)
            self._touch()

        return lines

    def subtotal(self) -> Decimal:
        return sum(
            (line['line_total'] for line in self.detailed_items()),
            Decimal('0.00'),
        )

    # ------------------------------------------------------------- internals
    def _touch(self) -> None:
        self.session[CART_SESSION_KEY] = self._cart
        self.session.modified = True

    @staticmethod
    def _coerce_quantity(value) -> int:
        try:
            qty = int(value)
        except (TypeError, ValueError):
            raise CartError('Quantity must be a whole number.')
        if qty < 1:
            raise CartError('Quantity must be at least 1.')
        return qty

    @staticmethod
    def _coerce_price(value) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            return Decimal('0')

    @staticmethod
    def _guard_product(product: Products) -> None:
        if product is None or product.pk is None:
            raise CartError('Unknown product.')
        if product.discontinued:
            raise CartError(f'"{product.product_name}" has been discontinued.')
