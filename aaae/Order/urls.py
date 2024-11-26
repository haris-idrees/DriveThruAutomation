from django.urls import path
from aaae.Order.views import Orders, OrderDetail, process_speech, OrderConfirmed, TakeOrder

urlpatterns = [
    path("", Orders.as_view(), name='home'),
    path('orders/<int:order_id>/', OrderDetail.as_view(), name='order_detail'),
    path('process_speech/', process_speech, name='process_speech'),
    path('take_order/', TakeOrder.as_view(),name='take_order'),
    path('confirm_order/', OrderConfirmed.as_view(), name='confirm_order'),
]
