from django.urls import path

from . import views

app_name = 'purchasing'

urlpatterns = [
    path('', views.purchasing_index, name='index'),
    path('orders/', views.purchase_order_list, name='purchase_order_list'),
    path('orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('inventory/', views.inventory_activity, name='inventory_activity'),
]
