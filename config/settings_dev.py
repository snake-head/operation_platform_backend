# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = True

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
MEDIA_ROOT = r'D:\Project_Code\video-site\resource'

# temp dictionary to save file chunks when uploading big files by chunk
TMP_UPLOAD_ROOT = r'D:\Project_Code\video-site\resource\tmp'

STATIC_SERVER = r'http://localhost:3557/'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "ERROR",  # 设置处理程序的日志级别为ERROR
            "class": "logging.FileHandler",  # 使用文件处理程序
            "filename": "django_error.log",  # 指定日志文件名
            "formatter": "verbose",  # 可选，指定日志消息的格式
        },
    },
    "loggers": {
        "django_python3_all": {
            "handlers": ["file"],  # 将"file"处理程序关联到"django_python3_all"记录器
            "level": "ERROR",  # 设置"django_python3_all"记录器的日志级别为ERROR
            "propagate": True,  # 消息可以传递给其他记录器
        }
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
}

# Broker配置，使用Redis作为消息中间件
BROKER_URL = 'redis://127.0.0.1:6379/0'

# BACKEND配置，这里使用redis
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

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