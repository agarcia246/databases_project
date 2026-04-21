"""Storefront-side service helpers.

The most non-trivial bit is :func:`register_shop_user`, which has to keep
the Django auth tables (managed) and the Northwind ``customers`` table
(unmanaged) in sync. We do it inside a single ``transaction.atomic`` so a
failure halfway through never leaves an orphan ``User`` or a customer with
no login.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction

from crm.models import Customers

from .models import ShopProfile


User = get_user_model()


class RegistrationError(Exception):
    """Raised when a storefront account cannot be created."""


@transaction.atomic
def register_shop_user(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    company: str = '',
) -> ShopProfile:
    """Create a ``User``, a ``Customers`` row, and a ``ShopProfile`` linking them.

    Email is used as the username so the customer only has to remember one
    identifier. The two writes touch *different* DBs in production (auth →
    MySQL ``auth_user``, customers → MySQL ``customers``) but both go through
    the ``default`` connection so a single transaction is enough.
    """
    email = (email or '').strip().lower()
    if not email or not password:
        raise RegistrationError('Email and password are required.')
    if User.objects.filter(username__iexact=email).exists():
        raise RegistrationError('An account with this email already exists.')

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    customer = Customers.objects.create(
        company=company or f'{first_name} {last_name}'.strip() or email,
        first_name=first_name,
        last_name=last_name,
        email_address=email,
    )

    return ShopProfile.objects.create(user=user, customer_id=customer.pk)


def get_or_create_profile(user) -> ShopProfile:
    """Return the user's ``ShopProfile``, creating a stub customer if missing.

    Useful for users created via ``createsuperuser`` who never went through
    the storefront sign-up flow.
    """
    try:
        return user.shop_profile
    except ShopProfile.DoesNotExist:
        customer = Customers.objects.create(
            company=user.get_full_name() or user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email_address=user.email,
        )
        return ShopProfile.objects.create(user=user, customer_id=customer.pk)
