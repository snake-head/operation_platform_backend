import os
import random
import base64
import json
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response

# 图片路径配置
REAL_IMAGES_PATH = os.path.join(settings.BASE_DIR, '..', 'data', 'OMENTOR_reCAPTCHA_data', 'RealImages')
FAKE_IMAGES_PATH = os.path.join(settings.BASE_DIR, '..', 'data', 'OMENTOR_reCAPTCHA_data', 'SyntheticImages')

# 确保这些目录存在
os.makedirs(REAL_IMAGES_PATH, exist_ok=True)
os.makedirs(FAKE_IMAGES_PATH, exist_ok=True)

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
        return 'image/jpeg'  # 默认使用 jpeg

def get_random_images(real_count=5, fake_count=1):
    """获取指定数量的随机真实和虚假图片"""
    # 获取所有图片文件
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
    fake_indexes = []  # 修改为记录虚假图片的索引，而非真实图片
    
    # 添加真实图片
    for i, img_file in enumerate(selected_real):
        img_path = os.path.join(REAL_IMAGES_PATH, img_file)
        with open(img_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        
        extension = os.path.splitext(img_file)[1]
        mime_type = get_mime_type(extension)
        
        images.append({
            'id': f'real_{img_file}',
            'src': f'data:{mime_type};base64,{img_data}',
            'is_real': True  # 在后端标记，但不会直接发送给前端
        })
    
    # 添加虚假图片
    for i, img_file in enumerate(selected_fake):
        img_path = os.path.join(FAKE_IMAGES_PATH, img_file)
        with open(img_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        
        images.append({
            'id': f'fake_{img_file}',
            'src': f'data:image/{os.path.splitext(img_file)[1][1:]};base64,{img_data}',
            'is_real': False  # 在后端标记，但不会直接发送给前端
        })
    
    # 随机打乱图片顺序
    random.shuffle(images)
    
    # 记录虚假图片的索引（而非真实图片）
    for i, img in enumerate(images):
        if not img['is_real']:  # 条件变成 not is_real
            fake_indexes.append(i)
    
    # 移除后端标记，不直接告诉前端哪些是真实的
    for img in images:
        del img['is_real']
    
    return {
        'images': images,
        'fake_indexes': fake_indexes  # 返回虚假图片索引
    }

@api_view(['GET'])
def get_recaptcha(request):
    """获取验证码图片"""
    try:
        real_count = int(request.query_params.get('real_count', 5))
        fake_count = int(request.query_params.get('fake_count', 1))
        
        result = get_random_images(real_count, fake_count)
        
        # 将虚假图片索引存储在会话中，用于后续验证
        request.session['recaptcha_correct'] = result['fake_indexes']
        
        # 只返回图片，不返回答案
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
        selected_indexes = request.data.get('selected', [])
        
        # 获取存储在会话中的正确答案
        correct_indexes = request.session.get('recaptcha_correct', [])
        
        # 获取当前尝试次数，默认为0
        attempt_count = request.session.get('recaptcha_attempts', 0)
        
        if not correct_indexes:
            return Response({
                'success': False,
                'message': '验证会话已过期，请重新获取图片'
            }, status=400)
        
        # 转换为集合进行比较
        selected_set = set(selected_indexes)
        correct_set = set(correct_indexes)
        
        # 验证选择是否正确
        is_correct = selected_set == correct_set
        
        # 更新尝试次数
        attempt_count += 1
        request.session['recaptcha_attempts'] = attempt_count
        
        # 只有在验证成功或尝试次数超过3次时清除会话
        max_attempts = 3
        if is_correct or attempt_count >= max_attempts:
            if 'recaptcha_correct' in request.session:
                del request.session['recaptcha_correct']
            if 'recaptcha_attempts' in request.session:
                del request.session['recaptcha_attempts']
        
        # 构造适当的响应消息
        message = '验证成功' if is_correct else '验证失败，请重试'
        if not is_correct and attempt_count >= max_attempts:
            message = '验证失败次数过多，将获取新的验证码'
        
        return Response({
            'success': True,
            'data': {
                'is_correct': is_correct,
                'attempts': attempt_count,
                'max_attempts': max_attempts,
                'message': message,
                'require_refresh': is_correct or attempt_count >= max_attempts
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)