from django.urls import path
from . import views

urlpatterns = [
    path('recaptcha/get/', views.get_recaptcha, name='get_recaptcha'),
    path('recaptcha/verify/', views.verify_recaptcha, name='verify_recaptcha'),
    path('recaptcha/image/<str:image_type>/<str:image_name>', views.get_captcha_image, name='get_captcha_image'),
]