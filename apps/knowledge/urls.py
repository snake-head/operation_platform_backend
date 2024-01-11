from django.urls import path, include
from rest_framework import routers

from apps.knowledge.views import KnowledgeViewSet

router = routers.DefaultRouter()
router.register('knowledge', KnowledgeViewSet)

urlpatterns = [
    path('data/', include(router.urls)),
]
