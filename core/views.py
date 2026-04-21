from django.shortcuts import render
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncMonth

from crm.models import Customers, Employees
from sales.models import Orders, OrderDetails
from catalog.models import Products


def dashboard(request):
    total_customers = Customers.objects.count()
    total_employees = Employees.objects.count()
    total_orders = Orders.objects.count()
    total_products = Products.objects.count()

    total_revenue = (
        OrderDetails.objects
        .aggregate(rev=Sum(F('unit_price') * F('quantity')))['rev']
    ) or 0

    top_product = (
        OrderDetails.objects
        .values('product__product_name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
        .first()
    )

    recent_orders = (
        Orders.objects
        .select_related('customer', 'employee', 'status')
        .order_by('-order_date')[:10]
    )

    monthly_sales = list(
        Orders.objects
        .filter(order_date__isnull=False)
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(count=Count('id'), revenue=Sum(F('orderdetails__unit_price') * F('orderdetails__quantity')))
        .order_by('month')
    )

    top_customers = list(
        OrderDetails.objects
        .values(name=F('order__customer__company'))
        .annotate(revenue=Sum(F('unit_price') * F('quantity')))
        .order_by('-revenue')[:5]
    )

    employee_performance = list(
        Orders.objects
        .values(name=F('employee__first_name'))
        .annotate(order_count=Count('id'))
        .order_by('-order_count')[:5]
    )

    context = {
        'active_nav': 'dashboard',
        'total_customers': total_customers,
        'total_employees': total_employees,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'top_product': top_product,
        'recent_orders': recent_orders,
        'monthly_sales': monthly_sales,
        'top_customers': top_customers,
        'employee_performance': employee_performance,
    }
    return render(request, 'core/dashboard.html', context)
