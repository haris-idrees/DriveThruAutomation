from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('aaae.Menu.urls')),
    path('order/', include('aaae.Order.urls')),
]
