# Create your views here.
import base64
import os.path
import subprocess
import uuid

from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models.functions import TruncDate
from django.db.models.expressions import RawSQL
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters
from django.core.cache import cache
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
from openai import OpenAI

from apps.video import tasks

MEDIA_ROOT = settings.MEDIA_ROOT

client = OpenAI(
    api_key=os.environ.get("API_KEY", "0"),
    base_url=f"http://qwen-service:{os.environ.get('API_PORT', 8000)}/v1"
)


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

    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_json_response(self, data):
        """返回标准格式的JSON响应"""
        return JsonResponse({
            'success': True,
            'code': 200,
            'msg': '成功',
            'data': data
        })
    def format_duration(self, seconds):
        """将秒数转换为时分秒格式"""
        if seconds is None:
            return "0秒"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"
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

    # Create a function to handle the POST request
    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="提取视频帧并发送给OpenAI模型",
        operation_description="**根据视频ID和播放时间提取视频帧，转为base64格式，并发送至OpenAI进行处理**",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['video_id', 'play_time'],
            properties={
                'video_id': openapi.Schema(type=openapi.TYPE_INTEGER,
                                           description="视频ID"),
                'play_time': openapi.Schema(type=openapi.TYPE_NUMBER,
                                            description="提取视频帧的播放时间（秒）"),
            },
        ),
    )
    @action(detail=False, methods=['post'], url_path='getCaption')
    def get_caption(self, request, *args, **kwargs):
        video_id = request.data.get('video_id')
        play_time = request.data.get('play_time')
        temperature = request.data.get('temperature', 0)  # 从request中获取temperature,默认为0

        # Check if video exists
        try:
            video = Video.objects.get(videoId=video_id)
        except Video.DoesNotExist:
            return JsonResponse({"error": "Video not found"},
                                status=status.HTTP_404_NOT_FOUND)

        # Get the file path of the video
        video_url = video.coverImgUrl.replace('poster.png', '640x360.mp4')
        video_file_path = os.path.join(settings.MEDIA_ROOT, video_url)

        # Generate a unique filename for the extracted frame
        output_image_path = f"{str(uuid.uuid4())}.jpg"

        # Use ffmpeg to extract the frame at the specified play_time
        if 0 < float(play_time) < 10:
            play_time = 10
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-ss", str(play_time),
                    "-i", video_file_path,
                    "-vframes", "1",
                    "-q:v", "2",  # Highest quality JPEG
                    output_image_path
                ],
                check=True
            )
        except subprocess.CalledProcessError:
            return JsonResponse(
                {"error": "Failed to extract frame from video"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Read the image and convert it to base64
        with open(output_image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')

        # Remove the temporary image file
        os.remove(output_image_path)

        # Send the base64 image to OpenAI

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please describe this image"},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"}},
                ]
            }
        ]

        result = client.chat.completions.create(
            messages=messages,
            model="test",
            temperature=temperature  # 使用从request获取的temperature值
        )

        # Return the response from OpenAI
        return JsonResponse(
            {"description": result.choices[0].message.content})

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="记录视频播放量",
        operation_description="**记录视频被播放的次数**",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['videoId'],
            properties={
                'videoId': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="视频ID",
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description='成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'code': openapi.Schema(type=openapi.TYPE_NUMBER, default=200),
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, default='成功'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT, 
                            properties={
                                'view_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='当前播放量')
                            }
                        )
                    }
                )
            ),
            404: openapi.Response(description='视频不存在')
        }
    )
    @action(detail=False, methods=['post'], url_path='record-view')
    def record_view(self, request, *args, **kwargs):
        """记录视频播放量"""
        video_id = request.data.get('videoId')
        user_id = request.user.id if request.user.is_authenticated else None
        client_ip = self.get_client_ip(request)
        
        if not video_id:
            return JsonResponse({'error': '缺少videoId参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取视频对象
            video = Video.objects.get(videoId=video_id)
            
            # 创建唯一键，基于视频ID、用户ID和IP地址
            cache_key = f"video_view:{video_id}:{user_id or ''}:{client_ip}"
            
            # 检查缓存中是否存在该键（30分钟内同一用户/IP不重复计数）
            if not cache.get(cache_key):
                # 增加播放量
                video.view_count += 1
                video.save(update_fields=['view_count'])
                
                # 设置缓存，30分钟内不再重复计数
                cache.set(cache_key, True, 60 * 30)  # 30分钟过期
            
            return JsonResponse({
                'data': {
                    'view_count': video.view_count
                }
            })
        
        except Video.DoesNotExist:
            return JsonResponse({
                'error': '视频不存在'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="记录视频观看时长",
        operation_description="**记录用户观看视频的时长**",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['videoId', 'duration'],
            properties={
                'videoId': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="视频ID",
                ),
                'duration': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="观看时长(秒)",
                ),
                'isEnded': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="是否看完视频",
                    default=False,
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description='成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'code': openapi.Schema(type=openapi.TYPE_NUMBER, default=200),
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, default='成功'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT, 
                            properties={
                                'total_duration': openapi.Schema(type=openapi.TYPE_INTEGER, description='用户累计观看时长(秒)'),
                                'session_id': openapi.Schema(type=openapi.TYPE_STRING, description='会话ID')
                            }
                        )
                    }
                )
            ),
            404: openapi.Response(description='视频不存在')
        }
    )
    @action(detail=False, methods=['post'], url_path='record-watch-time')
    def record_watch_time(self, request, *args, **kwargs):
        """记录视频观看时长"""
        from apps.video.models import VideoWatchRecord
        import uuid
        
        video_id = request.data.get('videoId')
        duration = request.data.get('duration')
        is_ended = request.data.get('isEnded', False)
        force_update_end_status = request.data.get('forceUpdateEndStatus', False) 
        
        # 从请求参数中获取 openid
        param_openid = request.data.get('openid')
        
        if not video_id or duration is None:
            return JsonResponse({
                'error': '缺少必要参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取视频对象
            video = Video.objects.get(videoId=video_id)  # 确保使用 videoId 字段获取视频对象
            
            # 获取用户信息 - 优先使用请求参数中的 openid
            openid = param_openid  # 首先尝试从请求参数获取
            
            # 如果请求参数中没有 openid，尝试从其他来源获取
            if not openid and request.user.is_authenticated:
                openid = request.COOKIES.get('openid') or getattr(request.user, 'openid', None)
            
            client_ip = self.get_client_ip(request)
            
            # 获取或创建会话ID (从cookie或创建新的)
            session_id = request.COOKIES.get('video_session_id')
            is_new_session = False
            
            if not session_id:
                session_id = f"session_{uuid.uuid4().hex[:16]}"
                is_new_session = True
            
            # 修改：根据 openid 和 video 查找记录，不再使用 session_id 作为条件
            if openid:
                # 已登录用户，根据 openid 和 video 查找记录
                watch_record, created = VideoWatchRecord.objects.get_or_create(
                    openid=openid, 
                    course_ID=video.courseId,  
                    video=video,  # 直接传递整个 video 对象，处理外键关系
                    defaults={
                        'course_ID': video.courseId,  
                        'duration': duration,
                        'is_ended': is_ended,
                        'ip_address': client_ip,
                        'session_id': session_id  # 仍然记录会话ID，但不作为查询条件
                    }
                )
            else:
                # 未登录用户，根据IP地址和会话ID查找记录
                watch_record, created = VideoWatchRecord.objects.get_or_create(
                    video=video,
                    ip_address=client_ip,
                    session_id=session_id,  # 匿名用户仍然使用会话ID区分
                    defaults={
                        'duration': duration,
                        'is_ended': is_ended
                    }
                )
            
            if not created:
                # 记录视频结束尝试次数，便于调试
                if is_ended:
                    print(f"尝试更新视频结束状态: video={video_id}, openid={openid}, 当前状态={watch_record.is_ended}")
                    
                # 原有更新逻辑
                watch_record.duration += duration
                
                # 修改更新is_ended的逻辑，如果强制更新标志为True，则直接设置为True
                if force_update_end_status:
                    old_status = watch_record.is_ended
                    watch_record.is_ended = True
                    print(f"强制更新视频结束状态: 从{old_status}更新为True")
                else:
                    # 原有逻辑，如果已经是True就保持True
                    watch_record.is_ended = watch_record.is_ended or is_ended
                    
                watch_record.session_id = session_id
                watch_record.save()
            
            # 计算用户在此视频上的总观看时长
            user_filter = {'openid': openid} if openid else {'ip_address': client_ip}
            total_duration = VideoWatchRecord.objects.filter(
                video=video, 
                **user_filter
            ).aggregate(models.Sum('duration'))['duration__sum'] or 0
            
            # 直接更新用户统计数据
            if openid:
                try:
                    from apps.login.models import UserInfo
                    user = UserInfo.objects.get(openid=openid)
                    user.update_watch_stats()
                except UserInfo.DoesNotExist:
                    print(f"未找到openid为 {openid} 的用户")
                except Exception as e:
                    print(f"直接更新用户统计时出错: {str(e)}")
            
                response = JsonResponse({
                    'data': {
                        'total_duration': total_duration,
                        'session_id': session_id,
                        'openid': openid,
                        'is_created': created,
                        'is_ended': watch_record.is_ended  
                    }
                })
            
            # 如果是新会话，设置会话ID cookie
            if is_new_session:
                response.set_cookie('video_session_id', session_id, max_age=60*60*24*30)  # 30天有效期
                
            return response
            
        except Video.DoesNotExist:
            return JsonResponse({
                'error': '视频不存在'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="获取用户视频观看统计",
        operation_description="**获取用户累计观看视频数和总观看时长**",
        manual_parameters=[
            openapi.Parameter('openid', openapi.IN_QUERY, description="用户openID", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response(
                description='成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'code': openapi.Schema(type=openapi.TYPE_NUMBER, default=200),
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, default='成功'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT, 
                            properties={
                                'total_videos': openapi.Schema(type=openapi.TYPE_INTEGER, description='累计观看视频数'),
                                'total_duration': openapi.Schema(type=openapi.TYPE_INTEGER, description='累计观看时长(秒)'),
                                'total_completed': openapi.Schema(type=openapi.TYPE_INTEGER, description='完整观看视频数')
                            }
                        )
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='user-watch-stats')
    def user_watch_stats(self, request, *args, **kwargs):
        """获取用户累计观看视频数和总观看时长"""
        from apps.video.models import VideoWatchRecord
        from django.db.models import Count, Sum, Q
        
        # 从查询参数获取 openid
        param_openid = request.query_params.get('openid')
        
        # 获取用户openid - 优先使用查询参数中的openid
        openid = param_openid
        
        # 如果查询参数中没有 openid，尝试从其他来源获取
        if not openid and request.user.is_authenticated:
            openid = getattr(request.user, 'openid', None)
        
        client_ip = self.get_client_ip(request)
        
        # 构建查询条件
        if openid:
            # 已登录用户
            query_filter = {'openid': openid}
        else:
            # 匿名用户，使用IP地址
            query_filter = {'ip_address': client_ip}
        
        # 获取统计数据
        stats = VideoWatchRecord.objects.filter(**query_filter).aggregate(
            total_videos=Count('video', distinct=True),
            total_duration=Sum('duration'),
            total_completed=Count('video', filter=Q(is_ended=True), distinct=True)
        )
        
        # 处理可能的None值
        stats['total_videos'] = stats['total_videos'] or 0
        stats['total_duration'] = stats['total_duration'] or 0
        stats['total_completed'] = stats['total_completed'] or 0
        
        # 格式化响应
        return JsonResponse({
            'success': True,
            'code': 200,
            'msg': '成功',
            'data': {
                'total_videos': stats['total_videos'],
                'total_duration': stats['total_duration'],
                'total_completed': stats['total_completed'],
                'openid': openid  # 返回使用的openid，便于调试
            }
        })

    @swagger_auto_schema(
        tags=["手术视频相关接口"],
        operation_summary="获取用户每日观看统计",
        operation_description="**根据日期统计用户每天观看的视频数量**",
        manual_parameters=[
            openapi.Parameter('openid', openapi.IN_QUERY, description="用户openID", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="起始日期 (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="结束日期 (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('days', openapi.IN_QUERY, description="最近几天(不需要填写start_date和end_date)", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(description='成功')
        }
    )
    @action(detail=False, methods=['get'], url_path='daily-watch-stats')
    def daily_watch_stats(self, request, *args, **kwargs):
        """获取用户每日观看视频统计"""
        from apps.video.models import VideoWatchRecord
        from django.db.models import Count, Sum, Q
        from django.db.models.functions import TruncDate
        import datetime, logging
        
        # 初始化结果列表和计数，避免未定义错误
        result = []
        stats_count = 0
        
        print("\n" + "="*50)
        print("DEBUG: 进入 daily_watch_stats 方法")
        
        # 从查询参数获取 openid
        openid = request.GET.get('openid')
        days = request.GET.get('days', '5')  # 默认5天
        print(f"DEBUG: 请求参数 - openid={openid}, days={days}")
        
        # 先获取用户所有记录，查看实际日期分布
        all_records = VideoWatchRecord.objects.filter(openid=openid)
        total_records = all_records.count()
        print(f"DEBUG: 用户 {openid} 共有 {total_records} 条观看记录")
        
        if all_records.exists():
            # 获取一条记录的详细信息进行检查
            sample_record = all_records.first()
            print(f"DEBUG: 示例记录 - ID={sample_record.id}, 视频={sample_record.video_id}")
            print(f"DEBUG: 创建时间={sample_record.created_at}, 更新时间={sample_record.updated_at}")
            
            # 检查记录的日期分布
            record_dates = all_records.values_list('updated_at', flat=True).distinct()
            date_strs = [d.strftime('%Y-%m-%d') if d else 'None' for d in record_dates]
            print(f"DEBUG: 记录日期分布: {', '.join(date_strs)}")
        
        # 构建日期过滤条件
        try:
            days_int = int(days)
            
            from django.utils import timezone
            end_date = timezone.now().date()
            start_date = end_date - datetime.timedelta(days=days_int-1)
            print(f"DEBUG: 查询日期范围(调整时区后): {start_date} 到 {end_date}")
            
            print("DEBUG: 执行带日期过滤的查询(不使用时区转换)...")
            combined_query = VideoWatchRecord.objects.filter(
                openid=openid,
                updated_at__range=(
                    timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min)),
                    timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))
                )
            )
            
            filtered_count = combined_query.count()
            print(f"DEBUG: 日期过滤后记录数: {filtered_count}")
            
            if filtered_count == 0:
                print("DEBUG: 日期过滤后没有记录，请检查日期范围是否合适")
            
            # SQL记录
            print(f"DEBUG: 实际SQL查询: {str(combined_query.query)}")
            
            print("DEBUG: 执行日期分组统计...")
            # 使用原生SQL函数提取日期，避免时区转换问题
            daily_stats = combined_query.annotate(
                date=RawSQL("DATE(updated_at)", [])
            ).values(
                'date'
            ).annotate(
                videos_count=Count('video', distinct=True),
                total_duration=Sum('duration'),
                completed_count=Count('video', filter=Q(is_ended=True), distinct=True)
            ).order_by('date')
            
            stats_count = len(daily_stats)
            print(f"DEBUG: 统计结果条数: {stats_count}")
            
            # 只保留一个处理循环
            if stats_count > 0:
                for stat in daily_stats:
                    # 添加对None值的处理
                    if stat['date'] is None:
                        print(f"DEBUG: 跳过一条日期为空的记录，视频数: {stat['videos_count']}")
                        continue
                        
                    result.append({
                        'date': stat['date'].strftime('%Y-%m-%d'),
                        'videos_count': stat['videos_count'],
                        'total_duration': stat['total_duration'] or 0,
                        'completed_count': stat['completed_count'],
                        'formatted_duration': self.format_duration(stat['total_duration'] or 0)
                    })
            else:
                # 如果没有找到任何记录，生成过去几天的默认空记录
                print("DEBUG: 没有记录，生成默认的日期数据")
                today = datetime.date.today()
                for i in range(days_int):
                    date = today - datetime.timedelta(days=days_int-1-i)  # 按日期升序
                    result.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'videos_count': 0,
                        'total_duration': 0,
                        'completed_count': 0,
                        'formatted_duration': '0秒'
                    })
        except Exception as e:
            print(f"DEBUG: 发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 异常情况下也生成默认数据
            today = datetime.date.today()
            days_to_show = int(days) if days and days.isdigit() else 5
            for i in range(days_to_show):
                date = today - datetime.timedelta(days=days_to_show-1-i)
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'videos_count': 0,
                    'total_duration': 0,
                    'completed_count': 0,
                    'formatted_duration': '0秒'
                })

        # 返回结果
        print(f"DEBUG: 最终返回 {len(result)} 条记录")
        print("="*50 + "\n")
        return self.get_json_response(result)