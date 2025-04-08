import requests
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import UserInfo  # 导入 UserInfo 模型

def callback(request):
    code = request.GET.get('code')
    openid = request.COOKIES.get('openid') 

    if not code:
        return JsonResponse({'error': 'No code provided'}, status=400)

    if not openid:
        return JsonResponse({'error': 'No openid provided'}, status=400)

    token_url = 'https://national.medevice.pro/oauth2/token'
    params = {
        'appid': settings.APP_ID,
        'secret': settings.CLIENT_SECRET,
        'code': code
    }

    response = requests.get(token_url, params=params)
    if response.status_code == 200:
        token_data = response.json()
        print("Token Data:", token_data)  # 打印 token_data

        token = token_data.get("token")

        # 获取用户信息
        userinfo_url = 'https://national.medevice.pro/userinfo'
        userinfo_params = {
            'token': token,
            'openid': openid,
            'code': code
        }
        userinfo_response = requests.get(userinfo_url, params=userinfo_params)

        if userinfo_response.status_code == 200:
            user_data = userinfo_response.json()

            try:
                # 创建或更新用户信息
                user, created = UserInfo.objects.update_or_create(
                    openid=user_data.get('openid'),
                    defaults={
                        'userName': user_data.get('userName'),
                        'userNo': user_data.get('userNo'),
                        'sex': user_data.get('sex'),
                        'hospital': user_data.get('hospital'),
                        'postionType': user_data.get('postionType'),
                        'accountType': user_data.get('accountType'),
                        'department': user_data.get('department'),
                    }
                )
                print(f"User {'created' if created else 'updated'}: {user}")
            except Exception as e:
                print(f"Error saving user info: {e}")
                return JsonResponse({'error': 'Failed to save user info'}, status=500)

            redirect_url = f'https://omentor.medevice.pro/callback?token={token}' # 重定向到前端页面
            # redirect_url = f'http://localhost:4000/callback?token={token}' # 本地测试用
            return HttpResponseRedirect(redirect_url)
        else:
            return JsonResponse({'error': 'Failed to get user info'}, status=400)

    else:
        return JsonResponse({'error': 'Failed to get token'}, status=400)
    
def get_user_info(request):
    """获取用户信息接口"""
    openid = request.GET.get('openid')
    
    if not openid:
        return JsonResponse({
            'success': False,
            'code': 400,
            'msg': '缺少必要参数openid'
        }, status=400)
    
    try:
        user = UserInfo.objects.get(openid=openid)
        
        # 获取用户信息
        user_data = {
            'openid': user.openid,
            'userName': user.userName,
            'userNo': user.userNo,
            'sex': user.sex,
            'hospital': user.hospital,
            'postionType': user.postionType,
            'accountType': user.accountType,
            'department': user.department,
            'total_duration': user.total_duration,
            'formatted_duration': user.formatted_duration,
            'total_end': user.total_end,
            'total_viewed': user.total_viewed
        }
        
        return JsonResponse({
            'success': True,
            'code': 200,
            'msg': '获取用户信息成功',
            'data': user_data
        })
        
    except UserInfo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'code': 404,
            'msg': f'未找到openid为{openid}的用户'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'code': 500,
            'msg': f'获取用户信息失败: {str(e)}'
        }, status=500)