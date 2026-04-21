from django.shortcuts import render
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth

from crm.models import Customers
from sales.models import Orders, OrderDetails
from catalog.models import Products


def report_index(request):
    total_customers = Customers.objects.count()
    total_orders = Orders.objects.count()
    total_products = Products.objects.count()
    total_revenue = (
        OrderDetails.objects
        .aggregate(rev=Sum(F('unit_price') * F('quantity')))['rev']
    ) or 0

    return render(request, 'reporting/report_index.html', {
        'active_nav': 'reports',
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
    })


def top_customers(request):
    customers = list(
        OrderDetails.objects
        .values(
            company=F('order__customer__company'),
            customer_id=F('order__customer__id'),
        )
        .annotate(
            total_orders=Count('order', distinct=True),
            total_revenue=Sum(F('unit_price') * F('quantity')),
        )
        .order_by('-total_revenue')[:20]
    )

    return render(request, 'reporting/top_customers.html', {
        'active_nav': 'reports',
        'customers': customers,
        'chart_labels': [c['company'] or 'Unknown' for c in customers[:10]],
        'chart_data': [float(c['total_revenue'] or 0) for c in customers[:10]],
    })


def top_products(request):
    products = list(
        OrderDetails.objects
        .values(
            product_name=F('product__product_name'),
            product_id=F('product__id'),
        )
        .annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(F('unit_price') * F('quantity')),
        )
        .order_by('-total_revenue')[:20]
    )

    return render(request, 'reporting/top_products.html', {
        'active_nav': 'reports',
        'products': products,
        'chart_labels': [p['product_name'] or 'Unknown' for p in products[:10]],
        'chart_data': [float(p['total_revenue'] or 0) for p in products[:10]],
    })


def sales_trends(request):
    monthly = list(
        Orders.objects
        .filter(order_date__isnull=False)
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(
            order_count=Count('id'),
            revenue=Sum(F('orderdetails__unit_price') * F('orderdetails__quantity')),
        )
        .order_by('month')
    )

    return render(request, 'reporting/sales_trends.html', {
        'active_nav': 'reports',
        'monthly': monthly,
        'chart_labels': [m['month'].strftime('%b %Y') for m in monthly if m['month']],
        'chart_revenue': [float(m['revenue'] or 0) for m in monthly],
        'chart_orders': [m['order_count'] for m in monthly],
    })
