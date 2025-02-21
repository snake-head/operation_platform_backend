from django.urls import path
from .views import callback

urlpatterns = [
    path('callback/', callback, name='callback'),
]