from django.db import models

# Create your models here.

class UserVisitLog(models.Model):
    """用户访问日志模型"""
    log_id = models.BigAutoField(primary_key=True, help_text="日志唯一ID")
    openid = models.CharField(max_length=255, db_index=True, help_text="访问用户的标识符")
    visit_timestamp = models.DateTimeField(auto_now_add=True, db_index=True, help_text="访问时间戳")
    user_agent = models.TextField(null=True, blank=True, help_text="用户代理信息")

    class Meta:
        db_table = 'user_visit_log'
        verbose_name = '用户访问日志'
        verbose_name_plural = verbose_name
        ordering = ['-visit_timestamp']

    def __str__(self):
        return f"Log {self.log_id} by {self.openid} at {self.visit_timestamp}"