from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F

from .models import Orders, OrderDetails, OrdersStatus, Invoices
from .forms import OrderSearchForm


def order_list(request):
    status_choices = OrdersStatus.objects.values_list('id', 'status_name')
    form = OrderSearchForm(request.GET, status_choices=status_choices)

    qs = (
        Orders.objects
        .select_related('customer', 'employee', 'status', 'shipper')
        .order_by('-order_date')
    )

    if form.is_valid():
        q = form.cleaned_data.get('q')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if q:
            qs = qs.filter(
                Q(pk__icontains=q) |
                Q(customer__company__icontains=q) |
                Q(employee__first_name__icontains=q) |
                Q(employee__last_name__icontains=q)
            )
        if status:
            qs = qs.filter(status_id=status)
        if date_from:
            qs = qs.filter(order_date__gte=date_from)
        if date_to:
            qs = qs.filter(order_date__lte=date_to)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'sales/order_list.html', {
        'active_nav': 'orders',
        'form': form,
        'page_obj': page_obj,
        'total': paginator.count,
    })


def order_detail(request, pk):
    order = get_object_or_404(
        Orders.objects.select_related('customer', 'employee', 'status', 'shipper', 'tax_status'),
        pk=pk
    )

    line_items = (
        OrderDetails.objects
        .filter(order=order)
        .select_related('product', 'status')
    )

    subtotal = line_items.aggregate(
        total=Sum(F('unit_price') * F('quantity'))
    )['total'] or 0

    invoices = Invoices.objects.filter(order=order)

    return render(request, 'sales/order_detail.html', {
        'active_nav': 'orders',
        'order': order,
        'line_items': line_items,
        'subtotal': subtotal,
        'invoices': invoices,
    })


def invoice_list(request):
    qs = (
        Invoices.objects
        .select_related('order', 'order__customer')
        .order_by('-invoice_date')
    )

    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(
            Q(order__customer__company__icontains=q) |
            Q(pk__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'sales/invoice_list.html', {
        'active_nav': 'invoices',
        'page_obj': page_obj,
        'total': paginator.count,
        'q': q,
    })
