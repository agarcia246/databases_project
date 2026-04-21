"""Tests for the customer-facing storefront.

The Northwind business tables (``products``, ``customers``, ``orders``) are
``managed = False`` so the test runner does not create them. We mock ORM hits
against those tables while exercising the real cart / auth / routing logic.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from .cart import CART_SESSION_KEY, Cart, CartError


User = get_user_model()


# --------------------------------------------------------------------- helpers
def _fake_product(pk: int = 1, *, name: str = 'Earl Grey', price: str = '12.50',
                  discontinued: int = 0, category: str = 'Beverages'):
    return SimpleNamespace(
        pk=pk, id=pk, product_name=name, list_price=Decimal(price),
        discontinued=discontinued, category=category,
        product_code=f'NW-{pk:03d}', description='', quantity_per_unit='',
    )


class _SessionDict(dict):
    modified = False


def _request_with_session():
    request = RequestFactory().get('/')
    request.session = _SessionDict()
    return request


# ============================================================================
#                                   Cart
# ============================================================================
class CartLogicTests(SimpleTestCase):
    def setUp(self):
        self.request = _request_with_session()
        self.cart = Cart(self.request)

    def test_add_then_increment(self):
        product = _fake_product(pk=10, price='5.00')
        self.cart.add(product, 2)
        self.cart.add(product, 3)
        raw = self.request.session[CART_SESSION_KEY]
        self.assertEqual(raw['10']['quantity'], 5)
        self.assertEqual(raw['10']['unit_price'], '5.00')
        self.assertTrue(self.request.session.modified)

    def test_add_rejects_discontinued(self):
        with self.assertRaises(CartError):
            self.cart.add(_fake_product(pk=11, discontinued=1), 1)

    def test_add_rejects_zero_quantity(self):
        with self.assertRaises(CartError):
            self.cart.add(_fake_product(pk=12), 0)

    def test_update_to_zero_removes_line(self):
        self.cart.add(_fake_product(pk=13), 4)
        self.cart.update(13, 0)
        self.assertNotIn('13', self.request.session[CART_SESSION_KEY])

    def test_update_unknown_product_raises(self):
        with self.assertRaises(CartError):
            self.cart.update(999, 1)

    def test_remove_and_clear(self):
        self.cart.add(_fake_product(pk=14), 1)
        self.cart.add(_fake_product(pk=15), 1)
        self.cart.remove(14)
        self.assertEqual(list(self.request.session[CART_SESSION_KEY].keys()), ['15'])
        self.cart.clear()
        self.assertEqual(self.request.session[CART_SESSION_KEY], {})

    def test_quantity_cap_enforced(self):
        product = _fake_product(pk=16)
        self.cart.add(product, 999)
        with self.assertRaises(CartError):
            self.cart.add(product, 1)

    @patch('shop.cart.Products.objects')
    def test_detailed_items_filters_missing_or_discontinued(self, products_mgr):
        products_mgr.filter.return_value = [_fake_product(pk=20, price='3.00')]
        self.request.session[CART_SESSION_KEY] = {
            '20': {'quantity': 2, 'unit_price': '3.00'},
            '21': {'quantity': 1, 'unit_price': '9.00'},
        }
        cart = Cart(self.request)
        items = cart.detailed_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['line_total'], Decimal('6.00'))
        self.assertNotIn('21', self.request.session[CART_SESSION_KEY])

    @patch('shop.cart.Products.objects')
    def test_subtotal_sums_all_lines(self, products_mgr):
        products_mgr.filter.return_value = [
            _fake_product(pk=30, price='4.00'),
            _fake_product(pk=31, price='2.50'),
        ]
        self.request.session[CART_SESSION_KEY] = {
            '30': {'quantity': 3, 'unit_price': '4.00'},
            '31': {'quantity': 2, 'unit_price': '2.50'},
        }
        self.assertEqual(Cart(self.request).subtotal(), Decimal('17.00'))


# ============================================================================
#                         Routing & anonymous access
# ============================================================================
class PublicRoutingTests(TestCase):
    """Anonymous users can browse but not checkout / see orders / account."""

    @patch('shop.views.Products.objects')
    def test_home_renders(self, products_mgr):
        products_mgr.filter.return_value.order_by.return_value = []
        products_mgr.filter.return_value.exclude.return_value.exclude.return_value\
            .values_list.return_value.distinct.return_value.order_by.return_value = []

        response = self.client.get(reverse('shop:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Northwind')

    @patch('shop.views.hydrate_products')
    @patch('shop.views.semantic_search')
    @patch('shop.views.Products.objects')
    def test_semantic_mode_calls_existing_search_service(
        self, products_mgr, semantic_search_mock, hydrate_mock,
    ):
        products_mgr.filter.return_value.exclude.return_value.exclude.return_value\
            .values_list.return_value.distinct.return_value.order_by.return_value = []

        fake_row = SimpleNamespace(
            product=_fake_product(pk=1, name='Iced Tea'),
            similarity=0.87, distance=0.13,
            product_id=1, product_name='Iced Tea', category='Beverages',
        )
        semantic_search_mock.return_value = ['raw-row']
        hydrate_mock.return_value = [fake_row]

        response = self.client.get(
            reverse('shop:home'), {'mode': 'semantic', 'q': 'cold refreshing drinks'},
        )
        self.assertEqual(response.status_code, 200)
        semantic_search_mock.assert_called_once()
        hydrate_mock.assert_called_once_with(['raw-row'])
        self.assertContains(response, 'Iced Tea')

    def test_mutation_endpoints_reject_get(self):
        for name, kwargs in [
            ('shop:cart_add', {'product_id': 1}),
            ('shop:cart_update', {'product_id': 1}),
            ('shop:cart_remove', {'product_id': 1}),
            ('shop:cart_clear', {}),
            ('shop:logout', {}),
        ]:
            response = self.client.get(reverse(name, kwargs=kwargs))
            self.assertEqual(response.status_code, 405, msg=name)

    def test_checkout_requires_login(self):
        response = self.client.get(reverse('shop:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('shop:login'), response['Location'])

    def test_orders_require_login(self):
        response = self.client.get(reverse('shop:order_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('shop:login'), response['Location'])

    def test_account_requires_login(self):
        response = self.client.get(reverse('shop:account'))
        self.assertEqual(response.status_code, 302)


# ============================================================================
#                              Cart view wiring
# ============================================================================
class CartViewTests(TestCase):
    @patch('shop.views.get_object_or_404')
    def test_cart_add_increments_session(self, get_or_404):
        get_or_404.return_value = _fake_product(pk=42, price='7.00')
        response = self.client.post(reverse('shop:cart_add', args=[42]),
                                    {'quantity': 3})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session[CART_SESSION_KEY]['42']['quantity'], 3)

    def test_cart_remove_drops_line(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {'7': {'quantity': 2, 'unit_price': '5.00'}}
        session.save()

        response = self.client.post(reverse('shop:cart_remove', args=[7]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session[CART_SESSION_KEY], {})


# ============================================================================
#                                  Auth
# ============================================================================
class AuthFlowTests(TestCase):
    """Register + login flow. We mock ``Customers.objects.create`` because
    the ``customers`` table is unmanaged and isn't created in the test DB."""

    def test_login_page_renders(self):
        response = self.client.get(reverse('shop:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_register_page_renders(self):
        response = self.client.get(reverse('shop:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create')

    @patch('shop.services.Customers.objects')
    def test_register_creates_user_and_profile(self, customers_mgr):
        # Pretend Customers.objects.create returned a row with pk=99.
        customers_mgr.create.return_value = MagicMock(pk=99)

        response = self.client.post(reverse('shop:register'), {
            'email': 'Alice@Example.com',
            'first_name': 'Alice', 'last_name': 'Jones',
            'company': 'Northwind Fans',
            'password1': 'supersecret123', 'password2': 'supersecret123',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='alice@example.com')
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.shop_profile.customer_id, 99)
        customers_mgr.create.assert_called_once()

    @patch('shop.services.Customers.objects')
    def test_duplicate_email_rejected(self, customers_mgr):
        customers_mgr.create.return_value = MagicMock(pk=10)
        User.objects.create_user(username='bob@example.com', email='bob@example.com',
                                 password='x1')
        response = self.client.post(reverse('shop:register'), {
            'email': 'bob@example.com',
            'first_name': 'Bob', 'last_name': 'X',
            'password1': 'anotherpass123', 'password2': 'anotherpass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_logout_is_post_only(self):
        User.objects.create_user(username='c@example.com', email='c@example.com',
                                 password='pw')
        self.client.login(username='c@example.com', password='pw')
        self.assertEqual(self.client.get(reverse('shop:logout')).status_code, 405)
        response = self.client.post(reverse('shop:logout'))
        self.assertEqual(response.status_code, 302)


# ============================================================================
#                       Logged-in checkout (empty cart path)
# ============================================================================
class CheckoutAccessTests(TestCase):
    """Lightweight checkout test: validates the auth gate + empty-cart redirect
    without triggering the unmanaged Customers/Orders writes that a full
    end-to-end flow would require."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='dana@example.com', email='dana@example.com', password='pw',
        )

    @patch('shop.views.get_or_create_profile')
    def test_empty_cart_redirects_home(self, get_or_create):
        get_or_create.return_value = SimpleNamespace(
            customer_id=1,
            customer=SimpleNamespace(
                pk=1, first_name='Dana', last_name='Doe',
                company='Acme', address='1 St', city='Madrid',
                state_province='', zip_postal_code='', country_region='',
            ),
        )
        self.client.login(username='dana@example.com', password='pw')
        response = self.client.get(reverse('shop:checkout'))
        self.assertRedirects(response, reverse('shop:home'),
                             fetch_redirect_response=False)
