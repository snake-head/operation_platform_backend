# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = False

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'operation_platform',
        'USER': 'miva_admin',
        'PASSWORD': '@Vico0808',
        'HOST': '172.16.200.25',
        'PORT': '3306'
    }
}

# resource root path for videos, images, etc
MEDIA_ROOT = r'/data'

# temp dictionary to save file chunks when uploading big files by chunk
TMP_UPLOAD_ROOT = r'/data/tmp'

STATIC_SERVER = r'https://omentor.vico-lab.com:3443/'

# Broker配置，使用Redis作为消息中间件
BROKER_URL = 'redis://omentor-redis-service:6379/0'

# BACKEND配置，这里使用redis
CELERY_RESULT_BACKEND = 'redis://omentor-redis-service:6379/0'

# 结果序列化方案
CELERY_RESULT_SERIALIZER = 'json'

# 任务结果过期时间，秒
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24

# 时区配置
CELERY_TIMEZONE = 'Asia/Shanghai'

# 指定导入的任务模块，可以指定多个
CELERY_IMPORTS = (
   'apps.video.tasks',
)