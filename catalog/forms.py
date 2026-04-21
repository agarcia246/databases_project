from django import forms


class ProductSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by product name or code…',
        })
    )
    category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Category',
        })
    )
    discontinued = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('0', 'Active'), ('1', 'Discontinued')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
