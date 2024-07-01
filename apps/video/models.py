from enum import Enum

from django.db import models


class StatusEnum(Enum):
    UNKNOWN = 0
    UPLOADING = 1
    PROCESSING = 2
    FINISHED = 3


# Create your models here.
class Video(models.Model):
    class StatusChoices(models.IntegerChoices):
        UNKNOWN = StatusEnum.UNKNOWN.value
        UPLOADING = StatusEnum.UPLOADING.value
        PROCESSING = StatusEnum.PROCESSING.value
        FINISHED = StatusEnum.FINISHED.value

    videoId = models.CharField(unique=True, max_length=50,
                               verbose_name="视频ID")
    videoName = models.CharField(max_length=100, verbose_name="视频名称")
    videoUrl = models.CharField(unique=True, max_length=255,
                                verbose_name="视频URL")
    coverImgUrl = models.CharField(blank=True, null=True, max_length=255,
                                   verbose_name="封面图像URL")
    createdAt = models.DateTimeField(auto_now_add=True,
                                     verbose_name="创建时间")
    lastModifiedAt = models.DateTimeField(auto_now=True,
                                          verbose_name="最后修改时间")
    courseId = models.CharField(max_length=50, null=True, blank=True,
                                verbose_name="课程ID")
    resolutionVersion = models.CharField(max_length=50, null=True, blank=True,
                                         verbose_name="分辨率版本")
    status = models.IntegerField(default=StatusEnum.UNKNOWN.value,
                                 choices=StatusChoices.choices,
                                 verbose_name="状态")
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    triplet = models.CharField(max_length=200, null=True, blank=True,
                                         verbose_name="三元组字幕文件路径")

    class Meta:
        db_table = 'video'


class CaptionAudio(models.Model):
    text = models.TextField(null=True, blank=True, verbose_name="文字")
    audioUrl = models.CharField(unique=True, max_length=255, verbose_name="音频URL")

    class Meta:
        db_table = 'caption_audio'