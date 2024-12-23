from django.http import JsonResponse
from django.conf import settings
from .models import Picture
import os
import random

def get_pictures(request):
    # 获取前端传递的三元组参数
    equipment = request.GET.get('equipment')
    action = request.GET.get('action')
    body_part = request.GET.get('bodyPart')
    
    # 验证参数是否完整
    if not all([equipment, action, body_part]):
        return JsonResponse({
            'error': '缺少必要参数',
            'required': ['equipment', 'action', 'bodyPart']
        }, status=400)
    
    # 构建文件夹名称
    folder_name = f"{equipment}_{action}_{body_part}"
    
    # 定义基础路径和 URL
    BASE_URL = 'https://omentor.vico-lab.com:3443'
    BASE_PATH = os.path.join(settings.BASE_DIR, 'data', 'Selected_SD_images')
    folder_path = os.path.join(BASE_PATH, folder_name)
    
    try:
        # 获取文件夹中所有的 PNG 文件
        png_files = [f for f in os.listdir(folder_path) if f.endswith('.png')]
        
        if not png_files:
            return JsonResponse({
                'error': '文件夹中没有PNG文件',
                'folder': folder_name
            }, status=404)
        
        # 随机选择一个文件
        random_file = random.choice(png_files)
        
        # 构建完整的图片 URL
        full_url = f"{BASE_URL}/resource/media/{folder_name}/{random_file}"
        
        # 构建返回数据
        data = {
            'imageUrl': full_url
        }
        
        return JsonResponse(data)
        
    except FileNotFoundError:
        return JsonResponse({
            'error': '文件夹不存在',
            'folder': folder_name
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'发生错误: {str(e)}'
        }, status=500)