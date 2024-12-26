'''
Description: 
Version: 1.0
Autor: ZhuYichen
Date: 2024-05-13 16:47:01
LastEditors: ZhuYichen
LastEditTime: 2024-12-23 14:36:14
'''
from django.db import models
from django.utils import timezone


# Create your models here.
class Resource(models.Model):
    resourceHash = models.CharField(null=True, blank=True, max_length=64,
                                    verbose_name="文件哈希")
    resourceName = models.CharField(max_length=100, verbose_name="文件名称")
    resourceUrl = models.CharField(unique=True, max_length=255,
                                   verbose_name="文件URL")
    coverImgUrl = models.CharField(blank=True, null=True, max_length=255,
                                   verbose_name="封面图像URL")
    createdAt = models.DateTimeField(default=timezone.now,
                                     verbose_name="创建时间")
    courseId = models.CharField(max_length=50, null=True, blank=True,
                                verbose_name="课程ID")
    metadata = models.JSONField(default=dict, verbose_name="元数据")

    class Meta:
        db_table = 'resource'
