from django.db import models
from apps.login.models import UserInfo  # 导入 login app 的 UserInfo 模型

class Suggestion(models.Model):
    username = models.CharField(max_length=64, verbose_name="用户名", null=True, blank=True)
    suggestion = models.TextField(verbose_name="建议内容")
    contact = models.CharField(max_length=255, blank=True, null=True, verbose_name="联系方式")
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, verbose_name="用户", null=True, blank=True)
    user_openid = models.CharField(max_length=128, verbose_name="用户openid", null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'suggestion'
        verbose_name = '建议'
        verbose_name_plural = '建议'

    def __str__(self):
        if self.username:
            return f"Suggestion by {self.username}"
        return "Anonymous suggestion"