from django.urls import path
from aaae.Order.views import home, process_speech

urlpatterns = [
    path("", home, name='home'),
    path('process_speech/', process_speech, name='process_speech'),
]
