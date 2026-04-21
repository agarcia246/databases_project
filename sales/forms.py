from django import forms


class OrderSearchForm(forms.Form):
    """Back-office order list search bar."""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by order ID, customer, or employee…',
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    def __init__(self, *args, status_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if status_choices:
            self.fields['status'].choices = [('', 'All Statuses')] + list(status_choices)
