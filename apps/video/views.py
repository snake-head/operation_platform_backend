# Create your views here.
import os.path
import uuid

from django.conf import settings
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request

from apps.video.models import Video, StatusEnum
from apps.video.service import VideoUploadService
from utils.paginator import AppPageNumberPagination
from utils.queryset_filter import VideoFilter
from utils.response import JsonResponse
from utils.serializer import VideoSerializer

from apps.video import tasks

MEDIA_ROOT = settings.MEDIA_ROOT


@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="部分更新手术视频记录",
        operation_description="**更新某一条手术视频记录**"
    )
)
class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all().order_by('id')
    serializer_class = VideoSerializer
    pagination_class = AppPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = VideoFilter

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_upload_service = VideoUploadService()

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="查询多条手术视频记录",
        operation_description="**查询手术视频记录列表**"
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="创建手术视频记录",
        operation_description="**创建一条手术视频记录**"
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="查询手术视频记录",
        operation_description="**查询某一条手术视频记录**"
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="完全更新手术视频记录",
        operation_description="**更新某一条手术视频记录**"
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="删除手术视频记录",
        operation_description="**删除某一条手术视频记录**"
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="上传手术视频分片",
        operation_description="**上传一小段手术视频的分段文件**",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['chunk', 'fileHash', 'fileExt', 'chunkName'],
            properties={
                'chunk': openapi.Schema(type=openapi.TYPE_FILE, description="视频分片文件"),
                'fileHash': openapi.Schema(type=openapi.TYPE_STRING,
                                           description="手术视频文件计算得到的哈希值，用于区分不同的视频",
                                           default='b4cd45e94e80e13c7407d87ad3d5358e'),
                'fileExt': openapi.Schema(type=openapi.TYPE_STRING, description="手术视频文件的扩展名，如.mp4",
                                          default='.mp4'),
                'chunkName': openapi.Schema(type=openapi.TYPE_STRING,
                                            description="分片文件的名称，以`-`分隔，前半部分为`fileHash`，后半部分为本切片在整个视频中所处的位置序号",
                                            default="b4cd45e94e80e13c7407d87ad3d5358e-1")
            }
        ),
        responses={
            200: openapi.Response(
                description='ok',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'code': openapi.Schema(type=openapi.TYPE_NUMBER, default=200),
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, default='成功'),
                        'data': openapi.Schema(type=openapi.TYPE_STRING, default='')
                    }
                )
            )
        },
    )
    @action(methods=['post'], detail=False, url_path='uploadChunk')
    def upload_chunk(self, request: Request, *args, **kwargs):
        chunk = request.FILES.get('chunk')
        file_hash = request.data.get('fileHash')
        file_ext = request.data.get('fileExt')
        chunk_name = request.data.get('chunkName')

        self.video_upload_service.upload_file_chunk(chunk, chunk_name, file_hash, file_ext)

        return JsonResponse()

    # noinspection PyTypeChecker
    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="合并手术视频分片",
        operation_description="**将之前上传的手术视频分段合并为完整的手术视频，并进行去雾、转码等操作**",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['fileHash', 'fileExt', 'fileName'],
            properties={
                'fileHash': openapi.Schema(type=openapi.TYPE_STRING,
                                           description="手术视频文件计算得到的哈希值，用于区分不同的视频",
                                           default='b4cd45e94e80e13c7407d87ad3d5358e'),
                'fileExt': openapi.Schema(type=openapi.TYPE_STRING, description="手术视频文件的扩展名，如.mp4",
                                          default='.mp4'),
                'fileName': openapi.Schema(type=openapi.TYPE_STRING,
                                           description="手术视频文件的名称",
                                           default="video01.mp4")
            }
        ),
        responses={
            200: VideoSerializer
        }
    )
    @action(methods=['post'], detail=False, url_path='mergeChunk')
    def merge_chunk(self, request: Request, *args, **kwargs):
        file_hash = request.data.get('fileHash')
        file_ext = request.data.get('fileExt')
        file_name = request.data.get('fileName')
        course_id = request.data.get('courseId')

        origin_path = self.video_upload_service.merge_file_chunk(file_hash, file_ext)
        target_path = self.video_upload_service.move_to_db_dictionary(origin_path)
        mpd_path = self.video_upload_service.generate_mpd_path(target_path, file_hash)
        poster_path = self.video_upload_service.generate_poster_path(target_path, file_hash)
        video_id = f'vid_{file_hash}_{uuid.uuid4().hex[:8]}'
        video_data = {
            "videoId": video_id,
            "videoName": file_name,
            "videoUrl": os.path.relpath(mpd_path, MEDIA_ROOT),
            "coverImgUrl": os.path.relpath(poster_path, MEDIA_ROOT),
            "courseId": course_id,
            "status": StatusEnum.PROCESSING.value
        }
        serializer = self.get_serializer(data=video_data)
        serializer.is_valid(raise_exception=True)
        # step0 为视频生成首帧封面
        self.video_upload_service.generate_video_poster(target_path, poster_path)
        # 先更新数据库，再视频后处理
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # self.video_upload_service.video_process(target_path, mpd_path, poster_path, video_id, self)
        tasks.video_process(target_path, mpd_path, video_id)
        return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="验证手术视频分片",
        operation_description="**验证服务端是否存在尚未进行合并的手术视频分片**",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['fileHash', 'fileExt'],
            properties={
                'fileHash': openapi.Schema(type=openapi.TYPE_STRING,
                                           description="手术视频文件计算得到的哈希值，用于区分不同的视频",
                                           default='b4cd45e94e80e13c7407d87ad3d5358e'),
                'fileExt': openapi.Schema(type=openapi.TYPE_STRING, description="手术视频文件的扩展名，如.mp4",
                                          default='.mp4')
            }
        ),
        responses={
            200: openapi.Response(
                description='ok',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'code': openapi.Schema(type=openapi.TYPE_NUMBER, default=200),
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, default='成功'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            'shouldUpload': openapi.Schema(
                                type=openapi.TYPE_BOOLEAN,
                                default=True,
                                description='秒传时判断此视频文件是否已在服务器存在，从而决定是否继续上传'),
                            'uploadedList': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING, default='chunk-1'),
                                description='此视频文件已在服务器存在的部分切片，客户端应当上传其余的切片')
                        })
                    }
                )
            )
        },
    )
    @action(methods=['post'], detail=False, url_path='verifyUpload')
    def verify_upload(self, request: Request, *args, **kwargs):
        file_hash = request.data.get('fileHash')
        file_ext = request.data.get('fileExt')
        res = self.video_upload_service.verify_should_upload(file_hash, file_ext)
        return JsonResponse(data=res)



