from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from datetime import timedelta, date as py_date, datetime, time
from django.db.models import Count, Case, When, Value, IntegerField
from django.db.models.functions import TruncDate
from django.conf import settings
import pytz

from .models import UserVisitLog
from utils.response import JsonResponse

class UserVisitLogView(APIView):
    """
    记录用户访问日志 (一小时内同一用户不重复记录)
    """
    @swagger_auto_schema(
        tags=["统计相关接口"],
        operation_summary="记录用户访问日志",
        operation_description="接收用户 openid 并记录访问时间。如果同一用户在一小时内已有访问记录，则不创建新记录。",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['openid'],
            properties={
                'openid': openapi.Schema(type=openapi.TYPE_STRING, description='用户唯一标识符'),
            }
        ),
        responses={
            200: openapi.Response(
                description='用户最近一小时内已访问，未创建新日志',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'code': openapi.Schema(type=openapi.TYPE_NUMBER, default=200),
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, default='用户最近一小时内已访问'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
                    }
                )
            ),
            201: openapi.Response(
                description='日志记录成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'code': openapi.Schema(type=openapi.TYPE_NUMBER, default=201),
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, default='日志记录成功'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
                    }
                )
            ),
            400: openapi.Response(description='请求数据无效 (例如缺少 openid)'),
        }
    )
    def post(self, request, *args, **kwargs):
        openid = request.data.get('openid')

        if not openid:
            return JsonResponse({
                'success': False,
                'code': 400,
                'msg': '缺少 openid 参数'
            }, status=status.HTTP_400_BAD_REQUEST)

        one_hour_ago = timezone.now() - timedelta(hours=1)

        recent_visit_exists = UserVisitLog.objects.filter(
            openid=openid,
            visit_timestamp__gte=one_hour_ago
        ).exists()

        if recent_visit_exists:
            return JsonResponse({
                'success': True,
                'code': 200,
                'msg': '用户最近一小时内已访问',
                'data': None
            }, status=status.HTTP_200_OK)

        user_agent = request.META.get('HTTP_USER_AGENT', '')

        try:
            log_entry = UserVisitLog.objects.create(
                openid=openid,
                user_agent=user_agent
            )
            # --- 结束恢复 ---

            print(f"日志已创建，ID: {log_entry.log_id}, 时间戳: {log_entry.visit_timestamp}")
            return JsonResponse({
                'success': True,
                'code': 201,
                'msg': '日志记录成功',
                'data': {'log_id': log_entry.log_id}
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"创建日志时出错: {e}")
            return JsonResponse({
                'success': False,
                'code': 500,
                'msg': '服务器内部错误，无法记录日志'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DailyVisitCountView(APIView):
    """
    获取最近七天的每日访问量 (基于去重后的日志)
    """
    @swagger_auto_schema(
        tags=["统计相关接口"],
        operation_summary="获取近7天每日访问量",
        operation_description="统计 UserVisitLog 表中过去7天（含今天）每天的记录数。",
        responses={
            200: openapi.Response(
                description='成功获取数据',
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
                                    'date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='日期'),
                                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='当日访问记录数')
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            local_tz = pytz.timezone(settings.TIME_ZONE)
        except pytz.UnknownTimeZoneError:
            local_tz = pytz.utc

        today_local = timezone.localtime(timezone.now(), local_tz).date()
        seven_days_ago_local = today_local - timedelta(days=6)
        start_datetime_local = local_tz.localize(datetime.combine(seven_days_ago_local, time.min))
        end_datetime_local = local_tz.localize(datetime.combine(today_local, time.max))

        print(f"--- Daily Counts Query (Python Aggregation) ---")
        print(f"Local Date Range: {seven_days_ago_local} to {today_local}")
        print(f"Querying Local Aware Datetime Range: {start_datetime_local} to {end_datetime_local}")

        # --- 修改：仅获取原始时间戳 ---
        visit_logs = UserVisitLog.objects.filter(
            visit_timestamp__range=(start_datetime_local, end_datetime_local)
        ).values_list('visit_timestamp', flat=True) # 只获取时间戳列表

        print(f"Fetched {len(visit_logs)} timestamps.")

        # --- 在 Python 中进行聚合 ---
        daily_counts = {} # 使用字典存储每日计数
        for ts in visit_logs:
            if ts is None: # 跳过仍然可能存在的 NULL (虽然理论上不应该有)
                continue
            # 确保时间戳是 aware 的 (数据库返回的应该是 UTC)
            if timezone.is_naive(ts):
                 ts = timezone.make_aware(ts, pytz.utc) # 如果是 naive, 假定为 UTC
            # 转换为本地时区并获取日期
            local_dt = timezone.localtime(ts, local_tz)
            log_date = local_dt.date()
            daily_counts[log_date] = daily_counts.get(log_date, 0) + 1

        print(f"Python Aggregation Result: {daily_counts}")

        result_data = []
        current_local_date = seven_days_ago_local
        while current_local_date <= today_local:
            # 从 Python 聚合结果中获取计数
            count = daily_counts.get(current_local_date, 0)
            result_data.append({
                'date': current_local_date.strftime('%Y-%m-%d'),
                'count': count
            })
            current_local_date += timedelta(days=1)

        return JsonResponse(data=result_data)

class HourlyActivityView(APIView):
    """
    获取最近七天用户活跃时间段统计 (按指定时间段)
    """
    @swagger_auto_schema(
        tags=["统计相关接口"],
        operation_summary="获取近7天用户活跃时间段",
        operation_description="统计 UserVisitLog 表中过去7天（含今天）在 '0-6时', '6-12时', '12-18时', '18-24时' 四个时间段的访问记录总数。",
        responses={
            200: openapi.Response(
                description='成功获取数据',
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
                                    'time_slot': openapi.Schema(type=openapi.TYPE_STRING, description='时间段 (例如: 0-6时)'),
                                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='该时间段总访问记录数')
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            local_tz = pytz.timezone(settings.TIME_ZONE)
        except pytz.UnknownTimeZoneError:
            local_tz = pytz.utc

        today_local = timezone.localtime(timezone.now(), local_tz).date()
        seven_days_ago_local = today_local - timedelta(days=6)
        start_datetime_local = local_tz.localize(datetime.combine(seven_days_ago_local, time.min))
        end_datetime_local = local_tz.localize(datetime.combine(today_local, time.max))

        print(f"--- Hourly Activity Query (Python Aggregation) ---")
        print(f"Local Date Range: {seven_days_ago_local} to {today_local}")
        print(f"Querying Local Aware Datetime Range: {start_datetime_local} to {end_datetime_local}")

        # --- 修改：仅获取原始时间戳 ---
        visit_logs = UserVisitLog.objects.filter(
            visit_timestamp__range=(start_datetime_local, end_datetime_local)
        ).values_list('visit_timestamp', flat=True) # 只获取时间戳列表

        print(f"Fetched {len(visit_logs)} timestamps.")

        # --- 在 Python 中进行聚合 ---
        slot_counts = {0: 0, 1: 0, 2: 0, 3: 0} # 初始化时间段计数
        for ts in visit_logs:
            if ts is None:
                continue
            if timezone.is_naive(ts):
                ts = timezone.make_aware(ts, pytz.utc)
            # 转换为本地时区并获取小时
            local_dt = timezone.localtime(ts, local_tz)
            hour = local_dt.hour
            slot = None
            if 0 <= hour < 6: slot = 0
            elif 6 <= hour < 12: slot = 1
            elif 12 <= hour < 18: slot = 2
            elif 18 <= hour < 24: slot = 3

            if slot is not None:
                slot_counts[slot] += 1

        print(f"Python Aggregation Result: {slot_counts}")

        result_data = []
        slot_labels = ['0-6时', '6-12时', '12-18时', '18-24时']
        for i, label in enumerate(slot_labels):
            result_data.append({
                'time_slot': label,
                'count': slot_counts.get(i, 0) # 从 Python 聚合结果获取
            })

        return JsonResponse(data=result_data)
