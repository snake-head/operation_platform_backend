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

    class Meta:
        db_table = 'user_info'
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'

    def __str__(self):
        return self.userName
