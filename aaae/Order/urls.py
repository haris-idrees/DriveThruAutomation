from django.urls import path
from aaae.Order.views import home, process_speech, OrderConfirmed

urlpatterns = [
    path("", home, name='home'),
    path('process_speech/', process_speech, name='process_speech'),
    path('confirm_order/', OrderConfirmed.as_view(), name='confirm_order'),
]
