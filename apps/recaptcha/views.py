import os
import random
import json
from .models import RecaptchaRecord
from .models import RecaptchaStats
from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import path
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response

# 图片路径配置
REAL_IMAGES_PATH = os.path.join(settings.BASE_DIR, '..', 'data', 'OMENTOR_reCAPTCHA_data', 'RealImages')
FAKE_IMAGES_PATH = os.path.join(settings.BASE_DIR, '..', 'data', 'OMENTOR_reCAPTCHA_data', 'SyntheticImages')

# 图片URL路径配置
REAL_IMAGES_URL = 'RealImages' 
FAKE_IMAGES_URL = 'SyntheticImages'  

# 获取更精确的 MIME 类型
def get_mime_type(extension):
    """根据文件扩展名获取MIME类型"""
    extension = extension.lower()
    if extension == '.jpg' or extension == '.jpeg':
        return 'image/jpeg'
    elif extension == '.png':
        return 'image/png'
    elif extension == '.gif':
        return 'image/gif'
    else:
        return 'image/jpeg' 

# 添加图片访问函数
def get_captcha_image(request, image_type, image_name):
    """
    通过URL获取验证码图片
    :param image_type: 'real' 或 'fake'
    :param image_name: 图片文件名
    """
    # 验证会话令牌，防止直接访问
    session_token = request.GET.get('token')
    valid_token = request.session.get('recaptcha_image_token')
    
    if not valid_token or session_token != valid_token:
        raise Http404("图片不存在")
    
    # 确定图片路径
    if image_type == 'real':
        img_path = os.path.join(REAL_IMAGES_PATH, image_name)
    elif image_type == 'fake':
        img_path = os.path.join(FAKE_IMAGES_PATH, image_name)
    else:
        raise Http404("图片类型无效")
    
    # 验证文件路径安全性
    if not os.path.exists(img_path) or not os.path.isfile(img_path):
        raise Http404("图片不存在")
        
    # 返回文件响应
    return FileResponse(open(img_path, 'rb'))

def get_random_images(request, real_count=5, fake_count=1):
    """获取指定数量的随机真实和虚假图片"""
    # 使用固定的服务器URL
    base_url = 'https://omentor.vico-lab.com:3443'
    
    # 获取所有图片文件 (仅读取文件列表，不访问文件内容)
    real_images = [f for f in os.listdir(REAL_IMAGES_PATH) 
                  if os.path.isfile(os.path.join(REAL_IMAGES_PATH, f)) and 
                  f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    
    fake_images = [f for f in os.listdir(FAKE_IMAGES_PATH) 
                  if os.path.isfile(os.path.join(FAKE_IMAGES_PATH, f)) and 
                  f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    
    # 确保有足够的图片
    if len(real_images) < real_count:
        raise ValueError(f"没有足够的真实图片，需要{real_count}张，只有{len(real_images)}张")
    
    if len(fake_images) < fake_count:
        raise ValueError(f"没有足够的虚假图片，需要{fake_count}张，只有{len(fake_images)}张")
    
    # 随机选择图片
    selected_real = random.sample(real_images, real_count)
    selected_fake = random.sample(fake_images, fake_count)
    
    # 准备结果数据
    images = []
    fake_indexes = []
    
    # 添加真实图片
    for i, img_file in enumerate(selected_real):
        # 构建图片URL
        img_url = f"{base_url}/resource/media/{REAL_IMAGES_URL}/{img_file}"
        
        images.append({
            'id': f'real_{img_file}',
            'src': img_url,
            'is_real': True
        })
    
    # 添加虚假图片
    for i, img_file in enumerate(selected_fake):
        # 构建图片URL
        img_url = f"{base_url}/resource/media/{FAKE_IMAGES_URL}/{img_file}"
        
        images.append({
            'id': f'fake_{img_file}',
            'src': img_url,
            'is_real': False
        })
    
    # 随机打乱图片顺序
    random.shuffle(images)
    
    # 记录虚假图片的索引
    for i, img in enumerate(images):
        if not img['is_real']:
            fake_indexes.append(i)
    
    # 移除后端标记
    for img in images:
        del img['is_real']
    
    return {
        'images': images,
        'fake_indexes': fake_indexes
    }

@api_view(['GET'])
def get_recaptcha(request):
    """获取验证码图片"""
    try:
        real_count = int(request.query_params.get('real_count', 5))
        fake_count = int(request.query_params.get('fake_count', 1))
        
        result = get_random_images(request, real_count, fake_count)
        
        # 将虚假图片索引存储在会话中，用于后续验证
        request.session['recaptcha_correct'] = result['fake_indexes']
        
        # 添加这一行，将图片列表存储在会话中
        request.session['recaptcha_images'] = result['images']
        
        # 重置尝试次数
        request.session['recaptcha_attempts'] = 0
        
        # 只返回图片URL，不返回答案
        return Response({
            'success': True,
            'message': '请选择虚假的图片',  
            'data': {
                'images': result['images'],
                'total': len(result['images'])
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['POST'])
def verify_recaptcha(request):
    """验证用户选择的图片"""
    try:
        # 获取用户选择的图片索引
        selected_index = request.data.get('selected', [])[0] if request.data.get('selected') else None
        
        # 获取存储在会话中的正确答案
        correct_index = request.session.get('recaptcha_correct', [])[0] if request.session.get('recaptcha_correct') else None
        
        if correct_index is None:
            return Response({
                'success': False,
                'message': '验证会话已过期，请重新获取图片'
            }, status=400)
            
        # 获取用户提供的理由
        reason = request.data.get('reason', '')
        
        # 获取用户openid
        openid = request.data.get('openid', '') or request.session.get('openid', '')
        
        # 确保从会话中获取完整的图片数据
        images = request.session.get('recaptcha_images', [])
        
        # 获取虚假图片的名称 - 直接使用正确索引，不考虑用户选择
        if correct_index is not None and images and correct_index < len(images):
            correct_image = images[correct_index]
            fake_image_name = correct_image['id'].split('_', 1)[1] if '_' in correct_image['id'] else correct_image['id']
        else:
            # 如果没有找到图片信息，使用默认值
            fake_image_name = 'unknown'
        
        # 验证逻辑
        is_correct = selected_index == correct_index
        
         # 记录验证结果 - 这里记录的是虚假图片的名称，而不是用户选择的图片
        RecaptchaRecord.objects.create(
            openid=openid,
            imgname=fake_image_name,  # 虚假图片名称
            iscorrect=is_correct,     # 用户是否选择正确
            reason=reason             # 用户提供的理由
        )
        
        # 更新统计数据 (可选，如果希望实时统计)
        RecaptchaStats.update_single_stat(fake_image_name)
        
        # 构造响应消息
        message = '验证成功' if is_correct else '验证失败，请查看正确答案'
        
        # 清除会话数据 - 无论成功或失败都只尝试一次
        if 'recaptcha_correct' in request.session:
            del request.session['recaptcha_correct']
        if 'recaptcha_attempts' in request.session:
            del request.session['recaptcha_attempts']
        
        # 准备响应数据
        response_data = {
            'success': True,
            'data': {
                'is_correct': is_correct,
                'message': message,
                'require_refresh': True  # 总是需要刷新，因为只允许一次尝试
            }
        }
        
        # 如果验证失败，添加正确答案
        if not is_correct:
            response_data['data'].update({
                'correct_index': correct_index,
                'selected_index': selected_index
            })
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)