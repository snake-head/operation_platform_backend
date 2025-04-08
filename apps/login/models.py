from django.db import models

class UserInfo(models.Model):
    openid = models.CharField(max_length=255, primary_key=True, verbose_name='OpenID')
    userName = models.CharField(max_length=255, verbose_name='用户名')
    userNo = models.CharField(max_length=255, verbose_name='用户电话')
    sex = models.CharField(max_length=255, verbose_name='性别')
    hospital = models.CharField(max_length=255, verbose_name='医院')
    postionType = models.CharField(max_length=255, verbose_name='职位类型')
    accountType = models.CharField(max_length=255, verbose_name='账户类型')
    department = models.CharField(max_length=255, blank=True, null=True, verbose_name='部门')
    total_duration = models.PositiveIntegerField(default=0, verbose_name='总观看时长(秒)')
    total_end = models.PositiveIntegerField(default=0, verbose_name='已完成视频数')
    total_viewed = models.PositiveIntegerField(default=0, verbose_name='已观看视频总数') 

    class Meta:
        db_table = 'user_info'
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'

    def __str__(self):
        return self.userName
        
    @property
    def formatted_duration(self):
        """将总观看时长格式化为时.分.秒"""
        seconds = self.total_duration
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"
            
    def update_watch_stats(self):
        """更新用户的观看统计数据"""
        from apps.video.models import VideoWatchRecord
        from django.db.models import Sum, Count, Q
        
        stats = VideoWatchRecord.objects.filter(openid=self.openid).aggregate(
            total_duration=Sum('duration'),
            total_end=Count('video', filter=Q(is_ended=True), distinct=True),
            total_viewed=Count('video', distinct=True)  
        )
        
        self.total_duration = stats['total_duration'] or 0
        self.total_end = stats['total_end'] or 0
        self.total_viewed = stats['total_viewed'] or 0  
        self.save(update_fields=['total_duration', 'total_end', 'total_viewed'])
        
        return self.total_duration, self.total_end, self.total_viewed
