"""Storefront views.

The storefront is a self-contained, customer-facing web app at ``/shop/``.
It has its own base template (no CRM sidebar) and requires a customer to log
in before checking out or viewing past orders. Browsing and search are public
so search engines and curious visitors can still see the catalog.
"""
from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from catalog.models import Products
from sales.models import OrderDetails, Orders
from sales.services import (
    OrderLineInput,
    OrderPlacementError,
    order_summary,
    place_order,
)
from search.services import hydrate_products, semantic_search

from .cart import CART_SESSION_KEY, Cart, CartError  # noqa: F401  (re-export)
from .forms import AccountForm, CheckoutForm, EmailLoginForm, RegistrationForm
from .services import RegistrationError, get_or_create_profile, register_shop_user


PRODUCT_PAGE_SIZE = 12
SEMANTIC_RESULT_K = 12


# ============================================================================
#                                  Browsing
# ============================================================================
def home(request):
    """Storefront landing page: discovery, search, semantic search."""
    cart = Cart(request)
    mode = request.GET.get('mode', 'keyword')
    q = (request.GET.get('q') or '').strip()
    category = (request.GET.get('category') or '').strip()

    semantic_results = []
    page_obj = None

    if mode == 'semantic' and q:
        try:
            semantic_results = hydrate_products(
                semantic_search(q, k=SEMANTIC_RESULT_K)
            )
        except Exception as exc:
            messages.warning(
                request,
                f'Smart search is temporarily unavailable ({exc.__class__.__name__}).'
            )
    else:
        qs = Products.objects.filter(discontinued=0).order_by('product_name')
        if q:
            qs = qs.filter(
                Q(product_name__icontains=q) | Q(product_code__icontains=q)
            )
        if category:
            qs = qs.filter(category__icontains=category)
        page_obj = Paginator(qs, PRODUCT_PAGE_SIZE).get_page(request.GET.get('page'))

    categories = (
        Products.objects
        .filter(discontinued=0)
        .exclude(category__isnull=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    return render(request, 'shop/home.html', {
        'active_nav': 'home',
        'mode': mode,
        'q': q,
        'category': category,
        'categories': list(categories),
        'page_obj': page_obj,
        'semantic_results': semantic_results,
        'cart_count': len(cart),
    })


def product_detail(request, pk: int):
    product = get_object_or_404(Products, pk=pk, discontinued=0)
    cart = Cart(request)

    related = []
    try:
        from search.services import similar_products
        related = hydrate_products(similar_products(product.pk, k=4))
    except Exception:
        related = []

    return render(request, 'shop/product_detail.html', {
        'active_nav': 'home',
        'product': product,
        'related': [r for r in related if getattr(r, 'product', None)],
        'cart_count': len(cart),
    })


# ============================================================================
#                                    Cart
# ============================================================================
def cart_detail(request):
    cart = Cart(request)
    items = cart.detailed_items()
    return render(request, 'shop/cart.html', {
        'active_nav': 'cart',
        'items': items,
        'subtotal': cart.subtotal(),
        'cart_count': len(cart),
    })


def _safe_redirect(request, fallback: str):
    nxt = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if nxt and nxt.startswith('/'):
        return HttpResponseRedirect(nxt)
    return redirect(fallback)


@require_POST
def cart_add(request, product_id: int):
    cart = Cart(request)
    product = get_object_or_404(Products, pk=product_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    try:
        cart.add(product, quantity)
        messages.success(request, f'Added "{product.product_name}" to your cart.')
    except CartError as exc:
        messages.error(request, str(exc))
    return _safe_redirect(request, 'shop:cart')


@require_POST
def cart_update(request, product_id: int):
    cart = Cart(request)
    try:
        quantity = int(request.POST.get('quantity', 0))
    except (TypeError, ValueError):
        messages.error(request, 'Quantity must be a whole number.')
        return redirect('shop:cart')
    try:
        cart.update(product_id, quantity)
        if quantity <= 0:
            messages.info(request, 'Item removed from cart.')
        else:
            messages.success(request, 'Cart updated.')
    except CartError as exc:
        messages.error(request, str(exc))
    return redirect('shop:cart')


@require_POST
def cart_remove(request, product_id: int):
    Cart(request).remove(product_id)
    messages.info(request, 'Item removed from cart.')
    return redirect('shop:cart')


@require_POST
def cart_clear(request):
    Cart(request).clear()
    messages.info(request, 'Cart cleared.')
    return redirect('shop:cart')


# ============================================================================
#                                  Checkout
# ============================================================================
@login_required
def checkout(request):
    cart = Cart(request)
    items = cart.detailed_items()
    subtotal = cart.subtotal()

    if not items:
        messages.warning(request, 'Your cart is empty — add a product first.')
        return redirect('shop:home')

    profile = get_or_create_profile(request.user)
    customer = profile.customer
    if customer is None:
        messages.error(
            request,
            'Your account is missing a customer record. Please contact support.',
        )
        return redirect('shop:account')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            lines = [
                OrderLineInput(
                    product_id=line['product_id'],
                    quantity=line['quantity'],
                    unit_price=line['unit_price'],
                )
                for line in items
            ]
            try:
                order = place_order(
                    customer=customer,
                    lines=lines,
                    ship_name=data['ship_name'],
                    ship_address=data['ship_address'],
                    ship_city=data['ship_city'],
                    ship_state_province=data['ship_state_province'],
                    ship_zip_postal_code=data['ship_zip_postal_code'],
                    ship_country_region=data['ship_country_region'],
                    payment_type=data['payment_type'],
                    notes=data['notes'],
                    shipping_fee=Decimal('0'),
                    tax_rate=0.0,
                )
            except OrderPlacementError as exc:
                messages.error(request, str(exc))
            else:
                cart.clear()
                messages.success(request, f'Order #{order.pk} placed successfully.')
                return redirect(reverse('shop:order_confirmation',
                                        args=[order.pk]))
    else:
        form = CheckoutForm(initial=_initial_from_customer(customer))

    return render(request, 'shop/checkout.html', {
        'active_nav': 'checkout',
        'form': form,
        'items': items,
        'subtotal': subtotal,
        'cart_count': len(cart),
        'customer': customer,
    })


def _initial_from_customer(customer) -> dict:
    """Pre-fill the shipping form with the customer's saved address."""
    full_name = ' '.join(filter(None, [customer.first_name, customer.last_name]))
    return {
        'ship_name': customer.company or full_name or '',
        'ship_address': customer.address or '',
        'ship_city': customer.city or '',
        'ship_state_province': customer.state_province or '',
        'ship_zip_postal_code': customer.zip_postal_code or '',
        'ship_country_region': customer.country_region or '',
        'payment_type': 'Credit Card',
    }


@login_required
def order_confirmation(request, pk: int):
    order = _get_user_order_or_404(request, pk)
    summary = order_summary(order)
    return render(request, 'shop/confirmation.html', {
        'active_nav': 'orders',
        'order': order,
        'lines': summary['lines'],
        'subtotal': summary['subtotal'],
        'shipping': summary['shipping'],
        'taxes': summary['taxes'],
        'total': summary['total'],
        'cart_count': len(Cart(request)),
    })


# ============================================================================
#                                  My Orders
# ============================================================================
@login_required
def order_list(request):
    profile = get_or_create_profile(request.user)
    qs = (
        Orders.objects
        .filter(customer_id=profile.customer_id)
        .select_related('status', 'shipper')
        .order_by('-order_date')
    )
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'shop/order_list.html', {
        'active_nav': 'orders',
        'page_obj': page_obj,
        'total': paginator.count,
        'cart_count': len(Cart(request)),
    })


@login_required
def order_detail(request, pk: int):
    order = _get_user_order_or_404(request, pk)
    summary = order_summary(order)
    return render(request, 'shop/order_detail.html', {
        'active_nav': 'orders',
        'order': order,
        'lines': summary['lines'],
        'subtotal': summary['subtotal'],
        'shipping': summary['shipping'],
        'taxes': summary['taxes'],
        'total': summary['total'],
        'cart_count': len(Cart(request)),
    })


def _get_user_order_or_404(request, pk: int) -> Orders:
    """Lookup an order, refusing to leak orders that belong to other users."""
    profile = get_or_create_profile(request.user)
    return get_object_or_404(
        Orders.objects.select_related('customer', 'status', 'shipper'),
        pk=pk, customer_id=profile.customer_id,
    )


# ============================================================================
#                                   Account
# ============================================================================
@login_required
def account(request):
    profile = get_or_create_profile(request.user)
    customer = profile.customer
    if customer is None:
        messages.error(request, 'Your account is missing a customer record.')
        return redirect('shop:home')

    if request.method == 'POST':
        form = AccountForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account details updated.')
            return redirect('shop:account')
    else:
        form = AccountForm(instance=customer)

    return render(request, 'shop/account.html', {
        'active_nav': 'account',
        'form': form,
        'customer': customer,
        'cart_count': len(Cart(request)),
    })


# ============================================================================
#                                Authentication
# ============================================================================
class ShopLoginView(LoginView):
    template_name = 'shop/auth/login.html'
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        nxt = self.request.GET.get('next') or self.request.POST.get('next')
        if nxt and nxt.startswith('/'):
            return nxt
        return reverse_lazy('shop:home')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cart_count'] = len(Cart(self.request))
        ctx['active_nav'] = 'login'
        return ctx


def register(request):
    if request.user.is_authenticated:
        return redirect('shop:home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                profile = register_shop_user(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    company=form.cleaned_data.get('company', ''),
                )
            except RegistrationError as exc:
                messages.error(request, str(exc))
            else:
                auth_login(request, profile.user)
                messages.success(request, 'Welcome to Northwind! Your account is ready.')
                return redirect('shop:home')
    else:
        form = RegistrationForm()

    return render(request, 'shop/auth/register.html', {
        'form': form,
        'active_nav': 'register',
        'cart_count': len(Cart(request)),
    })


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('shop:home')
