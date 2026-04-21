from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('invoices/', views.invoice_list, name='invoice_list'),
]
