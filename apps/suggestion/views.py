from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from .models import Suggestion
from utils.serializer import SuggestionSerializer, UserInfoSerializer
from apps.login.models import UserInfo

class SuggestionViewSet(viewsets.ModelViewSet):
    queryset = Suggestion.objects.all()
    serializer_class = SuggestionSerializer
    permission_classes = []  # 允许匿名访问

    def create(self, request, *args, **kwargs):
        print("收到原始请求数据:", request.data)
        
        # 提取feedbackForm和openid
        data_to_save = {}
        if 'feedbackForm' in request.data:
            # 从嵌套的feedbackForm对象中提取数据
            feedback_form = request.data.get('feedbackForm', {})
            data_to_save['suggestion'] = feedback_form.get('suggestion', '')
            data_to_save['contact'] = feedback_form.get('contact', '')
        else:
            # 直接从请求数据中提取
            data_to_save['suggestion'] = request.data.get('suggestion', '')
            data_to_save['contact'] = request.data.get('contact', '')
        
        # 先从查询参数获取，然后从请求体、最后从cookies获取
        openid = request.query_params.get('openid') or request.data.get('openid') or request.COOKIES.get('openid')
        print("使用的openid:", openid)
        
        # 创建序列化器
        serializer = self.get_serializer(data=data_to_save)
        serializer.is_valid(raise_exception=True)
        
        # 保存数据
        if openid:
            try:
                user_info = UserInfo.objects.get(openid=openid)
                username = user_info.userName  # 从UserInfo获取用户名
                print(f"找到用户: {username}, 保存 user_openid={openid}")
                instance = serializer.save(
                    user=user_info, 
                    user_openid=openid,
                    username=username  # 保存用户名
                )
                print(f"保存后的实例: {instance.id}, username={instance.username}, user_openid={instance.user_openid}")
            except UserInfo.DoesNotExist:
                print(f"未找到用户，但设置 user_openid={openid}")
                instance = serializer.save(
                    user=None, 
                    user_openid=openid,
                    username=None  # 用户不存在，用户名为空
                )
                print(f"保存后的实例: {instance.id}, username=None, user_openid={instance.user_openid}")
        else:
            print("无openid")
            instance = serializer.save(
                user=None, 
                user_openid=None,
                username=None  # 无openid，用户名为空
            )
            print(f"保存后的实例: {instance.id}, username=None, user_openid=None")
        
        # 返回响应
        headers = self.get_success_headers(serializer.data)
        from rest_framework.response import Response
        from rest_framework import status
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)