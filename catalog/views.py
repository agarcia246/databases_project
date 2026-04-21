from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F

from .models import Products
from .forms import ProductSearchForm
from sales.models import OrderDetails


def product_list(request):
    form = ProductSearchForm(request.GET)
    qs = Products.objects.all().order_by('product_name')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        discontinued = form.cleaned_data.get('discontinued')

        if q:
            qs = qs.filter(
                Q(product_name__icontains=q) |
                Q(product_code__icontains=q)
            )
        if category:
            qs = qs.filter(category__icontains=category)
        if discontinued:
            qs = qs.filter(discontinued=int(discontinued))

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'catalog/product_list.html', {
        'active_nav': 'products',
        'form': form,
        'page_obj': page_obj,
        'total': paginator.count,
    })


def product_detail(request, pk):
    product = get_object_or_404(Products, pk=pk)

    sales_stats = (
        OrderDetails.objects
        .filter(product=product)
        .aggregate(
            total_orders=Sum('quantity'),
            total_revenue=Sum(F('unit_price') * F('quantity'))
        )
    )

    recent_orders = (
        OrderDetails.objects
        .filter(product=product)
        .select_related('order', 'order__customer', 'status')
        .order_by('-order__order_date')[:10]
    )

    return render(request, 'catalog/product_detail.html', {
        'active_nav': 'products',
        'product': product,
        'sales_stats': sales_stats,
        'recent_orders': recent_orders,
    })
