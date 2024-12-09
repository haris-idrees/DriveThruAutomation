from django.urls import path
from .views import process_recording, PlaceOrder

urlpatterns = [
    path('', PlaceOrder.as_view(), name='take-order'),
    path('process_recording/', process_recording, name='process_recording'),
]
