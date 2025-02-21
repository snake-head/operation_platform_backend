"""operation_platform_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include, re_path
from django.contrib import admin
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls

from apps.course.urls import urlpatterns as course_urls
from apps.department.urls import urlpatterns as department_urls
from apps.privilege.urls import urlpatterns as privilege_urls
from apps.user.urls import urlpatterns as user_urls
from apps.video.urls import urlpatterns as video_urls
from apps.knowledge.urls import urlpatterns as knowledge_urls
from apps.resource.urls import urlpatterns as resource_urls
from apps.generatepicture.urls import urlpatterns as generatepicture_urls
from apps.login.urls import urlpatterns as login_urls
from utils.exception_handler import http404handler, http500handler

API_PREFIX = 'api/v1/'

schema_view = get_schema_view(
    openapi.Info(
        title="手术视频示教平台API文档",
        default_version='v1',
        description="此处描述了目前平台中可用的后端接口",
        contact=openapi.Contact(email="showenshi@foxmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path(API_PREFIX, include(video_urls)),
    path(API_PREFIX, include(user_urls)),
    path(API_PREFIX, include(privilege_urls)),
    path(API_PREFIX, include(course_urls)),
    path(API_PREFIX, include(department_urls)),
    path(API_PREFIX, include(knowledge_urls)),
    path(API_PREFIX, include(resource_urls)),
    path(API_PREFIX, include(generatepicture_urls)),
    path('', include(login_urls)),
    # 以下是几种不同的接口文档页面，可以选择一个最舒适的进行阅读
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^docs/', include_docs_urls(title='手术视频示教平台API文档'))
]

handler404 = http404handler
handler500 = http500handler
