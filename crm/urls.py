from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
]
