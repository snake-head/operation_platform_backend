from django.urls import path, include
from rest_framework import routers

from apps.resource.views import ResourceViewSet

router = routers.DefaultRouter()
router.register('resource', ResourceViewSet)

urlpatterns = [
    path('data/', include(router.urls)),
]
