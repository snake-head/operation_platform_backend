from django.shortcuts import render

# Create your views here.
# Create your views here.
import os.path
import uuid

from django.conf import settings
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status

from apps.resource.models import Resource
from utils.paginator import AppPageNumberPagination
from utils.queryset_filter import ResourceFilter
from utils.response import JsonResponse
from utils.serializer import ResourceSerializer

MEDIA_ROOT = settings.MEDIA_ROOT


@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        tags=["课件资源相关接口"],
        operation_summary="获取课件资源记录",
        operation_description="**获取课件资源记录**"
    )
)
class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all().order_by('id')
    serializer_class = ResourceSerializer
    pagination_class = AppPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ResourceFilter

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @swagger_auto_schema(
        tags=["课件资源相关接口"],
        operation_summary="查询多条课件资源记录",
        operation_description="**查询课件资源记录列表**"
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["课件资源相关接口"],
        operation_summary="创建课件资源记录",
        operation_description="**创建一条课件资源记录**"
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["课件资源相关接口"],
        operation_summary="查询课件资源记录",
        operation_description="**查询某一条课件资源记录**"
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["课件资源相关接口"],
        operation_summary="删除课件资源记录",
        operation_description="**删除某一条课件资源记录**"
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return JsonResponse(data=response.data)
