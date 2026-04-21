from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    # Browse
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),

    # Checkout & confirmation
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/confirmation/<int:pk>/',
         views.order_confirmation, name='order_confirmation'),

    # My orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),

    # Account
    path('account/', views.account, name='account'),

    # Auth
    path('login/', views.ShopLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
