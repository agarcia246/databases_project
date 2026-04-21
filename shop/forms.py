"""Forms for the storefront: registration, login, checkout, account update."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from crm.models import Customers


User = get_user_model()

_INPUT = {'class': 'form-control'}
_SELECT = {'class': 'form-select'}

PAYMENT_CHOICES = [
    ('Credit Card', 'Credit Card'),
    ('Debit Card', 'Debit Card'),
    ('PayPal', 'PayPal'),
    ('Wire Transfer', 'Wire Transfer'),
]


# ---------------------------------------------------------------- registration
class RegistrationForm(forms.Form):
    """Sign-up form. Email doubles as username so customers don't need to
    invent a separate handle to log in."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={**_INPUT, 'autocomplete': 'email'}),
    )
    first_name = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={**_INPUT, 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={**_INPUT, 'autocomplete': 'family-name'}),
    )
    company = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={**_INPUT, 'placeholder': 'Optional'}),
    )
    password1 = forms.CharField(
        label='Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={**_INPUT, 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={**_INPUT, 'autocomplete': 'new-password'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') and cleaned.get('password2'):
            if cleaned['password1'] != cleaned['password2']:
                self.add_error('password2', "Passwords don't match.")
        return cleaned


# ---------------------------------------------------------------------- login
class EmailLoginForm(AuthenticationForm):
    """Use email as the username field, with a friendly placeholder."""
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={**_INPUT, 'autocomplete': 'email',
                                       'autofocus': True}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={**_INPUT, 'autocomplete': 'current-password'}),
    )


# ------------------------------------------------------------------- checkout
class CheckoutForm(forms.Form):
    """Shipping + payment fields. The customer is taken from ``request.user``."""

    ship_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs=_INPUT))
    ship_address = forms.CharField(
        widget=forms.Textarea(attrs={**_INPUT, 'rows': 2}),
    )
    ship_city = forms.CharField(max_length=50, widget=forms.TextInput(attrs=_INPUT))
    ship_state_province = forms.CharField(
        max_length=50, required=False, widget=forms.TextInput(attrs=_INPUT),
        label='State / Province',
    )
    ship_zip_postal_code = forms.CharField(
        max_length=50, required=False, widget=forms.TextInput(attrs=_INPUT),
        label='ZIP / Postal code',
    )
    ship_country_region = forms.CharField(
        max_length=50, required=False, widget=forms.TextInput(attrs=_INPUT),
        label='Country / Region',
    )
    payment_type = forms.ChoiceField(
        choices=[('', '— Select payment method —')] + PAYMENT_CHOICES,
        widget=forms.Select(attrs=_SELECT),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**_INPUT, 'rows': 2,
                                     'placeholder': 'Optional delivery notes…'}),
    )

    def clean_ship_name(self):
        return (self.cleaned_data.get('ship_name') or '').strip()

    def clean_ship_address(self):
        return (self.cleaned_data.get('ship_address') or '').strip()


# ----------------------------------------------------------------- account
class AccountForm(forms.ModelForm):
    """Edit the linked ``Customers`` row from the storefront 'Account' page."""

    class Meta:
        model = Customers
        fields = (
            'company', 'first_name', 'last_name', 'email_address',
            'business_phone', 'mobile_phone',
            'address', 'city', 'state_province',
            'zip_postal_code', 'country_region',
        )
        widgets = {
            'address': forms.Textarea(attrs={**_INPUT, 'rows': 2}),
            **{
                f: forms.TextInput(attrs=_INPUT)
                for f in (
                    'company', 'first_name', 'last_name', 'email_address',
                    'business_phone', 'mobile_phone',
                    'city', 'state_province', 'zip_postal_code', 'country_region',
                )
            },
        }
