from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, render

from .models import (
    InventoryTransactions,
    InventoryTransactionTypes,
    PurchaseOrderDetails,
    PurchaseOrders,
    PurchaseOrderStatus,
)


def _query_string_without_page(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def purchasing_index(request):
    total_purchase_orders = PurchaseOrders.objects.count()
    total_inventory_events = InventoryTransactions.objects.count()
    outstanding_lines = PurchaseOrderDetails.objects.filter(
        date_received__isnull=True
    ).count()
    received_lines = PurchaseOrderDetails.objects.filter(
        date_received__isnull=False
    ).count()

    recent_purchase_orders = (
        PurchaseOrders.objects
        .select_related('supplier', 'created_by', 'status')
        .order_by('-creation_date', '-pk')[:6]
    )
    recent_inventory = (
        InventoryTransactions.objects
        .select_related(
            'transaction_type',
            'product',
            'purchase_order',
            'customer_order',
        )
        .order_by('-transaction_created_date', '-pk')[:8]
    )

    return render(request, 'purchasing/index.html', {
        'active_nav': 'purchasing',
        'total_purchase_orders': total_purchase_orders,
        'total_inventory_events': total_inventory_events,
        'outstanding_lines': outstanding_lines,
        'received_lines': received_lines,
        'recent_purchase_orders': recent_purchase_orders,
        'recent_inventory': recent_inventory,
    })


def purchase_order_list(request):
    qs = (
        PurchaseOrders.objects
        .select_related('supplier', 'created_by', 'status')
        .order_by('-creation_date', '-expected_date', '-pk')
    )

    q = (request.GET.get('q') or '').strip()
    status_id = (request.GET.get('status') or '').strip()
    supplier_id = (request.GET.get('supplier') or '').strip()

    if q:
        q_filter = (
            Q(supplier__company__icontains=q) |
            Q(notes__icontains=q) |
            Q(payment_method__icontains=q)
        )
        if q.isdigit():
            q_filter |= Q(pk=int(q))
        qs = qs.filter(q_filter)
    if status_id:
        qs = qs.filter(status_id=status_id)
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    supplier_choices = list(
        PurchaseOrders.objects
        .exclude(supplier__isnull=True)
        .values_list('supplier_id', 'supplier__company')
        .distinct()
        .order_by('supplier__company')
    )
    status_choices = PurchaseOrderStatus.objects.order_by('status')

    return render(request, 'purchasing/purchase_order_list.html', {
        'active_nav': 'purchasing',
        'page_obj': page_obj,
        'total': paginator.count,
        'q': q,
        'status_id': status_id,
        'supplier_id': supplier_id,
        'status_choices': status_choices,
        'supplier_choices': supplier_choices,
        'query_string': _query_string_without_page(request),
    })


def purchase_order_detail(request, pk):
    purchase_order = get_object_or_404(
        PurchaseOrders.objects.select_related('supplier', 'created_by', 'status'),
        pk=pk,
    )
    line_items = (
        PurchaseOrderDetails.objects
        .filter(purchase_order=purchase_order)
        .select_related('product', 'inventory')
    )
    for item in line_items:
        item.line_total = (item.quantity or 0) * (item.unit_cost or 0)
    summary = line_items.aggregate(
        subtotal=Sum(F('quantity') * F('unit_cost')),
        total_quantity=Sum('quantity'),
        total_lines=Count('id'),
        received_lines=Count('id', filter=Q(date_received__isnull=False)),
    )
    related_inventory = (
        InventoryTransactions.objects
        .filter(purchase_order=purchase_order)
        .select_related('transaction_type', 'product', 'customer_order')
        .order_by('-transaction_created_date', '-pk')
    )

    return render(request, 'purchasing/purchase_order_detail.html', {
        'active_nav': 'purchasing',
        'purchase_order': purchase_order,
        'line_items': line_items,
        'subtotal': summary['subtotal'] or 0,
        'total_quantity': summary['total_quantity'] or 0,
        'total_lines': summary['total_lines'] or 0,
        'received_lines': summary['received_lines'] or 0,
        'related_inventory': related_inventory,
    })


def inventory_activity(request):
    qs = (
        InventoryTransactions.objects
        .select_related(
            'transaction_type',
            'product',
            'purchase_order',
            'customer_order',
        )
        .order_by('-transaction_created_date', '-pk')
    )

    q = (request.GET.get('q') or '').strip()
    transaction_type_id = (request.GET.get('type') or '').strip()

    if q:
        q_filter = (
            Q(product__product_name__icontains=q) |
            Q(comments__icontains=q)
        )
        if q.isdigit():
            q_filter |= Q(purchase_order__pk=int(q))
            q_filter |= Q(customer_order__pk=int(q))
        qs = qs.filter(q_filter)
    if transaction_type_id:
        qs = qs.filter(transaction_type_id=transaction_type_id)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    transaction_types = InventoryTransactionTypes.objects.order_by('type_name')

    return render(request, 'purchasing/inventory_activity.html', {
        'active_nav': 'inventory',
        'page_obj': page_obj,
        'total': paginator.count,
        'q': q,
        'transaction_type_id': transaction_type_id,
        'transaction_types': transaction_types,
        'query_string': _query_string_without_page(request),
    })
