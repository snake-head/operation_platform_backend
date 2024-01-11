# Create your views here.
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from apps.knowledge.models import Knowledge
from utils.paginator import AppPageNumberPagination
from utils.queryset_filter import KnowledgeFilter
from utils.response import JsonResponse
from utils.serializer import KnowledgeSerializer


@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        tags=['知识库相关接口'],
        operation_description="**更新某一条词条记录**"
    )
)
class KnowledgeViewSet(viewsets.ModelViewSet):
    queryset = Knowledge.objects.all().order_by('id')
    serializer_class = KnowledgeSerializer
    pagination_class = AppPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = KnowledgeFilter

    @swagger_auto_schema(
        tags=['知识库相关接口'],
        operation_description='**查询知识库列表**'
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['知识库相关接口'],
        operation_description="**创建一个词条**"
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['知识库相关接口'],
        operation_description="**查询某一个词条**"
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['知识库相关接口'],
        operation_description="**更新某一条词条记录**"
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['知识库相关接口'],
        operation_description="**删除一个词条**"
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return JsonResponse(data=response.data)
