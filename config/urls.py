from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('crm/', include('crm.urls')),
    path('sales/', include('sales.urls')),
    path('purchasing/', include('purchasing.urls')),
    path('catalog/', include('catalog.urls')),
    path('reports/', include('reporting.urls')),
    path('search/', include('search.urls')),
    path('shop/', include('shop.urls')),
]
