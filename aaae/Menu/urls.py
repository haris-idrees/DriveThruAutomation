from django.urls import path
from aaae.Menu.views import upload_menu, menu_list, menu_detail

urlpatterns = [
    path("", upload_menu, name='upload-menu'),
    path('menu/', menu_list, name='menu_list.css'),
    path('menu/<int:pk>/', menu_detail, name='menu_detail'),
]
