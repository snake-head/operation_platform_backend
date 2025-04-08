from django.urls import path
from . import views

urlpatterns = [
    path('recaptcha/get/', views.get_recaptcha, name='get_recaptcha'),
    path('recaptcha/verify/', views.verify_recaptcha, name='verify_recaptcha'),
]