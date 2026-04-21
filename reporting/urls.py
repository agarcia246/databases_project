from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('', views.report_index, name='report_index'),
    path('top-customers/', views.top_customers, name='top_customers'),
    path('top-products/', views.top_products, name='top_products'),
    path('sales-trends/', views.sales_trends, name='sales_trends'),
]
