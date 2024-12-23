from django.urls import path
from .views import get_pictures

urlpatterns = [
    path('get_pictures/', get_pictures, name='get_pictures'),
]