from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Count, Sum, F

from .models import Customers, Employees, Suppliers
from .forms import CustomerSearchForm, CustomerNoteForm, EmployeeSearchForm, SupplierSearchForm
from sales.models import Orders, OrderDetails


def customer_list(request):
    form = CustomerSearchForm(request.GET)
    qs = Customers.objects.all().order_by('company', 'last_name')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        city = form.cleaned_data.get('city')
        country = form.cleaned_data.get('country')
        if q:
            qs = qs.filter(
                Q(company__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email_address__icontains=q)
            )
        if city:
            qs = qs.filter(city__icontains=city)
        if country:
            qs = qs.filter(country_region__icontains=country)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/customer_list.html', {
        'active_nav': 'customers',
        'form': form,
        'page_obj': page_obj,
        'total': paginator.count,
    })


def customer_detail(request, pk):
    customer = get_object_or_404(Customers, pk=pk)

    if request.method == 'POST':
        note_form = CustomerNoteForm(request.POST)
        if note_form.is_valid():
            existing = customer.notes or ''
            separator = '\n---\n' if existing else ''
            customer.notes = existing + separator + note_form.cleaned_data['notes']
            customer.save()
            messages.success(request, 'Note added successfully.')
            return redirect('crm:customer_detail', pk=pk)
    else:
        note_form = CustomerNoteForm()

    recent_orders = (
        Orders.objects
        .filter(customer=customer)
        .select_related('status', 'employee')
        .order_by('-order_date')[:10]
    )

    order_stats = (
        OrderDetails.objects
        .filter(order__customer=customer)
        .aggregate(
            total_orders=Count('order', distinct=True),
            total_spent=Sum(F('unit_price') * F('quantity'))
        )
    )

    return render(request, 'crm/customer_detail.html', {
        'active_nav': 'customers',
        'customer': customer,
        'note_form': note_form,
        'recent_orders': recent_orders,
        'order_stats': order_stats,
    })


def employee_list(request):
    form = EmployeeSearchForm(request.GET)
    qs = Employees.objects.all().order_by('last_name')

    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(job_title__icontains=q)
        )

    employees = qs.annotate(order_count=Count('orders'))
    paginator = Paginator(employees, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/employee_list.html', {
        'active_nav': 'employees',
        'form': form,
        'page_obj': page_obj,
        'total': paginator.count,
    })


def employee_detail(request, pk):
    employee = get_object_or_404(Employees, pk=pk)

    recent_orders = (
        Orders.objects
        .filter(employee=employee)
        .select_related('customer', 'status')
        .order_by('-order_date')[:10]
    )

    order_stats = (
        Orders.objects
        .filter(employee=employee)
        .aggregate(total_orders=Count('id'))
    )

    return render(request, 'crm/employee_detail.html', {
        'active_nav': 'employees',
        'employee': employee,
        'recent_orders': recent_orders,
        'order_stats': order_stats,
    })


def supplier_list(request):
    form = SupplierSearchForm(request.GET)
    qs = Suppliers.objects.all().order_by('company')

    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(
            Q(company__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'crm/supplier_list.html', {
        'active_nav': 'suppliers',
        'form': form,
        'page_obj': page_obj,
        'total': paginator.count,
    })
