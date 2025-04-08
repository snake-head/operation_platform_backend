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
    surgery_info = models.JSONField(default=dict, verbose_name="手术信息")
    view_count = models.IntegerField(default=0, verbose_name="视频浏览量")

    class Meta:
        db_table = 'video'


class CaptionAudio(models.Model):
    text = models.TextField(null=True, blank=True, verbose_name="文字")
    audioUrl = models.CharField(unique=True, max_length=255, verbose_name="音频URL")

    class Meta:
        db_table = 'caption_audio'
class VideoWatchRecord(models.Model):
    """用户视频观看记录"""
    # 关联用户
    openid = models.CharField(max_length=100, null=True, blank=True, verbose_name='用户OpenID')
    
    # 视频ID
    video = models.ForeignKey(Video, to_field='videoId', on_delete=models.CASCADE, verbose_name='视频')

    # 课程ID
    course_ID = models.CharField(max_length=50, null=True, blank=True, verbose_name='课程ID', db_column='course_id')
    
    # 观看时长(秒)
    duration = models.PositiveIntegerField(default=0, verbose_name='观看时长(秒)')
    
    # 是否看完
    is_ended = models.BooleanField(default=False, verbose_name='是否看完')
    
    # IP地址(用于匿名用户)
    ip_address = models.CharField(max_length=50, blank=True, null=True, verbose_name='IP地址')
    
    # 会话ID(标识同一用户的不同观看会话)
    session_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='会话ID')
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    # 更新时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    @property
    def course_id(self):
        """获取关联视频的课程ID"""
        if self.course_ID:
            return self.course_ID
        return self.video.courseId if self.video else None
    
    def save(self, *args, **kwargs):
        """重写保存方法，确保course_ID正确设置"""
        if not self.course_ID and self.video_id:
            try:
                self.course_ID = Video.objects.get(videoId=self.video_id).courseId
            except Video.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = '视频观看记录'
        verbose_name_plural = '视频观看记录'
        
    def __str__(self):
      return f"{self.openid if self.openid else self.ip_address} - {self.video.videoName} - {self.duration}秒"