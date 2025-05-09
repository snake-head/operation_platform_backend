# Create your views here.
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.db.models import Max, Count, Q
from apps.course.models import Course, CourseType
from apps.video.models import VideoWatchRecord, Video
import datetime
from utils.paginator import AppPageNumberPagination
from utils.queryset_filter import CourseFilter, CourseTypeFilter
from utils.response import JsonResponse
from utils.serializer import CourseSerializer, CourseTypeSerializer


@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        tags=['课程相关接口'],
        operation_description="**更新某一条课程记录**"
    )
)
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('id')
    serializer_class = CourseSerializer
    pagination_class = AppPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CourseFilter

    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_description="**查询课程列表**"
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_description="**创建一个课程**"
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_description="**查询某一个课程**"
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_description="**更新某一条课程记录**"
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_description="**删除某一个课程**"
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return JsonResponse(data=response.data)
    
    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_summary="获取所有课程ID",
        operation_description="**返回一个包含所有课程 courseId 的列表，用于分类筛选等场景。**",
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
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING, description='课程ID (courseId)')
                        )
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='allcourseid')
    def get_all_course_ids(self, request, *args, **kwargs):
        all_course_ids = list(Course.objects.values_list('courseId', flat=True).distinct().order_by('courseId'))
        return JsonResponse(data=all_course_ids)

    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_summary="获取所有课程ID和名称",
        operation_description="**返回一个包含所有课程 courseId 和 courseName 的对象列表。**",
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
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'courseId': openapi.Schema(type=openapi.TYPE_STRING, description='课程ID'),
                                    'courseName': openapi.Schema(type=openapi.TYPE_STRING, description='课程名称')
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='allcourse')
    def get_all_course_ids_names(self, request, *args, **kwargs):
        """
        高效获取所有课程的 courseId 和 courseName 列表。
        """
        all_courses_data = list(
            Course.objects.values('courseId', 'courseName')
                          .distinct()
                          .order_by('courseId')
        )

        return JsonResponse(data=all_courses_data)

    @swagger_auto_schema(
        tags=['课程相关接口'],
        operation_summary="获取用户课程观看进度列表",
        operation_description="**获取指定用户观看过的课程列表，包含最后观看日期和观看进度。**",
        manual_parameters=[
            openapi.Parameter('openid', openapi.IN_QUERY, description="用户openID", type=openapi.TYPE_STRING, required=True),
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
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'courseId': openapi.Schema(type=openapi.TYPE_STRING, description='课程ID'),
                                    'lastWatchedAt': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='最后观看日期'),
                                    'courseName': openapi.Schema(type=openapi.TYPE_STRING, description='课程名称'),
                                    'watchProgress': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='观看进度 (0.0 to 1.0)')
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(description='缺少 openid 参数'),
        }
    )
    @action(detail=False, methods=['get'], url_path='userprogress')
    def get_user_course_progress(self, request, *args, **kwargs):
        """
        获取用户的课程观看进度列表。
        """
        openid = request.query_params.get('openid')

        if not openid:
            return JsonResponse({
                'success': False,
                'code': 400,
                'msg': '缺少 openid 参数'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 1. 从 VideoWatchRecord 获取用户观看过的课程、最后观看日期、完成的视频数
        user_watch_stats = VideoWatchRecord.objects.filter(
            openid=openid
        ).values(
            'course_ID'
        ).annotate(
            lastWatchedAt_datetime=Max('updated_at'),
            completed_video_count=Count('video', filter=Q(is_ended=True), distinct=True)
        ).order_by('-lastWatchedAt_datetime')

        watched_course_ids = [stat['course_ID'] for stat in user_watch_stats]

        if not watched_course_ids:
            return JsonResponse(data=[])

        # 2. 获取这些课程的名称
        courses_info = Course.objects.filter(
            courseId__in=watched_course_ids
        ).values('courseId', 'courseName')
        course_name_map = {info['courseId']: info['courseName'] for info in courses_info}

        # 3. 获取这些课程的总视频数
        course_video_counts = Video.objects.filter(
            courseId__in=watched_course_ids
        ).values(
            'courseId'
        ).annotate(
            total_videos=Count('id')
        )
        total_videos_map = {stat['courseId']: stat['total_videos'] for stat in course_video_counts}

        # 4. 合并数据并计算进度
        result_data = []
        for stat in user_watch_stats:
            course_id = stat['course_ID']
            total_videos = total_videos_map.get(course_id, 0)
            completed_videos = stat['completed_video_count']

            watch_progress = (completed_videos / total_videos) if total_videos > 0 else 0.0

            last_watched_date_str = stat['lastWatchedAt_datetime'].strftime('%Y-%m-%d') if stat['lastWatchedAt_datetime'] else None

            result_data.append({
                'courseId': course_id,
                'lastWatchedAt': last_watched_date_str,
                'courseName': course_name_map.get(course_id, '未知课程'),
                'watchProgress': round(watch_progress, 3)
            })

        return JsonResponse(data=result_data)


@method_decorator(
    name='partial_update',
    decorator=swagger_auto_schema(
        tags=['课程类别相关接口'],
        operation_description="**更新某一条课程类别记录**"
    )
)
class CourseTypeViewSet(viewsets.ModelViewSet):
    queryset = CourseType.objects.all().order_by('id')
    serializer_class = CourseTypeSerializer
    pagination_class = AppPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CourseTypeFilter

    @swagger_auto_schema(
        tags=['课程类别相关接口'],
        operation_description="**查询课程类别列表**"
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程类别相关接口'],
        operation_description="**创建一个课程类别**"
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, args, kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程类别相关接口'],
        operation_description="**查询某一个课程类别**"
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, args, kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程类别相关接口'],
        operation_description="**更新某一条课程类别记录**"
    )
    def update(self, request, *args, **kwargs):
        response = super().update(request, args, kwargs)
        return JsonResponse(data=response.data)

    @swagger_auto_schema(
        tags=['课程类别相关接口'],
        operation_description="**删除一个课程类别**"
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, args, kwargs)
        return JsonResponse(data=response.data)
