from django.urls import path
from .views import callback, get_user_info

urlpatterns = [
    path('callback/', callback, name='callback'),
    path('user-info/', get_user_info, name='user_info'),
]