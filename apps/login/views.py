import requests
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
import urllib.parse
from .models import UserInfo  # 导入 UserInfo 模型

def callback(request):
    code = request.GET.get('code')
    openid = request.COOKIES.get('openid') 

    if not code:
        return JsonResponse({'error': 'No code provided'}, status=400)

    if not openid:
        return JsonResponse({'error': 'No openid provided'}, status=400)

    token_url = 'https://www.medevice.pro/oauth2/token'
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
        userinfo_url = 'https://www.medevice.pro/userinfo'
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

            redirect_url = f'https://omentor.medevice.pro/callback?token={token}'
            return HttpResponseRedirect(redirect_url)
        else:
            return JsonResponse({'error': 'Failed to get user info'}, status=400)

    else:
        return JsonResponse({'error': 'Failed to get token'}, status=400)