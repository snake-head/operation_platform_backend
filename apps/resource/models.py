from django.db import models


# Create your models here.
class Resource(models.Model):
    resourceHash = models.CharField(null=True, blank=True, max_length=64,
                                    verbose_name="文件哈希")
    resourceName = models.CharField(max_length=100, verbose_name="文件名称")
    resourceUrl = models.CharField(unique=True, max_length=255,
                                   verbose_name="文件URL")
    coverImgUrl = models.CharField(blank=True, null=True, max_length=255,
                                   verbose_name="封面图像URL")
    createdAt = models.DateTimeField(auto_now_add=True,
                                     verbose_name="创建时间")
    courseId = models.CharField(max_length=50, null=True, blank=True,
                                verbose_name="课程ID")
    metadata = models.JSONField(default=dict, verbose_name="元数据")

    class Meta:
        db_table = 'resource'
