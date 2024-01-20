from django.db import models

from django.db import models


# Create your models here.
class Knowledge(models.Model):
    pageName = models.CharField(max_length=100, verbose_name='页面名称')
    pageContent = models.JSONField(default=dict, verbose_name='页面内容')
    createdAt = models.DateTimeField(auto_now_add=True,
                                     verbose_name='创建时间')
    lastModifiedAt = models.DateTimeField(auto_now=True,
                                          verbose_name='最后修改时间')
    courseTypeId = models.IntegerField(verbose_name='课程类型ID')

    class Meta:
        db_table = 'knowledge'
