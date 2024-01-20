from __future__ import absolute_import , unicode_literals
import os
from celery import Celery
from django.conf import settings

# 设置系统环境变量，安装django，必须设置，否则在启动celery时会报错
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'operation_platform_backend.settings')

celery_app = Celery('operation_platform_backend')
celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
celery_app.conf.worker_concurrency = 8
celery_app.conf.worker_max_tasks_per_child = 100
